from panel_pjn.acciones_pjn.gestion_actuaciones.extraccion_v2 import extraer_actuaciones_pagina, obtener_actuaciones_todas_paginas_async
from panel_pjn.acciones_pjn.gestion_actuaciones.extraccion_completa import extraer_actuaciones_completas
from panel_pjn.acciones_pjn.gestion_actuaciones.bk.descarga import descargar_archivos_actuaciones
from panel_pjn.acciones_pjn.gestion_actuaciones.utilidades import limpiar_texto, normalizar_fecha, generar_hash_archivo

# Procesamiento inteligente (opcional)
try:
    from panel_pjn.acciones_pjn.gestion_actuaciones.procesamiento import (
        ProcesadorActuacionesExtraccion,
        procesar_actuaciones_extraidas
    )
except ImportError:
    # procesador_pdf no disponible
    ProcesadorActuacionesExtraccion = None
    procesar_actuaciones_extraidas = None