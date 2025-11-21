"""
Router REST API para Modulo Agenda.

Endpoints para:
- CRUD de eventos/tareas
- Consulta por rango de fechas
- Importar vencimientos como eventos
- Resumen de proximos eventos
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from datetime import datetime, date
from enum import Enum
import logging
import os

import mysql.connector

logger = logging.getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================

class TipoEvento(str, Enum):
    vencimiento = "vencimiento"
    audiencia = "audiencia"
    tarea = "tarea"
    recordatorio = "recordatorio"
    otro = "otro"


class Prioridad(str, Enum):
    baja = "baja"
    media = "media"
    alta = "alta"
    urgente = "urgente"


class EstadoEvento(str, Enum):
    pendiente = "pendiente"
    en_progreso = "en_progreso"
    completado = "completado"
    cancelado = "cancelado"


# ============================================================================
# Modelos de Request/Response
# ============================================================================

class EventoBase(BaseModel):
    """Base para evento de agenda"""
    titulo: str
    descripcion: Optional[str] = None
    fecha_inicio: datetime
    fecha_fin: Optional[datetime] = None
    todo_el_dia: bool = False
    tipo: TipoEvento = TipoEvento.otro
    prioridad: Prioridad = Prioridad.media
    expediente_numero: Optional[str] = None
    actuacion_indice: Optional[int] = None
    color: Optional[str] = None
    recordatorio_minutos: Optional[int] = None
    notas: Optional[str] = None


class EventoCreate(EventoBase):
    """Request para crear evento"""
    pass


class EventoUpdate(BaseModel):
    """Request para actualizar evento"""
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    todo_el_dia: Optional[bool] = None
    tipo: Optional[TipoEvento] = None
    prioridad: Optional[Prioridad] = None
    estado: Optional[EstadoEvento] = None
    expediente_numero: Optional[str] = None
    actuacion_indice: Optional[int] = None
    color: Optional[str] = None
    recordatorio_minutos: Optional[int] = None
    notas: Optional[str] = None


class EventoResponse(EventoBase):
    """Response con evento completo"""
    id: int
    estado: EstadoEvento
    created_at: datetime
    updated_at: datetime
    urgencia: Optional[str] = None
    dias_restantes: Optional[int] = None


class ResumenAgenda(BaseModel):
    """Resumen de eventos proximos"""
    total_pendientes: int
    total_hoy: int
    total_semana: int
    total_vencidos: int
    proximos_eventos: List[EventoResponse]


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


async def get_current_user_id() -> int:
    """Obtiene el ID del usuario actual desde el token JWT."""
    # TODO: Implementar extraccion real del user_id desde el token
    return 1


# ============================================================================
# Router
# ============================================================================

router = APIRouter(
    prefix="/agenda",
    tags=["Agenda"]
)


@router.get("/eventos", response_model=List[EventoResponse])
async def listar_eventos(
    fecha_desde: Optional[date] = Query(None, description="Fecha desde"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha hasta"),
    tipo: Optional[TipoEvento] = Query(None, description="Filtrar por tipo"),
    estado: Optional[EstadoEvento] = Query(None, description="Filtrar por estado"),
    expediente: Optional[str] = Query(None, description="Filtrar por expediente"),
    user_id: int = Depends(get_current_user_id)
):
    """
    Lista eventos del usuario con filtros opcionales.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT
                id, user_id, titulo, descripcion, fecha_inicio, fecha_fin,
                todo_el_dia, tipo, prioridad, estado, expediente_numero,
                actuacion_indice, color, recordatorio_minutos, notas,
                created_at, updated_at,
                CASE
                    WHEN fecha_inicio < NOW() AND estado = 'pendiente' THEN 'vencido'
                    WHEN fecha_inicio <= DATE_ADD(NOW(), INTERVAL 1 DAY) AND estado = 'pendiente' THEN 'proximo'
                    ELSE 'futuro'
                END as urgencia,
                DATEDIFF(fecha_inicio, NOW()) as dias_restantes
            FROM agenda_eventos
            WHERE user_id = %s
        """
        params = [user_id]

        if fecha_desde:
            query += " AND DATE(fecha_inicio) >= %s"
            params.append(fecha_desde)

        if fecha_hasta:
            query += " AND DATE(fecha_inicio) <= %s"
            params.append(fecha_hasta)

        if tipo:
            query += " AND tipo = %s"
            params.append(tipo.value)

        if estado:
            query += " AND estado = %s"
            params.append(estado.value)

        if expediente:
            query += " AND expediente_numero = %s"
            params.append(expediente)

        query += " ORDER BY fecha_inicio ASC"

        cursor.execute(query, params)
        eventos_raw = cursor.fetchall()

        cursor.close()
        conn.close()

        eventos = []
        for e in eventos_raw:
            eventos.append(EventoResponse(
                id=e['id'],
                titulo=e['titulo'],
                descripcion=e['descripcion'],
                fecha_inicio=e['fecha_inicio'],
                fecha_fin=e['fecha_fin'],
                todo_el_dia=bool(e['todo_el_dia']),
                tipo=e['tipo'],
                prioridad=e['prioridad'],
                estado=e['estado'],
                expediente_numero=e['expediente_numero'],
                actuacion_indice=e['actuacion_indice'],
                color=e['color'],
                recordatorio_minutos=e['recordatorio_minutos'],
                notas=e['notas'],
                created_at=e['created_at'],
                updated_at=e['updated_at'],
                urgencia=e['urgencia'],
                dias_restantes=e['dias_restantes']
            ))

        return eventos

    except Exception as e:
        logger.error(f"Error listando eventos: {e}")
        raise HTTPException(status_code=500, detail=f"Error al listar eventos: {str(e)}")


@router.get("/eventos/{evento_id}", response_model=EventoResponse)
async def obtener_evento(
    evento_id: int,
    user_id: int = Depends(get_current_user_id)
):
    """
    Obtiene un evento por ID.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id, user_id, titulo, descripcion, fecha_inicio, fecha_fin,
                todo_el_dia, tipo, prioridad, estado, expediente_numero,
                actuacion_indice, color, recordatorio_minutos, notas,
                created_at, updated_at,
                CASE
                    WHEN fecha_inicio < NOW() AND estado = 'pendiente' THEN 'vencido'
                    WHEN fecha_inicio <= DATE_ADD(NOW(), INTERVAL 1 DAY) AND estado = 'pendiente' THEN 'proximo'
                    ELSE 'futuro'
                END as urgencia,
                DATEDIFF(fecha_inicio, NOW()) as dias_restantes
            FROM agenda_eventos
            WHERE id = %s AND user_id = %s
        """, (evento_id, user_id))

        e = cursor.fetchone()

        cursor.close()
        conn.close()

        if not e:
            raise HTTPException(status_code=404, detail="Evento no encontrado")

        return EventoResponse(
            id=e['id'],
            titulo=e['titulo'],
            descripcion=e['descripcion'],
            fecha_inicio=e['fecha_inicio'],
            fecha_fin=e['fecha_fin'],
            todo_el_dia=bool(e['todo_el_dia']),
            tipo=e['tipo'],
            prioridad=e['prioridad'],
            estado=e['estado'],
            expediente_numero=e['expediente_numero'],
            actuacion_indice=e['actuacion_indice'],
            color=e['color'],
            recordatorio_minutos=e['recordatorio_minutos'],
            notas=e['notas'],
            created_at=e['created_at'],
            updated_at=e['updated_at'],
            urgencia=e['urgencia'],
            dias_restantes=e['dias_restantes']
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo evento {evento_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener evento: {str(e)}")


@router.post("/eventos", response_model=EventoResponse)
async def crear_evento(
    request: EventoCreate,
    user_id: int = Depends(get_current_user_id)
):
    """
    Crea un nuevo evento.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            INSERT INTO agenda_eventos (
                user_id, titulo, descripcion, fecha_inicio, fecha_fin,
                todo_el_dia, tipo, prioridad, expediente_numero,
                actuacion_indice, color, recordatorio_minutos, notas
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id, request.titulo, request.descripcion, request.fecha_inicio,
            request.fecha_fin, request.todo_el_dia, request.tipo.value,
            request.prioridad.value, request.expediente_numero,
            request.actuacion_indice, request.color, request.recordatorio_minutos,
            request.notas
        ))

        conn.commit()
        evento_id = cursor.lastrowid

        # Obtener el evento creado
        cursor.execute("""
            SELECT
                id, user_id, titulo, descripcion, fecha_inicio, fecha_fin,
                todo_el_dia, tipo, prioridad, estado, expediente_numero,
                actuacion_indice, color, recordatorio_minutos, notas,
                created_at, updated_at,
                CASE
                    WHEN fecha_inicio < NOW() AND estado = 'pendiente' THEN 'vencido'
                    WHEN fecha_inicio <= DATE_ADD(NOW(), INTERVAL 1 DAY) AND estado = 'pendiente' THEN 'proximo'
                    ELSE 'futuro'
                END as urgencia,
                DATEDIFF(fecha_inicio, NOW()) as dias_restantes
            FROM agenda_eventos
            WHERE id = %s
        """, (evento_id,))

        e = cursor.fetchone()

        cursor.close()
        conn.close()

        return EventoResponse(
            id=e['id'],
            titulo=e['titulo'],
            descripcion=e['descripcion'],
            fecha_inicio=e['fecha_inicio'],
            fecha_fin=e['fecha_fin'],
            todo_el_dia=bool(e['todo_el_dia']),
            tipo=e['tipo'],
            prioridad=e['prioridad'],
            estado=e['estado'],
            expediente_numero=e['expediente_numero'],
            actuacion_indice=e['actuacion_indice'],
            color=e['color'],
            recordatorio_minutos=e['recordatorio_minutos'],
            notas=e['notas'],
            created_at=e['created_at'],
            updated_at=e['updated_at'],
            urgencia=e['urgencia'],
            dias_restantes=e['dias_restantes']
        )

    except Exception as e:
        logger.error(f"Error creando evento: {e}")
        raise HTTPException(status_code=500, detail=f"Error al crear evento: {str(e)}")


@router.put("/eventos/{evento_id}", response_model=EventoResponse)
async def actualizar_evento(
    evento_id: int,
    request: EventoUpdate,
    user_id: int = Depends(get_current_user_id)
):
    """
    Actualiza un evento existente.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Verificar que el evento existe y pertenece al usuario
        cursor.execute(
            "SELECT id FROM agenda_eventos WHERE id = %s AND user_id = %s",
            (evento_id, user_id)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Evento no encontrado")

        # Construir query dinamico solo con campos proporcionados
        updates = []
        params = []

        if request.titulo is not None:
            updates.append("titulo = %s")
            params.append(request.titulo)
        if request.descripcion is not None:
            updates.append("descripcion = %s")
            params.append(request.descripcion)
        if request.fecha_inicio is not None:
            updates.append("fecha_inicio = %s")
            params.append(request.fecha_inicio)
        if request.fecha_fin is not None:
            updates.append("fecha_fin = %s")
            params.append(request.fecha_fin)
        if request.todo_el_dia is not None:
            updates.append("todo_el_dia = %s")
            params.append(request.todo_el_dia)
        if request.tipo is not None:
            updates.append("tipo = %s")
            params.append(request.tipo.value)
        if request.prioridad is not None:
            updates.append("prioridad = %s")
            params.append(request.prioridad.value)
        if request.estado is not None:
            updates.append("estado = %s")
            params.append(request.estado.value)
        if request.expediente_numero is not None:
            updates.append("expediente_numero = %s")
            params.append(request.expediente_numero)
        if request.actuacion_indice is not None:
            updates.append("actuacion_indice = %s")
            params.append(request.actuacion_indice)
        if request.color is not None:
            updates.append("color = %s")
            params.append(request.color)
        if request.recordatorio_minutos is not None:
            updates.append("recordatorio_minutos = %s")
            params.append(request.recordatorio_minutos)
        if request.notas is not None:
            updates.append("notas = %s")
            params.append(request.notas)

        if updates:
            query = f"UPDATE agenda_eventos SET {', '.join(updates)} WHERE id = %s"
            params.append(evento_id)
            cursor.execute(query, params)
            conn.commit()

        # Obtener evento actualizado
        cursor.execute("""
            SELECT
                id, user_id, titulo, descripcion, fecha_inicio, fecha_fin,
                todo_el_dia, tipo, prioridad, estado, expediente_numero,
                actuacion_indice, color, recordatorio_minutos, notas,
                created_at, updated_at,
                CASE
                    WHEN fecha_inicio < NOW() AND estado = 'pendiente' THEN 'vencido'
                    WHEN fecha_inicio <= DATE_ADD(NOW(), INTERVAL 1 DAY) AND estado = 'pendiente' THEN 'proximo'
                    ELSE 'futuro'
                END as urgencia,
                DATEDIFF(fecha_inicio, NOW()) as dias_restantes
            FROM agenda_eventos
            WHERE id = %s
        """, (evento_id,))

        e = cursor.fetchone()

        cursor.close()
        conn.close()

        return EventoResponse(
            id=e['id'],
            titulo=e['titulo'],
            descripcion=e['descripcion'],
            fecha_inicio=e['fecha_inicio'],
            fecha_fin=e['fecha_fin'],
            todo_el_dia=bool(e['todo_el_dia']),
            tipo=e['tipo'],
            prioridad=e['prioridad'],
            estado=e['estado'],
            expediente_numero=e['expediente_numero'],
            actuacion_indice=e['actuacion_indice'],
            color=e['color'],
            recordatorio_minutos=e['recordatorio_minutos'],
            notas=e['notas'],
            created_at=e['created_at'],
            updated_at=e['updated_at'],
            urgencia=e['urgencia'],
            dias_restantes=e['dias_restantes']
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando evento {evento_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar evento: {str(e)}")


@router.delete("/eventos/{evento_id}")
async def eliminar_evento(
    evento_id: int,
    user_id: int = Depends(get_current_user_id)
):
    """
    Elimina un evento.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM agenda_eventos WHERE id = %s AND user_id = %s",
            (evento_id, user_id)
        )

        affected = cursor.rowcount
        conn.commit()

        cursor.close()
        conn.close()

        if affected == 0:
            raise HTTPException(status_code=404, detail="Evento no encontrado")

        return {"mensaje": "Evento eliminado", "id": evento_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando evento {evento_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar evento: {str(e)}")


@router.get("/resumen", response_model=ResumenAgenda)
async def obtener_resumen(
    user_id: int = Depends(get_current_user_id)
):
    """
    Obtiene resumen de agenda con estadisticas y proximos eventos.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Contar pendientes
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM agenda_eventos
            WHERE user_id = %s AND estado = 'pendiente'
        """, (user_id,))
        total_pendientes = cursor.fetchone()['total']

        # Contar eventos de hoy
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM agenda_eventos
            WHERE user_id = %s AND DATE(fecha_inicio) = CURDATE() AND estado = 'pendiente'
        """, (user_id,))
        total_hoy = cursor.fetchone()['total']

        # Contar eventos de la semana
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM agenda_eventos
            WHERE user_id = %s
            AND fecha_inicio BETWEEN NOW() AND DATE_ADD(NOW(), INTERVAL 7 DAY)
            AND estado = 'pendiente'
        """, (user_id,))
        total_semana = cursor.fetchone()['total']

        # Contar vencidos
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM agenda_eventos
            WHERE user_id = %s AND fecha_inicio < NOW() AND estado = 'pendiente'
        """, (user_id,))
        total_vencidos = cursor.fetchone()['total']

        # Proximos 5 eventos
        cursor.execute("""
            SELECT
                id, user_id, titulo, descripcion, fecha_inicio, fecha_fin,
                todo_el_dia, tipo, prioridad, estado, expediente_numero,
                actuacion_indice, color, recordatorio_minutos, notas,
                created_at, updated_at,
                CASE
                    WHEN fecha_inicio < NOW() AND estado = 'pendiente' THEN 'vencido'
                    WHEN fecha_inicio <= DATE_ADD(NOW(), INTERVAL 1 DAY) AND estado = 'pendiente' THEN 'proximo'
                    ELSE 'futuro'
                END as urgencia,
                DATEDIFF(fecha_inicio, NOW()) as dias_restantes
            FROM agenda_eventos
            WHERE user_id = %s AND estado = 'pendiente'
            ORDER BY fecha_inicio ASC
            LIMIT 5
        """, (user_id,))

        eventos_raw = cursor.fetchall()

        cursor.close()
        conn.close()

        proximos = []
        for e in eventos_raw:
            proximos.append(EventoResponse(
                id=e['id'],
                titulo=e['titulo'],
                descripcion=e['descripcion'],
                fecha_inicio=e['fecha_inicio'],
                fecha_fin=e['fecha_fin'],
                todo_el_dia=bool(e['todo_el_dia']),
                tipo=e['tipo'],
                prioridad=e['prioridad'],
                estado=e['estado'],
                expediente_numero=e['expediente_numero'],
                actuacion_indice=e['actuacion_indice'],
                color=e['color'],
                recordatorio_minutos=e['recordatorio_minutos'],
                notas=e['notas'],
                created_at=e['created_at'],
                updated_at=e['updated_at'],
                urgencia=e['urgencia'],
                dias_restantes=e['dias_restantes']
            ))

        return ResumenAgenda(
            total_pendientes=total_pendientes,
            total_hoy=total_hoy,
            total_semana=total_semana,
            total_vencidos=total_vencidos,
            proximos_eventos=proximos
        )

    except Exception as e:
        logger.error(f"Error obteniendo resumen de agenda: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener resumen: {str(e)}")


@router.post("/eventos/{evento_id}/completar", response_model=EventoResponse)
async def completar_evento(
    evento_id: int,
    user_id: int = Depends(get_current_user_id)
):
    """
    Marca un evento como completado.
    """
    update_request = EventoUpdate(estado=EstadoEvento.completado)
    return await actualizar_evento(evento_id, update_request, user_id)
