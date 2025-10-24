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

# Intentar import relativo primero (cuando Sistema_v5 es un paquete real)
# Si falla, intentar import absoluto (cuando Sistema_v5 está en sys.path)
try:
    from ...configuracion.monitor.exceptions import (
        MonitorError,
        ValidationError,
        IntervalError,
        DateRangeError,
        WorkHoursError,
        SchedulerError,
        NotificationError,
        StorageError,
        ConfigurationError,
        VerificationError,
        AuthenticationError,
        ExtractionError,
        NetworkError,
    )
except ImportError:
    from configuracion.monitor.exceptions import (
        MonitorError,
        ValidationError,
        IntervalError,
        DateRangeError,
        WorkHoursError,
        SchedulerError,
        NotificationError,
        StorageError,
        ConfigurationError,
        VerificationError,
        AuthenticationError,
        ExtractionError,
        NetworkError,
    )

__all__ = [
    "MonitorError",
    "ValidationError",
    "IntervalError",
    "DateRangeError",
    "WorkHoursError",
    "SchedulerError",
    "NotificationError",
    "StorageError",
    "ConfigurationError",
    "VerificationError",
    "AuthenticationError",
    "ExtractionError",
    "NetworkError",
]
