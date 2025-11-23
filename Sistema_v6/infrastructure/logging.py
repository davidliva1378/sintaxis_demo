"""Configuración centralizada de logging para el Sistema PJN v6.

Este módulo proporciona:
- Configuración unificada desde LoggingSettings
- Rotación de archivos automática
- Formato consistente en toda la aplicación
- Niveles de log configurables por módulo
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from infrastructure.config import get_settings


def setup_logging() -> None:
    """Configura el logging centralizado de la aplicación.

    Debe llamarse una sola vez al inicio de la aplicación.
    Configura handlers para consola y archivo (si está habilitado).
    """
    settings = get_settings()
    log_settings = settings.logging

    # Obtener nivel de logging
    log_level = getattr(logging, log_settings.level, logging.INFO)

    # Configurar logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Limpiar handlers existentes para evitar duplicados
    root_logger.handlers.clear()

    # Crear formatter
    formatter = logging.Formatter(
        fmt=log_settings.format,
        datefmt=log_settings.date_format
    )

    # Handler de consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Handler de archivo (si está habilitado)
    if log_settings.log_to_file:
        # Asegurar que existe el directorio de logs
        log_dir = Path(settings.storage.base_path) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / log_settings.log_file

        file_handler = RotatingFileHandler(
            filename=str(log_path),
            maxBytes=log_settings.max_bytes,
            backupCount=log_settings.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        logging.info(f"Logging configurado: archivo en {log_path}")

    # Reducir verbosidad de librerías externas
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("watchfiles").setLevel(logging.WARNING)
    logging.getLogger("mysql.connector").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logging.info(f"Sistema de logging inicializado (nivel: {log_settings.level})")


def get_logger(name: str) -> logging.Logger:
    """Obtiene un logger con el nombre especificado.

    Args:
        name: Nombre del logger (normalmente __name__)

    Returns:
        Logger configurado

    Example:
        from infrastructure.logging import get_logger
        logger = get_logger(__name__)
        logger.info("Mensaje de ejemplo")
    """
    return logging.getLogger(name)
