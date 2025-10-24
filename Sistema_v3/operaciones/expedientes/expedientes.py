
import os
import json
import time
from datetime import datetime
from typing import Optional
from pathlib import Path
import asyncio
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

_FP_MAX_LEN = 4_096
_TBODY_SELECTOR = "table.table-striped tbody"


def _build_fingerprint(html: str, max_len: Optional[int] = _FP_MAX_LEN) -> str:
    signature = f"{len(html)}::{html}"
    if max_len is None:
        return signature
    return signature[:max_len]


async def _tbody_fingerprint(page: Page, selector: str = _TBODY_SELECTOR) -> Optional[str]:
    tbody = await page.query_selector(selector)
    if not tbody:
        return None
    html = await tbody.inner_html()
    return _build_fingerprint(html)


async def _esperar_cambio_tbody(
    page: Page,
    selector: str,
    fingerprint_anterior: Optional[str],
    intentos: int = 10,
    espera_segundos: float = 0.5,
) -> Optional[str]:
    if fingerprint_anterior is None:
        return await _tbody_fingerprint(page, selector)

    for _ in range(intentos):
        await asyncio.sleep(espera_segundos)
        fingerprint_actual = await _tbody_fingerprint(page, selector)
        if fingerprint_actual and fingerprint_actual != fingerprint_anterior:
            return fingerprint_actual
    return None

async def extraer_expedientes(
    page: Page,
    carpeta_salida: str = "datos_extraidos/monitoreo",
    delay: int = 3000,
    nombre_archivo: Optional[str] = None,
    detener_en_duplicado: bool = True,
    guardar_json: bool = True,
    fecha_corte: Optional[str] = None,
    tiempo_maximo_segundos: Optional[int] = None,
    orden: Optional[str] = None
) -> tuple[list[dict], Optional[str], str]:
    try:
        await page.wait_for_selector("table.table-striped tbody tr", timeout=10000)
    except PlaywrightTimeoutError:
        print("❌ No se detectó la tabla de expedientes.")
        return [], None, "tabla_no_disponible"

    if orden:
        orden_map = {
            "fecha": "FECHA",
            "caratula": "CARATULA",
            "oficina": "OFICINA",
            "situacion": "SITUACION"
        }
        valor_orden = orden_map.get(orden.lower())
        if valor_orden:
            try:
                await page.select_option("#j_idt150\:order_by_form\:camara", value=valor_orden)
                await page.click("a:has-text('Ordenar')")
                await page.wait_for_selector("table.table-striped tbody tr", timeout=10000)
                print(f"🔽 Tabla ordenada por {orden.upper()}")
            except Exception as e:
                print(f"⚠️ No se pudo ordenar la tabla por {orden}: {e}")

    expedientes = []
    expedientes_vistos = set()
    pagina = 1
    inicio = time.time()

    if fecha_corte:
        try:
            fecha_corte_dt = datetime.strptime(fecha_corte, "%d/%m/%Y")
        except Exception:
            print(f"⚠️ Fecha de corte inválida: {fecha_corte}")
            return [], None, "fecha_invalida"

    while True:
        print(f"📄 Página {pagina}...")
        filas = await page.query_selector_all(f"{_TBODY_SELECTOR} tr")
        if not filas:
            break

        nuevos_en_pagina = 0
        duplicados_en_pagina = 0
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
                except Exception:
                    continue

            hash_expte = f"{numero}|{caratula}|{dependencia}"
            if hash_expte in expedientes_vistos:
                duplicados_en_pagina += 1
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

        if (
            detener_en_duplicado
            and duplicados_en_pagina > 0
            and nuevos_en_pagina == 0
        ):
            print("ℹ️ Sin expedientes nuevos en la página. Se alcanzó el fin del listado.")
            return expedientes, None, "fin_listado"

        if tiempo_maximo_segundos and (time.time() - inicio > tiempo_maximo_segundos):
            print(f"⏳ Tiempo máximo alcanzado ({tiempo_maximo_segundos}s). Finalizando.")
            return expedientes, None, "tiempo_maximo"

        try:
            boton_siguiente = await page.query_selector("a:has(span[title='Siguiente'])")
            if not boton_siguiente:
                break
            fingerprint_actual = await _tbody_fingerprint(page, _TBODY_SELECTOR)
            await boton_siguiente.click()
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(2)
            nuevo_fingerprint = await _esperar_cambio_tbody(
                page, _TBODY_SELECTOR, fingerprint_actual
            )
            if not nuevo_fingerprint:
                print(
                    "ℹ️ No se detectaron cambios en la tabla tras hacer clic en 'Siguiente'."
                )
                print("ℹ️ Se asume fin del listado de expedientes.")
                return expedientes, None, "fin_listado"
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
