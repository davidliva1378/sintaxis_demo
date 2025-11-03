"""
Módulo Generador de Documentos con integración procesador_pdf.

Este módulo proporciona utilidades para generar documentos jurídicos
inteligentes utilizando procesador_pdf para filtrar contenido relevante.

Exporta:
- FiltroContenidoInteligente: Filtra actuaciones por relevancia
- GeneradorDocumentosBase: Clase base para generadores
- generar_contexto_filtrado: Función auxiliar para crear contexto
"""

try:
    from Sistema_v5.generador_documentos.integracion_procesador import (
        FiltroContenidoInteligente,
        generar_contexto_filtrado,
        PROCESADOR_DISPONIBLE
    )
except ImportError:
    FiltroContenidoInteligente = None
    generar_contexto_filtrado = None
    PROCESADOR_DISPONIBLE = False

try:
    from Sistema_v5.generador_documentos.generador_base import (
        GeneradorDocumentosBase,
    )
except ImportError:
    GeneradorDocumentosBase = None

__all__ = [
    "FiltroContenidoInteligente",
    "generar_contexto_filtrado",
    "GeneradorDocumentosBase",
    "PROCESADOR_DISPONIBLE",
]
