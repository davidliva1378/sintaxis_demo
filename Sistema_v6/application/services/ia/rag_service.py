"""
Servicio RAG (Retrieval Augmented Generation) para actuaciones.

Permite indexar actuaciones y realizar búsquedas semánticas
para encontrar información relevante en el expediente.

MIGRADO A QDRANT - Usa exclusivamente los servicios de infrastructure/rag/
"""

import logging
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RAGService:
    """
    Servicio para búsqueda semántica y generación aumentada.

    Usa Qdrant para búsqueda vectorial + BM25 para búsqueda híbrida.
    """

    def __init__(
        self,
        embeddings_service=None,
        qdrant_service=None,
        llm_service=None,
        hybrid_search_service=None,
        collection_name: str = "actuaciones"
    ):
        """
        Inicializa el servicio RAG.

        Args:
            embeddings_service: Servicio de embeddings (usa EmbeddingService de rag si None)
            qdrant_service: Servicio Qdrant (crea uno nuevo si None)
            llm_service: Servicio LLM
            hybrid_search_service: Servicio de búsqueda híbrida
            collection_name: Nombre de la colección
        """
        self._embeddings = embeddings_service
        self._qdrant = qdrant_service
        self._llm = llm_service
        self._hybrid_search = hybrid_search_service
        self.collection_name = collection_name

        # Cache para consultas frecuentes (TTL: 1 hora)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = timedelta(hours=1)

    def _get_embeddings(self):
        """Obtiene servicio de embeddings (lazy loading)."""
        if self._embeddings is None:
            try:
                from infrastructure.rag.services.embedding_service import EmbeddingService
                self._embeddings = EmbeddingService()
            except Exception as e:
                logger.warning(f"No se pudo cargar EmbeddingService de rag, usando legacy: {e}")
                from .embeddings_service import EmbeddingsService
                self._embeddings = EmbeddingsService()
        return self._embeddings

    def _get_qdrant(self):
        """Obtiene servicio Qdrant (lazy loading)."""
        if self._qdrant is None:
            from infrastructure.rag.services.qdrant_service import QdrantService
            self._qdrant = QdrantService()
            self._qdrant.connect()
            self._qdrant.ensure_collection_exists()
        return self._qdrant

    def _get_llm(self):
        """Obtiene servicio LLM (lazy loading)."""
        if self._llm is None:
            from .llm_service import LLMService
            self._llm = LLMService()
        return self._llm

    def _get_hybrid_search(self):
        """Obtiene servicio de búsqueda híbrida (lazy loading)."""
        if self._hybrid_search is None:
            from infrastructure.rag.services.hybrid_search_service import HybridSearchService
            self._hybrid_search = HybridSearchService()
            self._hybrid_search.load_indices()
        return self._hybrid_search

    def _cache_key(self, query: str, n_results: int, expediente_id: str = None, expediente_numero: str = None) -> str:
        """Genera clave de cache para una consulta."""
        key_data = f"{query}|{n_results}|{expediente_id or ''}|{expediente_numero or ''}"
        return hashlib.md5(key_data.encode('utf-8')).hexdigest()

    def _cache_get(self, key: str) -> Optional[List[Dict[str, Any]]]:
        """Obtiene resultado del cache si existe y no expiró."""
        if key in self._cache:
            cached = self._cache[key]
            if datetime.now() - cached['timestamp'] < self._cache_ttl:
                logger.debug(f"Cache hit: {key[:8]}...")
                return cached['results']
            else:
                del self._cache[key]
        return None

    def _cache_set(self, key: str, results: List[Dict[str, Any]]):
        """Guarda resultado en cache."""
        self._cache[key] = {
            'results': results,
            'timestamp': datetime.now()
        }
        if len(self._cache) > 100:
            self._cache_cleanup()

    def _cache_cleanup(self):
        """Elimina entradas expiradas del cache."""
        now = datetime.now()
        expired = [
            key for key, value in self._cache.items()
            if now - value['timestamp'] >= self._cache_ttl
        ]
        for key in expired:
            del self._cache[key]

    def limpiar_cache(self):
        """Limpia todo el cache de consultas."""
        self._cache.clear()
        logger.info("Cache de consultas limpiado")

    def indexar_actuacion(
        self,
        id_actuacion: str,
        texto: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Indexa una actuación individual en Qdrant + BM25.

        Args:
            id_actuacion: ID único de la actuación
            texto: Contenido textual
            metadata: Metadatos adicionales
        """
        if not texto or len(texto.strip()) < 10:
            logger.warning(f"Texto muy corto para indexar: {id_actuacion}")
            return

        try:
            from infrastructure.rag.models.dto import DocumentChunk, ChunkType

            embeddings_service = self._get_embeddings()
            hybrid = self._get_hybrid_search()

            # Generar chunks si el texto es largo
            chunk_size = 1000
            overlap = 150
            chunks_texto = self._chunk_text(texto, chunk_size, overlap)

            chunks = []
            for i, chunk_text in enumerate(chunks_texto):
                chunk_id = f"{id_actuacion}_chunk_{i}"

                chunk = DocumentChunk(
                    chunk_id=chunk_id,
                    doc_id=id_actuacion,
                    chunk_index=i,
                    chunk_type=ChunkType.FULL,
                    texto=chunk_text,
                    metadata={
                        "actuacion_id": id_actuacion,
                        "chunk_index": i,
                        "total_chunks": len(chunks_texto),
                        "indexed_at": datetime.now().isoformat(),
                        **(metadata or {})
                    }
                )
                chunks.append(chunk)

            # Indexar usando HybridSearchService (maneja Qdrant + BM25)
            hybrid.index_chunks(chunks)

            logger.info(
                f"Indexada actuación {id_actuacion}: "
                f"{len(chunks)} chunks (Qdrant + BM25)"
            )

        except Exception as e:
            logger.error(f"Error indexando actuación {id_actuacion}: {e}")
            raise

    def _chunk_text(self, texto: str, chunk_size: int = 1000, overlap: int = 150) -> List[str]:
        """Divide texto en chunks con overlap."""
        if len(texto) <= chunk_size:
            return [texto]

        chunks = []
        start = 0
        while start < len(texto):
            end = start + chunk_size
            chunk = texto[start:end]

            # Intentar cortar en espacio
            if end < len(texto):
                last_space = chunk.rfind(' ')
                if last_space > chunk_size // 2:
                    end = start + last_space
                    chunk = texto[start:end]

            chunks.append(chunk)
            start = end - overlap

        return chunks

    def indexar_batch(
        self,
        actuaciones: List[Dict[str, Any]],
        batch_size: int = 100
    ):
        """
        Indexa múltiples actuaciones.

        Args:
            actuaciones: Lista de actuaciones con id, texto y metadata
            batch_size: Tamaño del batch
        """
        total = len(actuaciones)
        indexadas = 0

        for actuacion in actuaciones:
            try:
                self.indexar_actuacion(
                    id_actuacion=str(actuacion.get("id", "")),
                    texto=actuacion.get("texto", ""),
                    metadata=actuacion.get("metadata", {})
                )
                indexadas += 1

                if indexadas % batch_size == 0:
                    logger.info(f"Progreso: {indexadas}/{total}")

            except Exception as e:
                logger.error(
                    f"Error indexando actuación {actuacion.get('id')}: {e}"
                )

        logger.info(f"Indexación completada: {indexadas}/{total}")

    def buscar(
        self,
        query: str,
        n_results: int = 5,
        filtros: Optional[Dict[str, Any]] = None,
        expediente_id: Optional[str] = None,
        expediente_numero: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca actuaciones relevantes usando Qdrant.

        Args:
            query: Texto de búsqueda
            n_results: Número de resultados
            filtros: Filtros adicionales de metadata
            expediente_id: Filtrar por ID de expediente
            expediente_numero: Filtrar por número de expediente

        Returns:
            Lista de resultados con documento, metadata y score
        """
        # Verificar cache
        if not filtros:
            cache_key = self._cache_key(query, n_results, expediente_id, expediente_numero)
            cached_results = self._cache_get(cache_key)
            if cached_results is not None:
                return cached_results

        try:
            embeddings_service = self._get_embeddings()
            qdrant = self._get_qdrant()

            # Generar embedding de la query
            if hasattr(embeddings_service, 'encode_text'):
                query_vector = embeddings_service.encode_text(query)
            else:
                query_vector = embeddings_service.encode(query)

            # Construir filtros
            filter_dict = {}
            if expediente_id:
                filter_dict["expediente_id"] = expediente_id
            if expediente_numero:
                filter_dict["expediente_numero"] = expediente_numero
            if filtros:
                filter_dict.update(filtros)

            # Buscar en Qdrant
            results = qdrant.search_similar(
                query_vector=query_vector,
                limit=n_results,
                filter_dict=filter_dict if filter_dict else None
            )

            # Convertir a formato estándar
            resultados = []
            for result in results:
                payload = result.payload if hasattr(result, 'payload') else {}
                resultados.append({
                    "id": payload.get("chunk_id", ""),
                    "document": payload.get("texto", ""),
                    "metadata": {k: v for k, v in payload.items() if k != "texto"},
                    "score": result.score if hasattr(result, 'score') else 0.0
                })

            # Guardar en cache
            if not filtros:
                self._cache_set(cache_key, resultados)

            return resultados

        except Exception as e:
            logger.error(f"Error en búsqueda: {e}")
            return []

    def buscar_hibrido(
        self,
        query: str,
        n_results: int = 5,
        expediente_id: Optional[str] = None,
        expediente_numero: Optional[str] = None,
        use_bm25: bool = True,
        use_semantic: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Busca actuaciones usando búsqueda híbrida (BM25 + Semántica con Qdrant).

        Combina resultados de búsqueda por palabras clave y semántica
        usando Reciprocal Rank Fusion (RRF) para mejores resultados.

        Args:
            query: Texto de búsqueda
            n_results: Número de resultados
            expediente_id: Filtrar por ID de expediente
            expediente_numero: Filtrar por número de expediente
            use_bm25: Usar búsqueda BM25 (keywords)
            use_semantic: Usar búsqueda semántica (embeddings)

        Returns:
            Lista de resultados con documento, metadata y score híbrido
        """
        # Verificar cache
        cache_key = self._cache_key(f"hybrid:{query}", n_results, expediente_id, expediente_numero)
        cached_results = self._cache_get(cache_key)
        if cached_results is not None:
            return cached_results

        try:
            from infrastructure.rag.models.dto import SearchQuery

            hybrid = self._get_hybrid_search()

            # Crear query
            search_query = SearchQuery(
                texto=query,
                limit=n_results,
                filter_expediente=expediente_numero,
                filter_tipo=None
            )

            # Buscar
            search_results = hybrid.search(
                query=search_query,
                use_dense=use_semantic,
                use_sparse=use_bm25,
                use_query_expansion=False,  # Desactivar por defecto para rapidez
                use_reranking=True
            )

            # Convertir a formato estándar
            resultados = []
            for sr in search_results:
                resultados.append({
                    "id": sr.chunk.chunk_id,
                    "document": sr.chunk.texto,
                    "metadata": sr.chunk.metadata,
                    "score": sr.score,
                    "hybrid_score": sr.score,
                    "rank": sr.rank,
                    "highlights": sr.highlights
                })

            # Guardar en cache
            self._cache_set(cache_key, resultados)

            logger.info(
                f"Búsqueda híbrida: '{query[:50]}...' -> {len(resultados)} resultados"
            )
            return resultados

        except Exception as e:
            logger.error(f"Error en búsqueda híbrida: {e}")
            # Fallback a búsqueda semántica simple
            return self.buscar(
                query=query,
                n_results=n_results,
                expediente_id=expediente_id,
                expediente_numero=expediente_numero
            )

    def responder(
        self,
        pregunta: str,
        n_contextos: int = 5,
        expediente_id: Optional[str] = None,
        expediente_numero: Optional[str] = None,
        incluir_fuentes: bool = True
    ) -> Dict[str, Any]:
        """
        Responde una pregunta usando RAG.
        
        Delegates to LLMService for advanced prompt generation (CoT, dynamic prompts).
        """
        try:
            from infrastructure.rag.models.dto import SearchQuery
            
            # 1. Buscar contextos (objetos SearchResult)
            hybrid = self._get_hybrid_search()
            search_query = SearchQuery(
                texto=pregunta,
                limit=n_contextos,
                filter_expediente=expediente_numero,
                filter_tipo=None
            )
            
            # Usar búsqueda híbrida
            resultados = hybrid.search(
                query=search_query,
                use_dense=True,
                use_sparse=True,
                use_reranking=True
            )
            
            if not resultados:
                return {
                    "respuesta": "No encontré información relevante para responder esta pregunta.",
                    "fuentes": [],
                    "confianza": 0.0
                }
            
            # 2. Generar respuesta con LLMService (usa CoT y prompts dinámicos)
            llm = self._get_llm()
            rag_response = llm.generate_answer(
                question=pregunta,
                search_results=resultados,
                num_chunks=n_contextos
            )
            
            # 3. Formatear respuesta
            resultado = {
                "respuesta": rag_response.respuesta,
                "confianza": sum(r.score for r in resultados) / len(resultados) if resultados else 0.0
            }
            
            if incluir_fuentes:
                resultado["fuentes"] = [
                    {
                        "id": r.chunk.chunk_id,
                        "fragmento": r.chunk.texto[:200] + "..." if len(r.chunk.texto) > 200 else r.chunk.texto,
                        "score": r.score,
                        "metadata": r.chunk.metadata
                    }
                    for r in resultados
                ]
                
            return resultado
            
        except Exception as e:
            logger.error(f"Error generando respuesta: {e}")
            return {
                "respuesta": f"Error al generar respuesta: {str(e)}",
                "fuentes": [],
                "confianza": 0.0
            }

    def resumir_expediente(
        self,
        expediente_id: Optional[str] = None,
        expediente_numero: Optional[str] = None,
        max_length: int = 500
    ) -> str:
        """
        Genera un resumen del expediente.

        Args:
            expediente_id: ID del expediente
            expediente_numero: Número del expediente
            max_length: Longitud máxima del resumen

        Returns:
            Resumen del expediente
        """
        # Buscar todas las actuaciones del expediente
        contextos = self.buscar_hibrido(
            query="resumen del caso partes demanda resolución",
            n_results=10,
            expediente_id=expediente_id,
            expediente_numero=expediente_numero
        )

        if not contextos:
            return "No hay información suficiente para generar un resumen."

        llm = self._get_llm()
        
        # Concatenar textos
        contexto_texto = "\n\n".join([c["document"] for c in contextos])
        
        # Usar nuevo método summarize
        return llm.summarize(contexto_texto, max_length=max_length)

    def eliminar_actuacion(self, id_actuacion: str):
        """
        Elimina una actuación del índice Qdrant.

        Args:
            id_actuacion: ID de la actuación
        """
        try:
            qdrant = self._get_qdrant()
            deleted = qdrant.delete_by_doc_id(id_actuacion)
            logger.info(f"Eliminada actuación del índice: {id_actuacion} ({deleted} chunks)")
        except Exception as e:
            logger.error(f"Error eliminando actuación {id_actuacion}: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del índice.

        Returns:
            Dict con estadísticas
        """
        try:
            hybrid = self._get_hybrid_search()
            stats = hybrid.get_stats()
            stats["collection"] = self.collection_name
            return stats
        except Exception as e:
            logger.error(f"Error obteniendo stats: {e}")
            return {
                "collection": self.collection_name,
                "error": str(e)
            }

    def limpiar_indice(self):
        """
        Elimina todos los documentos del índice.
        """
        try:
            qdrant = self._get_qdrant()
            qdrant.clear_collection()
            logger.warning(f"Índice {self.collection_name} eliminado")
        except Exception as e:
            logger.error(f"Error limpiando índice: {e}")
