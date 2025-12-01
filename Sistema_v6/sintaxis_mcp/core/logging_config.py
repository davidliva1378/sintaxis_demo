"""
Configuración de logging para servidores MCP.

Proporciona:
- Rotación automática de logs (por tamaño)
- Formato consistente
- Diferentes handlers para archivo y consola
- Configuración por niveles
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


# Configuración por defecto
DEFAULT_LOG_DIR = Path("var/logs")
DEFAULT_LOG_FILE = "mcp_server.log"
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
DEFAULT_BACKUP_COUNT = 5
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_mcp_logging(
    log_dir: Optional[Path] = None,
    log_file: str = DEFAULT_LOG_FILE,
    level: int = logging.INFO,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
    console: bool = True,
    logger_name: str = "sintaxis_mcp"
) -> logging.Logger:
    """
    Configura logging para el servidor MCP con rotación.

    Args:
        log_dir: Directorio para logs (default: var/logs)
        log_file: Nombre del archivo de log
        level: Nivel de logging (default: INFO)
        max_bytes: Tamaño máximo antes de rotar (default: 10MB)
        backup_count: Número de backups a mantener (default: 5)
        console: Agregar handler de consola (default: True)
        logger_name: Nombre del logger

    Returns:
        Logger configurado

    Example:
        logger = setup_mcp_logging(level=logging.DEBUG)
        logger.info("Servidor iniciado")
    """
    log_dir = log_dir or DEFAULT_LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / log_file

    # Crear logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    # Evitar duplicados si ya está configurado
    if logger.handlers:
        return logger

    # Formato
    formatter = logging.Formatter(DEFAULT_FORMAT, DEFAULT_DATE_FORMAT)

    # Handler de archivo con rotación
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Handler de consola (opcional)
    if console:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


def get_log_stats(log_dir: Optional[Path] = None, log_file: str = DEFAULT_LOG_FILE) -> dict:
    """
    Obtiene estadísticas del archivo de log.

    Returns:
        Dict con size, backup_count, path, etc.
    """
    log_dir = log_dir or DEFAULT_LOG_DIR
    log_path = log_dir / log_file

    stats = {
        "path": str(log_path),
        "exists": log_path.exists(),
        "backups": []
    }

    if log_path.exists():
        stats["size_bytes"] = log_path.stat().st_size
        stats["size_mb"] = round(stats["size_bytes"] / (1024 * 1024), 2)

    # Buscar backups
    for i in range(1, DEFAULT_BACKUP_COUNT + 1):
        backup_path = log_dir / f"{log_file}.{i}"
        if backup_path.exists():
            stats["backups"].append({
                "name": backup_path.name,
                "size_bytes": backup_path.stat().st_size
            })

    stats["backup_count"] = len(stats["backups"])
    stats["total_size_bytes"] = stats.get("size_bytes", 0) + sum(
        b["size_bytes"] for b in stats["backups"]
    )
    stats["total_size_mb"] = round(stats["total_size_bytes"] / (1024 * 1024), 2)

    return stats


def cleanup_old_logs(log_dir: Optional[Path] = None, keep_count: int = 5) -> int:
    """
    Limpia logs antiguos más allá del límite.

    Args:
        log_dir: Directorio de logs
        keep_count: Número de backups a mantener

    Returns:
        Número de archivos eliminados
    """
    log_dir = log_dir or DEFAULT_LOG_DIR
    deleted = 0

    if not log_dir.exists():
        return 0

    # Buscar todos los logs .log y .log.N
    log_files = sorted(log_dir.glob("*.log*"), key=lambda f: f.stat().st_mtime)

    # Mantener solo los más recientes
    for log_file in log_files[:-keep_count]:
        try:
            log_file.unlink()
            deleted += 1
        except Exception:
            pass

    return deleted


class MCPLogAdapter(logging.LoggerAdapter):
    """
    Adapter para agregar contexto a los logs.

    Example:
        logger = MCPLogAdapter(base_logger, {"tool": "buscar_expedientes"})
        logger.info("Ejecutando búsqueda")
        # Output: ... [tool:buscar_expedientes] Ejecutando búsqueda
    """

    def process(self, msg, kwargs):
        extra = " ".join(f"[{k}:{v}]" for k, v in self.extra.items())
        return f"{extra} {msg}", kwargs
