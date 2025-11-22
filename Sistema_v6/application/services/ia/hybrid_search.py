"""
Servicio de búsqueda híbrida (BM25 + Semántica).

Combina resultados de búsqueda por palabras clave y semántica
usando Reciprocal Rank Fusion (RRF).
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class HybridSearchService:
    """
    Servicio de búsqueda híbrida.

    Combina BM25 (keywords) y búsqueda semántica (embeddings)
    para obtener mejores resultados.
    """

    def __init__(
        self,
        bm25_indexer=None,
        chroma_client=None,
        embeddings_service=None,
        bm25_weight: float = 0.4,
        semantic_weight: float = 0.6,
        rrf_k: int = 60
    ):
        """
        Inicializa el servicio de búsqueda híbrida.

        Args:
            bm25_indexer: Indexador BM25
            chroma_client: Cliente ChromaDB
            embeddings_service: Servicio de embeddings
            bm25_weight: Peso para resultados BM25 (0-1)
            semantic_weight: Peso para resultados semánticos (0-1)
            rrf_k: Constante K para RRF (típicamente 60)
        """
        self._bm25 = bm25_indexer
        self._chroma = chroma_client
        self._embeddings = embeddings_service
        self.bm25_weight = bm25_weight
        self.semantic_weight = semantic_weight
        self.rrf_k = rrf_k

    def _get_bm25(self):
        """Lazy loading del indexador BM25."""
        if self._bm25 is None:
            from infrastructure.vector_store.bm25_indexer import BM25Indexer
            self._bm25 = BM25Indexer()
        return self._bm25

    def _get_chroma(self):
        """Lazy loading del cliente ChromaDB."""
        if self._chroma is None:
            from infrastructure.vector_store.chroma_client import ChromaClient
            self._chroma = ChromaClient()
        return self._chroma

    def _get_embeddings(self):
        """Lazy loading del servicio de embeddings."""
        if self._embeddings is None:
            from .embeddings_service import EmbeddingsService
            self._embeddings = EmbeddingsService()
        return self._embeddings

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
        # Obtener más resultados de cada fuente para mejor fusión
        fetch_limit = n_results * 3

        bm25_results = []
        semantic_results = []

        # Búsqueda BM25
        if use_bm25:
            try:
                bm25 = self._get_bm25()
                bm25_results = bm25.search(
                    query=query,
                    n_results=fetch_limit,
                    expediente_id=expediente_id,
                    expediente_numero=expediente_numero
                )
                logger.debug(f"BM25 encontró {len(bm25_results)} resultados")
            except Exception as e:
                logger.error(f"Error en búsqueda BM25: {e}")

        # Búsqueda semántica
        if use_semantic:
            try:
                chroma = self._get_chroma()
                embeddings = self._get_embeddings()

                # Construir filtros
                where = {}
                if expediente_id:
                    where["expediente_id"] = expediente_id
                if expediente_numero:
                    where["expediente_numero"] = expediente_numero

                semantic_results = chroma.search(
                    query_text=query,
                    embeddings_service=embeddings,
                    n_results=fetch_limit,
                    where=where if where else None
                )
                logger.debug(f"Semántica encontró {len(semantic_results)} resultados")
            except Exception as e:
                logger.error(f"Error en búsqueda semántica: {e}")

        # Combinar resultados
        if not bm25_results and not semantic_results:
            return []

        if not use_bm25 or not bm25_results:
            return semantic_results[:n_results]

        if not use_semantic or not semantic_results:
            return bm25_results[:n_results]

        # Reciprocal Rank Fusion
        combined = self._rrf_combine(
            bm25_results,
            semantic_results,
            n_results
        )

        return combined

    def _rrf_combine(
        self,
        bm25_results: List[Dict[str, Any]],
        semantic_results: List[Dict[str, Any]],
        n_results: int
    ) -> List[Dict[str, Any]]:
        """
        Combina resultados usando Reciprocal Rank Fusion (RRF).

        RRF Score = sum(1 / (k + rank))

        Args:
            bm25_results: Resultados de BM25
            semantic_results: Resultados semánticos
            n_results: Número de resultados a retornar

        Returns:
            Lista combinada ordenada por score RRF
        """
        scores: Dict[str, float] = {}
        documents: Dict[str, Dict[str, Any]] = {}

        # Procesar resultados BM25
        for rank, result in enumerate(bm25_results):
            doc_id = result["id"]
            rrf_score = self.bm25_weight / (self.rrf_k + rank + 1)
            scores[doc_id] = scores.get(doc_id, 0) + rrf_score
            if doc_id not in documents:
                documents[doc_id] = result

        # Procesar resultados semánticos
        for rank, result in enumerate(semantic_results):
            doc_id = result["id"]
            rrf_score = self.semantic_weight / (self.rrf_k + rank + 1)
            scores[doc_id] = scores.get(doc_id, 0) + rrf_score
            if doc_id not in documents:
                documents[doc_id] = result

        # Ordenar por score RRF
        sorted_ids = sorted(
            scores.keys(),
            key=lambda x: scores[x],
            reverse=True
        )

        # Construir resultados finales
        results = []
        for doc_id in sorted_ids[:n_results]:
            doc = documents[doc_id].copy()
            doc["hybrid_score"] = scores[doc_id]
            doc["original_score"] = doc.get("score", 0)
            doc["score"] = scores[doc_id]  # Usar hybrid_score como score principal
            results.append(doc)

        logger.debug(f"RRF combinó {len(results)} resultados")
        return results

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
        Indexa un documento en BM25.

        Args:
            doc_id: ID del documento
            content: Contenido textual
            actuacion_id: ID de la actuación
            expediente_id: ID del expediente
            expediente_numero: Número del expediente
            tipo: Tipo de actuación
            detalle: Detalle de la actuación
        """
        bm25 = self._get_bm25()
        bm25.add(
            doc_id=doc_id,
            content=content,
            actuacion_id=actuacion_id,
            expediente_id=expediente_id,
            expediente_numero=expediente_numero,
            tipo=tipo,
            detalle=detalle
        )

    def index_batch(self, documents: List[Dict[str, Any]]):
        """
        Indexa múltiples documentos en BM25.

        Args:
            documents: Lista de documentos
        """
        bm25 = self._get_bm25()
        bm25.add_batch(documents)

    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del servicio.

        Returns:
            Dict con estadísticas de BM25 y semántica
        """
        stats = {
            "bm25_weight": self.bm25_weight,
            "semantic_weight": self.semantic_weight,
            "rrf_k": self.rrf_k
        }

        try:
            bm25 = self._get_bm25()
            stats["bm25"] = bm25.get_stats()
        except Exception as e:
            stats["bm25_error"] = str(e)

        try:
            chroma = self._get_chroma()
            stats["semantic"] = chroma.get_stats()
        except Exception as e:
            stats["semantic_error"] = str(e)

        return stats

    def clear_bm25_index(self):
        """Limpia el índice BM25."""
        bm25 = self._get_bm25()
        bm25.clear()
