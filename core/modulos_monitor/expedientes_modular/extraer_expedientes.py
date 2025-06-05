
from datetime import datetime
import json
import os
import time
from typing import Optional
from pathlib import Path
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
import asyncio

async def extraer_expedientes(
    page: Page,
    carpeta_salida: str = "panel_pjn/acciones_pjn/Actuaciones",
    delay: int = 3000,
    nombre_archivo: Optional[str] = None,
    detener_en_duplicado: bool = True,
    guardar_json: bool = True,
    fecha_corte: Optional[str] = None,
    tiempo_maximo_segundos: Optional[int] = None
) -> tuple[list[dict], Optional[str], str]:
    try:
        await page.wait_for_selector("table.table-striped tbody tr", timeout=10000)
    except PlaywrightTimeoutError:
        print("❌ No se detectó la tabla de expedientes.")
        return [], None, "tabla_no_disponible"

    expedientes = []
    expedientes_vistos = set()
    pagina = 1
    inicio = time.time()

    if fecha_corte:
        try:
            fecha_corte_dt = datetime.strptime(fecha_corte, "%d/%m/%Y")
        except Exception as e:
            print(f"⚠️ Fecha de corte inválida: {fecha_corte}")
            return [], None, "fecha_invalida"

    while True:
        print(f"📄 Página {pagina}...")

        filas = await page.query_selector_all("table.table-striped tbody tr")
        if not filas:
            break

        nuevos_en_pagina = 0
        for fila in filas:
            celdas = await fila.query_selector_all("td")
            if len(celdas) < 5:
                continue

            numero = (await celdas[0].inner_text()).strip()
            dependencia = (await celdas[1].inner_text()).strip()
            caratula = (await celdas[2].inner_text()).strip()
            situacion = (await celdas[3].inner_text()).strip()
            ultima_actuacion = (await celdas[4].inner_text()).strip()

            if fecha_corte:
                try:
                    ultima_act_dt = datetime.strptime(ultima_actuacion, "%d/%m/%Y")
                    if ultima_act_dt < fecha_corte_dt:
                        print(f"🛑 Corte en {ultima_actuacion} < {fecha_corte}")
                        print(f"📊 Página {pagina}: {nuevos_en_pagina} expedientes incluidos hasta el corte.")
                        return expedientes, None, "corte_fecha"
                except Exception as e:
                    print(f"⚠️ Error interpretando fecha: {ultima_actuacion}")
                    continue

            hash_expte = f"{numero}|{caratula}|{dependencia}"
            if hash_expte in expedientes_vistos:
                if detener_en_duplicado:
                    print("⚠️ Expediente repetido detectado. Finalizando.")
                    return expedientes, None, "repetido_detectado"
                continue

            expediente = {
                "numero": numero,
                "caratula": caratula,
                "dependencia": dependencia,
                "situacion": situacion,
                "ultima_actuacion": ultima_actuacion,
                "valido": all([numero, caratula, dependencia]),
                "extraido_en": datetime.now().isoformat()
            }
            expedientes.append(expediente)
            expedientes_vistos.add(hash_expte)
            nuevos_en_pagina += 1

        print(f"📊 Expedientes extraídos en página {pagina}: {nuevos_en_pagina}")

        if tiempo_maximo_segundos and (time.time() - inicio > tiempo_maximo_segundos):
            print(f"⏳ Tiempo máximo alcanzado ({tiempo_maximo_segundos}s). Finalizando.")
            return expedientes, None, "tiempo_maximo"

        try:
            boton_siguiente = await page.query_selector("a:has(span[title='Siguiente'])")
            if not boton_siguiente:
                break
            await boton_siguiente.click()
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(2)
            pagina += 1
        except Exception:
            break

    duracion = time.time() - inicio
    print(f"⏱️ Extracción completada en {duracion:.2f} segundos.")
    print(f"📦 Total expedientes extraídos: {len(expedientes)}")

    ruta = None
    if guardar_json:
        Path(carpeta_salida).mkdir(parents=True, exist_ok=True)
        if not nombre_archivo:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"expedientes_{timestamp}.json"
        ruta = os.path.join(carpeta_salida, nombre_archivo)
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(expedientes, f, indent=2, ensure_ascii=False)
        print(f"✅ Expedientes guardados en: {ruta}")

    return expedientes, ruta, "completo"
