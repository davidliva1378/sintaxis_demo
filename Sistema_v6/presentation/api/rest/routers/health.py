"""Health Check Router - Endpoints de estado del sistema."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, status

from infrastructure.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint.

    Returns:
        Dict con estado del sistema
    """
    settings = get_settings()

    # Verificar que base_path existe
    base_path_exists = settings.storage.base_path.exists()

    return {
        "status": "healthy" if base_path_exists else "degraded",
        "version": "6.0.0",
        "base_path": str(settings.storage.base_path),
        "base_path_exists": base_path_exists,
    }


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_check():
    """Readiness check - verifica si el sistema está listo para recibir requests.

    Returns:
        Dict con estado de preparación
    """
    settings = get_settings()

    # Verificaciones básicas
    checks = {
        "base_path": settings.storage.base_path.exists(),
        "config_loaded": True,
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
