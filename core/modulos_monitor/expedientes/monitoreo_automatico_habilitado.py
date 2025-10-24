from datetime import datetime
import json

def monitoreo_automatico_habilitado(config_path="config_monitor_expedientes.json"):
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        dias_habilitados = config.get("dias_habilitados", [])
        hora_desde = config.get("hora_desde", "00:00")
        hora_hasta = config.get("hora_hasta", "23:59")

        ahora = datetime.now()
        dia_actual = ahora.strftime("%A").lower()
        hora_actual = ahora.strftime("%H:%M")

        dias_ingles_a_espanol = {
            "monday": "lunes", "tuesday": "martes", "wednesday": "miércoles",
            "thursday": "jueves", "friday": "viernes", "saturday": "sábado", "sunday": "domingo"
        }
        dia_actual = dias_ingles_a_espanol.get(dia_actual, dia_actual)

        if dia_actual not in dias_habilitados:
            return False

        return hora_desde <= hora_actual <= hora_hasta

    except Exception as e:
        print(f"❌ Error al verificar monitoreo automático: {e}")
        return False
