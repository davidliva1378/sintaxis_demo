from .extraccion_v2 import extraer_actuaciones_pagina, obtener_actuaciones_todas_paginas_async
from .extraccion_completa import extraer_actuaciones_completas
from .bk.descarga import descargar_archivos_actuaciones
from .utilidades import limpiar_texto, normalizar_fecha, generar_hash_archivo

# Procesamiento inteligente (opcional)
try:
    from .procesamiento import (
        ProcesadorActuacionesExtraccion,
        procesar_actuaciones_extraidas
    )
except ImportError:
    # procesador_pdf no disponible
    ProcesadorActuacionesExtraccion = None
    procesar_actuaciones_extraidas = None
