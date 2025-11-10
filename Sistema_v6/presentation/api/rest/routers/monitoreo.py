"""Monitoreo Router - Endpoints para monitoreo de expedientes."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from application.dtos import MonitorearExpedientesCommand
from infrastructure.di_container import get_container
from infrastructure.exceptions import PJNError

from ..schemas.monitoreo_schemas import (
    CambioDetectadoResponse,
    IniciarMonitoreoRequest,
    MonitoreoResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/iniciar", response_model=MonitoreoResponse, status_code=status.HTTP_200_OK)
async def iniciar_monitoreo(request: IniciarMonitoreoRequest):
    """Inicia monitoreo de expedientes (verificación única).

    NOTA: Este endpoint ejecuta UNA verificación de cambios.
    Para monitoreo continuo, usar un scheduler externo (cron, systemd timer, etc.)
    o implementar un proceso de background con APScheduler.

    Args:
        request: Datos de la petición

    Returns:
        MonitoreoResponse con cambios detectados

    Raises:
        HTTPException: Si hay error en el monitoreo
    """
    logger.info("POST /monitoreo/iniciar")

    try:
        # Preparar comando
        command = MonitorearExpedientesCommand(
            archivo_sistema=Path(request.archivo_sistema),
            workspaces_dir=Path(request.workspaces_dir) if request.workspaces_dir else None,
            intervalo_minutos=request.intervalo_minutos,
            notificar=request.notificar,
        )

        # Ejecutar use case (una vez)
        container = get_container()
        use_case = container.monitorear_expedientes_use_case()
        result = await use_case.execute(command)

        if result.success:
            response_data = result.value

            # Convertir cambios a response
            cambios_response = [
                CambioDetectadoResponse(
                    numero_expediente=cambio.get("numero_expediente", ""),
                    tipo_cambio=cambio.get("tipo_cambio", "desconocido"),
                    descripcion=cambio.get("descripcion", ""),
                    fecha_deteccion=cambio.get("fecha_deteccion", datetime.now().isoformat()),
                )
                for cambio in response_data.cambios
            ]

            return MonitoreoResponse(
                success=True,
                total_expedientes=response_data.total_expedientes,
                cambios_detectados=response_data.cambios_detectados,
                cambios=cambios_response,
            )
        else:
            return MonitoreoResponse(
                success=False,
                total_expedientes=0,
                cambios_detectados=0,
                cambios=[],
                error=result.error,
            )

    except NotImplementedError as e:
        logger.warning(f"Funcionalidad no implementada: {e}")
        return MonitoreoResponse(
            success=False,
            total_expedientes=0,
            cambios_detectados=0,
            cambios=[],
            error="Monitoreo no implementado completamente. Scraping pendiente desde Sistema_v5.",
        )

    except PJNError as e:
        logger.error(f"Error PJN en monitoreo: {e}")
        return MonitoreoResponse(
            success=False,
            total_expedientes=0,
            cambios_detectados=0,
            cambios=[],
            error=str(e),
        )

    except Exception as e:
        logger.exception("Error inesperado en monitoreo")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}",
        )


@router.get("/estado", status_code=status.HTTP_200_OK)
async def obtener_estado_monitoreo():
    """Obtiene el estado actual del monitoreo.

    NOTA: Implementación básica. En producción, usar Redis/DB para estado persistente.

    Returns:
        Dict con estado del monitoreo
    """
    logger.info("GET /monitoreo/estado")

    # TODO: Implementar estado persistente con Redis/DB
    return {
        "activo": False,
        "ultima_ejecucion": None,
        "proxima_ejecucion": None,
        "mensaje": "Monitoreo on-demand. Use POST /monitoreo/iniciar para ejecutar.",
    }
