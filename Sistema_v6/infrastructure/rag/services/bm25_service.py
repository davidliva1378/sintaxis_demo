"""
BM25Service - Servicio para búsqueda sparse con BM25

Maneja:
- Indexación de documentos con BM25
- Búsqueda por keywords
- Persistencia del índice en disco
- Tokenización en español
"""

import logging
import pickle
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from rank_bm25 import BM25Okapi
import re

from infrastructure.rag.config import get_rag_settings
from infrastructure.rag.models.dto import DocumentChunk

logger = logging.getLogger(__name__)


class BM25Service:
    """Servicio para búsqueda sparse usando BM25"""

    def __init__(self, index_name: str = "actuaciones"):
        self.settings = get_rag_settings()
        self.index_name = index_name
        self.index_path = self.settings.bm25_index_path / f"{index_name}.pkl"

        self.bm25: Optional[BM25Okapi] = None
        self.chunk_ids: List[str] = []  # IDs de chunks en el índice
        self.chunks_dict: Dict[str, DocumentChunk] = {}  # chunk_id -> chunk

        # Stopwords en español (básicas)
        self.stopwords = {
            'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'ser', 'se', 'no', 'haber',
            'por', 'con', 'su', 'para', 'como', 'estar', 'tener', 'le', 'lo', 'todo',
            'pero', 'más', 'hacer', 'o', 'poder', 'decir', 'este', 'ir', 'otro', 'ese',
            'si', 'me', 'ya', 'ver', 'porque', 'dar', 'cuando', 'él', 'muy', 'sin',
            'vez', 'mucho', 'saber', 'qué', 'sobre', 'mi', 'alguno', 'mismo', 'yo',
            'también', 'hasta', 'año', 'dos', 'querer', 'entre', 'así', 'primero',
            'desde', 'grande', 'eso', 'ni', 'nos', 'llegar', 'pasar', 'tiempo', 'ella',
            'del', 'al', 'los', 'las', 'uno', 'una', 'unos', 'unas'
        }

    def tokenize(self, text: str) -> List[str]:
        """
        Tokenizar texto en español

        Args:
            text: Texto a tokenizar

        Returns:
            Lista de tokens
        """
        # Convertir a minúsculas
        text = text.lower()

        # Separar por espacios y puntuación
        tokens = re.findall(r'\b\w+\b', text)

        # Filtrar stopwords y tokens muy cortos
        tokens = [
            token for token in tokens
            if token not in self.stopwords and len(token) > 2
        ]

        return tokens

    def build_index(self, chunks: List[DocumentChunk]) -> None:
        """
        Construir índice BM25 desde chunks

        Args:
            chunks: Lista de chunks a indexar
        """
        try:
            logger.info(f"Construyendo índice BM25 para {len(chunks)} chunks...")

            # Tokenizar todos los textos
            tokenized_corpus = []
            self.chunk_ids = []
            self.chunks_dict = {}

            for chunk in chunks:
                tokens = self.tokenize(chunk.texto)
                tokenized_corpus.append(tokens)
                self.chunk_ids.append(chunk.chunk_id)
                self.chunks_dict[chunk.chunk_id] = chunk

            # Crear índice BM25
            self.bm25 = BM25Okapi(tokenized_corpus)

            logger.info(f"✅ Índice BM25 construido con {len(self.chunk_ids)} documentos")

        except Exception as e:
            logger.error(f"Error al construir índice BM25: {e}")
            raise

    def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        """
        Agregar chunks al índice existente

        Args:
            chunks: Chunks a agregar
        """
        try:
            logger.info(f"Agregando {len(chunks)} chunks al índice BM25...")

            # Si no hay índice, construirlo
            if self.bm25 is None:
                self.build_index(chunks)
                return

            # Cargar índice existente
            existing_chunks = [self.chunks_dict[cid] for cid in self.chunk_ids]

            # Agregar nuevos chunks
            all_chunks = existing_chunks + chunks

            # Reconstruir índice completo
            self.build_index(all_chunks)

            logger.info(f"✅ Índice actualizado con {len(self.chunk_ids)} documentos totales")

        except Exception as e:
            logger.error(f"Error al agregar chunks: {e}")
            raise

    def search(
        self,
        query: str,
        top_k: int = 10,
        filter_dict: Optional[Dict[str, any]] = None
    ) -> List[Tuple[str, float]]:
        """
        Buscar en el índice BM25

        Args:
            query: Query de búsqueda
            top_k: Número de resultados
            filter_dict: Filtros opcionales (ej: {"doc_id": "actuacion_123"})

        Returns:
            Lista de tuplas (chunk_id, score)
        """
        try:
            if self.bm25 is None:
                logger.warning("Índice BM25 no inicializado")
                return []

            # Tokenizar query
            query_tokens = self.tokenize(query)

            if not query_tokens:
                logger.warning("Query no generó tokens válidos")
                return []

            # Obtener scores
            scores = self.bm25.get_scores(query_tokens)

            # Crear lista de (chunk_id, score)
            results = list(zip(self.chunk_ids, scores))

            # Aplicar filtros si existen
            if filter_dict:
                filtered_results = []
                for chunk_id, score in results:
                    chunk = self.chunks_dict.get(chunk_id)
                    if chunk and self._matches_filters(chunk, filter_dict):
                        filtered_results.append((chunk_id, score))
                results = filtered_results

            # Ordenar por score descendente
            results.sort(key=lambda x: x[1], reverse=True)

            # Retornar top_k
            return results[:top_k]

        except Exception as e:
            logger.error(f"Error en búsqueda BM25: {e}")
            return []

    def _matches_filters(self, chunk: DocumentChunk, filter_dict: Dict[str, any]) -> bool:
        """Verificar si un chunk cumple con los filtros"""
        for key, value in filter_dict.items():
            # Buscar en metadata
            if key in chunk.metadata:
                chunk_value = chunk.metadata[key]
                # Para expediente_numero usar búsqueda parcial (contains)
                # porque los expedientes tienen prefijos como "FPO " que el usuario no incluye
                if key == "expediente_numero":
                    if value not in str(chunk_value):
                        return False
                elif chunk_value != value:
                    return False
            # Buscar en atributos del chunk
            elif hasattr(chunk, key):
                chunk_value = getattr(chunk, key)
                # Para expediente_numero usar búsqueda parcial (contains)
                if key == "expediente_numero":
                    if value not in str(chunk_value):
                        return False
                elif chunk_value != value:
                    return False
            else:
                return False
        return True

    def save_index(self) -> None:
        """Guardar índice a disco"""
        try:
            if self.bm25 is None:
                logger.warning("No hay índice para guardar")
                return

            # Crear directorio si no existe
            self.index_path.parent.mkdir(parents=True, exist_ok=True)

            # Guardar índice y metadata
            index_data = {
                'bm25': self.bm25,
                'chunk_ids': self.chunk_ids,
                'chunks_dict': self.chunks_dict,
            }

            with open(self.index_path, 'wb') as f:
                pickle.dump(index_data, f)

            logger.info(f"✅ Índice BM25 guardado en {self.index_path}")

        except Exception as e:
            logger.error(f"Error al guardar índice BM25: {e}")
            raise

    def load_index(self) -> bool:
        """
        Cargar índice desde disco

        Returns:
            True si se cargó exitosamente, False si no existe
        """
        try:
            if not self.index_path.exists():
                logger.info(f"No existe índice en {self.index_path}")
                return False

            with open(self.index_path, 'rb') as f:
                index_data = pickle.load(f)

            self.bm25 = index_data['bm25']
            self.chunk_ids = index_data['chunk_ids']
            self.chunks_dict = index_data['chunks_dict']

            logger.info(f"✅ Índice BM25 cargado con {len(self.chunk_ids)} documentos")
            return True

        except Exception as e:
            logger.error(f"Error al cargar índice BM25: {e}")
            return False

    def clear_index(self) -> None:
        """Limpiar índice"""
        self.bm25 = None
        self.chunk_ids = []
        self.chunks_dict = {}

        if self.index_path.exists():
            self.index_path.unlink()
            logger.info("Índice BM25 eliminado")

    def get_stats(self) -> Dict[str, any]:
        """Obtener estadísticas del índice"""
        return {
            "total_documents": len(self.chunk_ids),
            "index_exists": self.bm25 is not None,
            "index_path": str(self.index_path),
        }
