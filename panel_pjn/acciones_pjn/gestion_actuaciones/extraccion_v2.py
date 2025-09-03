#refactor
import os
import re
import json
import asyncio
from datetime import datetime, date
from urllib.parse import urlparse, parse_qs
import hashlib
from playwright.async_api import TimeoutError
from panel_pjn.acciones_pjn.gestion_actuaciones.utilidades import limpiar_texto, normalizar_fecha, generar_hash_archivo


async def extraer_actuaciones_pagina(page_expediente, expediente_datos, indice_inicial=1):
    actuaciones = []
    try:
        await page_expediente.wait_for_selector(r"#expediente\:action-table tbody tr", timeout=8000)
        filas = await page_expediente.query_selector_all(r"#expediente\:action-table tbody tr")
        if not filas:
            return [], None

        expediente_numero = expediente_datos.get("numero", "desconocido")
        expediente_numero = re.sub(r'[^a-zA-Z0-9_-]', '_', expediente_numero)

        timestamp_extraccion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for idx, fila in enumerate(filas, start=indice_inicial):
            celdas = await fila.query_selector_all("td")
            if len(celdas) < 6:
                continue

            oficina = limpiar_texto(await celdas[1].inner_text())
            oficina_completa = await celdas[1].get_attribute("title") or oficina
            fecha_cruda = limpiar_texto(await celdas[2].inner_text())
            fecha = normalizar_fecha(fecha_cruda)
            tipo = limpiar_texto(await celdas[3].inner_text()).replace(" ", "_").upper()
            detalle = limpiar_texto(await celdas[4].inner_text())
            foja = limpiar_texto(await celdas[5].inner_text())

            archivo_url = None
            nombre_archivo = None
            tipo_archivo = None

            icono = await fila.query_selector("i.fa-download")
            tiene_archivo = bool(icono)

            if icono:
                link = await page_expediente.evaluate_handle("(el) => el.closest('a')", icono)
                if link:
                    archivo_url = await link.get_attribute("href")
                    nombre_archivo = await link.get_attribute("download")
                    if not nombre_archivo and archivo_url:
                        parsed = urlparse(archivo_url)
                        nombre_archivo = parse_qs(parsed.query).get("tipoDoc", ["documento.pdf"])[0]
                    tipo_archivo = os.path.splitext(nombre_archivo)[1][1:].lower() if nombre_archivo else None
                    hash_val = generar_hash_archivo(fecha, tipo, detalle)
                    nombre_archivo = f"{fecha}_{tipo}_{hash_val}.pdf"
            else:
                hash_val = generar_hash_archivo(fecha, tipo, detalle)

            actuaciones.append({
                "Indice": idx,
                "Oficina": oficina,
                "OficinaCompleta": oficina_completa,
                "Fecha": fecha,
                "Tipo": tipo,
                "Detalle": detalle,
                "Foja": foja,
                "Archivo": archivo_url if archivo_url else "N/A",
                "NombreArchivo": nombre_archivo if archivo_url else "N/A",
                "TieneArchivo": tiene_archivo,
                "TipoArchivo": tipo_archivo if tipo_archivo else "N/A",
                "Hash": hash_val,
                "ExtraidaEn": timestamp_extraccion
            })
        return actuaciones, None
    except Exception as e:
        return [], f"{type(e).__name__}: {str(e)}"


async def obtener_actuaciones_todas_paginas_async(page_expediente, expediente_datos, carpeta_destino="Actuaciones"):
    todas = []
    pagina = 1
    indice_actual = 1

    while True:
        print(f"📄 Página {pagina}: extrayendo...")
        nuevas, error = await extraer_actuaciones_pagina(page_expediente, expediente_datos, indice_actual)
        if error:
            return todas, f"❌ Error en página {pagina}: {error}"
        if not nuevas:
            break
        todas.extend(nuevas)
        indice_actual += len(nuevas)

        boton_siguiente = await page_expediente.query_selector("a:has(span[title='Siguiente']):not(.ui-state-disabled)")

        if not boton_siguiente:
            print("✅ No hay más páginas.")
            break

        try:
            html_anterior = await page_expediente.inner_html(r"#expediente\:action-table")
            await boton_siguiente.click()
            await page_expediente.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(2)
            await page_expediente.wait_for_function(
                f'document.querySelector("#expediente\\\\:action-table").innerHTML !== `{html_anterior}`',
                timeout=8000
            )
            pagina += 1
        except TimeoutError:
            return todas, f"⏳ Timeout al intentar avanzar a la página {pagina + 1}"
        except Exception as e:
            return todas, f"⚠️ Error inesperado al avanzar a la página {pagina + 1}: {type(e).__name__}: {str(e)}"

    expediente_numero = expediente_datos.get("numero", "expediente").replace("/", "_")
    expediente_datos["Cantidad de Actuaciones Obtenidas"] = len(todas)
    expediente_datos["Cantidad de Archivos Descargados"] = sum(1 for act in todas if act["TieneArchivo"])

    for key, value in expediente_datos.items():
        if isinstance(value, (date, datetime)):
            expediente_datos[key] = value.strftime("%Y-%m-%d")

    carpeta_actuaciones = os.path.abspath(carpeta_destino)
    os.makedirs(carpeta_actuaciones, exist_ok=True)
    json_path = os.path.join(carpeta_actuaciones, f"actuaciones-{expediente_numero}.json")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"Expediente": expediente_datos, "Actuaciones": todas}, f, indent=2, ensure_ascii=False)

    print(f"✅ Archivo JSON guardado: {json_path}")
    print(f"📂 Total de actuaciones: {len(todas)}")
    return todas, None, carpeta_destino
