"""
Servicio de Feriados - Gestión dinámica de feriados y ferias judiciales.

Este servicio proporciona:
- Consulta de feriados por año/rango
- Verificación si una fecha es feriado
- Gestión de períodos de feria judicial
- Cálculo de días hábiles
"""

from __future__ import annotations

import logging
import os
from datetime import date, timedelta
from typing import Optional, List, Dict, Any, Tuple
from functools import lru_cache

import mysql.connector

logger = logging.getLogger(__name__)


class FeriadosService:
    """
    Servicio para gestionar feriados y ferias judiciales.

    Reemplaza el calendario estático por consultas dinámicas a la BD.
    """

    def __init__(self):
        """Inicializa el servicio."""
        self._cache_feriados: Dict[int, List[date]] = {}
        self._cache_ferias: Dict[int, Tuple[date, date]] = {}

    def _get_connection(self):
        """Obtiene conexión a MySQL."""
        return mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            database=os.getenv("MYSQL_DATABASE", "sintaxis"),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""),
        )

    # =========================================================================
    # CONSULTAS DE FERIADOS
    # =========================================================================

    def obtener_feriados_año(self, año: int) -> List[Dict[str, Any]]:
        """
        Obtiene todos los feriados de un año.

        Args:
            año: Año a consultar

        Returns:
            Lista de feriados con fecha, nombre, tipo
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT id, fecha, nombre, tipo, es_trasladable, activo
                FROM feriados
                WHERE año = %s AND activo = TRUE
                ORDER BY fecha
            """, (año,))

            feriados = cursor.fetchall()

            cursor.close()
            conn.close()

            return feriados

        except Exception as e:
            logger.error(f"Error obteniendo feriados de {año}: {e}")
            return []

    def obtener_feriados_rango(
        self,
        fecha_desde: date,
        fecha_hasta: date
    ) -> List[Dict[str, Any]]:
        """
        Obtiene feriados en un rango de fechas.

        Args:
            fecha_desde: Fecha inicial
            fecha_hasta: Fecha final

        Returns:
            Lista de feriados en el rango
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT id, fecha, nombre, tipo, es_trasladable
                FROM feriados
                WHERE fecha BETWEEN %s AND %s AND activo = TRUE
                ORDER BY fecha
            """, (fecha_desde, fecha_hasta))

            feriados = cursor.fetchall()

            cursor.close()
            conn.close()

            return feriados

        except Exception as e:
            logger.error(f"Error obteniendo feriados en rango: {e}")
            return []

    def es_feriado(self, fecha: date) -> Tuple[bool, Optional[str]]:
        """
        Verifica si una fecha es feriado.

        Args:
            fecha: Fecha a verificar

        Returns:
            Tupla (es_feriado, nombre_feriado)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT nombre, tipo
                FROM feriados
                WHERE fecha = %s AND activo = TRUE
            """, (fecha,))

            result = cursor.fetchone()

            cursor.close()
            conn.close()

            if result:
                return True, result['nombre']
            return False, None

        except Exception as e:
            logger.error(f"Error verificando feriado {fecha}: {e}")
            return False, None

    def obtener_fechas_feriados(self, año: int) -> List[date]:
        """
        Obtiene solo las fechas de feriados de un año (para cálculos).

        Incluye caché para mejorar rendimiento.

        Args:
            año: Año a consultar

        Returns:
            Lista de fechas de feriados
        """
        if año in self._cache_feriados:
            return self._cache_feriados[año]

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT fecha
                FROM feriados
                WHERE año = %s AND activo = TRUE
            """, (año,))

            fechas = [row[0] for row in cursor.fetchall()]

            cursor.close()
            conn.close()

            self._cache_feriados[año] = fechas
            return fechas

        except Exception as e:
            logger.error(f"Error obteniendo fechas de feriados: {e}")
            return []

    # =========================================================================
    # FERIA JUDICIAL
    # =========================================================================

    def obtener_feria_judicial(self, año: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene el período de feria judicial de un año.

        Args:
            año: Año a consultar

        Returns:
            Diccionario con fecha_inicio, fecha_fin, nombre
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT id, año, fecha_inicio, fecha_fin, nombre, activo
                FROM feria_judicial
                WHERE año = %s AND activo = TRUE
            """, (año,))

            feria = cursor.fetchone()

            cursor.close()
            conn.close()

            return feria

        except Exception as e:
            logger.error(f"Error obteniendo feria judicial de {año}: {e}")
            return None

    def es_feria_judicial(self, fecha: date) -> bool:
        """
        Verifica si una fecha cae en período de feria judicial.

        Args:
            fecha: Fecha a verificar

        Returns:
            True si está en feria judicial
        """
        año = fecha.year

        if año in self._cache_ferias:
            inicio, fin = self._cache_ferias[año]
            return inicio <= fecha <= fin

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT fecha_inicio, fecha_fin
                FROM feria_judicial
                WHERE año = %s AND activo = TRUE
            """, (año,))

            result = cursor.fetchone()

            cursor.close()
            conn.close()

            if result:
                inicio, fin = result
                self._cache_ferias[año] = (inicio, fin)
                return inicio <= fecha <= fin

            return False

        except Exception as e:
            logger.error(f"Error verificando feria judicial: {e}")
            return False

    # =========================================================================
    # CÁLCULO DE DÍAS HÁBILES (OPTIMIZADO)
    # =========================================================================

    def _cargar_feriados_rango(self, fecha_desde: date, fecha_hasta: date) -> set:
        """
        Carga feriados en un rango como set para búsquedas O(1).

        Args:
            fecha_desde: Fecha inicial
            fecha_hasta: Fecha final

        Returns:
            Set de fechas de feriados
        """
        # Recolectar años relevantes
        años = set()
        año_actual = fecha_desde.year
        while año_actual <= fecha_hasta.year:
            años.add(año_actual)
            año_actual += 1

        # Cargar feriados de todos los años en una sola consulta
        feriados_set = set()
        for año in años:
            feriados = self.obtener_fechas_feriados(año)
            feriados_set.update(feriados)

        return feriados_set

    def _cargar_ferias_rango(self, fecha_desde: date, fecha_hasta: date) -> List[Tuple[date, date]]:
        """
        Carga períodos de feria judicial para el rango.

        Args:
            fecha_desde: Fecha inicial
            fecha_hasta: Fecha final

        Returns:
            Lista de tuplas (inicio, fin) de períodos de feria
        """
        ferias = []
        año_actual = fecha_desde.year
        while año_actual <= fecha_hasta.year:
            feria = self.obtener_feria_judicial(año_actual)
            if feria:
                ferias.append((feria['fecha_inicio'], feria['fecha_fin']))
            año_actual += 1
        return ferias

    def _fecha_en_feria(self, fecha: date, ferias: List[Tuple[date, date]]) -> bool:
        """
        Verifica si una fecha está en algún período de feria.

        Args:
            fecha: Fecha a verificar
            ferias: Lista de períodos de feria

        Returns:
            True si está en feria
        """
        for inicio, fin in ferias:
            if inicio <= fecha <= fin:
                return True
        return False

    def es_dia_habil(self, fecha: date) -> bool:
        """
        Verifica si una fecha es día hábil.

        Un día NO es hábil si:
        - Es sábado o domingo
        - Es feriado
        - Está en período de feria judicial

        Args:
            fecha: Fecha a verificar

        Returns:
            True si es día hábil
        """
        # Fin de semana
        if fecha.weekday() >= 5:  # 5=sábado, 6=domingo
            return False

        # Feriado
        es_feriado, _ = self.es_feriado(fecha)
        if es_feriado:
            return False

        # Feria judicial
        if self.es_feria_judicial(fecha):
            return False

        return True

    def es_dia_habil_optimizado(
        self,
        fecha: date,
        feriados_set: set,
        ferias: List[Tuple[date, date]]
    ) -> bool:
        """
        Versión optimizada de es_dia_habil usando datos pre-cargados.

        Args:
            fecha: Fecha a verificar
            feriados_set: Set de fechas de feriados
            ferias: Lista de períodos de feria

        Returns:
            True si es día hábil
        """
        # Fin de semana (más rápido)
        if fecha.weekday() >= 5:
            return False

        # Feriado (O(1) con set)
        if fecha in feriados_set:
            return False

        # Feria judicial
        if self._fecha_en_feria(fecha, ferias):
            return False

        return True

    def calcular_fecha_vencimiento(
        self,
        fecha_inicio: date,
        dias_plazo: int
    ) -> date:
        """
        Calcula la fecha de vencimiento considerando días hábiles.

        Versión optimizada que pre-carga datos para evitar consultas por día.

        Args:
            fecha_inicio: Fecha de inicio del plazo
            dias_plazo: Cantidad de días hábiles

        Returns:
            Fecha de vencimiento
        """
        # Estimar fecha máxima (plazo * 2 para contemplar fines de semana)
        fecha_max_estimada = fecha_inicio + timedelta(days=dias_plazo * 2 + 30)

        # Pre-cargar todos los datos necesarios
        feriados_set = self._cargar_feriados_rango(fecha_inicio, fecha_max_estimada)
        ferias = self._cargar_ferias_rango(fecha_inicio, fecha_max_estimada)

        fecha_actual = fecha_inicio
        dias_transcurridos = 0

        while dias_transcurridos < dias_plazo:
            fecha_actual += timedelta(days=1)
            if self.es_dia_habil_optimizado(fecha_actual, feriados_set, ferias):
                dias_transcurridos += 1

        return fecha_actual

    def contar_dias_habiles(
        self,
        fecha_desde: date,
        fecha_hasta: date
    ) -> int:
        """
        Cuenta los días hábiles entre dos fechas.

        Versión optimizada que pre-carga datos.

        Args:
            fecha_desde: Fecha inicial
            fecha_hasta: Fecha final

        Returns:
            Cantidad de días hábiles
        """
        if fecha_hasta <= fecha_desde:
            return 0

        # Pre-cargar todos los datos necesarios
        feriados_set = self._cargar_feriados_rango(fecha_desde, fecha_hasta)
        ferias = self._cargar_ferias_rango(fecha_desde, fecha_hasta)

        dias = 0
        fecha_actual = fecha_desde

        while fecha_actual < fecha_hasta:
            fecha_actual += timedelta(days=1)
            if self.es_dia_habil_optimizado(fecha_actual, feriados_set, ferias):
                dias += 1

        return dias

    def calcular_dias_habiles_batch(
        self,
        calculos: List[Tuple[date, int]]
    ) -> List[date]:
        """
        Calcula múltiples fechas de vencimiento en batch.

        Optimizado para cuando se procesan muchos vencimientos.

        Args:
            calculos: Lista de tuplas (fecha_inicio, dias_plazo)

        Returns:
            Lista de fechas de vencimiento calculadas
        """
        if not calculos:
            return []

        # Encontrar rango total
        fecha_min = min(c[0] for c in calculos)
        fecha_max_estimada = max(c[0] for c in calculos) + timedelta(days=max(c[1] for c in calculos) * 2 + 30)

        # Pre-cargar datos una sola vez
        feriados_set = self._cargar_feriados_rango(fecha_min, fecha_max_estimada)
        ferias = self._cargar_ferias_rango(fecha_min, fecha_max_estimada)

        resultados = []
        for fecha_inicio, dias_plazo in calculos:
            fecha_actual = fecha_inicio
            dias_transcurridos = 0

            while dias_transcurridos < dias_plazo:
                fecha_actual += timedelta(days=1)
                if self.es_dia_habil_optimizado(fecha_actual, feriados_set, ferias):
                    dias_transcurridos += 1

            resultados.append(fecha_actual)

        return resultados

    # =========================================================================
    # GESTIÓN (CRUD)
    # =========================================================================

    def crear_feriado(
        self,
        fecha: date,
        nombre: str,
        tipo: str = 'nacional',
        es_trasladable: bool = False
    ) -> Dict[str, Any]:
        """
        Crea un nuevo feriado.

        Args:
            fecha: Fecha del feriado
            nombre: Nombre del feriado
            tipo: Tipo (nacional, judicial, provincial, feria_judicial)
            es_trasladable: Si es trasladable

        Returns:
            Feriado creado
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                INSERT INTO feriados (fecha, nombre, tipo, es_trasladable)
                VALUES (%s, %s, %s, %s)
            """, (fecha, nombre, tipo, es_trasladable))

            conn.commit()
            feriado_id = cursor.lastrowid

            # Invalidar caché
            año = fecha.year
            if año in self._cache_feriados:
                del self._cache_feriados[año]

            cursor.execute("""
                SELECT id, fecha, nombre, tipo, es_trasladable, año, activo
                FROM feriados WHERE id = %s
            """, (feriado_id,))

            feriado = cursor.fetchone()

            cursor.close()
            conn.close()

            return feriado

        except Exception as e:
            logger.error(f"Error creando feriado: {e}")
            raise

    def actualizar_feriado(
        self,
        feriado_id: int,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Actualiza un feriado existente.

        Args:
            feriado_id: ID del feriado
            **kwargs: Campos a actualizar (nombre, tipo, es_trasladable, activo)

        Returns:
            Feriado actualizado
        """
        campos_permitidos = {'nombre', 'tipo', 'es_trasladable', 'activo'}
        updates = {k: v for k, v in kwargs.items() if k in campos_permitidos}

        if not updates:
            return None

        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)

            # Obtener año para invalidar caché
            cursor.execute("SELECT año FROM feriados WHERE id = %s", (feriado_id,))
            result = cursor.fetchone()
            if not result:
                cursor.close()
                conn.close()
                return None

            año = result['año']

            # Construir query dinámico
            set_clause = ", ".join(f"{k} = %s" for k in updates.keys())
            values = list(updates.values()) + [feriado_id]

            cursor.execute(f"""
                UPDATE feriados SET {set_clause} WHERE id = %s
            """, values)

            conn.commit()

            # Invalidar caché
            if año in self._cache_feriados:
                del self._cache_feriados[año]

            cursor.execute("""
                SELECT id, fecha, nombre, tipo, es_trasladable, año, activo
                FROM feriados WHERE id = %s
            """, (feriado_id,))

            feriado = cursor.fetchone()

            cursor.close()
            conn.close()

            return feriado

        except Exception as e:
            logger.error(f"Error actualizando feriado {feriado_id}: {e}")
            raise

    def eliminar_feriado(self, feriado_id: int) -> bool:
        """
        Elimina (desactiva) un feriado.

        Args:
            feriado_id: ID del feriado

        Returns:
            True si se eliminó
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)

            # Obtener año para invalidar caché
            cursor.execute("SELECT año FROM feriados WHERE id = %s", (feriado_id,))
            result = cursor.fetchone()

            if not result:
                cursor.close()
                conn.close()
                return False

            año = result['año']

            # Soft delete
            cursor.execute("""
                UPDATE feriados SET activo = FALSE WHERE id = %s
            """, (feriado_id,))

            conn.commit()
            affected = cursor.rowcount

            cursor.close()
            conn.close()

            # Invalidar caché
            if año in self._cache_feriados:
                del self._cache_feriados[año]

            return affected > 0

        except Exception as e:
            logger.error(f"Error eliminando feriado {feriado_id}: {e}")
            return False

    def crear_feria_judicial(
        self,
        año: int,
        fecha_inicio: date,
        fecha_fin: date,
        nombre: str = "Feria Judicial de Verano"
    ) -> Dict[str, Any]:
        """
        Crea un nuevo período de feria judicial.

        Args:
            año: Año de la feria
            fecha_inicio: Fecha de inicio
            fecha_fin: Fecha de fin
            nombre: Nombre del período

        Returns:
            Feria creada
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                INSERT INTO feria_judicial (año, fecha_inicio, fecha_fin, nombre)
                VALUES (%s, %s, %s, %s)
            """, (año, fecha_inicio, fecha_fin, nombre))

            conn.commit()
            feria_id = cursor.lastrowid

            # Invalidar caché
            if año in self._cache_ferias:
                del self._cache_ferias[año]

            cursor.execute("""
                SELECT id, año, fecha_inicio, fecha_fin, nombre, activo
                FROM feria_judicial WHERE id = %s
            """, (feria_id,))

            feria = cursor.fetchone()

            cursor.close()
            conn.close()

            return feria

        except Exception as e:
            logger.error(f"Error creando feria judicial: {e}")
            raise

    def limpiar_cache(self):
        """Limpia los cachés de feriados y ferias."""
        self._cache_feriados.clear()
        self._cache_ferias.clear()
        logger.info("Caché de feriados limpiado")


# Singleton
_feriados_service: Optional[FeriadosService] = None


def get_feriados_service() -> FeriadosService:
    """Obtiene la instancia singleton del servicio de feriados."""
    global _feriados_service
    if _feriados_service is None:
        _feriados_service = FeriadosService()
    return _feriados_service
