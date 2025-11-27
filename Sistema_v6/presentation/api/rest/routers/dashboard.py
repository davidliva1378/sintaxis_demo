"""
Router REST API para Dashboard.

Endpoints consolidados para el panel de control:
- Estadísticas globales (KPIs)
- Estado de salud del sistema completo
- Últimos movimientos/actividad
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import logging
import os
import httpx

from infrastructure.config import get_settings
from infrastructure.rag.config import get_rag_settings
from infrastructure.persistence.database import (
    test_mysql_connection,
    get_mysql_pool_status,
)
from infrastructure.di_container import get_container

logger = logging.getLogger(__name__)


# ============================================================================
# Modelos de Response
# ============================================================================


class DashboardStatsResponse(BaseModel):
    """KPIs principales del dashboard"""
    total_expedientes: int = Field(description="Total de expedientes en el sistema")
    expedientes_semana: int = Field(description="Expedientes agregados esta semana")
    vencimientos_urgentes: int = Field(description="Vencimientos en los próximos 7 días")
    vencimientos_vencidos: int = Field(description="Vencimientos ya vencidos")
    expedientes_monitoreados: int = Field(description="Expedientes activos en monitoreo")
    porcentaje_procesado_ia: float = Field(description="% actuaciones procesadas con IA")
    total_actuaciones: int = Field(description="Total de actuaciones procesadas")
    documentos_indexados_rag: int = Field(description="Documentos en índice RAG")


class ServiceHealthStatus(BaseModel):
    """Estado de un servicio individual"""
    name: str
    status: str  # 'ok', 'error', 'warning', 'unknown'
    message: Optional[str] = None
    response_time_ms: Optional[float] = None


class SystemHealthResponse(BaseModel):
    """Estado completo del sistema"""
    overall_status: str  # 'healthy', 'degraded', 'critical'
    services: List[ServiceHealthStatus]
    timestamp: datetime


class MovimientoReciente(BaseModel):
    """Movimiento/actividad reciente en el sistema"""
    id: int
    tipo: str  # 'extraccion', 'monitoreo', 'procesamiento', 'alerta'
    descripcion: str
    expediente_numero: Optional[str] = None
    fecha: datetime
    icono: str = "bell"


class UltimosMovimientosResponse(BaseModel):
    """Lista de movimientos recientes"""
    movimientos: List[MovimientoReciente]
    total: int


# ============================================================================
# Router
# ============================================================================


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


def _get_db_connection():
    """Obtiene conexión MySQL desde el pool."""
    from infrastructure.persistence.database import get_mysql_connection
    return get_mysql_connection()


@router.get("/stats", response_model=DashboardStatsResponse)
async def obtener_estadisticas_dashboard():
    """
    Obtiene las estadísticas consolidadas para el dashboard.

    Combina datos de:
    - Workspaces (expedientes)
    - Procesamiento (actuaciones, vencimientos)
    - Monitoreo (expedientes monitoreados)
    - RAG (documentos indexados)

    Returns:
        DashboardStatsResponse con todos los KPIs
    """
    try:
        conn = _get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. Total expedientes (desde workspaces)
        cursor.execute("""
            SELECT COUNT(DISTINCT expediente_numero) as total
            FROM workspaces
            WHERE expediente_numero IS NOT NULL
        """)
        result = cursor.fetchone()
        total_expedientes = result['total'] if result else 0

        # 2. Expedientes esta semana
        cursor.execute("""
            SELECT COUNT(DISTINCT expediente_numero) as total
            FROM workspaces
            WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        """)
        result = cursor.fetchone()
        expedientes_semana = result['total'] if result else 0

        # 3. Vencimientos urgentes (próximos 7 días)
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM vencimientos
            WHERE fecha_vencimiento BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY)
        """)
        result = cursor.fetchone()
        vencimientos_urgentes = result['total'] if result else 0

        # 4. Vencimientos vencidos (fecha pasada)
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM vencimientos
            WHERE fecha_vencimiento < CURDATE()
        """)
        result = cursor.fetchone()
        vencimientos_vencidos = result['total'] if result else 0

        # 5. Expedientes monitoreados activos
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM expedientes_monitoreo
            WHERE activo = 1
        """)
        result = cursor.fetchone()
        expedientes_monitoreados = result['total'] if result else 0

        # 6. Total actuaciones y % procesadas con IA
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN tipo_ia IS NOT NULL THEN 1 ELSE 0 END) as con_ia
            FROM actuaciones
        """)
        result = cursor.fetchone()
        total_actuaciones = result['total'] if result else 0
        con_ia = result['con_ia'] if result else 0
        porcentaje_ia = (con_ia / total_actuaciones * 100) if total_actuaciones > 0 else 0

        # 7. Documentos RAG indexados
        documentos_rag = 0
        try:
            container = get_container()
            if hasattr(container, 'rag_service') and container.rag_service:
                stats = container.rag_service.get_stats()
                documentos_rag = stats.get('total_documents', 0)
        except Exception as e:
            logger.warning(f"No se pudo obtener stats RAG: {e}")

        cursor.close()
        conn.close()

        return DashboardStatsResponse(
            total_expedientes=total_expedientes,
            expedientes_semana=expedientes_semana,
            vencimientos_urgentes=vencimientos_urgentes,
            vencimientos_vencidos=vencimientos_vencidos,
            expedientes_monitoreados=expedientes_monitoreados,
            porcentaje_procesado_ia=round(porcentaje_ia, 1),
            total_actuaciones=total_actuaciones,
            documentos_indexados_rag=documentos_rag
        )

    except Exception as e:
        logger.error(f"Error obteniendo estadísticas dashboard: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener estadísticas: {str(e)}"
        )


@router.get("/health", response_model=SystemHealthResponse)
async def obtener_salud_sistema():
    """
    Obtiene el estado de salud completo del sistema.

    Verifica:
    - Backend API (siempre ok si responde)
    - MySQL Database
    - Qdrant (RAG)
    - Ollama (LLM)
    - Monitoreo Scheduler

    Returns:
        SystemHealthResponse con estado de cada servicio
    """
    services = []

    # 1. Backend API - siempre ok si llegamos aquí
    services.append(ServiceHealthStatus(
        name="Backend API",
        status="ok",
        message="Operativo"
    ))

    # 2. MySQL Database
    try:
        mysql_ok = test_mysql_connection()
        pool_status = get_mysql_pool_status()
        services.append(ServiceHealthStatus(
            name="MySQL",
            status="ok" if mysql_ok else "error",
            message=f"Pool: {pool_status.get('checked_out', 0)}/{pool_status.get('pool_size', 0)}" if mysql_ok else "Sin conexión"
        ))
    except Exception as e:
        services.append(ServiceHealthStatus(
            name="MySQL",
            status="error",
            message=str(e)
        ))

    # 3. Qdrant (RAG)
    try:
        rag_settings = get_rag_settings()
        qdrant_url = f"http://{rag_settings.qdrant_host}:{rag_settings.qdrant_port}/collections"
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(qdrant_url)
            if response.status_code == 200:
                services.append(ServiceHealthStatus(
                    name="Qdrant (RAG)",
                    status="ok",
                    message="Operativo",
                    response_time_ms=response.elapsed.total_seconds() * 1000
                ))
            else:
                services.append(ServiceHealthStatus(
                    name="Qdrant (RAG)",
                    status="warning",
                    message=f"HTTP {response.status_code}"
                ))
    except Exception as e:
        services.append(ServiceHealthStatus(
            name="Qdrant (RAG)",
            status="error",
            message="No disponible"
        ))

    # 4. Ollama (LLM)
    try:
        ollama_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{ollama_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                services.append(ServiceHealthStatus(
                    name="Ollama (LLM)",
                    status="ok",
                    message=f"{len(models)} modelos disponibles",
                    response_time_ms=response.elapsed.total_seconds() * 1000
                ))
            else:
                services.append(ServiceHealthStatus(
                    name="Ollama (LLM)",
                    status="warning",
                    message=f"HTTP {response.status_code}"
                ))
    except Exception as e:
        services.append(ServiceHealthStatus(
            name="Ollama (LLM)",
            status="error",
            message="No disponible"
        ))

    # 5. Monitoreo Scheduler
    try:
        container = get_container()
        scheduler = container.monitor_scheduler
        estado = scheduler.obtener_estado()
        if estado.get('activo'):
            services.append(ServiceHealthStatus(
                name="Monitoreo",
                status="ok",
                message=f"Próx: {estado.get('proxima_ejecucion', 'N/A')}"
            ))
        else:
            services.append(ServiceHealthStatus(
                name="Monitoreo",
                status="warning",
                message="Scheduler inactivo"
            ))
    except Exception as e:
        services.append(ServiceHealthStatus(
            name="Monitoreo",
            status="unknown",
            message="No se pudo verificar"
        ))

    # Determinar estado general
    statuses = [s.status for s in services]
    if all(s == 'ok' for s in statuses):
        overall = 'healthy'
    elif 'error' in statuses:
        overall = 'critical' if statuses.count('error') > 1 else 'degraded'
    else:
        overall = 'degraded'

    return SystemHealthResponse(
        overall_status=overall,
        services=services,
        timestamp=datetime.now()
    )


@router.get("/movimientos", response_model=UltimosMovimientosResponse)
async def obtener_ultimos_movimientos(limite: int = 10):
    """
    Obtiene los últimos movimientos/actividad del sistema.

    Combina:
    - Logs de monitoreo
    - Extracciones recientes
    - Alertas de vencimientos

    Args:
        limite: Máximo de movimientos a retornar (default: 10)

    Returns:
        Lista de movimientos recientes ordenados por fecha
    """
    try:
        conn = _get_db_connection()
        cursor = conn.cursor(dictionary=True)

        movimientos = []

        # 1. Logs de monitoreo recientes
        cursor.execute("""
            SELECT
                id,
                'monitoreo' as tipo,
                CONCAT(
                    'Monitoreo: ',
                    COALESCE(expedientes_revisados, 0), ' revisados, ',
                    COALESCE(con_cambios, 0), ' con cambios'
                ) as descripcion,
                NULL as expediente_numero,
                fecha_inicio as fecha,
                'refresh-cw' as icono
            FROM monitoreo_logs
            ORDER BY fecha_inicio DESC
            LIMIT %s
        """, (limite,))

        for row in cursor.fetchall():
            movimientos.append(MovimientoReciente(**row))

        # 2. Actuaciones recientes (últimas extraídas/procesadas)
        cursor.execute("""
            SELECT
                a.id,
                'extraccion' as tipo,
                CONCAT(a.tipo, ' - ', LEFT(a.detalle, 50), '...') as descripcion,
                a.expediente_numero,
                a.fecha_creacion as fecha,
                'download' as icono
            FROM actuaciones a
            WHERE a.fecha_creacion >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            ORDER BY a.fecha_creacion DESC
            LIMIT %s
        """, (limite,))

        for row in cursor.fetchall():
            if row['fecha']:
                movimientos.append(MovimientoReciente(**row))

        # 3. Vencimientos próximos (alertas)
        cursor.execute("""
            SELECT
                v.id,
                'alerta' as tipo,
                CONCAT('Vencimiento: ', v.tipo, ' - ', v.descripcion) as descripcion,
                v.expediente_numero,
                v.fecha_vencimiento as fecha,
                'alert-triangle' as icono
            FROM vencimientos v
            WHERE v.fecha_vencimiento BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 3 DAY)
            ORDER BY v.fecha_vencimiento ASC
            LIMIT %s
        """, (limite,))

        for row in cursor.fetchall():
            if row['fecha']:
                movimientos.append(MovimientoReciente(**row))

        cursor.close()
        conn.close()

        # Ordenar por fecha y limitar
        movimientos.sort(key=lambda x: x.fecha, reverse=True)
        movimientos = movimientos[:limite]

        return UltimosMovimientosResponse(
            movimientos=movimientos,
            total=len(movimientos)
        )

    except Exception as e:
        logger.error(f"Error obteniendo últimos movimientos: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener movimientos: {str(e)}"
        )


@router.get("/vencimientos-urgentes")
async def obtener_vencimientos_dashboard(limite: int = 5):
    """
    Obtiene los vencimientos más urgentes para mostrar en el dashboard.

    Args:
        limite: Máximo de vencimientos a retornar (default: 5)

    Returns:
        Lista de vencimientos urgentes con nivel de urgencia
    """
    try:
        conn = _get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                v.id,
                v.expediente_numero,
                v.tipo,
                v.descripcion,
                v.fecha_vencimiento,
                DATEDIFF(v.fecha_vencimiento, CURDATE()) as dias_restantes,
                CASE
                    WHEN DATEDIFF(v.fecha_vencimiento, CURDATE()) < 0 THEN 'vencido'
                    WHEN DATEDIFF(v.fecha_vencimiento, CURDATE()) <= 1 THEN 'critico'
                    WHEN DATEDIFF(v.fecha_vencimiento, CURDATE()) <= 3 THEN 'urgente'
                    ELSE 'proximo'
                END as nivel_urgencia
            FROM vencimientos v
            WHERE v.fecha_vencimiento >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            ORDER BY v.fecha_vencimiento ASC
            LIMIT %s
        """, (limite,))

        vencimientos = cursor.fetchall()

        cursor.close()
        conn.close()

        return {
            "vencimientos": vencimientos,
            "total": len(vencimientos)
        }

    except Exception as e:
        logger.error(f"Error obteniendo vencimientos dashboard: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener vencimientos: {str(e)}"
        )
