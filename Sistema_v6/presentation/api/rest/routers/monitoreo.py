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
    EstadoMonitoreoResponse,
    IniciarMonitoreoRequest,
    MonitoreoResponse,
    StartSchedulerResponse,
    StopSchedulerResponse,
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


@router.post("/start", response_model=StartSchedulerResponse, status_code=status.HTTP_200_OK)
async def iniciar_scheduler():
    """Inicia el scheduler de monitoreo continuo.

    El scheduler ejecutará verificaciones periódicas según la configuración
    (horario laboral/no laboral).

    Returns:
        StartSchedulerResponse con resultado de la operación

    Raises:
        HTTPException: Si el scheduler ya está activo o hay error
    """
    logger.info("POST /monitoreo/start")

    try:
        container = get_container()
        scheduler = container.monitor_scheduler

        # Verificar si ya está activo
        if scheduler.obtener_estado()["activo"]:
            return StartSchedulerResponse(
                success=False, mensaje="Scheduler ya está activo", intervalo_minutos=None
            )

        # Iniciar scheduler
        await scheduler.start()

        intervalo = scheduler.obtener_estado()["intervalo_actual_minutos"]

        return StartSchedulerResponse(
            success=True,
            mensaje="Scheduler iniciado correctamente",
            intervalo_minutos=intervalo,
        )

    except RuntimeError as e:
        logger.error(f"Error al iniciar scheduler: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error: {str(e)}"
        )

    except Exception as e:
        logger.exception("Error inesperado al iniciar scheduler")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}",
        )


@router.post("/stop", response_model=StopSchedulerResponse, status_code=status.HTTP_200_OK)
async def detener_scheduler():
    """Detiene el scheduler de monitoreo continuo.

    Espera a que termine cualquier verificación en curso antes de detener.

    Returns:
        StopSchedulerResponse con resultado de la operación

    Raises:
        HTTPException: Si hay error al detener
    """
    logger.info("POST /monitoreo/stop")

    try:
        container = get_container()
        scheduler = container.monitor_scheduler

        # Verificar si ya está detenido
        if not scheduler.obtener_estado()["activo"]:
            return StopSchedulerResponse(success=False, mensaje="Scheduler ya está detenido")

        # Detener scheduler
        await scheduler.stop()

        return StopSchedulerResponse(success=True, mensaje="Scheduler detenido correctamente")

    except Exception as e:
        logger.exception("Error inesperado al detener scheduler")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}",
        )


@router.get("/estado", response_model=EstadoMonitoreoResponse, status_code=status.HTTP_200_OK)
async def obtener_estado_monitoreo():
    """Obtiene el estado actual del scheduler de monitoreo.

    Returns:
        EstadoMonitoreoResponse con información del estado:
        - activo: Si el scheduler está corriendo
        - ejecutando: Si hay verificación en curso
        - intervalo_actual_minutos: Intervalo de verificación
        - es_horario_laboral: Si está en horario laboral
        - proxima_ejecucion: Timestamp de próxima ejecución
        - jobs_programados: Número de jobs activos
    """
    logger.info("GET /monitoreo/estado")

    try:
        container = get_container()
        scheduler = container.monitor_scheduler
        estado = scheduler.obtener_estado()

        return EstadoMonitoreoResponse(**estado)

    except Exception as e:
        logger.exception("Error al obtener estado del scheduler")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}",
        )


@router.post("/verificar", response_model=MonitoreoResponse, status_code=status.HTTP_200_OK)
async def verificar_manual():
    """Ejecuta una verificación manual inmediata (sin afectar el scheduler).

    Útil para verificar cambios manualmente sin esperar al próximo ciclo programado.

    Returns:
        MonitoreoResponse con cambios detectados

    Raises:
        HTTPException: Si hay error en la verificación
    """
    logger.info("POST /monitoreo/verificar")

    try:
        container = get_container()
        scheduler = container.monitor_scheduler

        # Ejecutar verificación manual
        resultado = await scheduler.ejecutar_verificacion_manual()

        if resultado["exito"]:
            # Convertir cambios a response
            cambios_response = [
                CambioDetectadoResponse(
                    numero_expediente=c["numero_expediente"],
                    tipo_cambio=c["tipo"],
                    descripcion=c["descripcion"],
                    fecha_deteccion=datetime.now().isoformat(),
                )
                for c in resultado["cambios"]
            ]

            return MonitoreoResponse(
                success=True,
                total_expedientes=resultado["expedientes_verificados"],
                cambios_detectados=resultado["cambios_detectados"],
                cambios=cambios_response,
            )
        else:
            return MonitoreoResponse(
                success=False,
                total_expedientes=0,
                cambios_detectados=0,
                cambios=[],
                error=resultado.get("error", "Error desconocido"),
            )

    except Exception as e:
        logger.exception("Error inesperado en verificación manual")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}",
        )
