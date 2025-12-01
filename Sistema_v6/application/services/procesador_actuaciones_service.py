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
from application.services.extraccion_texto_service import ExtraccionTextoService
from core.domain.expediente_utils import normalizar_numero_expediente
from application.services.ia.ia_integration_service import IAIntegrationService
from infrastructure.persistence.actuaciones_mysql import MysqlActuacionRepository

# Importar repositorio de expedientes para obtener expediente_id
try:
    from infrastructure.persistence.expedientes_mysql import get_expedientes_repository
    _expedientes_repo_available = True
except ImportError:
    _expedientes_repo_available = False

# Importar servicio de integración IA
try:
    from application.services.ia.ia_integration_service import get_ia_integration_service
    _ia_integration_available = True
except ImportError:
    _ia_integration_available = False

logger = logging.getLogger(__name__)

# Importar servicios de NER y normalización de entidades
try:
    from application.services.ia import EntityNormalizer, NERChunker
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


# ActuacionesRepository removido (usar MysqlActuacionRepository)

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

    def __init__(self, db_config: dict, base_dir: Path = None):
        """
        Inicializa el servicio.

        Args:
            db_config: Configuración de BD
            base_dir: Directorio base para archivos (opcional)
        """
        self.db_config = db_config
        self.base_dir = base_dir or Path("data")
        
        # Inicializar repositorio usando MysqlActuacionRepository
        self.repository = MysqlActuacionRepository(db_config)
        
        # Inicializar servicio de integración IA si está disponible
        self.ia_service = None
        if _ia_integration_available:
            try:
                self.ia_service = get_ia_integration_service()
                logger.info("Servicio de Integración IA inicializado")
            except Exception as e:
                logger.warning(f"No se pudo inicializar servicio IA: {e}")

    def _get_expediente_id(self, numero_expediente: str) -> Optional[int]:
        """Obtiene el ID del expediente desde MySQL."""
        try:
            conn = self.repository._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM expedientes WHERE numero_normalizado = %s OR numero_original = %s", (numero_expediente, numero_expediente))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            return row[0] if row else None
        except Exception as e:
            logger.error(f"Error obteniendo ID de expediente {numero_expediente}: {e}")
            return None

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
            indice = actuacion.get('id') # El 'id' del input es el índice
            expediente_numero = actuacion.get('expediente_numero', '')
            
            # Resolver expediente_id
            expediente_id = self._get_expediente_id(expediente_numero)
            
            if indice and expediente_id:
                real_id = self.repository.guardar_clasificacion(
                    indice,
                    resultado,
                    expediente_numero=expediente_numero,
                    actuacion_data=actuacion,
                    expediente_id=expediente_id,
                    ruta_pdf=ruta_pdf
                )

                if real_id:
                    # Actualizar ID en el resultado para que coincida con BD
                    resultado.actuacion_id = real_id
                    
                    if resultado.vencimientos:
                        self.repository.guardar_vencimientos(
                            real_id,
                            expediente_numero,
                            resultado.vencimientos,
                            expediente_id=expediente_id
                        )
                    
                    # Guardar entidades si existen
                    if hasattr(resultado, 'entidades') and resultado.entidades:
                         self.repository.guardar_entidades(
                            resultado.entidades,
                            expediente_numero,
                            actuacion_id=real_id
                        )
            elif not expediente_id:
                logger.warning(f"No se encontró expediente_id para {expediente_numero}, no se guardó actuación.")

        return resultado

    async def procesar_desde_json(
        self,
        numero_expediente: str,
        ruta_json: str,
        guardar_en_bd: bool = True
    ) -> dict:
        """
        Procesa actuaciones desde un archivo JSON y las persiste en MySQL.

        Args:
            numero_expediente: Número del expediente
            ruta_json: Ruta al archivo JSON con las actuaciones
            guardar_en_bd: Si guardar resultados en BD

        Returns:
            Dict con estadísticas del procesamiento
        """
        import json
        from pathlib import Path

        # Cargar JSON
        json_path = Path(ruta_json)
        if not json_path.exists():
            raise FileNotFoundError(f"No se encontró el archivo JSON: {ruta_json}")

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Extraer actuaciones del JSON
        # Intentar diferentes formatos
        actuaciones = (
            data.get("actuaciones_actuales", []) +
            data.get("actuaciones_historicas", [])
        )
        
        # Formato alternativo
        if not actuaciones:
            actuaciones = data.get("Actuaciones", [])

        if not actuaciones:
            logger.warning(f"No se encontraron actuaciones en {ruta_json}")
            return {
                "total_actuaciones": 0,
                "actuaciones_procesadas": 0,
                "error": "No se encontraron actuaciones en el JSON"
            }

        # Procesar con el método existente
        return await self.procesar_expediente_completo(
            numero_expediente=numero_expediente,
            actuaciones=actuaciones,
            rutas_pdf=None,  # No hay PDFs en este flujo
            guardar_en_bd=guardar_en_bd
        )

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

        logger.info(f"Procesando expediente {numero_expediente}. Actuaciones: {len(actuaciones)}. Rutas PDF: {len(rutas_pdf) if rutas_pdf else 0}")
        
        # Normalizar número de expediente (necesario para búsquedas posteriores)
        numero_normalizado = normalizar_numero_expediente(numero_expediente)

        # Auto-descubrimiento de PDFs si no se proporcionan
        if not rutas_pdf:
            logger.info("rutas_pdf vacio, iniciando auto-descubrimiento...")
            try:
                from gestor_directorios.expedientes import GestorDirectoriosExpedientes
                gestor = GestorDirectoriosExpedientes.desde_config()
                # Obtener ruta del expediente (crea estructura si no existe, pero es idempotente)
                path_expediente, _ = gestor.crear_para_expediente(numero_expediente)
                path_actuaciones = path_expediente / "actuaciones"
                
                if path_actuaciones.exists():
                    rutas_pdf = {}
                    # Estrategia 1: Usar NombreArchivo si viene en los datos de la actuación
                    for act in actuaciones:
                        act_id = act.get('id') or act.get('Indice')
                        if not act_id:
                            continue
                            
                        # Intentar obtener nombre de archivo de varias claves posibles
                        nombre_archivo = (
                            act.get('NombreArchivo') or 
                            act.get('nombre_archivo') or 
                            act.get('archivo')
                        )
                        
                        if nombre_archivo and isinstance(nombre_archivo, str) and not nombre_archivo.startswith('http'):
                            # Si es una ruta relativa o solo nombre
                            posible_path = path_actuaciones / nombre_archivo
                            if posible_path.exists():
                                rutas_pdf[act_id] = str(posible_path)
                                continue

                    # Estrategia 2: Si falló la 1, intentar mapeo por JSON (fallback)
                    if not rutas_pdf:
                        logger.info("Estrategia 1 falló, intentando leer JSON de actuaciones para mapeo...")
                        path_json_dir = path_expediente / "json"
                        if path_json_dir.exists():
                            # Buscar el archivo json más reciente o el que coincida
                            json_files = list(path_json_dir.glob("actuaciones-*.json"))
                            if json_files:
                                import json
                                # Usar el primero encontrado (usualmente solo hay uno por exp)
                                json_path = json_files[0]
                                try:
                                    with open(json_path, 'r', encoding='utf-8') as f:
                                        data = json.load(f)
                                        actuaciones_json = data.get('Actuaciones', [])
                                        
                                        # Crear mapa hash/fecha+tipo -> nombre_archivo
                                        mapa_archivos = {}
                                        for aj in actuaciones_json:
                                            if aj.get('NombreArchivo'):
                                                # Clave compuesta para matching
                                                clave = f"{aj.get('Fecha')}_{aj.get('Tipo')}" # Corregido TipoActuacion -> Tipo
                                                mapa_archivos[clave] = aj.get('NombreArchivo')
                                                # También por descripción si es única
                                                if aj.get('Detalle'): # Corregido Descripcion -> Detalle
                                                    mapa_archivos[aj.get('Detalle')] = aj.get('NombreArchivo')

                                        # Intentar matchear con las actuaciones recibidas
                                        for act in actuaciones:
                                            act_id = act.get('id') or act.get('Indice')
                                            if act_id and act_id not in rutas_pdf:
                                                # Normalizar claves para matching
                                                fecha = act.get('fecha') or act.get('Fecha')
                                                tipo = act.get('tipo') or act.get('Tipo')
                                                detalle = act.get('detalle') or act.get('Detalle') or act.get('descripcion')
                                                
                                                clave = f"{fecha}_{tipo}"
                                                nombre = mapa_archivos.get(clave)
                                                if not nombre and detalle:
                                                    nombre = mapa_archivos.get(detalle)
                                                
                                                if nombre:
                                                    p = path_actuaciones / nombre
                                                    if p.exists():
                                                        rutas_pdf[act_id] = str(p)
                                except Exception as e:
                                    logger.warning(f"Error leyendo JSON de actuaciones: {e}")

                    if rutas_pdf:
                        logger.info(f"Auto-descubiertos {len(rutas_pdf)} PDFs en {path_actuaciones}")
                        # DEBUG: Imprimir algunas rutas encontradas
                        for k, v in list(rutas_pdf.items())[:3]:
                            logger.info(f"  ID {k} -> {v}")
                    else:
                        logger.warning(f"No se encontraron PDFs coincidentes en {path_actuaciones}")
                        logger.warning(f"  - Estrategia 1 probada con {len(actuaciones)} actuaciones")
                        logger.warning(f"  - Estrategia 2 probada con JSON en {path_json_dir if 'path_json_dir' in locals() else 'N/A'}")
            except Exception as e:
                logger.error(f"Falló el auto-descubrimiento de PDFs: {e}", exc_info=True)

        logger.info(f"Llamando a procesar_expediente con {len(rutas_pdf) if rutas_pdf else 0} rutas de PDF")

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
                    # numero_normalizado ya se obtiene al inicio del método
                    repo_expedientes = get_expedientes_repository(self.db_config)
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
                act_id = actuacion.get('id') or actuacion.get('Indice')
                if act_id and act_id in resultado_procesamiento['resultados']:
                    resultado = resultado_procesamiento['resultados'][act_id]
                    
                    # Guardar clasificación y obtener ID real
                    real_id = self.repository.guardar_clasificacion(
                        act_id,
                        resultado,
                        expediente_numero=numero_expediente,
                        actuacion_data=actuacion,
                        expediente_id=expediente_id,
                        ruta_pdf=rutas_pdf.get(act_id) if rutas_pdf else None
                    )

                    if not real_id:
                        logger.warning(f"No se pudo guardar clasificación para actuación {act_id}")
                        continue

                    # Guardar vencimientos
                    if resultado.vencimientos:
                        self.repository.guardar_vencimientos(
                            real_id,
                            numero_expediente,
                            resultado.vencimientos,
                            expediente_id=expediente_id
                        )

                    # Integración IA Unificada (Clasificación + NER + RAG)
                    if _ia_integration_available and self.ia_service:
                        metadata_ia = {
                            "expediente_id": expediente_id,
                            "expediente_numero": numero_expediente,
                            "actuacion_id": real_id,
                            "tipo": actuacion.get("tipo", "DESCONOCIDO"),
                            "detalle": actuacion.get("detalle", "") or actuacion.get("descripcion", ""),
                            "fecha": actuacion.get("fecha", "")
                        }
                        
                        texto_ia = ""
                        origen_texto = ""
                        if resultado.texto and resultado.texto.texto_completo:
                            texto_ia = resultado.texto.texto_completo
                            origen_texto = "pdf_extract"
                        
                        # Fallback de texto para RAG si no hay PDF
                        if not texto_ia and self.ia_service.habilitar_rag:
                             detalle = actuacion.get("detalle", "") or actuacion.get("descripcion", "")
                             tipo = actuacion.get("tipo", "DESCONOCIDO")
                             if detalle:
                                 texto_ia = f"TIPO: {tipo}\nDETALLE: {detalle}"
                                 origen_texto = "metadata_fallback"
                        
                        if texto_ia:
                            # Llamada unificada a IA
                            res_ia = self.ia_service.procesar_actuacion(
                                actuacion_id=str(real_id),
                                texto=texto_ia,
                                metadata=metadata_ia,
                                clasificar=True,
                                indexar=True,
                                extraer_entidades=True
                            )
                            
                            # Actualizar DB y Entidades
                            if res_ia and not res_ia.get("skipped"):
                                self.repository.actualizar_clasificacion_ia(real_id, res_ia)
                                if res_ia.get("entidades"):
                                    entidades_por_actuacion[act_id] = res_ia["entidades"]
                                
                                if res_ia.get("indexado"):
                                    logger.debug(f"Actuación {real_id} (idx {act_id}) procesada por IA (Origen: {origen_texto})")

                    # Fallback Manual (Solo si IA NO disponible)
                    elif resultado.texto and resultado.texto.texto_completo:
                         entidades = self.extraer_entidades_actuacion(resultado.texto.texto_completo)
                         if entidades:
                             entidades_por_actuacion[act_id] = entidades
                             self.repository.guardar_entidades(
                                 entidades, 
                                 numero_expediente, 
                                 actuacion_id=real_id
                             )
                             logger.debug(f"Entidades extraídas manualmente para {real_id} (idx {act_id})")

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

            # Si no encuentra, intentar con formato original (FPA_000635_2017 -> FPA 000635/2017)
            if estadisticas is None:
                import re
                partes = re.match(r'^([A-Z]+)_(\d+)_(\d+)$', numero_expediente)
                if partes:
                    numero_original = f"{partes.group(1)} {partes.group(2)}/{partes.group(3)}"
                    cursor.execute(query, (numero_original,))
                    estadisticas = cursor.fetchone()

            cursor.close()
            conn.close()

            return estadisticas

        except MySQLError as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return None

    async def procesar_expediente_stream(
        self,
        numero_expediente: str,
        actuaciones: list[dict],
        rutas_pdf: dict[int, str] = None,
        guardar_en_bd: bool = True,
        usar_ocr: bool = True
    ):
        """
        Procesa un expediente generando eventos de progreso (Streaming).

        Yields:
            JSON strings con eventos:
            - {"event": "start", "total": N}
            - {"event": "progress", "current": I, "actuacion_id": ID, "status": "..."}
            - {"event": "saving", "message": "..."}
            - {"event": "complete", "result": {...}}
            - {"event": "error", "message": "..."}
        """
        import time
        import json
        from core.procesador_pdf import (
            procesar_actuacion,
            DetectorDuplicados,
            AnalizadorVencimientos,
            ClasificadorActuaciones
        )

        inicio = time.time()
        rutas_pdf = rutas_pdf or {}
        total_actuaciones = len(actuaciones)
        
        yield json.dumps({
            "event": "start", 
            "total": total_actuaciones,
            "message": f"Iniciando procesamiento de {total_actuaciones} actuaciones..."
        }) + "\n"

        try:
            # 1. Auto-descubrimiento de PDFs (si es necesario)
            # Nota: Esto podría tomar tiempo, quizás deberíamos emitir eventos aquí también
            # Por ahora lo mantenemos simple reutilizando la lógica pero sin duplicarla demasiado
            # Si rutas_pdf está vacío, intentamos descubrir
            if not rutas_pdf:
                yield json.dumps({
                    "event": "info", 
                    "message": "Buscando archivos PDF asociados..."
                }) + "\n"
                
                # Reutilizamos lógica de auto-descubrimiento (simplificada para no duplicar todo el bloque)
                # Idealmente extraer a método privado, pero por ahora copiamos lo esencial
                try:
                    from gestor_directorios.expedientes import GestorDirectoriosExpedientes
                    gestor = GestorDirectoriosExpedientes.desde_config()
                    path_expediente, _ = gestor.crear_para_expediente(numero_expediente)
                    path_actuaciones = path_expediente / "actuaciones"
                    
                    if path_actuaciones.exists():
                        # Estrategia 1: NombreArchivo directo
                        for act in actuaciones:
                            act_id = act.get('id') or act.get('Indice')
                            if not act_id: continue
                            nombre = act.get('NombreArchivo') or act.get('nombre_archivo') or act.get('archivo')
                            if nombre and isinstance(nombre, str) and not nombre.startswith('http'):
                                p = path_actuaciones / nombre
                                if p.exists(): rutas_pdf[act_id] = str(p)
                except Exception as e:
                    logger.warning(f"Error en auto-descubrimiento stream: {e}")

            # 2. Procesamiento iterativo
            resultados = {}
            for i, actuacion in enumerate(actuaciones):
                act_id = actuacion.get("id") or actuacion.get("Indice")
                
                # Emitir progreso
                yield json.dumps({
                    "event": "progress",
                    "current": i + 1,
                    "total": total_actuaciones,
                    "actuacion_id": act_id,
                    "message": f"Actuación {i+1}/{total_actuaciones}: Extrayendo texto y clasificando..."
                }) + "\n"

                # Buscar PDF
                ruta_pdf = rutas_pdf.get(act_id)
                if not ruta_pdf and act_id is not None:
                    try:
                        ruta_pdf = rutas_pdf.get(int(act_id)) or rutas_pdf.get(str(act_id))
                    except (ValueError, TypeError): pass

                # Procesar
                # Nota: procesar_actuacion es síncrono (CPU bound), en un entorno real de alta concurrencia
                # esto debería correrse en un threadpool, pero para este caso de uso está bien.
                resultado = procesar_actuacion(
                    actuacion=actuacion,
                    ruta_pdf=ruta_pdf,
                    analizar_vencimientos=True,
                    detectar_duplicados=False, # Se hace al final
                    usar_ocr=usar_ocr # Habilitar OCR según parámetro
                )
                resultados[act_id] = resultado
                
                # Pequeña pausa para permitir que el event loop respire si es necesario
                # await asyncio.sleep(0) 

            # 3. Post-procesamiento (Duplicados, Stats)
            yield json.dumps({
                "event": "analyzing",
                "message": "Analizando duplicados y generando estadísticas..."
            }) + "\n"

            # Detección de duplicados
            duplicados_globales = []
            try:
                detector = DetectorDuplicados()
                duplicados_globales = detector.detectar_duplicados_exactos(actuaciones)
                duplicados_cedulas = detector.detectar_cedulas_duplicadas(actuaciones)
                duplicados_globales.extend(duplicados_cedulas)
                
                for dup in duplicados_globales:
                    if dup.actuacion_id_original in resultados:
                        resultados[dup.actuacion_id_original].duplicados.append(dup)
                    if dup.actuacion_id_duplicada in resultados:
                        resultados[dup.actuacion_id_duplicada].duplicados.append(dup)
            except Exception: pass

            # Vencimientos y Stats
            todos_vencimientos = []
            for res in resultados.values():
                todos_vencimientos.extend(res.vencimientos)
            
            analizador = AnalizadorVencimientos()
            vencimientos_urgentes = analizador.filtrar_vencimientos_urgentes(todos_vencimientos)
            
            clasificador = ClasificadorActuaciones()
            clasificaciones = {act_id: res.clasificacion for act_id, res in resultados.items()}
            estadisticas_dict = clasificador.estadisticas_clasificacion(clasificaciones)

            tiempo_procesamiento = time.time() - inicio

            # Construir resultado final preliminar
            resultado_final = {
                "resultados": resultados, # No serializable directamente, cuidado
                "estadisticas": estadisticas_dict,
                "vencimientos_urgentes": vencimientos_urgentes, # Objetos Vencimiento
                "vencimientos_totales": len(todos_vencimientos),
                "duplicados_detectados": duplicados_globales,
                "total_actuaciones": len(actuaciones),
                "con_errores": len([r for r in resultados.values() if r.tiene_errores])
            }

            # 4. Persistencia
            if guardar_en_bd:
                yield json.dumps({
                    "event": "saving",
                    "message": "Guardando resultados en base de datos..."
                }) + "\n"
                
                # Reutilizar lógica de guardado
                # Necesitamos expediente_id
                expediente_id = None
                if _expedientes_repo_available:
                    try:
                        numero_normalizado = normalizar_numero_expediente(numero_expediente)
                        repo = get_expedientes_repository()
                        expediente_id = repo.obtener_id(numero_normalizado)
                    except Exception: pass

                # Guardar uno a uno
                entidades_por_actuacion = {}
                for i, act in enumerate(actuaciones):
                    act_id = act.get('id')
                    if act_id and act_id in resultados:
                        res = resultados[act_id]
                        
                        # Emitir evento de guardado/enriquecimiento
                        yield json.dumps({
                            "event": "saving",
                            "message": f"Guardando actuación {i+1}/{total_actuaciones}..."
                        }) + "\n"

                        self.repository.guardar_clasificacion(
                            act_id, res, numero_expediente, act, expediente_id
                        )
                        if res.vencimientos:
                            self.repository.guardar_vencimientos(
                                act_id, numero_expediente, res.vencimientos, expediente_id
                            )
                        
                        # Integración IA Unificada (Stream)
                        if _ia_integration_available and self.ia_service:
                            yield json.dumps({
                                "event": "analyzing",
                                "message": f"Actuación {i+1}/{total_actuaciones}: Procesando con IA (Clasificación/NER/RAG)..."
                            }) + "\n"

                            metadata_ia = {
                                "expediente_id": expediente_id,
                                "expediente_numero": numero_expediente,
                                "actuacion_id": act_id,
                                "tipo": act.get("tipo", "DESCONOCIDO"),
                                "detalle": act.get("detalle", "") or act.get("descripcion", ""),
                                "fecha": act.get("fecha", "")
                            }
                            
                            texto_ia = ""
                            if res.texto and res.texto.texto_completo:
                                texto_ia = res.texto.texto_completo
                            
                            # Fallback RAG
                            if not texto_ia and self.ia_service.habilitar_rag:
                                detalle = act.get("detalle", "") or act.get("descripcion", "")
                                tipo = act.get("tipo", "DESCONOCIDO")
                                if detalle:
                                    texto_ia = f"TIPO: {tipo}\nDETALLE: {detalle}"

                            if texto_ia:
                                try:
                                    res_ia = self.ia_service.procesar_actuacion(
                                        actuacion_id=str(act_id),
                                        texto=texto_ia,
                                        metadata=metadata_ia,
                                        clasificar=True,
                                        indexar=True,
                                        extraer_entidades=True
                                    )
                                    
                                    if res_ia and not res_ia.get("skipped"):
                                        self.repository.actualizar_clasificacion_ia(act_id, res_ia)
                                        if res_ia.get("entidades"):
                                            entidades_por_actuacion[act_id] = res_ia["entidades"]
                                except Exception as e:
                                    logger.error(f"Error IA stream: {e}")

                        # Fallback Manual
                        elif res.texto and res.texto.texto_completo:
                            yield json.dumps({
                                "event": "analyzing",
                                "message": f"Actuación {i+1}/{total_actuaciones}: Extrayendo entidades manualmente..."
                            }) + "\n"
                            
                            ents = self.extraer_entidades_actuacion(res.texto.texto_completo)
                            if ents: 
                                entidades_por_actuacion[act_id] = ents
                                self.repository.guardar_entidades(
                                    ents,
                                    numero_expediente,
                                    actuacion_id=act_id
                                )

                # Guardar globales
                if duplicados_globales:
                    self.repository.guardar_duplicados(duplicados_globales, numero_expediente)
                
                stats_obj = EstadisticasProcesamiento(
                    expediente_numero=numero_expediente,
                    total_actuaciones=len(actuaciones),
                    actuaciones_alta=estadisticas_dict.get('alta', {}).get('count', 0),
                    actuaciones_media=estadisticas_dict.get('media', {}).get('count', 0),
                    actuaciones_baja=estadisticas_dict.get('baja', {}).get('count', 0),
                    actuaciones_nula=estadisticas_dict.get('nula', {}).get('count', 0),
                    reduccion_estimada_pct=estadisticas_dict.get('reduccion_estimada', 0.0),
                    vencimientos_detectados=len(todos_vencimientos),
                    vencimientos_urgentes=len(vencimientos_urgentes),
                    duplicados_detectados=len(duplicados_globales),
                    tiempo_procesamiento_seg=tiempo_procesamiento
                )
                self.repository.guardar_estadisticas(stats_obj, expediente_id)
                
                # Agregar entidades al resultado final para el cliente
                resultado_final['entidades_por_actuacion'] = entidades_por_actuacion

            # 5. Finalización
            # Preparamos el objeto de resultado final serializable
            # Necesitamos convertir objetos a dicts/tipos simples para JSON
            
            # Serializar vencimientos urgentes
            vencimientos_serializables = []
            for i, v in enumerate(vencimientos_urgentes):
                v_dict = vars(v) if hasattr(v, '__dict__') else v
                # Convertir fechas a str
                if 'fecha_vencimiento' in v_dict and isinstance(v_dict['fecha_vencimiento'], (datetime, date)):
                    v_dict['fecha_vencimiento'] = str(v_dict['fecha_vencimiento'])
                if 'fecha_notificacion' in v_dict and isinstance(v_dict['fecha_notificacion'], (datetime, date)):
                    v_dict['fecha_notificacion'] = str(v_dict['fecha_notificacion'])
                # Convertir Enum a value
                if 'tipo' in v_dict and hasattr(v_dict['tipo'], 'value'):
                    v_dict['tipo'] = v_dict['tipo'].value
                vencimientos_serializables.append(v_dict)

            response_payload = {
                "expediente_numero": numero_expediente,
                "estadisticas": {
                    "total_actuaciones": len(actuaciones),
                    "actuaciones_alta": estadisticas_dict.get('alta', {}).get('count', 0),
                    "actuaciones_media": estadisticas_dict.get('media', {}).get('count', 0),
                    "actuaciones_baja": estadisticas_dict.get('baja', {}).get('count', 0),
                    "actuaciones_nula": estadisticas_dict.get('nula', {}).get('count', 0),
                    "reduccion_estimada_pct": estadisticas_dict.get('reduccion_estimada', 0.0),
                    "vencimientos_detectados": len(todos_vencimientos),
                    "vencimientos_urgentes": len(vencimientos_urgentes),
                    "duplicados_detectados": len(duplicados_globales),
                    "tiempo_procesamiento_seg": tiempo_procesamiento
                },
                "vencimientos_urgentes": vencimientos_serializables,
                "con_errores": resultado_final["con_errores"]
            }

            yield json.dumps({
                "event": "complete",
                "result": response_payload
            }) + "\n"

        except Exception as e:
            logger.error(f"Error en stream: {e}", exc_info=True)
            yield json.dumps({
                "event": "error",
                "message": str(e)
            }) + "\n"
