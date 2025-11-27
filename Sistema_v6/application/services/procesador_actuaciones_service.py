"""
Servicio de Procesamiento de Actuaciones.

Wrapper sobre Sistema_v5.procesador_pdf que provee:
- Clasificación automática de actuaciones por utilidad jurídica
- Detección de duplicados (exactos y semánticos)
- Análisis de vencimientos y plazos procesales
- Persistencia en base de datos MySQL

Integra el módulo procesador_pdf con el sistema Sistema_v6.
"""

from pathlib import Path
from typing import Optional, Protocol
from dataclasses import dataclass
from datetime import datetime
import logging
import json

try:
    from core.procesador_pdf import (
        procesar_actuacion,
        procesar_expediente,
        ClasificadorActuaciones,
        DetectorDuplicados,
        ExtractorTexto,
        AnalizadorVencimientos,
        UtilidadJuridica,
        ResultadoProcesamiento,
    )
except ImportError as e:
    logging.error(f"Error importando procesador_pdf: {e}")
    raise ImportError(
        "No se pudo importar procesador_pdf desde core. "
        "Verifique que el módulo existe en Sistema_v6/core/procesador_pdf/"
    ) from e

import mysql.connector
from mysql.connector import Error as MySQLError

# Importar servicio de extracción de texto estructurado
from Sistema_v6.application.services.extraccion_texto_service import ExtraccionTextoService
from Sistema_v6.core.domain.expediente_utils import normalizar_numero_expediente

# Importar repositorio de expedientes para obtener expediente_id
try:
    from Sistema_v6.infrastructure.persistence.expedientes_mysql import get_expedientes_repository
    _expedientes_repo_available = True
except ImportError:
    _expedientes_repo_available = False

# Importar servicio de integración IA
try:
    from Sistema_v6.application.services.ia.ia_integration_service import get_ia_integration_service
    _ia_integration_available = True
except ImportError:
    _ia_integration_available = False

logger = logging.getLogger(__name__)

# Importar servicios de NER y normalización de entidades
try:
    from Sistema_v6.application.services.ia import EntityNormalizer, NERChunker
    _ner_services_available = True
except ImportError:
    _ner_services_available = False
    logger.warning("Servicios NER (EntityNormalizer, NERChunker) no disponibles")


# La función normalizar_numero_expediente se importa de core.domain.expediente_utils
# Formato unificado: FPA-015960-2018 (con guiones)


# ============================================================================
# Protocols y tipos
# ============================================================================


class DatabaseConfig(Protocol):
    """Protocol para configuración de base de datos"""
    host: str
    port: int
    database: str
    user: str
    password: str


@dataclass
class EstadisticasProcesamiento:
    """Estadísticas de procesamiento de un expediente"""
    expediente_numero: str
    total_actuaciones: int
    actuaciones_alta: int
    actuaciones_media: int
    actuaciones_baja: int
    actuaciones_nula: int
    reduccion_estimada_pct: float
    vencimientos_detectados: int
    vencimientos_urgentes: int
    duplicados_detectados: int
    tiempo_procesamiento_seg: float
    version_procesador: str = "1.0.0"


# ============================================================================
# Repositorio de Actuaciones
# ============================================================================


class ActuacionesRepository:
    """
    Repositorio para persistir resultados de procesamiento en MySQL.

    Gestiona las tablas:
    - actuaciones: Actualiza campos de clasificación
    - vencimientos: Inserta vencimientos detectados
    - duplicados_detectados: Inserta duplicados encontrados
    - procesamiento_estadisticas: Guarda estadísticas
    """

    def __init__(self, db_config: dict):
        """
        Inicializa el repositorio con la configuración de BD.

        Args:
            db_config: Dict con host, port, database, user, password
        """
        self.db_config = db_config
        logger.info(f"ActuacionesRepository inicializado para BD: {db_config.get('database')}")

    def _get_connection(self):
        """Obtiene una conexión a la base de datos"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            return conn
        except MySQLError as e:
            logger.error(f"Error conectando a MySQL: {e}")
            raise

    def guardar_clasificacion(
        self,
        actuacion_id: int,
        resultado: ResultadoProcesamiento,
        expediente_numero: str = None,
        actuacion_data: dict = None,
        expediente_id: int = None
    ) -> bool:
        """
        Guarda los resultados de clasificación en la tabla actuaciones.

        Usa INSERT ... ON DUPLICATE KEY UPDATE para crear el registro si no existe.

        Args:
            actuacion_id: ID de la actuación
            resultado: Resultado del procesamiento
            expediente_numero: Número del expediente
            actuacion_data: Dict con datos de la actuación (tipo, detalle, etc.)
            expediente_id: ID del expediente en MySQL (opcional)

        Returns:
            True si se guardó correctamente
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            clasificacion = resultado.clasificacion

            # Convertir UtilidadJuridica enum a string
            utilidad_str = clasificacion.utilidad.value  # nula, baja, media, alta

            # Convertir keywords_detectados a JSON
            keywords_json = json.dumps(clasificacion.keywords_detectados) if clasificacion.keywords_detectados else None

            # Hash del contenido y texto estructurado (si hay texto extraído)
            hash_contenido = None
            texto_extraido = None
            texto_json = None
            tiene_texto_extraido = False
            metodo_extraccion = None

            if resultado.texto:
                import hashlib
                texto_extraido = resultado.texto.texto_completo
                hash_contenido = hashlib.md5(texto_extraido.encode()).hexdigest()

                # Generar texto estructurado para almacenamiento JSON
                extraccion_service = ExtraccionTextoService(usar_ocr=False)
                texto_estructurado = extraccion_service.convertir_resultado(resultado)
                if texto_estructurado:
                    texto_json = ExtraccionTextoService.generar_json_para_db(texto_estructurado)
                    tiene_texto_extraido = True
                    metodo_extraccion = resultado.texto.metodo_extraccion

            # Datos de la actuación
            tipo = actuacion_data.get('tipo', '') if actuacion_data else ''
            detalle = actuacion_data.get('detalle', '') if actuacion_data else ''
            tiene_archivo = actuacion_data.get('tiene_archivo', False) if actuacion_data else False

            # Usar INSERT ... ON DUPLICATE KEY UPDATE para crear el registro si no existe
            query = """
                INSERT INTO actuaciones (
                    id,
                    expediente_id,
                    expediente_numero,
                    tipo,
                    detalle,
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
                    metodo_extraccion
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    expediente_id = VALUES(expediente_id),
                    expediente_numero = VALUES(expediente_numero),
                    tipo = VALUES(tipo),
                    detalle = VALUES(detalle),
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
                    metodo_extraccion = VALUES(metodo_extraccion)
            """

            params = (
                actuacion_id,
                expediente_id,
                expediente_numero,
                tipo,
                detalle,
                tiene_archivo,
                utilidad_str,
                clasificacion.score,
                clasificacion.motivo,
                clasificacion.requiere_pdf,
                clasificacion.tiene_plazo_probable,
                len(resultado.duplicados) > 0,  # es_duplicado_probable
                keywords_json,
                datetime.now(),
                texto_extraido,
                hash_contenido,
                texto_json,
                tiene_texto_extraido,
                metodo_extraccion
            )

            cursor.execute(query, params)
            conn.commit()

            logger.debug(f"Clasificación guardada para actuación {actuacion_id}: {utilidad_str}")

            cursor.close()
            conn.close()

            # Integrar con IA si hay texto extraído y el servicio está disponible
            if texto_extraido and _ia_integration_available:
                try:
                    ia_service = get_ia_integration_service(
                        habilitar_clasificacion=True,
                        habilitar_rag=True,
                        habilitar_ner=True
                    )
                    resultado_ia = ia_service.procesar_actuacion(
                        actuacion_id=str(actuacion_id),
                        texto=texto_extraido,
                        metadata={
                            "expediente_id": expediente_id,
                            "expediente_numero": expediente_numero,
                            "actuacion_id": actuacion_id,
                            "tipo": tipo,
                            "detalle": detalle,
                            "caratula": ""
                        },
                        clasificar=True,
                        indexar=True,
                        extraer_entidades=True
                    )

                    # Persistir clasificación IA en MySQL
                    if resultado_ia and not resultado_ia.get("skipped"):
                        try:
                            conn2 = self._get_connection()
                            cursor2 = conn2.cursor()

                            clasificacion_ia = resultado_ia.get("clasificacion")
                            indexado = resultado_ia.get("indexado", False)

                            if clasificacion_ia:
                                update_query = """
                                    UPDATE actuaciones SET
                                        tipo_ia = %s,
                                        confianza_ia = %s,
                                        justificacion_ia = %s,
                                        metodo_ia = %s,
                                        fecha_clasificacion_ia = %s,
                                        indexado_rag = %s
                                    WHERE id = %s
                                """
                                cursor2.execute(update_query, (
                                    clasificacion_ia.get("tipo"),
                                    clasificacion_ia.get("confianza"),
                                    clasificacion_ia.get("justificacion"),
                                    clasificacion_ia.get("metodo"),
                                    datetime.now(),
                                    indexado,
                                    actuacion_id
                                ))
                            elif indexado:
                                # Solo actualizar indexado_rag si no hay clasificación
                                cursor2.execute(
                                    "UPDATE actuaciones SET indexado_rag = %s WHERE id = %s",
                                    (True, actuacion_id)
                                )

                            conn2.commit()
                            cursor2.close()
                            conn2.close()

                        except MySQLError as e2:
                            logger.warning(f"Error guardando clasificación IA: {e2}")

                    logger.debug(f"Actuación {actuacion_id} procesada con IA")
                except Exception as e:
                    logger.warning(f"Error en integración IA para actuación {actuacion_id}: {e}")
                    # No falla el proceso principal si IA falla

            return True

        except MySQLError as e:
            logger.error(f"Error guardando clasificación de actuación {actuacion_id}: {e}")
            return False

    def guardar_vencimientos(
        self,
        actuacion_id: int,
        expediente_numero: str,
        vencimientos: list,
        expediente_id: int = None
    ) -> int:
        """
        Guarda vencimientos detectados en la tabla vencimientos.

        Usa INSERT ON DUPLICATE KEY UPDATE para evitar duplicados cuando
        se reprocesa el mismo expediente.

        Args:
            actuacion_id: ID de la actuación
            expediente_numero: Número de expediente
            vencimientos: Lista de objetos Vencimiento
            expediente_id: ID del expediente en MySQL (opcional)

        Returns:
            Cantidad de vencimientos guardados
        """
        if not vencimientos:
            return 0

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Usar INSERT ON DUPLICATE KEY UPDATE para deduplicación
            query = """
                INSERT INTO vencimientos (
                    actuacion_id,
                    expediente_numero,
                    expediente_id,
                    tipo,
                    fecha_notificacion,
                    plazo_dias,
                    fecha_vencimiento,
                    dias_habiles,
                    descripcion,
                    texto_fuente,
                    confianza,
                    estado
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
                    actuacion_id,
                    expediente_numero,
                    expediente_id,
                    venc.tipo.value,  # Enum a string
                    venc.fecha_notificacion,
                    venc.plazo_dias,
                    venc.fecha_vencimiento,
                    venc.dias_habiles,
                    venc.descripcion,
                    venc.texto_fuente,
                    venc.confianza,
                    'pendiente'
                )

                cursor.execute(query, params)
                guardados += 1

            conn.commit()
            logger.info(f"Guardados {guardados} vencimientos para actuación {actuacion_id}")

            cursor.close()
            conn.close()

            return guardados

        except MySQLError as e:
            logger.error(f"Error guardando vencimientos: {e}")
            return 0

    def guardar_duplicados(
        self,
        duplicados: list,
        expediente_numero: str
    ) -> int:
        """
        Guarda duplicados detectados en la tabla duplicados_detectados.

        Args:
            duplicados: Lista de objetos DuplicadoDetectado
            expediente_numero: Número de expediente

        Returns:
            Cantidad de duplicados guardados
        """
        if not duplicados:
            return 0

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = """
                INSERT INTO duplicados_detectados (
                    actuacion_original_id,
                    actuacion_duplicada_id,
                    tipo,
                    similitud,
                    hash_normalizado,
                    motivo
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    similitud = VALUES(similitud),
                    motivo = VALUES(motivo)
            """

            guardados = 0
            for dup in duplicados:
                params = (
                    dup.actuacion_id_original,
                    dup.actuacion_id_duplicada,
                    dup.tipo.value,  # Enum a string
                    dup.similitud,
                    dup.hash_normalizado,
                    dup.motivo
                )

                cursor.execute(query, params)
                guardados += 1

            conn.commit()
            logger.info(f"Guardados {guardados} duplicados para expediente {expediente_numero}")

            cursor.close()
            conn.close()

            return guardados

        except MySQLError as e:
            logger.error(f"Error guardando duplicados: {e}")
            return 0

    def guardar_estadisticas(
        self,
        estadisticas: EstadisticasProcesamiento,
        expediente_id: int = None
    ) -> bool:
        """
        Guarda estadísticas de procesamiento.

        Usa INSERT ON DUPLICATE KEY UPDATE para mantener solo el último
        registro de estadísticas por expediente (evita duplicados).

        Args:
            estadisticas: Objeto EstadisticasProcesamiento
            expediente_id: ID del expediente en MySQL (opcional)

        Returns:
            True si se guardó correctamente
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Usar INSERT ON DUPLICATE KEY UPDATE para deduplicación
            query = """
                INSERT INTO procesamiento_estadisticas (
                    expediente_numero,
                    expediente_id,
                    fecha_procesamiento,
                    total_actuaciones,
                    actuaciones_alta,
                    actuaciones_media,
                    actuaciones_baja,
                    actuaciones_nula,
                    reduccion_estimada_pct,
                    vencimientos_detectados,
                    vencimientos_urgentes,
                    duplicados_detectados,
                    tiempo_procesamiento_seg,
                    version_procesador
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
                estadisticas.expediente_numero,
                expediente_id,
                datetime.now(),
                estadisticas.total_actuaciones,
                estadisticas.actuaciones_alta,
                estadisticas.actuaciones_media,
                estadisticas.actuaciones_baja,
                estadisticas.actuaciones_nula,
                estadisticas.reduccion_estimada_pct,
                estadisticas.vencimientos_detectados,
                estadisticas.vencimientos_urgentes,
                estadisticas.duplicados_detectados,
                estadisticas.tiempo_procesamiento_seg,
                estadisticas.version_procesador
            )

            cursor.execute(query, params)
            conn.commit()

            logger.info(f"Estadísticas guardadas para expediente {estadisticas.expediente_numero}")

            cursor.close()
            conn.close()

            return True

        except MySQLError as e:
            logger.error(f"Error guardando estadísticas: {e}")
            return False


# ============================================================================
# Servicio Principal
# ============================================================================


class ProcesadorActuacionesService:
    """
    Servicio de alto nivel para procesar actuaciones.

    Coordina el procesador_pdf de Sistema_v5 con la persistencia
    en base de datos de Sistema_v6.

    Funcionalidades:
    - Procesar actuaciones individuales
    - Procesar expedientes completos
    - Obtener estadísticas de procesamiento
    - Gestionar vencimientos urgentes

    Example:
        >>> config = {
        ...     "host": "localhost",
        ...     "port": 3306,
        ...     "database": "sintaxis",
        ...     "user": "root",
        ...     "password": "password"
        ... }
        >>> servicio = ProcesadorActuacionesService(config)
        >>> resultado = await servicio.procesar_expediente(
        ...     numero_expediente="CAF 12345/2024",
        ...     actuaciones=[...],
        ...     rutas_pdf={1: "/path/to/pdf1.pdf"}
        ... )
    """

    def __init__(self, db_config: dict):
        """
        Inicializa el servicio de procesamiento.

        Args:
            db_config: Configuración de base de datos
        """
        self.repository = ActuacionesRepository(db_config)
        logger.info("ProcesadorActuacionesService inicializado")

    async def procesar_actuacion_individual(
        self,
        actuacion: dict,
        ruta_pdf: Optional[str] = None,
        guardar_en_bd: bool = True
    ) -> ResultadoProcesamiento:
        """
        Procesa una actuación individual.

        Args:
            actuacion: Dict con datos de la actuación (id, tipo, detalle, tiene_archivo)
            ruta_pdf: Ruta al PDF (opcional)
            guardar_en_bd: Si guardar resultados en BD

        Returns:
            ResultadoProcesamiento con clasificación, vencimientos, etc.
        """
        logger.info(f"Procesando actuación {actuacion.get('id')}")

        # Procesar con procesador_pdf
        resultado = procesar_actuacion(
            actuacion=actuacion,
            ruta_pdf=ruta_pdf,
            analizar_vencimientos=True,
            detectar_duplicados=False  # Se hace en batch
        )

        # Guardar en BD si se solicita
        if guardar_en_bd:
            actuacion_id = actuacion.get('id')
            expediente_numero = actuacion.get('expediente_numero', '')
            if actuacion_id:
                self.repository.guardar_clasificacion(
                    actuacion_id,
                    resultado,
                    expediente_numero=expediente_numero,
                    actuacion_data=actuacion
                )

                if resultado.vencimientos:
                    self.repository.guardar_vencimientos(
                        actuacion_id,
                        expediente_numero,
                        resultado.vencimientos
                    )

        return resultado

    async def procesar_expediente_completo(
        self,
        numero_expediente: str,
        actuaciones: list[dict],
        rutas_pdf: dict[int, str] = None,
        guardar_en_bd: bool = True
    ) -> dict:
        """
        Procesa todas las actuaciones de un expediente.

        Args:
            numero_expediente: Número del expediente
            actuaciones: Lista de actuaciones del expediente
            rutas_pdf: Dict {actuacion_id: ruta_pdf}
            guardar_en_bd: Si guardar resultados en BD

        Returns:
            Dict con resultados, estadísticas y vencimientos urgentes
        """
        import time
        inicio = time.time()

        logger.info(f"Procesando expediente {numero_expediente} ({len(actuaciones)} actuaciones)")

        # Procesar con procesador_pdf
        resultado_procesamiento = procesar_expediente(
            actuaciones=actuaciones,
            rutas_pdf=rutas_pdf,
            analizar_vencimientos=True,
            detectar_duplicados=True
        )

        tiempo_procesamiento = time.time() - inicio

        # Obtener estadísticas del resultado (siempre necesario para logging)
        stats = resultado_procesamiento.get('estadisticas', {})
        entidades_por_actuacion = {}

        # Guardar en BD si se solicita
        if guardar_en_bd:
            # Obtener expediente_id de MySQL
            expediente_id = None
            if _expedientes_repo_available:
                try:
                    numero_normalizado = normalizar_numero_expediente(numero_expediente)
                    repo_expedientes = get_expedientes_repository()
                    expediente_id = repo_expedientes.obtener_id(numero_normalizado)
                    if expediente_id:
                        logger.debug(f"Obtenido expediente_id {expediente_id} para {numero_expediente}")
                    else:
                        logger.warning(f"No se encontró expediente_id para {numero_expediente}")
                except Exception as e:
                    logger.warning(f"Error obteniendo expediente_id: {e}")
            # Guardar clasificaciones individuales y extraer entidades
            entidades_por_actuacion = {}
            for actuacion in actuaciones:
                act_id = actuacion.get('id')
                if act_id and act_id in resultado_procesamiento['resultados']:
                    resultado = resultado_procesamiento['resultados'][act_id]
                    self.repository.guardar_clasificacion(
                        act_id,
                        resultado,
                        expediente_numero=numero_expediente,
                        actuacion_data=actuacion,
                        expediente_id=expediente_id
                    )

                    # Guardar vencimientos
                    if resultado.vencimientos:
                        self.repository.guardar_vencimientos(
                            act_id,
                            numero_expediente,
                            resultado.vencimientos,
                            expediente_id=expediente_id
                        )

                    # Extraer entidades si hay texto disponible
                    if resultado.texto and resultado.texto.texto_completo:
                        entidades = self.extraer_entidades_actuacion(resultado.texto.texto_completo)
                        if entidades:
                            entidades_por_actuacion[act_id] = entidades
                            logger.debug(f"Extraídas {len(entidades)} entidades de actuación {act_id}")

            # Guardar duplicados
            if resultado_procesamiento['duplicados_detectados']:
                self.repository.guardar_duplicados(
                    resultado_procesamiento['duplicados_detectados'],
                    numero_expediente
                )

            # Guardar estadísticas
            estadisticas = EstadisticasProcesamiento(
                expediente_numero=numero_expediente,
                total_actuaciones=len(actuaciones),
                actuaciones_alta=stats.get('alta', {}).get('count', 0),
                actuaciones_media=stats.get('media', {}).get('count', 0),
                actuaciones_baja=stats.get('baja', {}).get('count', 0),
                actuaciones_nula=stats.get('nula', {}).get('count', 0),
                reduccion_estimada_pct=stats.get('reduccion_estimada', 0.0),
                vencimientos_detectados=resultado_procesamiento['vencimientos_totales'],
                vencimientos_urgentes=len(resultado_procesamiento['vencimientos_urgentes']),
                duplicados_detectados=len(resultado_procesamiento['duplicados_detectados']),
                tiempo_procesamiento_seg=tiempo_procesamiento
            )

            self.repository.guardar_estadisticas(estadisticas, expediente_id=expediente_id)

        # Agregar entidades al resultado
        resultado_procesamiento['entidades_por_actuacion'] = entidades_por_actuacion if guardar_en_bd else {}

        logger.info(
            f"Expediente {numero_expediente} procesado en {tiempo_procesamiento:.2f}s: "
            f"{stats.get('alta', {}).get('count', 0)} alta, "
            f"{len(resultado_procesamiento['vencimientos_urgentes'])} vencimientos urgentes, "
            f"{len(entidades_por_actuacion)} actuaciones con entidades"
        )

        return resultado_procesamiento

    async def obtener_vencimientos_urgentes(
        self,
        dias_adelante: int = 7
    ) -> list[dict]:
        """
        Obtiene vencimientos urgentes de la base de datos.

        Args:
            dias_adelante: Días hacia adelante a considerar

        Returns:
            Lista de vencimientos urgentes
        """
        try:
            conn = self.repository._get_connection()
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT * FROM vencimientos_urgentes
                WHERE dias_restantes <= %s
                ORDER BY fecha_vencimiento ASC
            """

            cursor.execute(query, (dias_adelante,))
            vencimientos = cursor.fetchall()

            cursor.close()
            conn.close()

            logger.info(f"Encontrados {len(vencimientos)} vencimientos urgentes")
            return vencimientos

        except MySQLError as e:
            logger.error(f"Error obteniendo vencimientos urgentes: {e}")
            return []

    def extraer_entidades_actuacion(self, texto: str) -> list[dict]:
        """
        Extrae y normaliza entidades de una actuación usando NER.

        Args:
            texto: Texto de la actuación

        Returns:
            Lista de entidades normalizadas como dicts
        """
        if not _ner_services_available:
            logger.debug("Servicios NER no disponibles, saltando extracción")
            return []

        if not texto or len(texto) < 50:
            return []

        try:
            # Usar NERChunker para textos largos
            chunker = NERChunker()
            entidades_raw = chunker.process_long_text(
                text=texto,
                labels=None,  # Usa labels predefinidos (ENTIDADES_JURIDICAS)
                threshold=0.5
            )

            if not entidades_raw:
                return []

            # Normalizar entidades (fechas, montos, nombres)
            normalizer = EntityNormalizer()
            entidades_norm = normalizer.normalize(entidades_raw)

            return normalizer.to_dict_list(entidades_norm)

        except Exception as e:
            logger.warning(f"Error extrayendo entidades: {e}")
            return []

    async def obtener_estadisticas_expediente(
        self,
        numero_expediente: str
    ) -> Optional[dict]:
        """
        Obtiene las estadísticas de procesamiento de un expediente.

        Args:
            numero_expediente: Número del expediente

        Returns:
            Dict con estadísticas o None si no existe
        """
        try:
            conn = self.repository._get_connection()
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT * FROM procesamiento_estadisticas
                WHERE expediente_numero = %s
                ORDER BY fecha_procesamiento DESC
                LIMIT 1
            """

            cursor.execute(query, (numero_expediente,))
            estadisticas = cursor.fetchone()

            cursor.close()
            conn.close()

            return estadisticas

        except MySQLError as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return None
