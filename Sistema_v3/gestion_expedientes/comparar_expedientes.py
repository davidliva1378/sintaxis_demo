import json

CAMPOS_COMPARABLES = ["caratula", "dependencia", "situacion", "ultima_actuacion"]

def comparar_con_base(json_actual, base_json):
    nuevos = []
    modificados = []
    eliminados = []

    base_por_numero = {exp["numero"]: exp for exp in base_json}
    actual_por_numero = {exp["numero"]: exp for exp in json_actual}

    # Detectar nuevos y modificados
    for numero, actual in actual_por_numero.items():
        if numero not in base_por_numero:
            nuevos.append(actual)
        else:
            base = base_por_numero[numero]
            cambios = {}
            for campo in CAMPOS_COMPARABLES:
                if actual.get(campo) != base.get(campo):
                    cambios[campo] = {
                        "antes": base.get(campo),
                        "despues": actual.get(campo)
                    }
            if cambios:
                modificados.append({
                    "numero": numero,
                    "caratula": base.get("caratula", "SIN CARÁTULA"),
                    "cambios": cambios
                })

    # Detectar eliminados
    for numero in base_por_numero:
        if numero not in actual_por_numero:
            eliminados.append(base_por_numero[numero])

    return nuevos, modificados, eliminados
