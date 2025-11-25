"""Monitoreo Router - Endpoints para monitoreo de expedientes."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from application.dtos import MonitorearExpedientesCommand
from infrastructure.di_container import get_container
from infrastructure.exceptions import PJNError
from infrastructure.persistence.database import Usuario
from .auth import get_current_active_user, oauth2_scheme

from ..schemas.monitoreo_schemas import (
    ActualizarConfiguracionRequest,
    ActualizarExpedienteRequest,
    AgregarExpedienteRequest,
    CambioDetectadoResponse,
    ConfiguracionMonitoreoResponse,
    EstadisticasMonitoreoResponse,
    EstadoMonitoreoResponse,
    ExpedienteMonitoreado,
    IniciarMonitoreoRequest,
    ListaCambiosResponse,
    ListaExpedientesResponse,
    MarcarLeidoResponse,
    MonitoreoResponse,
    StartSchedulerResponse,
    StopSchedulerResponse,
)

from application.services.monitoreo_service import MonitoreoService

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
async def verificar_manual(headless: bool = True):
    """Ejecuta una verificación manual inmediata (sin afectar el scheduler).

    Útil para verificar cambios manualmente sin esperar al próximo ciclo programado.

    Args:
        headless: Si True (default), ejecuta el navegador sin interfaz gráfica.
                  Si False, muestra el navegador para depuración visual.

    Returns:
        MonitoreoResponse con cambios detectados

    Raises:
        HTTPException: Si hay error en la verificación
    """
    logger.info(f"POST /monitoreo/verificar (headless={headless})")

    try:
        container = get_container()
        scheduler = container.monitor_scheduler

        # Ejecutar verificación manual
        resultado = await scheduler.ejecutar_verificacion_manual(headless=headless)

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


# ============================================================================
# NUEVOS ENDPOINTS CRUD PARA MONITOREO
# ============================================================================

def _get_service() -> MonitoreoService:
    return MonitoreoService()


# Dependencia opcional para autenticación (fallback a usuario_id=1 para desarrollo)
async def get_optional_current_user(
    token: Annotated[Optional[str], Depends(oauth2_scheme)] = None
) -> Optional[Usuario]:
    """Obtiene el usuario actual si está autenticado, None si no."""
    if token is None:
        return None
    try:
        from .auth import get_current_user
        from sqlalchemy.orm import Session
        from infrastructure.persistence.database import get_db

        # Crear sesión para validar token
        db = next(get_db())
        try:
            return await get_current_user(token, db)
        finally:
            db.close()
    except Exception:
        return None


def _get_usuario_id_from_user(user: Optional[Usuario]) -> int:
    """Obtiene el usuario_id del usuario o fallback a 1 para desarrollo."""
    if user is not None:
        return user.id
    # Fallback para desarrollo sin autenticación
    return 1


def _get_usuario_id() -> int:
    """Fallback a usuario_id=1 para desarrollo.

    NOTA: Esta función es temporal mientras no se implementa
    autenticación completa en todos los endpoints.
    """
    return 1


# --- CONFIGURACION ---

@router.get("/configuracion", response_model=ConfiguracionMonitoreoResponse)
async def obtener_configuracion(
    current_user: Annotated[Optional[Usuario], Depends(get_optional_current_user)] = None
):
    """Obtiene la configuración de monitoreo del usuario.

    Si no existe configuración, se crea automáticamente con valores por defecto.

    Returns:
        ConfiguracionMonitoreoResponse: Configuración del usuario

    Raises:
        HTTPException 500: Si hay error en BD o no se puede crear configuración
    """
    logger.info("GET /monitoreo/configuracion")
    try:
        service = _get_service()
        usuario_id = _get_usuario_id_from_user(current_user)

        logger.debug(f"Obteniendo configuracion para usuario_id={usuario_id}")

        config = service.obtener_configuracion(usuario_id)

        # Validar que config no sea None (no deberia serlo tras los fixes)
        if not config:
            logger.error(f"obtener_configuracion() devolvio None para usuario_id={usuario_id}")
            raise HTTPException(
                status_code=500,
                detail="No se pudo obtener o crear configuracion para el usuario. Contacte al administrador."
            )

        logger.debug(f"Configuracion obtenida: usuario_id={usuario_id}, config_id={config.get('id')}")

        return ConfiguracionMonitoreoResponse(**config)

    except HTTPException:
        # Re-raise HTTPException sin modificar
        raise
    except RuntimeError as e:
        # Error especifico del repository
        logger.error(f"RuntimeError obteniendo configuracion: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error creando configuracion: {str(e)}"
        )
    except Exception as e:
        # Error inesperado
        logger.exception(f"Error inesperado obteniendo configuracion: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error del servidor: {str(e)}"
        )


@router.put("/configuracion", response_model=ConfiguracionMonitoreoResponse)
async def actualizar_configuracion(
    request: ActualizarConfiguracionRequest,
    current_user: Annotated[Optional[Usuario], Depends(get_optional_current_user)] = None
):
    """Actualiza la configuración de monitoreo del usuario."""
    logger.info("PUT /monitoreo/configuracion")
    try:
        service = _get_service()
        usuario_id = _get_usuario_id_from_user(current_user)

        logger.info(f"Actualizando configuración para usuario_id={usuario_id}")
        logger.debug(f"Datos recibidos: activo={request.activo}, frecuencia={request.frecuencia}, "
                    f"hora_inicio={request.hora_inicio}, hora_fin={request.hora_fin}, "
                    f"dias_semana={request.dias_semana}")

        config = service.actualizar_configuracion(
            usuario_id=usuario_id,
            activo=request.activo,
            frecuencia=request.frecuencia,
            notificar_email=request.notificar_email,
            notificar_sistema=request.notificar_sistema,
            hora_inicio=request.hora_inicio,
            hora_fin=request.hora_fin,
            dias_semana=request.dias_semana,
            # Opciones de extracción
            fecha_corte_dias=request.fecha_corte_dias,
            max_paginas_monitoreo=request.max_paginas_monitoreo,
            tiempo_maximo_extraccion=request.tiempo_maximo_extraccion,
            detener_en_duplicado=request.detener_en_duplicado,
            orden_extraccion=request.orden_extraccion,
            mostrar_navegador_monitoreo=request.mostrar_navegador_monitoreo
        )

        logger.info(f"Configuración actualizada exitosamente: config_id={config.get('id')}")

        # Gestionar estado del scheduler según lo solicitado por el usuario
        try:
            container = get_container()
            scheduler = container.monitor_scheduler
            estado_actual = scheduler.obtener_estado()
            activo_actual = estado_actual.get("activo")
            activo_deseado = request.activo

            # Caso 1: Usuario quiere ACTIVAR y NO está activo
            if activo_deseado and not activo_actual:
                logger.info("Activando scheduler con nueva configuración...")
                await scheduler.start()
                logger.info("✓ Scheduler activado exitosamente")

            # Caso 2: Usuario quiere DESACTIVAR y está activo
            elif not activo_deseado and activo_actual:
                logger.info("Desactivando scheduler...")
                await scheduler.stop()
                logger.info("✓ Scheduler detenido exitosamente")

            # Caso 3: Usuario quiere ACTIVAR y YA está activo (cambio de config)
            elif activo_deseado and activo_actual:
                logger.info("Reiniciando scheduler con nueva configuración...")
                await scheduler.stop()
                await scheduler.start()
                nuevo_estado = scheduler.obtener_estado()
                logger.info(
                    f"✓ Scheduler reiniciado: "
                    f"intervalo={nuevo_estado.get('intervalo_actual_minutos')}min, "
                    f"frecuencia={request.frecuencia}"
                )

            # Caso 4: Usuario quiere DESACTIVAR y YA está detenido (no hacer nada)
            else:
                logger.debug("Scheduler ya está en el estado deseado, no se requiere acción")

        except RuntimeError as e:
            # Error esperado de start() si ya está activo
            logger.error(f"Error al gestionar scheduler: {e}")
            logger.warning("La configuración se guardó pero el scheduler no se pudo gestionar")
        except Exception as e:
            logger.error(f"Error inesperado al gestionar scheduler: {e}")
            logger.warning("La configuración se guardó pero el scheduler no se pudo gestionar")

        return ConfiguracionMonitoreoResponse(**config)
    except Exception as e:
        logger.exception("Error actualizando configuración")
        raise HTTPException(status_code=500, detail=str(e))


# --- EXPEDIENTES MONITOREADOS ---

@router.get("/expedientes", response_model=ListaExpedientesResponse)
async def listar_expedientes(
    solo_activos: bool = False,
    pagina: int = 1,
    por_pagina: int = 50
):
    """Lista los expedientes monitoreados del usuario."""
    logger.info(f"GET /monitoreo/expedientes?solo_activos={solo_activos}")
    try:
        service = _get_service()
        resultado = service.listar_expedientes(
            usuario_id=_get_usuario_id(),
            solo_activos=solo_activos,
            pagina=pagina,
            por_pagina=por_pagina
        )
        return ListaExpedientesResponse(
            expedientes=[ExpedienteMonitoreado(**exp) for exp in resultado['expedientes']],
            total=resultado['total'],
            pagina=resultado['pagina'],
            por_pagina=resultado['por_pagina'],
            total_paginas=resultado['total_paginas']
        )
    except Exception as e:
        logger.exception("Error listando expedientes")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/expedientes", response_model=ExpedienteMonitoreado, status_code=201)
async def agregar_expediente(request: AgregarExpedienteRequest):
    """Agrega un expediente al monitoreo."""
    logger.info(f"POST /monitoreo/expedientes - {request.expediente_numero}")
    try:
        service = _get_service()
        exp = service.agregar_expediente(
            usuario_id=_get_usuario_id(),
            expediente_numero=request.expediente_numero,
            expediente_caratula=request.expediente_caratula,
            expediente_dependencia=request.expediente_dependencia,
            prioridad=request.prioridad,
            notas=request.notas
        )
        return ExpedienteMonitoreado(**exp)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.exception("Error agregando expediente")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/expedientes/{expediente_numero}", response_model=ExpedienteMonitoreado)
async def obtener_expediente(expediente_numero: str):
    """Obtiene un expediente monitoreado específico."""
    logger.info(f"GET /monitoreo/expedientes/{expediente_numero}")
    try:
        service = _get_service()
        exp = service.obtener_expediente(_get_usuario_id(), expediente_numero)
        if not exp:
            raise HTTPException(status_code=404, detail="Expediente no encontrado")
        return ExpedienteMonitoreado(**exp)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error obteniendo expediente")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/expedientes/{expediente_numero}", response_model=ExpedienteMonitoreado)
async def actualizar_expediente(expediente_numero: str, request: ActualizarExpedienteRequest):
    """Actualiza un expediente monitoreado."""
    logger.info(f"PUT /monitoreo/expedientes/{expediente_numero}")
    try:
        service = _get_service()
        exp = service.actualizar_expediente(
            usuario_id=_get_usuario_id(),
            expediente_numero=expediente_numero,
            activo=request.activo,
            prioridad=request.prioridad,
            notas=request.notas
        )
        if not exp:
            raise HTTPException(status_code=404, detail="Expediente no encontrado")
        return ExpedienteMonitoreado(**exp)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error actualizando expediente")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/expedientes/{expediente_numero}")
async def eliminar_expediente(expediente_numero: str):
    """Elimina un expediente del monitoreo."""
    logger.info(f"DELETE /monitoreo/expedientes/{expediente_numero}")
    try:
        service = _get_service()
        deleted = service.eliminar_expediente(_get_usuario_id(), expediente_numero)
        if not deleted:
            raise HTTPException(status_code=404, detail="Expediente no encontrado")
        return {"success": True, "mensaje": f"Expediente {expediente_numero} eliminado"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error eliminando expediente")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/expedientes/{expediente_numero}/pausar", response_model=ExpedienteMonitoreado)
async def pausar_expediente(expediente_numero: str):
    """Pausa el monitoreo de un expediente."""
    logger.info(f"POST /monitoreo/expedientes/{expediente_numero}/pausar")
    try:
        service = _get_service()
        exp = service.pausar_expediente(_get_usuario_id(), expediente_numero)
        if not exp:
            raise HTTPException(status_code=404, detail="Expediente no encontrado")
        return ExpedienteMonitoreado(**exp)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error pausando expediente")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/expedientes/{expediente_numero}/reanudar", response_model=ExpedienteMonitoreado)
async def reanudar_expediente(expediente_numero: str):
    """Reanuda el monitoreo de un expediente."""
    logger.info(f"POST /monitoreo/expedientes/{expediente_numero}/reanudar")
    try:
        service = _get_service()
        exp = service.reanudar_expediente(_get_usuario_id(), expediente_numero)
        if not exp:
            raise HTTPException(status_code=404, detail="Expediente no encontrado")
        return ExpedienteMonitoreado(**exp)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error reanudando expediente")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sincronizar")
async def sincronizar_expedientes():
    """Sincroniza todos los expedientes del sistema principal con el monitoreo.

    Este endpoint registra automáticamente todos los expedientes que están
    en el sistema principal pero no están siendo monitoreados.

    Returns:
        dict con cantidad de expedientes sincronizados
    """
    logger.info("POST /monitoreo/sincronizar")
    try:
        # Obtener expedientes del sistema principal
        container = get_container()
        expediente_repo = container.expediente_repo
        expedientes_sistema = await expediente_repo.obtener_todos()

        if not expedientes_sistema:
            return {
                "success": True,
                "mensaje": "No hay expedientes en el sistema para sincronizar",
                "total_sistema": 0,
                "nuevos_monitoreados": 0,
                "ya_monitoreados": 0
            }

        # Obtener servicio de monitoreo
        service = _get_service()
        usuario_id = _get_usuario_id()

        nuevos = 0
        ya_existentes = 0
        errores = []

        for exp in expedientes_sistema:
            try:
                # Intentar agregar al monitoreo
                service.agregar_expediente(
                    usuario_id=usuario_id,
                    expediente_numero=exp.numero,
                    expediente_caratula=exp.caratula,
                    expediente_dependencia=exp.dependencia,
                    prioridad='media'
                )
                nuevos += 1
            except ValueError as e:
                # Ya existe en monitoreo
                if "ya está siendo monitoreado" in str(e):
                    ya_existentes += 1
                else:
                    errores.append(f"{exp.numero}: {str(e)}")
            except Exception as e:
                errores.append(f"{exp.numero}: {str(e)}")

        resultado = {
            "success": True,
            "mensaje": f"Sincronización completada: {nuevos} nuevos, {ya_existentes} ya monitoreados",
            "total_sistema": len(expedientes_sistema),
            "nuevos_monitoreados": nuevos,
            "ya_monitoreados": ya_existentes
        }

        if errores:
            resultado["errores"] = errores[:10]  # Limitar a 10 errores

        return resultado

    except Exception as e:
        logger.exception("Error sincronizando expedientes")
        raise HTTPException(status_code=500, detail=str(e))


# --- CAMBIOS DETECTADOS ---

@router.get("/cambios", response_model=ListaCambiosResponse)
async def listar_cambios(
    solo_no_leidos: bool = False,
    tipo_cambio: str | None = None,
    expediente_numero: str | None = None,
    pagina: int = 1,
    por_pagina: int = 50
):
    """Lista los cambios detectados."""
    logger.info(f"GET /monitoreo/cambios?solo_no_leidos={solo_no_leidos}")
    try:
        service = _get_service()
        resultado = service.listar_cambios(
            usuario_id=_get_usuario_id(),
            solo_no_leidos=solo_no_leidos,
            tipo_cambio=tipo_cambio,
            expediente_numero=expediente_numero,
            pagina=pagina,
            por_pagina=por_pagina
        )
        return ListaCambiosResponse(**resultado)
    except Exception as e:
        logger.exception("Error listando cambios")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cambios/{cambio_id}/marcar-leido", response_model=MarcarLeidoResponse)
async def marcar_cambio_leido(cambio_id: int):
    """Marca un cambio como leído."""
    logger.info(f"POST /monitoreo/cambios/{cambio_id}/marcar-leido")
    try:
        service = _get_service()
        marcado = service.marcar_leido(cambio_id)
        return MarcarLeidoResponse(success=marcado, cantidad_marcados=1 if marcado else 0)
    except Exception as e:
        logger.exception("Error marcando cambio leído")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cambios/marcar-todos-leidos", response_model=MarcarLeidoResponse)
async def marcar_todos_leidos():
    """Marca todos los cambios como leídos."""
    logger.info("POST /monitoreo/cambios/marcar-todos-leidos")
    try:
        service = _get_service()
        cantidad = service.marcar_todos_leidos(_get_usuario_id())
        return MarcarLeidoResponse(success=True, cantidad_marcados=cantidad)
    except Exception as e:
        logger.exception("Error marcando todos leídos")
        raise HTTPException(status_code=500, detail=str(e))


# --- ESTADISTICAS ---

@router.get("/estadisticas", response_model=EstadisticasMonitoreoResponse)
async def obtener_estadisticas():
    """Obtiene estadísticas del monitoreo."""
    logger.info("GET /monitoreo/estadisticas")
    try:
        service = _get_service()
        stats = service.obtener_estadisticas(_get_usuario_id())
        return EstadisticasMonitoreoResponse(**stats)
    except Exception as e:
        logger.exception("Error obteniendo estadísticas")
        raise HTTPException(status_code=500, detail=str(e))
