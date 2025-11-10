"""Workspaces Router - Endpoints para gestión de workspaces."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from application.dtos import CrearWorkspacesCommand
from infrastructure.di_container import get_container
from infrastructure.exceptions import PJNError

from ..schemas.workspace_schemas import (
    CrearWorkspacesRequest,
    CrearWorkspacesResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/crear", response_model=CrearWorkspacesResponse, status_code=status.HTTP_200_OK)
async def crear_workspaces(request: CrearWorkspacesRequest):
    """Crea workspaces para expedientes del sistema.

    Args:
        request: Datos de la petición

    Returns:
        CrearWorkspacesResponse con resultado

    Raises:
        HTTPException: Si hay error en la creación
    """
    logger.info("POST /workspaces/crear")

    try:
        # Preparar comando
        command = CrearWorkspacesCommand(
            archivo_sistema=Path(request.archivo_sistema),
            workspaces_dir=Path(request.workspaces_dir) if request.workspaces_dir else None,
            extraer_actuaciones=request.extraer_actuaciones,
            descargar_archivos=request.descargar_archivos,
        )

        # Ejecutar use case
        container = get_container()
        use_case = container.crear_workspaces_use_case()
        result = await use_case.execute(command)

        if result.success:
            response_data = result.value
            return CrearWorkspacesResponse(
                success=True,
                total_expedientes=response_data.total_expedientes,
                workspaces_creados=response_data.workspaces_creados,
                errores=response_data.errores,
            )
        else:
            return CrearWorkspacesResponse(
                success=False,
                total_expedientes=0,
                workspaces_creados=0,
                errores=0,
                error=result.error,
            )

    except NotImplementedError as e:
        logger.warning(f"Funcionalidad no implementada: {e}")
        return CrearWorkspacesResponse(
            success=False,
            total_expedientes=0,
            workspaces_creados=0,
            errores=0,
            error="Extracción de actuaciones no implementada aún. Workspaces creados sin actuaciones.",
        )

    except PJNError as e:
        logger.error(f"Error PJN en creación de workspaces: {e}")
        return CrearWorkspacesResponse(
            success=False,
            total_expedientes=0,
            workspaces_creados=0,
            errores=0,
            error=str(e),
        )

    except Exception as e:
        logger.exception("Error inesperado en creación de workspaces")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}",
        )
