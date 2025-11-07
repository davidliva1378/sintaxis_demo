"""
Configuración central del Sistema v6.

Este módulo contiene la configuración general del sistema de gestión
de expedientes del Poder Judicial de la Nación (PJN).
"""

from pathlib import Path
from typing import Optional
import os


class Config:
    """Configuración central del sistema."""

    # Directorios base
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / "data"

    # Directorios de datos
    EXPEDIENTES_DIR = DATA_DIR / "expedientes"
    MONITOREO_DIR = DATA_DIR / "monitoreo"
    EXTRACCION_MASIVA_DIR = DATA_DIR / "extraccion_masiva"
    REPORTES_DIR = EXTRACCION_MASIVA_DIR / "reportes"
    LOGS_DIR = EXTRACCION_MASIVA_DIR / "logs"

    # Configuración de sesión Playwright
    SESSION_DIR = BASE_DIR.parent / "web" / "sesion_pjn"
    SESSION_FILE = SESSION_DIR / "Default" / "Cookies"

    # Credenciales PJN (desde variables de entorno)
    PJN_USERNAME = os.getenv("PJN_USERNAME", "")
    PJN_PASSWORD = os.getenv("PJN_PASSWORD", "")

    # Configuración de extracción
    HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
    TIMEOUT_NAVEGACION = 30000  # milisegundos
    DELAY_ENTRE_PAGINAS = 3000  # milisegundos

    # Configuración de extracción masiva
    UMBRAL_ERRORES_CONSECUTIVOS = 5
    MAX_REINTENTOS_POR_EXPEDIENTE = 3
    TIMEOUT_POR_EXPEDIENTE = 120  # segundos

    # Base de datos (si se implementa)
    DATABASE_URL = os.getenv("DATABASE_URL", "")

    # Interfaz web
    WEB_HOST = os.getenv("WEB_HOST", "127.0.0.1")
    WEB_PORT = int(os.getenv("WEB_PORT", "8000"))

    @classmethod
    def init_directories(cls):
        """Crear directorios necesarios si no existen."""
        for dir_path in [
            cls.DATA_DIR,
            cls.EXPEDIENTES_DIR,
            cls.MONITOREO_DIR,
            cls.EXTRACCION_MASIVA_DIR,
            cls.REPORTES_DIR,
            cls.LOGS_DIR,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_session_file(cls) -> Optional[Path]:
        """Obtener ruta del archivo de sesión si existe."""
        if cls.SESSION_FILE.exists():
            return cls.SESSION_FILE
        return None


# Inicializar directorios al importar
Config.init_directories()
