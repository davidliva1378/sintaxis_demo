import os
import json
from datetime import datetime
from playwright.async_api import Page

async def extraer_expedientes(page: Page, carpeta_salida="panel_pjn/acciones_pjn/Actuaciones", delay=3000):
    print("🔍 Iniciando extracción robusta de expedientes...")
    await page.wait_for_selector("table.table-striped tbody tr", timeout=10000)

    expedientes = []
    expedientes_vistos = set()
    pagina_actual = 1

    while True:
        print(f"📄 Página {pagina_actual}...")

        try:
            filas = await page.query_selector_all("table.table-striped tbody tr")
        except:
            print("❌ Tabla de expedientes no encontrada.")
            break

        nuevos_en_pagina = 0

        for fila in filas:
            columnas = await fila.query_selector_all("td")
            if len(columnas) >= 5:
                numero = (await columnas[0].inner_text()).strip()
                dependencia = (await columnas[1].inner_text()).strip()
                caratula = (await columnas[2].inner_text()).strip()
                situacion = (await columnas[3].inner_text()).strip()
                ultima = (await columnas[4].inner_text()).strip()

                hash_expte = f"{numero}|{caratula}|{dependencia}"
                if hash_expte in expedientes_vistos:
                    print(f"⚠️ Expediente repetido detectado. Finalizando.")
                    return guardar_json(expedientes, carpeta_salida)

                expediente = {
                    "numero": numero,
                    "dependencia": dependencia,
                    "caratula": caratula,
                    "situacion": situacion,
                    "ultima_actuacion": ultima,
                    "valido": all([numero, caratula, dependencia]),
                    "extraido_en": datetime.now().isoformat()
                }

                expedientes.append(expediente)
                expedientes_vistos.add(hash_expte)
                nuevos_en_pagina += 1

        if nuevos_en_pagina == 0:
            print("⚠️ Página sin expedientes nuevos.")
            break

        boton_siguiente = await page.query_selector("a[id*=':j_idt285'][class]:not(.ui-state-disabled)")
        if not boton_siguiente:
            print("✅ Fin de páginas.")
            break

        try:
            await boton_siguiente.click()
            await page.wait_for_timeout(delay)
            pagina_actual += 1
        except Exception as e:
            print(f"❌ Error al cambiar de página: {e}")
            break

    return guardar_json(expedientes, carpeta_salida)

def guardar_json(expedientes, carpeta_salida):
    os.makedirs(carpeta_salida, exist_ok=True)
    nombre_archivo = f"expedientes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    ruta = os.path.join(carpeta_salida, nombre_archivo)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(expedientes, f, indent=2, ensure_ascii=False)
    print(f"✅ Archivo guardado: {ruta}")
    return ruta