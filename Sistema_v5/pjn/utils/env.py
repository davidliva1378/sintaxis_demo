"""Compatibilidad con imports legacy de utilidades de entorno.

⚠️  DEPRECADO: Este módulo se ha movido a Sistema_v5.configuracion.utils.env

Por favor actualiza tus imports:
    Antes: from Sistema_v5.pjn.utils.env import parse_bool
    Ahora:  from Sistema_v5.configuracion.utils.env import parse_bool

Este wrapper se mantendrá por compatibilidad pero será removido en futuras versiones.
"""

from __future__ import annotations

import warnings

warnings.warn(
    "Importing from pjn.utils.env is deprecated. "
    "Use 'from Sistema_v5.configuracion.utils.env import ...' instead.",
    DeprecationWarning,
    stacklevel=2
)

from Sistema_v5.configuracion.utils.env import (
    parse_bool,
    parse_int,
    parse_str_list,
)

__all__ = ["parse_bool", "parse_int", "parse_str_list"]
