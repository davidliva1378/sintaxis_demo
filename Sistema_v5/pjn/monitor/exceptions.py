"""Compatibilidad con imports legacy de exceptions del monitor.

⚠️  DEPRECADO: Este módulo se ha movido a Sistema_v5.configuracion.monitor.exceptions

Por favor actualiza tus imports:
    Antes: from Sistema_v5.pjn.monitor.exceptions import ValidationError
    Ahora:  from Sistema_v5.configuracion.monitor.exceptions import ValidationError

Este wrapper se mantendrá por compatibilidad pero será removido en futuras versiones.
"""

from __future__ import annotations

import warnings

warnings.warn(
    "Importing from pjn.monitor.exceptions is deprecated. "
    "Use 'from Sistema_v5.configuracion.monitor.exceptions import ...' instead.",
    DeprecationWarning,
    stacklevel=2
)

from Sistema_v5.configuracion.monitor.exceptions import (
    ValidationError,
    IntervalError,
    DateRangeError,
    WorkHoursError,
    SchedulerError,
    NotificationError,
    StorageError,
)

__all__ = [
    "ValidationError",
    "IntervalError",
    "DateRangeError",
    "WorkHoursError",
    "SchedulerError",
    "NotificationError",
    "StorageError",
]
