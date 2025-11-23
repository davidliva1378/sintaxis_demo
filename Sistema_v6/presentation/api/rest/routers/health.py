"""Health Check Router - Endpoints de estado del sistema."""

from __future__ import annotations

import logging
import shutil
import psutil
from pathlib import Path

from fastapi import APIRouter, status

from infrastructure.config import get_settings
from infrastructure.persistence.database import (
    test_mysql_connection,
    get_mysql_pool_status,
    get_native_pool_status,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint completo.

    Returns:
        Dict con estado del sistema incluyendo BD, disco y memoria
    """
    settings = get_settings()

    # Verificar base_path
    base_path_exists = settings.storage.base_path.exists()

    # Verificar MySQL
    mysql_ok = test_mysql_connection()

    # Estado del pool MySQL
    pool_status = get_mysql_pool_status()

    # Espacio en disco
    disk_usage = shutil.disk_usage(settings.storage.base_path if base_path_exists else "/")
    disk_free_gb = disk_usage.free / (1024 ** 3)
    disk_total_gb = disk_usage.total / (1024 ** 3)
    disk_percent_used = (disk_usage.used / disk_usage.total) * 100

    # Memoria
    memory = psutil.virtual_memory()
    memory_available_gb = memory.available / (1024 ** 3)
    memory_percent_used = memory.percent

    # Determinar estado general
    issues = []
    if not base_path_exists:
        issues.append("base_path_missing")
    if not mysql_ok:
        issues.append("mysql_unavailable")
    if disk_percent_used > 90:
        issues.append("disk_space_critical")
    if memory_percent_used > 90:
        issues.append("memory_critical")

    if issues:
        status_str = "degraded"
    else:
        status_str = "healthy"

    return {
        "status": status_str,
        "version": "6.0.0",
        "checks": {
            "storage": {
                "base_path": str(settings.storage.base_path),
                "exists": base_path_exists,
            },
            "database": {
                "mysql_connected": mysql_ok,
                "pool": pool_status,
            },
            "disk": {
                "free_gb": round(disk_free_gb, 2),
                "total_gb": round(disk_total_gb, 2),
                "percent_used": round(disk_percent_used, 1),
            },
            "memory": {
                "available_gb": round(memory_available_gb, 2),
                "percent_used": round(memory_percent_used, 1),
            },
        },
        "issues": issues if issues else None,
    }


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_check():
    """Readiness check - verifica si el sistema está listo para recibir requests.

    Returns:
        Dict con estado de preparación
    """
    settings = get_settings()

    # Verificaciones críticas para readiness
    checks = {
        "base_path": settings.storage.base_path.exists(),
        "config_loaded": True,
        "mysql_connected": test_mysql_connection(),
    }

    all_ready = all(checks.values())

    return {
        "ready": all_ready,
        "checks": checks,
    }


@router.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_check():
    """Liveness check - verifica si la aplicación está viva.

    Returns:
        Dict simple con estado
    """
    return {"alive": True}


@router.get("/health/detailed", status_code=status.HTTP_200_OK)
async def detailed_health_check():
    """Health check detallado con información adicional del sistema.

    Returns:
        Dict con información completa del sistema
    """
    settings = get_settings()

    # Información básica
    base_path_exists = settings.storage.base_path.exists()

    # MySQL
    mysql_ok = test_mysql_connection()
    sqlalchemy_pool = get_mysql_pool_status()
    native_pool = get_native_pool_status()

    # Disco
    disk_usage = shutil.disk_usage(settings.storage.base_path if base_path_exists else "/")

    # Memoria
    memory = psutil.virtual_memory()

    # CPU
    cpu_percent = psutil.cpu_percent(interval=0.1)

    # Procesos
    process = psutil.Process()
    process_memory = process.memory_info()

    return {
        "version": "6.0.0",
        "storage": {
            "base_path": str(settings.storage.base_path),
            "exists": base_path_exists,
        },
        "database": {
            "mysql_connected": mysql_ok,
            "pools": {
                "sqlalchemy": sqlalchemy_pool,
                "native": native_pool,
            },
        },
        "system": {
            "disk": {
                "free_bytes": disk_usage.free,
                "total_bytes": disk_usage.total,
                "used_bytes": disk_usage.used,
                "free_gb": round(disk_usage.free / (1024 ** 3), 2),
                "percent_used": round((disk_usage.used / disk_usage.total) * 100, 1),
            },
            "memory": {
                "total_bytes": memory.total,
                "available_bytes": memory.available,
                "percent_used": memory.percent,
                "available_gb": round(memory.available / (1024 ** 3), 2),
            },
            "cpu": {
                "percent_used": cpu_percent,
            },
        },
        "process": {
            "memory_rss_mb": round(process_memory.rss / (1024 ** 2), 2),
            "memory_vms_mb": round(process_memory.vms / (1024 ** 2), 2),
        },
    }
