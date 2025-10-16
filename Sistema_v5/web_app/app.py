"""Aplicación web Flask para el Monitor PJN.

Esta aplicación proporciona una interfaz web para gestionar y visualizar
el monitoreo de expedientes y entradas del PJN.
"""

from __future__ import annotations

import sys
import subprocess
import signal
from datetime import datetime
from pathlib import Path
from threading import Lock

from flask import Flask, render_template, jsonify, request, redirect, url_for

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
        if 'headless' in data:
            config.headless = data['headless']
        if 'verificar_entradas' in data:
            config.verificar_entradas = data['verificar_entradas']
        if 'verificar_expedientes' in data:
            config.verificar_expedientes = data['verificar_expedientes']

        # Actualizar intervalos
        if 'intervalos_laboral_entradas' in data:
            value = data['intervalos_laboral_entradas']
            if value not in (None, ""):
                try:
                    config.intervalos_laboral_entradas = int(value)
                except (TypeError, ValueError):
                    errors['intervalos_laboral_entradas'] = 'Debe ser un número entero'
        if 'intervalos_laboral_expedientes' in data:
            value = data['intervalos_laboral_expedientes']
            if value not in (None, ""):
                try:
                    config.intervalos_laboral_expedientes = int(value)
                except (TypeError, ValueError):
                    errors['intervalos_laboral_expedientes'] = 'Debe ser un número entero'

        # Actualizar notificaciones
        if 'notificar_nuevas_entradas' in data:
            config.notificar_nuevas_entradas = data['notificar_nuevas_entradas']
        if 'notificar_cambios_expedientes' in data:
            config.notificar_cambios_expedientes = data['notificar_cambios_expedientes']
        if 'notificar_errores' in data:
            config.notificar_errores = data['notificar_errores']

        # Actualizar filtros de fecha
        if 'fecha_desde_entradas' in data:
            config.fecha_desde_entradas = data['fecha_desde_entradas'] or None
        if 'fecha_hasta_entradas' in data:
            config.fecha_hasta_entradas = data['fecha_hasta_entradas'] or None
        if 'fecha_desde_expedientes' in data:
            config.fecha_desde_expedientes = data['fecha_desde_expedientes'] or None

        if errors:
            return jsonify({'success': False, 'errors': errors, 'message': 'Revisa los campos indicados'}), 400

        # Guardar configuración
        config.to_file(CONFIG_PATH)

        return jsonify({'success': True, 'message': 'Configuración actualizada correctamente'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error al actualizar configuración: {str(e)}'}), 500


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
    global monitor_process

    with monitor_lock:
        if monitor_process is None:
            return 'stopped'

        # Verificar si el proceso sigue corriendo
        poll = monitor_process.poll()
        if poll is None:
            return 'running'
        else:
            monitor_process = None
            return 'stopped'


@app.route('/api/monitor/status')
def api_monitor_status():
    """API endpoint para obtener el estado del monitor."""
    status = get_monitor_status()

    return jsonify({
        'status': status,
        'running': status == 'running'
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

            # Iniciar el proceso del monitor
            creationflags = 0
            if sys.platform == 'win32':
                creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)

            monitor_process = subprocess.Popen(
                [sys.executable, str(MONITOR_SCRIPT)],
                cwd=str(MONITOR_SCRIPT.parent),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creationflags
            )

            return jsonify({
                'success': True,
                'message': 'Monitor iniciado correctamente',
                'pid': monitor_process.pid
            })

    except Exception as e:
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
            if monitor_process is None or monitor_process.poll() is not None:
                return jsonify({
                    'success': False,
                    'message': 'El monitor no está en ejecución'
                }), 400

            # Terminar el proceso
            if sys.platform == 'win32':
                # En Windows, enviar señal de terminación
                monitor_process.terminate()
            else:
                # En Unix, enviar SIGTERM
                monitor_process.send_signal(signal.SIGTERM)

            # Esperar a que termine (máximo 5 segundos)
            try:
                monitor_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Si no termina, forzar kill
                monitor_process.kill()
                monitor_process.wait()

            monitor_process = None

            return jsonify({
                'success': True,
                'message': 'Monitor detenido correctamente'
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al detener monitor: {str(e)}'
        }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
