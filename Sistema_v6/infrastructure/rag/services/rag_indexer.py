"""
RAGIndexer - Servicio para indexar actuaciones judiciales en el sistema RAG

Maneja:
- Conversión de actuaciones JSON a DocumentChunks
- Indexación automática de actuaciones procesadas
- Reindexación de archivos existentes
- Enriquecimiento con metadata legal
"""

import logging
import json
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from infrastructure.rag.config import get_rag_settings
from infrastructure.rag.models.dto import LegalDocument, DocumentChunk, ChunkType
from infrastructure.rag.services.legal_chunker import LegalChunker
from infrastructure.rag.services.metadata_enricher import MetadataEnricher
from infrastructure.rag.services.hybrid_search_service import HybridSearchService
from application.services.extraccion_texto_service import ExtraccionTextoService

logger = logging.getLogger(__name__)


class RAGIndexer:
    """Servicio para indexar actuaciones del PJN en el sistema RAG"""

    def __init__(self):
        self.settings = get_rag_settings()
        self.chunker = LegalChunker()
        self.enricher = MetadataEnricher()
        self.search_service = HybridSearchService()
        self.extractor_texto = ExtraccionTextoService(usar_ocr=True)

        # Directorio base de expedientes
        self.expedientes_base_dir = Path("data/expedientes")

        # Cargar índices existentes
        self.search_service.load_indices()

    def indexar_expediente(
        self,
        ruta_json: Path | str,
        expediente_numero: str,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Indexar todas las actuaciones de un expediente desde su JSON

        Args:
            ruta_json: Ruta al archivo JSON de actuaciones
            expediente_numero: Número del expediente
            force: Si True, reindexar aunque ya exista

        Returns:
            Dict con estadísticas de indexación
        """
        try:
            logger.info(f"📥 Indexando expediente {expediente_numero}...")

            # Cargar JSON
            ruta_json = Path(ruta_json)
            if not ruta_json.exists():
                logger.error(f"❌ JSON no existe: {ruta_json}")
                return {
                    "success": False,
                    "error": "Archivo JSON no existe",
                    "expediente": expediente_numero
                }

            with open(ruta_json, 'r', encoding='utf-8') as f:
                datos = json.load(f)

            # Extraer datos del expediente
            expediente_data = datos.get("Expediente", datos.get("expediente", {}))
            actuaciones = datos.get("Actuaciones", datos.get("actuaciones", []))

            if not actuaciones:
                logger.warning(f"⚠️ No hay actuaciones en {expediente_numero}")
                return {
                    "success": True,
                    "chunks_indexados": 0,
                    "actuaciones_procesadas": 0,
                    "expediente": expediente_numero
                }

            logger.info(f"   📄 {len(actuaciones)} actuaciones encontradas")

            # Convertir actuaciones a LegalDocuments
            documentos = self._convertir_actuaciones_a_documentos(
                actuaciones,
                expediente_data,
                expediente_numero
            )

            logger.info(f"   ✅ {len(documentos)} documentos creados")

            # Chunking de documentos
            all_chunks = []
            for doc in documentos:
                chunks = self.chunker.chunk_document(doc)
                all_chunks.extend(chunks)

            logger.info(f"   ✂️ {len(all_chunks)} chunks generados")

            # Enriquecer metadata
            for chunk in all_chunks:
                metadata_enriquecida = self.enricher.enrich_chunk(chunk)
                # Agregar metadata enriquecida al chunk
                chunk.metadata.update({
                    "personas": metadata_enriquecida.personas,
                    "organizaciones": metadata_enriquecida.organizaciones,
                    "normativa_citada": metadata_enriquecida.normativa_citada,
                    "montos": metadata_enriquecida.montos,
                    "plazos": metadata_enriquecida.plazos,
                })

            logger.info(f"   🧠 Metadata enriquecida")

            # Indexar chunks
            self.search_service.index_chunks(all_chunks)

            logger.info(f"✅ Expediente {expediente_numero} indexado exitosamente")

            return {
                "success": True,
                "expediente": expediente_numero,
                "actuaciones_procesadas": len(actuaciones),
                "documentos_creados": len(documentos),
                "chunks_indexados": len(all_chunks),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Error indexando expediente {expediente_numero}: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "expediente": expediente_numero
            }

    def _convertir_actuaciones_a_documentos(
        self,
        actuaciones: List[Dict[str, Any]],
        expediente_data: Dict[str, Any],
        expediente_numero: str
    ) -> List[LegalDocument]:
        """
        Convertir lista de actuaciones a LegalDocuments

        Args:
            actuaciones: Lista de actuaciones del JSON
            expediente_data: Metadata del expediente
            expediente_numero: Número del expediente

        Returns:
            Lista de LegalDocuments
        """
        documentos = []
        pdfs_procesados = 0
        pdfs_con_texto = 0

        for idx, act in enumerate(actuaciones):
            # Extraer datos de la actuación
            fecha_str = act.get("Fecha", act.get("fecha", ""))
            tipo = act.get("Tipo", act.get("tipo", "Actuación"))
            detalle = act.get("Detalle", act.get("detalle", ""))
            oficina = act.get("Oficina", act.get("oficina", ""))
            indice = act.get("Indice", act.get("indice", idx + 1))
            tiene_archivo = act.get("TieneArchivo", act.get("tiene_archivo", False))
            nombre_archivo = act.get("NombreArchivo", act.get("nombre_archivo", ""))

            # Parsear fecha
            fecha = None
            if fecha_str:
                try:
                    # Intentar varios formatos de fecha
                    for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]:
                        try:
                            fecha = datetime.strptime(fecha_str, fmt)
                            break
                        except ValueError:
                            continue
                except Exception as e:
                    logger.warning(f"No se pudo parsear fecha '{fecha_str}': {e}")

            # Extraer texto del PDF si existe
            texto_pdf = ""
            if tiene_archivo and nombre_archivo:
                ruta_pdf = self._construir_ruta_pdf(expediente_numero, nombre_archivo)
                if ruta_pdf and Path(ruta_pdf).exists():
                    pdfs_procesados += 1
                    try:
                        texto_estructurado = self.extractor_texto.extraer_y_estructurar(str(ruta_pdf))
                        if texto_estructurado and texto_estructurado.texto_normalizado:
                            texto_pdf = texto_estructurado.texto_normalizado
                            pdfs_con_texto += 1
                    except Exception as e:
                        logger.warning(f"Error extrayendo texto de {ruta_pdf}: {e}")

            # Construir contenido combinado (metadata + contenido extraído)
            contenido_partes = []
            if tipo:
                contenido_partes.append(f"TIPO: {tipo}")
            if oficina:
                contenido_partes.append(f"OFICINA: {oficina}")
            if detalle:
                contenido_partes.append(f"DETALLE: {detalle}")

            # Agregar contenido extraído del PDF
            if texto_pdf:
                contenido_partes.append(f"\nCONTENIDO DEL DOCUMENTO:\n{texto_pdf}")

            contenido = "\n".join(contenido_partes)

            # Crear LegalDocument
            doc = LegalDocument(
                doc_id=f"actuacion_{expediente_numero.replace('/', '_')}_{indice}",
                expediente_numero=expediente_numero,
                actuacion_id=indice,
                tipo=tipo or "Actuación",
                fecha=fecha or datetime.now(),
                contenido=contenido,
                metadata={
                    "expediente_numero": expediente_numero,
                    "caratula": expediente_data.get("Caratula", expediente_data.get("caratula", "")),
                    "dependencia": expediente_data.get("Dependencia", expediente_data.get("dependencia", "")),
                    "situacion": expediente_data.get("Situacion", expediente_data.get("situacion", "")),
                    "oficina": oficina,
                    "foja": act.get("Foja", act.get("foja")),
                    "tiene_archivo": tiene_archivo,
                    "tiene_texto_extraido": bool(texto_pdf),
                    "tipo_actuacion": tipo,
                    "fecha_actuacion": fecha.isoformat() if fecha else None,
                }
            )

            documentos.append(doc)

        logger.info(f"   📄 PDFs procesados: {pdfs_procesados}, con texto: {pdfs_con_texto}")
        return documentos

    def _construir_ruta_pdf(self, expediente_numero: str, nombre_archivo: str) -> Optional[str]:
        """
        Construir ruta al PDF basándose en la estructura de directorios

        Args:
            expediente_numero: Número del expediente (ej: "FRE 004542/2021")
            nombre_archivo: Nombre del archivo PDF

        Returns:
            Ruta completa al PDF o None si no existe
        """
        if not nombre_archivo:
            return None

        # Normalizar número de expediente para buscar carpeta
        numero_normalizado = expediente_numero.replace("/", "_").replace(" ", "_")

        # Buscar en estructura: data/expedientes/{carpeta}/actuaciones/{nombre}.pdf
        if self.expedientes_base_dir.exists():
            for carpeta in self.expedientes_base_dir.iterdir():
                if not carpeta.is_dir():
                    continue
                # La carpeta puede tener prefijo numérico (ej: 000001_FRE_004542_2021)
                if numero_normalizado in carpeta.name:
                    ruta_pdf = carpeta / "actuaciones" / nombre_archivo
                    if ruta_pdf.exists():
                        return str(ruta_pdf)

        return None

    def reindexar_todos_expedientes(
        self,
        directorio_base: Path | str,
        limite: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Reindexar todos los expedientes encontrados en el directorio base

        Args:
            directorio_base: Directorio raíz donde están los expedientes
            limite: Límite de expedientes a procesar (None = todos)

        Returns:
            Dict con estadísticas de reindexación
        """
        try:
            directorio_base = Path(directorio_base)
            logger.info(f"🔄 Iniciando reindexación desde {directorio_base}")

            # Buscar todos los JSONs de actuaciones
            archivos_json = list(directorio_base.rglob("actuaciones-*.json"))

            if limite:
                archivos_json = archivos_json[:limite]

            logger.info(f"   📂 {len(archivos_json)} archivos JSON encontrados")

            exitosos = 0
            errores = 0
            total_chunks = 0

            for idx, json_path in enumerate(archivos_json, 1):
                logger.info(f"\n[{idx}/{len(archivos_json)}] Procesando {json_path.name}...")

                # Extraer número de expediente del nombre del archivo
                # Formato: actuaciones-{numero_normalizado}.json
                nombre_archivo = json_path.stem  # Sin extensión
                numero_expediente = nombre_archivo.replace("actuaciones-", "").replace("_", "/")

                resultado = self.indexar_expediente(
                    ruta_json=json_path,
                    expediente_numero=numero_expediente,
                    force=True
                )

                if resultado["success"]:
                    exitosos += 1
                    total_chunks += resultado.get("chunks_indexados", 0)
                else:
                    errores += 1

            logger.info(f"\n{'='*60}")
            logger.info(f"✅ REINDEXACIÓN COMPLETADA")
            logger.info(f"{'='*60}")
            logger.info(f"   Exitosos: {exitosos}")
            logger.info(f"   Errores: {errores}")
            logger.info(f"   Total chunks indexados: {total_chunks}")

            return {
                "success": True,
                "total_archivos": len(archivos_json),
                "exitosos": exitosos,
                "errores": errores,
                "total_chunks": total_chunks
            }

        except Exception as e:
            logger.error(f"❌ Error en reindexación masiva: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del sistema RAG"""
        return self.search_service.get_stats()
