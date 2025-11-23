"""Manejadores de errores centralizados para la API REST.

Este módulo define handlers de excepciones para errores comunes
proporcionando respuestas consistentes y logging estructurado.
"""

import logging
import uuid
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from mysql.connector import Error as MySQLError

from infrastructure.exceptions import PJNError

logger = logging.getLogger(__name__)


def create_error_response(
    status_code: int,
    error: str,
    error_type: str,
    request_id: str | None = None,
    details: Any = None,
) -> JSONResponse:
    """Crea una respuesta de error estandarizada.

    Args:
        status_code: Código HTTP del error
        error: Mensaje de error
        error_type: Tipo/clase del error
        request_id: ID único de la petición para tracking
        details: Detalles adicionales del error

    Returns:
        JSONResponse con formato consistente
    """
    content = {
        "success": False,
        "error": error,
        "error_type": error_type,
    }

    if request_id:
        content["request_id"] = request_id

    if details:
        content["details"] = details

    return JSONResponse(status_code=status_code, content=content)


def setup_error_handlers(app: FastAPI) -> None:
    """Configura todos los handlers de errores en la aplicación.

    Args:
        app: Instancia de FastAPI
    """

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Maneja errores de validación de Pydantic/FastAPI."""
        request_id = str(uuid.uuid4())[:8]

        errors = []
        for error in exc.errors():
            loc = " -> ".join(str(l) for l in error["loc"])
            errors.append({
                "field": loc,
                "message": error["msg"],
                "type": error["type"],
            })

        logger.warning(
            f"[{request_id}] Validation error en {request.method} {request.url.path}: "
            f"{len(errors)} errores"
        )

        return create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error="Error de validación en los datos enviados",
            error_type="ValidationError",
            request_id=request_id,
            details=errors,
        )

    @app.exception_handler(PJNError)
    async def pjn_error_handler(
        request: Request, exc: PJNError
    ) -> JSONResponse:
        """Maneja excepciones del sistema PJN."""
        request_id = str(uuid.uuid4())[:8]

        logger.error(
            f"[{request_id}] PJNError en {request.method} {request.url.path}: {exc}"
        )

        return create_error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            error=str(exc),
            error_type=type(exc).__name__,
            request_id=request_id,
        )

    @app.exception_handler(MySQLError)
    async def mysql_error_handler(
        request: Request, exc: MySQLError
    ) -> JSONResponse:
        """Maneja errores de MySQL."""
        request_id = str(uuid.uuid4())[:8]

        logger.error(
            f"[{request_id}] MySQLError en {request.method} {request.url.path}: "
            f"[{exc.errno}] {exc.msg}"
        )

        # No exponer detalles de BD al cliente
        return create_error_response(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error="Error de base de datos. Por favor intente nuevamente.",
            error_type="DatabaseError",
            request_id=request_id,
        )

    @app.exception_handler(Exception)
    async def general_error_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Maneja excepciones generales no controladas."""
        request_id = str(uuid.uuid4())[:8]

        logger.exception(
            f"[{request_id}] Error no controlado en "
            f"{request.method} {request.url.path}: {type(exc).__name__}"
        )

        return create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Error interno del servidor",
            error_type="InternalServerError",
            request_id=request_id,
        )
