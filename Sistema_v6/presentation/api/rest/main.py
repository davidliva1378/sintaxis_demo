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
from dotenv import load_dotenv
import os
import sys

# Cargar variables de entorno explícitamente para asegurar que
# módulos que usan os.getenv() (como mysql_pool.py) funcionen correctamente
load_dotenv()

# Configurar logging básico para que los mensajes del lifespan se muestren
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:     %(message)s",
    stream=sys.stdout
)

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .error_handlers import setup_error_handlers

from infrastructure.config import get_settings
from infrastructure.di_container import get_container
from infrastructure.logging import setup_logging
from .rate_limiter import limiter

from .routers import (
    admin,
    agenda,
    analisis,
    auth,
    config,
    dashboard,
    entidades,
    escritos,
    expedientes,
    extraccion_masiva,
    feriados,
    health,
    ia,
    mcp,
    monitoreo,
    notificaciones,
    procesamiento,
    rag,
    tipos_entidad,
    tools,
    vencimientos,
    workspaces,
    logs,
    classification,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Maneja el ciclo de vida de la aplicación.

    Se ejecuta al inicio y al final de la aplicación.
    """
    # Startup
    print("\n" + "=" * 60)
    print("🚀 Iniciando Sistema PJN API v6...")
    print("=" * 60)

    settings = get_settings()
    print(f"📍 API configurada en: {settings.api.host}:{settings.api.port}")
    print(f"📁 Base path: {settings.storage.base_path}")

    # Iniciar scheduler de monitoreo automáticamente si está activo en MySQL
    container = get_container()
    scheduler = container.monitor_scheduler

    try:
        print("\n🔍 Verificando configuración de monitoreo en MySQL...")
        monitoreo_service = container.monitoreo_service
        config_db = monitoreo_service.repository.obtener_configuracion(usuario_id=1)

        if config_db and config_db.get('activo'):
            print("✓ Configuración de monitoreo activa, iniciando scheduler...")
            await scheduler.start()
            estado = scheduler.obtener_estado()
            print(
                f"✅ MonitorSchedulerService ACTIVO:\n"
                f"   • Intervalo: {estado.get('intervalo_actual_minutos')} minutos\n"
                f"   • Horario laboral: {'Sí' if estado.get('es_horario_laboral') else 'No'}\n"
                f"   • Próxima ejecución: {estado.get('proxima_ejecucion')}"
            )
        else:
            print("ℹ️  Monitoreo no activo en MySQL, scheduler no iniciado")
            print("   Para activar: POST /api/v1/monitoreo/start")
    except Exception as e:
        print(f"⚠️  Error al iniciar scheduler: {e}")
        print("   El scheduler se puede iniciar manualmente via POST /api/v1/monitoreo/start")

    print("=" * 60 + "\n")

    yield

    # Shutdown
    logger.info("Cerrando Sistema PJN API v6...")

    # Detener scheduler si está activo
    try:
        estado = scheduler.obtener_estado()
        if estado.get("activo"):
            logger.info("Deteniendo scheduler de monitoreo...")
            await scheduler.stop()
            logger.info("✓ Scheduler detenido correctamente")
    except Exception as e:
        logger.error(f"Error al detener scheduler: {e}")

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

# Configurar Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configurar CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar Error Handlers centralizados
setup_error_handlers(app)


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
app.include_router(entidades.router, prefix="/api/v1")
app.include_router(entidades.actuacion_router, prefix="/api/v1")
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
app.include_router(analisis.router, prefix="/api/v1", tags=["analisis"])
app.include_router(agenda.router, prefix="/api/v1", tags=["agenda"])
app.include_router(escritos.router, prefix="/api/v1", tags=["escritos"])
app.include_router(ia.router, prefix="/api/v1", tags=["ia"])
app.include_router(tools.router, prefix="/api/v1", tags=["tools"])
app.include_router(mcp.router, prefix="/api/v1", tags=["mcp"])
app.include_router(logs.router, prefix="/api/v1", tags=["logs"])
app.include_router(tipos_entidad.router, prefix="/api/v1", tags=["tipos_entidad"])
app.include_router(rag.router, tags=["rag"])
app.include_router(classification.router, prefix="/api/v1", tags=["classification"])
app.include_router(dashboard.router, prefix="/api/v1", tags=["dashboard"])
app.include_router(feriados.router, prefix="/api/v1", tags=["feriados"])
app.include_router(vencimientos.router, prefix="/api/v1", tags=["vencimientos"])
app.include_router(notificaciones.router, prefix="/api/v1/notificaciones", tags=["notificaciones"])


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

    # Configurar logging centralizado
    setup_logging()

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
