"""
Módulo de extracción masiva de expedientes del PJN.

Este módulo proporciona funcionalidad completa para extraer grandes
volúmenes de expedientes del portal PJN con:

- Extracción completa del listado (todas las páginas)
- Procesamiento por lotes con manejo de errores
- Filtrado por estados, fechas, dependencias
- Progreso en tiempo real vía callbacks
- Exportación a múltiples formatos (JSON, Excel, CSV)
"""

# Importar siempre los exportadores (no dependen de playwright)
from .exportadores import (
    exportar_json,
    exportar_excel,
    exportar_csv,
    generar_estadisticas,
)

# Importar módulos que requieren playwright solo si está disponible
__all__ = [
    "exportar_json",
    "exportar_excel",
    "exportar_csv",
    "generar_estadisticas",
]

try:
    from .extractor_masivo import (
        ExtractorMasivo,
        ConfigExtraccionMasiva,
    )
    from .gestor_batch import (
        GestorBatch,
        ResumenBatch,
        ResultadoProcesamiento,
    )

    __all__.extend([
        "ExtractorMasivo",
        "ConfigExtraccionMasiva",
        "GestorBatch",
        "ResumenBatch",
        "ResultadoProcesamiento",
    ])
except ImportError as e:
    # Playwright u otras dependencias no disponibles
    # Los exportadores siguen funcionando
    pass

__version__ = "1.0.0"
