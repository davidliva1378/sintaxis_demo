"""Compatibilidad con imports legacy de configuración de scraping.

⚠️  DEPRECADO: Este módulo se ha movido a Sistema_v5.configuracion.core.scraping_config

Por favor actualiza tus imports:
    Antes: from Sistema_v5.pjn.config import Config, get_config
    Ahora:  from Sistema_v5.configuracion.core.scraping_config import Config, get_config

Este wrapper se mantendrá por compatibilidad pero será removido en futuras versiones.
"""

from __future__ import annotations

import warnings

warnings.warn(
    "Importing from pjn.config is deprecated. "
    "Use 'from Sistema_v5.configuracion.core.scraping_config import Config, get_config' instead.",
    DeprecationWarning,
    stacklevel=2
)

try:
    from ..configuracion.core.scraping_config import (
        ScrapingConfig,
        BrowserConfig,
        AuthConfig,
        ArchivosConfig,
        Config,
        get_config,
        set_config,
        reset_config,
    )
except ImportError:
    from configuracion.core.scraping_config import (
        ScrapingConfig,
        BrowserConfig,
        AuthConfig,
        ArchivosConfig,
        Config,
        get_config,
        set_config,
        reset_config,
    )

__all__ = [
    "ScrapingConfig",
    "BrowserConfig",
    "AuthConfig",
    "ArchivosConfig",
    "Config",
    "get_config",
    "set_config",
    "reset_config",
]
