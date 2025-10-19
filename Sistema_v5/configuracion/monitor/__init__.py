"""Configuración del módulo de monitoreo.

Este módulo contiene configuraciones específicas del sistema de monitoreo:
- MonitorConfig: Configuración del monitor (legacy wrapper)
- MonitorSharedConfig: Configuración base compartida
- Validadores de configuración
"""

from __future__ import annotations

from .config import MonitorConfig
from .shared_config import MonitorSharedConfig, ModoMonitor

__all__ = ["MonitorConfig", "MonitorSharedConfig", "ModoMonitor"]
