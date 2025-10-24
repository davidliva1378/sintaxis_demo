import json
from datetime import datetime
import os

def guardar_comparacion_json(nuevos, modificados, eliminados, carpeta_destino):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"comparacion_{timestamp}.json"
    ruta_salida = os.path.join(carpeta_destino, nombre_archivo)

    resultado = {
        "timestamp": timestamp,
        "nuevos": nuevos,
        "modificados": modificados,
        "eliminados": eliminados,
        "total_nuevos": len(nuevos),
        "total_modificados": len(modificados),
        "total_eliminados": len(eliminados)
    }

    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)

    print(f"✅ Comparación guardada en: {ruta_salida}")
    return ruta_salida