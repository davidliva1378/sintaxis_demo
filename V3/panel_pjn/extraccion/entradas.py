"""
Adaptador público de notificaciones → `extraer_entradas`.

Expone una API estable para el resto del sistema y delega la lógica real en
`_impl_entradas.actualizar_notificaciones_nuevas` (tu implementación actual).

Además, provee un alias de compatibilidad `actualizar_notificaciones_nuevas`.

Contrato sugerido (ligero y práctico):
    extraer_entradas(page: playwright.Page, destino: Optional[str]=None)
        -> dict { 'nuevas': int, 'total': int, 'historial_json': str, 'entradas': list[dict] }

Esto permite a la GUI/monitores saber cuántas nuevas hubo y mostrar el listado.
"""
from __future__ import annotations
from typing import Dict, List, Optional
import os, json

from ._impl_entradas import actualizar_notificaciones_nuevas as _impl_actualizar


async def extraer_entradas(page, destino: Optional[str] = None) -> Dict[str, object]:
    """Ejecuta la actualización y devuelve resumen + historial completo.

    Retorna:
      {
        'nuevas': int,                      # cuántas nuevas se incorporaron
        'total': int,                       # total acumulado en historial
        'historial_json': str,              # ruta al JSON
        'entradas': list[dict],             # lista completa actual
      }
    """
    nuevas = await _impl_actualizar(page, destino=destino)

    notif_dir = destino or os.path.join(os.getcwd(), "datos_extraidos", "monitoreo")
    historial_json = os.path.join(notif_dir, "historial_notificaciones.json")

    entradas: List[Dict] = []
    if os.path.exists(historial_json):
        try:
            with open(historial_json, "r", encoding="utf-8") as f:
                entradas = json.load(f) or []
        except Exception:
            entradas = []

    return {
        "nuevas": int(nuevas or 0),
        "total": len(entradas),
        "historial_json": historial_json,
        "entradas": entradas,
    }


# Alias de compatibilidad para código legado
async def actualizar_notificaciones_nuevas(page, destino: Optional[str] = None) -> Dict[str, object]:
    return await extraer_entradas(page, destino=destino)
