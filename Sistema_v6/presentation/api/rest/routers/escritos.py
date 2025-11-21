"""Router para gestión de escritos judiciales."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from infrastructure.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/escritos", tags=["escritos"])


# === Modelos Pydantic ===

class PlantillaBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    contenido: str
    variables: Optional[list[str]] = None
    categoria: str = "general"
    es_publica: bool = False


class PlantillaCreate(PlantillaBase):
    pass


class PlantillaUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    contenido: Optional[str] = None
    variables: Optional[list[str]] = None
    categoria: Optional[str] = None
    es_publica: Optional[bool] = None


class PlantillaResponse(PlantillaBase):
    id: int
    user_id: int
    created_at: str
    updated_at: str


class EscritoBase(BaseModel):
    expediente_numero: Optional[str] = None
    plantilla_id: Optional[int] = None
    titulo: str
    contenido: str
    notas: Optional[str] = None


class EscritoCreate(EscritoBase):
    pass


class EscritoUpdate(BaseModel):
    expediente_numero: Optional[str] = None
    titulo: Optional[str] = None
    contenido: Optional[str] = None
    estado: Optional[str] = None
    fecha_presentacion: Optional[str] = None
    numero_escrito: Optional[str] = None
    notas: Optional[str] = None


class EscritoResponse(EscritoBase):
    id: int
    user_id: int
    estado: str
    fecha_presentacion: Optional[str] = None
    numero_escrito: Optional[str] = None
    created_at: str
    updated_at: str


class EstadisticasEscritos(BaseModel):
    total_escritos: int
    borradores: int
    en_revision: int
    presentados: int
    confirmados: int
    expedientes_con_escritos: int


# === Helpers ===

def get_db_connection():
    """Obtiene conexión a MySQL."""
    import mysql.connector
    settings = get_settings()
    return mysql.connector.connect(
        host=settings.database.host,
        port=settings.database.port,
        user=settings.database.user,
        password=settings.database.password,
        database=settings.database.name
    )


def get_current_user_id() -> int:
    """Placeholder para obtener el user_id actual."""
    return 1


# === Endpoints de Plantillas ===

@router.get("/plantillas", response_model=list[PlantillaResponse])
async def listar_plantillas(
    categoria: Optional[str] = None,
    incluir_publicas: bool = True
):
    """Lista plantillas del usuario y públicas."""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        query = """
            SELECT * FROM plantillas_escritos
            WHERE (user_id = %s OR (es_publica = TRUE AND %s = TRUE))
        """
        params = [user_id, incluir_publicas]

        if categoria:
            query += " AND categoria = %s"
            params.append(categoria)

        query += " ORDER BY nombre"

        cursor.execute(query, params)
        plantillas = cursor.fetchall()

        result = []
        for p in plantillas:
            # Parsear variables JSON
            import json
            variables = []
            if p.get('variables'):
                try:
                    variables = json.loads(p['variables']) if isinstance(p['variables'], str) else p['variables']
                except:
                    pass

            result.append(PlantillaResponse(
                id=p['id'],
                user_id=p['user_id'],
                nombre=p['nombre'],
                descripcion=p.get('descripcion'),
                contenido=p['contenido'],
                variables=variables,
                categoria=p.get('categoria', 'general'),
                es_publica=bool(p.get('es_publica', False)),
                created_at=p['created_at'].isoformat() if p.get('created_at') else '',
                updated_at=p['updated_at'].isoformat() if p.get('updated_at') else ''
            ))

        return result
    finally:
        cursor.close()
        conn.close()


@router.get("/plantillas/{plantilla_id}", response_model=PlantillaResponse)
async def obtener_plantilla(plantilla_id: int):
    """Obtiene una plantilla por ID."""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """SELECT * FROM plantillas_escritos
               WHERE id = %s AND (user_id = %s OR es_publica = TRUE)""",
            (plantilla_id, user_id)
        )
        p = cursor.fetchone()

        if not p:
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")

        import json
        variables = []
        if p.get('variables'):
            try:
                variables = json.loads(p['variables']) if isinstance(p['variables'], str) else p['variables']
            except:
                pass

        return PlantillaResponse(
            id=p['id'],
            user_id=p['user_id'],
            nombre=p['nombre'],
            descripcion=p.get('descripcion'),
            contenido=p['contenido'],
            variables=variables,
            categoria=p.get('categoria', 'general'),
            es_publica=bool(p.get('es_publica', False)),
            created_at=p['created_at'].isoformat() if p.get('created_at') else '',
            updated_at=p['updated_at'].isoformat() if p.get('updated_at') else ''
        )
    finally:
        cursor.close()
        conn.close()


@router.post("/plantillas", response_model=PlantillaResponse)
async def crear_plantilla(data: PlantillaCreate):
    """Crea una nueva plantilla."""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        import json
        variables_json = json.dumps(data.variables) if data.variables else None

        cursor.execute(
            """INSERT INTO plantillas_escritos
               (user_id, nombre, descripcion, contenido, variables, categoria, es_publica)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (user_id, data.nombre, data.descripcion, data.contenido,
             variables_json, data.categoria, data.es_publica)
        )
        conn.commit()
        plantilla_id = cursor.lastrowid

        return await obtener_plantilla(plantilla_id)
    finally:
        cursor.close()
        conn.close()


@router.put("/plantillas/{plantilla_id}", response_model=PlantillaResponse)
async def actualizar_plantilla(plantilla_id: int, data: PlantillaUpdate):
    """Actualiza una plantilla existente."""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Verificar que existe y pertenece al usuario
        cursor.execute(
            "SELECT id FROM plantillas_escritos WHERE id = %s AND user_id = %s",
            (plantilla_id, user_id)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")

        # Construir query de actualización
        updates = []
        params = []

        if data.nombre is not None:
            updates.append("nombre = %s")
            params.append(data.nombre)
        if data.descripcion is not None:
            updates.append("descripcion = %s")
            params.append(data.descripcion)
        if data.contenido is not None:
            updates.append("contenido = %s")
            params.append(data.contenido)
        if data.variables is not None:
            import json
            updates.append("variables = %s")
            params.append(json.dumps(data.variables))
        if data.categoria is not None:
            updates.append("categoria = %s")
            params.append(data.categoria)
        if data.es_publica is not None:
            updates.append("es_publica = %s")
            params.append(data.es_publica)

        if updates:
            params.append(plantilla_id)
            cursor.execute(
                f"UPDATE plantillas_escritos SET {', '.join(updates)} WHERE id = %s",
                params
            )
            conn.commit()

        return await obtener_plantilla(plantilla_id)
    finally:
        cursor.close()
        conn.close()


@router.delete("/plantillas/{plantilla_id}")
async def eliminar_plantilla(plantilla_id: int):
    """Elimina una plantilla."""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM plantillas_escritos WHERE id = %s AND user_id = %s",
            (plantilla_id, user_id)
        )
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")

        return {"message": "Plantilla eliminada"}
    finally:
        cursor.close()
        conn.close()


# === Endpoints de Escritos ===

@router.get("", response_model=list[EscritoResponse])
async def listar_escritos(
    expediente: Optional[str] = None,
    estado: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0
):
    """Lista escritos del usuario con filtros opcionales."""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        query = "SELECT * FROM escritos WHERE user_id = %s"
        params = [user_id]

        if expediente:
            query += " AND expediente_numero = %s"
            params.append(expediente)
        if estado:
            query += " AND estado = %s"
            params.append(estado)

        query += " ORDER BY updated_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor.execute(query, params)
        escritos = cursor.fetchall()

        return [
            EscritoResponse(
                id=e['id'],
                user_id=e['user_id'],
                expediente_numero=e.get('expediente_numero'),
                plantilla_id=e.get('plantilla_id'),
                titulo=e['titulo'],
                contenido=e['contenido'],
                estado=e['estado'],
                fecha_presentacion=e['fecha_presentacion'].isoformat() if e.get('fecha_presentacion') else None,
                numero_escrito=e.get('numero_escrito'),
                notas=e.get('notas'),
                created_at=e['created_at'].isoformat() if e.get('created_at') else '',
                updated_at=e['updated_at'].isoformat() if e.get('updated_at') else ''
            )
            for e in escritos
        ]
    finally:
        cursor.close()
        conn.close()


@router.get("/estadisticas", response_model=EstadisticasEscritos)
async def obtener_estadisticas():
    """Obtiene estadísticas de escritos del usuario."""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT * FROM escritos_estadisticas WHERE user_id = %s",
            (user_id,)
        )
        stats = cursor.fetchone()

        if not stats:
            return EstadisticasEscritos(
                total_escritos=0,
                borradores=0,
                en_revision=0,
                presentados=0,
                confirmados=0,
                expedientes_con_escritos=0
            )

        return EstadisticasEscritos(
            total_escritos=stats['total_escritos'],
            borradores=stats['borradores'],
            en_revision=stats['en_revision'],
            presentados=stats['presentados'],
            confirmados=stats['confirmados'],
            expedientes_con_escritos=stats['expedientes_con_escritos']
        )
    finally:
        cursor.close()
        conn.close()


@router.get("/{escrito_id}", response_model=EscritoResponse)
async def obtener_escrito(escrito_id: int):
    """Obtiene un escrito por ID."""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT * FROM escritos WHERE id = %s AND user_id = %s",
            (escrito_id, user_id)
        )
        e = cursor.fetchone()

        if not e:
            raise HTTPException(status_code=404, detail="Escrito no encontrado")

        return EscritoResponse(
            id=e['id'],
            user_id=e['user_id'],
            expediente_numero=e.get('expediente_numero'),
            plantilla_id=e.get('plantilla_id'),
            titulo=e['titulo'],
            contenido=e['contenido'],
            estado=e['estado'],
            fecha_presentacion=e['fecha_presentacion'].isoformat() if e.get('fecha_presentacion') else None,
            numero_escrito=e.get('numero_escrito'),
            notas=e.get('notas'),
            created_at=e['created_at'].isoformat() if e.get('created_at') else '',
            updated_at=e['updated_at'].isoformat() if e.get('updated_at') else ''
        )
    finally:
        cursor.close()
        conn.close()


@router.post("", response_model=EscritoResponse)
async def crear_escrito(data: EscritoCreate):
    """Crea un nuevo escrito."""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """INSERT INTO escritos
               (user_id, expediente_numero, plantilla_id, titulo, contenido, notas)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (user_id, data.expediente_numero, data.plantilla_id,
             data.titulo, data.contenido, data.notas)
        )
        conn.commit()
        escrito_id = cursor.lastrowid

        # Crear versión inicial
        cursor.execute(
            """INSERT INTO escritos_versiones (escrito_id, version, contenido, comentario)
               VALUES (%s, 1, %s, 'Versión inicial')""",
            (escrito_id, data.contenido)
        )
        conn.commit()

        return await obtener_escrito(escrito_id)
    finally:
        cursor.close()
        conn.close()


@router.put("/{escrito_id}", response_model=EscritoResponse)
async def actualizar_escrito(escrito_id: int, data: EscritoUpdate):
    """Actualiza un escrito existente."""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Verificar que existe
        cursor.execute(
            "SELECT id, contenido FROM escritos WHERE id = %s AND user_id = %s",
            (escrito_id, user_id)
        )
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Escrito no encontrado")

        # Construir query de actualización
        updates = []
        params = []

        if data.expediente_numero is not None:
            updates.append("expediente_numero = %s")
            params.append(data.expediente_numero)
        if data.titulo is not None:
            updates.append("titulo = %s")
            params.append(data.titulo)
        if data.contenido is not None:
            updates.append("contenido = %s")
            params.append(data.contenido)
        if data.estado is not None:
            updates.append("estado = %s")
            params.append(data.estado)
        if data.fecha_presentacion is not None:
            updates.append("fecha_presentacion = %s")
            params.append(data.fecha_presentacion)
        if data.numero_escrito is not None:
            updates.append("numero_escrito = %s")
            params.append(data.numero_escrito)
        if data.notas is not None:
            updates.append("notas = %s")
            params.append(data.notas)

        if updates:
            params.append(escrito_id)
            cursor.execute(
                f"UPDATE escritos SET {', '.join(updates)} WHERE id = %s",
                params
            )
            conn.commit()

            # Si cambió el contenido, crear nueva versión
            if data.contenido and data.contenido != existing['contenido']:
                cursor.execute(
                    "SELECT COALESCE(MAX(version), 0) + 1 FROM escritos_versiones WHERE escrito_id = %s",
                    (escrito_id,)
                )
                nueva_version = cursor.fetchone()[0]

                cursor.execute(
                    """INSERT INTO escritos_versiones (escrito_id, version, contenido, comentario)
                       VALUES (%s, %s, %s, 'Actualización')""",
                    (escrito_id, nueva_version, data.contenido)
                )
                conn.commit()

        return await obtener_escrito(escrito_id)
    finally:
        cursor.close()
        conn.close()


@router.delete("/{escrito_id}")
async def eliminar_escrito(escrito_id: int):
    """Elimina un escrito."""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM escritos WHERE id = %s AND user_id = %s",
            (escrito_id, user_id)
        )
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Escrito no encontrado")

        return {"message": "Escrito eliminado"}
    finally:
        cursor.close()
        conn.close()


@router.post("/{escrito_id}/presentar", response_model=EscritoResponse)
async def marcar_presentado(escrito_id: int, numero_escrito: Optional[str] = None):
    """Marca un escrito como presentado."""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """UPDATE escritos
               SET estado = 'presentado',
                   fecha_presentacion = NOW(),
                   numero_escrito = %s
               WHERE id = %s AND user_id = %s""",
            (numero_escrito, escrito_id, user_id)
        )
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Escrito no encontrado")

        return await obtener_escrito(escrito_id)
    finally:
        cursor.close()
        conn.close()


@router.post("/{escrito_id}/confirmar", response_model=EscritoResponse)
async def confirmar_presentacion(escrito_id: int):
    """Confirma la presentación de un escrito."""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """UPDATE escritos
               SET estado = 'confirmado'
               WHERE id = %s AND user_id = %s AND estado = 'presentado'""",
            (escrito_id, user_id)
        )
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Escrito no encontrado o no está presentado")

        return await obtener_escrito(escrito_id)
    finally:
        cursor.close()
        conn.close()


@router.get("/{escrito_id}/versiones")
async def listar_versiones(escrito_id: int):
    """Lista las versiones de un escrito."""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Verificar que el escrito pertenece al usuario
        cursor.execute(
            "SELECT id FROM escritos WHERE id = %s AND user_id = %s",
            (escrito_id, user_id)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Escrito no encontrado")

        cursor.execute(
            """SELECT id, version, comentario, created_at
               FROM escritos_versiones
               WHERE escrito_id = %s
               ORDER BY version DESC""",
            (escrito_id,)
        )
        versiones = cursor.fetchall()

        return [
            {
                "id": v['id'],
                "version": v['version'],
                "comentario": v.get('comentario'),
                "created_at": v['created_at'].isoformat() if v.get('created_at') else ''
            }
            for v in versiones
        ]
    finally:
        cursor.close()
        conn.close()


@router.get("/{escrito_id}/versiones/{version_id}")
async def obtener_version(escrito_id: int, version_id: int):
    """Obtiene el contenido de una versión específica."""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Verificar que el escrito pertenece al usuario
        cursor.execute(
            "SELECT id FROM escritos WHERE id = %s AND user_id = %s",
            (escrito_id, user_id)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Escrito no encontrado")

        cursor.execute(
            "SELECT * FROM escritos_versiones WHERE id = %s AND escrito_id = %s",
            (version_id, escrito_id)
        )
        v = cursor.fetchone()

        if not v:
            raise HTTPException(status_code=404, detail="Versión no encontrada")

        return {
            "id": v['id'],
            "escrito_id": v['escrito_id'],
            "version": v['version'],
            "contenido": v['contenido'],
            "comentario": v.get('comentario'),
            "created_at": v['created_at'].isoformat() if v.get('created_at') else ''
        }
    finally:
        cursor.close()
        conn.close()
