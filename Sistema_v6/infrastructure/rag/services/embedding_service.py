"""
EmbeddingService - Servicio para generar embeddings de texto

Maneja:
- Carga del modelo sentence-transformers
- Generación de embeddings (single y batch)
- Cache de embeddings frecuentes
- Gestión de memoria y dispositivo (CPU/GPU)
"""

import logging
import hashlib
from typing import List, Optional, Dict
from pathlib import Path
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

from infrastructure.rag.config import get_rag_settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Servicio para generar embeddings de texto usando sentence-transformers"""

    def __init__(self):
        self.settings = get_rag_settings()
        self.model: Optional[SentenceTransformer] = None
        self.cache: Dict[str, List[float]] = {}
        self.cache_file = self.settings.cache_dir / "embeddings_cache.pkl"
        self._load_cache()

    def load_model(self) -> None:
        """Cargar el modelo de embeddings"""
        try:
            logger.info(f"Cargando modelo de embeddings: {self.settings.embedding_model}")

            # Cargar modelo con configuración
            self.model = SentenceTransformer(
                self.settings.embedding_model,
                device=self.settings.embedding_device,
            )

            # Verificar dimensión
            actual_dim = self.model.get_sentence_embedding_dimension()
            if actual_dim != self.settings.embedding_dimension:
                logger.warning(
                    f"Dimensión del modelo ({actual_dim}) difiere de la configurada "
                    f"({self.settings.embedding_dimension}). Usando dimensión del modelo."
                )

            logger.info(f"✅ Modelo cargado exitosamente")
            logger.info(f"   Dimensión: {actual_dim}")
            logger.info(f"   Dispositivo: {self.settings.embedding_device}")

        except Exception as e:
            logger.error(f"Error al cargar modelo de embeddings: {e}")
            raise

    def encode_text(self, text: str, use_cache: bool = True) -> List[float]:
        """
        Generar embedding para un texto individual

        Args:
            text: Texto a vectorizar
            use_cache: Si True, usa/guarda en cache

        Returns:
            Vector de embeddings (dimensión configurada)
        """
        try:
            if not self.model:
                self.load_model()

            # Verificar si está en cache
            if use_cache:
                cache_key = self._get_cache_key(text)
                if cache_key in self.cache:
                    logger.debug(f"Cache hit para texto de {len(text)} caracteres")
                    return self.cache[cache_key]

            # Generar embedding
            embedding = self.model.encode(
                text,
                convert_to_numpy=True,
                show_progress_bar=False,
            )

            # Convertir a lista
            embedding_list = embedding.tolist()

            # Guardar en cache
            if use_cache:
                self.cache[cache_key] = embedding_list
                self._save_cache()

            return embedding_list

        except Exception as e:
            logger.error(f"Error al generar embedding: {e}")
            raise

    def encode_batch(
        self,
        texts: List[str],
        batch_size: Optional[int] = None,
        show_progress: bool = True,
    ) -> List[List[float]]:
        """
        Generar embeddings para múltiples textos (batch)

        Args:
            texts: Lista de textos a vectorizar
            batch_size: Tamaño del batch (default: configurado)
            show_progress: Mostrar barra de progreso

        Returns:
            Lista de vectores de embeddings
        """
        try:
            if not self.model:
                self.load_model()

            if not texts:
                logger.warning("Lista de textos vacía")
                return []

            # Usar batch_size configurado si no se especifica
            if batch_size is None:
                batch_size = self.settings.embedding_batch_size

            logger.info(f"Generando embeddings para {len(texts)} textos...")

            # Generar embeddings
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=show_progress,
            )

            # Convertir a lista de listas
            embeddings_list = embeddings.tolist()

            logger.info(f"✅ Generados {len(embeddings_list)} embeddings")

            return embeddings_list

        except Exception as e:
            logger.error(f"Error al generar embeddings en batch: {e}")
            raise

    def get_dimension(self) -> int:
        """
        Obtener dimensión de los embeddings

        Returns:
            Dimensión del vector (ej: 768)
        """
        if not self.model:
            self.load_model()
        return self.model.get_sentence_embedding_dimension()

    def compute_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float],
    ) -> float:
        """
        Calcular similitud coseno entre dos embeddings

        Args:
            embedding1: Primer embedding
            embedding2: Segundo embedding

        Returns:
            Score de similitud (0-1)
        """
        try:
            # Convertir a numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)

            # Cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = dot_product / (norm1 * norm2)

            # Asegurar rango [0, 1]
            return float(max(0.0, min(1.0, similarity)))

        except Exception as e:
            logger.error(f"Error al calcular similitud: {e}")
            return 0.0

    def clear_cache(self) -> None:
        """Limpiar cache de embeddings"""
        self.cache.clear()
        if self.cache_file.exists():
            self.cache_file.unlink()
        logger.info("Cache de embeddings limpiado")

    def get_cache_stats(self) -> Dict[str, int]:
        """Obtener estadísticas del cache"""
        return {
            "total_entries": len(self.cache),
            "cache_size_bytes": self.cache_file.stat().st_size if self.cache_file.exists() else 0,
        }

    # === Métodos privados ===

    def _get_cache_key(self, text: str) -> str:
        """Generar clave de cache para un texto"""
        # Usar hash MD5 del texto como clave
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def _load_cache(self) -> None:
        """Cargar cache desde disco"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'rb') as f:
                    self.cache = pickle.load(f)
                logger.info(f"Cache cargado: {len(self.cache)} entradas")
        except Exception as e:
            logger.warning(f"No se pudo cargar cache: {e}")
            self.cache = {}

    def _save_cache(self) -> None:
        """Guardar cache a disco"""
        try:
            # Limitar tamaño del cache (mantener últimos 1000)
            if len(self.cache) > 1000:
                # Eliminar las entradas más antiguas (primeras 200)
                keys_to_remove = list(self.cache.keys())[:200]
                for key in keys_to_remove:
                    del self.cache[key]
                logger.debug(f"Cache reducido a {len(self.cache)} entradas")

            # Guardar a disco
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.cache, f)

        except Exception as e:
            logger.warning(f"No se pudo guardar cache: {e}")

    def __enter__(self):
        """Context manager entry"""
        self.load_model()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        # Guardar cache al salir
        self._save_cache()
