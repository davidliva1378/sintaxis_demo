import os
import json
from panel_pjn.acciones_pjn.gestion_actuaciones.extraccion_v2 import obtener_actuaciones_todas_paginas_async
from panel_pjn.acciones_pjn.gestion_actuaciones.bk.historicas import extraer_actuaciones_historicas


async def extraer_actuaciones_completas(
    page_expediente,
    expediente_datos: dict,
    incluir_historicas: bool = True,
    directorio_base: str = "ActuacionesCompletas"
) -> tuple[list[dict], list[dict], str | None]:
    """
    Extrae actuaciones actuales e históricas (opcional) de un expediente y las guarda como JSON.
    También genera un único archivo con estructura detallada, campo EsHistorica y Descargado.
    """
    actuaciones_actuales = []
    actuaciones_historicas = []

    try:
        numero_original = expediente_datos['numero']
        numero_normalizado = numero_original.replace('/', '_')
        carpeta_expte = os.path.join(directorio_base, numero_normalizado)

        # Actuaciones actuales
        actuaciones_actuales, error_actuales, carpeta_final = await obtener_actuaciones_todas_paginas_async(
            page_expediente,
            expediente_datos,
            carpeta_destino=carpeta_expte
        )
        if error_actuales:
            return [], [], f"Error al extraer actuaciones actuales: {error_actuales}"

        for act in actuaciones_actuales:
            act["EsHistorica"] = False
            if act.get("TieneArchivo"):
                act["Descargado"] = False

        # Actuaciones históricas (si corresponde)
        if incluir_historicas:
            actuaciones_historicas, error_hist = await extraer_actuaciones_historicas(
                page_expediente, expediente_datos
            )
            if error_hist:
                return actuaciones_actuales, [], f"Error al extraer actuaciones históricas: {error_hist}"

            for act in actuaciones_historicas:
                act["EsHistorica"] = True
                if act.get("TieneArchivo"):
                    act["Descargado"] = False
        else:
            actuaciones_historicas = []

        todas = actuaciones_actuales + actuaciones_historicas

        expediente_info = {
            "numero": expediente_datos.get("numero"),
            "caratula": expediente_datos.get("caratula"),
            "dependencia": expediente_datos.get("dependencia"),
            "jurisdiccion": expediente_datos.get("jurisdiccion"),
            "situacion": expediente_datos.get("situacion"),
            "Cantidad de Actuaciones Obtenidas": len(todas),
            "Cantidad de Archivos Descargados": sum(1 for a in todas if a.get("TieneArchivo"))
        }

        estructura_json = {
            "Expediente": expediente_info,
            "Actuaciones": todas
        }

        json_path = os.path.join(carpeta_final, f"actuaciones-{numero_normalizado}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(estructura_json, f, indent=2, ensure_ascii=False)
        print(f"📄 JSON generado: {json_path}")

        return actuaciones_actuales, actuaciones_historicas, None

    except Exception as e:
        return [], [], f"Error general: {type(e).__name__}: {str(e)}"


