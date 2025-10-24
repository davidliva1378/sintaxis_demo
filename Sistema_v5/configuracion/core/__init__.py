"""Configuraciones core del Sistema PJN.

Este módulo contiene las configuraciones fundamentales del sistema:
- SystemConfig: Configuración unificada del sistema completo
- ScrapingConfig: Configuración específica de scraping/browser
- ExtraccionExpedientesConfig: Configuración de extracción de expedientes
"""

from __future__ import annotations

from .system_config import (
    SystemConfig,
    ModoMonitor,
    ModoComparacion,
    FormatoReporte,
    NivelLog,
)
from .scraping_config import (
    Config,
    get_config,
    set_config,
    reset_config,
    ScrapingConfig,
    BrowserConfig,
    AuthConfig,
    ArchivosConfig,
)
from .extraccion_config import ExtraccionExpedientesConfig

__all__ = [
    "SystemConfig",
    "ModoMonitor",
    "ModoComparacion",
    "FormatoReporte",
    "NivelLog",
    "Config",
    "get_config",
    "set_config",
    "reset_config",
    "ScrapingConfig",
    "BrowserConfig",
    "AuthConfig",
    "ArchivosConfig",
    "ExtraccionExpedientesConfig",
]
