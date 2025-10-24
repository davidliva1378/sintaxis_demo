"""Compatibilidad con imports legacy de config del monitor.

⚠️  DEPRECADO: Este módulo se ha movido a Sistema_v5.configuracion.monitor.config

Por favor actualiza tus imports:
    Antes: from Sistema_v5.pjn.monitor.config import MonitorConfig
    Ahora:  from Sistema_v5.configuracion.monitor import MonitorConfig

Este wrapper se mantendrá por compatibilidad pero será removido en futuras versiones.
"""

from __future__ import annotations

import warnings

warnings.warn(
    "Importing from pjn.monitor.config is deprecated. "
    "Use 'from Sistema_v5.configuracion.monitor import MonitorConfig' instead.",
    DeprecationWarning,
    stacklevel=2
)

try:
    from ...configuracion.monitor.config import MonitorConfig
except ImportError:
    from configuracion.monitor.config import MonitorConfig

__all__ = ["MonitorConfig"]
