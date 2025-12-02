"""
Repositorio MySQL para el sistema de alertas y notificaciones.

CRUD completo para:
- Alertas de vencimientos
- Configuración de alertas por usuario
- Notificaciones in-app
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from mysql.connector import Error as MySQLError

from infrastructure.persistence.database import get_pooled_connection

logger = logging.getLogger(__name__)


class AlertasRepository:
    """
    Repositorio para gestionar alertas y notificaciones en MySQL.

    Usa el pool de conexiones para mejor rendimiento.
    """

    # =========================================================================
    # ALERTAS DE VENCIMIENTOS
    # =========================================================================

    def crear_alerta(
        self,
        vencimiento_id: int,
        tipo_alerta: str,
        canal: str = "in_app",
        fecha_programada: Optional[datetime] = None,
        mensaje: Optional[str] = None
    ) -> int:
        """
        Crea una alerta para un vencimiento.

        Args:
            vencimiento_id: ID del vencimiento
            tipo_alerta: Tipo de alerta (3_dias, 1_dia, hoy, vencido)
            canal: Canal de envío (email, push, webhook, in_app)
            fecha_programada: Fecha/hora de envío programado
            mensaje: Mensaje personalizado

        Returns:
            ID de la alerta creada
        """
        if fecha_programada is None:
            fecha_programada = datetime.now()

        conn = None
        try:
            conn = get_pooled_connection()
            cursor = conn.cursor()

            query = """
                INSERT INTO alertas_vencimientos (
                    vencimiento_id, tipo_alerta, canal,
                    fecha_programada, mensaje
                ) VALUES (%s, %s, %s, %s, %s)
            """

            cursor.execute(query, (
                vencimiento_id, tipo_alerta, canal,
                fecha_programada, mensaje
            ))
            conn.commit()
            alerta_id = cursor.lastrowid

            logger.debug(f"Alerta {alerta_id} creada para vencimiento {vencimiento_id}")
            cursor.close()
            return alerta_id

        except MySQLError as e:
            logger.error(f"Error creando alerta: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def existe_alerta(self, vencimiento_id: int, tipo_alerta: str) -> bool:
        """
        Verifica si ya existe una alerta de este tipo para el vencimiento.

        Args:
            vencimiento_id: ID del vencimiento
            tipo_alerta: Tipo de alerta

        Returns:
            True si existe, False en caso contrario
        """
        conn = None
        try:
            conn = get_pooled_connection()
            cursor = conn.cursor()

            query = """
                SELECT COUNT(*) FROM alertas_vencimientos
                WHERE vencimiento_id = %s AND tipo_alerta = %s
            """

            cursor.execute(query, (vencimiento_id, tipo_alerta))
            count = cursor.fetchone()[0]
            cursor.close()
            return count > 0

        except MySQLError as e:
            logger.error(f"Error verificando alerta: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def marcar_alerta_enviada(
        self,
        alerta_id: int,
        error: Optional[str] = None
    ) -> bool:
        """
        Marca una alerta como enviada.

        Args:
            alerta_id: ID de la alerta
            error: Error si falló el envío

        Returns:
            True si se actualizó correctamente
        """
        conn = None
        try:
            conn = get_pooled_connection()
            cursor = conn.cursor()

            if error:
                query = """
                    UPDATE alertas_vencimientos
                    SET intentos = intentos + 1, error_envio = %s
                    WHERE id = %s
                """
                cursor.execute(query, (error, alerta_id))
            else:
                query = """
                    UPDATE alertas_vencimientos
                    SET enviada = TRUE, fecha_envio = NOW()
                    WHERE id = %s
                """
                cursor.execute(query, (alerta_id,))

            conn.commit()
            cursor.close()
            return True

        except MySQLError as e:
            logger.error(f"Error actualizando alerta: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def obtener_alertas_pendientes(self, limite: int = 100) -> List[Dict[str, Any]]:
        """
        Obtiene alertas pendientes de envío.

        Args:
            limite: Máximo de alertas a retornar

        Returns:
            Lista de alertas pendientes
        """
        conn = None
        try:
            conn = get_pooled_connection()
            cursor = conn.cursor(dictionary=True)

            # Usar la vista v_alertas_pendientes si existe
            query = """
                SELECT * FROM v_alertas_pendientes
                LIMIT %s
            """

            cursor.execute(query, (limite,))
            results = cursor.fetchall()
            cursor.close()
            return results

        except MySQLError as e:
            logger.error(f"Error obteniendo alertas pendientes: {e}")
            return []
        finally:
            if conn:
                conn.close()

    # =========================================================================
    # NOTIFICACIONES IN-APP
    # =========================================================================

    def crear_notificacion(
        self,
        usuario_id: int,
        tipo: str,
        titulo: str,
        mensaje: str,
        prioridad: str = "normal",
        url_accion: Optional[str] = None,
        datos_extra: Optional[dict] = None,
        expira_en: Optional[datetime] = None
    ) -> int:
        """
        Crea una notificación in-app.

        Args:
            usuario_id: ID del usuario destinatario
            tipo: Tipo (vencimiento, sistema, monitoreo, extraccion, error)
            titulo: Título de la notificación
            mensaje: Mensaje descriptivo
            prioridad: Prioridad (baja, normal, alta, urgente)
            url_accion: URL para redirigir al hacer clic
            datos_extra: Datos adicionales en JSON
            expira_en: Fecha de expiración

        Returns:
            ID de la notificación creada
        """
        conn = None
        try:
            conn = get_pooled_connection()
            cursor = conn.cursor()

            query = """
                INSERT INTO notificaciones (
                    usuario_id, tipo, titulo, mensaje,
                    prioridad, url_accion, datos_extra, expira_en
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            datos_json = json.dumps(datos_extra) if datos_extra else None

            cursor.execute(query, (
                usuario_id, tipo, titulo, mensaje,
                prioridad, url_accion, datos_json, expira_en
            ))
            conn.commit()
            notif_id = cursor.lastrowid

            logger.debug(f"Notificación {notif_id} creada para usuario {usuario_id}")
            cursor.close()
            return notif_id

        except MySQLError as e:
            logger.error(f"Error creando notificación: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def listar_notificaciones(
        self,
        usuario_id: int,
        solo_no_leidas: bool = False,
        tipo: Optional[str] = None,
        limite: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Lista notificaciones de un usuario.

        Args:
            usuario_id: ID del usuario
            solo_no_leidas: Si True, solo retorna no leídas
            tipo: Filtrar por tipo
            limite: Máximo a retornar
            offset: Offset para paginación

        Returns:
            Lista de notificaciones
        """
        conn = None
        try:
            conn = get_pooled_connection()
            cursor = conn.cursor(dictionary=True)

            conditions = ["usuario_id = %s", "(expira_en IS NULL OR expira_en > NOW())"]
            params = [usuario_id]

            if solo_no_leidas:
                conditions.append("leida = FALSE")

            if tipo:
                conditions.append("tipo = %s")
                params.append(tipo)

            where_clause = " AND ".join(conditions)
            params.extend([limite, offset])

            query = f"""
                SELECT
                    id, usuario_id, tipo, titulo, mensaje,
                    datos_extra, leida, fecha_lectura,
                    url_accion, prioridad, expira_en, creado_en
                FROM notificaciones
                WHERE {where_clause}
                ORDER BY creado_en DESC
                LIMIT %s OFFSET %s
            """

            cursor.execute(query, params)
            results = cursor.fetchall()

            # Parsear JSON
            for r in results:
                if r.get('datos_extra'):
                    try:
                        r['datos_extra'] = json.loads(r['datos_extra'])
                    except json.JSONDecodeError:
                        pass

            cursor.close()
            return results

        except MySQLError as e:
            logger.error(f"Error listando notificaciones: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def contar_notificaciones_no_leidas(self, usuario_id: int) -> int:
        """
        Cuenta notificaciones no leídas.

        Args:
            usuario_id: ID del usuario

        Returns:
            Número de notificaciones no leídas
        """
        conn = None
        try:
            conn = get_pooled_connection()
            cursor = conn.cursor()

            query = """
                SELECT COUNT(*) FROM notificaciones
                WHERE usuario_id = %s
                  AND leida = FALSE
                  AND (expira_en IS NULL OR expira_en > NOW())
            """

            cursor.execute(query, (usuario_id,))
            count = cursor.fetchone()[0]
            cursor.close()
            return count

        except MySQLError as e:
            logger.error(f"Error contando notificaciones: {e}")
            return 0
        finally:
            if conn:
                conn.close()

    def marcar_notificacion_leida(
        self,
        notificacion_id: int,
        usuario_id: int
    ) -> bool:
        """
        Marca una notificación como leída.

        Args:
            notificacion_id: ID de la notificación
            usuario_id: ID del usuario (para verificación)

        Returns:
            True si se actualizó correctamente
        """
        conn = None
        try:
            conn = get_pooled_connection()
            cursor = conn.cursor()

            query = """
                UPDATE notificaciones
                SET leida = TRUE, fecha_lectura = NOW()
                WHERE id = %s AND usuario_id = %s
            """

            cursor.execute(query, (notificacion_id, usuario_id))
            conn.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected > 0

        except MySQLError as e:
            logger.error(f"Error marcando notificación como leída: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def marcar_todas_leidas(self, usuario_id: int) -> int:
        """
        Marca todas las notificaciones como leídas.

        Args:
            usuario_id: ID del usuario

        Returns:
            Número de notificaciones marcadas
        """
        conn = None
        try:
            conn = get_pooled_connection()
            cursor = conn.cursor()

            query = """
                UPDATE notificaciones
                SET leida = TRUE, fecha_lectura = NOW()
                WHERE usuario_id = %s AND leida = FALSE
            """

            cursor.execute(query, (usuario_id,))
            conn.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected

        except MySQLError as e:
            logger.error(f"Error marcando todas como leídas: {e}")
            return 0
        finally:
            if conn:
                conn.close()

    def obtener_estadisticas_notificaciones(self, usuario_id: int) -> Dict[str, Any]:
        """
        Obtiene estadísticas de notificaciones.

        Args:
            usuario_id: ID del usuario

        Returns:
            Diccionario con estadísticas
        """
        conn = None
        try:
            conn = get_pooled_connection()
            cursor = conn.cursor(dictionary=True)

            # Intentar usar la vista
            query = """
                SELECT * FROM v_estadisticas_notificaciones
                WHERE usuario_id = %s
            """

            cursor.execute(query, (usuario_id,))
            result = cursor.fetchone()
            cursor.close()

            if result:
                return result
            return {
                "usuario_id": usuario_id,
                "total": 0,
                "no_leidas": 0,
                "vencimientos": 0,
                "urgentes_no_leidas": 0
            }

        except MySQLError as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {
                "usuario_id": usuario_id,
                "total": 0,
                "no_leidas": 0,
                "vencimientos": 0,
                "urgentes_no_leidas": 0
            }
        finally:
            if conn:
                conn.close()

    def eliminar_expiradas(self) -> int:
        """
        Elimina notificaciones expiradas.

        Returns:
            Número de notificaciones eliminadas
        """
        conn = None
        try:
            conn = get_pooled_connection()
            cursor = conn.cursor()

            query = """
                DELETE FROM notificaciones
                WHERE expira_en IS NOT NULL AND expira_en < NOW()
            """

            cursor.execute(query)
            conn.commit()
            deleted = cursor.rowcount
            cursor.close()

            if deleted > 0:
                logger.info(f"Eliminadas {deleted} notificaciones expiradas")

            return deleted

        except MySQLError as e:
            logger.error(f"Error eliminando expiradas: {e}")
            return 0
        finally:
            if conn:
                conn.close()

    # =========================================================================
    # CONFIGURACION DE ALERTAS
    # =========================================================================

    def obtener_configuracion_usuario(self, usuario_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene la configuración de alertas de un usuario.

        Args:
            usuario_id: ID del usuario

        Returns:
            Configuración o None si no existe
        """
        conn = None
        try:
            conn = get_pooled_connection()
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT
                    id, usuario_id, alertas_email, alertas_push,
                    alertas_in_app, dias_anticipacion, hora_envio,
                    expedientes_excluidos, activo, creado_en, actualizado_en
                FROM configuracion_alertas
                WHERE usuario_id = %s
            """

            cursor.execute(query, (usuario_id,))
            result = cursor.fetchone()

            if result:
                # Parsear JSON
                if result.get('dias_anticipacion'):
                    try:
                        result['dias_anticipacion'] = json.loads(result['dias_anticipacion'])
                    except json.JSONDecodeError:
                        result['dias_anticipacion'] = [3, 1, 0]

                if result.get('expedientes_excluidos'):
                    try:
                        result['expedientes_excluidos'] = json.loads(result['expedientes_excluidos'])
                    except json.JSONDecodeError:
                        result['expedientes_excluidos'] = []

                # Convertir hora a string
                if result.get('hora_envio'):
                    result['hora_envio'] = str(result['hora_envio'])

            cursor.close()
            return result

        except MySQLError as e:
            logger.error(f"Error obteniendo configuración de alertas: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def crear_configuracion_usuario(
        self,
        usuario_id: int,
        alertas_email: bool = True,
        alertas_push: bool = True,
        alertas_in_app: bool = True,
        dias_anticipacion: Optional[List[int]] = None,
        hora_envio: str = "09:00:00"
    ) -> Dict[str, Any]:
        """
        Crea configuración de alertas para un usuario.

        Args:
            usuario_id: ID del usuario
            alertas_email: Habilitar alertas por email
            alertas_push: Habilitar alertas push
            alertas_in_app: Habilitar notificaciones in-app
            dias_anticipacion: Días antes para alertar [3, 1, 0]
            hora_envio: Hora preferida de envío

        Returns:
            Configuración creada
        """
        if dias_anticipacion is None:
            dias_anticipacion = [3, 1, 0]

        conn = None
        try:
            conn = get_pooled_connection()
            cursor = conn.cursor()

            query = """
                INSERT INTO configuracion_alertas (
                    usuario_id, alertas_email, alertas_push,
                    alertas_in_app, dias_anticipacion, hora_envio,
                    expedientes_excluidos
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE actualizado_en = NOW()
            """

            cursor.execute(query, (
                usuario_id, alertas_email, alertas_push,
                alertas_in_app, json.dumps(dias_anticipacion),
                hora_envio, json.dumps([])
            ))
            conn.commit()
            cursor.close()

            # Retornar la configuración creada
            return self.obtener_configuracion_usuario(usuario_id)

        except MySQLError as e:
            logger.error(f"Error creando configuración de alertas: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def actualizar_configuracion_usuario(
        self,
        usuario_id: int,
        alertas_email: Optional[bool] = None,
        alertas_push: Optional[bool] = None,
        alertas_in_app: Optional[bool] = None,
        dias_anticipacion: Optional[List[int]] = None,
        hora_envio: Optional[str] = None,
        expedientes_excluidos: Optional[List[str]] = None,
        activo: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Actualiza configuración de alertas.

        Args:
            usuario_id: ID del usuario
            alertas_email: Habilitar alertas por email
            alertas_push: Habilitar alertas push
            alertas_in_app: Habilitar notificaciones in-app
            dias_anticipacion: Días antes para alertar
            hora_envio: Hora preferida de envío
            expedientes_excluidos: Lista de expedientes a excluir
            activo: Si las alertas están activas

        Returns:
            Configuración actualizada
        """
        conn = None
        try:
            conn = get_pooled_connection()
            cursor = conn.cursor()

            # Construir query dinámico
            updates = []
            params = []

            if alertas_email is not None:
                updates.append("alertas_email = %s")
                params.append(alertas_email)

            if alertas_push is not None:
                updates.append("alertas_push = %s")
                params.append(alertas_push)

            if alertas_in_app is not None:
                updates.append("alertas_in_app = %s")
                params.append(alertas_in_app)

            if dias_anticipacion is not None:
                updates.append("dias_anticipacion = %s")
                params.append(json.dumps(dias_anticipacion))

            if hora_envio is not None:
                updates.append("hora_envio = %s")
                params.append(hora_envio)

            if expedientes_excluidos is not None:
                updates.append("expedientes_excluidos = %s")
                params.append(json.dumps(expedientes_excluidos))

            if activo is not None:
                updates.append("activo = %s")
                params.append(activo)

            if not updates:
                return self.obtener_configuracion_usuario(usuario_id)

            params.append(usuario_id)

            query = f"""
                UPDATE configuracion_alertas
                SET {', '.join(updates)}
                WHERE usuario_id = %s
            """

            cursor.execute(query, params)
            conn.commit()
            cursor.close()

            return self.obtener_configuracion_usuario(usuario_id)

        except MySQLError as e:
            logger.error(f"Error actualizando configuración de alertas: {e}")
            raise
        finally:
            if conn:
                conn.close()
