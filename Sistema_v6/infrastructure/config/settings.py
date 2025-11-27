"""Configuración del sistema.

Este módulo centraliza toda la configuración del sistema usando Pydantic Settings.
La configuración se puede cargar desde variables de entorno o archivo .env.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Union, List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Ruta base del proyecto (Sistema_v6)
PROJECT_ROOT = Path(__file__).parent.parent.parent


class AuthSettings(BaseSettings):
    """Configuración de autenticación del PJN.

    Attributes:
        login_url: URL de login del Portal Judicial Nacional
        usuario: Usuario del PJN (desde PJN_USER env var)
        password: Contraseña del PJN (desde PJN_PASSWORD env var)
        session_file_name: Nombre del archivo de sesión de Playwright
        session_timeout_seconds: Timeout de sesión en segundos
    """

    model_config = SettingsConfigDict(env_prefix="PJN_", case_sensitive=False)

    login_url: str = Field(default="https://portalpjn.pjn.gov.ar/inicio", alias="LOGIN_URL")
    usuario: str | None = Field(default=None, alias="USER")
    password: str | None = Field(default=None, alias="PASSWORD")
    session_file_name: str = "pjn_session.json"
    session_timeout_seconds: int = 3600


class BrowserSettings(BaseSettings):
    """Configuración del navegador Playwright.

    Attributes:
        headless: Si True, ejecuta el navegador sin interfaz gráfica
        args: Argumentos adicionales para el navegador
        timeout_ms: Timeout general en milisegundos
        navigation_timeout_ms: Timeout de navegación en milisegundos
        user_agent: User agent personalizado (None para usar default)
        anti_webdriver_script: Script JavaScript para ocultar marcas de automatización
    """

    model_config = SettingsConfigDict(env_prefix="BROWSER_", case_sensitive=False)

    headless: bool = True
    args: list[str] = Field(
        default_factory=lambda: [
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--no-sandbox",
        ]
    )
    timeout_ms: int = 30000
    navigation_timeout_ms: int = 60000
    user_agent: str | None = None
    anti_webdriver_script: str = """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """


class ScrapingSettings(BaseSettings):
    """Configuración de scraping (compatibilidad v5.1.1).

    Attributes:
        timeout_default: Timeout por defecto en ms para operaciones de scraping
        timeout_login: Timeout para operaciones de login en ms
        timeout_descarga: Timeout para descarga de archivos en ms
        timeout_tabla_expedientes: Timeout para tablas de expedientes en ms (sitios lentos)
        timeout_loading_hidden: Timeout para elementos aparecer/desaparecer en ms
        max_paginas_expedientes: Máximo de páginas a extraer (None = sin límite)
        max_reintentos_descarga: Máximo de reintentos para descargas
        caratula_coincidencia_parcial: Si True, permite coincidencia parcial en carátulas
    """

    model_config = SettingsConfigDict(env_prefix="SCRAPING_", case_sensitive=False)

    timeout_default: int = 8000
    timeout_login: int = 60000
    timeout_descarga: int = 30000
    timeout_tabla_expedientes: int = 30000  # 30s para sitios lentos
    timeout_loading_hidden: int = 12000  # 12s para elementos aparecer/desaparecer
    max_paginas_expedientes: int | None = 200
    max_reintentos_descarga: int = 3
    caratula_coincidencia_parcial: bool = True


class StorageSettings(BaseSettings):
    """Configuración de almacenamiento.

    Attributes:
        base_path: Directorio base para almacenamiento de datos
        json_base_file: Nombre del archivo JSON "base" (todos los expedientes)
        json_sistema_file: Nombre del archivo JSON "sistema" (expedientes seleccionados)
        workspaces_dir: Nombre del directorio de workspaces
        downloads_dir: Nombre del directorio de descargas
        pretty_json: Si True, formatea el JSON con indentación
        ensure_ascii: Si True, escapa caracteres no-ASCII en JSON
    """

    model_config = SettingsConfigDict(env_prefix="STORAGE_", case_sensitive=False)

    base_path: Path = Field(default_factory=lambda: PROJECT_ROOT / "data")
    json_base_file: str = "expedientes_base.json"
    json_sistema_file: str = "expedientes_sistema.json"
    workspaces_dir: str = "expedientes"
    downloads_dir: str = "descargas"
    pretty_json: bool = True
    ensure_ascii: bool = False


class MonitoreoSettings(BaseSettings):
    """Configuración de monitoreo.

    Attributes:
        intervalo_segundos: Intervalo entre verificaciones (0 = ejecutar una vez)
        dias_actividad: Días hacia atrás para considerar expediente "activo"
        notificar_cambios: Si True, envía notificaciones cuando hay cambios
        descargar_archivos: Si True, descarga archivos nuevos automáticamente
        max_reintentos: Máximo de reintentos en caso de error
        reintento_delay_segundos: Delay entre reintentos en segundos

        # Configuración avanzada (compatibilidad v5.1.1)
        intervalos_laboral_expedientes: Intervalo en minutos para expedientes en horario laboral
        intervalos_laboral_entradas: Intervalo en minutos para entradas en horario laboral
        intervalos_no_laboral_expedientes: Intervalo en minutos para expedientes fuera de horario laboral
        intervalos_no_laboral_entradas: Intervalo en minutos para entradas fuera de horario laboral
        dias_laborales: Lista de días laborales (lunes, martes, etc.)
        hora_inicio: Hora de inicio del horario laboral (formato HH:MM)
        hora_fin: Hora de fin del horario laboral (formato HH:MM)
        verificar_expedientes: Si True, verifica cambios en expedientes
        verificar_entradas: Si True, verifica nuevas entradas
        tipos_entradas: Tipos de entradas a monitorear (N=Notificaciones, D=Demandas)
        actualizar_actuaciones_auto: Si True, actualiza actuaciones automáticamente al detectar cambios
        max_reintentos_actualizacion: Máximo de reintentos para actualización de actuaciones
    """

    model_config = SettingsConfigDict(env_prefix="MONITOREO_", case_sensitive=False)

    # Configuración básica
    intervalo_segundos: int = 0
    dias_actividad: int = 30
    notificar_cambios: bool = True
    descargar_archivos: bool = True
    max_reintentos: int = 3
    reintento_delay_segundos: int = 60

    # Configuración avanzada (opcional, compatibilidad v5.1.1)
    intervalos_laboral_expedientes: int | None = None
    intervalos_laboral_entradas: int | None = None
    intervalos_no_laboral_expedientes: int | None = None
    intervalos_no_laboral_entradas: int | None = None
    dias_laborales: Union[str, List[str]] = Field(
        default_factory=lambda: ["lunes", "martes", "miercoles", "jueves", "viernes"]
    )

    @field_validator("dias_laborales", mode="before")
    @classmethod
    def parse_dias_laborales(cls, v):
        if isinstance(v, str):
            if not v.strip():
                return ["lunes", "martes", "miercoles", "jueves", "viernes"]
            try:
                import json
                return json.loads(v)
            except json.JSONDecodeError:
                return [d.strip() for d in v.split(",") if d.strip()]
        return v
    hora_inicio: str = "08:00"
    hora_fin: str = "18:00"
    verificar_expedientes: bool = True
    verificar_entradas: bool = True
    tipos_entradas: str = "N"  # N=Notificaciones, D=Demandas, separados por coma
    actualizar_actuaciones_auto: bool = False
    max_reintentos_actualizacion: int = 2

    # Opciones de extracción (para ExtractorMasivo)
    fecha_corte_dias: int | None = 30  # Solo expedientes con actividad en últimos N días
    max_paginas_monitoreo: int | None = 50  # Límite de páginas a extraer
    tiempo_maximo_extraccion: int | None = 600  # Timeout en segundos (10 min)
    detener_en_duplicado: bool = True  # Detener al encontrar expediente repetido
    orden_extraccion: str = "fecha"  # Orden: fecha, caratula, oficina, situacion


class NotificacionesSettings(BaseSettings):
    """Configuración de notificaciones.

    Attributes:
        habilitar_escritorio: Habilitar notificaciones de escritorio
        habilitar_email: Habilitar notificaciones por email
        habilitar_telegram: Habilitar notificaciones por Telegram
        email_smtp_host: Host del servidor SMTP
        email_smtp_port: Puerto del servidor SMTP
        email_from: Dirección de email del remitente
        email_to: Dirección de email del destinatario
        email_password: Contraseña del email (para SMTP)
        telegram_bot_token: Token del bot de Telegram
        telegram_chat_id: Chat ID de Telegram
    """

    model_config = SettingsConfigDict(env_prefix="NOTIF_", case_sensitive=False)

    habilitar_escritorio: bool = True
    habilitar_email: bool = False
    habilitar_telegram: bool = False

    # Email settings
    email_smtp_host: str | None = None
    email_smtp_port: int = 587
    email_from: str | None = None
    email_to: str | None = None
    email_password: str | None = None

    # Telegram settings
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None


class LoggingSettings(BaseSettings):
    """Configuración de logging.

    Attributes:
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Formato de los mensajes de log
        date_format: Formato de las fechas en logs
        log_to_file: Si True, guarda logs en archivo
        log_file: Nombre del archivo de log
        max_bytes: Tamaño máximo del archivo de log antes de rotar
        backup_count: Número de archivos de backup a mantener
    """

    model_config = SettingsConfigDict(env_prefix="LOG_", case_sensitive=False)

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    log_to_file: bool = True
    log_file: str = "sistema_pjn.log"
    max_bytes: int = 10_485_760  # 10 MB
    backup_count: int = 5


class APISettings(BaseSettings):
    """Configuración del servidor API REST.

    Attributes:
        host: Host donde escucha el servidor
        port: Puerto donde escucha el servidor
        reload: Si True, recarga automáticamente al cambiar código (dev)
        workers: Número de workers para el servidor
        cors_origins: Orígenes permitidos para CORS
        api_prefix: Prefijo de la API (ej: "/api/v1")
    """

    model_config = SettingsConfigDict(env_prefix="API_", case_sensitive=False)

    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = False
    workers: int = 1
    cors_origins: Union[str, List[str]] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:3002",
            "http://localhost:5173",
            "http://localhost:5174",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
            "http://127.0.0.1:8080"
        ]
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            if not v.strip():
                return [
                    "http://localhost:3000",
                    "http://localhost:3001",
                    "http://localhost:3002",
                    "http://localhost:5173",
                    "http://localhost:5174",
                    "http://localhost:8080",
                    "http://127.0.0.1:3000",
                    "http://127.0.0.1:3001",
                    "http://127.0.0.1:5173",
                    "http://127.0.0.1:5174",
                    "http://127.0.0.1:8080"
                ]
            try:
                import json
                return json.loads(v)
            except json.JSONDecodeError:
                return [d.strip() for d in v.split(",") if d.strip()]
        return v
    api_prefix: str = "/api/v1"


class MCPSettings(BaseSettings):
    """Configuración del servidor MCP (Model Context Protocol).

    Attributes:
        habilitar: Si True, habilita el servidor MCP
        puerto: Puerto donde escucha el servidor MCP
        mode: Modo del servidor MCP (stdio, http)
        workspace_path: Path del workspace para MCP
        server_name: Nombre del servidor MCP
        enable_pdf_extraction: Si True, habilita extracción de PDFs
        enable_full_text_search: Si True, habilita búsqueda de texto completo
        enable_statistics: Si True, habilita estadísticas
        max_pdf_pages: Límite de páginas por PDF
        max_pdf_size_mb: Tamaño máximo de PDF en MB
    """

    model_config = SettingsConfigDict(env_prefix="MCP_", case_sensitive=False)

    habilitar: bool = True
    puerto: int = 5000
    mode: Literal["stdio", "http"] = "stdio"
    workspace_path: str = "workspace"
    server_name: str = "sintaxis-actuaciones-v6"
    enable_pdf_extraction: bool = True
    enable_full_text_search: bool = True
    enable_statistics: bool = True
    max_pdf_pages: int = 100
    max_pdf_size_mb: int = 50


class JWTSettings(BaseSettings):
    """Configuración de JWT (JSON Web Tokens).

    Attributes:
        secret_key: Clave secreta para firmar los tokens JWT
        algorithm: Algoritmo de firma (HS256, RS256, etc)
        access_token_expire_minutes: Tiempo de expiración del token en minutos
    """

    model_config = SettingsConfigDict(env_prefix="JWT_", case_sensitive=False)

    secret_key: str = "your-secret-key-change-this-in-production-use-env-var"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 horas


class EncryptionSettings(BaseSettings):
    """Configuración de encriptación.

    Attributes:
        fernet_key: Clave Fernet para encriptar credenciales PJN (debe ser base64 de 32 bytes)
    """

    model_config = SettingsConfigDict(env_prefix="ENCRYPTION_", case_sensitive=False)

    fernet_key: str | None = None  # Se genera automáticamente si no se proporciona


class Settings(BaseSettings):
    """Configuración principal del sistema.

    Agrupa todas las configuraciones en una sola clase.
    Se carga automáticamente desde variables de entorno y archivo .env.

    Example:
        >>> settings = Settings()
        >>> print(settings.auth.usuario)
        >>> print(settings.storage.base_path)
    """

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Subsettings
    auth: AuthSettings = Field(default_factory=AuthSettings)
    browser: BrowserSettings = Field(default_factory=BrowserSettings)
    scraping: ScrapingSettings = Field(default_factory=ScrapingSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    monitoreo: MonitoreoSettings = Field(default_factory=MonitoreoSettings)
    notificaciones: NotificacionesSettings = Field(default_factory=NotificacionesSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    api: APISettings = Field(default_factory=APISettings)
    mcp: MCPSettings = Field(default_factory=MCPSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    encryption: EncryptionSettings = Field(default_factory=EncryptionSettings)

    # General settings
    environment: Literal["development", "production", "testing"] = "development"
    debug: bool = False

    # Database URL (se puede configurar via DATABASE_URL env var)
    database_url: str | None = None


# Singleton instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Obtiene la instancia singleton de configuración.

    Returns:
        Instancia de Settings

    Example:
        >>> from infrastructure.config import get_settings
        >>> settings = get_settings()
        >>> print(settings.auth.login_url)
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Recarga la configuración (útil para testing).

    Returns:
        Nueva instancia de Settings
    """
    global _settings
    _settings = Settings()
    return _settings
