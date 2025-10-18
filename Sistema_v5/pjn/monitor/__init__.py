"""Módulo de monitoreo automático del portal PJN.

Este módulo proporciona un sistema de monitoreo que verifica periódicamente:
- Nuevas entradas/notificaciones
- Cambios en expedientes (nuevas actuaciones)

El monitor puede ejecutarse como:
- Script CLI sin interfaz gráfica (multiplataforma)
- Aplicación de bandeja del sistema (opcional, requiere pystray + pillow)
"""

from .config import MonitorConfig
from .core import MonitorPJN
from .detector import DetectorCambios
from .notifier import NotificadorPlyer
from .scheduler import SchedulerMonitor
from .storage import EstadoMonitor, StorageManager

# System tray es opcional
try:
    from .tray import MonitorSystemTray, TRAY_AVAILABLE
    __all__ = [
        "MonitorConfig",
        "MonitorPJN",
        "DetectorCambios",
        "NotificadorPlyer",
        "SchedulerMonitor",
        "EstadoMonitor",
        "StorageManager",
        "MonitorSystemTray",
        "TRAY_AVAILABLE",
    ]
except ImportError:
    __all__ = [
        "MonitorConfig",
        "MonitorPJN",
        "DetectorCambios",
        "NotificadorPlyer",
        "SchedulerMonitor",
        "EstadoMonitor",
        "StorageManager",
    ]
