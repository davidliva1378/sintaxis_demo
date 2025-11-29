"""
Configuración del Sistema RAG - Wrapper de Compatibilidad

DEPRECATED: Este módulo es un wrapper de compatibilidad.
La configuración real ahora está en infrastructure.config.settings.RAGSettings

TODO: Migrar todos los imports a usar:
    from infrastructure.config.settings import get_settings
    settings = get_settings()
    rag_config = settings.rag
"""

from infrastructure.config.settings import get_settings, RAGSettings


def get_rag_settings() -> RAGSettings:
    """
    Obtiene la configuración RAG desde el settings unificado.
    
    DEPRECATED: Usar get_settings().rag en su lugar.
    
    Returns:
        RAGSettings: Configuración del sistema RAG
    
    Example:
        >>> from infrastructure.rag.config import get_rag_settings
        >>> settings = get_rag_settings()
        >>> print(settings.ollama_model)
    """
    return get_settings().rag


# Re-exportar RAGSettings para compatibilidad
__all__ = ["get_rag_settings", "RAGSettings"]
