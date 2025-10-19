"""Aplicación web Flask para el Monitor PJN.

Esta aplicación proporciona una interfaz web para gestionar y visualizar
el monitoreo de expedientes y entradas del PJN.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import signal
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

# Agregar el directorio padre al path para importar pjn
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# noinspection PyUnresolvedReferences
from pjn.monitor.config import MonitorConfig
# noinspection PyUnresolvedReferences
from pjn.monitor.core import MonitorPJN
# noinspection PyUnresolvedReferences
from pjn.monitor.exceptions import ConfigurationError, MonitorError, StorageError
# noinspection PyUnresolvedReferences
from pjn.monitor.storage import StorageManager

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # Para caracteres UTF-8

# Rutas de configuración


def _resolve_path_from_env(env_var: str, default: Path) -> Path:
    """Resuelve rutas permitiendo sobreescritura por variables de entorno."""

    override = os.getenv(env_var)
    if not override:
        return default

    candidate = Path(override)
    if not candidate.is_absolute():
        candidate = BASE_DIR / candidate

    return candidate


CONFIG_PATH = _resolve_path_from_env("MONITOR_CONFIG_PATH", BASE_DIR / "config" / "monitor.json")
MONITOR_SCRIPT = _resolve_path_from_env("MONITOR_SCRIPT_PATH", BASE_DIR / "ejecutar_monitor_universal.py")
LOGS_DIR = _resolve_path_from_env("MONITOR_LOGS_DIR", BASE_DIR / "logs")
RUNTIME_INFO_PATH = LOGS_DIR / "monitor_runtime.json"
EVENTS_LOG_PATH = LOGS_DIR / "monitor_web_actions.log"

# Variables globales para control del monitor
monitor_process = None
monitor_lock = Lock()


def get_monitor_config() -> MonitorConfig:
    """Carga la configuración del monitor con manejo robusto de errores."""

    try:
        return MonitorConfig.from_file(CONFIG_PATH)
    except (json.JSONDecodeError, TypeError, ValueError, OSError) as exc:
        app.logger.exception("Error accediendo al archivo de configuración")
        raise ConfigurationError(f"No se pudo cargar la configuración: {exc}") from exc
    except MonitorError as exc:
        app.logger.exception("Configuración inválida")
        raise ConfigurationError(f"La configuración del monitor es inválida: {exc}") from exc


def get_storage() -> StorageManager:
    """Obtiene el StorageManager resolviendo rutas relativas al proyecto."""

    config = get_monitor_config()
    data_dir = Path(config.directorio_datos)
    if not data_dir.is_absolute():
        data_dir = BASE_DIR / data_dir

    try:
        return StorageManager(data_dir)
    except OSError as exc:
        app.logger.exception("No se pudo inicializar el almacenamiento del monitor")
        raise StorageError(f"No se pudo acceder al directorio de datos: {exc}") from exc


def _build_monitor(config: MonitorConfig | None = None) -> MonitorPJN:
    """Crea una instancia del monitor con rutas absolutas para los datos."""

    base_config = config or get_monitor_config()
    config_dict = base_config.to_dict()
    working_config = MonitorConfig(**config_dict)

    data_dir = Path(working_config.directorio_datos)
    if not data_dir.is_absolute():
        data_dir = BASE_DIR / data_dir
    working_config.directorio_datos = str(data_dir)

    return MonitorPJN(working_config)


def _parse_datetime(value: str | None) -> datetime:
    """Intenta convertir una cadena en fecha/hora para ordenamiento."""
    if not value:
        return datetime.min

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        for fmt in ("%d/%m/%Y", "%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue

    return datetime.min


def _write_runtime_info(pid: int, started_at: str) -> None:
    """Persiste metadatos del proceso del monitor para futuras consultas."""

    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        payload = {"pid": pid, "started_at": started_at}
        RUNTIME_INFO_PATH.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        app.logger.exception("No se pudo guardar la información de ejecución del monitor")


def _load_runtime_info() -> dict[str, object]:
    """Obtiene los metadatos persistidos del monitor, si existen."""

    if not RUNTIME_INFO_PATH.exists():
        return {}

    try:
        return json.loads(RUNTIME_INFO_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        app.logger.warning("Archivo runtime info corrupto, se ignorará")
        return {}
    except OSError as exc:
        app.logger.exception("No se pudo leer información de ejecución previa")
        return {}


def _clear_runtime_info() -> None:
    """Elimina los metadatos persistidos del monitor."""

    try:
        RUNTIME_INFO_PATH.unlink(missing_ok=True)
    except TypeError:
        if RUNTIME_INFO_PATH.exists():
            RUNTIME_INFO_PATH.unlink()
    except OSError as exc:
        app.logger.exception("No se pudo limpiar la información de ejecución del monitor")


def _log_monitor_event(action: str, success: bool, message: str, pid: int | None = None) -> None:
    """Registra intentos de arranque/detención en un log dedicado."""

    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "success": success,
            "message": message,
        }
        if pid is not None:
            entry["pid"] = pid

        with EVENTS_LOG_PATH.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as exc:
        app.logger.exception("No se pudo registrar evento del monitor")


def _is_process_alive(pid: int | None) -> bool:
    """Verifica si un PID existe y sigue en ejecución."""

    if not pid or pid <= 0:
        return False

    if sys.platform == "win32":
        try:
            import ctypes  # pylint: disable=import-outside-toplevel

            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if handle == 0:
                return False
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        except Exception:  # noqa: BLE001
            return False

    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False

    return True


def _current_monitor_state() -> dict[str, object | None]:
    """Obtiene el estado actual del monitor con metadatos persistidos."""

    global monitor_process

    with monitor_lock:
        if monitor_process is not None and monitor_process.poll() is None:
            runtime_info = _load_runtime_info()
            started_at = runtime_info.get("started_at")
            if not started_at:
                started_at = datetime.now(timezone.utc).isoformat()
                _write_runtime_info(monitor_process.pid, started_at)

            return {
                "status": "running",
                "running": True,
                "pid": monitor_process.pid,
                "started_at": started_at,
                "source": "process",
            }

        if monitor_process is not None:
            monitor_process = None

    runtime_info = _load_runtime_info()
    pid = runtime_info.get("pid") if runtime_info else None
    started_at = runtime_info.get("started_at") if runtime_info else None

    if isinstance(pid, int) and _is_process_alive(pid):
        return {
            "status": "running",
            "running": True,
            "pid": pid,
            "started_at": started_at,
            "source": "runtime",
        }

    if runtime_info:
        _clear_runtime_info()

    return {
        "status": "stopped",
        "running": False,
        "pid": None,
        "started_at": None,
        "source": "stopped",
    }


def _run_monitor_coroutine(coro):
    """Ejecuta una coroutine del monitor en un loop aislado."""

    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(coro)
        loop.run_until_complete(loop.shutdown_asyncgens())
        return result
    finally:
        asyncio.set_event_loop(None)
        loop.close()


VALID_WEEK_DAYS = [
    "lunes",
    "martes",
    "miercoles",
    "jueves",
    "viernes",
    "sabado",
    "domingo",
]

TIME_PATTERN = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


def _update_int_field(
    config: MonitorConfig,
    data: dict,
    field: str,
    errors: dict[str, str],
    *,
    min_value: int = 1,
    max_value: int | None = None,
    allow_zero: bool = False,
) -> None:
    """Valida y actualiza un campo entero de la configuración."""

    if field not in data:
        return

    value = data[field]
    if value in (None, ""):
        return

    try:
        value_int = int(value)
    except (TypeError, ValueError):
        errors[field] = "Debe ser un número entero"
        return

    lower_bound = 0 if allow_zero else min_value
    if value_int < lower_bound or (max_value is not None and value_int > max_value):
        if max_value is not None:
            errors[field] = f"Debe estar entre {lower_bound} y {max_value}"
        else:
            errors[field] = f"Debe ser mayor o igual a {lower_bound}"
        return

    setattr(config, field, value_int)


def _update_time_field(config: MonitorConfig, data: dict, field: str, errors: dict[str, str]) -> None:
    """Valida un campo horario en formato HH:MM."""

    if field not in data:
        return

    value = data[field]
    if value in (None, ""):
        return

    if not isinstance(value, str) or not TIME_PATTERN.match(value):
        errors[field] = "Formato inválido (usar HH:MM)"
        return

    setattr(config, field, value)


def _update_days_field(config: MonitorConfig, data: dict, errors: dict[str, str]) -> None:
    """Valida y asigna los días laborales seleccionados."""

    if "dias_laborales" not in data:
        return

    value = data["dias_laborales"]
    if value in (None, ""):
        errors["dias_laborales"] = "Debes seleccionar al menos un día"
        return

    if isinstance(value, str):
        days = [part.strip().lower() for part in value.split(",") if part.strip()]
    else:
        days = [str(part).lower() for part in value]

    invalid_days = [day for day in days if day not in VALID_WEEK_DAYS]
    if invalid_days:
        errors["dias_laborales"] = f"Días inválidos: {', '.join(sorted(set(invalid_days)))}"
        return

    if not days:
        errors["dias_laborales"] = "Debes seleccionar al menos un día"
        return

    config.dias_laborales = days


@app.route('/')
def index():
    """Página principal - redirige al dashboard."""
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
def dashboard():
    """Dashboard principal con resumen del estado del monitor."""

    try:
        config = get_monitor_config()
        storage = get_storage()
        estado = storage.cargar_estado()

        # Cargar datos
        entradas = storage.cargar_entradas_conocidas()
        expedientes = storage.cargar_expedientes_conocidos()

        # Estadísticas
        stats = {
            'total_entradas': len(entradas),
            'total_expedientes': len(expedientes),
            'ultima_verificacion_entradas': estado.ultima_verificacion_entradas,
            'ultima_verificacion_expedientes': estado.ultima_verificacion_expedientes,
            'errores_entradas': estado.errores_consecutivos_entradas,
            'errores_expedientes': estado.errores_consecutivos_expedientes,
            'verificar_entradas': config.verificar_entradas,
            'verificar_expedientes': config.verificar_expedientes,
            'modo': config.modo,
        }

        # Entradas recientes (últimas 10)
        entradas_recientes = sorted(
            entradas,
            key=lambda e: _parse_datetime(e.fecha),
            reverse=True
        )[:10]

        # Expedientes con cambios recientes (últimos 10)
        expedientes_recientes = sorted(
            expedientes,
            key=lambda e: _parse_datetime(e.ultima_actuacion),
            reverse=True
        )[:10]

        return render_template(
            'dashboard.html',
            stats=stats,
            entradas_recientes=entradas_recientes,
            expedientes_recientes=expedientes_recientes
        )
    except (ConfigurationError, StorageError) as exc:
        app.logger.exception("Error al construir el dashboard")
        return render_template('error.html', error_message=str(exc)), 500
    except Exception as exc:  # noqa: BLE001
        app.logger.exception("Fallo inesperado en el dashboard")
        return render_template(
            'error.html',
            error_message="Ocurrió un error inesperado al cargar el panel.",
        ), 500


@app.route('/entradas')
def entradas():
    """Página de listado de entradas."""

    try:
        storage = get_storage()
        entradas_list = storage.cargar_entradas_conocidas()

        # Ordenar por fecha descendente
        entradas_list = sorted(
            entradas_list,
            key=lambda e: _parse_datetime(e.fecha),
            reverse=True
        )

        return render_template('entradas.html', entradas=entradas_list)
    except (ConfigurationError, StorageError) as exc:
        app.logger.exception("No se pudieron cargar las entradas")
        return render_template('error.html', error_message=str(exc)), 500
    except Exception as exc:  # noqa: BLE001
        app.logger.exception("Error inesperado al listar entradas")
        return render_template(
            'error.html',
            error_message="No se pudieron cargar las entradas por un error inesperado.",
        ), 500


@app.route('/expedientes')
def expedientes():
    """Página de listado de expedientes."""

    try:
        storage = get_storage()
        expedientes_list = storage.cargar_expedientes_conocidos()

        # Ordenar por última actuación descendente
        expedientes_list = sorted(
            expedientes_list,
            key=lambda e: _parse_datetime(e.ultima_actuacion),
            reverse=True
        )

        return render_template('expedientes.html', expedientes=expedientes_list)
    except (ConfigurationError, StorageError) as exc:
        app.logger.exception("No se pudieron cargar los expedientes")
        return render_template('error.html', error_message=str(exc)), 500
    except Exception as exc:  # noqa: BLE001
        app.logger.exception("Error inesperado al listar expedientes")
        return render_template(
            'error.html',
            error_message="No se pudieron cargar los expedientes por un error inesperado.",
        ), 500


@app.route('/config')
def config():
    """Página de configuración."""

    try:
        monitor_config = get_monitor_config()
        return render_template('config.html', config=monitor_config)
    except ConfigurationError as exc:
        app.logger.exception("No se pudo cargar la configuración para la vista")
        return render_template('error.html', error_message=str(exc)), 500
    except Exception as exc:  # noqa: BLE001
        app.logger.exception("Fallo inesperado al mostrar la configuración")
        return render_template(
            'error.html',
            error_message="No se pudo cargar la configuración por un error inesperado.",
        ), 500


@app.route('/config/update', methods=['POST'])
def config_update():
    """Actualiza la configuración."""
    try:
        config = get_monitor_config()
        data = request.json or {}
        errors: dict[str, str] = {}

        # Actualizar campos básicos
        if 'modo' in data:
            if data['modo'] in {"automatico", "laboral", "no_laboral"}:
                config.modo = data['modo']
            else:
                errors['modo'] = 'Modo de operación inválido'

        for field in [
            'headless',
            'verificar_entradas',
            'verificar_expedientes',
            'notificar_nuevas_entradas',
            'notificar_cambios_expedientes',
            'notificar_errores',
            'comparacion_automatica',
        ]:
            if field in data:
                config_value = data[field]
                config_value = bool(config_value)
                setattr(config, field, config_value)

        # Actualizar intervalos
        _update_int_field(config, data, 'intervalos_laboral_entradas', errors, min_value=1)
        _update_int_field(config, data, 'intervalos_laboral_expedientes', errors, min_value=1)
        _update_int_field(config, data, 'intervalos_no_laboral_entradas', errors, min_value=1)
        _update_int_field(config, data, 'intervalos_no_laboral_expedientes', errors, min_value=1)

        # Actualizar reintentos
        _update_int_field(config, data, 'max_reintentos_entradas', errors, min_value=1, allow_zero=False)
        _update_int_field(config, data, 'max_reintentos_expedientes', errors, min_value=1, allow_zero=False)
        _update_int_field(config, data, 'espera_reintentos_entradas', errors, min_value=1)
        _update_int_field(config, data, 'espera_reintentos_expedientes', errors, min_value=1)

        # Actualizar horario laboral
        _update_days_field(config, data, errors)
        _update_time_field(config, data, 'hora_inicio', errors)
        _update_time_field(config, data, 'hora_fin', errors)

        # Actualizar filtros de fecha
        if 'fecha_desde_entradas' in data:
            config.fecha_desde_entradas = data['fecha_desde_entradas'] or None
        if 'fecha_hasta_entradas' in data:
            config.fecha_hasta_entradas = data['fecha_hasta_entradas'] or None
        if 'fecha_desde_expedientes' in data:
            config.fecha_desde_expedientes = data['fecha_desde_expedientes'] or None
        if 'fecha_hasta_expedientes' in data:
            config.fecha_hasta_expedientes = data['fecha_hasta_expedientes'] or None
        if 'fecha_corte_expedientes' in data:
            config.fecha_corte_expedientes = data['fecha_corte_expedientes'] or None

        if errors:
            return jsonify({'success': False, 'errors': errors, 'message': 'Revisa los campos indicados'}), 400

        # Guardar configuración
        config.to_file(CONFIG_PATH)

        return jsonify({'success': True, 'message': 'Configuración actualizada correctamente'})

    except ConfigurationError as exc:
        app.logger.exception("No se pudo cargar la configuración existente para actualizar")
        return jsonify({'success': False, 'message': str(exc)}), 500
    except StorageError as exc:
        app.logger.exception("No se pudo acceder al almacenamiento de configuración")
        return jsonify({'success': False, 'message': str(exc)}), 500
    except OSError as exc:
        app.logger.exception("No se pudo guardar la configuración actualizada")
        return jsonify({'success': False, 'message': f'No se pudo escribir el archivo de configuración: {exc}'}), 500
    except Exception as exc:  # noqa: BLE001
        app.logger.exception("Error inesperado al actualizar la configuración")
        return jsonify({'success': False, 'message': 'Error al actualizar configuración'}), 500


@app.route('/config/download', methods=['GET'])
def config_download():
    """Permite descargar el archivo de configuración actual."""

    try:
        if not CONFIG_PATH.exists():
            config_obj = get_monitor_config()
            config_obj.to_file(CONFIG_PATH)

        return send_file(
            CONFIG_PATH,
            mimetype='application/json',
            as_attachment=True,
            download_name='monitor.json'
        )
    except (ConfigurationError, StorageError) as exc:
        app.logger.exception("No se pudo preparar la descarga de configuración")
        return jsonify({'success': False, 'message': str(exc)}), 500
    except OSError as exc:
        app.logger.exception("No se pudo enviar el archivo de configuración")
        return jsonify({'success': False, 'message': f'Error al acceder al archivo: {exc}'}), 500


@app.route('/config/upload', methods=['POST'])
def config_upload():
    """Carga un archivo monitor.json y lo valida antes de persistirlo."""

    if 'config_file' not in request.files:
        return jsonify({'success': False, 'message': 'No se encontró archivo para cargar'}), 400

    uploaded_file = request.files['config_file']
    if uploaded_file.filename == '':
        return jsonify({'success': False, 'message': 'Selecciona un archivo de configuración'}), 400

    try:
        data = json.load(uploaded_file.stream)
    except json.JSONDecodeError as exc:
        return jsonify({'success': False, 'message': f'El archivo no es un JSON válido: {exc}'}), 400

    if not isinstance(data, dict):
        return jsonify({'success': False, 'message': 'El archivo JSON debe contener un objeto de configuración'}), 400

    try:
        new_config = MonitorConfig(**data)
    except TypeError as exc:
        return jsonify({'success': False, 'message': f'Configuración incompatible: {exc}'}), 400
    except MonitorError as exc:
        return jsonify({'success': False, 'message': f'Configuración inválida: {exc}'}), 400

    try:
        new_config.to_file(CONFIG_PATH)
    except OSError as exc:
        app.logger.exception("No se pudo guardar la configuración cargada")
        return jsonify({'success': False, 'message': f'No se pudo guardar el archivo: {exc}'}), 500

    return jsonify({'success': True, 'message': 'Configuración cargada correctamente'})


@app.route('/logs')
def logs():
    """Página de logs."""
    # Por ahora solo mostramos el último archivo de log si existe
    log_path = LOGS_DIR / "monitor.log"

    log_lines = []
    if log_path.exists():
        try:
            with log_path.open('r', encoding='utf-8') as f:
                log_lines = f.readlines()[-100:]  # Últimas 100 líneas
        except OSError as exc:
            app.logger.exception("No se pudo leer el archivo de logs")
            log_lines = [f"Error leyendo log: {exc}"]

    return render_template('logs.html', log_lines=log_lines)


@app.route('/api/stats')
def api_stats():
    """API endpoint para estadísticas actuales."""
    try:
        storage = get_storage()
        estado = storage.cargar_estado()
        entradas = storage.cargar_entradas_conocidas()
        expedientes = storage.cargar_expedientes_conocidos()

        return jsonify({
            'total_entradas': len(entradas),
            'total_expedientes': len(expedientes),
            'ultima_verificacion_entradas': estado.ultima_verificacion_entradas,
            'ultima_verificacion_expedientes': estado.ultima_verificacion_expedientes,
            'errores_entradas': estado.errores_consecutivos_entradas,
            'errores_expedientes': estado.errores_consecutivos_expedientes,
        })
    except (ConfigurationError, StorageError) as exc:
        app.logger.exception("No se pudieron obtener las estadísticas")
        return jsonify({'success': False, 'message': str(exc)}), 500
    except Exception as exc:  # noqa: BLE001
        app.logger.exception("Fallo inesperado al obtener estadísticas")
        return jsonify({'success': False, 'message': 'No se pudieron obtener las estadísticas'}), 500


@app.route('/api/metrics')
def api_metrics():
    """Entrega métricas resumidas para paneles externos."""

    try:
        storage = get_storage()
        entradas = storage.cargar_entradas_conocidas()
        expedientes = storage.cargar_expedientes_conocidos()

        cutoff = datetime.utcnow() - timedelta(hours=24)

        def _normalize(dt: datetime) -> datetime:
            return dt.astimezone(timezone.utc).replace(tzinfo=None) if dt.tzinfo else dt

        entradas_24h = 0
        for entrada in entradas:
            dt = _parse_datetime(entrada.extraida_en or entrada.fecha)
            dt = _normalize(dt)
            if dt >= cutoff:
                entradas_24h += 1

        expedientes_24h = 0
        for expediente in expedientes:
            dt = _parse_datetime(expediente.ultima_actuacion)
            dt = _normalize(dt)
            if dt >= cutoff:
                expedientes_24h += 1

        return jsonify({
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'entradas_total': len(entradas),
            'expedientes_total': len(expedientes),
            'entradas_ultimas_24h': entradas_24h,
            'expedientes_actualizados_24h': expedientes_24h,
        })
    except (ConfigurationError, StorageError) as exc:
        app.logger.exception("No se pudieron obtener las métricas")
        return jsonify({'success': False, 'message': str(exc)}), 500
    except Exception as exc:  # noqa: BLE001
        app.logger.exception("Fallo inesperado al obtener métricas")
        return jsonify({'success': False, 'message': 'No se pudieron obtener las métricas'}), 500


@app.route('/api/activity')
def api_activity():
    """API endpoint para actividad reciente del monitor."""
    try:
        storage = get_storage()
        estado = storage.cargar_estado()

        # Leer últimas líneas del log
        log_path = LOGS_DIR / "monitor.log"
        log_lines = []
        if log_path.exists():
            try:
                with log_path.open('r', encoding='utf-8') as f:
                    all_lines = f.readlines()
                    log_lines = all_lines[-20:]  # Últimas 20 líneas
            except OSError as exc:
                app.logger.exception("No se pudo leer el archivo de logs para actividad")
                log_lines = [f"Error leyendo log: {exc}"]

        return jsonify({
            'ultima_verificacion_entradas': estado.ultima_verificacion_entradas,
            'ultima_verificacion_expedientes': estado.ultima_verificacion_expedientes,
            'errores_entradas': estado.errores_consecutivos_entradas,
            'errores_expedientes': estado.errores_consecutivos_expedientes,
            'log_lines': log_lines
        })
    except (ConfigurationError, StorageError) as exc:
        app.logger.exception("No se pudo obtener la actividad del monitor")
        return jsonify({'success': False, 'message': str(exc)}), 500
    except Exception as exc:  # noqa: BLE001
        app.logger.exception("Fallo inesperado al obtener la actividad")
        return jsonify({'success': False, 'message': 'No se pudo obtener la actividad del monitor'}), 500


# ===== Control del Monitor =====

def get_monitor_status():
    """Obtiene el estado actual del monitor."""
    state = _current_monitor_state()
    return state["status"]  # type: ignore[return-value]


@app.route('/api/monitor/status')
def api_monitor_status():
    """API endpoint para obtener el estado del monitor."""
    try:
        state = _current_monitor_state()
        config_obj = get_monitor_config()

        return jsonify({
            "status": state["status"],
            "running": state["running"],
            "pid": state["pid"],
            "started_at": state["started_at"],
            "source": state["source"],
            "verificar_entradas": config_obj.verificar_entradas,
            "verificar_expedientes": config_obj.verificar_expedientes,
        })
    except ConfigurationError as exc:
        app.logger.exception("No se pudo recuperar la configuración del monitor")
        return jsonify({'success': False, 'message': str(exc)}), 500
    except Exception as exc:  # noqa: BLE001
        app.logger.exception("Fallo inesperado consultando estado del monitor")
        return jsonify({'success': False, 'message': 'No se pudo obtener el estado del monitor'}), 500


@app.route('/api/monitor/verify/entradas', methods=['POST'])
def api_monitor_verify_entradas():
    """Permite ejecutar una verificación manual de entradas."""

    state = _current_monitor_state()
    if state["running"]:
        return jsonify({
            "success": False,
            "message": "Detén el monitor antes de ejecutar una verificación manual.",
        }), 400

    try:
        config_obj = get_monitor_config()
    except ConfigurationError as exc:
        app.logger.exception("No se pudo obtener la configuración para verificar entradas")
        return jsonify({'success': False, 'message': str(exc)}), 500
    except Exception as exc:  # noqa: BLE001
        app.logger.exception("Error inesperado al preparar verificación de entradas")
        return jsonify({'success': False, 'message': 'No se pudo preparar la verificación de entradas'}), 500

    if not config_obj.verificar_entradas:
        return jsonify({
            "success": False,
            "message": "La verificación de entradas está deshabilitada en la configuración.",
        }), 400

    monitor = _build_monitor(config_obj)

    try:
        nuevas = _run_monitor_coroutine(monitor.verificar_entradas())
        cantidad = len(nuevas)
        if cantidad:
            message = f"Se detectaron {cantidad} nuevas entradas."
        else:
            message = "Verificación completada sin nuevas entradas."

        _log_monitor_event("verify_entradas", True, message)

        return jsonify({
            "success": True,
            "message": message,
            "nuevas": cantidad,
            "ultima_verificacion": monitor.estado.ultima_verificacion_entradas,
        })

    except Exception as exc:  # noqa: BLE001
        _log_monitor_event("verify_entradas", False, f"Error en verificación manual: {exc}")
        return jsonify({
            "success": False,
            "message": f"Error al verificar entradas: {exc}",
        }), 500


@app.route('/api/monitor/verify/expedientes', methods=['POST'])
def api_monitor_verify_expedientes():
    """Permite ejecutar una verificación manual de expedientes."""

    state = _current_monitor_state()
    if state["running"]:
        return jsonify({
            "success": False,
            "message": "Detén el monitor antes de ejecutar una verificación manual.",
        }), 400

    try:
        config_obj = get_monitor_config()
    except ConfigurationError as exc:
        app.logger.exception("No se pudo obtener la configuración para verificar expedientes")
        return jsonify({'success': False, 'message': str(exc)}), 500
    except Exception as exc:  # noqa: BLE001
        app.logger.exception("Error inesperado al preparar verificación de expedientes")
        return jsonify({'success': False, 'message': 'No se pudo preparar la verificación de expedientes'}), 500

    if not config_obj.verificar_expedientes:
        return jsonify({
            "success": False,
            "message": "La verificación de expedientes está deshabilitada en la configuración.",
        }), 400

    monitor = _build_monitor(config_obj)

    try:
        cambios = _run_monitor_coroutine(monitor.verificar_expedientes())
        cantidad = len(cambios)
        if cantidad:
            message = f"Se detectaron cambios en {cantidad} expedientes."
        else:
            message = "Verificación completada sin cambios en expedientes."

        _log_monitor_event("verify_expedientes", True, message)

        return jsonify({
            "success": True,
            "message": message,
            "cambios": cantidad,
            "ultima_verificacion": monitor.estado.ultima_verificacion_expedientes,
        })

    except Exception as exc:  # noqa: BLE001
        _log_monitor_event("verify_expedientes", False, f"Error en verificación manual: {exc}")
        return jsonify({
            "success": False,
            "message": f"Error al verificar expedientes: {exc}",
        }), 500


@app.route('/api/monitor/start', methods=['POST'])
def api_monitor_start():
    """API endpoint para iniciar el monitor."""
    global monitor_process

    try:
        with monitor_lock:
            # Verificar si ya está corriendo
            if monitor_process is not None and monitor_process.poll() is None:
                return jsonify({
                    'success': False,
                    'message': 'El monitor ya está en ejecución'
                }), 400

            runtime_info = _load_runtime_info()
            existing_pid = runtime_info.get('pid') if runtime_info else None
            if isinstance(existing_pid, int) and _is_process_alive(existing_pid):
                return jsonify({
                    'success': False,
                    'message': 'Ya se detectó un proceso del monitor activo',
                    'pid': existing_pid,
                    'started_at': runtime_info.get('started_at') if runtime_info else None,
                }), 400

            # Iniciar el proceso del monitor
            creationflags = 0
            if sys.platform == 'win32':
                creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)

            monitor_process = subprocess.Popen(
                [sys.executable, str(MONITOR_SCRIPT)],
                cwd=str(MONITOR_SCRIPT.parent),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags
            )

            started_at = datetime.now(timezone.utc).isoformat()
            _write_runtime_info(monitor_process.pid, started_at)
            _log_monitor_event('start', True, 'Monitor iniciado desde la web', monitor_process.pid)

            return jsonify({
                'success': True,
                'message': 'Monitor iniciado correctamente',
                'pid': monitor_process.pid,
                'started_at': started_at
            })

    except Exception as e:  # noqa: BLE001
        app.logger.exception("Error al iniciar el monitor")
        _log_monitor_event('start', False, f'Error al iniciar monitor: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error al iniciar monitor'
        }), 500


@app.route('/api/monitor/stop', methods=['POST'])
def api_monitor_stop():
    """API endpoint para detener el monitor."""
    global monitor_process

    try:
        with monitor_lock:
            runtime_info = _load_runtime_info()
            started_at = runtime_info.get('started_at') if runtime_info else None

            if monitor_process is None or monitor_process.poll() is not None:
                pid_from_file = runtime_info.get('pid') if runtime_info else None
                if not isinstance(pid_from_file, int) or not _is_process_alive(pid_from_file):
                    _clear_runtime_info()
                    return jsonify({
                        'success': False,
                        'message': 'El monitor no está en ejecución'
                    }), 400

                try:
                    if sys.platform == 'win32':
                        subprocess.run(
                            ['taskkill', '/PID', str(pid_from_file), '/T', '/F'],
                            check=False,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                    else:
                        os.kill(pid_from_file, signal.SIGTERM)
                except Exception as exc:
                    _log_monitor_event('stop', False, f'No se pudo enviar señal al monitor: {exc}', pid_from_file)
                    return jsonify({
                        'success': False,
                        'message': f'No se pudo detener el monitor: {exc}'
                    }), 500

                for _ in range(10):
                    if not _is_process_alive(pid_from_file):
                        break
                    time.sleep(0.5)

                monitor_process = None
                _clear_runtime_info()
                _log_monitor_event('stop', True, 'Monitor detenido desde la web (PID persistido)', pid_from_file)

                return jsonify({
                    'success': True,
                    'message': 'Monitor detenido correctamente',
                    'pid': pid_from_file,
                    'started_at': started_at
                })

            target_pid = monitor_process.pid

            # Terminar el proceso controlado directamente
            if sys.platform == 'win32':
                monitor_process.terminate()
            else:
                monitor_process.send_signal(signal.SIGTERM)

            try:
                monitor_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                monitor_process.kill()
                monitor_process.wait()

            monitor_process = None
            _clear_runtime_info()
            _log_monitor_event('stop', True, 'Monitor detenido desde la web', target_pid)

            return jsonify({
                'success': True,
                'message': 'Monitor detenido correctamente',
                'pid': target_pid,
                'started_at': started_at
            })

    except Exception as e:  # noqa: BLE001
        app.logger.exception("Error al detener el monitor")
        _log_monitor_event('stop', False, f'Error al detener monitor: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error al detener monitor'
        }), 500


if __name__ == '__main__':
    # Permitir configurar el puerto desde variable de entorno
    port = int(os.getenv('FLASK_PORT', '5000'))
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    debug = os.getenv('FLASK_DEBUG', 'true').lower() in ('true', '1', 'yes')

    app.run(debug=debug, host=host, port=port)
