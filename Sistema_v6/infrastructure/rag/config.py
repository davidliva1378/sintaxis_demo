"""
Configuración del Sistema RAG para ActuacionesQuery

Este módulo centraliza toda la configuración necesaria para:
- Qdrant (Vector Database)
- Embeddings (sentence-transformers)
- spaCy (NER)
- Ollama (LLM)
- Chunking
- Search
"""

from pydantic_settings import BaseSettings
from pathlib import Path


class RAGSettings(BaseSettings):
    """Configuración del sistema RAG"""

    # ===== Qdrant =====
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "actuaciones"
    qdrant_grpc_port: int = 6334
    qdrant_timeout: int = 30

    # ===== Embeddings =====
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    embedding_dimension: int = 768
    embedding_device: str = "cpu"  # "cuda" si tienes GPU
    embedding_batch_size: int = 32

    # ===== spaCy NER =====
    spacy_model: str = "es_core_news_md"

    # ===== Ollama LLM =====
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    ollama_temperature: float = 0.1  # Más determinista para legal
    ollama_max_tokens: int = 2048
    ollama_timeout: int = 120

    # ===== Chunking =====
    chunk_size: int = 1500  # Caracteres por chunk
    chunk_overlap: int = 300  # Overlap entre chunks

    # ===== Search =====
    search_limit: int = 10  # Resultados híbridos iniciales
    rerank_top_k: int = 5   # Top resultados post-reranking

    # BM25 (sparse search)
    bm25_k1: float = 1.5
    bm25_b: float = 0.75

    # Hybrid search weights
    dense_weight: float = 0.7
    sparse_weight: float = 0.3

    # ===== Cache & Storage =====
    cache_dir: Path = Path("./data/cache")
    vector_store_path: Path = Path("./data/vector_store")
    bm25_index_path: Path = Path("./data/bm25_index")

    # ===== Paths =====
    data_dir: Path = Path("./data")
    models_dir: Path = Path("./data/models")

    class Config:
        env_prefix = "RAG_"
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignorar variables del .env que no están en el modelo


# Singleton instance
_settings = None


def get_rag_settings() -> RAGSettings:
    """Obtener instancia singleton de configuración"""
    global _settings
    if _settings is None:
        _settings = RAGSettings()

        # Crear directorios si no existen
        _settings.cache_dir.mkdir(parents=True, exist_ok=True)
        _settings.vector_store_path.mkdir(parents=True, exist_ok=True)
        _settings.bm25_index_path.mkdir(parents=True, exist_ok=True)
        _settings.models_dir.mkdir(parents=True, exist_ok=True)

    return _settings
