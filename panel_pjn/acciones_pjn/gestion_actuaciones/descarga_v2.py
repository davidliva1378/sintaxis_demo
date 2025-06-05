import os
import json
from panel_pjn.acciones_pjn.gestion_actuaciones.bk.descarga import descargar_archivos_actuaciones

async def descargar_archivos_de_json(page, carpeta_destino: str):
    """
    Lee el archivo unificado desde la carpeta del expediente
    y descarga los archivos vinculados usando Playwright.
    Marca las actuaciones descargadas como "Descargado": true.
    """
    archivos_json = [f for f in os.listdir(carpeta_destino) if f.startswith("actuaciones-") and f.endswith(".json")]
    if archivos_json:
        ruta_json = os.path.join(carpeta_destino, archivos_json[0])
        with open(ruta_json, "r", encoding="utf-8") as f:
            data = json.load(f)
            actuaciones = data.get("Actuaciones", [])
            actuaciones_filtradas = []

            for act in actuaciones:
                if act.get("TieneArchivo") and act.get("NombreArchivo"):
                    archivo_path = os.path.join(carpeta_destino, act["NombreArchivo"])
                    if not os.path.exists(archivo_path):
                        actuaciones_filtradas.append(act)
                    else:
                        act["Descargado"] = True
                        print(f"🟡 Ya existe: {act['NombreArchivo']}")

            if actuaciones_filtradas:
                print(f"\n🔽 Descargando {len(actuaciones_filtradas)} archivo(s)...")
                await descargar_archivos_actuaciones(page, actuaciones_filtradas, carpeta_destino)
                for act in actuaciones_filtradas:
                    act["Descargado"] = True
            else:
                print("✅ Todos los archivos ya existen.")

        # Guardar archivo actualizado
        with open(ruta_json, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("📝 JSON actualizado con estado de descarga.")
    else:
        print("⚠️ No se encontró archivo de actuaciones unificado.")
