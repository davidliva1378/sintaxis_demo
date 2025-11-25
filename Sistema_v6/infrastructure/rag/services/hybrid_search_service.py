"""
HybridSearchService - Servicio para búsqueda híbrida (Dense + Sparse)

Maneja:
- Búsqueda densa (vector similarity con Qdrant)
- Búsqueda sparse (keyword con BM25)
- Fusión de resultados (Reciprocal Rank Fusion)
- Query Expansion con LLM (NUEVO)
- Reranking con Cross-Encoder (NUEVO)
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from infrastructure.rag.config import get_rag_settings
from infrastructure.rag.models.dto import DocumentChunk, SearchResult, SearchQuery
from infrastructure.rag.services.qdrant_service import QdrantService
from infrastructure.rag.services.embedding_service import EmbeddingService
from infrastructure.rag.services.bm25_service import BM25Service

logger = logging.getLogger(__name__)


@dataclass
class HybridSearchResult:
    """Resultado de búsqueda híbrida con score combinado"""
    chunk_id: str
    chunk: DocumentChunk
    dense_score: float
    sparse_score: float
    combined_score: float
    rank: int


class HybridSearchService:
    """Servicio para búsqueda híbrida combinando dense y sparse"""

    def __init__(self):
        self.settings = get_rag_settings()

        # Servicios base
        self.qdrant = QdrantService()
        self.embedding = EmbeddingService()
        self.bm25 = BM25Service()

        # Servicios avanzados (lazy loading)
        self._query_expander = None
        self._reranker = None

        # Pesos para fusión (configurables)
        self.dense_weight = self.settings.dense_weight
        self.sparse_weight = self.settings.sparse_weight

    @property
    def query_expander(self):
        """Lazy loading del QueryExpansionService"""
        if self._query_expander is None:
            try:
                from infrastructure.rag.services.query_expansion_service import QueryExpansionService
                self._query_expander = QueryExpansionService()
            except Exception as e:
                logger.warning(f"QueryExpansionService no disponible: {e}")
        return self._query_expander

    @property
    def reranker(self):
        """Lazy loading del RerankerService"""
        if self._reranker is None:
            try:
                from infrastructure.rag.services.reranker_service import RerankerService
                self._reranker = RerankerService()
            except Exception as e:
                logger.warning(f"RerankerService no disponible: {e}")
        return self._reranker

    def search(
        self,
        query: SearchQuery,
        use_dense: bool = True,
        use_sparse: bool = True,
        dense_weight: Optional[float] = None,
        sparse_weight: Optional[float] = None,
        use_query_expansion: bool = True,
        use_reranking: bool = True,
    ) -> List[SearchResult]:
        """
        Realizar búsqueda híbrida

        Args:
            query: Query de búsqueda
            use_dense: Usar búsqueda vectorial
            use_sparse: Usar búsqueda BM25
            dense_weight: Peso para búsqueda vectorial (opcional)
            sparse_weight: Peso para búsqueda BM25 (opcional)
            use_query_expansion: Usar expansión de query con LLM
            use_reranking: Usar reranking con cross-encoder

        Returns:
            Lista de resultados ordenados por relevancia
        """
        try:
            # Usar pesos dinámicos o defaults de config
            current_dense_weight = dense_weight if dense_weight is not None else self.dense_weight
            current_sparse_weight = sparse_weight if sparse_weight is not None else self.sparse_weight

            logger.info(
                f"Búsqueda híbrida: '{query.texto}' "
                f"(dense={use_dense}, sparse={use_sparse}, "
                f"expansion={use_query_expansion}, rerank={use_reranking})"
            )

            # 0. Query Expansion (opcional)
            search_queries = [query.texto]
            if use_query_expansion and self.query_expander:
                try:
                    expanded = self.query_expander.expand(query.texto)
                    search_queries = expanded.variations[:3]  # Usar hasta 3 variaciones
                    logger.info(f"   Query expandida: {len(search_queries)} variaciones")
                except Exception as e:
                    logger.warning(f"Error en query expansion: {e}")

            # Preparar filtros
            filter_dict = {}
            if query.filter_expediente:
                filter_dict["expediente_numero"] = query.filter_expediente
            if query.filter_tipo:
                filter_dict["tipo_actuacion"] = query.filter_tipo

            # 1. Búsqueda densa (vectorial)
            dense_results = []
            if use_dense:
                dense_results = self._dense_search(
                    query.texto,
                    limit=query.limit * 2,  # Obtener más para fusión
                    filter_dict=filter_dict if filter_dict else None
                )
                logger.info(f"   Dense: {len(dense_results)} resultados")

            # 2. Búsqueda sparse (BM25)
            sparse_results = []
            if use_sparse:
                sparse_results = self._sparse_search(
                    query.texto,
                    top_k=query.limit * 2,  # Obtener más para fusión
                    filter_dict=filter_dict if filter_dict else None
                )
                logger.info(f"   Sparse: {len(sparse_results)} resultados")

            # 3. Fusión de resultados (Reciprocal Rank Fusion)
            if use_dense and use_sparse:
                fused_results = self._reciprocal_rank_fusion(
                    dense_results, sparse_results,
                    dense_weight=current_dense_weight,
                    sparse_weight=current_sparse_weight
                )
            elif use_dense:
                fused_results = [(chunk_id, score) for chunk_id, score in dense_results]
            elif use_sparse:
                fused_results = [(chunk_id, score) for chunk_id, score in sparse_results]
            else:
                logger.warning("Ningún modo de búsqueda activado")
                return []

            logger.info(f"   Fused: {len(fused_results)} resultados únicos")

            # 4. Convertir a SearchResult
            search_results = self._build_search_results(fused_results)

            # 5. Aplicar reranking con cross-encoder (usar query.limit del usuario)
            reranked = self._rerank(
                search_results,
                top_k=query.limit,
                query=query.texto,
                use_reranking=use_reranking
            )

            logger.info(f"✅ Retornando {len(reranked)} resultados finales")
            return reranked

        except Exception as e:
            logger.error(f"Error en búsqueda híbrida: {e}", exc_info=True)
            return []

    def _dense_search(
        self,
        query: str,
        limit: int,
        filter_dict: Optional[Dict[str, any]] = None
    ) -> List[Tuple[str, float]]:
        """Búsqueda vectorial densa con Qdrant"""
        try:
            # Generar embedding de la query
            query_vector = self.embedding.encode_text(query)

            # Buscar en Qdrant
            results = self.qdrant.search_similar(
                query_vector=query_vector,
                limit=limit,
                filter_dict=filter_dict
            )

            # Convertir a (chunk_id, score) - usar chunk_id del payload
            return [(result.payload.get("chunk_id"), result.score) for result in results]

        except Exception as e:
            logger.error(f"Error en búsqueda densa: {e}")
            return []

    def _sparse_search(
        self,
        query: str,
        top_k: int,
        filter_dict: Optional[Dict[str, any]] = None
    ) -> List[Tuple[str, float]]:
        """Búsqueda sparse con BM25"""
        try:
            results = self.bm25.search(
                query=query,
                top_k=top_k,
                filter_dict=filter_dict
            )
            return results

        except Exception as e:
            logger.error(f"Error en búsqueda sparse: {e}")
            return []

    def _reciprocal_rank_fusion(
        self,
        dense_results: List[Tuple[str, float]],
        sparse_results: List[Tuple[str, float]],
        k: int = 60,
        dense_weight: Optional[float] = None,
        sparse_weight: Optional[float] = None
    ) -> List[Tuple[str, float]]:
        """
        Fusión de resultados usando Reciprocal Rank Fusion (RRF)

        RRF Score = Σ 1 / (k + rank_i)

        Args:
            dense_results: Resultados de búsqueda densa
            sparse_results: Resultados de búsqueda sparse
            k: Constante para RRF (default: 60)
            dense_weight: Peso para búsqueda densa (opcional)
            sparse_weight: Peso para búsqueda sparse (opcional)

        Returns:
            Lista fusionada de (chunk_id, score)
        """
        # Usar pesos dinámicos o defaults
        use_dense_weight = dense_weight if dense_weight is not None else self.dense_weight
        use_sparse_weight = sparse_weight if sparse_weight is not None else self.sparse_weight

        # Crear diccionarios de rank
        dense_ranks = {chunk_id: rank for rank, (chunk_id, _) in enumerate(dense_results)}
        sparse_ranks = {chunk_id: rank for rank, (chunk_id, _) in enumerate(sparse_results)}

        # Obtener todos los chunk_ids únicos
        all_chunk_ids = set(dense_ranks.keys()) | set(sparse_ranks.keys())

        # Calcular RRF score
        rrf_scores = {}
        for chunk_id in all_chunk_ids:
            rrf_score = 0.0

            # Dense component
            if chunk_id in dense_ranks:
                rrf_score += use_dense_weight / (k + dense_ranks[chunk_id])

            # Sparse component
            if chunk_id in sparse_ranks:
                rrf_score += use_sparse_weight / (k + sparse_ranks[chunk_id])

            rrf_scores[chunk_id] = rrf_score

        # Ordenar por score descendente
        sorted_results = sorted(
            rrf_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_results

    def _build_search_results(
        self,
        fused_results: List[Tuple[str, float]]
    ) -> List[SearchResult]:
        """Convertir resultados fusionados a SearchResult"""
        search_results = []

        for rank, (chunk_id, score) in enumerate(fused_results):
            # Obtener chunk desde Qdrant
            chunk = self.qdrant.get_chunk_by_id(chunk_id)

            if chunk:
                search_result = SearchResult(
                    chunk=chunk,
                    score=score,
                    rank=rank + 1,
                    highlights=self._extract_highlights(chunk.texto, max_length=200)
                )
                search_results.append(search_result)
            else:
                logger.warning(f"Chunk {chunk_id} no encontrado en Qdrant")

        return search_results

    def _extract_highlights(self, text: str, max_length: int = 200) -> List[str]:
        """Extraer snippet del texto para mostrar como highlight"""
        # Tomar primeras palabras
        if len(text) <= max_length:
            return [text]

        # Cortar en espacio más cercano
        snippet = text[:max_length]
        last_space = snippet.rfind(' ')
        if last_space > 0:
            snippet = snippet[:last_space]

        return [snippet + "..."]

    def _rerank(
        self,
        results: List[SearchResult],
        top_k: int,
        query: str = "",
        use_reranking: bool = True
    ) -> List[SearchResult]:
        """
        Reranking usando cross-encoder o fallback a score

        Args:
            results: Resultados a reordenar
            top_k: Top K resultados a retornar
            query: Query original para cross-encoder
            use_reranking: Si usar cross-encoder

        Returns:
            Lista reordenada y limitada
        """
        if not use_reranking or not self.reranker or not query:
            # Fallback: ordenar por score y limitar
            return results[:top_k]

        try:
            # Usar cross-encoder para reranking
            reranked = self.reranker.rerank_search_results(
                query=query,
                search_results=results,
                top_k=top_k
            )
            logger.info(f"   Reranking completado: {len(reranked)} resultados")
            return reranked
        except Exception as e:
            logger.warning(f"Error en reranking, usando fallback: {e}")
            return results[:top_k]

    def index_chunks(self, chunks: List[DocumentChunk]) -> None:
        """
        Indexar chunks en ambos índices (Qdrant + BM25)

        Args:
            chunks: Chunks a indexar
        """
        try:
            logger.info(f"Indexando {len(chunks)} chunks...")

            # 1. Generar embeddings
            logger.info("   Generando embeddings...")
            texts = [chunk.texto for chunk in chunks]
            embeddings = self.embedding.encode_batch(texts, show_progress=True)

            # Asignar embeddings a chunks
            for chunk, embedding in zip(chunks, embeddings):
                chunk.dense_vector = embedding

            # 2. Indexar en Qdrant
            logger.info("   Indexando en Qdrant...")
            self.qdrant.upsert_chunks(chunks)

            # 3. Indexar en BM25
            logger.info("   Indexando en BM25...")
            self.bm25.build_index(chunks)
            self.bm25.save_index()

            logger.info(f"✅ {len(chunks)} chunks indexados exitosamente")

        except Exception as e:
            logger.error(f"Error al indexar chunks: {e}")
            raise

    def load_indices(self) -> bool:
        """
        Cargar índices desde disco

        Returns:
            True si se cargaron exitosamente
        """
        try:
            # Conectar a Qdrant
            self.qdrant.connect()

            # Verificar que existe la colección, si no existe, crearla
            if not self.qdrant.collection_exists():
                logger.warning("Colección de Qdrant no existe, creando automáticamente...")
                self.qdrant.create_collection(recreate=False)
                logger.info("✅ Colección de Qdrant creada exitosamente")

            # Cargar índice BM25 (si no existe, se creará al indexar)
            if not self.bm25.load_index():
                logger.warning("Índice BM25 no existe, se creará al indexar")

            logger.info("✅ Índices cargados/inicializados exitosamente")
            return True

        except Exception as e:
            logger.error(f"Error al cargar índices: {e}")
            return False

    def get_stats(self) -> Dict[str, any]:
        """Obtener estadísticas de los índices"""
        return {
            "qdrant": {
                "collection": self.qdrant.collection_name,
                "count": self.qdrant.count_points(),
            },
            "bm25": self.bm25.get_stats(),
            "weights": {
                "dense": self.dense_weight,
                "sparse": self.sparse_weight,
            }
        }
