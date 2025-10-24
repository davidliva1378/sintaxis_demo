"""Configuración centralizada para Sistema_v5.

Este módulo centraliza todas las configuraciones que antes estaban dispersas
como constantes hardcodeadas en múltiples archivos. Permite:

- Ajustar configuraciones desde un único lugar
- Override mediante variables de entorno
- Testing más fácil
- Personalización por entorno (dev, prod, testing)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Sequence


def _env_bool(nombre: str, default: bool) -> bool:
    """Obtiene un valor booleano desde el entorno."""

    valor = os.getenv(nombre)
    if valor is None:
        return default

    return valor.strip().lower() in {"1", "true", "yes", "y", "t"}


# ============================================================================
# CONFIGURACIÓN DE SCRAPING
# ============================================================================

@dataclass
class ScrapingConfig:
    """Configuraciones generales para scraping del portal PJN."""

    # Paginación
    expedientes_por_pagina: int = 15
    """Cantidad de expedientes mostrados por página en el listado."""

    max_paginas_expedientes: int = 200
    """Límite máximo de páginas a recorrer en búsquedas de expedientes."""

    max_iteraciones_scroll: int = 500
    """Límite de iteraciones de scroll para listas virtualizadas (entradas)."""

    # Timeouts (en milisegundos)
    timeout_default: int = 8_000
    """Timeout por defecto para operaciones de scraping."""

    timeout_selector: int = 8_000
    """Timeout para esperar selectores CSS."""

    timeout_login: int = 60_000
    """Timeout para proceso de autenticación."""

    timeout_tabla_expedientes: int = 25_000
    """Timeout para carga de tabla de expedientes."""

    timeout_actuaciones: int = 8_000
    """Timeout para carga de tabla de actuaciones."""

    timeout_descarga: int = 30_000
    """Timeout para descarga de archivos individuales."""

    timeout_pagina_cambio: int = 8_000
    """Timeout para detectar cambio de página tras navegación."""

    timeout_contenedor_entradas: int = 15_000
    """Timeout para contenedor de entradas (lista virtualizada)."""

    timeout_loading_hidden: int = 10_000
    """Timeout para esperar que desaparezca el indicador de carga."""

    # Filtros y normalizaciones
    caratula_coincidencia_parcial: bool = True
    """Si ``True``, permite coincidencias parciales al filtrar carátulas."""

    # Reintentos
    max_reintentos_descarga: int = 3
    """Número máximo de reintentos para descargas fallidas."""

    delay_entre_reintentos: int = 4_000
    """Delay en milisegundos entre reintentos (convertir a segundos en uso)."""

    # Polling para cambios de página
    poll_interval_cambio_pagina: int = 400
    """Intervalo de polling en ms para detectar cambios de página."""

    max_wait_cambio_pagina: int = 12_000
    """Tiempo máximo de espera para cambio de página en ms."""

    # Scroll (para entradas)
    scroll_tolerance: int = 24
    """Tolerancia en píxeles para detectar "cerca del fondo"."""

    scroll_wheel_delta: int = 900
    """Delta para eventos de scroll wheel."""

    @classmethod
    def from_env(cls) -> ScrapingConfig:
        """Crea configuración desde variables de entorno.

        Variables soportadas:
        - PJN_MAX_PAGINAS: int
        - PJN_TIMEOUT_DEFAULT: int (ms)
        - PJN_TIMEOUT_LOGIN: int (ms)
        - PJN_MAX_REINTENTOS_DESCARGA: int

        Returns:
            ScrapingConfig: Instancia con valores desde env o defaults.
        """
        return cls(
            max_paginas_expedientes=int(
                os.getenv("PJN_MAX_PAGINAS", cls.max_paginas_expedientes)
            ),
            timeout_default=int(
                os.getenv("PJN_TIMEOUT_DEFAULT", cls.timeout_default)
            ),
            timeout_login=int(
                os.getenv("PJN_TIMEOUT_LOGIN", cls.timeout_login)
            ),
            max_reintentos_descarga=int(
                os.getenv("PJN_MAX_REINTENTOS_DESCARGA", cls.max_reintentos_descarga)
            ),
            caratula_coincidencia_parcial=_env_bool(
                "PJN_COINCIDENCIA_CARATULA_PARCIAL",
                cls.caratula_coincidencia_parcial,
            ),
        )


# ============================================================================
# CONFIGURACIÓN DE BROWSER
# ============================================================================

@dataclass
class BrowserConfig:
    """Configuración del browser Playwright."""

    headless: bool = False
    """Si True, ejecuta el browser en modo headless."""

    args: Sequence[str] = field(default_factory=lambda: [
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
    ])
    """Argumentos adicionales para el browser."""

    anti_webdriver_script: str = (
        "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
    )
    """Script para ocultar detección de webdriver."""

    @classmethod
    def from_env(cls) -> BrowserConfig:
        """Crea configuración desde variables de entorno.

        Variables soportadas:
        - PJN_HEADLESS: 1/true/yes/y para True

        Returns:
            BrowserConfig: Instancia con valores desde env o defaults.
        """
        headless_env = os.getenv("PJN_HEADLESS", "false").lower()
        return cls(
            headless=headless_env in {"1", "true", "yes", "y"}
        )


# ============================================================================
# CONFIGURACIÓN DE AUTENTICACIÓN
# ============================================================================

@dataclass
class AuthConfig:
    """Configuración de autenticación."""

    login_url: str = "https://portalpjn.pjn.gov.ar/inicio"
    """URL de login del portal PJN."""

    session_file_name: str = "pjn_storage_state.json"
    """Nombre del archivo de sesión (storage state)."""

    @classmethod
    def from_env(cls) -> AuthConfig:
        """Crea configuración desde variables de entorno.

        Variables soportadas:
        - PJN_LOGIN_URL: str

        Returns:
            AuthConfig: Instancia con valores desde env o defaults.
        """
        return cls(
            login_url=os.getenv("PJN_LOGIN_URL", cls.login_url)
        )


# ============================================================================
# CONFIGURACIÓN DE ARCHIVOS
# ============================================================================

@dataclass
class ArchivosConfig:
    """Configuración para manejo de archivos descargados."""

    directorio_base_actuaciones: str = "ActuacionesCompletas"
    """Carpeta base para guardar actuaciones extraídas."""

    directorio_base_entradas: str = "datos_extraidos/monitoreo"
    """Carpeta base para guardar entradas monitoreadas."""

    prefijo_archivo_actuaciones: str = "actuaciones-"
    """Prefijo para archivos JSON de actuaciones."""

    prefijo_archivo_entradas: str = "historial_notificaciones"
    """Prefijo para archivos de entradas."""

    extension_default: str = ".pdf"
    """Extensión por defecto para archivos sin tipo conocido."""

    extensiones_genericas: frozenset[str] = field(default_factory=lambda: frozenset({
        ".bin", ".file", ".dat", ".tmp"
    }))
    """Extensiones genéricas a evitar (usar tipo real si está disponible)."""

    @classmethod
    def from_env(cls) -> ArchivosConfig:
        """Crea configuración desde variables de entorno.

        Variables soportadas:
        - PJN_DIR_ACTUACIONES: str
        - PJN_DIR_ENTRADAS: str

        Returns:
            ArchivosConfig: Instancia con valores desde env o defaults.
        """
        return cls(
            directorio_base_actuaciones=os.getenv(
                "PJN_DIR_ACTUACIONES",
                cls.directorio_base_actuaciones
            ),
            directorio_base_entradas=os.getenv(
                "PJN_DIR_ENTRADAS",
                cls.directorio_base_entradas
            ),
        )


# ============================================================================
# CONFIGURACIÓN GLOBAL
# ============================================================================

@dataclass
class Config:
    """Configuración global del sistema."""

    scraping: ScrapingConfig = field(default_factory=ScrapingConfig)
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)
    archivos: ArchivosConfig = field(default_factory=ArchivosConfig)

    @classmethod
    def from_env(cls) -> Config:
        """Crea configuración completa desde variables de entorno.

        Returns:
            Config: Instancia con todos los sub-configs desde env.
        """
        return cls(
            scraping=ScrapingConfig.from_env(),
            browser=BrowserConfig.from_env(),
            auth=AuthConfig.from_env(),
            archivos=ArchivosConfig.from_env(),
        )

    @classmethod
    def for_testing(cls) -> Config:
        """Crea configuración optimizada para testing.

        Returns:
            Config: Instancia con timeouts reducidos y límites bajos.
        """
        return cls(
            scraping=ScrapingConfig(
                max_paginas_expedientes=10,
                max_iteraciones_scroll=50,
                timeout_default=2_000,
                timeout_login=10_000,
                max_reintentos_descarga=1,
            ),
            browser=BrowserConfig(
                headless=True,
            ),
        )


# ============================================================================
# INSTANCIA GLOBAL (lazy loading)
# ============================================================================

_config: Config | None = None


def get_config() -> Config:
    """Obtiene la instancia global de configuración (singleton lazy).

    La primera llamada crea la instancia desde variables de entorno.
    Llamadas subsecuentes retornan la misma instancia.

    Returns:
        Config: Instancia global de configuración.

    Example:
        >>> from pjn.config import get_config
        >>> config = get_config()
        >>> print(config.scraping.timeout_default)
        8000
    """
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def set_config(config: Config) -> None:
    """Establece manualmente la configuración global.

    Útil para testing o personalización avanzada.

    Args:
        config: Instancia de Config a usar globalmente.

    Example:
        >>> from pjn.config import set_config, Config
        >>> set_config(Config.for_testing())
    """
    global _config
    _config = config


def reset_config() -> None:
    """Resetea la configuración global (fuerza recarga en próxima llamada).

    Útil principalmente para testing.
    """
    global _config
    _config = None


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "Config",
    "ScrapingConfig",
    "BrowserConfig",
    "AuthConfig",
    "ArchivosConfig",
    "get_config",
    "set_config",
    "reset_config",
]
