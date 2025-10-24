import json
from datetime import datetime
from src.expedientes_v1 import buscar_expediente
from src.reportes_v1 import guardar_en_excel
from src.configuracion_v1 import JSON_PATH

def cargar_json():
    """Carga el archivo JSON de expedientes y convierte fechas."""
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as file:
            expedientes = json.load(file)
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

def comparar_expedientes(nuevos_expedientes):
    """Compara expedientes nuevos con los existentes en la base de datos y consolida los cambios en una sola fila."""
    registros_excel = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for nuevo in nuevos_expedientes:
        expedientes_db = buscar_expediente(nuevo["numero"])
        if not expedientes_db:
            registros_excel.append([timestamp, nuevo["numero"], "Nuevo", "N/A", nuevo["situacion"], "N/A", nuevo["ultima_actuacion"], "N/A", nuevo["caratula"]])
        else:
            for expediente in expedientes_db:
                cambios = [timestamp, nuevo["numero"], expediente["id_expediente"], "Sin cambios" if expediente["situacion"] == nuevo["situacion"] else expediente["situacion"], nuevo["situacion"]]
                registros_excel.append(cambios)

    if registros_excel:
        guardar_en_excel(registros_excel)
