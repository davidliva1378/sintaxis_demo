"""
Servicio de embeddings para búsqueda semántica.

Utiliza sentence-transformers con el modelo BGE-M3 para generar
embeddings de alta calidad en español.
"""

import logging
import hashlib
from typing import List, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """
    Servicio para generar embeddings de texto.

    Utiliza BGE-M3 (BAAI/bge-m3) que tiene excelente soporte
    para español y textos largos (hasta 8192 tokens).
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        device: str = "cuda",
        cache_dir: Optional[str] = None
    ):
        """
        Inicializa el servicio de embeddings.

        Args:
            model_name: Nombre del modelo de sentence-transformers
            device: Dispositivo a usar ('cuda', 'cpu', 'mps')
            cache_dir: Directorio para cache de modelos
        """
        self.model_name = model_name
        self.device = device
        self.cache_dir = cache_dir
        self._model = None
        self._dimension = None

    def _lazy_load_model(self):
        """Carga el modelo solo cuando se necesita."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                logger.info(f"Cargando modelo de embeddings: {self.model_name}")

                self._model = SentenceTransformer(
                    self.model_name,
                    device=self.device,
                    cache_folder=self.cache_dir
                )

                # Obtener dimensión del modelo
                self._dimension = self._model.get_sentence_embedding_dimension()

                logger.info(
                    f"Modelo cargado: {self.model_name} "
                    f"(dim={self._dimension}, device={self.device})"
                )

            except ImportError:
                raise ImportError(
                    "sentence-transformers no está instalado. "
                    "Instalar con: pip install sentence-transformers"
                )
            except Exception as e:
                logger.error(f"Error cargando modelo: {e}")
                # Fallback a CPU si falla CUDA
                if self.device == "cuda":
                    logger.warning("Intentando con CPU...")
                    self.device = "cpu"
                    self._model = None
                    return self._lazy_load_model()
                raise

        return self._model

    @property
    def dimension(self) -> int:
        """Retorna la dimensión de los embeddings."""
        self._lazy_load_model()
        return self._dimension

    def encode(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        show_progress: bool = False,
        normalize: bool = True
    ) -> List[List[float]]:
        """
        Genera embeddings para uno o más textos.

        Args:
            texts: Texto o lista de textos
            batch_size: Tamaño del batch para procesamiento
            show_progress: Mostrar barra de progreso
            normalize: Normalizar embeddings (L2)

        Returns:
            Lista de embeddings (cada uno es lista de floats)
        """
        model = self._lazy_load_model()

        # Convertir a lista si es string
        if isinstance(texts, str):
            texts = [texts]
            single_input = True
        else:
            single_input = False

        # Generar embeddings
        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            normalize_embeddings=normalize,
            convert_to_numpy=True
        )

        # Convertir a lista de listas
        result = embeddings.tolist()

        if single_input:
            return result[0]

        return result

    def encode_query(self, query: str) -> List[float]:
        """
        Genera embedding optimizado para queries de búsqueda.

        Algunos modelos como BGE requieren un prefijo para queries.

        Args:
            query: Texto de la consulta

        Returns:
            Embedding como lista de floats
        """
        # BGE-M3 no requiere prefijo, pero otros modelos sí
        if "bge" in self.model_name.lower():
            # Para BGE, agregar instrucción de retrieval
            query = f"Represent this sentence for searching relevant passages: {query}"

        return self.encode(query)

    def encode_documents(
        self,
        documents: List[str],
        batch_size: int = 32,
        show_progress: bool = True
    ) -> List[List[float]]:
        """
        Genera embeddings para una lista de documentos.

        Args:
            documents: Lista de textos
            batch_size: Tamaño del batch
            show_progress: Mostrar progreso

        Returns:
            Lista de embeddings
        """
        return self.encode(
            documents,
            batch_size=batch_size,
            show_progress=show_progress
        )

    def similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Calcula similitud coseno entre dos embeddings.

        Args:
            embedding1: Primer embedding
            embedding2: Segundo embedding

        Returns:
            Similitud coseno (0-1)
        """
        import numpy as np

        a = np.array(embedding1)
        b = np.array(embedding2)

        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def get_cache_key(self, text: str) -> str:
        """
        Genera una clave de cache para un texto.

        Args:
            text: Texto a hashear

        Returns:
            Hash MD5 del texto
        """
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 1000,
        overlap: int = 150
    ) -> List[str]:
        """
        Divide un texto largo en chunks con overlap.

        Args:
            text: Texto a dividir
            chunk_size: Tamaño de cada chunk en caracteres (default: 1000)
            overlap: Solapamiento entre chunks (default: 150, 15%)

        Returns:
            Lista de chunks
        """
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))

            # Ajustar para no cortar palabras
            if end < len(text):
                last_space = text.rfind(' ', start, end)
                if last_space > start + chunk_size * 0.8:
                    end = last_space

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - overlap if end < len(text) else len(text)

        return chunks

    def is_available(self) -> bool:
        """
        Verifica si el servicio está disponible.

        Returns:
            True si se puede cargar el modelo
        """
        try:
            self._lazy_load_model()
            return True
        except Exception as e:
            logger.error(f"Servicio no disponible: {e}")
            return False

    def get_model_info(self) -> dict:
        """
        Retorna información del modelo.

        Returns:
            Dict con información del modelo
        """
        return {
            "model_name": self.model_name,
            "device": self.device,
            "dimension": self.dimension if self._model else None,
            "loaded": self._model is not None
        }
