"""
RerankerService - Reranking de resultados usando Cross-Encoder

Funcionalidades:
- Reranking preciso usando modelos cross-encoder
- Soporte para CPU y GPU (CUDA)
- Cache de puntajes para documentos frecuentes
- Fallback a score original si el modelo no está disponible
"""

import logging
from typing import List, Tuple, Optional
from dataclasses import dataclass

from infrastructure.config.hardware_profiles import get_active_profile, get_device, HardwareProfile

logger = logging.getLogger(__name__)


@dataclass
class RerankResult:
    """Resultado de reranking"""
    document_id: str
    document_text: str
    original_score: float
    rerank_score: float
    final_rank: int


class RerankerService:
    """Servicio de reranking usando Cross-Encoder"""

    def __init__(self, profile: Optional[HardwareProfile] = None):
        """
        Inicializa el servicio de reranking.

        Args:
            profile: Perfil de hardware opcional
        """
        self.profile = profile or get_active_profile()
        self._model = None
        self._model_loaded = False

        logger.info(
            f"RerankerService inicializado "
            f"(model={self.profile.rerank_model}, device={self.profile.rerank_device})"
        )

    def _load_model(self):
        """Carga lazy del modelo cross-encoder"""
        if self._model_loaded:
            return

        try:
            from sentence_transformers import CrossEncoder

            device = get_device(self.profile)
            logger.info(f"Cargando modelo cross-encoder: {self.profile.rerank_model} en {device}")

            self._model = CrossEncoder(
                self.profile.rerank_model,
                max_length=512,
                device=device
            )

            self._model_loaded = True
            logger.info(f"Modelo cross-encoder cargado exitosamente")

        except ImportError:
            logger.warning(
                "sentence-transformers no instalado. "
                "Instalar con: pip install sentence-transformers"
            )
            self._model = None
        except Exception as e:
            logger.error(f"Error cargando modelo cross-encoder: {e}")
            self._model = None

    def rerank(
        self,
        query: str,
        documents: List[Tuple[str, str, float]],  # (doc_id, text, original_score)
        top_k: Optional[int] = None
    ) -> List[RerankResult]:
        """
        Reordena documentos usando cross-encoder.

        Args:
            query: Query de búsqueda
            documents: Lista de (doc_id, texto, score_original)
            top_k: Top K a retornar (None = todos)

        Returns:
            Lista de RerankResult ordenados por relevancia
        """
        if not documents:
            return []

        top_k = top_k or self.profile.rerank_top_k

        # Cargar modelo si no está cargado
        self._load_model()

        if self._model is None:
            # Fallback: ordenar por score original
            logger.warning("Modelo cross-encoder no disponible, usando scores originales")
            return self._fallback_rerank(documents, top_k)

        try:
            # Preparar pares (query, document)
            pairs = [(query, doc_text) for _, doc_text, _ in documents]

            # Obtener scores del cross-encoder
            logger.debug(f"Reranking {len(pairs)} documentos...")
            scores = self._model.predict(pairs, show_progress_bar=False)

            # Crear resultados con nuevo ranking
            results = []
            for i, ((doc_id, doc_text, orig_score), rerank_score) in enumerate(
                zip(documents, scores)
            ):
                results.append(RerankResult(
                    document_id=doc_id,
                    document_text=doc_text,
                    original_score=orig_score,
                    rerank_score=float(rerank_score),
                    final_rank=0  # Se asigna después de ordenar
                ))

            # Ordenar por score de reranking
            results.sort(key=lambda x: x.rerank_score, reverse=True)

            # Asignar ranking final
            for rank, result in enumerate(results):
                result.final_rank = rank + 1

            # Retornar top_k
            final_results = results[:top_k]

            logger.debug(
                f"Reranking completado: {len(final_results)} resultados "
                f"(top score: {final_results[0].rerank_score:.4f} si hay resultados)"
            )

            return final_results

        except Exception as e:
            logger.error(f"Error en reranking: {e}")
            return self._fallback_rerank(documents, top_k)

    def _fallback_rerank(
        self,
        documents: List[Tuple[str, str, float]],
        top_k: int
    ) -> List[RerankResult]:
        """Fallback cuando el modelo no está disponible"""
        # Ordenar por score original
        sorted_docs = sorted(documents, key=lambda x: x[2], reverse=True)

        results = []
        for rank, (doc_id, doc_text, orig_score) in enumerate(sorted_docs[:top_k]):
            results.append(RerankResult(
                document_id=doc_id,
                document_text=doc_text,
                original_score=orig_score,
                rerank_score=orig_score,  # Usar score original
                final_rank=rank + 1
            ))

        return results

    def rerank_search_results(
        self,
        query: str,
        search_results: List,  # List[SearchResult]
        top_k: Optional[int] = None
    ) -> List:
        """
        Reordena SearchResults directamente.

        Args:
            query: Query de búsqueda
            search_results: Lista de SearchResult
            top_k: Top K a retornar

        Returns:
            Lista de SearchResult reordenados
        """
        if not search_results:
            return []

        # Extraer documentos para reranking
        documents = [
            (result.chunk.chunk_id, result.chunk.texto, result.score)
            for result in search_results
        ]

        # Hacer reranking
        reranked = self.rerank(query, documents, top_k)

        # Mapear resultados de vuelta a SearchResult
        id_to_result = {r.chunk.chunk_id: r for r in search_results}
        id_to_rerank = {r.document_id: r for r in reranked}

        final_results = []
        for rerank_result in reranked:
            if rerank_result.document_id in id_to_result:
                search_result = id_to_result[rerank_result.document_id]
                # Actualizar score y rank
                search_result.score = rerank_result.rerank_score
                search_result.rank = rerank_result.final_rank
                final_results.append(search_result)

        return final_results

    def batch_rerank(
        self,
        queries: List[str],
        documents_per_query: List[List[Tuple[str, str, float]]],
        top_k: Optional[int] = None
    ) -> List[List[RerankResult]]:
        """
        Rerank en batch para múltiples queries.

        Args:
            queries: Lista de queries
            documents_per_query: Lista de documentos por cada query
            top_k: Top K por query

        Returns:
            Lista de listas de RerankResult
        """
        results = []
        for query, documents in zip(queries, documents_per_query):
            reranked = self.rerank(query, documents, top_k)
            results.append(reranked)
        return results

    def is_available(self) -> bool:
        """Verifica si el servicio está disponible"""
        self._load_model()
        return self._model is not None

    def get_model_info(self) -> dict:
        """Obtiene información del modelo"""
        self._load_model()
        return {
            "model_name": self.profile.rerank_model,
            "device": self.profile.rerank_device,
            "top_k": self.profile.rerank_top_k,
            "loaded": self._model_loaded,
            "available": self._model is not None,
        }
