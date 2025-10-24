import os
import re
import json
from datetime import datetime, date
from urllib.parse import urlparse, parse_qs
import hashlib

async def extraer_actuaciones_pagina(page_expediente, expediente_datos):
    actuaciones = []

    try:
        await page_expediente.wait_for_selector(r"#expediente\:action-table tbody tr", timeout=8000)
        filas = await page_expediente.query_selector_all(r"#expediente\:action-table tbody tr")
        if not filas:
            return []

        def limpiar_texto(texto):
            return re.sub(r'^(Oficina:|Fecha:|Tipo actuacion:|Detalle:|Foja:)?\s*', '', texto.strip().replace("\n", " "))

        def normalizar_fecha(texto):
            try:
                return datetime.strptime(texto, "%d/%m/%Y").strftime("%Y-%m-%d")
            except Exception:
                return texto

        expediente_numero = expediente_datos.get("numero", "desconocido")
        expediente_numero = re.sub(r'[^a-zA-Z0-9_-]', '_', expediente_numero)

        for idx, fila in enumerate(filas, start=1):
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

            icono = await fila.query_selector("i.fa-download")
            if icono:
                link = await page_expediente.evaluate_handle("(el) => el.closest('a')", icono)
                if link:
                    archivo_url = await link.get_attribute("href")
                    nombre_archivo = await link.get_attribute("download")
                    if not nombre_archivo and archivo_url:
                        parsed = urlparse(archivo_url)
                        nombre_archivo = parse_qs(parsed.query).get("tipoDoc", ["documento.pdf"])[0]
                    hash_val = hashlib.sha256(f"{fecha}_{tipo}_{detalle}".encode("utf-8")).hexdigest()[:6]
                    nombre_archivo = f"{expediente_numero}_Acto_{idx}_{fecha}_{tipo}_{hash_val}.pdf"

            actuaciones.append({
                "Oficina": oficina,
                "OficinaCompleta": oficina_completa,
                "Fecha": fecha,
                "Tipo": tipo,
                "Detalle": detalle,
                "Foja": foja,
                "Archivo": archivo_url if archivo_url else "N/A",
                "NombreArchivo": nombre_archivo if archivo_url else "N/A"
            })
        return actuaciones
    except Exception as e:
        print(f"⚠️ Error al extraer actuaciones de la página: {e}")
        return []

async def obtener_actuaciones_todas_paginas_async(page_expediente, expediente_datos, carpeta_destino="Actuaciones"):
    todas = []
    pagina = 1

    while True:
        print(f"📄 Página {pagina}: extrayendo...")
        nuevas = await extraer_actuaciones_pagina(page_expediente, expediente_datos)
        if not nuevas:
            break
        todas.extend(nuevas)

        boton_siguiente = await page_expediente.query_selector("a[id^='expediente:j_idt214:j_idt231']:not(.ui-state-disabled)")
        if not boton_siguiente:
            print("✅ No hay más páginas.")
            break

        try:
            await boton_siguiente.click()
            await page_expediente.wait_for_timeout(3000)
            pagina += 1
        except Exception as e:
            print(f"⚠️ No se pudo avanzar a la página siguiente: {e}")
            break

    expediente_numero = expediente_datos.get("numero", "expediente").replace("/", "_")
    expediente_datos["Cantidad de Actuaciones Obtenidas"] = len(todas)
    expediente_datos["Cantidad de Archivos Descargados"] = sum(1 for act in todas if act["Archivo"] != "N/A")

    for key, value in expediente_datos.items():
        if isinstance(value, (date, datetime)):
            expediente_datos[key] = value.strftime("%Y-%m-%d")

    carpeta_actuaciones = os.path.join(os.getcwd(), carpeta_destino, expediente_numero)
    os.makedirs(carpeta_actuaciones, exist_ok=True)
    json_path = os.path.join(carpeta_actuaciones, f"actuaciones-{expediente_numero}.json")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"Expediente": expediente_datos, "Actuaciones": todas}, f, indent=2, ensure_ascii=False)

    print(f"✅ Archivo JSON guardado: {json_path}")
    print(f"📂 Total de actuaciones: {len(todas)}")
    return todas