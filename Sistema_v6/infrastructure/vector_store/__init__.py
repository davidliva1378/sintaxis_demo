"""
Vector Store para búsqueda semántica e híbrida.

DEPRECADO: Este módulo está deprecado y será eliminado.
Usar los nuevos servicios en infrastructure/rag/services/:
  - QdrantService para búsqueda vectorial
  - BM25Service para búsqueda por keywords
  - HybridSearchService para búsqueda híbrida
"""

import warnings

# Emitir advertencia al importar este módulo
warnings.warn(
    "infrastructure.vector_store está deprecado. "
    "Migrar a infrastructure.rag.services (QdrantService, BM25Service, HybridSearchService)",
    DeprecationWarning,
    stacklevel=2
)

# Mantener imports por compatibilidad pero con warning
try:
    from .chroma_client import ChromaClient
except ImportError:
    # ChromaDB ya fue eliminado
    ChromaClient = None

try:
    from .bm25_indexer import BM25Indexer
except ImportError:
    # BM25Indexer ya fue eliminado
    BM25Indexer = None

__all__ = ['ChromaClient', 'BM25Indexer']
