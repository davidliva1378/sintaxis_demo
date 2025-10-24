import json
import pandas as pd
import re
from datetime import datetime
from src.configuracion_v1 import JSON_PATH

# 📌 FUNCIÓN PARA CARGAR EL ARCHIVO JSON
def cargar_json():
    """Carga el archivo JSON de expedientes y convierte las fechas al formato adecuado."""
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as file:
            expedientes = json.load(file)
            # Convertir fecha de 'ultima_actuacion' a formato datetime.date
            for exp in expedientes:
                exp["ultima_actuacion"] = datetime.strptime(exp["ultima_actuacion"], "%d/%m/%Y").date()
            return expedientes
    except FileNotFoundError:
        print("❌ Error: No se encontró el archivo JSON.")
        return []
    except json.JSONDecodeError:
        print("❌ Error: El archivo JSON tiene un formato incorrecto.")
        return []
    except Exception as e:
        print(f"❌ Otro error ocurrió: {e}")
        return []

#FUNCION PARA PROCESAR EL JSON DE EXPEDIENTES:

def procesar_expedientes(json_data):
    """
    Procesa un JSON de expedientes y devuelve un DataFrame con columnas estructuradas.

    :param json_data: Lista de diccionarios con los datos de expedientes.
    :return: DataFrame procesado.
    """
    registros = []

    for expediente in json_data:
        numero = expediente.get("numero", "")

        # Omitir registros sin número válido
        if not numero or numero == "null-00":
            continue

        dependencia = expediente.get("dependencia", "SIN ASIGNAR")
        caratula = expediente.get("caratula", "SIN ASIGNAR")
        situacion = expediente.get("situacion", "SIN ASIGNAR")
        ultima_actuacion = expediente.get("ultima_actuacion", "SIN ASIGNAR")

        # Convertir fecha a tipo date si es válida
        try:
            ultima_actuacion = datetime.strptime(ultima_actuacion, "%d/%m/%Y").date()
        except ValueError:
            ultima_actuacion = None

        # Extraer jurisdicción (primeros tres caracteres si es alfabético)
        match_jurisdiccion = re.match(r"([A-Z]{3})\s", numero)
        if match_jurisdiccion:
            id_jurisdiccion = match_jurisdiccion.group(1)
            numero_sin_jurisdiccion = numero[4:]  # Eliminar los 4 primeros caracteres (incluyendo el espacio)
        else:
            id_jurisdiccion = "SIN ASIGNAR"
            numero_sin_jurisdiccion = numero  # Usar número completo si no hay prefijo

        # Extraer número antes de la barra "/"
        match_numero = re.search(r"(\d+)/", numero_sin_jurisdiccion)
        numero_expediente = match_numero.group(1) if match_numero else numero_sin_jurisdiccion

        # Extraer año después de la primera barra "/"
        match_anio = re.search(r"/(\d{4})", numero_sin_jurisdiccion)
        anio_expediente = match_anio.group(1) if match_anio else "SIN ASIGNAR"

        # Extraer incidental (cualquier cosa después del año)
        match_incidental = re.search(r"/\d{4}(/.+)?", numero_sin_jurisdiccion)
        incidental = match_incidental.group(1)[1:] if match_incidental and match_incidental.group(1) else "SIN ASIGNAR"

        # Extraer "Juzgado" y "Secretaría" de la dependencia
        partes_dependencia = [p.strip() for p in dependencia.split(" - ")]
        juzgado = partes_dependencia[0] if len(partes_dependencia) > 0 else "SIN ASIGNAR"
        secretaria = partes_dependencia[1] if len(
            partes_dependencia) > 1 else juzgado  # Si no hay secretaria, repetir el juzgado

        registros.append({
            "Numero": numero,
            "Dependencia": dependencia,
            "ID-Jurisdiccion": id_jurisdiccion,
            "Numero_solo": numero_expediente,
            "Año": anio_expediente,
            "Incidental": incidental,
            "Juzgado": juzgado,
            "Secretaria": secretaria,
            "Carátula": caratula,
            "Situación": situacion,
            "Última Actuación": ultima_actuacion
        })

    # Convertir a DataFrame
    df_expedientes = pd.DataFrame(registros)

    return df_expedientes

