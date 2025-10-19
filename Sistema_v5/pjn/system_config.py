"""Compatibilidad con imports legacy de system_config.

⚠️  DEPRECADO: Este módulo se ha movido a Sistema_v5.configuracion.core.system_config

Por favor actualiza tus imports:
    Antes: from Sistema_v5.pjn.system_config import SystemConfig
    Ahora:  from Sistema_v5.configuracion.core import SystemConfig

Este wrapper se mantendrá por compatibilidad pero será removido en futuras versiones.
"""

from __future__ import annotations

import warnings

warnings.warn(
    "Importing from pjn.system_config is deprecated. "
    "Use 'from Sistema_v5.configuracion.core import SystemConfig' instead.",
    DeprecationWarning,
    stacklevel=2
)

from Sistema_v5.configuracion.core.system_config import (
    SystemConfig,
    ModoMonitor,
    ModoComparacion,
    FormatoReporte,
    NivelLog,
    ENV_FIELD_MAP,
    BOOL_FIELDS,
    INT_FIELDS,
    LIST_FIELDS,
    LOWER_FIELDS,
    UPPER_FIELDS,
    OPTIONAL_STR_FIELDS,
)

__all__ = [
    "SystemConfig",
    "ModoMonitor",
    "ModoComparacion",
    "FormatoReporte",
    "NivelLog",
    "ENV_FIELD_MAP",
    "BOOL_FIELDS",
    "INT_FIELDS",
    "LIST_FIELDS",
    "LOWER_FIELDS",
    "UPPER_FIELDS",
    "OPTIONAL_STR_FIELDS",
]
