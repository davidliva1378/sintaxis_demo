"""
Repositorio MySQL para expedientes.

Sincroniza expedientes_index.json con la tabla expedientes de MySQL.
Provee métodos para:
- Crear/actualizar expedientes
- Obtener ID por número normalizado
- Sincronización masiva desde JSON
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Sequence, Set

import mysql.connector
from mysql.connector import Error as MySQLError

from application.ports import IExpedienteRepository
from core.domain.entities import ExpedienteResumen

logger = logging.getLogger(__name__)


class ExpedientesRepository(IExpedienteRepository):
    """
    Repositorio para gestionar expedientes en MySQL.

    Mantiene sincronización entre expedientes_index.json y tabla MySQL.
    """

    def __init__(self, db_config: Optional[Dict[str, Any]] = None):
        """
        Inicializa el repositorio.

        Args:
            db_config: Configuración de BD. Si no se provee, usa variables de entorno.
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

        logger.info(f"ExpedientesRepository inicializado para BD: {self.db_config.get('database')}")

    def _get_connection(self):
        """Obtiene una conexión a la base de datos."""
        try:
            conn = mysql.connector.connect(**self.db_config)
            return conn
        except MySQLError as e:
            logger.error(f"Error conectando a MySQL: {e}")
            raise

    def _map_row_to_entity(self, row: Dict[str, Any]) -> ExpedienteResumen:
        """Mapea una fila de BD a entidad ExpedienteResumen."""
        return ExpedienteResumen(
            numero=row['numero_normalizado'],
            dependencia=row['dependencia'] or "Sin dependencia",
            caratula=row['caratula'] or "Sin carátula",
            situacion=row['situacion'],
            ultima_actuacion=row['ultima_actuacion'].isoformat() if row['ultima_actuacion'] else None
        )

    def crear_o_actualizar(
        self,
        expediente_id: Optional[int],
        numero_normalizado: str,
        numero_original: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Crea o actualiza un expediente en MySQL.

        Args:
            expediente_id: ID del índice JSON (opcional)
            numero_normalizado: Número normalizado (ej: FPA_012332_2019)
            numero_original: Número original (ej: FPA 012332/2019)
            metadata: Datos adicionales (dependencia, caratula, etc.)

        Returns:
            True si se guardó correctamente
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Extraer campos de metadata
            dependencia = None
            caratula = None
            situacion = None
            ultima_actuacion = None
            estado_monitoreo = 'activo'
            prioridad = 'normal'

            if metadata:
                # Datos del portal
                estado_portal = metadata.get('estado_portal', {})
                dependencia = estado_portal.get('dependencia') or metadata.get('dependencia')
                caratula = estado_portal.get('caratula') or metadata.get('caratula')
                situacion = estado_portal.get('situacion') or metadata.get('situacion')
                ultima_actuacion_str = estado_portal.get('ultima_actuacion') or metadata.get('ultima_actuacion')

                if ultima_actuacion_str:
                    try:
                        # Intentar parsear la fecha
                        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']:
                            try:
                                ultima_actuacion = datetime.strptime(ultima_actuacion_str, fmt).date()
                                break
                            except ValueError:
                                continue
                    except Exception:
                        pass

                # Datos de monitoreo
                monitoreo = metadata.get('monitoreo', {})
                estado_monitoreo = monitoreo.get('estado', 'activo')
                prioridad = monitoreo.get('prioridad', 'normal')

            if expediente_id is not None:
                # Query con ID explícito
                query = """
                    INSERT INTO expedientes (
                        id,
                        numero_normalizado,
                        numero_original,
                        dependencia,
                        caratula,
                        situacion,
                        ultima_actuacion,
                        estado_monitoreo,
                        prioridad,
                        fecha_creacion
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        numero_original = VALUES(numero_original),
                        dependencia = COALESCE(VALUES(dependencia), dependencia),
                        caratula = COALESCE(VALUES(caratula), caratula),
                        situacion = COALESCE(VALUES(situacion), situacion),
                        ultima_actuacion = COALESCE(VALUES(ultima_actuacion), ultima_actuacion),
                        estado_monitoreo = VALUES(estado_monitoreo),
                        prioridad = VALUES(prioridad)
                """
                params = (
                    expediente_id,
                    numero_normalizado,
                    numero_original,
                    dependencia,
                    caratula,
                    situacion,
                    ultima_actuacion,
                    estado_monitoreo,
                    prioridad,
                    datetime.now()
                )
            else:
                # Query sin ID (auto-increment)
                query = """
                    INSERT INTO expedientes (
                        numero_normalizado,
                        numero_original,
                        dependencia,
                        caratula,
                        situacion,
                        ultima_actuacion,
                        estado_monitoreo,
                        prioridad,
                        fecha_creacion
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        numero_original = VALUES(numero_original),
                        dependencia = COALESCE(VALUES(dependencia), dependencia),
                        caratula = COALESCE(VALUES(caratula), caratula),
                        situacion = COALESCE(VALUES(situacion), situacion),
                        ultima_actuacion = COALESCE(VALUES(ultima_actuacion), ultima_actuacion),
                        estado_monitoreo = VALUES(estado_monitoreo),
                        prioridad = VALUES(prioridad)
                """
                params = (
                    numero_normalizado,
                    numero_original,
                    dependencia,
                    caratula,
                    situacion,
                    ultima_actuacion,
                    estado_monitoreo,
                    prioridad,
                    datetime.now()
                )

            cursor.execute(query, params)
            conn.commit()

            logger.debug(f"Expediente {numero_normalizado} guardado (ID: {expediente_id if expediente_id else 'Auto'})")

            cursor.close()
            conn.close()

            return True

        except MySQLError as e:
            logger.error(f"Error guardando expediente {numero_normalizado}: {e}")
            return False

    async def guardar(self, expediente: ExpedienteResumen) -> None:
        """Guarda un expediente en el repositorio."""
        # Convertir entidad a metadata para crear_o_actualizar
        metadata = {
            'dependencia': expediente.dependencia,
            'caratula': expediente.caratula,
            'situacion': expediente.situacion,
            'ultima_actuacion': expediente.ultima_actuacion
        }
        
        # Intentar obtener ID existente para mantenerlo si es posible (aunque crear_o_actualizar lo maneja con ON DUPLICATE KEY)
        # Pero crear_o_actualizar sin ID usa auto-increment para nuevos.
        # Si ya existe, ON DUPLICATE KEY UPDATE actualiza.
        # Así que pasar None es seguro.
        
        # Reconstruir numero original (aproximado) si no lo tenemos
        numero_original = expediente.numero.replace('_', ' ').replace(' ', '/', 1)
        
        self.crear_o_actualizar(
            expediente_id=None,
            numero_normalizado=expediente.numero,
            numero_original=numero_original,
            metadata=metadata
        )

    async def guardar_varios(self, expedientes: Sequence[ExpedienteResumen]) -> None:
        """Guarda múltiples expedientes en el repositorio."""
        for exp in expedientes:
            await self.guardar(exp)

    async def recargar(self) -> None:
        """Recarga los expedientes (no-op en MySQL)."""
        pass

    async def existe(self, numero: str) -> bool:
        """Verifica si existe un expediente con el número dado."""
        from core.domain.expediente_utils import normalizar_numero_expediente
        numero_normalizado = normalizar_numero_expediente(numero)
        return self.obtener_id(numero_normalizado) is not None

    async def verificar_existencia_masiva(self, numeros: List[str]) -> Set[str]:
        """
        Verifica la existencia de múltiples expedientes.
        
        Args:
            numeros: Lista de números de expediente
            
        Returns:
            Set con los números normalizados que existen en la BD
        """
        if not numeros:
            return set()
            
        from core.domain.expediente_utils import normalizar_numero_expediente
        numeros_norm = [normalizar_numero_expediente(n) for n in numeros]
        
        if not numeros_norm:
            return set()
            
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Crear placeholders para la query IN (%s, %s, ...)
            placeholders = ', '.join(['%s'] * len(numeros_norm))
            query = f"SELECT numero_normalizado FROM expedientes WHERE numero_normalizado IN ({placeholders})"
            
            cursor.execute(query, numeros_norm)
            resultados = cursor.fetchall()
            
            existentes = {row[0] for row in resultados}
            
            cursor.close()
            conn.close()
            
            return existentes
            
        except MySQLError as e:
            logger.error(f"Error verificando existencia masiva: {e}")
            return set()


    def _obtener_fila_por_numero(self, numero_normalizado: str) -> Optional[Dict[str, Any]]:
        """Obtiene la fila cruda de un expediente por su número."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)

            query = "SELECT * FROM expedientes WHERE numero_normalizado = %s"
            cursor.execute(query, (numero_normalizado,))

            resultado = cursor.fetchone()

            cursor.close()
            conn.close()

            return resultado

        except MySQLError as e:
            logger.error(f"Error obteniendo expediente {numero_normalizado}: {e}")
            return None

    async def obtener_por_numero(self, numero: str) -> ExpedienteResumen | None:
        """
        Obtiene un expediente por su número.

        Args:
            numero: Número del expediente

        Returns:
            ExpedienteResumen o None
        """
        # Normalizar número si es necesario (el repo espera normalizado)
        # Pero la interfaz recibe "numero" genérico.
        # Asumimos que el caller puede pasar cualquiera, así que normalizamos.
        # Importar normalización aquí para evitar circular imports si es necesario
        from core.domain.expediente_utils import normalizar_numero_expediente
        numero_normalizado = normalizar_numero_expediente(numero)
        
        row = self._obtener_fila_por_numero(numero_normalizado)
        if row:
            return self._map_row_to_entity(row)
        return None

    def obtener_id(self, numero_normalizado: str) -> Optional[int]:
        """
        Obtiene el ID de un expediente por su número normalizado.

        Args:
            numero_normalizado: Número normalizado del expediente

        Returns:
            ID del expediente o None si no existe
        """
        row = self._obtener_fila_por_numero(numero_normalizado)
        return row['id'] if row else None

    def actualizar_extraccion(
        self,
        expediente_id: int,
        total_actuaciones: int = 0,
        total_pdfs: int = 0
    ) -> bool:
        """
        Actualiza datos de extracción de un expediente.

        Args:
            expediente_id: ID del expediente
            total_actuaciones: Total de actuaciones extraídas
            total_pdfs: Total de PDFs descargados

        Returns:
            True si se actualizó correctamente
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = """
                UPDATE expedientes
                SET fecha_ultima_extraccion = %s,
                    total_actuaciones = %s,
                    total_pdfs_descargados = %s
                WHERE id = %s
            """

            cursor.execute(query, (datetime.now(), total_actuaciones, total_pdfs, expediente_id))
            conn.commit()

            cursor.close()
            conn.close()

            return True

        except MySQLError as e:
            logger.error(f"Error actualizando extracción de expediente {expediente_id}: {e}")
            return False

    def actualizar_procesamiento(self, expediente_id: int) -> bool:
        """
        Marca un expediente como procesado.

        Args:
            expediente_id: ID del expediente

        Returns:
            True si se actualizó correctamente
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = """
                UPDATE expedientes
                SET fecha_ultimo_procesamiento = %s
                WHERE id = %s
            """

            cursor.execute(query, (datetime.now(), expediente_id))
            conn.commit()

            cursor.close()
            conn.close()

            return True

        except MySQLError as e:
            logger.error(f"Error actualizando procesamiento de expediente {expediente_id}: {e}")
            return False

    def sincronizar_desde_json(self, ruta_index: Path) -> Dict[str, int]:
        """
        Sincroniza todos los expedientes desde expedientes_index.json a MySQL.

        Args:
            ruta_index: Ruta al archivo expedientes_index.json

        Returns:
            Dict con estadísticas de sincronización
        """
        stats = {
            'procesados': 0,
            'creados': 0,
            'actualizados': 0,
            'errores': 0
        }

        if not ruta_index.exists():
            logger.warning(f"Archivo de índice no encontrado: {ruta_index}")
            return stats

        try:
            with open(ruta_index, 'r', encoding='utf-8') as f:
                indice = json.load(f)

            expedientes = indice.get('expedientes', {})

            for numero_normalizado, exp_id in expedientes.items():
                stats['procesados'] += 1

                # Verificar si ya existe
                existente = self.obtener_por_numero(numero_normalizado)

                # Reconstruir número original (revertir normalización básica)
                numero_original = numero_normalizado.replace('_', ' ').replace(' ', '/', 1)

                # Intentar cargar metadata del manifest.json si existe
                metadata = None
                directorio_expediente = ruta_index.parent / f"{exp_id:06d}_{numero_normalizado}"
                manifest_path = directorio_expediente / "manifest.json"

                if manifest_path.exists():
                    try:
                        with open(manifest_path, 'r', encoding='utf-8') as f:
                            manifest = json.load(f)
                            metadata = manifest.get('metadata', {})
                            # Usar número original del manifest si está disponible
                            if 'numero_expediente' in metadata:
                                numero_original = metadata['numero_expediente']
                    except Exception as e:
                        logger.debug(f"No se pudo leer manifest de {numero_normalizado}: {e}")

                success = self.crear_o_actualizar(
                    expediente_id=exp_id,
                    numero_normalizado=numero_normalizado,
                    numero_original=numero_original,
                    metadata=metadata
                )

                if success:
                    if existente:
                        stats['actualizados'] += 1
                    else:
                        stats['creados'] += 1
                else:
                    stats['errores'] += 1

            logger.info(
                f"Sincronización completada: {stats['procesados']} procesados, "
                f"{stats['creados']} creados, {stats['actualizados']} actualizados, "
                f"{stats['errores']} errores"
            )

        except Exception as e:
            logger.error(f"Error en sincronización desde JSON: {e}")
            stats['errores'] += 1

        return stats

    async def listar_todos(self, estado: Optional[str] = None) -> List[ExpedienteResumen]:
        """
        Lista todos los expedientes (método legacy, alias de obtener_todos con filtro).
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)

            if estado:
                query = "SELECT * FROM expedientes WHERE estado_monitoreo = %s ORDER BY id"
                cursor.execute(query, (estado,))
            else:
                query = "SELECT * FROM expedientes ORDER BY id"
                cursor.execute(query)

            resultados = cursor.fetchall()

            cursor.close()
            conn.close()

            return [self._map_row_to_entity(row) for row in resultados]

        except MySQLError as e:
            logger.error(f"Error listando expedientes: {e}")
            return []

    async def obtener_todos(self) -> list[ExpedienteResumen]:
        """Obtiene todos los expedientes del repositorio."""
        return await self.listar_todos()

    async def obtener_por_estado(self, estado: str) -> list[ExpedienteResumen]:
        """Obtiene expedientes filtrados por estado de monitoreo."""
        return await self.listar_todos(estado=estado)

    async def obtener_activos(self, dias: int = 30) -> list[ExpedienteResumen]:
        """Obtiene expedientes con movimientos recientes."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)

            # Calcular fecha de corte
            fecha_corte = datetime.now().date() - timedelta(days=dias)

            query = "SELECT * FROM expedientes WHERE ultima_actuacion >= %s ORDER BY ultima_actuacion DESC"
            cursor.execute(query, (fecha_corte,))

            resultados = cursor.fetchall()

            cursor.close()
            conn.close()

            return [self._map_row_to_entity(row) for row in resultados]

        except MySQLError as e:
            logger.error(f"Error obteniendo expedientes activos: {e}")
            return []

    async def filtrar_por_dependencia(self, dependencia: str) -> list[ExpedienteResumen]:
        """Filtra expedientes por dependencia."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)

            query = "SELECT * FROM expedientes WHERE dependencia LIKE %s ORDER BY id"
            cursor.execute(query, (f"%{dependencia}%",))

            resultados = cursor.fetchall()

            cursor.close()
            conn.close()

            return [self._map_row_to_entity(row) for row in resultados]

        except MySQLError as e:
            logger.error(f"Error filtrando por dependencia: {e}")
            return []

    async def contar(self) -> int:
        """
        Cuenta el total de expedientes en MySQL.

        Returns:
            Cantidad de expedientes
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM expedientes")
            resultado = cursor.fetchone()

            cursor.close()
            conn.close()

            return resultado[0] if resultado else 0

        except MySQLError as e:
            logger.error(f"Error contando expedientes: {e}")
            return 0

    async def eliminar(self, numero: str) -> bool:
        """
        Elimina un expediente del repositorio.

        Args:
            numero: Número del expediente a eliminar

        Returns:
            True si se eliminó, False si no existía
        """
        try:
            # Primero obtener ID para saber si existe
            from core.domain.expediente_utils import normalizar_numero_expediente
            numero_normalizado = normalizar_numero_expediente(numero)
            
            exp_id = self.obtener_id(numero_normalizado)
            if not exp_id:
                return False

            conn = self._get_connection()
            cursor = conn.cursor()

            query = "DELETE FROM expedientes WHERE id = %s"
            cursor.execute(query, (exp_id,))
            conn.commit()

            cursor.close()
            conn.close()

            logger.info(f"Eliminado expediente {numero} (ID: {exp_id})")
            return True

        except MySQLError as e:
            logger.error(f"Error eliminando expediente {numero}: {e}")
            return False

    def eliminar_todos(self) -> int:
        """
        Elimina todos los expedientes (usado en reset).

        Returns:
            Cantidad de registros eliminados
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Obtener count antes de eliminar
            cursor.execute("SELECT COUNT(*) FROM expedientes")
            count = cursor.fetchone()[0]

            cursor.execute("DELETE FROM expedientes")
            conn.commit()

            cursor.close()
            conn.close()

            logger.info(f"Eliminados {count} expedientes de MySQL")
            return count

        except MySQLError as e:
            logger.error(f"Error eliminando expedientes: {e}")
            return 0


# Instancia global (singleton pattern)
_repository_instance: Optional[ExpedientesRepository] = None


def get_expedientes_repository(db_config: Optional[Dict[str, Any]] = None) -> ExpedientesRepository:
    """
    Obtiene la instancia del repositorio de expedientes.

    Args:
        db_config: Configuración de BD (opcional)

    Returns:
        ExpedientesRepository
    """
    global _repository_instance

    if _repository_instance is None or db_config is not None:
        _repository_instance = ExpedientesRepository(db_config)

    return _repository_instance
