"""
ARCHIVO DE REFERENCIA PARA PASO 6
Crear este archivo en: Sistema_v6/presentation/api/rest/routers/extraccion_masiva.py
"""

"""Router de Extracción Masiva - Endpoints avanzados para gestión de extracciones."""

from __future__ import annotations

import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks, WebSocket, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional

from application.dtos import (
    IniciarExtraccionMasivaCommand,
    IniciarExtraccionMasivaResponse,
    ProgresoExtraccionResponse,
    ResumenExtraccionResponse,
)
from infrastructure.di_container import get_container
from infrastructure.services.gestor_sesiones_service import get_gestor_sesiones
from Sistema_v6.extraccion_masiva import ConfigExtraccionMasiva
from Sistema_v6.configuracion.config import Config
from ..websocket.extraccion_ws import websocket_progreso

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== Schemas Pydantic ====================

class IniciarExtraccionRequest(BaseModel):
    """Request para iniciar extracción masiva."""
    usuario: str = Field(..., description="Usuario PJN")
    contrasena: str = Field(..., description="Contraseña PJN")
    fecha_desde: Optional[str] = Field(None, description="Fecha desde (YYYY-MM-DD)")
    fecha_hasta: Optional[str] = Field(None, description="Fecha hasta (YYYY-MM-DD)")
    estados: Optional[List[str]] = Field(None, description="Estados a filtrar")
    dependencias: Optional[List[str]] = Field(None, description="Dependencias a filtrar")
    umbral_errores: int = Field(10, description="Máximo de errores consecutivos")
    headless: bool = Field(True, description="Ejecutar navegador en modo headless")
    exportar_formatos: List[str] = Field(["json"], description="Formatos: json, excel, csv")


class IniciarExtraccionResponseSchema(BaseModel):
    """Response al iniciar extracción."""
    session_id: str
    mensaje: str
    estado: str


class ProgresoExtraccionSchema(BaseModel):
    """Schema de progreso de extracción."""
    session_id: str
    estado: str
    fase: str
    progreso_actual: int
    progreso_total: int
    porcentaje: float
    mensaje: str
    errores: int
    tiempo_transcurrido: float
    tiempo_estimado: Optional[float]
    velocidad: Optional[float]


class ResumenExtraccionSchema(BaseModel):
    """Schema de resumen de extracción."""
    session_id: str
    estado: str
    total: int
    exitosos: int
    errores: int
    omitidos: int
    duracion_segundos: float
    velocidad_promedio: float
    archivos_generados: List[str]


# ==================== Endpoints ====================

@router.post("/masivo", response_model=IniciarExtraccionResponseSchema, status_code=status.HTTP_200_OK)
async def iniciar_extraccion_masiva(request: IniciarExtraccionRequest, background_tasks: BackgroundTasks):
    """Inicia una extracción masiva de expedientes del PJN.

    Esta es la versión avanzada con:
    - Gestión de sesiones
    - Progreso en tiempo real via WebSocket
    - Control de pausar/reanudar/cancelar
    - Exportación a múltiples formatos

    Args:
        request: Configuración de la extracción
        background_tasks: Gestor de tareas en background

    Returns:
        Información de la sesión iniciada

    Raises:
        HTTPException: Si hay error al iniciar
    """
    logger.info("POST /expedientes/extraer/masivo")

    try:
        # Crear comando
        command = IniciarExtraccionMasivaCommand(
            usuario=request.usuario,
            contrasena=request.contrasena,
            fecha_desde=request.fecha_desde,
            fecha_hasta=request.fecha_hasta,
            estados=request.estados,
            dependencias=request.dependencias,
            umbral_errores=request.umbral_errores,
            headless=request.headless,
            exportar_formatos=request.exportar_formatos,
        )

        # Obtener use case
        container = get_container()
        use_case = container.extraccion_masiva_use_case()

        # Iniciar extracción
        result = await use_case.iniciar_extraccion(command)

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error,
            )

        response_data = result.value

        # Ejecutar extracción en background
        config_extractor = ConfigExtraccionMasiva(
            fecha_desde=request.fecha_desde,
            fecha_hasta=request.fecha_hasta,
            estados=request.estados,
            dependencias=request.dependencias,
            umbral_errores=request.umbral_errores,
            headless=request.headless,
        )

        background_tasks.add_task(
            use_case.ejecutar_extraccion_background,
            response_data.session_id,
            config_extractor,
            request.exportar_formatos,
        )

        return IniciarExtraccionResponseSchema(
            session_id=response_data.session_id,
            mensaje=response_data.mensaje,
            estado=response_data.estado,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error inesperado al iniciar extracción masiva")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}",
        )


@router.get("/{session_id}/progreso", response_model=ProgresoExtraccionSchema, status_code=status.HTTP_200_OK)
async def obtener_progreso(session_id: str):
    """Obtiene el progreso actual de una extracción.

    Args:
        session_id: ID de la sesión

    Returns:
        Información de progreso actualizada

    Raises:
        HTTPException: Si la sesión no existe
    """
    logger.info(f"GET /expedientes/extraer/{session_id}/progreso")

    gestor = get_gestor_sesiones()
    sesion = await gestor.obtener_sesion(session_id)

    if not sesion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sesión no encontrada",
        )

    # Calcular métricas
    from datetime import datetime
    inicio = datetime.fromisoformat(sesion["tiempo_inicio"])
    transcurrido = (datetime.now() - inicio).total_seconds()

    tiempo_estimado = None
    velocidad = None

    if sesion["progreso_actual"] > 0 and sesion["progreso_total"] > 0:
        velocidad = sesion["progreso_actual"] / transcurrido if transcurrido > 0 else 0
        if velocidad > 0:
            restante = sesion["progreso_total"] - sesion["progreso_actual"]
            tiempo_estimado = restante / velocidad

    return ProgresoExtraccionSchema(
        session_id=session_id,
        estado=sesion["estado"],
        fase=sesion["fase"],
        progreso_actual=sesion["progreso_actual"],
        progreso_total=sesion["progreso_total"],
        porcentaje=sesion["porcentaje"],
        mensaje=sesion["mensaje"],
        errores=sesion["errores"],
        tiempo_transcurrido=transcurrido,
        tiempo_estimado=tiempo_estimado,
        velocidad=velocidad,
    )


@router.post("/{session_id}/pausar", status_code=status.HTTP_200_OK)
async def pausar_extraccion(session_id: str):
    """Pausa una extracción en progreso.

    Args:
        session_id: ID de la sesión

    Returns:
        Confirmación de pausa

    Raises:
        HTTPException: Si no se puede pausar
    """
    logger.info(f"POST /expedientes/extraer/{session_id}/pausar")

    try:
        container = get_container()
        use_case = container.extraccion_masiva_use_case()

        result = await use_case.pausar_extraccion(session_id)

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error,
            )

        return result.value

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error al pausar extracción {session_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}",
        )


@router.post("/{session_id}/reanudar", status_code=status.HTTP_200_OK)
async def reanudar_extraccion(session_id: str):
    """Reanuda una extracción pausada.

    Args:
        session_id: ID de la sesión

    Returns:
        Confirmación de reanudación

    Raises:
        HTTPException: Si no se puede reanudar
    """
    logger.info(f"POST /expedientes/extraer/{session_id}/reanudar")

    try:
        container = get_container()
        use_case = container.extraccion_masiva_use_case()

        result = await use_case.reanudar_extraccion(session_id)

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error,
            )

        return result.value

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error al reanudar extracción {session_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}",
        )


@router.post("/{session_id}/cancelar", status_code=status.HTTP_200_OK)
async def cancelar_extraccion(session_id: str):
    """Cancela una extracción.

    Args:
        session_id: ID de la sesión

    Returns:
        Confirmación de cancelación

    Raises:
        HTTPException: Si no se puede cancelar
    """
    logger.info(f"POST /expedientes/extraer/{session_id}/cancelar")

    try:
        container = get_container()
        use_case = container.extraccion_masiva_use_case()

        result = await use_case.cancelar_extraccion(session_id)

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error,
            )

        return result.value

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error al cancelar extracción {session_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}",
        )


@router.get("/{session_id}/resumen", response_model=ResumenExtraccionSchema, status_code=status.HTTP_200_OK)
async def obtener_resumen(session_id: str):
    """Obtiene el resumen final de una extracción completada.

    Args:
        session_id: ID de la sesión

    Returns:
        Resumen con estadísticas finales

    Raises:
        HTTPException: Si la sesión no existe o no ha finalizado
    """
    logger.info(f"GET /expedientes/extraer/{session_id}/resumen")

    gestor = get_gestor_sesiones()
    sesion = await gestor.obtener_sesion(session_id)

    if not sesion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sesión no encontrada",
        )

    if sesion["estado"] != "completado":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La extracción no ha finalizado",
        )

    resultados = sesion.get("resultados", {})
    resumen_batch = resultados.get("resultado", {})

    return ResumenExtraccionSchema(
        session_id=session_id,
        estado=sesion["estado"],
        total=resumen_batch.get("total", 0),
        exitosos=resumen_batch.get("exitosos", 0),
        errores=resumen_batch.get("errores", 0),
        omitidos=resumen_batch.get("omitidos", 0),
        duracion_segundos=resumen_batch.get("duracion_segundos", 0),
        velocidad_promedio=resumen_batch.get("velocidad_promedio", 0),
        archivos_generados=sesion.get("archivos", []),
    )


@router.get("/{session_id}/descargar/{formato}", status_code=status.HTTP_200_OK)
async def descargar_reporte(session_id: str, formato: str):
    """Descarga el reporte de una extracción finalizada.

    Args:
        session_id: ID de la sesión
        formato: Formato del reporte (json, excel, csv, html)

    Returns:
        Archivo del reporte

    Raises:
        HTTPException: Si el archivo no existe o formato no válido
    """
    logger.info(f"GET /expedientes/extraer/{session_id}/descargar/{formato}")

    gestor = get_gestor_sesiones()
    sesion = await gestor.obtener_sesion(session_id)

    if not sesion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sesión no encontrada",
        )

    if sesion["estado"] != "completado":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La extracción no ha finalizado",
        )

    # Buscar archivo según formato
    base_path = Config.EXTRACCION_MASIVA_DIR / session_id

    archivos_map = {
        "json": base_path / "reporte.json",
        "excel": base_path / "reporte.xlsx",
        "csv": base_path / "resultados.csv",
        "html": base_path / "reporte.html",
    }

    if formato not in archivos_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato no válido. Formatos disponibles: {', '.join(archivos_map.keys())}",
        )

    archivo = archivos_map[formato]

    if not archivo.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Archivo {formato} no encontrado",
        )

    return FileResponse(
        path=str(archivo),
        filename=f"extraccion_{session_id}.{formato}",
        media_type="application/octet-stream",
    )


@router.websocket("/{session_id}/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket para recibir actualizaciones de progreso en tiempo real.

    Args:
        websocket: Conexión WebSocket
        session_id: ID de la sesión a monitorear
    """
    await websocket_progreso(websocket, session_id)
