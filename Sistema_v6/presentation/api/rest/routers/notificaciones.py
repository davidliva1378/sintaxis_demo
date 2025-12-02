"""Notificaciones Router - Endpoints para sistema de alertas y notificaciones."""

from __future__ import annotations

import logging
from typing import Optional, List

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field

from infrastructure.persistence.alertas_repository import AlertasRepository
from infrastructure.persistence.vencimientos_repository import VencimientosRepository
from application.services.alertas_service import AlertasService

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Schemas
# =============================================================================

class NotificacionResponse(BaseModel):
    """Respuesta de notificación."""
    id: int
    usuario_id: int
    tipo: str
    titulo: str
    mensaje: str
    datos_extra: Optional[dict] = None
    leida: bool
    fecha_lectura: Optional[str] = None
    url_accion: Optional[str] = None
    prioridad: str
    expira_en: Optional[str] = None
    creado_en: str


class ListaNotificacionesResponse(BaseModel):
    """Lista de notificaciones."""
    notificaciones: List[NotificacionResponse]
    total: int
    no_leidas: int


class EstadisticasNotificacionesResponse(BaseModel):
    """Estadísticas de notificaciones."""
    total: int
    no_leidas: int
    vencimientos: int
    urgentes_no_leidas: int


class ConfiguracionAlertasResponse(BaseModel):
    """Configuración de alertas."""
    id: int
    usuario_id: int
    alertas_email: bool
    alertas_push: bool
    alertas_in_app: bool
    dias_anticipacion: List[int]
    hora_envio: str
    expedientes_excluidos: List[str]
    activo: bool


class ActualizarConfiguracionRequest(BaseModel):
    """Request para actualizar configuración."""
    alertas_email: Optional[bool] = None
    alertas_push: Optional[bool] = None
    alertas_in_app: Optional[bool] = None
    dias_anticipacion: Optional[List[int]] = None
    hora_envio: Optional[str] = None
    expedientes_excluidos: Optional[List[str]] = None
    activo: Optional[bool] = None


class CrearNotificacionRequest(BaseModel):
    """Request para crear notificación."""
    titulo: str = Field(..., min_length=1, max_length=255)
    mensaje: str = Field(..., min_length=1)
    tipo: str = Field(default="sistema")
    prioridad: str = Field(default="normal")
    url_accion: Optional[str] = None
    datos_extra: Optional[dict] = None


class VerificarAlertasResponse(BaseModel):
    """Respuesta de verificación de alertas."""
    alertas_generadas: int
    notificaciones_creadas: int
    vencimientos_evaluados: int
    timestamp: str


# =============================================================================
# Helpers
# =============================================================================

def get_alertas_service() -> AlertasService:
    """Obtiene instancia del servicio de alertas."""
    alertas_repo = AlertasRepository()
    vencimientos_repo = VencimientosRepository()
    return AlertasService(alertas_repo, vencimientos_repo)


# =============================================================================
# Endpoints de Notificaciones
# =============================================================================

@router.get("", response_model=ListaNotificacionesResponse)
async def listar_notificaciones(
    usuario_id: int = Query(default=1, description="ID del usuario"),
    solo_no_leidas: bool = Query(default=False, description="Solo no leídas"),
    tipo: Optional[str] = Query(default=None, description="Filtrar por tipo"),
    limite: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0)
):
    """Lista notificaciones del usuario.

    Args:
        usuario_id: ID del usuario (default 1)
        solo_no_leidas: Filtrar solo no leídas
        tipo: Filtrar por tipo (vencimiento, sistema, monitoreo, extraccion, error)
        limite: Máximo de resultados
        offset: Offset para paginación

    Returns:
        Lista de notificaciones con contadores
    """
    logger.info(f"GET /notificaciones - usuario={usuario_id}, no_leidas={solo_no_leidas}")

    try:
        service = get_alertas_service()

        notificaciones = service.obtener_notificaciones(
            usuario_id=usuario_id,
            solo_no_leidas=solo_no_leidas,
            limite=limite,
            offset=offset
        )

        no_leidas = service.contar_no_leidas(usuario_id)

        # Convertir a response
        notifs_response = []
        for n in notificaciones:
            notifs_response.append(NotificacionResponse(
                id=n["id"],
                usuario_id=n["usuario_id"],
                tipo=n["tipo"],
                titulo=n["titulo"],
                mensaje=n["mensaje"],
                datos_extra=n.get("datos_extra"),
                leida=n["leida"],
                fecha_lectura=str(n["fecha_lectura"]) if n.get("fecha_lectura") else None,
                url_accion=n.get("url_accion"),
                prioridad=n["prioridad"],
                expira_en=str(n["expira_en"]) if n.get("expira_en") else None,
                creado_en=str(n["creado_en"])
            ))

        return ListaNotificacionesResponse(
            notificaciones=notifs_response,
            total=len(notificaciones),
            no_leidas=no_leidas
        )

    except Exception as e:
        logger.error(f"Error listando notificaciones: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/estadisticas", response_model=EstadisticasNotificacionesResponse)
async def obtener_estadisticas(
    usuario_id: int = Query(default=1, description="ID del usuario")
):
    """Obtiene estadísticas de notificaciones.

    Args:
        usuario_id: ID del usuario

    Returns:
        Estadísticas de notificaciones
    """
    logger.debug(f"GET /notificaciones/estadisticas - usuario={usuario_id}")

    try:
        service = get_alertas_service()
        stats = service.obtener_estadisticas(usuario_id)

        return EstadisticasNotificacionesResponse(
            total=stats.get("total", 0),
            no_leidas=stats.get("no_leidas", 0),
            vencimientos=stats.get("vencimientos", 0),
            urgentes_no_leidas=stats.get("urgentes_no_leidas", 0)
        )

    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/no-leidas/count")
async def contar_no_leidas(
    usuario_id: int = Query(default=1, description="ID del usuario")
):
    """Cuenta notificaciones no leídas (endpoint ligero para polling).

    Args:
        usuario_id: ID del usuario

    Returns:
        Contador de no leídas
    """
    try:
        service = get_alertas_service()
        count = service.contar_no_leidas(usuario_id)
        return {"no_leidas": count}

    except Exception as e:
        logger.error(f"Error contando no leídas: {e}")
        return {"no_leidas": 0}


@router.post("/{notificacion_id}/leer")
async def marcar_como_leida(
    notificacion_id: int,
    usuario_id: int = Query(default=1, description="ID del usuario")
):
    """Marca una notificación como leída.

    Args:
        notificacion_id: ID de la notificación
        usuario_id: ID del usuario

    Returns:
        Confirmación
    """
    logger.debug(f"POST /notificaciones/{notificacion_id}/leer")

    try:
        service = get_alertas_service()
        success = service.marcar_como_leida(notificacion_id, usuario_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notificación no encontrada"
            )

        return {"success": True, "notificacion_id": notificacion_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marcando como leída: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/leer-todas")
async def marcar_todas_leidas(
    usuario_id: int = Query(default=1, description="ID del usuario")
):
    """Marca todas las notificaciones como leídas.

    Args:
        usuario_id: ID del usuario

    Returns:
        Número de notificaciones marcadas
    """
    logger.info(f"POST /notificaciones/leer-todas - usuario={usuario_id}")

    try:
        service = get_alertas_service()
        count = service.marcar_todas_leidas(usuario_id)

        return {"success": True, "marcadas": count}

    except Exception as e:
        logger.error(f"Error marcando todas como leídas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("", status_code=status.HTTP_201_CREATED)
async def crear_notificacion(
    request: CrearNotificacionRequest,
    usuario_id: int = Query(default=1, description="ID del usuario destinatario")
):
    """Crea una notificación manualmente.

    Útil para enviar notificaciones desde otros sistemas o para testing.

    Args:
        request: Datos de la notificación
        usuario_id: ID del usuario destinatario

    Returns:
        ID de la notificación creada
    """
    logger.info(f"POST /notificaciones - usuario={usuario_id}, titulo={request.titulo}")

    try:
        service = get_alertas_service()
        notif_id = service.crear_notificacion_sistema(
            usuario_id=usuario_id,
            titulo=request.titulo,
            mensaje=request.mensaje,
            tipo=request.tipo,
            prioridad=request.prioridad,
            url_accion=request.url_accion,
            datos_extra=request.datos_extra
        )

        return {"success": True, "notificacion_id": notif_id}

    except Exception as e:
        logger.error(f"Error creando notificación: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# =============================================================================
# Endpoints de Configuración de Alertas
# =============================================================================

@router.get("/configuracion", response_model=ConfiguracionAlertasResponse)
async def obtener_configuracion(
    usuario_id: int = Query(default=1, description="ID del usuario")
):
    """Obtiene la configuración de alertas del usuario.

    Args:
        usuario_id: ID del usuario

    Returns:
        Configuración de alertas
    """
    logger.debug(f"GET /notificaciones/configuracion - usuario={usuario_id}")

    try:
        service = get_alertas_service()
        config = service.obtener_configuracion(usuario_id)

        return ConfiguracionAlertasResponse(
            id=config.get("id", 0),
            usuario_id=config.get("usuario_id", usuario_id),
            alertas_email=config.get("alertas_email", True),
            alertas_push=config.get("alertas_push", True),
            alertas_in_app=config.get("alertas_in_app", True),
            dias_anticipacion=config.get("dias_anticipacion", [3, 1, 0]),
            hora_envio=config.get("hora_envio", "09:00:00"),
            expedientes_excluidos=config.get("expedientes_excluidos", []),
            activo=config.get("activo", True)
        )

    except Exception as e:
        logger.error(f"Error obteniendo configuración: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/configuracion", response_model=ConfiguracionAlertasResponse)
async def actualizar_configuracion(
    request: ActualizarConfiguracionRequest,
    usuario_id: int = Query(default=1, description="ID del usuario")
):
    """Actualiza la configuración de alertas.

    Args:
        request: Nuevos valores de configuración
        usuario_id: ID del usuario

    Returns:
        Configuración actualizada
    """
    logger.info(f"PUT /notificaciones/configuracion - usuario={usuario_id}")

    try:
        service = get_alertas_service()
        config = service.actualizar_configuracion(
            usuario_id=usuario_id,
            alertas_email=request.alertas_email,
            alertas_push=request.alertas_push,
            alertas_in_app=request.alertas_in_app,
            dias_anticipacion=request.dias_anticipacion,
            hora_envio=request.hora_envio,
            expedientes_excluidos=request.expedientes_excluidos,
            activo=request.activo
        )

        return ConfiguracionAlertasResponse(
            id=config.get("id", 0),
            usuario_id=config.get("usuario_id", usuario_id),
            alertas_email=config.get("alertas_email", True),
            alertas_push=config.get("alertas_push", True),
            alertas_in_app=config.get("alertas_in_app", True),
            dias_anticipacion=config.get("dias_anticipacion", [3, 1, 0]),
            hora_envio=config.get("hora_envio", "09:00:00"),
            expedientes_excluidos=config.get("expedientes_excluidos", []),
            activo=config.get("activo", True)
        )

    except Exception as e:
        logger.error(f"Error actualizando configuración: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# =============================================================================
# Endpoints de Verificación de Alertas
# =============================================================================

@router.post("/verificar-vencimientos", response_model=VerificarAlertasResponse)
async def verificar_vencimientos(
    usuario_id: int = Query(default=1, description="ID del usuario")
):
    """Verifica vencimientos y genera alertas/notificaciones.

    Este endpoint puede ser llamado manualmente o por un scheduler.

    Args:
        usuario_id: ID del usuario

    Returns:
        Resumen de alertas generadas
    """
    logger.info(f"POST /notificaciones/verificar-vencimientos - usuario={usuario_id}")

    try:
        service = get_alertas_service()
        resultado = await service.verificar_y_generar_alertas(usuario_id)

        return VerificarAlertasResponse(
            alertas_generadas=resultado.get("alertas_generadas", 0),
            notificaciones_creadas=resultado.get("notificaciones_creadas", 0),
            vencimientos_evaluados=resultado.get("vencimientos_evaluados", 0),
            timestamp=resultado.get("timestamp", "")
        )

    except Exception as e:
        logger.error(f"Error verificando vencimientos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/expiradas")
async def eliminar_expiradas():
    """Elimina notificaciones expiradas.

    Returns:
        Número de notificaciones eliminadas
    """
    logger.info("DELETE /notificaciones/expiradas")

    try:
        service = get_alertas_service()
        count = service.eliminar_notificaciones_expiradas()

        return {"success": True, "eliminadas": count}

    except Exception as e:
        logger.error(f"Error eliminando expiradas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
