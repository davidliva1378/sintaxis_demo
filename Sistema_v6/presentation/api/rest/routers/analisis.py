"""
Router REST API para Analisis de Usuario.

Endpoints para:
- Obtener notas de actuaciones de un expediente
- Crear/actualizar notas
- Eliminar notas
- Gestionar tags y destacados
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import os
import json

import mysql.connector

logger = logging.getLogger(__name__)


# ============================================================================
# Modelos de Request/Response
# ============================================================================


class NotaActuacionBase(BaseModel):
    """Base para nota de actuacion"""
    nota: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    destacado: bool = False
    oculto: bool = False
    color: Optional[str] = None


class NotaActuacionCreate(NotaActuacionBase):
    """Request para crear/actualizar nota"""
    actuacion_indice: int


class NotaActuacionUpdate(NotaActuacionBase):
    """Request para actualizar nota"""
    pass


class NotaActuacionResponse(NotaActuacionBase):
    """Response con nota de actuacion"""
    id: int
    expediente_numero: str
    actuacion_indice: int
    created_at: datetime
    updated_at: datetime


class NotasExpedienteResponse(BaseModel):
    """Response con todas las notas de un expediente"""
    expediente_numero: str
    total_notas: int
    total_destacados: int
    notas: List[NotaActuacionResponse]


class DestacadoGlobalResponse(BaseModel):
    """Response con una nota destacada global"""
    id: int
    expediente_numero: str
    actuacion_indice: int
    nota: Optional[str]
    tags: List[str]
    color: Optional[str]
    created_at: datetime
    updated_at: datetime


class DestacadosGlobalListResponse(BaseModel):
    """Response con todos los destacados agrupados por expediente"""
    total_destacados: int
    expedientes: dict  # {numero: [DestacadoGlobalResponse]}


# ============================================================================
# Dependencias
# ============================================================================


def get_db_config() -> dict:
    """Obtiene la configuracion de base de datos."""
    return {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "database": os.getenv("MYSQL_DATABASE", "sintaxis"),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
    }


def get_connection():
    """Obtiene conexion a MySQL."""
    config = get_db_config()
    return mysql.connector.connect(**config)


# Placeholder para obtener user_id del token (se debe implementar con auth real)
async def get_current_user_id() -> int:
    """Obtiene el ID del usuario actual desde el token JWT."""
    # TODO: Implementar extraccion real del user_id desde el token
    # Por ahora retornamos 1 (admin) para desarrollo
    return 1


# ============================================================================
# Router
# ============================================================================


router = APIRouter(
    prefix="/analisis",
    tags=["Analisis de Usuario"]
)


@router.get("/expediente/{numero}/notas", response_model=NotasExpedienteResponse)
async def obtener_notas_expediente(
    numero: str,
    user_id: int = Depends(get_current_user_id)
):
    """
    Obtiene todas las notas del usuario para un expediente.

    Args:
        numero: Numero del expediente

    Returns:
        Lista de notas del usuario para las actuaciones del expediente
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT
                id,
                expediente_numero,
                actuacion_indice,
                nota,
                tags,
                destacado,
                oculto,
                color,
                created_at,
                updated_at
            FROM usuario_actuaciones_notas
            WHERE user_id = %s AND expediente_numero = %s
            ORDER BY actuacion_indice ASC
        """

        cursor.execute(query, (user_id, numero))
        notas_raw = cursor.fetchall()

        cursor.close()
        conn.close()

        # Convertir a response
        notas = []
        total_destacados = 0
        for n in notas_raw:
            tags = []
            if n['tags']:
                try:
                    tags = json.loads(n['tags']) if isinstance(n['tags'], str) else n['tags']
                except:
                    tags = []

            if n['destacado']:
                total_destacados += 1

            notas.append(NotaActuacionResponse(
                id=n['id'],
                expediente_numero=n['expediente_numero'],
                actuacion_indice=n['actuacion_indice'],
                nota=n['nota'],
                tags=tags,
                destacado=bool(n['destacado']),
                oculto=bool(n['oculto']),
                color=n['color'],
                created_at=n['created_at'],
                updated_at=n['updated_at']
            ))

        return NotasExpedienteResponse(
            expediente_numero=numero,
            total_notas=len(notas),
            total_destacados=total_destacados,
            notas=notas
        )

    except Exception as e:
        logger.error(f"Error obteniendo notas del expediente {numero}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener notas: {str(e)}"
        )


@router.post("/expediente/{numero}/notas", response_model=NotaActuacionResponse)
async def crear_nota_actuacion(
    numero: str,
    request: NotaActuacionCreate,
    user_id: int = Depends(get_current_user_id)
):
    """
    Crea o actualiza una nota para una actuacion.

    Args:
        numero: Numero del expediente
        request: Datos de la nota

    Returns:
        Nota creada/actualizada
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Usar INSERT ... ON DUPLICATE KEY UPDATE para upsert
        tags_json = json.dumps(request.tags) if request.tags else None

        query = """
            INSERT INTO usuario_actuaciones_notas
                (user_id, expediente_numero, actuacion_indice, nota, tags, destacado, oculto, color)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                nota = VALUES(nota),
                tags = VALUES(tags),
                destacado = VALUES(destacado),
                oculto = VALUES(oculto),
                color = VALUES(color),
                updated_at = CURRENT_TIMESTAMP
        """

        cursor.execute(query, (
            user_id,
            numero,
            request.actuacion_indice,
            request.nota,
            tags_json,
            request.destacado,
            request.oculto,
            request.color
        ))

        conn.commit()

        # Obtener la nota insertada/actualizada
        cursor.execute("""
            SELECT * FROM usuario_actuaciones_notas
            WHERE user_id = %s AND expediente_numero = %s AND actuacion_indice = %s
        """, (user_id, numero, request.actuacion_indice))

        nota = cursor.fetchone()

        cursor.close()
        conn.close()

        if not nota:
            raise HTTPException(status_code=500, detail="Error al guardar nota")

        tags = []
        if nota['tags']:
            try:
                tags = json.loads(nota['tags']) if isinstance(nota['tags'], str) else nota['tags']
            except:
                tags = []

        return NotaActuacionResponse(
            id=nota['id'],
            expediente_numero=nota['expediente_numero'],
            actuacion_indice=nota['actuacion_indice'],
            nota=nota['nota'],
            tags=tags,
            destacado=bool(nota['destacado']),
            oculto=bool(nota['oculto']),
            color=nota['color'],
            created_at=nota['created_at'],
            updated_at=nota['updated_at']
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando nota para {numero}/{request.actuacion_indice}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear nota: {str(e)}"
        )


@router.put("/expediente/{numero}/notas/{indice}", response_model=NotaActuacionResponse)
async def actualizar_nota_actuacion(
    numero: str,
    indice: int,
    request: NotaActuacionUpdate,
    user_id: int = Depends(get_current_user_id)
):
    """
    Actualiza una nota existente.

    Args:
        numero: Numero del expediente
        indice: Indice de la actuacion
        request: Datos a actualizar

    Returns:
        Nota actualizada
    """
    # Reusar la logica de crear (upsert)
    create_request = NotaActuacionCreate(
        actuacion_indice=indice,
        nota=request.nota,
        tags=request.tags,
        destacado=request.destacado,
        oculto=request.oculto,
        color=request.color
    )
    return await crear_nota_actuacion(numero, create_request, user_id)


@router.delete("/expediente/{numero}/notas/{indice}")
async def eliminar_nota_actuacion(
    numero: str,
    indice: int,
    user_id: int = Depends(get_current_user_id)
):
    """
    Elimina una nota de actuacion.

    Args:
        numero: Numero del expediente
        indice: Indice de la actuacion

    Returns:
        Mensaje de confirmacion
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            DELETE FROM usuario_actuaciones_notas
            WHERE user_id = %s AND expediente_numero = %s AND actuacion_indice = %s
        """

        cursor.execute(query, (user_id, numero, indice))
        affected = cursor.rowcount

        conn.commit()
        cursor.close()
        conn.close()

        if affected == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontro nota para actuacion {indice}"
            )

        return {"mensaje": "Nota eliminada", "actuacion_indice": indice}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando nota para {numero}/{indice}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al eliminar nota: {str(e)}"
        )


@router.post("/expediente/{numero}/notas/{indice}/toggle-destacado")
async def toggle_destacado(
    numero: str,
    indice: int,
    user_id: int = Depends(get_current_user_id)
):
    """
    Alterna el estado destacado de una actuacion.

    Args:
        numero: Numero del expediente
        indice: Indice de la actuacion

    Returns:
        Nuevo estado de destacado
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Obtener estado actual o crear nuevo
        cursor.execute("""
            SELECT destacado FROM usuario_actuaciones_notas
            WHERE user_id = %s AND expediente_numero = %s AND actuacion_indice = %s
        """, (user_id, numero, indice))

        result = cursor.fetchone()

        if result:
            # Toggle existente
            new_value = not bool(result['destacado'])
            cursor.execute("""
                UPDATE usuario_actuaciones_notas
                SET destacado = %s, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s AND expediente_numero = %s AND actuacion_indice = %s
            """, (new_value, user_id, numero, indice))
        else:
            # Crear nuevo con destacado = true
            new_value = True
            cursor.execute("""
                INSERT INTO usuario_actuaciones_notas
                    (user_id, expediente_numero, actuacion_indice, destacado)
                VALUES (%s, %s, %s, %s)
            """, (user_id, numero, indice, True))

        conn.commit()
        cursor.close()
        conn.close()

        return {"actuacion_indice": indice, "destacado": new_value}

    except Exception as e:
        logger.error(f"Error toggling destacado para {numero}/{indice}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al cambiar destacado: {str(e)}"
        )


@router.get("/destacados")
async def obtener_todos_destacados(
    user_id: int = Depends(get_current_user_id)
):
    """
    Obtiene todas las notas destacadas del usuario agrupadas por expediente.

    Returns:
        Lista de destacados agrupados por expediente
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT
                id,
                expediente_numero,
                actuacion_indice,
                nota,
                tags,
                color,
                created_at,
                updated_at
            FROM usuario_actuaciones_notas
            WHERE user_id = %s AND destacado = 1
            ORDER BY expediente_numero, actuacion_indice
        """

        cursor.execute(query, (user_id,))
        notas_raw = cursor.fetchall()

        cursor.close()
        conn.close()

        # Agrupar por expediente
        expedientes = {}
        for n in notas_raw:
            tags = []
            if n['tags']:
                try:
                    tags = json.loads(n['tags']) if isinstance(n['tags'], str) else n['tags']
                except:
                    tags = []

            nota_data = {
                "id": n['id'],
                "expediente_numero": n['expediente_numero'],
                "actuacion_indice": n['actuacion_indice'],
                "nota": n['nota'],
                "tags": tags,
                "color": n['color'],
                "created_at": n['created_at'].isoformat() if n['created_at'] else None,
                "updated_at": n['updated_at'].isoformat() if n['updated_at'] else None
            }

            if n['expediente_numero'] not in expedientes:
                expedientes[n['expediente_numero']] = []
            expedientes[n['expediente_numero']].append(nota_data)

        return {
            "total_destacados": len(notas_raw),
            "expedientes": expedientes
        }

    except Exception as e:
        logger.error(f"Error obteniendo destacados globales: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener destacados: {str(e)}"
        )


@router.get("/expediente/{numero}/exportar")
async def exportar_notas(
    numero: str,
    formato: str = "json",
    user_id: int = Depends(get_current_user_id)
):
    """
    Exporta las notas de un expediente en el formato especificado.

    Args:
        numero: Numero del expediente
        formato: Formato de exportacion (json, csv)

    Returns:
        Datos exportados
    """
    from fastapi.responses import Response
    import csv
    import io

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT
                actuacion_indice,
                nota,
                tags,
                destacado,
                color,
                created_at,
                updated_at
            FROM usuario_actuaciones_notas
            WHERE user_id = %s AND expediente_numero = %s
            ORDER BY actuacion_indice ASC
        """

        cursor.execute(query, (user_id, numero))
        notas_raw = cursor.fetchall()

        cursor.close()
        conn.close()

        if formato == "csv":
            # Exportar a CSV
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['actuacion_indice', 'nota', 'tags', 'destacado', 'color', 'created_at', 'updated_at'])

            for n in notas_raw:
                tags = n['tags']
                if tags:
                    try:
                        tags = json.loads(tags) if isinstance(tags, str) else tags
                        tags = ','.join(tags)
                    except:
                        tags = ''
                else:
                    tags = ''

                writer.writerow([
                    n['actuacion_indice'],
                    n['nota'] or '',
                    tags,
                    '1' if n['destacado'] else '0',
                    n['color'] or '',
                    n['created_at'].isoformat() if n['created_at'] else '',
                    n['updated_at'].isoformat() if n['updated_at'] else ''
                ])

            return Response(
                content=output.getvalue(),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=notas_{numero}.csv"
                }
            )
        else:
            # Exportar a JSON
            notas = []
            for n in notas_raw:
                tags = []
                if n['tags']:
                    try:
                        tags = json.loads(n['tags']) if isinstance(n['tags'], str) else n['tags']
                    except:
                        tags = []

                notas.append({
                    "actuacion_indice": n['actuacion_indice'],
                    "nota": n['nota'],
                    "tags": tags,
                    "destacado": bool(n['destacado']),
                    "color": n['color'],
                    "created_at": n['created_at'].isoformat() if n['created_at'] else None,
                    "updated_at": n['updated_at'].isoformat() if n['updated_at'] else None
                })

            export_data = {
                "expediente_numero": numero,
                "total_notas": len(notas),
                "exportado_at": datetime.now().isoformat(),
                "notas": notas
            }

            return Response(
                content=json.dumps(export_data, indent=2, ensure_ascii=False),
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename=notas_{numero}.json"
                }
            )

    except Exception as e:
        logger.error(f"Error exportando notas del expediente {numero}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al exportar notas: {str(e)}"
        )
