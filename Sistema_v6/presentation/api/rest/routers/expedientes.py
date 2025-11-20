"""Expedientes Router - Endpoints para gestión de expedientes."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from application.dtos import (
    ExtraerExpedientesCommand,
    FiltrarExpedientesCommand,
    ListarExpedientesQuery,
    ObtenerExpedienteQuery,
)
from infrastructure.di_container import get_container
from infrastructure.exceptions import PJNError

from ..schemas.expediente_schemas import (
    ActuacionResponse,
    ExpedienteResponse,
    ExtraerExpedientesRequest,
    ExtraerExpedientesResponse,
    FiltrarExpedientesRequest,
    FiltrarExpedientesResponse,
    ListarExpedientesResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/extraer", response_model=ExtraerExpedientesResponse, status_code=status.HTTP_200_OK)
async def extraer_expedientes(request: ExtraerExpedientesRequest):
    """Extrae la lista completa de expedientes del PJN.

    Args:
        request: Datos de la petición

    Returns:
        ExtraerExpedientesResponse con resultado

    Raises:
        HTTPException: Si hay error en la extracción
    """
    logger.info("POST /expedientes/extraer")

    try:
        # Preparar comando
        guardar_en = Path(request.guardar_en) if request.guardar_en else None
        command = ExtraerExpedientesCommand(
            usuario=request.usuario,
            contrasena=request.contrasena,
            headless=request.headless,
            guardar_en=guardar_en,
        )

        # Ejecutar use case
        container = get_container()
        use_case = container.extraer_expedientes_use_case()
        result = await use_case.execute(command)

        if result.success:
            response_data = result.value
            return ExtraerExpedientesResponse(
                success=True,
                total=response_data.total,
                archivo_guardado=str(response_data.archivo_guardado) if response_data.archivo_guardado else None,
            )
        else:
            return ExtraerExpedientesResponse(
                success=False,
                total=0,
                error=result.error,
            )

    except NotImplementedError as e:
        logger.warning(f"Funcionalidad no implementada: {e}")
        return ExtraerExpedientesResponse(
            success=False,
            total=0,
            error="Scraping no implementado aún. Migración pendiente desde Sistema_v5.",
        )

    except PJNError as e:
        logger.error(f"Error PJN en extracción: {e}")
        return ExtraerExpedientesResponse(
            success=False,
            total=0,
            error=str(e),
        )

    except Exception as e:
        logger.exception("Error inesperado en extracción")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}",
        )


@router.post("/filtrar", response_model=FiltrarExpedientesResponse, status_code=status.HTTP_200_OK)
async def filtrar_expedientes(request: FiltrarExpedientesRequest):
    """Filtra expedientes según selección del usuario.

    Args:
        request: Datos de la petición

    Returns:
        FiltrarExpedientesResponse con resultado

    Raises:
        HTTPException: Si hay error en el filtrado
    """
    logger.info("POST /expedientes/filtrar")

    try:
        # Preparar comando
        command = FiltrarExpedientesCommand(
            numeros_seleccionados=request.numeros_seleccionados,
            origen=Path(request.origen),
            destino=Path(request.destino) if request.destino else None,
            incluir_activos=request.incluir_activos,
            dias_actividad=request.dias_actividad,
        )

        # Ejecutar use case
        container = get_container()
        use_case = container.filtrar_expedientes_use_case()
        result = await use_case.execute(command)

        if result.success:
            response_data = result.value
            return FiltrarExpedientesResponse(
                success=True,
                total_origen=response_data.total_origen,
                total_filtrados=response_data.total_filtrados,
                archivo_guardado=str(response_data.archivo_guardado) if response_data.archivo_guardado else None,
            )
        else:
            return FiltrarExpedientesResponse(
                success=False,
                total_origen=0,
                total_filtrados=0,
                error=result.error,
            )

    except PJNError as e:
        logger.error(f"Error PJN en filtrado: {e}")
        return FiltrarExpedientesResponse(
            success=False,
            total_origen=0,
            total_filtrados=0,
            error=str(e),
        )

    except Exception as e:
        logger.exception("Error inesperado en filtrado")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}",
        )


@router.get("", response_model=ListarExpedientesResponse, status_code=status.HTTP_200_OK)
async def listar_expedientes(activos_solo: bool = False, dias: int = 30):
    """Lista expedientes almacenados.

    Args:
        activos_solo: Si True, solo expedientes activos
        dias: Días para considerar activo

    Returns:
        ListarExpedientesResponse con lista de expedientes

    Raises:
        HTTPException: Si hay error al listar
    """
    logger.info(f"GET /expedientes (activos_solo={activos_solo}, dias={dias})")

    try:
        # Obtener repositorio
        container = get_container()
        repo = container.expediente_repo

        # Obtener expedientes
        if activos_solo:
            expedientes = await repo.obtener_activos(dias=dias)
        else:
            expedientes = await repo.obtener_todos()

        # Convertir a response
        expedientes_response = [
            ExpedienteResponse(
                numero=exp.numero,
                dependencia=exp.dependencia,
                caratula=exp.caratula,
                situacion=exp.situacion,
                ultima_actuacion=exp.ultima_actuacion,
            )
            for exp in expedientes
        ]

        return ListarExpedientesResponse(
            success=True,
            total=len(expedientes_response),
            expedientes=expedientes_response,
            pagina=1,
            por_pagina=len(expedientes_response),
            total_paginas=1,
        )

    except Exception as e:
        logger.exception("Error al listar expedientes")
        return ListarExpedientesResponse(
            success=False,
            total=0,
            expedientes=[],
            pagina=1,
            por_pagina=0,
            total_paginas=0,
            error=str(e),
        )


@router.get("/{numero}", response_model=ExpedienteResponse, status_code=status.HTTP_200_OK)
async def obtener_expediente(numero: str):
    """Obtiene un expediente por número.

    Args:
        numero: Número del expediente

    Returns:
        ExpedienteResponse con datos del expediente

    Raises:
        HTTPException: Si el expediente no existe
    """
    logger.info(f"GET /expedientes/{numero}")

    try:
        # Obtener repositorio
        container = get_container()
        repo = container.expediente_repo

        # Buscar expediente
        expediente = await repo.obtener_por_numero(numero)

        if expediente is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Expediente {numero} no encontrado",
            )

        return ExpedienteResponse(
            numero=expediente.numero,
            dependencia=expediente.dependencia,
            caratula=expediente.caratula,
            situacion=expediente.situacion,
            ultima_actuacion=expediente.ultima_actuacion,
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.exception(f"Error al obtener expediente {numero}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}",
        )


@router.post("/reload", status_code=status.HTTP_200_OK)
async def recargar_expedientes():
    """Recarga la lista de expedientes desde el almacenamiento, invalidando la caché.

    Returns:
        dict con mensaje de confirmación

    Raises:
        HTTPException: Si hay error al recargar
    """
    logger.info("POST /expedientes/reload")

    try:
        # Obtener repositorio
        container = get_container()
        repo = container.expediente_repo

        # Recargar desde archivo
        await repo.recargar()

        return {
            "success": True,
            "message": "Expedientes recargados exitosamente"
        }

    except Exception as e:
        logger.exception("Error al recargar expedientes")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}",
        )


@router.get("/{numero}/actuaciones", response_model=list[ActuacionResponse], status_code=status.HTTP_200_OK)
async def obtener_actuaciones(numero: str):
    """Obtiene las actuaciones de un expediente.

    Args:
        numero: Número del expediente

    Returns:
        Lista de actuaciones del expediente

    Raises:
        HTTPException: Si el expediente no existe o no tiene actuaciones
    """
    logger.info(f"GET /expedientes/{numero}/actuaciones")

    try:
        # Obtener repositorio de actuaciones
        container = get_container()
        actuacion_repo = container.actuacion_repo

        # Buscar actuaciones
        actuaciones = await actuacion_repo.obtener_actuaciones(numero)

        if actuaciones is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontraron actuaciones para el expediente {numero}",
            )

        # Obtener path base de workspaces para construir rutas de PDF
        from core.domain.utils import normalizar_numero_expediente
        numero_normalizado = normalizar_numero_expediente(numero).replace('-', '_')
        workspaces_base = actuacion_repo._workspaces_base

        # Buscar el directorio del expediente
        pdf_base_path = None
        if workspaces_base.exists():
            for dir_path in workspaces_base.iterdir():
                if dir_path.is_dir() and numero_normalizado in dir_path.name:
                    pdf_dir = dir_path / "pdfs"
                    if pdf_dir.exists():
                        pdf_base_path = pdf_dir
                    break

        # Convertir a response
        actuaciones_response = []
        for act in actuaciones:
            # Construir ruta_pdf si tiene archivo
            ruta_pdf = None
            if act.nombre_archivo and pdf_base_path:
                posible_ruta = pdf_base_path / act.nombre_archivo
                if posible_ruta.exists():
                    ruta_pdf = str(posible_ruta)

            actuaciones_response.append(
                ActuacionResponse(
                    indice=act.indice,
                    oficina=act.oficina,
                    tipo=act.tipo,
                    fecha=act.fecha,
                    detalle=act.detalle,
                    foja=act.foja,
                    firmante=None,  # La entidad no tiene firmante
                    archivos=[act.nombre_archivo] if act.nombre_archivo else [],
                    ruta_pdf=ruta_pdf,
                )
            )

        return actuaciones_response

    except HTTPException:
        raise

    except Exception as e:
        logger.exception(f"Error al obtener actuaciones de {numero}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}",
        )
