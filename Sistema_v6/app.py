"""
FastAPI Application para Sistema v6 - Extracción Masiva con Filtrado.

Este módulo crea la aplicación FastAPI y registra los routers necesarios.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from presentation import extraccion_masiva_router


def create_app() -> FastAPI:
    """
    Crea y configura la aplicación FastAPI.

    Returns:
        FastAPI: Aplicación configurada
    """
    app = FastAPI(
        title="Sistema v6 - Extracción Masiva",
        description="API para extracción masiva de expedientes con filtrado y selección",
        version="6.0.0",
    )

    # Configurar CORS para permitir frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # En producción, especificar orígenes exactos
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Registrar routers
    app.include_router(extraccion_masiva_router)

    @app.get("/")
    async def root():
        """Endpoint raíz con información de la API."""
        return {
            "name": "Sistema v6 - Extracción Masiva",
            "version": "6.0.0",
            "description": "API para extracción masiva de expedientes del PJN",
            "endpoints": {
                "listado": "/extraccion-masiva/listado",
                "procesar": "/extraccion-masiva/procesar-seleccionados",
                "sesiones": "/extraccion-masiva/sesiones",
            }
        }

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}

    return app


# Crear instancia de la aplicación
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
