"""Configuration module.

Este módulo centraliza la configuración del sistema usando Pydantic Settings.
"""

from .settings import (
    APISettings,
    AuthSettings,
    BrowserSettings,
    LoggingSettings,
    MCPSettings,
    MonitoreoSettings,
    NotificacionesSettings,
    Settings,
    StorageSettings,
    get_settings,
    reload_settings,
)
from .hardware_profiles import (
    HardwareProfile,
    HardwareProfileType,
    HARDWARE_PROFILES,
    get_hardware_profile,
    get_active_profile,
    set_active_profile,
    get_device,
    get_profile_info,
)

__all__ = [
    "Settings",
    "AuthSettings",
    "BrowserSettings",
    "StorageSettings",
    "MonitoreoSettings",
    "NotificacionesSettings",
    "LoggingSettings",
    "APISettings",
    "MCPSettings",
    "get_settings",
    "reload_settings",
    # Hardware profiles
    "HardwareProfile",
    "HardwareProfileType",
    "HARDWARE_PROFILES",
    "get_hardware_profile",
    "get_active_profile",
    "set_active_profile",
    "get_device",
    "get_profile_info",
]
