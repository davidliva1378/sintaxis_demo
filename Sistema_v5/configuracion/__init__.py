"""Configuración centralizada del Sistema PJN.

Este paquete contiene toda la lógica relacionada con configuración:
- Modelos de configuración (SystemConfig, ScrapingConfig, etc.)
- Herramientas CLI para gestionar configuración
- Interfaz gráfica para editar configuración
- Validadores y utilidades de carga

Estructura:
    core/          - Configuraciones principales del sistema
    monitor/       - Configuración específica del monitor
    cli/           - Interfaz de línea de comandos
    gui/           - Interfaz gráfica (Tkinter)
    utils/         - Utilidades compartidas

Ejemplos:
    >>> from Sistema_v5.configuracion.core import SystemConfig
    >>> config = SystemConfig.from_file("config/sistema.json")
    >>> config.modo_monitor
    'automatico'

    >>> from Sistema_v5.configuracion.cli import main as run_config_cli
    >>> run_config_cli(["show", "--format", "json"])
"""

from __future__ import annotations

# Configuraciones principales
from .core.system_config import (
    SystemConfig,
    ModoMonitor,
    ModoComparacion,
    FormatoReporte,
    NivelLog,
)
from .core.scraping_config import (
    Config,
    get_config,
    set_config,
    reset_config,
    ScrapingConfig,
    BrowserConfig,
    AuthConfig,
    ArchivosConfig,
)
from .core.extraccion_config import ExtraccionExpedientesConfig

# Configuración de monitor
from .monitor.config import MonitorConfig
from .monitor.shared_config import MonitorSharedConfig

# Interfaces de usuario
from .gui.config_form import ConfigForm
from .cli.configuracion import main as run_config_cli

# Utilidades
from .utils.env import parse_bool, parse_int, parse_str_list

__all__ = [
    # Core configs
    "SystemConfig",
    "Config",
    "get_config",
    "set_config",
    "reset_config",
    "ScrapingConfig",
    "BrowserConfig",
    "AuthConfig",
    "ArchivosConfig",
    "ExtraccionExpedientesConfig",
    # Monitor configs
    "MonitorConfig",
    "MonitorSharedConfig",
    # Enums/Types
    "ModoMonitor",
    "ModoComparacion",
    "FormatoReporte",
    "NivelLog",
    # User interfaces
    "ConfigForm",
    "run_config_cli",
    # Utilities
    "parse_bool",
    "parse_int",
    "parse_str_list",
]
