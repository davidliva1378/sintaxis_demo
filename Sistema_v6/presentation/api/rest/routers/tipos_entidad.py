"""
Router de API para gestión de tipos de entidad personalizados.

Endpoints CRUD para tipos de entidad que pueden ser agregados por el usuario.
"""

import logging
import os
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import mysql.connector

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/tipos-entidad",
    tags=["Tipos de Entidad"]
)


# ============================================================================
# Schemas
# ============================================================================

class TipoEntidadCreate(BaseModel):
    """Schema para crear un tipo de entidad."""
    nombre: str = Field(..., min_length=2, max_length=50, description="Nombre en mayúsculas")
    descripcion: Optional[str] = Field(None, max_length=200, description="Descripción del tipo")
    color: Optional[str] = Field("gray", max_length=20, description="Color para UI")


class TipoEntidadUpdate(BaseModel):
    """Schema para actualizar un tipo de entidad."""
    descripcion: Optional[str] = Field(None, max_length=200)
    color: Optional[str] = Field(None, max_length=20)
    activo: Optional[bool] = None


class TipoEntidadResponse(BaseModel):
    """Schema de respuesta para un tipo de entidad."""
    id: int
    nombre: str
    descripcion: Optional[str]
    color: str
    es_predefinido: bool
    activo: bool


class TiposEntidadListResponse(BaseModel):
    """Schema de respuesta para lista de tipos."""
    total: int
    tipos: List[TipoEntidadResponse]


# ============================================================================
# Helpers
# ============================================================================

def _get_connection():
    """Obtiene conexión a MySQL."""
    return mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', ''),
        database=os.getenv('MYSQL_DATABASE', 'sintaxis')
    )


# ============================================================================
# Endpoints
# ============================================================================

@router.get("", response_model=TiposEntidadListResponse)
async def listar_tipos_entidad(
    solo_activos: bool = Query(True, description="Solo tipos activos"),
    incluir_predefinidos: bool = Query(True, description="Incluir tipos predefinidos")
):
    """
    Lista todos los tipos de entidad.

    Args:
        solo_activos: Solo mostrar tipos activos
        incluir_predefinidos: Incluir tipos predefinidos del sistema

    Returns:
        Lista de tipos de entidad
    """
    try:
        conn = _get_connection()
        cursor = conn.cursor(dictionary=True)

        query = "SELECT id, nombre, descripcion, color, es_predefinido, activo FROM tipos_entidad_custom WHERE 1=1"
        params = []

        if solo_activos:
            query += " AND activo = TRUE"

        if not incluir_predefinidos:
            query += " AND es_predefinido = FALSE"

        query += " ORDER BY es_predefinido DESC, nombre ASC"

        cursor.execute(query, params)
        tipos = cursor.fetchall()

        cursor.close()
        conn.close()

        return TiposEntidadListResponse(
            total=len(tipos),
            tipos=[TipoEntidadResponse(**t) for t in tipos]
        )

    except Exception as e:
        logger.error(f"Error listando tipos de entidad: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tipo_id}", response_model=TipoEntidadResponse)
async def obtener_tipo_entidad(tipo_id: int):
    """
    Obtiene un tipo de entidad por ID.

    Args:
        tipo_id: ID del tipo

    Returns:
        Tipo de entidad
    """
    try:
        conn = _get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT id, nombre, descripcion, color, es_predefinido, activo FROM tipos_entidad_custom WHERE id = %s",
            (tipo_id,)
        )
        tipo = cursor.fetchone()

        cursor.close()
        conn.close()

        if not tipo:
            raise HTTPException(status_code=404, detail="Tipo de entidad no encontrado")

        return TipoEntidadResponse(**tipo)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo tipo de entidad {tipo_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", status_code=201, response_model=TipoEntidadResponse)
async def crear_tipo_entidad(tipo: TipoEntidadCreate):
    """
    Crea un nuevo tipo de entidad personalizado.

    Args:
        tipo: Datos del tipo

    Returns:
        Tipo creado
    """
    try:
        # Normalizar nombre a mayúsculas
        nombre = tipo.nombre.upper().strip()

        # Validar formato
        if not nombre.replace("_", "").isalpha():
            raise HTTPException(
                status_code=400,
                detail="El nombre solo puede contener letras y guiones bajos"
            )

        conn = _get_connection()
        cursor = conn.cursor(dictionary=True)

        # Verificar si ya existe
        cursor.execute("SELECT id FROM tipos_entidad_custom WHERE nombre = %s", (nombre,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            raise HTTPException(
                status_code=400,
                detail=f"Ya existe un tipo con nombre '{nombre}'"
            )

        # Insertar
        cursor.execute(
            """
            INSERT INTO tipos_entidad_custom (nombre, descripcion, color, es_predefinido, activo)
            VALUES (%s, %s, %s, FALSE, TRUE)
            """,
            (nombre, tipo.descripcion, tipo.color or "gray")
        )
        conn.commit()

        tipo_id = cursor.lastrowid

        # Obtener el tipo creado
        cursor.execute(
            "SELECT id, nombre, descripcion, color, es_predefinido, activo FROM tipos_entidad_custom WHERE id = %s",
            (tipo_id,)
        )
        nuevo_tipo = cursor.fetchone()

        cursor.close()
        conn.close()

        logger.info(f"Tipo de entidad creado: {nombre}")

        return TipoEntidadResponse(**nuevo_tipo)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando tipo de entidad: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{tipo_id}", response_model=TipoEntidadResponse)
async def actualizar_tipo_entidad(tipo_id: int, tipo: TipoEntidadUpdate):
    """
    Actualiza un tipo de entidad.

    Args:
        tipo_id: ID del tipo
        tipo: Datos a actualizar

    Returns:
        Tipo actualizado
    """
    try:
        conn = _get_connection()
        cursor = conn.cursor(dictionary=True)

        # Verificar que existe
        cursor.execute(
            "SELECT id, es_predefinido FROM tipos_entidad_custom WHERE id = %s",
            (tipo_id,)
        )
        existing = cursor.fetchone()

        if not existing:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Tipo de entidad no encontrado")

        # Construir query de actualización
        updates = []
        params = []

        if tipo.descripcion is not None:
            updates.append("descripcion = %s")
            params.append(tipo.descripcion)

        if tipo.color is not None:
            updates.append("color = %s")
            params.append(tipo.color)

        if tipo.activo is not None:
            updates.append("activo = %s")
            params.append(tipo.activo)

        if not updates:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")

        params.append(tipo_id)
        cursor.execute(
            f"UPDATE tipos_entidad_custom SET {', '.join(updates)} WHERE id = %s",
            params
        )
        conn.commit()

        # Obtener el tipo actualizado
        cursor.execute(
            "SELECT id, nombre, descripcion, color, es_predefinido, activo FROM tipos_entidad_custom WHERE id = %s",
            (tipo_id,)
        )
        tipo_actualizado = cursor.fetchone()

        cursor.close()
        conn.close()

        return TipoEntidadResponse(**tipo_actualizado)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando tipo de entidad {tipo_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{tipo_id}")
async def eliminar_tipo_entidad(tipo_id: int):
    """
    Elimina un tipo de entidad personalizado.

    Solo se pueden eliminar tipos no predefinidos.

    Args:
        tipo_id: ID del tipo

    Returns:
        Mensaje de éxito
    """
    try:
        conn = _get_connection()
        cursor = conn.cursor(dictionary=True)

        # Verificar que existe y no es predefinido
        cursor.execute(
            "SELECT id, nombre, es_predefinido FROM tipos_entidad_custom WHERE id = %s",
            (tipo_id,)
        )
        tipo = cursor.fetchone()

        if not tipo:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Tipo de entidad no encontrado")

        if tipo['es_predefinido']:
            cursor.close()
            conn.close()
            raise HTTPException(
                status_code=400,
                detail="No se pueden eliminar tipos predefinidos del sistema"
            )

        # Verificar si hay entidades usando este tipo
        cursor.execute(
            "SELECT COUNT(*) as count FROM entidades_extraidas WHERE entity_type = %s",
            (tipo['nombre'],)
        )
        count = cursor.fetchone()['count']

        if count > 0:
            cursor.close()
            conn.close()
            raise HTTPException(
                status_code=400,
                detail=f"No se puede eliminar: hay {count} entidades usando este tipo. Desactívelo en su lugar."
            )

        # Eliminar
        cursor.execute("DELETE FROM tipos_entidad_custom WHERE id = %s", (tipo_id,))
        conn.commit()

        cursor.close()
        conn.close()

        logger.info(f"Tipo de entidad eliminado: {tipo['nombre']}")

        return {"message": f"Tipo '{tipo['nombre']}' eliminado"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando tipo de entidad {tipo_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{tipo_id}/toggle")
async def toggle_tipo_entidad(tipo_id: int):
    """
    Activa/desactiva un tipo de entidad.

    Args:
        tipo_id: ID del tipo

    Returns:
        Estado actualizado
    """
    try:
        conn = _get_connection()
        cursor = conn.cursor(dictionary=True)

        # Obtener estado actual
        cursor.execute(
            "SELECT id, nombre, activo FROM tipos_entidad_custom WHERE id = %s",
            (tipo_id,)
        )
        tipo = cursor.fetchone()

        if not tipo:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Tipo de entidad no encontrado")

        # Toggle
        nuevo_estado = not tipo['activo']
        cursor.execute(
            "UPDATE tipos_entidad_custom SET activo = %s WHERE id = %s",
            (nuevo_estado, tipo_id)
        )
        conn.commit()

        cursor.close()
        conn.close()

        estado = "activado" if nuevo_estado else "desactivado"
        logger.info(f"Tipo {tipo['nombre']} {estado}")

        return {
            "message": f"Tipo '{tipo['nombre']}' {estado}",
            "activo": nuevo_estado
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggle tipo de entidad {tipo_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
