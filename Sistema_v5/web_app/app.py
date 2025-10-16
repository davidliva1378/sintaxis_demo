"""Aplicación web Flask para el Monitor PJN.

Esta aplicación proporciona una interfaz web para gestionar y visualizar
el monitoreo de expedientes y entradas del PJN.
"""

from __future__ import annotations

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
sys.path.insert(0, str(Path(__file__).parent.parent))

# noinspection PyUnresolvedReferences
from pjn.monitor.config import MonitorConfig
# noinspection PyUnresolvedReferences
from pjn.monitor.storage import StorageManager

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # Para caracteres UTF-8

# Rutas de configuración
CONFIG_PATH = Path(__file__).parent.parent / "config" / "monitor.json"
MONITOR_SCRIPT = Path(__file__).parent.parent / "ejecutar_monitor_continuo.py"
LOGS_DIR = Path(__file__).parent.parent / "logs"
RUNTIME_INFO_PATH = LOGS_DIR / "monitor_runtime.json"
EVENTS_LOG_PATH = LOGS_DIR / "monitor_web_actions.log"

# Variables globales para control del monitor
monitor_process = None
monitor_lock = Lock()


def get_monitor_config() -> MonitorConfig:
    """Carga la configuración del monitor."""
    return MonitorConfig.from_file(CONFIG_PATH)


def get_storage() -> StorageManager:
    """Obtiene el StorageManager resolviendo rutas relativas al proyecto."""
    config = get_monitor_config()
    data_dir = Path(config.directorio_datos)
    if not data_dir.is_absolute():
        data_dir = Path(__file__).parent.parent / data_dir
    return StorageManager(data_dir)


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

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"pid": pid, "started_at": started_at}
    RUNTIME_INFO_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_runtime_info() -> dict[str, object]:
    """Obtiene los metadatos persistidos del monitor, si existen."""

    if not RUNTIME_INFO_PATH.exists():
        return {}

    try:
        return json.loads(RUNTIME_INFO_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _clear_runtime_info() -> None:
    """Elimina los metadatos persistidos del monitor."""

    try:
        RUNTIME_INFO_PATH.unlink(missing_ok=True)
    except TypeError:
        if RUNTIME_INFO_PATH.exists():
            RUNTIME_INFO_PATH.unlink()


def _log_monitor_event(action: str, success: bool, message: str, pid: int | None = None) -> None:
    """Registra intentos de arranque/detención en un log dedicado."""

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
        except Exception:
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


@app.route('/entradas')
def entradas():
    """Página de listado de entradas."""
    storage = get_storage()
    entradas_list = storage.cargar_entradas_conocidas()

    # Ordenar por fecha descendente
    entradas_list = sorted(
        entradas_list,
        key=lambda e: _parse_datetime(e.fecha),
        reverse=True
    )

    return render_template('entradas.html', entradas=entradas_list)


@app.route('/expedientes')
def expedientes():
    """Página de listado de expedientes."""
    storage = get_storage()
    expedientes_list = storage.cargar_expedientes_conocidos()

    # Ordenar por última actuación descendente
    expedientes_list = sorted(
        expedientes_list,
        key=lambda e: _parse_datetime(e.ultima_actuacion),
        reverse=True
    )

    return render_template('expedientes.html', expedientes=expedientes_list)


@app.route('/config')
def config():
    """Página de configuración."""
    config = get_monitor_config()
    return render_template('config.html', config=config)


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

        if errors:
            return jsonify({'success': False, 'errors': errors, 'message': 'Revisa los campos indicados'}), 400

        # Guardar configuración
        config.to_file(CONFIG_PATH)

        return jsonify({'success': True, 'message': 'Configuración actualizada correctamente'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error al actualizar configuración: {str(e)}'}), 500


@app.route('/config/download', methods=['GET'])
def config_download():
    """Permite descargar el archivo de configuración actual."""

    if not CONFIG_PATH.exists():
        config = get_monitor_config()
        config.to_file(CONFIG_PATH)

    return send_file(
        CONFIG_PATH,
        mimetype='application/json',
        as_attachment=True,
        download_name='monitor.json'
    )


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

    new_config.to_file(CONFIG_PATH)

    return jsonify({'success': True, 'message': 'Configuración cargada correctamente'})


@app.route('/logs')
def logs():
    """Página de logs."""
    # Por ahora solo mostramos el último archivo de log si existe
    log_path = Path(__file__).parent.parent / "logs" / "monitor.log"

    log_lines = []
    if log_path.exists():
        with log_path.open('r', encoding='utf-8') as f:
            log_lines = f.readlines()[-100:]  # Últimas 100 líneas

    return render_template('logs.html', log_lines=log_lines)


@app.route('/api/stats')
def api_stats():
    """API endpoint para estadísticas actuales."""
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


@app.route('/api/metrics')
def api_metrics():
    """Entrega métricas resumidas para paneles externos."""

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


@app.route('/api/activity')
def api_activity():
    """API endpoint para actividad reciente del monitor."""
    storage = get_storage()
    estado = storage.cargar_estado()

    # Leer últimas líneas del log
    log_path = Path(__file__).parent.parent / "logs" / "monitor.log"
    log_lines = []
    if log_path.exists():
        try:
            with log_path.open('r', encoding='utf-8') as f:
                all_lines = f.readlines()
                log_lines = all_lines[-20:]  # Últimas 20 líneas
        except Exception as e:
            log_lines = [f"Error leyendo log: {str(e)}"]

    return jsonify({
        'ultima_verificacion_entradas': estado.ultima_verificacion_entradas,
        'ultima_verificacion_expedientes': estado.ultima_verificacion_expedientes,
        'errores_entradas': estado.errores_consecutivos_entradas,
        'errores_expedientes': estado.errores_consecutivos_expedientes,
        'log_lines': log_lines
    })


# ===== Control del Monitor =====

def get_monitor_status():
    """Obtiene el estado actual del monitor."""
    state = _current_monitor_state()
    return state["status"]  # type: ignore[return-value]


@app.route('/api/monitor/status')
def api_monitor_status():
    """API endpoint para obtener el estado del monitor."""
    state = _current_monitor_state()

    return jsonify({
        "status": state["status"],
        "running": state["running"],
        "pid": state["pid"],
        "started_at": state["started_at"],
        "source": state["source"],
    })


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

    except Exception as e:
        _log_monitor_event('start', False, f'Error al iniciar monitor: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Error al iniciar monitor: {str(e)}'
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

    except Exception as e:
        _log_monitor_event('stop', False, f'Error al detener monitor: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Error al detener monitor: {str(e)}'
        }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
