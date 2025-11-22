"""
Router de API para gestion de entidades extraidas (NER).

Endpoints CRUD para entidades extraidas por IA o agregadas manualmente.
"""

import logging
import re
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from infrastructure.persistence.entidades_repository import EntidadesRepository
from application.services.ia.ner_service import ENTIDADES_JURIDICAS, get_tipos_entidad_from_db


def normalizar_numero_expediente(numero: str) -> str:
    """
    Normaliza el número de expediente al formato de la BD.

    Convierte formatos como:
    - "FPO-006767-2025" -> "FPO_006767_2025"
    - "FPO 006767/2025" -> "FPO_006767_2025"
    """
    if not numero:
        return ""
    return re.sub(r'[\s\-/]', '_', numero)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/expedientes/{numero}/entidades",
    tags=["Entidades NER"]
)

# Inicializar repositorio
entidades_repo = EntidadesRepository()


# ============================================================================
# Schemas
# ============================================================================

class EntidadCreate(BaseModel):
    """Schema para crear una entidad."""
    entity_type: str = Field(..., description="Tipo de entidad (PERSONA, MONTO, etc.)")
    entity_value: str = Field(..., description="Valor de la entidad")
    actuacion_id: Optional[int] = Field(None, description="ID de la actuacion (opcional)")
    notas: Optional[str] = Field(None, description="Notas adicionales")


class EntidadUpdate(BaseModel):
    """Schema para actualizar una entidad."""
    entity_value: Optional[str] = None
    entity_type: Optional[str] = None
    notas: Optional[str] = None


class EntidadResponse(BaseModel):
    """Schema de respuesta para una entidad."""
    id: int
    expediente_numero: str
    actuacion_id: Optional[int]
    entity_type: str
    entity_value: str
    score: Optional[float]
    start_pos: Optional[int]
    end_pos: Optional[int]
    origen: str
    usuario_id: Optional[int]
    notas: Optional[str]
    fecha_creacion: str
    fecha_actualizacion: str


class EntidadesListResponse(BaseModel):
    """Schema de respuesta para lista de entidades."""
    expediente_numero: str
    total: int
    entidades: List[dict]


class EstadisticasEntidadesResponse(BaseModel):
    """Schema para estadisticas de entidades."""
    expediente_numero: str
    total: int
    total_ia: int
    total_manual: int
    por_tipo: List[dict]


class TiposEntidadResponse(BaseModel):
    """Schema para tipos de entidad disponibles."""
    tipos: List[str]


# ============================================================================
# Endpoints
# ============================================================================

@router.get("", response_model=EntidadesListResponse)
async def listar_entidades(
    numero: str,
    entity_type: Optional[str] = Query(None, description="Filtrar por tipo"),
    origen: Optional[str] = Query(None, description="Filtrar por origen (ia/manual)")
):
    """
    Lista las entidades de un expediente.

    Args:
        numero: Numero del expediente
        entity_type: Tipo de entidad para filtrar
        origen: Origen para filtrar ('ia' o 'manual')

    Returns:
        Lista de entidades
    """
    try:
        # Normalizar el número de expediente al formato de la BD
        numero_normalizado = normalizar_numero_expediente(numero)

        entidades = entidades_repo.obtener_por_expediente(
            expediente_numero=numero_normalizado,
            entity_type=entity_type,
            origen=origen
        )

        return EntidadesListResponse(
            expediente_numero=numero,
            total=len(entidades),
            entidades=entidades
        )

    except Exception as e:
        logger.error(f"Error listando entidades de {numero}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/estadisticas", response_model=EstadisticasEntidadesResponse)
async def obtener_estadisticas(numero: str):
    """
    Obtiene estadisticas de entidades de un expediente.

    Args:
        numero: Numero del expediente

    Returns:
        Estadisticas de entidades
    """
    try:
        numero_normalizado = normalizar_numero_expediente(numero)
        stats = entidades_repo.obtener_estadisticas(numero_normalizado)
        # Mantener el número original en la respuesta
        stats['expediente_numero'] = numero
        return EstadisticasEntidadesResponse(**stats)

    except Exception as e:
        logger.error(f"Error obteniendo estadisticas de {numero}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tipos", response_model=TiposEntidadResponse)
async def obtener_tipos_entidad(numero: str):
    """
    Obtiene los tipos de entidad disponibles desde la BD.

    Args:
        numero: Numero del expediente (no usado, pero necesario para ruta)

    Returns:
        Lista de tipos de entidad activos
    """
    tipos = get_tipos_entidad_from_db()
    return TiposEntidadResponse(tipos=tipos)


@router.post("", status_code=201)
async def crear_entidad(numero: str, entidad: EntidadCreate):
    """
    Crea una nueva entidad manualmente.

    Args:
        numero: Numero del expediente
        entidad: Datos de la entidad

    Returns:
        ID de la entidad creada
    """
    try:
        # Validar tipo de entidad usando tipos de la BD
        tipos_validos = get_tipos_entidad_from_db()
        if entidad.entity_type not in tipos_validos:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de entidad invalido. Opciones: {', '.join(tipos_validos)}"
            )

        numero_normalizado = normalizar_numero_expediente(numero)
        entity_id = entidades_repo.crear(
            expediente_numero=numero_normalizado,
            entity_type=entidad.entity_type,
            entity_value=entidad.entity_value,
            actuacion_id=entidad.actuacion_id,
            origen='manual',
            notas=entidad.notas
        )

        return {
            "id": entity_id,
            "message": f"Entidad creada: {entidad.entity_type}='{entidad.entity_value[:50]}...'"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando entidad: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{entidad_id}")
async def actualizar_entidad(
    numero: str,
    entidad_id: int,
    entidad: EntidadUpdate
):
    """
    Actualiza una entidad existente.

    Args:
        numero: Numero del expediente
        entidad_id: ID de la entidad
        entidad: Datos a actualizar

    Returns:
        Mensaje de exito
    """
    try:
        # Validar tipo si se proporciona usando tipos de la BD
        if entidad.entity_type:
            tipos_validos = get_tipos_entidad_from_db()
            if entidad.entity_type not in tipos_validos:
                raise HTTPException(
                    status_code=400,
                    detail=f"Tipo de entidad invalido. Opciones: {', '.join(tipos_validos)}"
                )

        updated = entidades_repo.actualizar(
            entidad_id=entidad_id,
            entity_value=entidad.entity_value,
            entity_type=entidad.entity_type,
            notas=entidad.notas
        )

        if not updated:
            raise HTTPException(status_code=404, detail="Entidad no encontrada")

        return {"message": "Entidad actualizada"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando entidad {entidad_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{entidad_id}")
async def eliminar_entidad(numero: str, entidad_id: int):
    """
    Elimina una entidad.

    Args:
        numero: Numero del expediente
        entidad_id: ID de la entidad

    Returns:
        Mensaje de exito
    """
    try:
        deleted = entidades_repo.eliminar(entidad_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Entidad no encontrada")

        return {"message": "Entidad eliminada"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando entidad {entidad_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("")
async def eliminar_todas_entidades(
    numero: str,
    origen: Optional[str] = Query(None, description="Solo eliminar de origen especifico")
):
    """
    Elimina todas las entidades de un expediente.

    Args:
        numero: Numero del expediente
        origen: Solo eliminar de origen especifico ('ia' o 'manual')

    Returns:
        Numero de entidades eliminadas
    """
    try:
        numero_normalizado = normalizar_numero_expediente(numero)
        count = entidades_repo.eliminar_por_expediente(
            expediente_numero=numero_normalizado,
            origen=origen
        )

        return {
            "message": f"Eliminadas {count} entidades",
            "count": count
        }

    except Exception as e:
        logger.error(f"Error eliminando entidades de {numero}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Router adicional para obtener entidades por actuacion
actuacion_router = APIRouter(
    prefix="/expedientes/{numero}/actuaciones/{actuacion_id}/entidades",
    tags=["Entidades NER"]
)


@actuacion_router.get("")
async def listar_entidades_actuacion(numero: str, actuacion_id: int):
    """
    Lista las entidades de una actuacion especifica.

    Args:
        numero: Numero del expediente
        actuacion_id: ID de la actuacion

    Returns:
        Lista de entidades
    """
    try:
        entidades = entidades_repo.obtener_por_actuacion(actuacion_id)

        return {
            "expediente_numero": numero,
            "actuacion_id": actuacion_id,
            "total": len(entidades),
            "entidades": entidades
        }

    except Exception as e:
        logger.error(f"Error listando entidades de actuacion {actuacion_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
