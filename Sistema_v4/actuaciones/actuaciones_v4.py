import asyncio
import json
import os
import re
from contextlib import suppress
from datetime import date, datetime
from urllib.parse import parse_qs, urlparse

from playwright.async_api import Page, TimeoutError

from .actuaciones_utils import generar_hash_archivo, limpiar_texto, normalizar_fecha


FORMATO_JSON_VERSION = "1.1"


def construir_encabezado_actuaciones(
    expediente_datos: dict,
    actuaciones_actuales: list,
    actuaciones_historicas: list,
    incluye_historicas: bool,
    timestamp_generacion: str,
):
    """Genera los metadatos enriquecidos para el archivo JSON de actuaciones."""

    campos_base = {
        "numero": expediente_datos.get("numero"),
        "caratula": expediente_datos.get("caratula"),
        "dependencia": expediente_datos.get("dependencia"),
        "jurisdiccion": expediente_datos.get("jurisdiccion"),
        "situacion": expediente_datos.get("situacion"),
    }

    for clave, valor in list(campos_base.items()):
        if isinstance(valor, (date, datetime)):
            campos_base[clave] = valor.strftime("%Y-%m-%d")

    total_actuales = len(actuaciones_actuales)
    total_historicas = len(actuaciones_historicas)
    todas = list(actuaciones_actuales) + list(actuaciones_historicas)
    total_con_archivo = sum(1 for act in todas if act.get("TieneArchivo"))
    descargas_pendientes = sum(
        1 for act in todas if act.get("TieneArchivo") and not act.get("Descargado")
    )

    ultimo_hash_actual = actuaciones_actuales[0]["Hash"] if actuaciones_actuales else None
    ultima_fecha_actual = actuaciones_actuales[0]["Fecha"] if actuaciones_actuales else None

    campos_base.update(
        {
            "Cantidad de Actuaciones Obtenidas": total_actuales + total_historicas,
            "Cantidad de Archivos Descargados": total_con_archivo,
            "version_formato": FORMATO_JSON_VERSION,
            "fecha_extraccion": timestamp_generacion,
            "incluye_historicas": incluye_historicas,
            "total_actuales": total_actuales,
            "total_historicas": total_historicas,
            "total_actuaciones": total_actuales + total_historicas,
            "total_archivos_con_enlace": total_con_archivo,
            "descargas_pendientes": descargas_pendientes,
            "ultimo_hash_actual": ultimo_hash_actual,
            "ultima_fecha_actual": ultima_fecha_actual,
        }
    )

    return campos_base


EXTENSIONES_CONOCIDAS = {
    "7z": ".7z",
    "avi": ".avi",
    "bak": ".bak",
    "bmp": ".bmp",
    "cer": ".cer",
    "csv": ".csv",
    "der": ".der",
    "doc": ".doc",
    "docm": ".docm",
    "docx": ".docx",
    "eml": ".eml",
    "epub": ".epub",
    "gif": ".gif",
    "gz": ".gz",
    "heic": ".heic",
    "heif": ".heif",
    "htm": ".htm",
    "html": ".html",
    "ics": ".ics",
    "jpeg": ".jpeg",
    "jpg": ".jpg",
    "json": ".json",
    "log": ".log",
    "m4a": ".m4a",
    "mkv": ".mkv",
    "mov": ".mov",
    "mp3": ".mp3",
    "mp4": ".mp4",
    "msg": ".msg",
    "odt": ".odt",
    "ogg": ".ogg",
    "pdf": ".pdf",
    "pdfa": ".pdf",
    "pfx": ".pfx",
    "p12": ".p12",
    "p7m": ".p7m",
    "p7s": ".p7s",
    "png": ".png",
    "ppt": ".ppt",
    "pptx": ".pptx",
    "pps": ".pps",
    "ppsx": ".ppsx",
    "rar": ".rar",
    "rtf": ".rtf",
    "svg": ".svg",
    "tar": ".tar",
    "tif": ".tif",
    "tiff": ".tiff",
    "txt": ".txt",
    "wav": ".wav",
    "webm": ".webm",
    "xls": ".xls",
    "xlsx": ".xlsx",
    "xml": ".xml",
    "xps": ".xps",
    "zip": ".zip",
}

EXTENSIONES_ALIAS = {
    "pkcs7": "p7m",
    "smime": "p7m",
    "s-mime": "p7m",
    "pkcs12": "p12",
}

EXTENSIONES_GENERICAS = {".seam", ".jsp", ".do", ".php", ".aspx", ".ashx"}


def obtener_extension_valida(valor):
    if valor is None:
        return None

    valor = str(valor).strip().lower()
    if not valor:
        return None

    candidatos = []

    def agregar_candidato(texto):
        if not texto:
            return
        texto = texto.strip().lower()
        if not texto:
            return
        if texto.startswith("."):
            texto = texto[1:]
        if texto and texto not in candidatos:
            candidatos.append(texto)

    agregar_candidato(valor)

    for separador in ("/", ".", "-", "_", " "):
        if separador in valor:
            for parte in valor.split(separador):
                agregar_candidato(parte)

    for candidato in candidatos:
        base = EXTENSIONES_ALIAS.get(candidato, candidato)
        if base in EXTENSIONES_CONOCIDAS:
            return EXTENSIONES_CONOCIDAS[base]

    return None


def construir_nombre_archivo_normalizado(fecha, tipo, hash_val, archivo_url, nombre_descarga=None):
    """Genera un nombre de archivo normalizado preservando la extensión original."""

    parsed_url = urlparse(archivo_url) if archivo_url else None

    nombre_origen = nombre_descarga or ""
    extension_candidatas = []
    tipo_doc_indico_fallback = False

    extension_nombre = obtener_extension_valida(os.path.splitext(nombre_origen)[1])
    if extension_nombre:
        extension_candidatas.append(extension_nombre)

    if parsed_url:
        tipo_doc = parse_qs(parsed_url.query).get("tipoDoc", [])
        if tipo_doc and tipo_doc[0]:
            tipo_doc_valor = tipo_doc[0].strip()
            if tipo_doc_valor:
                extension_tipo_doc = None
                if "." in tipo_doc_valor:
                    if not nombre_origen:
                        nombre_origen = tipo_doc_valor
                    extension_tipo_doc = obtener_extension_valida(os.path.splitext(tipo_doc_valor)[1])
                else:
                    extension_tipo_doc = obtener_extension_valida(tipo_doc_valor)

                if extension_tipo_doc:
                    extension_candidatas.append(extension_tipo_doc)
                else:
                    tipo_doc_indico_fallback = True

    if not nombre_origen and parsed_url:
        nombre_origen = os.path.basename(parsed_url.path)
        extension_desde_nombre = obtener_extension_valida(os.path.splitext(nombre_origen)[1])
        if extension_desde_nombre:
            extension_candidatas.append(extension_desde_nombre)

    if parsed_url:
        extension_desde_url = obtener_extension_valida(os.path.splitext(parsed_url.path)[1])
        if extension_desde_url:
            extension_candidatas.append(extension_desde_url)

    extension = None
    for candidata in extension_candidatas:
        if candidata and candidata not in EXTENSIONES_GENERICAS:
            extension = candidata
            break

    if not extension and tipo_doc_indico_fallback:
        extension = ".pdf"

    if not extension:
        extension = ".pdf"

    tipo_archivo = extension[1:] if len(extension) > 1 else None
    nombre_normalizado = f"{fecha}_{tipo}_{hash_val}{extension}" if extension else None

    return nombre_normalizado, tipo_archivo



def _escape_selector_for_css(selector: str) -> str:
    """Escapa los dos puntos presentes en un selector CSS para Playwright."""

    return re.sub(r"(?<!\\):", r"\\:", selector)


def _escape_selector_for_js(selector: str) -> str:
    """Escapa los dos puntos presentes en un selector CSS para ejecutarlo en JS."""

    return re.sub(r"(?<!\\):", r"\\\\:", selector)


async def _obtener_paginador_activo(page: Page, tabla_id: str) -> tuple[str | None, str | None]:
    """Obtiene el selector y el número de página activo de un datatable PrimeFaces."""

    sufijos = ("_paginator_bottom", "_paginator_top")
    for sufijo in sufijos:
        selector_base = f"#{tabla_id}{sufijo} .ui-paginator-page.ui-state-active"
        selector_css = _escape_selector_for_css(selector_base)
        elemento = await page.query_selector(selector_css)
        if elemento:
            pagina_activa = (await elemento.inner_text() or "").strip()
            selector_js = _escape_selector_for_js(selector_base)
            return selector_js, pagina_activa
    return None, None


async def _esperar_cambio_pagina(
    page: Page,
    tabla_id: str,
    html_anterior: str,
    paginador_selector_js: str | None,
    pagina_anterior: str | None,
) -> None:
    """Espera a que se actualice la tabla tras navegar a otra página."""

    if paginador_selector_js and pagina_anterior:
        try:
            await page.wait_for_function(
                r"""
                ({ selector, paginaAnterior }) => {
                    const elemento = document.querySelector(selector);
                    return elemento && elemento.textContent.trim() !== paginaAnterior;
                }
                """,
                arg={"selector": paginador_selector_js, "paginaAnterior": pagina_anterior},
                timeout=8000,
            )
            return
        except TimeoutError:
            # Si el paginador no cambia, reintentamos comparando el contenido de la tabla.
            pass

    await page.wait_for_function(
        r"""
        ({ tablaId, htmlPrevio }) => {
            const tabla = document.getElementById(tablaId);
            return tabla && tabla.innerHTML !== htmlPrevio;
        }
        """,
        arg={
            "tablaId": tabla_id,
            "htmlPrevio": html_anterior,
        },
        timeout=8000,
    )


async def construir_actuacion_desde_fila(
    page_expediente: Page,
    fila,
    indice: int,
    timestamp_extraccion: str,
    es_historica: bool = False,
):
    celdas = await fila.query_selector_all("td")
    if len(celdas) < 6:
        return None

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

    return {
        "Indice": indice,
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
        "EsHistorica": es_historica,
    }


async def extraer_actuaciones_historicas(page_expediente, expediente_datos, indice_inicial=1):
    actuaciones = []
    try:
        await page_expediente.click("a:has-text('Ver históricas')")

        # Esperamos que aparezca la tabla o el mensaje de "no posee actuaciones"
        try:
            await page_expediente.wait_for_selector(
                r"#expediente\:action-historic-table tbody tr, div.alert.white-panel",
                timeout=8000,
            )
        except Exception:
            return [], "Timeout esperando tabla o mensaje de actuaciones históricas"

        mensaje = await page_expediente.query_selector("div.alert.white-panel")
        if mensaje:
            texto = await mensaje.inner_text()
            if "no posee actuaciones históricas" in texto.lower():
                print("El expediente no posee actuaciones históricas.")
                return [], None

        expediente_numero = expediente_datos.get("numero")
        if not expediente_numero:
            expediente_numero = "desconocido"
        expediente_numero = re.sub(
            r"[^a-zA-Z0-9_-]", "_", str(expediente_numero)
        )
        timestamp_extraccion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        pagina = 1
        indice_actual = indice_inicial
        tabla_id = "expediente:action-historic-table"
        tabla_selector_css = _escape_selector_for_css(f"#{tabla_id}")
        filas_selector = f"{tabla_selector_css} tbody tr"
        while True:
            print(f"Página {pagina} (históricas): extrayendo...")

            filas = await page_expediente.query_selector_all(filas_selector)
            if not filas:
                print("No se encontraron filas en actuaciones históricas.")
                break

            for fila in filas:
                actuacion = await construir_actuacion_desde_fila(
                    page_expediente,
                    fila,
                    indice_actual,
                    timestamp_extraccion,
                    es_historica=True,
                )
                if actuacion:
                    actuaciones.append(actuacion)
                    indice_actual += 1

            boton_siguiente = await page_expediente.query_selector(
                "a[id^='expediente:j_idt']:not(.ui-state-disabled):has-text('Siguiente')"
            )
            if boton_siguiente:
                try:
                    html_anterior = await page_expediente.inner_html(tabla_selector_css)
                    paginador_selector_js, pagina_activa = await _obtener_paginador_activo(
                        page_expediente, tabla_id
                    )
                    await boton_siguiente.click()
                    pagina += 1

                    await page_expediente.wait_for_selector(filas_selector, timeout=8000)
                    await _esperar_cambio_pagina(
                        page_expediente,
                        tabla_id,
                        html_anterior,
                        paginador_selector_js,
                        pagina_activa,
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
        expediente_numero = re.sub(r"[^a-zA-Z0-9_-]", "_", expediente_numero)

        timestamp_extraccion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for idx, fila in enumerate(filas, start=indice_inicial):
            actuacion = await construir_actuacion_desde_fila(
                page_expediente,
                fila,
                idx,
                timestamp_extraccion,
                es_historica=False,
            )
            if actuacion:
                actuaciones.append(actuacion)
        return actuaciones, None
    except Exception as e:
        return [], f"{type(e).__name__}: {str(e)}"

async def obtener_actuaciones_todas_paginas_async(page_expediente, expediente_datos, carpeta_destino="Actuaciones"):
    todas = []
    pagina = 1
    indice_actual = 1

    tabla_id = "expediente:action-table"
    tabla_selector_css = _escape_selector_for_css(f"#{tabla_id}")
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
            html_anterior = await page_expediente.inner_html(tabla_selector_css)
            paginador_selector_js, pagina_activa = await _obtener_paginador_activo(
                page_expediente, tabla_id
            )
            await boton_siguiente.click()
            await page_expediente.wait_for_load_state("domcontentloaded")
            await _esperar_cambio_pagina(
                page_expediente,
                tabla_id,
                html_anterior,
                paginador_selector_js,
                pagina_activa,
            )
            pagina += 1
        except TimeoutError:
            return todas, f"⏳ Timeout al intentar avanzar a la página {pagina + 1}", None
        except Exception as e:
            return todas, f"⚠️ Error inesperado al avanzar a la página {pagina + 1}: {type(e).__name__}: {str(e)}", None

    expediente_numero = expediente_datos.get("numero")
    if not expediente_numero:
        expediente_numero = "expediente"
    expediente_numero = re.sub(r"[^a-zA-Z0-9_-]", "_", str(expediente_numero))
    timestamp_generacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    encabezado = construir_encabezado_actuaciones(
        expediente_datos,
        actuaciones_actuales=todas,
        actuaciones_historicas=[],
        incluye_historicas=False,
        timestamp_generacion=timestamp_generacion,
    )

    carpeta_actuaciones = os.path.abspath(carpeta_destino)
    os.makedirs(carpeta_actuaciones, exist_ok=True)
    json_path = os.path.join(carpeta_actuaciones, f"actuaciones-{expediente_numero}.json")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"Expediente": encabezado, "Actuaciones": todas}, f, indent=2, ensure_ascii=False)

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
        numero_original = expediente_datos.get("numero")
        if not numero_original:
            numero_original = "expediente"
        numero_normalizado = re.sub(r"[^a-zA-Z0-9_-]", "_", str(numero_original))
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

        timestamp_generacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        encabezado = construir_encabezado_actuaciones(
            expediente_datos,
            actuaciones_actuales=actuaciones_actuales,
            actuaciones_historicas=actuaciones_historicas,
            incluye_historicas=bool(actuaciones_historicas),
            timestamp_generacion=timestamp_generacion,
        )

        estructura_json = {"Expediente": encabezado, "Actuaciones": todas}

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
        if not archivo_url or archivo_url == "N/A":
            print(f"🚫 Actuación {idx}: sin archivo para descargar.")
            continue

        nombre_archivo = act.get("NombreArchivo")
        tipo_archivo_valor = act.get("TipoArchivo")

        if not nombre_archivo or nombre_archivo == "N/A":
            nombre_archivo = None

        if not tipo_archivo_valor or tipo_archivo_valor == "N/A":
            tipo_archivo_valor = None

        base_nombre = None
        extension_desde_nombre = None
        if nombre_archivo:
            base_nombre, extension_extraida = os.path.splitext(nombre_archivo)
            extension_desde_nombre = obtener_extension_valida(extension_extraida)
            base_nombre = base_nombre.strip().rstrip(".")
            if not base_nombre:
                base_nombre = None

        extension_desde_tipo = obtener_extension_valida(tipo_archivo_valor)

        extension_final = None
        for candidata in (extension_desde_tipo, extension_desde_nombre):
            if candidata and candidata not in EXTENSIONES_GENERICAS:
                extension_final = candidata
                break

        if not extension_final:
            extension_final = ".pdf"

        if not base_nombre:
            base_nombre = f"documento_{idx}"

        nombre_archivo = f"{base_nombre}{extension_final}"
        tipo_archivo_normalizado = extension_final[1:] if extension_final.startswith(".") else extension_final

        act["NombreArchivo"] = nombre_archivo
        act["TipoArchivo"] = tipo_archivo_normalizado

        ruta_archivo = os.path.join(carpeta_destino, nombre_archivo)

        if os.path.exists(ruta_archivo):
            print(f"⏭️ Archivo ya existe: {nombre_archivo}")
            continue

        for intento in range(3):
            advertencia = None
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

                print(f"✅ Archivo descargado: {nombre_archivo}")
                break  # éxito
            except Exception as e:
                if intento == 2:
                    print(f"❌ Falló la descarga tras 3 intentos para actuación {idx}: {e}")
                else:
                    print(f"⚠️ Reintentando actuación {idx} ({intento + 1}/3)...")
                    await asyncio.sleep(4)
            finally:
                if advertencia is not None:
                    advertencia.cancel()
                    with suppress(asyncio.CancelledError):
                        await advertencia




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
