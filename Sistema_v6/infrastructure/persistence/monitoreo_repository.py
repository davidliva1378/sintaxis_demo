"""
Repositorio MySQL para el sistema de monitoreo de expedientes.

CRUD completo para:
- Configuracion de monitoreo por usuario
- Expedientes monitoreados
- Cambios detectados
- Estadisticas
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from mysql.connector import Error as MySQLError

from infrastructure.persistence.database import get_pooled_connection

logger = logging.getLogger(__name__)


class MonitoreoRepository:
    """
    Repositorio para gestionar el monitoreo de expedientes en MySQL.

    Usa el pool de conexiones para mejor rendimiento.
    """

    # =========================================================================
    # CONFIGURACION DE MONITOREO
    # =========================================================================

    def obtener_configuracion(self, usuario_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene la configuracion de monitoreo de un usuario.

        Args:
            usuario_id: ID del usuario

        Returns:
            Configuracion o None si no existe
        """
        conn = None
        try:
            conn = get_pooled_connection()
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT
                    id, usuario_id, activo, frecuencia,
                    notificar_email, notificar_sistema,
                    hora_inicio, hora_fin, dias_semana,
                    ultima_ejecucion, proxima_ejecucion,
                    fecha_corte_dias, max_paginas_monitoreo,
                    tiempo_maximo_extraccion, detener_en_duplicado,
                    orden_extraccion, mostrar_navegador_monitoreo,
                    created_at, updated_at
                FROM monitoreo_configuracion
                WHERE usuario_id = %s
            """

            cursor.execute(query, (usuario_id,))
            result = cursor.fetchone()

            if result:
                result = self._format_config_result(result)

            cursor.close()
            return result

        except MySQLError as e:
            logger.error(f"Error obteniendo configuracion de monitoreo: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def crear_configuracion(
        self,
        usuario_id: int,
        activo: bool = True,
        frecuencia: str = '30min',
        notificar_email: bool = False,
        notificar_sistema: bool = True,
        hora_inicio: Optional[str] = '08:00',
        hora_fin: Optional[str] = '18:00',
        dias_semana: Optional[List[int]] = None,
        fecha_corte_dias: Optional[int] = 30,
        max_paginas_monitoreo: Optional[int] = 50,
        tiempo_maximo_extraccion: Optional[int] = 600,
        detener_en_duplicado: bool = True,
        orden_extraccion: str = 'fecha',
        mostrar_navegador_monitoreo: bool = False
    ) -> int:
        """
        Crea la configuracion de monitoreo para un usuario.

        Args:
            usuario_id: ID del usuario
            activo: Si el monitoreo esta activo
            frecuencia: Frecuencia de verificacion (default: 30min)
            notificar_email: Notificar por email
            notificar_sistema: Notificar en sistema
            hora_inicio: Hora inicio ventana (HH:MM, default: 08:00)
            hora_fin: Hora fin ventana (HH:MM, default: 18:00)
            dias_semana: Lista de dias [0-6] (default: lunes a viernes)
            fecha_corte_dias: Dias hacia atras para buscar actuaciones
            max_paginas_monitoreo: Maximo numero de paginas a procesar
            tiempo_maximo_extraccion: Tiempo maximo en segundos
            detener_en_duplicado: Detener al encontrar duplicado
            orden_extraccion: Orden de extraccion ('fecha' o 'caratula')

        Returns:
            ID de la configuracion creada
        """
        # Establecer valores por defecto si no se proporcionan
        if dias_semana is None:
            dias_semana = [1, 2, 3, 4, 5]  # Lunes a viernes por defecto

        conn = None
        try:
            conn = get_pooled_connection()
            cursor = conn.cursor()

            query = """
                INSERT INTO monitoreo_configuracion (
                    usuario_id, activo, frecuencia,
                    notificar_email, notificar_sistema,
                    hora_inicio, hora_fin, dias_semana,
                    fecha_corte_dias, max_paginas_monitoreo,
                    tiempo_maximo_extraccion, detener_en_duplicado,
                    orden_extraccion, mostrar_navegador_monitoreo
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            dias_json = json.dumps(dias_semana) if dias_semana else None

            cursor.execute(query, (
                usuario_id, activo, frecuencia,
                notificar_email, notificar_sistema,
                hora_inicio, hora_fin, dias_json,
                fecha_corte_dias, max_paginas_monitoreo,
                tiempo_maximo_extraccion, detener_en_duplicado,
                orden_extraccion, mostrar_navegador_monitoreo
            ))
            conn.commit()
            config_id = cursor.lastrowid

            logger.info(f"Configuracion de monitoreo creada para usuario {usuario_id}")
            cursor.close()
            return config_id

        except MySQLError as e:
            logger.error(f"Error creando configuracion: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def actualizar_configuracion(
        self,
        usuario_id: int,
        **kwargs
    ) -> bool:
        """
        Actualiza la configuracion de monitoreo.

        Args:
            usuario_id: ID del usuario
            **kwargs: Campos a actualizar

        Returns:
            True si se actualizo
        """
        conn = None
        try:
            conn = get_pooled_connection()
            cursor = conn.cursor()

            updates = []
            params = []

            for key, value in kwargs.items():
                if key == 'dias_semana' and value is not None:
                    updates.append(f"{key} = %s")
                    params.append(json.dumps(value))
                elif value is not None:
                    updates.append(f"{key} = %s")
                    params.append(value)

            if not updates:
                return False

            query = f"""
                UPDATE monitoreo_configuracion
                SET {', '.join(updates)}
                WHERE usuario_id = %s
            """
            params.append(usuario_id)

            cursor.execute(query, params)
            conn.commit()
            updated = cursor.rowcount > 0

            cursor.close()

            if updated:
                logger.info(f"Configuracion actualizada para usuario {usuario_id}")

            return updated

        except MySQLError as e:
            logger.error(f"Error actualizando configuracion: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def obtener_o_crear_configuracion(self, usuario_id: int) -> Dict[str, Any]:
        """
        Obtiene la configuracion existente o crea una por defecto.

        Args:
            usuario_id: ID del usuario

        Returns:
            Configuracion del usuario

        Raises:
            RuntimeError: Si no puede crear/obtener configuracion
        """
        config = self.obtener_configuracion(usuario_id)
        if not config:
            try:
                logger.info(f"Creando configuracion por defecto para usuario {usuario_id}")

                # Crear con valores por defecto completos
                config_id = self.crear_configuracion(
                    usuario_id=usuario_id,
                    hora_inicio='08:00',
                    hora_fin='18:00',
                    dias_semana=[1, 2, 3, 4, 5]
                )

                if not config_id:
                    raise RuntimeError(f"crear_configuracion() devolvio ID invalido: {config_id}")

                # Verificar que se creo correctamente
                config = self.obtener_configuracion(usuario_id)
                if not config:
                    raise RuntimeError(
                        f"No se pudo crear configuracion para usuario {usuario_id}. "
                        f"Verificar permisos de BD y constraints."
                    )

                logger.info(f"Configuracion creada exitosamente: usuario_id={usuario_id}, config_id={config_id}")

            except MySQLError as e:
                logger.error(f"Error MySQL creando configuracion: {e}", exc_info=True)
                raise RuntimeError(f"Error en base de datos: {str(e)}")
            except Exception as e:
                logger.error(f"Error inesperado creando configuracion: {e}", exc_info=True)
                raise RuntimeError(f"Error creando configuracion: {str(e)}")

        return config

    # =========================================================================
    # EXPEDIENTES MONITOREADOS
    # =========================================================================

    def agregar_expediente(
        self,
        usuario_id: int,
        expediente_numero: str,
        expediente_caratula: Optional[str] = None,
        expediente_dependencia: Optional[str] = None,
        prioridad: str = 'media',
        notas: Optional[str] = None
    ) -> int:
        """
        Agrega un expediente al monitoreo.

        Args:
            usuario_id: ID del usuario
            expediente_numero: Numero del expediente
            expediente_caratula: Caratula
            expediente_dependencia: Dependencia
            prioridad: 'baja', 'media', 'alta'
            notas: Notas del usuario

        Returns:
            ID del registro creado
        """
        conn = None
        try:
            conn = get_pooled_connection()
            cursor = conn.cursor()

            query = """
                INSERT INTO expedientes_monitoreados (
                    usuario_id, expediente_numero, expediente_caratula,
                    expediente_dependencia, prioridad, notas
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """

            cursor.execute(query, (
                usuario_id, expediente_numero, expediente_caratula,
                expediente_dependencia, prioridad, notas
            ))
            conn.commit()
            exp_id = cursor.lastrowid

            logger.info(f"Expediente {expediente_numero} agregado al monitoreo")
            cursor.close()
            return exp_id

        except MySQLError as e:
            if e.errno == 1062:  # Duplicate entry
                logger.warning(f"Expediente {expediente_numero} ya esta en monitoreo")
                raise ValueError(f"El expediente {expediente_numero} ya esta siendo monitoreado")
            logger.error(f"Error agregando expediente: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def obtener_expedientes(
        self,
        usuario_id: int,
        solo_activos: bool = False,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Obtiene los expedientes monitoreados de un usuario.

        Args:
            usuario_id: ID del usuario
            solo_activos: Solo retornar activos
            limit: Limite de resultados
            offset: Offset para paginacion

        Returns:
            Lista de expedientes
        """
        conn = None
        try:
            conn = get_pooled_connection()
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT
                    id, usuario_id, expediente_numero, expediente_caratula,
                    expediente_dependencia, activo, ultima_verificacion,
                    ultima_actuacion_fecha, ultima_actuacion_id,
                    total_cambios_detectados, notas, prioridad,
                    created_at, updated_at
                FROM expedientes_monitoreados
                WHERE 1=1
            """
            params = []

            if usuario_id is not None:
                query += " AND usuario_id = %s"
                params.append(usuario_id)

            if solo_activos:
                query += " AND activo = TRUE"

            query += " ORDER BY prioridad DESC, created_at DESC"

            if limit:
                query += f" LIMIT {limit} OFFSET {offset}"

            cursor.execute(query, params)
            results = cursor.fetchall()

            for row in results:
                self._format_expediente_result(row)

            cursor.close()
            return results

        except MySQLError as e:
            logger.error(f"Error obteniendo expedientes: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def obtener_expediente(
        self,
        usuario_id: int,
        expediente_numero: str
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene un expediente monitoreado especifico.

        Args:
            usuario_id: ID del usuario
            expediente_numero: Numero del expediente

        Returns:
            Expediente o None
        """
        conn = None
        try:
            conn = get_pooled_connection()
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT
                    id, usuario_id, expediente_numero, expediente_caratula,
                    expediente_dependencia, activo, ultima_verificacion,
                    ultima_actuacion_fecha, ultima_actuacion_id,
                    total_cambios_detectados, notas, prioridad,
                    created_at, updated_at
                FROM expedientes_monitoreados
                WHERE usuario_id = %s AND expediente_numero = %s
            """

            cursor.execute(query, (usuario_id, expediente_numero))
            result = cursor.fetchone()

            if result:
                self._format_expediente_result(result)

            cursor.close()
            return result

        except MySQLError as e:
            logger.error(f"Error obteniendo expediente: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def obtener_expediente_por_id(self, expediente_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene un expediente monitoreado por su ID.

        Args:
            expediente_id: ID del registro

        Returns:
            Expediente o None
        """
        conn = None
        try:
            conn = get_pooled_connection()
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT
                    id, usuario_id, expediente_numero, expediente_caratula,
                    expediente_dependencia, activo, ultima_verificacion,
                    ultima_actuacion_fecha, ultima_actuacion_id,
                    total_cambios_detectados, notas, prioridad,
                    created_at, updated_at
                FROM expedientes_monitoreados
                WHERE id = %s
            """

            cursor.execute(query, (expediente_id,))
            result = cursor.fetchone()

            if result:
                self._format_expediente_result(result)

            cursor.close()
            return result

        except MySQLError as e:
            logger.error(f"Error obteniendo expediente por ID: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def actualizar_expediente(
        self,
        expediente_id: int,
        **kwargs
    ) -> bool:
        """
        Actualiza un expediente monitoreado.

        Args:
            expediente_id: ID del registro
            **kwargs: Campos a actualizar

        Returns:
            True si se actualizo
        """
        conn = None
        try:
            conn = get_pooled_connection()
            cursor = conn.cursor()

            updates = []
            params = []

            for key, value in kwargs.items():
                if value is not None:
                    updates.append(f"{key} = %s")
                    params.append(value)

            if not updates:
                return False

            query = f"""
                UPDATE expedientes_monitoreados
                SET {', '.join(updates)}
                WHERE id = %s
            """
            params.append(expediente_id)

            cursor.execute(query, params)
            conn.commit()
            updated = cursor.rowcount > 0

            cursor.close()
            return updated

        except MySQLError as e:
            logger.error(f"Error actualizando expediente: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def eliminar_expediente(self, usuario_id: int, expediente_numero: str) -> bool:
        """
        Elimina un expediente del monitoreo.

        Args:
            usuario_id: ID del usuario
            expediente_numero: Numero del expediente

        Returns:
            True si se elimino
        """
        conn = None
        try:
            conn = get_pooled_connection()
            cursor = conn.cursor()

            query = """
                DELETE FROM expedientes_monitoreados
                WHERE usuario_id = %s AND expediente_numero = %s
            """

            cursor.execute(query, (usuario_id, expediente_numero))
            conn.commit()
            deleted = cursor.rowcount > 0

            cursor.close()

            if deleted:
                logger.info(f"Expediente {expediente_numero} eliminado del monitoreo")

            return deleted

        except MySQLError as e:
            logger.error(f"Error eliminando expediente: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def contar_expedientes(self, usuario_id: int, solo_activos: bool = False) -> int:
        """
        Cuenta los expedientes monitoreados de un usuario.

        Args:
            usuario_id: ID del usuario
            solo_activos: Solo contar activos

        Returns:
            Total de expedientes
        """
        conn = None
        try:
            conn = get_pooled_connection()
            cursor = conn.cursor()

            query = "SELECT COUNT(*) FROM expedientes_monitoreados WHERE 1=1"
            params = []

            if usuario_id is not None:
                query += " AND usuario_id = %s"
                params.append(usuario_id)

            if solo_activos:
                query += " AND activo = TRUE"

            cursor.execute(query, params)
            count = cursor.fetchone()[0]

            cursor.close()
            return count

        except MySQLError as e:
            logger.error(f"Error contando expedientes: {e}")
            raise
        finally:
            if conn:
                conn.close()

    # =========================================================================
    # CAMBIOS DETECTADOS
    # =========================================================================

    def registrar_cambio(
        self,
        expediente_monitoreado_id: int,
        expediente_numero: str,
        tipo_cambio: str,
        descripcion: str,
        expediente_caratula: Optional[str] = None,
        detalles: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Registra un cambio detectado.

        Args:
            expediente_monitoreado_id: ID del expediente monitoreado
            expediente_numero: Numero del expediente
            tipo_cambio: Tipo de cambio
            descripcion: Descripcion del cambio
            expediente_caratula: Caratula (desnormalizado)
            detalles: Detalles adicionales en JSON

        Returns:
            ID del cambio registrado
        """
        conn = None
        try:
            conn = get_pooled_connection()
            cursor = conn.cursor()

            query = """
                INSERT INTO cambios_detectados (
                    expediente_monitoreado_id, expediente_numero,
                    expediente_caratula, tipo_cambio, descripcion, detalles
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """

            detalles_json = json.dumps(detalles) if detalles else None

            cursor.execute(query, (
                expediente_monitoreado_id, expediente_numero,
                expediente_caratula, tipo_cambio, descripcion, detalles_json
            ))
            conn.commit()
            cambio_id = cursor.lastrowid

            # Incrementar contador en expediente monitoreado
            cursor.execute("""
                UPDATE expedientes_monitoreados
                SET total_cambios_detectados = total_cambios_detectados + 1
                WHERE id = %s
            """, (expediente_monitoreado_id,))
            conn.commit()

            logger.info(f"Cambio {tipo_cambio} registrado para {expediente_numero}")
            cursor.close()
            return cambio_id

        except MySQLError as e:
            logger.error(f"Error registrando cambio: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def obtener_cambios(
        self,
        usuario_id: int,
        solo_no_leidos: bool = False,
        tipo_cambio: Optional[str] = None,
        expediente_numero: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Obtiene los cambios detectados de un usuario.

        Args:
            usuario_id: ID del usuario
            solo_no_leidos: Solo cambios sin leer
            tipo_cambio: Filtrar por tipo
            expediente_numero: Filtrar por expediente
            limit: Limite de resultados
            offset: Offset para paginacion

        Returns:
            Lista de cambios
        """
        conn = None
        try:
            conn = get_pooled_connection()
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT
                    c.id, c.expediente_monitoreado_id, c.expediente_numero,
                    c.expediente_caratula, c.tipo_cambio, c.descripcion,
                    c.detalles, c.notificado, c.leido,
                    c.fecha_deteccion, c.created_at
                FROM cambios_detectados c
                INNER JOIN expedientes_monitoreados em
                    ON c.expediente_monitoreado_id = em.id
                WHERE em.usuario_id = %s
            """
            params = [usuario_id]

            if solo_no_leidos:
                query += " AND c.leido = FALSE"

            if tipo_cambio:
                query += " AND c.tipo_cambio = %s"
                params.append(tipo_cambio)

            if expediente_numero:
                query += " AND c.expediente_numero = %s"
                params.append(expediente_numero)

            query += f" ORDER BY c.fecha_deteccion DESC LIMIT {limit} OFFSET {offset}"

            cursor.execute(query, params)
            results = cursor.fetchall()

            for row in results:
                self._format_cambio_result(row)

            cursor.close()
            return results

        except MySQLError as e:
            logger.error(f"Error obteniendo cambios: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def marcar_cambio_leido(self, cambio_id: int) -> bool:
        """
        Marca un cambio como leido.

        Args:
            cambio_id: ID del cambio

        Returns:
            True si se actualizo
        """
        conn = None
        try:
            conn = get_pooled_connection()
            cursor = conn.cursor()

            cursor.execute(
                "UPDATE cambios_detectados SET leido = TRUE WHERE id = %s",
                (cambio_id,)
            )
            conn.commit()
            updated = cursor.rowcount > 0

            cursor.close()
            return updated

        except MySQLError as e:
            logger.error(f"Error marcando cambio leido: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def marcar_todos_leidos(self, usuario_id: int) -> int:
        """
        Marca todos los cambios de un usuario como leidos.

        Args:
            usuario_id: ID del usuario

        Returns:
            Cantidad de cambios marcados
        """
        conn = None
        try:
            conn = get_pooled_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE cambios_detectados c
                INNER JOIN expedientes_monitoreados em
                    ON c.expediente_monitoreado_id = em.id
                SET c.leido = TRUE
                WHERE em.usuario_id = %s AND c.leido = FALSE
            """, (usuario_id,))
            conn.commit()
            count = cursor.rowcount

            cursor.close()

            if count > 0:
                logger.info(f"{count} cambios marcados como leidos")

            return count

        except MySQLError as e:
            logger.error(f"Error marcando todos leidos: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def contar_cambios_no_leidos(self, usuario_id: int) -> int:
        """
        Cuenta los cambios no leidos de un usuario.

        Args:
            usuario_id: ID del usuario

        Returns:
            Total de cambios no leidos
        """
        conn = None
        try:
            conn = get_pooled_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*) FROM cambios_detectados c
                INNER JOIN expedientes_monitoreados em
                    ON c.expediente_monitoreado_id = em.id
                WHERE em.usuario_id = %s AND c.leido = FALSE
            """, (usuario_id,))
            count = cursor.fetchone()[0]

            cursor.close()
            return count

        except MySQLError as e:
            logger.error(f"Error contando no leidos: {e}")
            raise
        finally:
            if conn:
                conn.close()

    # =========================================================================
    # ESTADISTICAS
    # =========================================================================

    def obtener_estadisticas(self, usuario_id: int) -> Dict[str, Any]:
        """
        Obtiene estadisticas de monitoreo de un usuario.

        Args:
            usuario_id: ID del usuario

        Returns:
            Diccionario con estadisticas
        """
        conn = None
        try:
            conn = get_pooled_connection()
            cursor = conn.cursor(dictionary=True)

            # Usar la vista de estadisticas
            cursor.execute("""
                SELECT * FROM monitoreo_estadisticas
                WHERE usuario_id = %s
            """, (usuario_id,))

            result = cursor.fetchone()

            if not result:
                # Usuario sin expedientes monitoreados
                config = self.obtener_configuracion(usuario_id)
                result = {
                    'total_expedientes': 0,
                    'expedientes_activos': 0,
                    'expedientes_pausados': 0,
                    'cambios_hoy': 0,
                    'cambios_semana': 0,
                    'cambios_mes': 0,
                    'cambios_sin_leer': 0,
                    'ultima_ejecucion': config.get('ultima_ejecucion') if config else None,
                    'proxima_ejecucion': config.get('proxima_ejecucion') if config else None
                }
            else:
                # Formatear fechas
                if result.get('ultima_ejecucion'):
                    result['ultima_ejecucion'] = result['ultima_ejecucion'].isoformat()
                if result.get('proxima_ejecucion'):
                    result['proxima_ejecucion'] = result['proxima_ejecucion'].isoformat()

            cursor.close()
            return result

        except MySQLError as e:
            logger.error(f"Error obteniendo estadisticas: {e}")
            raise
        finally:
            if conn:
                conn.close()

    # =========================================================================
    # UTILIDADES INTERNAS
    # =========================================================================

    def _format_config_result(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Formatea resultado de configuracion."""
        if row.get('hora_inicio'):
            row['hora_inicio'] = str(row['hora_inicio'])
        if row.get('hora_fin'):
            row['hora_fin'] = str(row['hora_fin'])
        if row.get('dias_semana'):
            if isinstance(row['dias_semana'], str):
                row['dias_semana'] = json.loads(row['dias_semana'])
        if row.get('ultima_ejecucion'):
            row['ultima_ejecucion'] = row['ultima_ejecucion'].isoformat()
        if row.get('proxima_ejecucion'):
            row['proxima_ejecucion'] = row['proxima_ejecucion'].isoformat()
        if row.get('created_at'):
            row['created_at'] = row['created_at'].isoformat()
        if row.get('updated_at'):
            row['updated_at'] = row['updated_at'].isoformat()
        return row

    def _format_expediente_result(self, row: Dict[str, Any]) -> None:
        """Formatea resultado de expediente monitoreado."""
        for key in ['ultima_verificacion', 'ultima_actuacion_fecha', 'created_at', 'updated_at']:
            if row.get(key):
                row[key] = row[key].isoformat()

    def _format_cambio_result(self, row: Dict[str, Any]) -> None:
        """Formatea resultado de cambio detectado."""
        if row.get('detalles'):
            if isinstance(row['detalles'], str):
                row['detalles'] = json.loads(row['detalles'])
        for key in ['fecha_deteccion', 'created_at']:
            if row.get(key):
                row[key] = row[key].isoformat()
