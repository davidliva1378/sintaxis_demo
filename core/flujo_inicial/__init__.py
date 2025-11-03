"""
Módulo de extracción inicial de expedientes del PJN.

Incluye funcionalidades de:
- Extracción incremental de expedientes
- Procesamiento opcional con procesador_pdf (clasificación, vencimientos)
"""

from core.flujo_inicial.extraccion_inicial import extraccion_incremental_async

# Exportar funciones de procesamiento si están disponibles
try:
    from core.flujo_inicial.procesamiento_expedientes import (
        ProcesadorExpedientesInicial,
        clasificar_actuaciones_desde_json,
        PROCESADOR_DISPONIBLE
    )
except ImportError:
    ProcesadorExpedientesInicial = None
    clasificar_actuaciones_desde_json = None
    PROCESADOR_DISPONIBLE = False

__all__ = [
    "extraccion_incremental_async",
    "ProcesadorExpedientesInicial",
    "clasificar_actuaciones_desde_json",
    "PROCESADOR_DISPONIBLE",
]
