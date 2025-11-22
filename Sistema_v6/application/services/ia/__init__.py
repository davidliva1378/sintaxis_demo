"""
Servicios de IA para el sistema SintaXis.

Incluye:
- EmbeddingsService: Generación de embeddings con BGE-M3
- NERService: Extracción de entidades con GLiNER
- LLMService: Generación de texto con Ollama/Llama
"""

from .embeddings_service import EmbeddingsService
from .ner_service import NERService, ENTIDADES_JURIDICAS
from .llm_service import LLMService
from .clasificador_service import ClasificadorService, TIPOS_ACTUACION
from .rag_service import RAGService
from .ia_integration_service import IAIntegrationService, get_ia_integration_service

__all__ = [
    'EmbeddingsService',
    'NERService',
    'ENTIDADES_JURIDICAS',
    'LLMService',
    'ClasificadorService',
    'TIPOS_ACTUACION',
    'RAGService',
    'IAIntegrationService',
    'get_ia_integration_service'
]
