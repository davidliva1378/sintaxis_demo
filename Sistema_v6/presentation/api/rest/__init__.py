"""REST API Module - FastAPI REST API for Sistema PJN v6.

Este módulo implementa una API REST completa usando FastAPI que expone
todos los use cases del sistema a través de endpoints HTTP.

Estructura:
    - main.py: Aplicación FastAPI principal
    - routers/: Routers por recurso (expedientes, workspaces, monitoreo)
    - schemas/: Modelos Pydantic para request/response
    - middleware/: Middleware personalizado (futuro)

Uso:
    ```bash
    # Desarrollo
    uvicorn presentation.api.rest.main:app --reload

    # Producción
    uvicorn presentation.api.rest.main:app --host 0.0.0.0 --port 8000
    ```

Documentación:
    - Swagger UI: http://localhost:8000/docs
    - ReDoc: http://localhost:8000/redoc
"""

from .main import app

__all__ = ["app"]
