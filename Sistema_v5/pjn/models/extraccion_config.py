"""Compatibilidad con imports legacy de configuración de extracción.

⚠️  DEPRECADO: Este módulo se ha movido a Sistema_v5.configuracion.core.extraccion_config

Por favor actualiza tus imports:
    Antes: from Sistema_v5.pjn.models.extraccion_config import ExtraccionExpedientesConfig
    Ahora:  from Sistema_v5.configuracion.core import ExtraccionExpedientesConfig

Este wrapper se mantendrá por compatibilidad pero será removido en futuras versiones.
"""

from __future__ import annotations

import warnings

warnings.warn(
    "Importing from pjn.models.extraccion_config is deprecated. "
    "Use 'from Sistema_v5.configuracion.core.extraccion_config import ExtraccionExpedientesConfig' instead.",
    DeprecationWarning,
    stacklevel=2
)

from Sistema_v5.configuracion.core.extraccion_config import ExtraccionExpedientesConfig

__all__ = ["ExtraccionExpedientesConfig"]
