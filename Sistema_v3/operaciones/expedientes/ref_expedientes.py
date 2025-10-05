
from datetime import datetime
import json
import os
import time
from pathlib import Path
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
import asyncio
from typing import Dict, List, Optional

async def extraer_expedientes(
    page: Page,
    carpeta_salida: str = "panel_pjn/acciones_pjn/Actuaciones",
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

    # 🔽 Ordenamiento según parámetro
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




#funcion que extrae los datos del expediente, se utiliza para validar y para ver si hay un cambio de jurisdiccion
async def extraer_datos_expediente(page):
    try:
        await page.wait_for_load_state("load")
        await page.wait_for_timeout(2000)

        numero = await page.query_selector("span[style='color:#000000;']")
        caratula = await page.query_selector(r"#expediente\:j_idt96\:detailCover")
        dependencia = await page.query_selector(r"#expediente\:j_idt96\:detailDependencia")
        jurisdiccion = await page.query_selector(r"#expediente\:j_idt96\:detailCamera")
        situacion = await page.query_selector(r"#expediente\:j_idt96\:detailSituation")

        expediente = {
            "numero": await numero.inner_text() if numero else "No encontrado",
            "caratula": await caratula.inner_text() if caratula else "No encontrada",
            "dependencia": await dependencia.inner_text() if dependencia else "No encontrada",
            "jurisdiccion": await jurisdiccion.inner_text() if jurisdiccion else "No encontrada",
            "situacion": await situacion.inner_text() if situacion else "No encontrada"
        }

        return expediente
    except Exception as e:
        print(f"⚠️ Error al extraer datos del expediente: {e}")
        return None


 #funcion para seleccionar un expedientes desde varias filas
async def abrir_expediente_desde_fila(fila, page):
    if not fila:
        print("❌ No se proporcionó ninguna fila válida.")
        return False

    enlace = await fila.query_selector("a")
    if enlace:
        print("👁 Haciendo clic para abrir el expediente...")
        await enlace.click()
        await page.wait_for_load_state("load")
        await page.wait_for_timeout(2000)

        # Verificación: intentar extraer datos del expediente
        datos = await extraer_datos_expediente(page)
        if datos:
            print("✅ Datos del expediente extraídos correctamente.")
            return True
        else:
            print("⚠️ No se pudieron extraer datos. Posible error de apertura.")
            return False
    else:
        print("⚠️ No se encontró enlace para abrir el expediente en la fila.")
        return False


async def mostrar_y_elegir_expediente(page: Page, filas: List) -> Optional[Dict]:
    """
    Muestra los expedientes encontrados y permite al usuario seleccionar uno para abrir y extraer datos.

    :param page: Página Playwright actual.
    :param filas: Lista de filas encontradas.
    :return: Diccionario de datos extraídos del expediente seleccionado, o None.
    """

    if not filas:
        print("❌ No hay filas disponibles para seleccionar.")
        return None

    if len(filas) == 1:
        print("✅ Solo un expediente encontrado. Abriendo directamente...")
        fila = filas[0]
    else:
        print("🔎 Se encontraron múltiples expedientes:")
        opciones = []

        for idx, fila in enumerate(filas, start=1):
            columnas = await fila.query_selector_all("td")
            if len(columnas) >= 3:
                nro = (await columnas[0].inner_text()).strip()
                anio_fila = (await columnas[1].inner_text()).strip()
                caratula_fila = (await columnas[2].inner_text()).strip()
                print(f"[{idx}] Número: {nro} / Año: {anio_fila} / Carátula: {caratula_fila}")
                opciones.append(fila)

        seleccion = input("👉 Ingrese el número de opción que desea abrir (0 para cancelar): ")
        try:
            idx_elegido = int(seleccion) - 1
            if idx_elegido == -1:
                print("❌ Operación cancelada por el usuario.")
                return None
            fila = opciones[idx_elegido]
        except (ValueError, IndexError):
            print("❌ Selección inválida.")
            return None

    # Abrir el expediente seleccionado
    exito_apertura = await abrir_expediente_desde_fila(fila, page)
    if not exito_apertura:
        print("⚠️ No se pudo abrir el expediente seleccionado.")
        return None

    # Extraer datos
    datos = await extraer_datos_expediente(page)
    if datos:
        print("✅ Datos extraídos correctamente del expediente.")
        return datos
    else:
        print("⚠️ No se pudieron extraer datos luego de abrir el expediente.")
        return None


async def buscar_expediente_por_numero(page: Page, numero: str, anio: str, timeout: int = 8000) -> tuple[bool, str]:
    try:
        print(f"🔎 Buscando expediente {numero}/{anio} usando el formulario...")

        # Mostrar el panel de búsqueda
        await page.click("a[href='#collapseOne']")
        await page.wait_for_selector("#collapseOne.collapse.in", timeout=5000)

        # Completar número y año
        await page.fill("#j_idt83\:consultaExpediente\:j_idt116\:numero", numero)
        await page.fill("#j_idt83\:consultaExpediente\:j_idt118\:anio", anio)

        # Click en Consultar
        await page.click("#j_idt83\:consultaExpediente\:consultaFiltroSearchButtonSAU")

        # Intentar detectar mensaje de "no encontrado" primero
        try:
            await page.wait_for_selector("text=No se han encontrado expedientes", timeout=3000)
            print(f"❗ Expediente {numero}/{anio} no encontrado.")
            return False, "no_encontrado"
        except PlaywrightTimeoutError:
            pass  # No hay mensaje de error, seguir esperando la tabla

        # Esperar la tabla de resultados
        await page.wait_for_selector("table.table-striped", timeout=timeout)
        print(f"✅ Resultados cargados correctamente para {numero}/{anio}.")
        return True, "OK"

    except PlaywrightTimeoutError:
        print(f"⏳ Tiempo de espera agotado buscando expediente {numero}/{anio}.")
        return False, "timeout"

    except Exception as e:
        print(f"❌ Error general buscando expediente {numero}/{anio}: {e}")
        return False, "error"


async def buscar_expedientes_por_caratula(page: Page, caratula: str) -> List:
    """
    Realiza la búsqueda de expedientes utilizando únicamente la carátula como criterio.

    Actualmente actúa como punto de extensión: si no se implementa una búsqueda real,
    devuelve una lista vacía e informa al usuario.
    """

    if not caratula:
        print("❌ Debe indicar una carátula válida para utilizar este modo de búsqueda.")
        return []

    print(
        "ℹ️ La búsqueda exclusiva por carátula no está automatizada aún. "
        "Se devuelve una lista vacía para permitir un manejo seguro."
    )
    return []



async def buscar_expedientes(page: Page, numero: Optional[str] = None, anio: Optional[str] = None, caratula: Optional[str] = None) -> List:
    """
    Busca expedientes en el portal PJN y devuelve las filas encontradas según los filtros.

    Combinaciones admitidas:
      * ``numero`` + ``anio``: realiza la búsqueda principal en el portal.
      * ``numero`` + ``anio`` + ``caratula``: filtra los resultados obtenidos por número/año.
      * Sólo ``caratula``: deriva a ``buscar_expedientes_por_caratula``.

    :param page: Página Playwright actual.
    :param numero: Número de expediente (requiere ``anio`` si se especifica).
    :param anio: Año de expediente (requiere ``numero`` si se especifica).
    :param caratula: Carátula utilizada como filtro adicional o único criterio.
    :return: Lista de filas (ElementHandle) encontradas.
    """

    numero = numero.strip() if numero and numero.strip() else None
    anio = anio.strip() if anio and anio.strip() else None
    caratula = caratula.strip() if caratula and caratula.strip() else None

    if numero and not anio:
        print("❌ Para buscar por número debe indicar también el año del expediente.")
        return []

    if anio and not numero:
        print("❌ Para buscar por año debe indicar también el número del expediente.")
        return []

    if not numero and not caratula:
        print(
            "❌ Debe proporcionar un número y año del expediente o bien una carátula para realizar la búsqueda."
        )
        return []

    if not numero and caratula:
        return await buscar_expedientes_por_caratula(page, caratula)

    exito, motivo = await buscar_expediente_por_numero(page, numero, anio)

    if not exito:
        if motivo == "no_encontrado":
            print("❗ No se encontraron expedientes para los datos ingresados.")
        elif motivo == "timeout":
            print("⏳ La búsqueda tardó demasiado en cargar.")
        else:
            print(f"❌ Error inesperado durante la búsqueda: {motivo}")
        return []

    tabla = await page.query_selector("table.table-striped")
    if not tabla:
        print("⚠️ No se encontró la tabla de resultados.")
        return []

    filas = await tabla.query_selector_all("tbody tr")
    if not filas:
        print("❌ No se encontraron filas en la tabla de resultados.")
        return []

    # Si se pasa una carátula, filtrar solo las filas que coincidan
    if caratula:
        filas_filtradas = []
        for fila in filas:
            columnas = await fila.query_selector_all("td")
            if len(columnas) >= 3:
                caratula_texto = (await columnas[2].inner_text()).strip().lower()
                if caratula_texto == caratula.lower():
                    filas_filtradas.append(fila)
        return filas_filtradas

    return filas
