# V3/panel_pjn/acciones_pjn/operaciones.py
from __future__ import annotations
"""
Fachada de operaciones para el sistema PJN (punto único de importación).

Objetivo:
- Evitar imports dispersos desde GUI/CLI/monitores.
- Exponer una API estable que delega en submódulos de `extraccion/*` y `gestion/*`.
- Mantener compatibilidad con nombres previos (alias).

Uso típico desde la app:
    from panel_pjn.acciones_pjn import (
        extraer_expedientes, extraer_entradas,
        buscar_expedientes, abrir_expediente_desde_fila, extraer_datos_expediente,
        crear_estructura_expediente, guardar_metadata_expediente, MetaExpediente,
    )
"""

# --------------------------------------------------------------------------------------
# Extracción (Playwright) – adaptadores públicos
# --------------------------------------------------------------------------------------
from .extraccion.expedientes import extraer_expedientes
from .extraccion.entradas import extraer_entradas, actualizar_notificaciones_nuevas

# Búsqueda / detalle (Playwright)
from .extraccion.busqueda import (
    buscar_expedientes,
    abrir_expediente_desde_fila,
    extraer_datos_expediente,
    buscar_y_cargar_expediente,  # helper de alto nivel
)

# --------------------------------------------------------------------------------------
# Gestión (local, sin Playwright)
# --------------------------------------------------------------------------------------
from .gestion.expedientes import (
    MetaExpediente,
    crear_estructura_expediente,
    guardar_metadata_expediente,
    exportar_expedientes_a_base,
    seleccionar_expedientes,
    marcar_descartado,
    desmarcar_descartado,
    es_descartado,
)

from .gestion.actuaciones import (
    comparar_actuaciones,
    ingresar_actuaciones,
    eliminar_actuaciones_obsoletas,
)

# --------------------------------------------------------------------------------------
# API pública (reexports)
# --------------------------------------------------------------------------------------
__all__ = [
    # Extracción
    "extraer_expedientes",
    "extraer_entradas",
    "actualizar_notificaciones_nuevas",  # alias de compat

    # Búsqueda / detalle
    "buscar_expedientes",
    "abrir_expediente_desde_fila",
    "extraer_datos_expediente",
    "buscar_y_cargar_expediente",

    # Gestión – expedientes
    "MetaExpediente",
    "crear_estructura_expediente",
    "guardar_metadata_expediente",
    "exportar_expedientes_a_base",
    "seleccionar_expedientes",
    "marcar_descartado",
    "desmarcar_descartado",
    "es_descartado",

    # Gestión – actuaciones
    "comparar_actuaciones",
    "ingresar_actuaciones",
    "eliminar_actuaciones_obsoletas",

    # Helpers de orquestación (opcional)
    "importar_expediente_basico",
]

# --------------------------------------------------------------------------------------
# Helpers de orquestación (opcionales, para simplificar flujos comunes)
# --------------------------------------------------------------------------------------
async def importar_expediente_basico(
    page,
    *,
    numero: str | None = None,
    anio: str | None = None,
    caratula: str | None = None,
    persistir: bool = True,
) -> dict | None:
    """
    Busca → abre → extrae (y opcionalmente persiste metadatos mínimos) de un expediente.

    Args:
        page: Playwright.Page ya autenticada en la vista de búsqueda.
        numero, anio, caratula: criterios de búsqueda (usa número+anio o carátula).
        persistir: si True, crea estructura y guarda metadata.json.

    Returns:
        dict con los datos del expediente (o None si no hay resultados).
    """
    exp = await buscar_y_cargar_expediente(page, numero=numero, anio=anio, caratula=caratula)
    if not exp:
        return None

    if persistir:
        crear_estructura_expediente(exp["numero"])
        meta = MetaExpediente(
            numero=exp["numero"],
            caratula=exp.get("caratula"),
            jurisdiccion=exp.get("jurisdiccion"),
            dependencia=exp.get("dependencia"),
            situacion=exp.get("situicion") or exp.get("situacion"),
            fecha_inicio=exp.get("fecha_inicio"),
            ultima_actuacion=exp.get("ultima_actuacion"),
        )
        guardar_metadata_expediente(meta)

    return exp
