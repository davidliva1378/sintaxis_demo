"""
Módulo de integración del sistema RAG con componentes existentes

Contiene:
- Hook de indexación automática post-procesamiento
- Adaptadores para diferentes fuentes de datos
"""

from .actuaciones_hook import (
    ActuacionesIndexHook,
    actuaciones_index_hook,
    configurar_hook,
    obtener_hook,
)

__all__ = [
    "ActuacionesIndexHook",
    "actuaciones_index_hook",
    "configurar_hook",
    "obtener_hook",
]
