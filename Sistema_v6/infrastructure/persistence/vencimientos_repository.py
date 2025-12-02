"""
Repositorio MySQL para vencimientos.

Proporciona acceso a la tabla de vencimientos para el sistema de alertas.
"""

from __future__ import annotations

import logging
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List

from mysql.connector import Error as MySQLError

from infrastructure.persistence.database import get_pooled_connection

logger = logging.getLogger(__name__)


class VencimientosRepository:
    """
    Repositorio para consultar vencimientos desde MySQL.

    Usa el pool de conexiones para mejor rendimiento.
    """

    def listar_vencimientos(
        self,
        estado: Optional[str] = None,
        dias_desde: Optional[int] = None,
        dias_hasta: Optional[int] = None,
        expediente_numero: Optional[str] = None,
        tipo: Optional[str] = None,
        limite: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Lista vencimientos con filtros.

        Args:
            estado: Filtrar por estado (pendiente, atendido, vencido, cancelado)
            dias_desde: Días desde hoy (negativo = pasado)
            dias_hasta: Días hasta (positivo = futuro)
            expediente_numero: Filtrar por número de expediente
            tipo: Filtrar por tipo de vencimiento
            limite: Máximo de resultados
            offset: Offset para paginación

        Returns:
            Lista de vencimientos
        """
        conn = None
        try:
            conn = get_pooled_connection()
            cursor = conn.cursor(dictionary=True)

            conditions = []
            params = []

            # Filtro por estado
            if estado:
                conditions.append("estado = %s")
                params.append(estado)

            # Filtro por rango de fechas relativo
            hoy = date.today()
            if dias_desde is not None:
                fecha_desde = hoy + timedelta(days=dias_desde)
                conditions.append("fecha_vencimiento >= %s")
                params.append(fecha_desde)

            if dias_hasta is not None:
                fecha_hasta = hoy + timedelta(days=dias_hasta)
                conditions.append("fecha_vencimiento <= %s")
                params.append(fecha_hasta)

            # Filtro por expediente
            if expediente_numero:
                conditions.append("expediente_numero LIKE %s")
                params.append(f"%{expediente_numero}%")

            # Filtro por tipo
            if tipo:
                conditions.append("tipo = %s")
                params.append(tipo)

            where_clause = " AND ".join(conditions) if conditions else "1=1"
            params.extend([limite, offset])

            query = f"""
                SELECT
                    id,
                    expediente_numero,
                    tipo,
                    descripcion,
                    fecha_notificacion,
                    plazo_dias,
                    fecha_vencimiento,
                    dias_habiles,
                    estado,
                    DATEDIFF(fecha_vencimiento, CURDATE()) as dias_restantes,
                    texto_fuente,
                    confianza,
                    actuacion_id,
                    notas,
                    created_at,
                    updated_at
                FROM vencimientos
                WHERE {where_clause}
                ORDER BY fecha_vencimiento ASC
                LIMIT %s OFFSET %s
            """

            cursor.execute(query, params)
            results = cursor.fetchall()

            # Calcular nivel de urgencia
            for r in results:
                dias = r.get("dias_restantes", 0)
                if dias < 0:
                    r["nivel_urgencia"] = "vencido"
                elif dias <= 1:
                    r["nivel_urgencia"] = "critico"
                elif dias <= 3:
                    r["nivel_urgencia"] = "urgente"
                elif dias <= 7:
                    r["nivel_urgencia"] = "proximo"
                else:
                    r["nivel_urgencia"] = "futuro"

            cursor.close()
            return results

        except MySQLError as e:
            logger.error(f"Error listando vencimientos: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def obtener_por_id(self, vencimiento_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene un vencimiento por ID.

        Args:
            vencimiento_id: ID del vencimiento

        Returns:
            Vencimiento o None
        """
        conn = None
        try:
            conn = get_pooled_connection()
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT
                    id,
                    expediente_numero,
                    tipo,
                    descripcion,
                    fecha_notificacion,
                    plazo_dias,
                    fecha_vencimiento,
                    dias_habiles,
                    estado,
                    DATEDIFF(fecha_vencimiento, CURDATE()) as dias_restantes,
                    texto_fuente,
                    confianza,
                    actuacion_id,
                    notas,
                    created_at,
                    updated_at
                FROM vencimientos
                WHERE id = %s
            """

            cursor.execute(query, (vencimiento_id,))
            result = cursor.fetchone()

            if result:
                dias = result.get("dias_restantes", 0)
                if dias < 0:
                    result["nivel_urgencia"] = "vencido"
                elif dias <= 1:
                    result["nivel_urgencia"] = "critico"
                elif dias <= 3:
                    result["nivel_urgencia"] = "urgente"
                elif dias <= 7:
                    result["nivel_urgencia"] = "proximo"
                else:
                    result["nivel_urgencia"] = "futuro"

            cursor.close()
            return result

        except MySQLError as e:
            logger.error(f"Error obteniendo vencimiento {vencimiento_id}: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def contar_vencimientos(
        self,
        estado: Optional[str] = None,
        dias_desde: Optional[int] = None,
        dias_hasta: Optional[int] = None
    ) -> int:
        """
        Cuenta vencimientos según filtros.

        Args:
            estado: Filtrar por estado
            dias_desde: Días desde hoy
            dias_hasta: Días hasta

        Returns:
            Número de vencimientos
        """
        conn = None
        try:
            conn = get_pooled_connection()
            cursor = conn.cursor()

            conditions = []
            params = []

            if estado:
                conditions.append("estado = %s")
                params.append(estado)

            hoy = date.today()
            if dias_desde is not None:
                fecha_desde = hoy + timedelta(days=dias_desde)
                conditions.append("fecha_vencimiento >= %s")
                params.append(fecha_desde)

            if dias_hasta is not None:
                fecha_hasta = hoy + timedelta(days=dias_hasta)
                conditions.append("fecha_vencimiento <= %s")
                params.append(fecha_hasta)

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            query = f"""
                SELECT COUNT(*) FROM vencimientos
                WHERE {where_clause}
            """

            cursor.execute(query, params)
            count = cursor.fetchone()[0]
            cursor.close()
            return count

        except MySQLError as e:
            logger.error(f"Error contando vencimientos: {e}")
            return 0
        finally:
            if conn:
                conn.close()

    def obtener_estadisticas(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de vencimientos.

        Returns:
            Diccionario con estadísticas
        """
        conn = None
        try:
            conn = get_pooled_connection()
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN estado = 'pendiente' THEN 1 ELSE 0 END) as pendientes,
                    SUM(CASE WHEN estado = 'vencido' OR (estado = 'pendiente' AND fecha_vencimiento < CURDATE()) THEN 1 ELSE 0 END) as vencidos,
                    SUM(CASE WHEN estado = 'atendido' THEN 1 ELSE 0 END) as atendidos,
                    SUM(CASE WHEN estado = 'cancelado' THEN 1 ELSE 0 END) as cancelados,
                    SUM(CASE WHEN estado = 'pendiente' AND DATEDIFF(fecha_vencimiento, CURDATE()) <= 0 THEN 1 ELSE 0 END) as criticos_hoy,
                    SUM(CASE WHEN estado = 'pendiente' AND DATEDIFF(fecha_vencimiento, CURDATE()) BETWEEN 1 AND 3 THEN 1 ELSE 0 END) as urgentes_3_dias,
                    SUM(CASE WHEN estado = 'pendiente' AND DATEDIFF(fecha_vencimiento, CURDATE()) BETWEEN 4 AND 7 THEN 1 ELSE 0 END) as proximos_7_dias
                FROM vencimientos
            """

            cursor.execute(query)
            stats = cursor.fetchone()

            # Obtener conteo por tipo
            cursor.execute("""
                SELECT tipo, COUNT(*) as cantidad
                FROM vencimientos
                WHERE estado = 'pendiente'
                GROUP BY tipo
            """)
            por_tipo = {row["tipo"]: row["cantidad"] for row in cursor.fetchall()}

            cursor.close()

            return {
                "total": stats.get("total", 0),
                "pendientes": stats.get("pendientes", 0),
                "vencidos": stats.get("vencidos", 0),
                "atendidos": stats.get("atendidos", 0),
                "cancelados": stats.get("cancelados", 0),
                "criticos_hoy": stats.get("criticos_hoy", 0),
                "urgentes_3_dias": stats.get("urgentes_3_dias", 0),
                "proximos_7_dias": stats.get("proximos_7_dias", 0),
                "por_tipo": por_tipo
            }

        except MySQLError as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {
                "total": 0,
                "pendientes": 0,
                "vencidos": 0,
                "atendidos": 0,
                "cancelados": 0,
                "criticos_hoy": 0,
                "urgentes_3_dias": 0,
                "proximos_7_dias": 0,
                "por_tipo": {}
            }
        finally:
            if conn:
                conn.close()
