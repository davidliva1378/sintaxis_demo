"""
Módulo de Extracción Masiva

Componentes:
- ExtractorMasivo: Extrae listado completo de expedientes del PJN
- GestorBatch: Procesa lotes de expedientes seleccionados
"""

from .extractor_masivo import ExtractorMasivo
from .gestor_batch import GestorBatch
from .models import (
    ExpedienteListado,
    ConfigExtraccionMasiva,
    ResumenExtraccion,
    SesionExtraccion,
    EstadoExpediente,
    TipoExtraccion,
)
from .exportadores import (
    exportar_json,
    exportar_csv,
    exportar_excel,
    exportar_csv_resultados,
    generar_estadisticas,
    generar_reporte_html,
)

__all__ = [
    "ExtractorMasivo",
    "GestorBatch",
    "ExpedienteListado",
    "ConfigExtraccionMasiva",
    "ResumenExtraccion",
    "SesionExtraccion",
    "EstadoExpediente",
    "TipoExtraccion",
    "exportar_json",
    "exportar_csv",
    "exportar_excel",
    "exportar_csv_resultados",
    "generar_estadisticas",
    "generar_reporte_html",
]
