"""Compatibilidad con imports legacy de validators del monitor.

⚠️  DEPRECADO: Este módulo se ha movido a Sistema_v5.configuracion.monitor.validators

Por favor actualiza tus imports:
    Antes: from Sistema_v5.pjn.monitor.validators import validar_intervalo
    Ahora:  from Sistema_v5.configuracion.monitor.validators import validar_intervalo

Este wrapper se mantendrá por compatibilidad pero será removido en futuras versiones.
"""

from __future__ import annotations

import warnings

warnings.warn(
    "Importing from pjn.monitor.validators is deprecated. "
    "Use 'from Sistema_v5.configuracion.monitor.validators import ...' instead.",
    DeprecationWarning,
    stacklevel=2
)

from Sistema_v5.configuracion.monitor.validators import (
    ValidationError,
    IntervalError,
    DateRangeError,
    WorkHoursError,
    validar_intervalo,
    validar_max_reintentos,
    validar_formato_fecha,
    validar_rango_fechas,
    validar_formato_hora,
    validar_rango_horas,
    validar_dias_laborales,
    validar_directorio,
)

__all__ = [
    "ValidationError",
    "IntervalError",
    "DateRangeError",
    "WorkHoursError",
    "validar_intervalo",
    "validar_max_reintentos",
    "validar_formato_fecha",
    "validar_rango_fechas",
    "validar_formato_hora",
    "validar_rango_horas",
    "validar_dias_laborales",
    "validar_directorio",
]
