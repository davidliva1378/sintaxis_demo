"""Compatibilidad con imports legacy de shared_config del monitor.

⚠️  DEPRECADO: Este módulo se ha movido a Sistema_v5.configuracion.monitor.shared_config

Por favor actualiza tus imports:
    Antes: from Sistema_v5.pjn.monitor.shared_config import MonitorSharedConfig
    Ahora:  from Sistema_v5.configuracion.monitor import MonitorSharedConfig

Este wrapper se mantendrá por compatibilidad pero será removido en futuras versiones.
"""

from __future__ import annotations

import warnings

warnings.warn(
    "Importing from pjn.monitor.shared_config is deprecated. "
    "Use 'from Sistema_v5.configuracion.monitor import MonitorSharedConfig' instead.",
    DeprecationWarning,
    stacklevel=2
)

from Sistema_v5.configuracion.monitor.shared_config import (
    ModoMonitor,
    MonitorSharedConfig,
)

__all__ = ["ModoMonitor", "MonitorSharedConfig"]
