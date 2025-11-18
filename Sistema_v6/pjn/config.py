"""Wrapper de configuración para el módulo pjn.

Re-exporta la configuración desde el módulo principal de configuración.
"""

from __future__ import annotations

from infrastructure.config.settings import Settings, get_settings

def get_config() -> Settings:
    """Obtiene la instancia de configuración.

    Returns:
        Settings con estructura anidada (auth, browser, scraping, etc.)
    """
    return get_settings()

__all__ = [
    "Settings",
    "get_config",
    "get_settings",
]