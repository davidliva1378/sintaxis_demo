from __future__ import annotations

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import mysql.connector
from mysql.connector import Error as MySQLError

from application.ports import IActuacionRepository
from core.domain.entities import Actuacion, ActuacionesArchivo
from application.services.extraccion_texto_service import ExtraccionTextoService

logger = logging.getLogger(__name__)

class MysqlActuacionRepository(IActuacionRepository):
    """Repositorio de actuaciones usando MySQL.
    
    Implementa IActuacionRepository y provee métodos adicionales
    para el ProcesadorActuacionesService.
    """

    def __init__(self, db_config: dict, workspaces_path: Path | None = None):
        self.db_config = db_config
        self._workspaces_base = workspaces_path
        # Asegurar que el puerto sea int
        if 'port' in self.db_config:
            self.db_config['port'] = int(self.db_config['port'])

    def _get_connection(self):
        try:
            return mysql.connector.connect(**self.db_config)
        except MySQLError as e:
            logger.error(f"Error conectando a MySQL: {e}")
            raise

    # =========================================================================
    # Implementación IActuacionRepository (Lectura para API)
    # =========================================================================

    async def guardar_archivo(self, numero_expediente: str, archivo: ActuacionesArchivo) -> None:
        """Guarda un archivo completo (No implementado para MySQL, se usa guardado individual)."""
        logger.warning("guardar_archivo no implementado para MySQL (usar guardar_clasificacion)")
        pass

    async def obtener_archivo(self, numero_expediente: str) -> ActuacionesArchivo | None:
        """Obtiene el archivo de actuaciones (reconstruido desde DB)."""
        actuaciones = await self.obtener_actuaciones(numero_expediente)
        if not actuaciones:
            return None
        
        # Reconstruir estructura (encabezado dummy por ahora)
        return ActuacionesArchivo(
            encabezado={"Numero": numero_expediente},
            actuaciones=actuaciones
        )

    async def obtener_actuaciones(self, numero_expediente: str) -> Tuple[Actuacion, ...] | None:
        """Obtiene las actuaciones de un expediente desde MySQL."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)

            # 1. Intentar obtener ID del expediente primero
            # La columna puede ser numero_normalizado o numero_original
            cursor.execute("SELECT id FROM expedientes WHERE numero_normalizado = %s OR numero_original = %s", (numero_expediente, numero_expediente))
            exp_row = cursor.fetchone()
            
            rows = []
            if exp_row:
                # Si tenemos ID, buscar por expediente_id (más seguro)
                expediente_id = exp_row['id']
                query = """
                    SELECT * FROM actuaciones 
                    WHERE expediente_id = %s 
                      AND indice IS NOT NULL
                    ORDER BY indice ASC
                """
                cursor.execute(query, (expediente_id,))
                rows = cursor.fetchall()
            else:
                # Fallback: buscar por numero string (legacy/mismatch)
                query = """
                    SELECT * FROM actuaciones 
                    WHERE expediente_numero = %s 
                      AND indice IS NOT NULL
                    ORDER BY indice ASC
                """
                cursor.execute(query, (numero_expediente,))
                rows = cursor.fetchall()
            
            cursor.close()
            conn.close()

            if not rows:
                return None

            actuaciones = []
            for row in rows:
                # Obtener nombre_archivo: priorizar columna dedicada, fallback a ruta_pdf
                nombre_archivo = row.get('nombre_archivo')
                if not nombre_archivo and row.get('ruta_pdf'):
                    nombre_archivo = Path(row['ruta_pdf']).name

                # Mapear row a entidad Actuacion
                act = Actuacion(
                    indice=row['indice'],
                    oficina="",  # No tenemos oficina en DB
                    fecha=str(row.get('fecha')) if row.get('fecha') else None,
                    tipo=row['tipo'],
                    detalle=row['detalle'],
                    nombre_archivo=nombre_archivo,
                    foja=None,
                    tiene_archivo=bool(row['tiene_archivo'])
                )
                actuaciones.append(act)

            return tuple(actuaciones)

        except Exception as e:
            logger.error(f"Error obteniendo actuaciones de {numero_expediente}: {e}")
            return None

    async def obtener_por_indice(self, numero_expediente: str, indice: int) -> Actuacion | None:
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)

            query = "SELECT * FROM actuaciones WHERE expediente_numero = %s AND indice = %s"
            cursor.execute(query, (numero_expediente, indice))
            row = cursor.fetchone()
            
            cursor.close()
            conn.close()

            if row:
                # Obtener nombre_archivo: priorizar columna dedicada, fallback a ruta_pdf
                nombre_archivo = row.get('nombre_archivo')
                if not nombre_archivo and row.get('ruta_pdf'):
                    nombre_archivo = Path(row['ruta_pdf']).name

                return Actuacion(
                    indice=row['indice'],
                    oficina="",
                    fecha=str(row.get('fecha')) if row.get('fecha') else None,
                    tipo=row['tipo'],
                    detalle=row['detalle'],
                    nombre_archivo=nombre_archivo,
                    foja=None,
                    tiene_archivo=bool(row['tiene_archivo'])
                )
            return None
        except Exception as e:
            logger.error(f"Error obteniendo actuacion {indice} de {numero_expediente}: {e}")
            return None

    async def obtener_con_archivo(self, numero_expediente: str) -> Tuple[Actuacion, ...]:
        actuaciones = await self.obtener_actuaciones(numero_expediente)
        if not actuaciones:
            return ()
        return tuple(a for a in actuaciones if a.tiene_archivo)

    async def existe(self, numero_expediente: str) -> bool:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM actuaciones WHERE expediente_numero = %s", (numero_expediente,))
            count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            return count > 0
        except Exception:
            return False

    # =========================================================================
    # Métodos para ProcesadorActuacionesService (Escritura)
    # =========================================================================

    def guardar_clasificacion(
        self,
        indice: int,
        resultado, # ResultadoProcesamiento
        expediente_numero: str = None,
        actuacion_data: dict = None,
        expediente_id: int = None,
        ruta_pdf: str = None
    ) -> int:
        # Copia exacta del método original, ajustado a self
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            clasificacion = resultado.clasificacion
            utilidad_str = clasificacion.utilidad.value
            keywords_json = json.dumps(clasificacion.keywords_detectados) if clasificacion.keywords_detectados else None

            hash_contenido = None
            texto_extraido = None
            texto_json = None
            tiene_texto_extraido = False
            metodo_extraccion = None

            if resultado.texto:
                import hashlib
                texto_extraido = resultado.texto.texto_completo
                hash_contenido = hashlib.md5(texto_extraido.encode()).hexdigest()

                extraccion_service = ExtraccionTextoService(usar_ocr=False)
                texto_estructurado = extraccion_service.convertir_resultado(resultado)
                if texto_estructurado:
                    texto_json = ExtraccionTextoService.generar_json_para_db(texto_estructurado)
                    tiene_texto_extraido = True
                    metodo_extraccion = resultado.texto.metodo_extraccion

            tipo = actuacion_data.get('tipo') or actuacion_data.get('Tipo') or ''
            detalle = actuacion_data.get('detalle') or actuacion_data.get('Detalle') or ''
            tiene_archivo = actuacion_data.get('tiene_archivo') or actuacion_data.get('TieneArchivo') or False
            fecha_actuacion = actuacion_data.get('fecha') or actuacion_data.get('Fecha')

            # Obtener nombre_archivo desde JSON (campo NombreArchivo, nombre_archivo o archivo)
            nombre_archivo = (
                actuacion_data.get('NombreArchivo') or
                actuacion_data.get('nombre_archivo') or
                actuacion_data.get('archivo')
            )
            # Si es URL o no es string válido, ignorar
            if nombre_archivo and isinstance(nombre_archivo, str) and nombre_archivo.startswith('http'):
                nombre_archivo = None

            query = """
                INSERT INTO actuaciones (
                    expediente_id,
                    indice,
                    expediente_numero,
                    tipo,
                    detalle,
                    fecha,
                    tiene_archivo,
                    utilidad,
                    score,
                    motivo_clasificacion,
                    requiere_pdf,
                    tiene_plazo_probable,
                    es_duplicado_probable,
                    keywords_detectados,
                    fecha_clasificacion,
                    texto_extraido,
                    hash_contenido,
                    texto_json,
                    tiene_texto_extraido,
                    metodo_extraccion,
                    ruta_pdf,
                    nombre_archivo
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    expediente_numero = VALUES(expediente_numero),
                    tipo = VALUES(tipo),
                    detalle = VALUES(detalle),
                    fecha = VALUES(fecha),
                    tiene_archivo = VALUES(tiene_archivo),
                    utilidad = VALUES(utilidad),
                    score = VALUES(score),
                    motivo_clasificacion = VALUES(motivo_clasificacion),
                    requiere_pdf = VALUES(requiere_pdf),
                    tiene_plazo_probable = VALUES(tiene_plazo_probable),
                    es_duplicado_probable = VALUES(es_duplicado_probable),
                    keywords_detectados = VALUES(keywords_detectados),
                    fecha_clasificacion = VALUES(fecha_clasificacion),
                    texto_extraido = VALUES(texto_extraido),
                    hash_contenido = VALUES(hash_contenido),
                    texto_json = VALUES(texto_json),
                    tiene_texto_extraido = VALUES(tiene_texto_extraido),
                    metodo_extraccion = VALUES(metodo_extraccion),
                    ruta_pdf = VALUES(ruta_pdf),
                    nombre_archivo = VALUES(nombre_archivo)
            """

            params = (
                expediente_id,
                indice,
                expediente_numero,
                tipo,
                detalle,
                fecha_actuacion,
                tiene_archivo,
                utilidad_str,
                clasificacion.score,
                clasificacion.motivo,
                clasificacion.requiere_pdf,
                clasificacion.tiene_plazo_probable,
                len(resultado.duplicados) > 0,
                keywords_json,
                datetime.now(),
                texto_extraido,
                hash_contenido,
                texto_json,
                tiene_texto_extraido,
                metodo_extraccion,
                ruta_pdf,
                nombre_archivo
            )

            cursor.execute(query, params)
            conn.commit()
            
            if cursor.lastrowid:
                real_id = cursor.lastrowid
            else:
                cursor.execute(
                    "SELECT id FROM actuaciones WHERE expediente_id = %s AND indice = %s",
                    (expediente_id, indice)
                )
                row = cursor.fetchone()
                real_id = row[0] if row else None

            logger.debug(f"Clasificación guardada para actuación indice {indice} (ID: {real_id}): {utilidad_str}")
            cursor.close()
            conn.close()
            return real_id

        except MySQLError as e:
            logger.error(f"Error guardando clasificación de actuación indice {indice}: {e}")
            return None

    def guardar_vencimientos(self, actuacion_id: int, expediente_numero: str, vencimientos: list, expediente_id: int = None) -> int:
        if not vencimientos: return 0
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            query = """
                INSERT INTO vencimientos (
                    actuacion_id, expediente_numero, expediente_id, tipo, fecha_notificacion,
                    plazo_dias, fecha_vencimiento, dias_habiles, descripcion, texto_fuente, confianza, estado
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    fecha_notificacion = VALUES(fecha_notificacion),
                    plazo_dias = VALUES(plazo_dias),
                    dias_habiles = VALUES(dias_habiles),
                    descripcion = VALUES(descripcion),
                    texto_fuente = VALUES(texto_fuente),
                    confianza = VALUES(confianza)
            """
            guardados = 0
            for venc in vencimientos:
                params = (
                    actuacion_id, expediente_numero, expediente_id, venc.tipo.value, venc.fecha_notificacion,
                    venc.plazo_dias, venc.fecha_vencimiento, venc.dias_habiles, venc.descripcion,
                    venc.texto_fuente, venc.confianza, 'pendiente'
                )
                cursor.execute(query, params)
                guardados += 1
            conn.commit()
            cursor.close()
            conn.close()
            return guardados
        except MySQLError as e:
            logger.error(f"Error guardando vencimientos: {e}")
            return 0

    def guardar_duplicados(self, duplicados: list, expediente_numero: str) -> int:
        if not duplicados: return 0
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            query = """
                INSERT INTO duplicados_detectados (
                    actuacion_original_id, actuacion_duplicada_id, tipo, similitud, hash_normalizado, motivo
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE similitud = VALUES(similitud), motivo = VALUES(motivo)
            """
            guardados = 0
            for dup in duplicados:
                params = (
                    dup.actuacion_id_original, dup.actuacion_id_duplicada, dup.tipo.value,
                    dup.similitud, dup.hash_normalizado, dup.motivo
                )
                cursor.execute(query, params)
                guardados += 1
            conn.commit()
            cursor.close()
            conn.close()
            return guardados
        except MySQLError as e:
            logger.error(f"Error guardando duplicados: {e}")
            return 0

    def guardar_estadisticas(self, estadisticas, expediente_id: int = None) -> bool:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            query = """
                INSERT INTO procesamiento_estadisticas (
                    expediente_numero, expediente_id, fecha_procesamiento, total_actuaciones,
                    actuaciones_alta, actuaciones_media, actuaciones_baja, actuaciones_nula,
                    reduccion_estimada_pct, vencimientos_detectados, vencimientos_urgentes,
                    duplicados_detectados, tiempo_procesamiento_seg, version_procesador
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    fecha_procesamiento = VALUES(fecha_procesamiento),
                    total_actuaciones = VALUES(total_actuaciones),
                    actuaciones_alta = VALUES(actuaciones_alta),
                    actuaciones_media = VALUES(actuaciones_media),
                    actuaciones_baja = VALUES(actuaciones_baja),
                    actuaciones_nula = VALUES(actuaciones_nula),
                    reduccion_estimada_pct = VALUES(reduccion_estimada_pct),
                    vencimientos_detectados = VALUES(vencimientos_detectados),
                    vencimientos_urgentes = VALUES(vencimientos_urgentes),
                    duplicados_detectados = VALUES(duplicados_detectados),
                    tiempo_procesamiento_seg = VALUES(tiempo_procesamiento_seg),
                    version_procesador = VALUES(version_procesador)
            """
            params = (
                estadisticas.expediente_numero, expediente_id, datetime.now(), estadisticas.total_actuaciones,
                estadisticas.actuaciones_alta, estadisticas.actuaciones_media, estadisticas.actuaciones_baja,
                estadisticas.actuaciones_nula, estadisticas.reduccion_estimada_pct, estadisticas.vencimientos_detectados,
                estadisticas.vencimientos_urgentes, estadisticas.duplicados_detectados, estadisticas.tiempo_procesamiento_seg,
                estadisticas.version_procesador
            )
            cursor.execute(query, params)
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except MySQLError as e:
            logger.error(f"Error guardando estadísticas: {e}")
            return False

    def guardar_entidades(self, entidades: list, expediente_numero: str, actuacion_id: int = None) -> int:
        if not entidades: return 0
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            if actuacion_id:
                cursor.execute("DELETE FROM entidades_extraidas WHERE actuacion_id = %s AND origen = 'ia'", (actuacion_id,))
            
            query = """
                INSERT INTO entidades_extraidas (
                    expediente_numero, actuacion_id, entity_type, entity_value, score, start_pos, end_pos, origen
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            guardados = 0
            for ent in entidades:
                if not ent.get('text') or not ent.get('label'): continue
                params = (
                    expediente_numero, actuacion_id, ent.get('label'), ent.get('text'),
                    ent.get('score', 0.0), ent.get('start', 0), ent.get('end', 0), 'ia'
                )
                cursor.execute(query, params)
                guardados += 1
            conn.commit()
            cursor.close()
            conn.close()
            return guardados
        except MySQLError as e:
            logger.error(f"Error guardando entidades: {e}")
            return 0

    def actualizar_clasificacion_ia(self, actuacion_id: int, resultado_ia: dict) -> bool:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            clasif_ia = resultado_ia.get("clasificacion")
            indexado = resultado_ia.get("indexado", False)
            updated = False
            
            if clasif_ia:
                update_query = """
                    UPDATE actuaciones 
                    SET tipo_ia = %s, confianza_ia = %s, justificacion_ia = %s, metodo_ia = %s,
                        fecha_clasificacion_ia = NOW(), indexado_rag = %s
                    WHERE id = %s
                """
                cursor.execute(update_query, (
                    clasif_ia.get("tipo"), clasif_ia.get("confianza"), clasif_ia.get("justificacion"),
                    clasif_ia.get("metodo"), indexado, actuacion_id
                ))
                updated = cursor.rowcount > 0
            elif indexado:
                cursor.execute("UPDATE actuaciones SET indexado_rag = %s WHERE id = %s", (True, actuacion_id))
                updated = cursor.rowcount > 0
                
            conn.commit()
            cursor.close()
            conn.close()
            return updated
        except MySQLError as e:
            logger.error(f"Error actualizando IA: {e}")
            return False
