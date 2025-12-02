"""
Router REST API para gestión de vencimientos.

Endpoints CRUD completo para vencimientos:
- Listar con filtros
- Obtener por ID
- Crear manual
- Actualizar (estado, fecha, etc.)
- Eliminar
- Marcar como atendido/cumplido
"""

from typing import List, Optional, Dict, Any, Tuple
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import date, datetime
from enum import Enum
import logging
import hashlib
import time
from threading import Lock

from infrastructure.persistence.database import get_pooled_connection
from contextlib import contextmanager

logger = logging.getLogger(__name__)


# ============================================================================
# Caché simple con TTL
# ============================================================================

class VencimientosCache:
    """
    Caché en memoria para vencimientos con TTL.

    Reduce consultas frecuentes a la BD para los mismos filtros.
    """

    def __init__(self, ttl_seconds: int = 60):
        """
        Args:
            ttl_seconds: Tiempo de vida del caché en segundos
        """
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._lock = Lock()
        self._ttl = ttl_seconds

    def _make_key(self, **kwargs) -> str:
        """Genera clave de caché desde los parámetros."""
        # Ordenar kwargs para consistencia
        sorted_items = sorted(kwargs.items())
        key_string = str(sorted_items)
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, **kwargs) -> Optional[Any]:
        """
        Obtiene valor del caché si existe y no expiró.

        Args:
            **kwargs: Parámetros de la consulta

        Returns:
            Valor cacheado o None
        """
        key = self._make_key(**kwargs)
        with self._lock:
            if key in self._cache:
                value, timestamp = self._cache[key]
                if time.time() - timestamp < self._ttl:
                    logger.debug(f"Cache HIT: {key[:8]}...")
                    return value
                else:
                    # Expirado, eliminar
                    del self._cache[key]
                    logger.debug(f"Cache EXPIRED: {key[:8]}...")
        return None

    def set(self, value: Any, **kwargs) -> None:
        """
        Guarda valor en caché.

        Args:
            value: Valor a cachear
            **kwargs: Parámetros de la consulta
        """
        key = self._make_key(**kwargs)
        with self._lock:
            self._cache[key] = (value, time.time())
            logger.debug(f"Cache SET: {key[:8]}...")

    def invalidate(self) -> None:
        """Invalida todo el caché."""
        with self._lock:
            self._cache.clear()
            logger.info("Caché de vencimientos invalidado")

    def cleanup_expired(self) -> int:
        """
        Limpia entradas expiradas.

        Returns:
            Número de entradas eliminadas
        """
        now = time.time()
        count = 0
        with self._lock:
            keys_to_delete = [
                k for k, (_, ts) in self._cache.items()
                if now - ts >= self._ttl
            ]
            for k in keys_to_delete:
                del self._cache[k]
                count += 1
        if count:
            logger.debug(f"Cache cleanup: {count} entradas eliminadas")
        return count


# Instancia global del caché (TTL 60 segundos)
_vencimientos_cache = VencimientosCache(ttl_seconds=60)


# ============================================================================
# Enums
# ============================================================================

class TipoVencimiento(str, Enum):
    cedula_electronica = "CEDULA_ELECTRONICA"
    cedula_fisica = "CEDULA_FISICA"
    traslado = "TRASLADO"
    alegato = "ALEGATO"
    presentacion = "PRESENTACION"
    apelacion = "APELACION"
    recurso = "RECURSO"
    audiencia = "AUDIENCIA"
    otro = "OTRO"


class EstadoVencimiento(str, Enum):
    pendiente = "pendiente"
    atendido = "atendido"
    vencido = "vencido"
    cancelado = "cancelado"


class NivelUrgencia(str, Enum):
    vencido = "vencido"
    critico = "critico"
    urgente = "urgente"
    proximo = "proximo"
    futuro = "futuro"


# ============================================================================
# Modelos de Request/Response
# ============================================================================

class VencimientoBase(BaseModel):
    """Base para vencimiento."""
    expediente_numero: str
    tipo: TipoVencimiento
    descripcion: Optional[str] = None
    fecha_notificacion: date
    plazo_dias: int
    fecha_vencimiento: date
    dias_habiles: bool = True
    texto_fuente: Optional[str] = None
    confianza: float = 1.0
    actuacion_id: Optional[int] = None


class VencimientoCreate(VencimientoBase):
    """Request para crear vencimiento."""
    pass


class VencimientoUpdate(BaseModel):
    """Request para actualizar vencimiento."""
    descripcion: Optional[str] = None
    fecha_vencimiento: Optional[date] = None
    estado: Optional[EstadoVencimiento] = None
    notas: Optional[str] = None


class VencimientoResponse(VencimientoBase):
    """Response con vencimiento completo."""
    id: int
    estado: EstadoVencimiento
    dias_restantes: int
    nivel_urgencia: NivelUrgencia
    notas: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    # Campos adicionales del expediente
    caratula: Optional[str] = None
    dependencia: Optional[str] = None


class VencimientosListResponse(BaseModel):
    """Response de lista de vencimientos."""
    vencimientos: List[VencimientoResponse]
    total: int
    pendientes: int
    vencidos: int
    atendidos: int


class EstadisticasVencimientos(BaseModel):
    """Estadísticas de vencimientos."""
    total: int
    pendientes: int
    vencidos: int
    atendidos: int
    cancelados: int
    criticos_hoy: int
    urgentes_3_dias: int
    proximos_7_dias: int
    por_tipo: dict


# ============================================================================
# Utilidades
# ============================================================================

@contextmanager
def _get_db_connection():
    """Obtiene conexión MySQL desde el pool nativo."""
    conn = get_pooled_connection()
    try:
        yield conn
    finally:
        conn.close()


def _calcular_nivel_urgencia(dias_restantes: int) -> str:
    """Calcula el nivel de urgencia según días restantes."""
    if dias_restantes < 0:
        return "vencido"
    elif dias_restantes <= 1:
        return "critico"
    elif dias_restantes <= 3:
        return "urgente"
    elif dias_restantes <= 7:
        return "proximo"
    else:
        return "futuro"


def _normalizar_tipo(tipo: str) -> str:
    """Normaliza el tipo de vencimiento a mayúsculas."""
    if not tipo:
        return "OTRO"
    tipo_upper = tipo.upper()
    # Mapeo de valores legacy a valores del enum
    mapeo = {
        "CEDULA_ELECTRONICA": "CEDULA_ELECTRONICA",
        "CEDULA_FISICA": "CEDULA_FISICA",
        "TRASLADO": "TRASLADO",
        "ALEGATO": "ALEGATO",
        "PRESENTACION": "PRESENTACION",
        "APELACION": "APELACION",
        "RECURSO": "RECURSO",
        "AUDIENCIA": "AUDIENCIA",
        "OTRO": "OTRO",
    }
    return mapeo.get(tipo_upper, "OTRO")


def _row_to_response(row: dict) -> VencimientoResponse:
    """Convierte una fila de BD a VencimientoResponse."""
    dias_restantes = row.get('dias_restantes') or 0
    tipo_normalizado = _normalizar_tipo(row.get('tipo', 'OTRO'))
    return VencimientoResponse(
        id=row['id'],
        expediente_numero=row['expediente_numero'],
        tipo=tipo_normalizado,
        descripcion=row.get('descripcion'),
        fecha_notificacion=row['fecha_notificacion'],
        plazo_dias=row['plazo_dias'],
        fecha_vencimiento=row['fecha_vencimiento'],
        dias_habiles=bool(row.get('dias_habiles', True)),
        texto_fuente=row.get('texto_fuente'),
        confianza=float(row.get('confianza', 1.0) or 1.0),
        actuacion_id=row.get('actuacion_id'),
        estado=row.get('estado', 'pendiente'),
        dias_restantes=dias_restantes,
        nivel_urgencia=_calcular_nivel_urgencia(dias_restantes),
        notas=row.get('notas'),
        created_at=row.get('creado_en') or datetime.now(),
        updated_at=row.get('actualizado_en') or datetime.now(),
        # Campos del expediente (del JOIN)
        caratula=row.get('caratula'),
        dependencia=row.get('dependencia')
    )


# ============================================================================
# Router
# ============================================================================

router = APIRouter(
    prefix="/vencimientos",
    tags=["Vencimientos"]
)


@router.get("", response_model=VencimientosListResponse)
async def listar_vencimientos(
    expediente: Optional[str] = Query(None, description="Filtrar por número de expediente"),
    tipo: Optional[TipoVencimiento] = Query(None, description="Filtrar por tipo"),
    estado: Optional[EstadoVencimiento] = Query(None, description="Filtrar por estado"),
    urgencia: Optional[NivelUrgencia] = Query(None, description="Filtrar por nivel de urgencia"),
    desde: Optional[date] = Query(None, description="Fecha desde"),
    hasta: Optional[date] = Query(None, description="Fecha hasta"),
    solo_pendientes: bool = Query(False, description="Solo vencimientos pendientes"),
    limite: int = Query(100, ge=1, le=500, description="Máximo de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginación"),
    use_cache: bool = Query(True, description="Usar caché (desactivar para datos frescos)")
):
    """
    Lista vencimientos con filtros opcionales.

    El caché tiene un TTL de 60 segundos. Usar use_cache=false para forzar datos frescos.
    """
    # Preparar parámetros para caché
    cache_params = {
        "expediente": expediente,
        "tipo": tipo.value if tipo else None,
        "estado": estado.value if estado else None,
        "urgencia": urgencia.value if urgencia else None,
        "desde": str(desde) if desde else None,
        "hasta": str(hasta) if hasta else None,
        "solo_pendientes": solo_pendientes,
        "limite": limite,
        "offset": offset
    }

    # Intentar obtener del caché
    if use_cache:
        cached = _vencimientos_cache.get(**cache_params)
        if cached:
            return cached

    try:
        with _get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            # Query base con JOIN a expedientes para obtener caratula
            # Normalizamos el numero: "FRE 004409/2021" -> "FRE_004409_2021"
            # Usamos COLLATE para evitar errores de collation entre tablas
            query = """
                SELECT
                    v.*,
                    DATEDIFF(v.fecha_vencimiento, CURDATE()) as dias_restantes,
                    e.caratula,
                    e.dependencia
                FROM vencimientos v
                LEFT JOIN expedientes e ON e.numero_normalizado COLLATE utf8mb4_unicode_ci = REPLACE(REPLACE(v.expediente_numero, ' ', '_'), '/', '_') COLLATE utf8mb4_unicode_ci
                WHERE 1=1
            """
            params = []

            # Aplicar filtros
            if expediente:
                query += " AND v.expediente_numero = %s"
                params.append(expediente)

            if tipo:
                query += " AND v.tipo = %s"
                params.append(tipo.value)

            if estado:
                query += " AND v.estado = %s"
                params.append(estado.value)

            if solo_pendientes:
                query += " AND v.estado = 'pendiente'"

            if desde:
                query += " AND v.fecha_vencimiento >= %s"
                params.append(desde)

            if hasta:
                query += " AND v.fecha_vencimiento <= %s"
                params.append(hasta)

            if urgencia:
                if urgencia == NivelUrgencia.vencido:
                    query += " AND DATEDIFF(v.fecha_vencimiento, CURDATE()) < 0"
                elif urgencia == NivelUrgencia.critico:
                    query += " AND DATEDIFF(v.fecha_vencimiento, CURDATE()) BETWEEN 0 AND 1"
                elif urgencia == NivelUrgencia.urgente:
                    query += " AND DATEDIFF(v.fecha_vencimiento, CURDATE()) BETWEEN 2 AND 3"
                elif urgencia == NivelUrgencia.proximo:
                    query += " AND DATEDIFF(v.fecha_vencimiento, CURDATE()) BETWEEN 4 AND 7"
                elif urgencia == NivelUrgencia.futuro:
                    query += " AND DATEDIFF(v.fecha_vencimiento, CURDATE()) > 7"

            # Ordenar y paginar
            query += " ORDER BY v.fecha_vencimiento ASC LIMIT %s OFFSET %s"
            params.extend([limite, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Contar totales
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN estado = 'pendiente' THEN 1 ELSE 0 END) as pendientes,
                    SUM(CASE WHEN estado = 'vencido' OR (estado = 'pendiente' AND fecha_vencimiento < CURDATE()) THEN 1 ELSE 0 END) as vencidos,
                    SUM(CASE WHEN estado = 'atendido' THEN 1 ELSE 0 END) as atendidos
                FROM vencimientos
            """)
            totals = cursor.fetchone()

            cursor.close()

        vencimientos = [_row_to_response(row) for row in rows]

        response = VencimientosListResponse(
            vencimientos=vencimientos,
            total=totals['total'] or 0,
            pendientes=totals['pendientes'] or 0,
            vencidos=totals['vencidos'] or 0,
            atendidos=totals['atendidos'] or 0
        )

        # Guardar en caché
        if use_cache:
            _vencimientos_cache.set(response, **cache_params)

        return response

    except Exception as e:
        logger.error(f"Error listando vencimientos: {e}")
        raise HTTPException(status_code=500, detail=f"Error al listar vencimientos: {str(e)}")


@router.get("/estadisticas", response_model=EstadisticasVencimientos)
async def obtener_estadisticas():
    """
    Obtiene estadísticas de vencimientos.
    """
    try:
        with _get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            # Estadísticas generales
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN estado = 'pendiente' THEN 1 ELSE 0 END) as pendientes,
                    SUM(CASE WHEN estado = 'vencido' OR (estado = 'pendiente' AND fecha_vencimiento < CURDATE()) THEN 1 ELSE 0 END) as vencidos,
                    SUM(CASE WHEN estado = 'atendido' THEN 1 ELSE 0 END) as atendidos,
                    SUM(CASE WHEN estado = 'cancelado' THEN 1 ELSE 0 END) as cancelados,
                    SUM(CASE WHEN estado = 'pendiente' AND DATEDIFF(fecha_vencimiento, CURDATE()) BETWEEN 0 AND 1 THEN 1 ELSE 0 END) as criticos_hoy,
                    SUM(CASE WHEN estado = 'pendiente' AND DATEDIFF(fecha_vencimiento, CURDATE()) BETWEEN 0 AND 3 THEN 1 ELSE 0 END) as urgentes_3_dias,
                    SUM(CASE WHEN estado = 'pendiente' AND DATEDIFF(fecha_vencimiento, CURDATE()) BETWEEN 0 AND 7 THEN 1 ELSE 0 END) as proximos_7_dias
                FROM vencimientos
            """)
            stats = cursor.fetchone()

            # Por tipo
            cursor.execute("""
                SELECT tipo, COUNT(*) as cantidad
                FROM vencimientos
                GROUP BY tipo
            """)
            por_tipo = {row['tipo']: row['cantidad'] for row in cursor.fetchall()}

            cursor.close()

        return EstadisticasVencimientos(
            total=stats['total'] or 0,
            pendientes=stats['pendientes'] or 0,
            vencidos=stats['vencidos'] or 0,
            atendidos=stats['atendidos'] or 0,
            cancelados=stats['cancelados'] or 0,
            criticos_hoy=stats['criticos_hoy'] or 0,
            urgentes_3_dias=stats['urgentes_3_dias'] or 0,
            proximos_7_dias=stats['proximos_7_dias'] or 0,
            por_tipo=por_tipo
        )

    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener estadísticas: {str(e)}")


@router.get("/{vencimiento_id}", response_model=VencimientoResponse)
async def obtener_vencimiento(vencimiento_id: int):
    """
    Obtiene un vencimiento por ID.
    """
    try:
        with _get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT
                    v.*,
                    DATEDIFF(v.fecha_vencimiento, CURDATE()) as dias_restantes
                FROM vencimientos v
                WHERE v.id = %s
            """, (vencimiento_id,))

            row = cursor.fetchone()
            cursor.close()

            if not row:
                raise HTTPException(status_code=404, detail="Vencimiento no encontrado")

        return _row_to_response(row)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo vencimiento {vencimiento_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener vencimiento: {str(e)}")


@router.post("", response_model=VencimientoResponse)
async def crear_vencimiento(request: VencimientoCreate):
    """
    Crea un vencimiento manual.
    """
    try:
        with _get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                INSERT INTO vencimientos (
                    expediente_numero, tipo, descripcion, fecha_notificacion,
                    plazo_dias, fecha_vencimiento, dias_habiles, texto_fuente,
                    confianza, actuacion_id, estado
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pendiente')
            """, (
                request.expediente_numero,
                request.tipo.value,
                request.descripcion,
                request.fecha_notificacion,
                request.plazo_dias,
                request.fecha_vencimiento,
                request.dias_habiles,
                request.texto_fuente,
                request.confianza,
                request.actuacion_id
            ))

            conn.commit()
            vencimiento_id = cursor.lastrowid

            # Obtener el vencimiento creado
            cursor.execute("""
                SELECT
                    v.*,
                    DATEDIFF(v.fecha_vencimiento, CURDATE()) as dias_restantes
                FROM vencimientos v
                WHERE v.id = %s
            """, (vencimiento_id,))

            row = cursor.fetchone()
            cursor.close()

        # Invalidar caché al crear
        _vencimientos_cache.invalidate()

        return _row_to_response(row)

    except Exception as e:
        logger.error(f"Error creando vencimiento: {e}")
        raise HTTPException(status_code=500, detail=f"Error al crear vencimiento: {str(e)}")


@router.put("/{vencimiento_id}", response_model=VencimientoResponse)
async def actualizar_vencimiento(vencimiento_id: int, request: VencimientoUpdate):
    """
    Actualiza un vencimiento existente.
    """
    try:
        with _get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            # Verificar que existe
            cursor.execute("SELECT id FROM vencimientos WHERE id = %s", (vencimiento_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Vencimiento no encontrado")

            # Construir query dinámico
            updates = []
            params = []

            if request.descripcion is not None:
                updates.append("descripcion = %s")
                params.append(request.descripcion)
            if request.fecha_vencimiento is not None:
                updates.append("fecha_vencimiento = %s")
                params.append(request.fecha_vencimiento)
            if request.estado is not None:
                updates.append("estado = %s")
                params.append(request.estado.value)
            if request.notas is not None:
                updates.append("notas = %s")
                params.append(request.notas)

            if not updates:
                raise HTTPException(status_code=400, detail="No se proporcionaron campos para actualizar")

            updates.append("actualizado_en = NOW()")
            params.append(vencimiento_id)

            query = f"UPDATE vencimientos SET {', '.join(updates)} WHERE id = %s"
            cursor.execute(query, params)
            conn.commit()

            # Obtener actualizado
            cursor.execute("""
                SELECT
                    v.*,
                    DATEDIFF(v.fecha_vencimiento, CURDATE()) as dias_restantes
                FROM vencimientos v
                WHERE v.id = %s
            """, (vencimiento_id,))

            row = cursor.fetchone()
            cursor.close()

        # Invalidar caché al actualizar
        _vencimientos_cache.invalidate()

        return _row_to_response(row)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando vencimiento {vencimiento_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar vencimiento: {str(e)}")


@router.delete("/{vencimiento_id}")
async def eliminar_vencimiento(vencimiento_id: int):
    """
    Elimina un vencimiento.
    """
    try:
        with _get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM vencimientos WHERE id = %s", (vencimiento_id,))
            affected = cursor.rowcount
            conn.commit()
            cursor.close()

            if affected == 0:
                raise HTTPException(status_code=404, detail="Vencimiento no encontrado")

        # Invalidar caché al eliminar
        _vencimientos_cache.invalidate()

        return {"mensaje": "Vencimiento eliminado", "id": vencimiento_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando vencimiento {vencimiento_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar vencimiento: {str(e)}")


@router.post("/{vencimiento_id}/atender", response_model=VencimientoResponse)
async def marcar_como_atendido(
    vencimiento_id: int,
    notas: Optional[str] = Query(None, description="Notas opcionales")
):
    """
    Marca un vencimiento como atendido/cumplido.
    """
    request = VencimientoUpdate(estado=EstadoVencimiento.atendido, notas=notas)
    return await actualizar_vencimiento(vencimiento_id, request)


@router.post("/{vencimiento_id}/cancelar", response_model=VencimientoResponse)
async def cancelar_vencimiento(
    vencimiento_id: int,
    notas: Optional[str] = Query(None, description="Motivo de cancelación")
):
    """
    Cancela un vencimiento (ya no aplica).
    """
    request = VencimientoUpdate(estado=EstadoVencimiento.cancelado, notas=notas)
    return await actualizar_vencimiento(vencimiento_id, request)


@router.get("/expediente/{expediente_numero}", response_model=List[VencimientoResponse])
async def obtener_vencimientos_expediente(expediente_numero: str):
    """
    Obtiene todos los vencimientos de un expediente.
    """
    try:
        with _get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT
                    v.*,
                    DATEDIFF(v.fecha_vencimiento, CURDATE()) as dias_restantes
                FROM vencimientos v
                WHERE v.expediente_numero = %s
                ORDER BY v.fecha_vencimiento ASC
            """, (expediente_numero,))

            rows = cursor.fetchall()
            cursor.close()

        return [_row_to_response(row) for row in rows]

    except Exception as e:
        logger.error(f"Error obteniendo vencimientos de {expediente_numero}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener vencimientos: {str(e)}")
