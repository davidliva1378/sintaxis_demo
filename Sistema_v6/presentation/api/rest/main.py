"""REST API con FastAPI - Sistema PJN v6.

Este módulo implementa una API REST completa para el Sistema PJN v6,
exponiendo todos los use cases a través de endpoints HTTP.

Arquitectura:
    - FastAPI para el framework web
    - Pydantic para validación de datos
    - Dependency Injection para use cases
    - CORS configurado desde settings
    - Middleware de logging y error handling
    - Autenticación JWT para multi-usuario

Endpoints:
    Auth:
    - POST /api/v1/auth/register - Registra un nuevo usuario
    - POST /api/v1/auth/login - Login de usuario (devuelve token JWT)
    - GET /api/v1/auth/me - Obtiene información del usuario actual
    - PUT /api/v1/auth/credentials - Actualiza credenciales PJN del usuario
    - GET /api/v1/auth/credentials - Obtiene credenciales PJN del usuario
    - DELETE /api/v1/auth/credentials - Elimina credenciales PJN del usuario

    Expedientes:
    - POST /api/v1/expedientes/extraer - Extrae expedientes del PJN
    - POST /api/v1/expedientes/filtrar - Filtra expedientes
    - GET /api/v1/expedientes - Lista expedientes
    - GET /api/v1/expedientes/{numero} - Obtiene un expediente
    - GET /api/v1/actuaciones/{numero} - Obtiene actuaciones

    Extracción Masiva:
    - POST /api/v1/expedientes/extraer/masivo - Inicia extracción masiva
    - GET /api/v1/expedientes/extraer/{session_id}/progreso - Obtiene progreso
    - POST /api/v1/expedientes/extraer/{session_id}/pausar - Pausa extracción
    - POST /api/v1/expedientes/extraer/{session_id}/reanudar - Reanuda extracción
    - POST /api/v1/expedientes/extraer/{session_id}/cancelar - Cancela extracción
    - GET /api/v1/expedientes/extraer/{session_id}/resumen - Obtiene resumen
    - GET /api/v1/expedientes/extraer/{session_id}/descargar/{formato} - Descarga reporte
    - WS /api/v1/expedientes/extraer/{session_id}/ws - WebSocket para progreso

    Workspaces:
    - POST /api/v1/workspaces/crear - Crea workspaces

    Monitoreo:
    - POST /api/v1/monitoreo/iniciar - Inicia monitoreo

    Otros:
    - GET /api/v1/health - Health check
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from infrastructure.config import get_settings
from infrastructure.di_container import get_container
from infrastructure.exceptions import PJNError

from .routers import (
    admin,
    auth,
    config,
    expedientes,
    extraccion_masiva,
    health,
    monitoreo,
    procesamiento,
    workspaces,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Maneja el ciclo de vida de la aplicación.

    Se ejecuta al inicio y al final de la aplicación.
    """
    # Startup
    logger.info("Iniciando Sistema PJN API v6...")
    settings = get_settings()
    logger.info(f"API configurada en: {settings.api.host}:{settings.api.port}")
    logger.info(f"Base path: {settings.storage.base_path}")

    yield

    # Shutdown
    logger.info("Cerrando Sistema PJN API v6...")
    container = get_container()
    container.cleanup()


# Crear aplicación FastAPI
app = FastAPI(
    title="Sistema PJN API",
    description="API REST para extracción y monitoreo del Portal Judicial Nacional (Argentina)",
    version="6.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configurar CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Middleware de Error Handling ===

@app.exception_handler(PJNError)
async def pjn_error_handler(request: Request, exc: PJNError) -> JSONResponse:
    """Maneja excepciones del sistema PJN.

    Args:
        request: Request de FastAPI
        exc: Excepción PJN

    Returns:
        JSONResponse con detalles del error
    """
    logger.error(f"PJNError en {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error": str(exc),
            "error_type": type(exc).__name__,
        },
    )


@app.exception_handler(Exception)
async def general_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Maneja excepciones generales no controladas.

    Args:
        request: Request de FastAPI
        exc: Excepción general

    Returns:
        JSONResponse con error genérico
    """
    logger.exception(f"Error no controlado en {request.url.path}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Error interno del servidor",
            "error_type": "InternalServerError",
        },
    )


# === Middleware de Logging ===

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Registra todas las peticiones HTTP.

    Args:
        request: Request de FastAPI
        call_next: Siguiente middleware/handler

    Returns:
        Response
    """
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"{request.method} {request.url.path} - {response.status_code}")
    return response


# === Incluir Routers ===

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(expedientes.router, prefix="/api/v1/expedientes", tags=["expedientes"])
app.include_router(
    extraccion_masiva.router,
    prefix="/api/v1/extraccion-masiva",
    tags=["extraccion_masiva"]
)
app.include_router(workspaces.router, prefix="/api/v1/workspaces", tags=["workspaces"])
app.include_router(monitoreo.router, prefix="/api/v1/monitoreo", tags=["monitoreo"])
app.include_router(procesamiento.router, prefix="/api/v1", tags=["procesamiento"])
app.include_router(config.router, prefix="/api/v1", tags=["configuracion"])
app.include_router(admin.router, prefix="/api/v1", tags=["administracion"])


# === Root Endpoint ===

@app.get("/")
async def root():
    """Endpoint raíz con información de la API."""
    return {
        "name": "Sistema PJN API",
        "version": "6.0.0",
        "description": "API REST para extracción y monitoreo del Portal Judicial Nacional",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


def start_server():
    """Función de entrada para el comando pjn-api."""
    import uvicorn

    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Iniciar servidor
    uvicorn.run(
        "presentation.api.rest.main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.api.reload,
        log_level="info",
    )


if __name__ == "__main__":
    start_server()
