"""Módulo de monitoreo automático del portal PJN.

Este módulo proporciona un sistema de monitoreo que verifica periódicamente:
- Nuevas entradas/notificaciones
- Cambios en expedientes (nuevas actuaciones)

El monitor puede ejecutarse como:
- Script CLI sin interfaz gráfica (multiplataforma)
- Aplicación de bandeja del sistema con UI (opcional, requiere PySide6)
"""

from .config import MonitorConfig
from .core import MonitorPJN
from .detector import DetectorCambios
from .notifier import NotificadorPlyer
from .scheduler import SchedulerMonitor
from .storage import EstadoMonitor, StorageManager

__all__ = [
    "MonitorConfig",
    "MonitorPJN",
    "DetectorCambios",
    "NotificadorPlyer",
    "SchedulerMonitor",
    "EstadoMonitor",
    "StorageManager",
]
