import json
import os
from datetime import datetime
from core.gestion_expedientes.comparar_expedientes import comparar_con_base
from core.gestion_expedientes.guardar_comparacion import guardar_comparacion_json


def comparar_expedientes_monitor(json_actual_path: str, base_json_path: str, carpeta_salida: str):
    """
    Compara dos archivos JSON de expedientes y guarda un informe de diferencias.

    :param json_actual_path: Ruta al archivo JSON actual extraído del portal.
    :param base_json_path: Ruta al archivo JSON base (histórico o simulado).
    :param carpeta_salida: Carpeta donde guardar el informe de comparación.
    :return: Tupla (nuevos, modificados, eliminados)
    """
    try:
        with open(json_actual_path, "r", encoding="utf-8") as f:
            json_actual = json.load(f)
    except Exception as e:
        print(f"❌ Error al cargar JSON actual: {e}")
        return [], [], []

    try:
        with open(base_json_path, "r", encoding="utf-8") as f:
            base_json = json.load(f)
    except Exception as e:
        print(f"❌ Error al cargar JSON base: {e}")
        return [], [], []

    nuevos, modificados, eliminados = comparar_con_base(json_actual, base_json)

    if nuevos or modificados or eliminados:
        ruta_guardada = guardar_comparacion_json(nuevos, modificados, eliminados, carpeta_salida)
        print(f"✅ Comparación realizada. Archivo guardado: {ruta_guardada}")
    else:
        print("✅ No se detectaron cambios entre los expedientes.")

    return nuevos, modificados, eliminados
