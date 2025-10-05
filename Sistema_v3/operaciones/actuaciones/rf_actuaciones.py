import asyncio
import json
import os
import re
from datetime import date, datetime
from urllib.parse import parse_qs, urlparse

from playwright.async_api import Page, TimeoutError

from .actuaciones_utils import generar_hash_archivo, limpiar_texto, normalizar_fecha


def construir_nombre_archivo_normalizado(fecha, tipo, hash_val, archivo_url, nombre_descarga=None):
    """Genera un nombre de archivo normalizado preservando la extensión original."""
    parsed_url = urlparse(archivo_url) if archivo_url else None

    nombre_origen = nombre_descarga or ""
    if not nombre_origen and parsed_url:
        tipo_doc = parse_qs(parsed_url.query).get("tipoDoc", [])
        if tipo_doc and tipo_doc[0]:
            nombre_origen = tipo_doc[0]

    if not nombre_origen and parsed_url:
        nombre_origen = os.path.basename(parsed_url.path)

    if not nombre_origen:
        nombre_origen = "documento.pdf"

    extension = os.path.splitext(nombre_origen)[1]
    if not extension and parsed_url:
        extension = os.path.splitext(parsed_url.path)[1]

    if not extension:
        extension = ".pdf"

    if not extension.startswith("."):
        extension = f".{extension}"

    extension = extension.lower()
    tipo_archivo = extension[1:] if len(extension) > 1 else None
    nombre_normalizado = f"{fecha}_{tipo}_{hash_val}{extension}" if extension else None

    return nombre_normalizado, tipo_archivo


async def extraer_actuaciones_historicas(page_expediente, expediente_datos, indice_inicial=1):
    actuaciones = []
    try:
        await page_expediente.click("a:has-text('Ver históricas')")

        # Esperamos que aparezca la tabla o el mensaje de "no posee actuaciones"
        try:
            await page_expediente.wait_for_selector(
                "#expediente\\:action-historic-table tbody tr, div.alert.white-panel",
                timeout=8000
            )
        except Exception:
            return [], "Timeout esperando tabla o mensaje de actuaciones históricas"

        mensaje = await page_expediente.query_selector("div.alert.white-panel")
        if mensaje:
            texto = await mensaje.inner_text()
            if "no posee actuaciones históricas" in texto.lower():
                print("El expediente no posee actuaciones históricas.")
                return [], None

        expediente_numero = expediente_datos.get("numero", "desconocido")
        expediente_numero = re.sub(r'[^a-zA-Z0-9_-]', '_', expediente_numero)
        timestamp_extraccion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        pagina = 1
        indice_actual = indice_inicial
        while True:
            print(f"Página {pagina} (históricas): extrayendo...")

            filas = await page_expediente.query_selector_all("#expediente\\:action-historic-table tbody tr")
            if not filas:
                print("No se encontraron filas en actuaciones históricas.")
                break

            for fila in filas:
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
                hash_val = generar_hash_archivo(fecha, tipo, detalle)

                icono = await fila.query_selector("i.fa-download")
                tiene_archivo = bool(icono)

                if icono:
                    link = await page_expediente.evaluate_handle("(el) => el.closest('a')", icono)
                    if link:
                        archivo_url = await link.get_attribute("href")
                        if archivo_url:
                            nombre_descarga = await link.get_attribute("download")
                            nombre_archivo, tipo_archivo = construir_nombre_archivo_normalizado(
                                fecha,
                                tipo,
                                hash_val,
                                archivo_url,
                                nombre_descarga,
                            )
                        else:
                            archivo_url = None
                            nombre_archivo = None
                            tipo_archivo = None
                    else:
                        archivo_url = None
                        nombre_archivo = None
                        tipo_archivo = None

                actuaciones.append({
                    "Indice": indice_actual,
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
                    "ExtraidaEn": timestamp_extraccion,
                    "EsHistorica": True
                })

                indice_actual += 1

            boton_siguiente = await page_expediente.query_selector("a[id^='expediente:j_idt']:not(.ui-state-disabled):has-text('Siguiente')")
            if boton_siguiente:
                try:
                    fila_primera = await page_expediente.query_selector("#expediente\\:action-historic-table tbody tr td:nth-child(3)")
                    fecha_antes = await fila_primera.inner_text() if fila_primera else ""

                    await boton_siguiente.click()
                    pagina += 1

                    await page_expediente.wait_for_selector("#expediente\\:action-historic-table tbody tr", timeout=8000)
                    await page_expediente.wait_for_function(
                        """
                        (fechaAntes) => {
                            const celda = document.querySelector('#expediente\\\\:action-historic-table tbody tr td:nth-child(3)');
                            return celda && celda.innerText.trim() !== fechaAntes;
                        }
                        """,
                        arg=fecha_antes.strip(),
                        timeout=8000
                    )

                except Exception as e:
                    print(f"No se pudo avanzar de página histórica: {e}")
                    break
            else:
                print("No hay más páginas históricas.")
                break

        return actuaciones, None

    except Exception as e:
        return [], f"Error al extraer históricas: {type(e).__name__}: {str(e)}"



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
            hash_val = generar_hash_archivo(fecha, tipo, detalle)

            icono = await fila.query_selector("i.fa-download")
            tiene_archivo = bool(icono)

            if icono:
                link = await page_expediente.evaluate_handle("(el) => el.closest('a')", icono)
                if link:
                    archivo_url = await link.get_attribute("href")
                    if archivo_url:
                        nombre_descarga = await link.get_attribute("download")
                        nombre_archivo, tipo_archivo = construir_nombre_archivo_normalizado(
                            fecha,
                            tipo,
                            hash_val,
                            archivo_url,
                            nombre_descarga,
                        )
                    else:
                        archivo_url = None
                        nombre_archivo = None
                        tipo_archivo = None
                else:
                    archivo_url = None
                    nombre_archivo = None
                    tipo_archivo = None

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
            return todas, f"❌ Error en página {pagina}: {error}", None
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
            return todas, f"⏳ Timeout al intentar avanzar a la página {pagina + 1}", None
        except Exception as e:
            return todas, f"⚠️ Error inesperado al avanzar a la página {pagina + 1}: {type(e).__name__}: {str(e)}", None

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
    return todas, None, carpeta_actuaciones


async def extraer_actuaciones_completas(
    page_expediente,
    expediente_datos: dict,
    incluir_historicas: bool = True,
    directorio_base: str = "ActuacionesCompletas"
) -> tuple[list[dict], list[dict], str | None]:
    """
    Extrae actuaciones actuales e históricas (opcional) de un expediente y las guarda como JSON.
    También genera un único archivo con estructura detallada, campo EsHistorica y Descargado.
    """
    actuaciones_actuales = []
    actuaciones_historicas = []

    try:
        numero_original = expediente_datos['numero']
        numero_normalizado = numero_original.replace('/', '_')
        carpeta_expte = os.path.join(directorio_base, numero_normalizado)

        # Actuaciones actuales
        actuaciones_actuales, error_actuales, carpeta_final = await obtener_actuaciones_todas_paginas_async(
            page_expediente,
            expediente_datos,
            carpeta_destino=carpeta_expte
        )
        if error_actuales:
            return [], [], f"Error al extraer actuaciones actuales: {error_actuales}"
        if not carpeta_final:
            return [], [], "No se pudo determinar la carpeta de salida para las actuaciones actuales."

        for act in actuaciones_actuales:
            act["EsHistorica"] = False
            if act.get("TieneArchivo"):
                act["Descargado"] = False

        indice_base = len(actuaciones_actuales) + 1

        # Actuaciones históricas (si corresponde)
        if incluir_historicas:
            actuaciones_historicas, error_hist = await extraer_actuaciones_historicas(
                page_expediente, expediente_datos, indice_base
            )
            if error_hist:
                return actuaciones_actuales, [], f"Error al extraer actuaciones históricas: {error_hist}"

            for act in actuaciones_historicas:
                act["EsHistorica"] = True
                if act.get("TieneArchivo"):
                    act["Descargado"] = False
        else:
            actuaciones_historicas = []

        todas = actuaciones_actuales + actuaciones_historicas

        if actuaciones_historicas:
            indice_historico_esperado = len(actuaciones_actuales) + 1
            primer_indice_historico = actuaciones_historicas[0].get("Indice")
            if primer_indice_historico != indice_historico_esperado:
                print(
                    "⚠️ Verificar numeración histórica: se esperaba que iniciara en "
                    f"{indice_historico_esperado}, pero comenzó en {primer_indice_historico}."
                )

        expediente_info = {
            "numero": expediente_datos.get("numero"),
            "caratula": expediente_datos.get("caratula"),
            "dependencia": expediente_datos.get("dependencia"),
            "jurisdiccion": expediente_datos.get("jurisdiccion"),
            "situacion": expediente_datos.get("situacion"),
            "Cantidad de Actuaciones Obtenidas": len(todas),
            "Cantidad de Archivos Descargados": sum(1 for a in todas if a.get("TieneArchivo"))
        }

        estructura_json = {
            "Expediente": expediente_info,
            "Actuaciones": todas
        }

        json_path = os.path.join(carpeta_final, f"actuaciones-{numero_normalizado}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(estructura_json, f, indent=2, ensure_ascii=False)
        print(f"📄 JSON generado: {json_path}")

        return actuaciones_actuales, actuaciones_historicas, None

    except Exception as e:
        return [], [], f"Error general: {type(e).__name__}: {str(e)}"



async def aviso_si_tarda(idx, segundos):
    await asyncio.sleep(segundos)
    print(f"⏳ Descarga en curso para actuación {idx}... lleva más de {segundos} segundos.")

async def descargar_archivos_actuaciones(page: Page, actuaciones: list, carpeta_destino: str):
    if not actuaciones:
        print("⚠️ No se proporcionaron actuaciones para descargar.")
        return

    print(f"📥 Iniciando descarga de archivos ({len(actuaciones)} actuaciones)...")
    os.makedirs(carpeta_destino, exist_ok=True)

    for idx, act in enumerate(actuaciones, start=1):
        archivo_url = act.get("Archivo", "N/A")
        nombre_archivo = act.get("NombreArchivo")
        if not nombre_archivo:
            tipo_archivo = act.get("TipoArchivo")
            if tipo_archivo and tipo_archivo != "N/A":
                nombre_archivo = f"documento_{idx}.{tipo_archivo.lower()}"
            else:
                nombre_archivo = f"documento_{idx}.pdf"

        if archivo_url == "N/A":
            print(f"🚫 Actuación {idx}: sin archivo para descargar.")
            continue

        ruta_archivo = os.path.join(carpeta_destino, nombre_archivo)

        if os.path.exists(ruta_archivo):
            print(f"⏭️ Archivo ya existe: {nombre_archivo}")
            continue

        for intento in range(3):
            try:
                async with page.expect_download() as download_info:
                    await page.evaluate("""
                        (url) => {
                            const a = document.createElement('a');
                            a.href = url;
                            a.target = '_blank';
                            a.rel = 'noopener';
                            a.click();
                        }
                    """, archivo_url)

                download = await download_info.value

                # Aviso si tarda
                advertencia = asyncio.create_task(aviso_si_tarda(idx, 30))
                await download.save_as(ruta_archivo)
                advertencia.cancel()

                print(f"✅ Archivo descargado: {nombre_archivo}")
                break  # éxito
            except Exception as e:
                if intento == 2:
                    print(f"❌ Falló la descarga tras 3 intentos para actuación {idx}: {e}")
                else:
                    print(f"⚠️ Reintentando actuación {idx} ({intento + 1}/3)...")
                    await asyncio.sleep(4)




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