"""Expedientes Router - Endpoints para gestión de expedientes."""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, HTTPException, status, Request, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from presentation.api.rest.rate_limiter import limiter
from infrastructure.persistence.database import get_pooled_connection

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


# Response model for texto extraido
class TextoExtraidoResponse(BaseModel):
    """Respuesta con texto extraído de una actuación."""
    tiene_texto: bool
    texto_completo: Optional[str] = None
    texto_normalizado: Optional[str] = None
    preview: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    texto_por_pagina: Optional[List[Dict[str, Any]]] = None


class ActuacionConAnalisisIA(BaseModel):
    """Actuación con campos de análisis IA."""
    id: int
    indice: int
    tipo: str
    detalle: Optional[str] = None
    fecha: Optional[str] = None
    tiene_texto_extraido: bool = False
    # Campos de clasificación IA
    tipo_ia: Optional[str] = None
    confianza_ia: Optional[float] = None
    justificacion_ia: Optional[str] = None
    metodo_ia: Optional[str] = None
    fecha_clasificacion_ia: Optional[str] = None
    # Campo de indexación RAG
    indexado_rag: bool = False


class AnalisisIAExpedienteResponse(BaseModel):
    """Respuesta completa del análisis IA de un expediente."""
    expediente_numero: str
    total_actuaciones: int
    actuaciones_con_ia: int
    actuaciones_indexadas: int
    porcentaje_clasificado: float
    porcentaje_indexado: float
    actuaciones: List[ActuacionConAnalisisIA]


def _get_db_connection():
    """Obtiene conexión a MySQL desde el pool centralizado."""
    return get_pooled_connection()


@router.post("/extraer", response_model=ExtraerExpedientesResponse, status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def extraer_expedientes(request: Request, data: ExtraerExpedientesRequest):
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
        guardar_en = Path(data.guardar_en) if data.guardar_en else None
        command = ExtraerExpedientesCommand(
            usuario=data.usuario,
            contrasena=data.contrasena,
            headless=data.headless,
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
@limiter.limit("10/minute")
async def filtrar_expedientes(request: Request, data: FiltrarExpedientesRequest):
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
            numeros_seleccionados=data.numeros_seleccionados,
            origen=Path(data.origen),
            destino=Path(data.destino) if data.destino else None,
            incluir_activos=data.incluir_activos,
            dias_actividad=data.dias_actividad,
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
async def listar_expedientes(
    activos_solo: bool = False,
    dias: int = 30,
    pagina: int = Query(default=1, ge=1, description="Número de página"),
    por_pagina: int = Query(default=20, ge=1, le=100, description="Elementos por página"),
):
    """Lista expedientes almacenados con paginación.

    Args:
        activos_solo: Si True, solo expedientes activos
        dias: Días para considerar activo
        pagina: Número de página (comienza en 1)
        por_pagina: Cantidad de expedientes por página (máx 100)

    Returns:
        ListarExpedientesResponse con lista paginada de expedientes

    Raises:
        HTTPException: Si hay error al listar
    """
    logger.info(f"GET /expedientes (activos_solo={activos_solo}, dias={dias}, pagina={pagina}, por_pagina={por_pagina})")

    try:
        # Obtener repositorio
        container = get_container()
        repo = container.expediente_repo

        # Obtener todos los expedientes
        if activos_solo:
            expedientes = await repo.obtener_activos(dias=dias)
        else:
            expedientes = await repo.obtener_todos()

        # Calcular paginación
        total = len(expedientes)
        total_paginas = math.ceil(total / por_pagina) if total > 0 else 1

        # Validar página solicitada
        if pagina > total_paginas and total > 0:
            pagina = total_paginas

        # Calcular índices de slice
        inicio = (pagina - 1) * por_pagina
        fin = inicio + por_pagina

        # Obtener expedientes de la página actual
        expedientes_pagina = expedientes[inicio:fin]

        # Convertir a response
        expedientes_response = [
            ExpedienteResponse(
                numero=exp.numero,
                dependencia=exp.dependencia,
                caratula=exp.caratula,
                situacion=exp.situacion,
                ultima_actuacion=exp.ultima_actuacion,
            )
            for exp in expedientes_pagina
        ]

        return ListarExpedientesResponse(
            success=True,
            total=total,
            expedientes=expedientes_response,
            pagina=pagina,
            por_pagina=por_pagina,
            total_paginas=total_paginas,
        )

    except Exception as e:
        logger.exception("Error al listar expedientes")
        return ListarExpedientesResponse(
            success=False,
            total=0,
            expedientes=[],
            pagina=1,
            por_pagina=por_pagina,
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
                    pdf_dir = dir_path / "actuaciones"
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
                    oficina_completa=getattr(act, 'oficina_completa', None),
                    tipo=act.tipo,
                    fecha=act.fecha,
                    detalle=act.detalle,
                    foja=act.foja,
                    firmante=None,  # La entidad no tiene firmante
                    archivos=[act.nombre_archivo] if act.nombre_archivo else [],
                    ruta_pdf=ruta_pdf,
                    tiene_archivo=act.tiene_archivo,
                    nombre_archivo=act.nombre_archivo,
                    tipo_archivo=getattr(act, 'tipo_archivo', None),
                    descargado=getattr(act, 'descargado', False),
                    es_historica=getattr(act, 'es_historica', False),
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


@router.get("/{numero}/actuaciones/{indice}/pdf", status_code=status.HTTP_200_OK)
async def descargar_pdf_actuacion(numero: str, indice: int):
    """Descarga el PDF de una actuación específica.

    Args:
        numero: Número del expediente
        indice: Índice de la actuación

    Returns:
        FileResponse con el archivo PDF

    Raises:
        HTTPException: Si el archivo no existe
    """
    logger.info(f"GET /expedientes/{numero}/actuaciones/{indice}/pdf")

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

        # Buscar la actuación por índice
        actuacion = None
        for act in actuaciones:
            if act.indice == indice:
                actuacion = act
                break

        if actuacion is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontró la actuación {indice} en el expediente {numero}",
            )

        if not actuacion.nombre_archivo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"La actuación {indice} no tiene archivo adjunto",
            )

        # Obtener path base de workspaces para construir ruta de PDF
        from core.domain.utils import normalizar_numero_expediente
        numero_normalizado = normalizar_numero_expediente(numero).replace('-', '_')
        workspaces_base = actuacion_repo._workspaces_base

        # Buscar el directorio del expediente
        pdf_path = None
        if workspaces_base.exists():
            for dir_path in workspaces_base.iterdir():
                if dir_path.is_dir() and numero_normalizado in dir_path.name:
                    posible_ruta = dir_path / "actuaciones" / actuacion.nombre_archivo
                    if posible_ruta.exists():
                        pdf_path = posible_ruta
                    break

        if pdf_path is None or not pdf_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Archivo PDF no encontrado: {actuacion.nombre_archivo}",
            )

        return FileResponse(
            path=str(pdf_path),
            filename=actuacion.nombre_archivo,
            media_type="application/pdf"
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.exception(f"Error al descargar PDF de {numero}/{indice}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}",
        )


@router.get("/{numero}/actuaciones/{indice}/texto", response_model=TextoExtraidoResponse, status_code=status.HTTP_200_OK)
async def obtener_texto_actuacion(numero: str, indice: int):
    """Obtiene el texto extraído de una actuación específica.

    Args:
        numero: Número del expediente
        indice: Índice de la actuación

    Returns:
        TextoExtraidoResponse con el texto estructurado

    Raises:
        HTTPException: Si no hay texto o la actuación no existe
    """
    logger.info(f"GET /expedientes/{numero}/actuaciones/{indice}/texto")

    try:
        # Primero obtener la actuación usando el repositorio (como hace descargar_pdf)
        container = get_container()
        actuacion_repo = container.actuacion_repo

        # Buscar actuaciones del expediente
        actuaciones = await actuacion_repo.obtener_actuaciones(numero)

        if actuaciones is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontraron actuaciones para el expediente {numero}",
            )

        # Buscar la actuación por índice
        actuacion = None
        for act in actuaciones:
            if act.indice == indice:
                actuacion = act
                break

        if actuacion is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontró la actuación {indice} en el expediente {numero}",
            )

        # Ahora buscar el texto en la base de datos
        conn = _get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Buscar por expediente_numero y tipo (ya que ruta_pdf puede ser NULL)
        # Primero intentamos por tipo y detalle para mayor precisión
        query = """
            SELECT
                id,
                detalle,
                texto_json,
                tiene_texto_extraido,
                metodo_extraccion,
                texto_extraido
            FROM actuaciones
            WHERE expediente_numero = %s AND tipo = %s
            ORDER BY id
        """

        cursor.execute(query, (numero, actuacion.tipo))
        rows = cursor.fetchall()

        # Si hay múltiples resultados, intentar filtrar por detalle
        row = None
        if rows:
            if len(rows) == 1:
                row = rows[0]
            else:
                # Buscar el que coincida mejor con el índice
                # El índice en el frontend corresponde a la posición en la lista
                for i, r in enumerate(rows):
                    # Comparar por detalle si está disponible
                    if actuacion.detalle and r.get('detalle') == actuacion.detalle:
                        row = r
                        break
                # Si no encontró por detalle, usar el primero
                if row is None:
                    row = rows[0]

        # Si no encuentra, intentar con número normalizado
        if row is None:
            from core.domain.utils import normalizar_numero_expediente
            numero_normalizado = normalizar_numero_expediente(numero)
            cursor.execute(query, (numero_normalizado, actuacion.tipo))
            rows = cursor.fetchall()
            if rows:
                row = rows[0]

        cursor.close()
        conn.close()

        if row is None:
            # No hay registro en la BD - devolver respuesta vacía
            return TextoExtraidoResponse(
                tiene_texto=False,
                texto_completo=None,
                texto_normalizado=None,
                preview=None,
                metadata=None,
                texto_por_pagina=None
            )

        # Si tiene texto_json estructurado, usarlo
        if row.get('texto_json'):
            try:
                texto_data = json.loads(row['texto_json']) if isinstance(row['texto_json'], str) else row['texto_json']
                return TextoExtraidoResponse(
                    tiene_texto=True,
                    texto_completo=texto_data.get('texto_completo'),
                    texto_normalizado=texto_data.get('texto_normalizado'),
                    preview=texto_data.get('preview'),
                    metadata=texto_data.get('metadata'),
                    texto_por_pagina=texto_data.get('texto_por_pagina')
                )
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Error parseando texto_json: {e}")

        # Fallback: usar texto_extraido plano si existe
        if row.get('texto_extraido'):
            preview = row['texto_extraido'][:500] + '...' if len(row['texto_extraido']) > 500 else row['texto_extraido']
            return TextoExtraidoResponse(
                tiene_texto=True,
                texto_completo=row['texto_extraido'],
                texto_normalizado=row['texto_extraido'],
                preview=preview,
                metadata={
                    'metodo_extraccion': row.get('metodo_extraccion', 'desconocido'),
                    'tiene_texto_extraido': bool(row.get('tiene_texto_extraido', False))
                },
                texto_por_pagina=None
            )

        # No hay texto disponible
        return TextoExtraidoResponse(
            tiene_texto=False,
            texto_completo=None,
            texto_normalizado=None,
            preview=None,
            metadata=None,
            texto_por_pagina=None
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.exception(f"Error al obtener texto de {numero}/{indice}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}",
        )


@router.get("/{numero}/analisis-ia", response_model=AnalisisIAExpedienteResponse, status_code=status.HTTP_200_OK)
async def obtener_analisis_ia(numero: str):
    """Obtiene el análisis IA de todas las actuaciones de un expediente.

    Incluye para cada actuación:
    - Clasificación IA (tipo_ia, confianza_ia, justificacion_ia, metodo_ia)
    - Estado de indexación RAG
    - Resumen estadístico del expediente

    Args:
        numero: Número del expediente (normalizado o original)

    Returns:
        AnalisisIAExpedienteResponse con análisis completo

    Raises:
        HTTPException 404: Si el expediente no existe
        HTTPException 500: Error interno
    """
    logger.info(f"GET /expedientes/{numero}/analisis-ia")

    try:
        conn = _get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Obtener actuaciones con campos IA
        query = """
            SELECT
                id,
                tipo,
                detalle,
                fecha,
                tiene_texto_extraido,
                tipo_ia,
                confianza_ia,
                justificacion_ia,
                metodo_ia,
                fecha_clasificacion_ia,
                COALESCE(indexado_rag, 0) as indexado_rag
            FROM actuaciones
            WHERE expediente_numero = %s
            ORDER BY id ASC
        """
        cursor.execute(query, (numero,))
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontraron actuaciones para el expediente {numero}"
            )

        # Convertir a lista de ActuacionConAnalisisIA
        actuaciones = []
        actuaciones_con_ia = 0
        actuaciones_indexadas = 0

        for row in rows:
            # Contar estadísticas
            if row.get('tipo_ia'):
                actuaciones_con_ia += 1
            if row.get('indexado_rag'):
                actuaciones_indexadas += 1

            # Convertir fechas a string
            fecha_str = None
            if row.get('fecha'):
                fecha_val = row['fecha']
                if hasattr(fecha_val, 'strftime'):
                    fecha_str = fecha_val.strftime('%Y-%m-%d')
                else:
                    fecha_str = str(fecha_val)

            fecha_clas_str = None
            if row.get('fecha_clasificacion_ia'):
                fecha_clas_val = row['fecha_clasificacion_ia']
                if hasattr(fecha_clas_val, 'strftime'):
                    fecha_clas_str = fecha_clas_val.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    fecha_clas_str = str(fecha_clas_val)

            actuaciones.append(ActuacionConAnalisisIA(
                id=row['id'],
                indice=row['id'],  # Usar id como indice
                tipo=row['tipo'] or '',
                detalle=row.get('detalle'),
                fecha=fecha_str,
                tiene_texto_extraido=bool(row.get('tiene_texto_extraido', False)),
                tipo_ia=row.get('tipo_ia'),
                confianza_ia=float(row['confianza_ia']) if row.get('confianza_ia') is not None else None,
                justificacion_ia=row.get('justificacion_ia'),
                metodo_ia=row.get('metodo_ia'),
                fecha_clasificacion_ia=fecha_clas_str,
                indexado_rag=bool(row.get('indexado_rag', False))
            ))

        total = len(actuaciones)
        porcentaje_clasificado = (actuaciones_con_ia / total * 100) if total > 0 else 0.0
        porcentaje_indexado = (actuaciones_indexadas / total * 100) if total > 0 else 0.0

        return AnalisisIAExpedienteResponse(
            expediente_numero=numero,
            total_actuaciones=total,
            actuaciones_con_ia=actuaciones_con_ia,
            actuaciones_indexadas=actuaciones_indexadas,
            porcentaje_clasificado=round(porcentaje_clasificado, 1),
            porcentaje_indexado=round(porcentaje_indexado, 1),
            actuaciones=actuaciones
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.exception(f"Error al obtener análisis IA de {numero}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}",
        )


# ============================================================================
# Endpoint de Inteligencia Consolidada
# ============================================================================

class EntidadNormalizadaDTO(BaseModel):
    """Entidad extraída y normalizada."""
    original: str
    normalized: str
    label: str
    score: float
    normalization_type: Optional[str] = None


class ParteProcesalDTO(BaseModel):
    """Parte procesal identificada."""
    nombre: str
    rol: str  # ACTOR, DEMANDADO, JUEZ, ABOGADO, PERITO
    abogado: Optional[str] = None


class AnalisisActuacionDTO(BaseModel):
    """Análisis de una actuación individual."""
    id: int
    tipo: str
    tipo_ia: Optional[str] = None
    confianza_ia: Optional[float] = None
    fecha: Optional[str] = None
    entidades: List[EntidadNormalizadaDTO] = []
    indexado_rag: bool = False


class InteligenciaExpedienteResponse(BaseModel):
    """Response consolidada de inteligencia del expediente."""
    expediente_numero: str
    # Resumen (se genera en frontend o con LLM en PASO 9)
    resumen_ejecutivo: Optional[str] = None
    # Partes procesales agrupadas
    partes_procesales: Dict[str, List[ParteProcesalDTO]]
    # Entidades normalizadas agrupadas por tipo
    entidades_normalizadas: Dict[str, List[EntidadNormalizadaDTO]]
    # Análisis por actuación
    analisis_actuaciones: List[AnalisisActuacionDTO]
    # Estadísticas
    total_actuaciones: int
    total_entidades: int
    actuaciones_con_ia: int
    actuaciones_indexadas: int


@router.get("/{numero}/inteligencia", response_model=InteligenciaExpedienteResponse, status_code=status.HTTP_200_OK)
async def obtener_inteligencia_expediente(numero: str):
    """Obtiene análisis de inteligencia consolidado del expediente.

    Incluye:
    - Entidades normalizadas agrupadas (fechas, montos, personas, normas)
    - Partes procesales (actor, demandado, abogados, juez)
    - Análisis por actuación con clasificación IA
    - Estadísticas generales

    Args:
        numero: Número del expediente

    Returns:
        InteligenciaExpedienteResponse con análisis consolidado

    Raises:
        HTTPException 404: Si el expediente no existe
        HTTPException 500: Error interno
    """
    from urllib.parse import unquote
    numero = unquote(numero)  # Decodificar %2F -> /
    logger.info(f"GET /expedientes/{numero}/inteligencia")

    try:
        conn = _get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Obtener actuaciones (sin texto_extraido para mejor performance)
        query = """
            SELECT
                id,
                tipo,
                detalle,
                fecha,
                tipo_ia,
                confianza_ia,
                COALESCE(indexado_rag, 0) as indexado_rag
            FROM actuaciones
            WHERE expediente_numero = %s
            ORDER BY id ASC
        """
        cursor.execute(query, (numero,))
        rows = cursor.fetchall()

        # Obtener entidades pre-calculadas de MySQL (evita reprocesar NER)
        entidades_query = """
            SELECT entity_type, entity_value, actuacion_id, score
            FROM entidades_extraidas
            WHERE expediente_numero = %s
        """
        cursor.execute(entidades_query, (numero,))
        entidades_db = cursor.fetchall()

        cursor.close()
        conn.close()

        # Indexar entidades por actuación para acceso rápido
        entidades_por_actuacion: Dict[int, list] = {}
        for ent in entidades_db:
            act_id = ent.get('actuacion_id')
            if act_id:
                if act_id not in entidades_por_actuacion:
                    entidades_por_actuacion[act_id] = []
                entidades_por_actuacion[act_id].append(ent)

        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontraron actuaciones para el expediente {numero}"
            )

        # Procesar actuaciones y extraer entidades
        analisis_actuaciones = []
        entidades_por_tipo: Dict[str, List[EntidadNormalizadaDTO]] = {
            'FECHA': [],
            'MONTO': [],
            'PERSONA': [],
            'NORMA': [],
            'TRIBUNAL': [],
            'OTROS': []
        }
        partes_procesales: Dict[str, List[ParteProcesalDTO]] = {
            'ACTOR': [],
            'DEMANDADO': [],
            'ABOGADO': [],
            'JUEZ': [],
            'PERITO': []
        }

        actuaciones_con_ia = 0
        actuaciones_indexadas = 0
        total_entidades = 0

        for row in rows:
            act_id = row['id']

            # Contar estadísticas
            if row.get('tipo_ia'):
                actuaciones_con_ia += 1
            if row.get('indexado_rag'):
                actuaciones_indexadas += 1

            # Convertir fecha
            fecha_str = None
            if row.get('fecha'):
                fecha_val = row['fecha']
                if hasattr(fecha_val, 'strftime'):
                    fecha_str = fecha_val.strftime('%Y-%m-%d')
                else:
                    fecha_str = str(fecha_val)

            # Obtener entidades pre-calculadas de MySQL (sin reprocesar NER)
            entidades_actuacion = []
            entidades_act_db = entidades_por_actuacion.get(act_id, [])

            for ent in entidades_act_db:
                entity_type = ent.get('entity_type', 'OTROS')
                entity_value = ent.get('entity_value', '')
                score = float(ent.get('score') or 0.8)

                ent_dto = EntidadNormalizadaDTO(
                    original=entity_value,
                    normalized=entity_value,
                    label=entity_type,
                    score=score,
                    normalization_type='db_cached'
                )
                entidades_actuacion.append(ent_dto)
                total_entidades += 1

                # Agrupar por tipo
                label_upper = entity_type.upper()
                if label_upper in ['FECHA', 'PLAZO', 'VENCIMIENTO']:
                    entidades_por_tipo['FECHA'].append(ent_dto)
                elif label_upper in ['MONTO', 'DINERO', 'HONORARIOS', 'CAPITAL']:
                    entidades_por_tipo['MONTO'].append(ent_dto)
                elif label_upper in ['PERSONA', 'JUEZ', 'ABOGADO', 'ACTOR', 'DEMANDADO', 'PERITO', 'TESTIGO']:
                    entidades_por_tipo['PERSONA'].append(ent_dto)
                    # También agregar a partes procesales si aplica
                    if label_upper in partes_procesales:
                        partes_procesales[label_upper].append(
                            ParteProcesalDTO(
                                nombre=entity_value,
                                rol=label_upper
                            )
                        )
                elif label_upper in ['NORMA', 'LEY', 'ARTICULO', 'DECRETO']:
                    entidades_por_tipo['NORMA'].append(ent_dto)
                elif label_upper == 'TRIBUNAL':
                    entidades_por_tipo['TRIBUNAL'].append(ent_dto)
                else:
                    entidades_por_tipo['OTROS'].append(ent_dto)

            analisis_actuaciones.append(AnalisisActuacionDTO(
                id=act_id,
                tipo=row['tipo'] or '',
                tipo_ia=row.get('tipo_ia'),
                confianza_ia=float(row['confianza_ia']) if row.get('confianza_ia') else None,
                fecha=fecha_str,
                entidades=entidades_actuacion,
                indexado_rag=bool(row.get('indexado_rag'))
            ))

        # Eliminar duplicados en entidades por normalized value
        for tipo in entidades_por_tipo:
            seen = set()
            unique = []
            for ent in entidades_por_tipo[tipo]:
                if ent.normalized not in seen:
                    seen.add(ent.normalized)
                    unique.append(ent)
            entidades_por_tipo[tipo] = unique

        # Eliminar duplicados en partes procesales
        for rol in partes_procesales:
            seen = set()
            unique = []
            for parte in partes_procesales[rol]:
                if parte.nombre not in seen:
                    seen.add(parte.nombre)
                    unique.append(parte)
            partes_procesales[rol] = unique

        return InteligenciaExpedienteResponse(
            expediente_numero=numero,
            resumen_ejecutivo=None,  # Se implementará en PASO 9
            partes_procesales=partes_procesales,
            entidades_normalizadas=entidades_por_tipo,
            analisis_actuaciones=analisis_actuaciones,
            total_actuaciones=len(rows),
            total_entidades=total_entidades,
            actuaciones_con_ia=actuaciones_con_ia,
            actuaciones_indexadas=actuaciones_indexadas
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.exception(f"Error al obtener inteligencia de {numero}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}",
        )
