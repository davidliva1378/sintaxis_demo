"""Sistema de logging para Sistema_v5 con soporte de colores y emojis.

Este módulo proporciona un sistema de logging que:
- Mantiene el estilo visual actual con emojis
- Permite control de verbosidad por nivel
- Guarda logs en archivo opcionalmente
- Usa colores en consola para mejor legibilidad
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Literal

# Configuración global
_LOGGERS: dict[str, logging.Logger] = {}
_DEFAULT_LEVEL = logging.INFO


class ColoredFormatter(logging.Formatter):
    """Formatter que agrega colores ANSI a los niveles de log.

    Solo aplica colores si el output es a una terminal (tty).
    """

    # Códigos de color ANSI
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Verde
        'WARNING': '\033[33m',    # Amarillo
        'ERROR': '\033[31m',      # Rojo
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'

    def __init__(self, *args, use_colors: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_colors = use_colors and sys.stdout.isatty()

    def format(self, record: logging.LogRecord) -> str:
        if self.use_colors:
            color = self.COLORS.get(record.levelname, '')
            levelname_colored = f"{color}{record.levelname}{self.RESET}"

            # Guardar el original y restaurar después
            original_levelname = record.levelname
            record.levelname = levelname_colored
            result = super().format(record)
            record.levelname = original_levelname
            return result
        return super().format(record)


def setup_logging(
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] | int = "INFO",
    log_file: str | Path | None = None,
    use_colors: bool = True,
    file_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] | int = "DEBUG",
) -> None:
    """Configura el sistema de logging global para toda la aplicación.

    Args:
        level: Nivel de logging para consola (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Ruta al archivo donde guardar logs (opcional)
        use_colors: Si usar colores en la consola
        file_level: Nivel de logging para archivo (por defecto DEBUG para guardar todo)

    Example:
        >>> setup_logging("INFO")  # Solo INFO y superiores en consola
        >>> setup_logging("DEBUG", log_file="debug.log")  # DEBUG en archivo
        >>> setup_logging("ERROR")  # Solo errores en consola
    """
    global _DEFAULT_LEVEL

    # Convertir nivel string a constante
    if isinstance(level, str):
        level = getattr(logging, level.upper())
    if isinstance(file_level, str):
        file_level = getattr(logging, file_level.upper())

    _DEFAULT_LEVEL = level

    # Configurar logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Captura todo, los handlers filtran
    root_logger.handlers.clear()  # Limpiar handlers existentes

    # Handler para CONSOLA
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # Formato simple para consola (mantiene emojis visibles)
    console_format = ColoredFormatter(
        '%(levelname)s - %(message)s',
        use_colors=use_colors
    )
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)

    # Handler para ARCHIVO (opcional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(file_level)

        # Formato detallado para archivo
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        root_logger.addHandler(file_handler)

    # Silenciar loggers ruidosos de terceros
    logging.getLogger('playwright').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> logging.Logger:
    """Obtiene un logger configurado para el módulo especificado.

    Args:
        name: Nombre del módulo (usa __name__ del módulo que llama)

    Returns:
        Logger configurado

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("📄 Iniciando proceso...")
        >>> logger.debug("Variable x = %s", x)
    """
    if name is None:
        name = __name__

    if name in _LOGGERS:
        return _LOGGERS[name]

    logger = logging.getLogger(name)
    _LOGGERS[name] = logger
    return logger


def configure_from_env() -> None:
    """Configura logging desde variables de entorno.

    Variables soportadas:
        LOG_LEVEL: Nivel de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        LOG_FILE: Ruta al archivo de log
        LOG_COLORS: Si usar colores (true/false, 1/0)

    Example:
        >>> export LOG_LEVEL=DEBUG
        >>> export LOG_FILE=logs/sistema_v5.log
        >>> python script.py
    """
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_file = os.getenv("LOG_FILE")
    use_colors = os.getenv("LOG_COLORS", "true").lower() in {"true", "1", "yes", "y"}

    setup_logging(
        level=level,
        log_file=log_file,
        use_colors=use_colors
    )


# Configuración automática si se importa el módulo
# Usa variables de entorno si existen, sino defaults
if "LOG_LEVEL" in os.environ or "LOG_FILE" in os.environ:
    configure_from_env()
else:
    # Configuración por defecto: INFO en consola con colores
    setup_logging(level="INFO", use_colors=True)
