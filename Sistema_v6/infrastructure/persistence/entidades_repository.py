"""
Repositorio MySQL para entidades extraidas.

CRUD para entidades NER (extraidas por IA o agregadas manualmente).
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

import mysql.connector
from mysql.connector import Error as MySQLError

logger = logging.getLogger(__name__)


class EntidadesRepository:
    """
    Repositorio para gestionar entidades extraidas en MySQL.

    Soporta:
    - Entidades extraidas automaticamente por IA (GLiNER)
    - Entidades agregadas/editadas manualmente por usuarios
    """

    def __init__(self, db_config: Optional[Dict[str, Any]] = None):
        """
        Inicializa el repositorio.

        Args:
            db_config: Configuracion de BD. Si no se provee, usa variables de entorno.
        """
        if db_config:
            self.db_config = db_config
        else:
            self.db_config = {
                'host': os.getenv('MYSQL_HOST', 'localhost'),
                'port': int(os.getenv('MYSQL_PORT', '3306')),
                'database': os.getenv('MYSQL_DATABASE', 'sintaxis'),
                'user': os.getenv('MYSQL_USER', 'root'),
                'password': os.getenv('MYSQL_PASSWORD', ''),
                'charset': 'utf8mb4',
                'collation': 'utf8mb4_unicode_ci'
            }

        logger.info(f"EntidadesRepository inicializado para BD: {self.db_config.get('database')}")

    def _get_connection(self):
        """Obtiene una conexion a la base de datos."""
        try:
            conn = mysql.connector.connect(**self.db_config)
            return conn
        except MySQLError as e:
            logger.error(f"Error conectando a MySQL: {e}")
            raise

    def crear(
        self,
        expediente_numero: str,
        entity_type: str,
        entity_value: str,
        actuacion_id: Optional[int] = None,
        score: Optional[float] = None,
        start_pos: Optional[int] = None,
        end_pos: Optional[int] = None,
        origen: str = 'ia',
        usuario_id: Optional[int] = None,
        notas: Optional[str] = None
    ) -> int:
        """
        Crea una nueva entidad.

        Args:
            expediente_numero: Numero del expediente
            entity_type: Tipo de entidad (PERSONA, MONTO, etc.)
            entity_value: Valor de la entidad
            actuacion_id: ID de la actuacion (opcional)
            score: Confianza IA (0-1)
            start_pos: Posicion inicio en texto
            end_pos: Posicion fin en texto
            origen: 'ia' o 'manual'
            usuario_id: ID del usuario (para manuales)
            notas: Notas adicionales

        Returns:
            ID de la entidad creada
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = """
                INSERT INTO entidades_extraidas (
                    expediente_numero,
                    actuacion_id,
                    entity_type,
                    entity_value,
                    score,
                    start_pos,
                    end_pos,
                    origen,
                    usuario_id,
                    notas
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            params = (
                expediente_numero,
                actuacion_id,
                entity_type,
                entity_value,
                score,
                start_pos,
                end_pos,
                origen,
                usuario_id,
                notas
            )

            cursor.execute(query, params)
            conn.commit()
            entity_id = cursor.lastrowid

            logger.info(f"Entidad creada: {entity_type}='{entity_value[:50]}...' (ID: {entity_id})")

            cursor.close()
            conn.close()

            return entity_id

        except MySQLError as e:
            logger.error(f"Error creando entidad: {e}")
            raise

    def crear_batch(self, entidades: List[Dict[str, Any]]) -> int:
        """
        Crea multiples entidades en batch.

        Args:
            entidades: Lista de diccionarios con datos de entidades

        Returns:
            Numero de entidades creadas
        """
        if not entidades:
            return 0

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = """
                INSERT INTO entidades_extraidas (
                    expediente_numero,
                    actuacion_id,
                    entity_type,
                    entity_value,
                    score,
                    start_pos,
                    end_pos,
                    origen,
                    usuario_id,
                    notas
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            params_list = []
            for e in entidades:
                params_list.append((
                    e.get('expediente_numero'),
                    e.get('actuacion_id'),
                    e.get('entity_type'),
                    e.get('entity_value'),
                    e.get('score'),
                    e.get('start_pos'),
                    e.get('end_pos'),
                    e.get('origen', 'ia'),
                    e.get('usuario_id'),
                    e.get('notas')
                ))

            cursor.executemany(query, params_list)
            conn.commit()
            count = cursor.rowcount

            logger.info(f"Batch de {count} entidades creadas")

            cursor.close()
            conn.close()

            return count

        except MySQLError as e:
            logger.error(f"Error en batch de entidades: {e}")
            raise

    def obtener_por_expediente(
        self,
        expediente_numero: str,
        entity_type: Optional[str] = None,
        origen: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene entidades de un expediente.

        Args:
            expediente_numero: Numero del expediente
            entity_type: Filtrar por tipo (opcional)
            origen: Filtrar por origen 'ia' o 'manual' (opcional)

        Returns:
            Lista de entidades
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT
                    id,
                    expediente_numero,
                    actuacion_id,
                    entity_type,
                    entity_value,
                    score,
                    start_pos,
                    end_pos,
                    origen,
                    usuario_id,
                    notas,
                    fecha_creacion,
                    fecha_actualizacion
                FROM entidades_extraidas
                WHERE expediente_numero = %s
            """
            params = [expediente_numero]

            if entity_type:
                query += " AND entity_type = %s"
                params.append(entity_type)

            if origen:
                query += " AND origen = %s"
                params.append(origen)

            query += " ORDER BY entity_type, fecha_creacion DESC"

            cursor.execute(query, params)
            results = cursor.fetchall()

            # Convertir fechas a string
            for row in results:
                if row.get('fecha_creacion'):
                    row['fecha_creacion'] = row['fecha_creacion'].isoformat()
                if row.get('fecha_actualizacion'):
                    row['fecha_actualizacion'] = row['fecha_actualizacion'].isoformat()
                if row.get('score'):
                    row['score'] = float(row['score'])

            cursor.close()
            conn.close()

            return results

        except MySQLError as e:
            logger.error(f"Error obteniendo entidades: {e}")
            raise

    def obtener_por_actuacion(self, actuacion_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene entidades de una actuacion especifica.

        Args:
            actuacion_id: ID de la actuacion

        Returns:
            Lista de entidades
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT
                    id,
                    expediente_numero,
                    actuacion_id,
                    entity_type,
                    entity_value,
                    score,
                    start_pos,
                    end_pos,
                    origen,
                    usuario_id,
                    notas,
                    fecha_creacion,
                    fecha_actualizacion
                FROM entidades_extraidas
                WHERE actuacion_id = %s
                ORDER BY start_pos, entity_type
            """

            cursor.execute(query, (actuacion_id,))
            results = cursor.fetchall()

            # Convertir fechas a string
            for row in results:
                if row.get('fecha_creacion'):
                    row['fecha_creacion'] = row['fecha_creacion'].isoformat()
                if row.get('fecha_actualizacion'):
                    row['fecha_actualizacion'] = row['fecha_actualizacion'].isoformat()
                if row.get('score'):
                    row['score'] = float(row['score'])

            cursor.close()
            conn.close()

            return results

        except MySQLError as e:
            logger.error(f"Error obteniendo entidades por actuacion: {e}")
            raise

    def actualizar(
        self,
        entidad_id: int,
        entity_value: Optional[str] = None,
        entity_type: Optional[str] = None,
        notas: Optional[str] = None,
        usuario_id: Optional[int] = None
    ) -> bool:
        """
        Actualiza una entidad existente.

        Args:
            entidad_id: ID de la entidad
            entity_value: Nuevo valor
            entity_type: Nuevo tipo
            notas: Nuevas notas
            usuario_id: Usuario que modifica

        Returns:
            True si se actualizo
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            updates = []
            params = []

            if entity_value is not None:
                updates.append("entity_value = %s")
                params.append(entity_value)

            if entity_type is not None:
                updates.append("entity_type = %s")
                params.append(entity_type)

            if notas is not None:
                updates.append("notas = %s")
                params.append(notas)

            if usuario_id is not None:
                updates.append("usuario_id = %s")
                params.append(usuario_id)

            if not updates:
                return False

            query = f"""
                UPDATE entidades_extraidas
                SET {', '.join(updates)}
                WHERE id = %s
            """
            params.append(entidad_id)

            cursor.execute(query, params)
            conn.commit()
            updated = cursor.rowcount > 0

            cursor.close()
            conn.close()

            if updated:
                logger.info(f"Entidad {entidad_id} actualizada")

            return updated

        except MySQLError as e:
            logger.error(f"Error actualizando entidad: {e}")
            raise

    def eliminar(self, entidad_id: int) -> bool:
        """
        Elimina una entidad.

        Args:
            entidad_id: ID de la entidad

        Returns:
            True si se elimino
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = "DELETE FROM entidades_extraidas WHERE id = %s"
            cursor.execute(query, (entidad_id,))
            conn.commit()
            deleted = cursor.rowcount > 0

            cursor.close()
            conn.close()

            if deleted:
                logger.info(f"Entidad {entidad_id} eliminada")

            return deleted

        except MySQLError as e:
            logger.error(f"Error eliminando entidad: {e}")
            raise

    def eliminar_por_expediente(
        self,
        expediente_numero: str,
        origen: Optional[str] = None
    ) -> int:
        """
        Elimina todas las entidades de un expediente.

        Args:
            expediente_numero: Numero del expediente
            origen: Solo eliminar de origen especifico

        Returns:
            Numero de entidades eliminadas
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = "DELETE FROM entidades_extraidas WHERE expediente_numero = %s"
            params = [expediente_numero]

            if origen:
                query += " AND origen = %s"
                params.append(origen)

            cursor.execute(query, params)
            conn.commit()
            count = cursor.rowcount

            cursor.close()
            conn.close()

            logger.info(f"Eliminadas {count} entidades del expediente {expediente_numero}")

            return count

        except MySQLError as e:
            logger.error(f"Error eliminando entidades: {e}")
            raise

    def obtener_estadisticas(self, expediente_numero: str) -> Dict[str, Any]:
        """
        Obtiene estadisticas de entidades de un expediente.

        Args:
            expediente_numero: Numero del expediente

        Returns:
            Dict con estadisticas
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)

            # Total por tipo
            query = """
                SELECT
                    entity_type,
                    COUNT(*) as total,
                    SUM(CASE WHEN origen = 'ia' THEN 1 ELSE 0 END) as por_ia,
                    SUM(CASE WHEN origen = 'manual' THEN 1 ELSE 0 END) as manuales,
                    AVG(CASE WHEN origen = 'ia' THEN score ELSE NULL END) as avg_score
                FROM entidades_extraidas
                WHERE expediente_numero = %s
                GROUP BY entity_type
                ORDER BY total DESC
            """

            cursor.execute(query, (expediente_numero,))
            por_tipo = cursor.fetchall()

            # Convertir decimales
            for row in por_tipo:
                if row.get('avg_score'):
                    row['avg_score'] = float(row['avg_score'])

            # Totales
            query_totales = """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN origen = 'ia' THEN 1 ELSE 0 END) as total_ia,
                    SUM(CASE WHEN origen = 'manual' THEN 1 ELSE 0 END) as total_manual
                FROM entidades_extraidas
                WHERE expediente_numero = %s
            """

            cursor.execute(query_totales, (expediente_numero,))
            totales = cursor.fetchone()

            cursor.close()
            conn.close()

            return {
                'expediente_numero': expediente_numero,
                'total': totales['total'] or 0,
                'total_ia': totales['total_ia'] or 0,
                'total_manual': totales['total_manual'] or 0,
                'por_tipo': por_tipo
            }

        except MySQLError as e:
            logger.error(f"Error obteniendo estadisticas: {e}")
            raise

    def obtener_tipos_disponibles(self) -> List[str]:
        """
        Obtiene la lista de tipos de entidad disponibles.

        Returns:
            Lista de tipos
        """
        from application.services.ia.ner_service import ENTIDADES_JURIDICAS
        return ENTIDADES_JURIDICAS
