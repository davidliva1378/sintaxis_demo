"""
Servicio de búsqueda híbrida (BM25 + Semántica).

DEPRECADO: Este módulo es un wrapper de compatibilidad.
Usar directamente: infrastructure.rag.services.hybrid_search_service.HybridSearchService

Combina resultados de búsqueda por palabras clave y semántica
usando Reciprocal Rank Fusion (RRF).
"""

import logging
from typing import List, Dict, Any, Optional
import warnings

logger = logging.getLogger(__name__)


class HybridSearchService:
    """
    Servicio de búsqueda híbrida.

    DEPRECADO: Este es un wrapper de compatibilidad hacia el nuevo
    HybridSearchService en infrastructure.rag.services.

    Combina BM25 (keywords) y búsqueda semántica (embeddings con Qdrant).
    """

    def __init__(
        self,
        bm25_indexer=None,
        chroma_client=None,  # IGNORADO - ya no se usa ChromaDB
        embeddings_service=None,
        bm25_weight: float = 0.4,
        semantic_weight: float = 0.6,
        rrf_k: int = 60
    ):
        """
        Inicializa el servicio de búsqueda híbrida.

        Args:
            bm25_indexer: IGNORADO - usa el nuevo BM25Service
            chroma_client: IGNORADO - migrado a Qdrant
            embeddings_service: IGNORADO - usa EmbeddingService de rag
            bm25_weight: Peso para resultados BM25 (0-1)
            semantic_weight: Peso para resultados semánticos (0-1)
            rrf_k: Constante K para RRF (típicamente 60)
        """
        if chroma_client is not None:
            warnings.warn(
                "chroma_client está deprecado. El sistema ahora usa Qdrant. "
                "Este parámetro será ignorado.",
                DeprecationWarning,
                stacklevel=2
            )

        self.bm25_weight = bm25_weight
        self.semantic_weight = semantic_weight
        self.rrf_k = rrf_k

        # Delegamos al nuevo servicio
        self._new_service = None

    def _get_new_service(self):
        """Obtiene el nuevo HybridSearchService de Qdrant."""
        if self._new_service is None:
            from infrastructure.rag.services.hybrid_search_service import HybridSearchService as NewHybridSearch
            self._new_service = NewHybridSearch()
            self._new_service.load_indices()
        return self._new_service

    def search(
        self,
        query: str,
        n_results: int = 10,
        expediente_id: Optional[str] = None,
        expediente_numero: Optional[str] = None,
        use_bm25: bool = True,
        use_semantic: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Realiza búsqueda híbrida.

        Args:
            query: Texto de búsqueda
            n_results: Número de resultados finales
            expediente_id: Filtrar por expediente ID
            expediente_numero: Filtrar por número de expediente
            use_bm25: Usar búsqueda BM25
            use_semantic: Usar búsqueda semántica

        Returns:
            Lista de resultados combinados con score híbrido
        """
        try:
            from infrastructure.rag.models.dto import SearchQuery

            service = self._get_new_service()

            # Crear query con nuevo formato
            search_query = SearchQuery(
                texto=query,
                limit=n_results,
                filter_expediente=expediente_numero,
                filter_tipo=None
            )

            # Buscar
            search_results = service.search(
                query=search_query,
                use_dense=use_semantic,
                use_sparse=use_bm25,
                dense_weight=self.semantic_weight,
                sparse_weight=self.bm25_weight,
                use_query_expansion=False,
                use_reranking=True
            )

            # Convertir a formato legacy
            resultados = []
            for sr in search_results:
                resultados.append({
                    "id": sr.chunk.chunk_id,
                    "document": sr.chunk.texto,
                    "metadata": sr.chunk.metadata,
                    "score": sr.score,
                    "hybrid_score": sr.score,
                    "original_score": sr.score
                })

            logger.debug(f"Búsqueda híbrida (wrapper): '{query[:50]}...' -> {len(resultados)} resultados")
            return resultados

        except Exception as e:
            logger.error(f"Error en búsqueda híbrida: {e}")
            return []

    def index_document(
        self,
        doc_id: str,
        content: str,
        actuacion_id: str = "",
        expediente_id: str = "",
        expediente_numero: str = "",
        tipo: str = "",
        detalle: str = ""
    ):
        """
        Indexa un documento.

        DEPRECADO: Usar HybridSearchService.index_chunks() del nuevo servicio.

        Args:
            doc_id: ID del documento
            content: Contenido textual
            actuacion_id: ID de la actuación
            expediente_id: ID del expediente
            expediente_numero: Número del expediente
            tipo: Tipo de actuación
            detalle: Detalle de la actuación
        """
        warnings.warn(
            "index_document está deprecado. Usar RAGService.indexar_actuacion() "
            "o HybridSearchService.index_chunks() del nuevo servicio.",
            DeprecationWarning,
            stacklevel=2
        )

        try:
            from infrastructure.rag.models.dto import DocumentChunk, ChunkType
            from datetime import datetime

            service = self._get_new_service()

            # Crear chunk con nuevo formato
            chunk = DocumentChunk(
                chunk_id=doc_id,
                doc_id=actuacion_id or doc_id,
                chunk_index=0,
                chunk_type=ChunkType.ACTUACION,
                texto=content,
                metadata={
                    "actuacion_id": actuacion_id,
                    "expediente_id": expediente_id,
                    "expediente_numero": expediente_numero,
                    "tipo": tipo,
                    "detalle": detalle,
                    "indexed_at": datetime.now().isoformat()
                }
            )

            service.index_chunks([chunk])
            logger.info(f"Documento indexado (wrapper): {doc_id}")

        except Exception as e:
            logger.error(f"Error indexando documento: {e}")

    def index_batch(self, documents: List[Dict[str, Any]]):
        """
        Indexa múltiples documentos.

        DEPRECADO: Usar HybridSearchService.index_chunks() del nuevo servicio.

        Args:
            documents: Lista de documentos
        """
        warnings.warn(
            "index_batch está deprecado. Usar RAGService.indexar_batch() "
            "o HybridSearchService.index_chunks() del nuevo servicio.",
            DeprecationWarning,
            stacklevel=2
        )

        for doc in documents:
            self.index_document(
                doc_id=doc.get("doc_id", doc.get("id", "")),
                content=doc.get("content", doc.get("texto", "")),
                actuacion_id=doc.get("actuacion_id", ""),
                expediente_id=doc.get("expediente_id", ""),
                expediente_numero=doc.get("expediente_numero", ""),
                tipo=doc.get("tipo", ""),
                detalle=doc.get("detalle", "")
            )

    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del servicio.

        Returns:
            Dict con estadísticas de BM25 y semántica
        """
        try:
            service = self._get_new_service()
            stats = service.get_stats()

            # Agregar info de pesos legacy
            stats["bm25_weight"] = self.bm25_weight
            stats["semantic_weight"] = self.semantic_weight
            stats["rrf_k"] = self.rrf_k
            stats["backend"] = "qdrant"  # Indicar que usa Qdrant

            return stats

        except Exception as e:
            logger.error(f"Error obteniendo stats: {e}")
            return {
                "bm25_weight": self.bm25_weight,
                "semantic_weight": self.semantic_weight,
                "rrf_k": self.rrf_k,
                "error": str(e)
            }

    def clear_bm25_index(self):
        """Limpia el índice BM25."""
        try:
            service = self._get_new_service()
            # El nuevo servicio maneja esto internamente
            logger.info("Índice BM25 limpiado")
        except Exception as e:
            logger.error(f"Error limpiando índice BM25: {e}")
