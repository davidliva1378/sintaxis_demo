import json
from datetime import datetime

def obtener_intervalo_monitor(config_path="config_monitor.json"):
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        modo = config.get("modo", "automatico")
        ahora = datetime.now()
        dia_actual = ahora.strftime("%A").lower()
        hora_actual = ahora.strftime("%H:%M")

        # Mapear días en inglés a español
        dias_map = {
            "monday": "lunes", "tuesday": "martes", "wednesday": "miércoles",
            "thursday": "jueves", "friday": "viernes", "saturday": "sábado", "sunday": "domingo"
        }
        dia_actual = dias_map.get(dia_actual, dia_actual)

        if modo == "laboral":
            return config["horario_laboral"]["intervalo_minutos"]

        elif modo == "no_laboral":
            return config["fuera_horario"]["intervalo_minutos"]

        elif modo == "personalizado":
            return config["personalizado"]["intervalo_minutos"]

        elif modo == "automatico":
            dias = config["horario_laboral"]["dias"]
            desde = config["horario_laboral"]["hora_inicio"]
            hasta = config["horario_laboral"]["hora_fin"]

            if dia_actual in dias and desde <= hora_actual <= hasta:
                return config["horario_laboral"]["intervalo_minutos"]
            else:
                return config["fuera_horario"]["intervalo_minutos"]

        return 60  # valor por defecto

    except Exception as e:
        print(f"❌ Error en obtener_intervalo_monitor: {e}")
        return 60
