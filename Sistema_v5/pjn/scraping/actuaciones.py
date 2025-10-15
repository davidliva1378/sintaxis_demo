import asyncio
import json
import os
import re
from contextlib import suppress
from datetime import datetime
from typing import Awaitable, Callable, Iterable, Mapping, TypeVar
from urllib.parse import parse_qs, urlparse

from playwright.async_api import ElementHandle, Page
from playwright.async_api import TimeoutError as PlaywrightTimeout

from ..exceptions import (
    ActuacionesNoDisponibles,
    DescargaFallida,
    ExtraccionError,
    TimeoutExtraccion,
)
from ..models import Actuacion, ActuacionesArchivo
from ..parsers.actuaciones_parser import (
    EXTENSIONES_GENERICAS,
    construir_actuaciones_archivo,
    construir_encabezado_actuaciones as parser_construir_encabezado_actuaciones,
    construir_nombre_archivo_normalizado,
    obtener_extension_valida,
    parse_actuacion_row,
)
from ..utils.logging import get_logger
from .base import normalizar_numero_expediente

# Logger para este módulo
logger = get_logger(__name__)

TActuacion = TypeVar("TActuacion")

ActuacionBuilder = Callable[
    [Page, ElementHandle, int, str, bool], Awaitable[TActuacion | None]
]


def _calcular_metricas_descargas(
    actuaciones: Iterable[Actuacion | Mapping[str, object]]
) -> tuple[int, int, int]:
    """Devuelve ``(total_con_archivo, total_descargados, pendientes)``."""

    total_con_archivo = 0
    total_descargados = 0

    for act in actuaciones:
        if isinstance(act, Actuacion):
            modelo = act
        elif isinstance(act, Mapping):
            modelo = Actuacion.from_dict(act)
        else:
            continue

        if modelo.tiene_archivo:
            total_con_archivo += 1
            if modelo.descargado:
                total_descargados += 1

    pendientes = max(total_con_archivo - total_descargados, 0)
    return total_con_archivo, total_descargados, pendientes


def actualizar_metricas_descargas_en_json(payload: dict) -> None:
    """Recalcula los contadores de descargas dentro de la estructura JSON."""

    if not payload or not isinstance(payload, dict):
        return

    encabezado = payload.get("Expediente")
    actuaciones = payload.get("Actuaciones")

    if not isinstance(encabezado, dict) or not isinstance(actuaciones, list):
        return

    total_con_archivo, total_descargados, pendientes = _calcular_metricas_descargas(actuaciones)

    encabezado["Cantidad de Archivos Descargados"] = total_descargados
    encabezado["total_archivos_con_enlace"] = total_con_archivo
    encabezado["descargas_pendientes"] = pendientes


def construir_encabezado_actuaciones(
    expediente_datos: Mapping[str, object] | dict,
    actuaciones_actuales: Iterable[Actuacion | Mapping[str, object]],
    actuaciones_historicas: Iterable[Actuacion | Mapping[str, object]],
    incluye_historicas: bool,
    timestamp_generacion: str,
) -> dict[str, object]:
    """Genera los metadatos enriquecidos para el archivo JSON de actuaciones."""

    actuales_modelo = [
        act if isinstance(act, Actuacion) else Actuacion.from_dict(act)
        for act in actuaciones_actuales
    ]
    historicas_modelo = [
        act if isinstance(act, Actuacion) else Actuacion.from_dict(act)
        for act in actuaciones_historicas
    ]

    return parser_construir_encabezado_actuaciones(
        expediente_datos,
        actuales_modelo,
        historicas_modelo,
        incluye_historicas=incluye_historicas,
        timestamp_generacion=timestamp_generacion,
    )


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


async def construir_actuacion_modelo_desde_fila(
    page_expediente: Page,
    fila: ElementHandle,
    indice: int,
    timestamp_extraccion: str,
    *,
    es_historica: bool = False,
) -> Actuacion | None:
    """Construye un modelo :class:`Actuacion` a partir de la fila HTML."""

    return await parse_actuacion_row(
        page_expediente,
        fila,
        indice,
        timestamp_extraccion,
        es_historica=es_historica,
    )


async def construir_actuacion_desde_fila(
    page_expediente: Page,
    fila: ElementHandle,
    indice: int,
    timestamp_extraccion: str,
    es_historica: bool = False,
):
    modelo = await construir_actuacion_modelo_desde_fila(
        page_expediente,
        fila,
        indice,
        timestamp_extraccion,
        es_historica=es_historica,
    )
    return modelo.to_dict() if modelo else None


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
        except PlaywrightTimeout as e:
            raise TimeoutExtraccion(
                "Timeout esperando tabla o mensaje de actuaciones históricas"
            ) from e

        mensaje = await page_expediente.query_selector("div.alert.white-panel")
        if mensaje:
            texto = await mensaje.inner_text()
            if "no posee actuaciones históricas" in texto.lower():
                logger.info("El expediente no posee actuaciones históricas.")
                return [], None

        expediente_numero = normalizar_numero_expediente(
            expediente_datos.get("numero"), valor_por_defecto="desconocido"
        )
        timestamp_extraccion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        pagina = 1
        indice_actual = indice_inicial
        tabla_id = "expediente:action-historic-table"
        tabla_selector_css = _escape_selector_for_css(f"#{tabla_id}")
        filas_selector = f"{tabla_selector_css} tbody tr"
        while True:
            logger.info("📄 Página %d (históricas): extrayendo...", pagina)

            filas = await page_expediente.query_selector_all(filas_selector)
            if not filas:
                logger.warning("⚠️ No se encontraron filas en actuaciones históricas.")
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
                    logger.error("❌ No se pudo avanzar de página histórica: %s", e)
                    break
            else:
                logger.info("✅ No hay más páginas históricas.")
                break

        return actuaciones, None

    except Exception as e:
        return [], f"Error al extraer históricas: {type(e).__name__}: {str(e)}"


async def _extraer_actuaciones_pagina_generico(
    page_expediente: Page,
    expediente_datos: Mapping[str, object] | dict,
    indice_inicial: int,
    builder: ActuacionBuilder[TActuacion],
) -> tuple[list[TActuacion], str | None]:
    actuaciones: list[TActuacion] = []
    try:
        await page_expediente.wait_for_selector(
            r"#expediente\:action-table tbody tr", timeout=8000
        )
        filas = await page_expediente.query_selector_all(
            r"#expediente\:action-table tbody tr"
        )
        if not filas:
            return [], None

        normalizar_numero_expediente(
            expediente_datos.get("numero"), valor_por_defecto="desconocido"
        )

        timestamp_extraccion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for idx, fila in enumerate(filas, start=indice_inicial):
            actuacion = await builder(
                page_expediente,
                fila,
                idx,
                timestamp_extraccion,
                False,
            )
            if actuacion:
                actuaciones.append(actuacion)
        return actuaciones, None
    except Exception as e:  # noqa: BLE001
        return [], f"{type(e).__name__}: {str(e)}"


async def extraer_actuaciones_pagina(
    page_expediente, expediente_datos, indice_inicial=1
):
    return await _extraer_actuaciones_pagina_generico(
        page_expediente,
        expediente_datos,
        indice_inicial,
        construir_actuacion_desde_fila,
    )


async def extraer_actuaciones_pagina_modelos(
    page_expediente: Page,
    expediente_datos: Mapping[str, object] | dict,
    indice_inicial: int = 1,
) -> tuple[list[Actuacion], str | None]:
    return await _extraer_actuaciones_pagina_generico(
        page_expediente,
        expediente_datos,
        indice_inicial,
        construir_actuacion_modelo_desde_fila,
    )

async def obtener_actuaciones_todas_paginas_async(page_expediente, expediente_datos, carpeta_destino="Actuaciones"):
    todas = []
    pagina = 1
    indice_actual = 1

    tabla_id = "expediente:action-table"
    tabla_selector_css = _escape_selector_for_css(f"#{tabla_id}")
    while True:
        logger.info("📄 Página %d: extrayendo...", pagina)
        nuevas, error = await extraer_actuaciones_pagina(page_expediente, expediente_datos, indice_actual)
        if error:
            return todas, f"❌ Error en página {pagina}: {error}", None
        if not nuevas:
            break
        todas.extend(nuevas)
        indice_actual += len(nuevas)

        boton_siguiente = await page_expediente.query_selector("a:has(span[title='Siguiente']):not(.ui-state-disabled)")

        if not boton_siguiente:
            logger.info("✅ No hay más páginas.")
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

    expediente_numero = normalizar_numero_expediente(expediente_datos.get("numero"))
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

    logger.info("✅ Archivo JSON guardado: %s", json_path)
    logger.info("📂 Total de actuaciones: %d", len(todas))
    return todas, None, carpeta_actuaciones


async def obtener_actuaciones_todas_paginas_modelos_async(
    page_expediente: Page,
    expediente_datos: Mapping[str, object] | dict,
    carpeta_destino: str = "Actuaciones",
) -> tuple[ActuacionesArchivo | None, str | None, str | None]:
    """Obtiene las actuaciones en formato de modelos dataclass."""

    actuaciones_dicts, error, carpeta = await obtener_actuaciones_todas_paginas_async(
        page_expediente, expediente_datos, carpeta_destino
    )
    if error:
        return None, error, carpeta

    actuaciones_modelo = [
        Actuacion.from_dict(act)
        for act in actuaciones_dicts
        if isinstance(act, Mapping)
    ]

    timestamp_generacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    archivo = construir_actuaciones_archivo(
        expediente_datos,
        actuaciones_modelo,
        [],
        incluye_historicas=False,
        timestamp_generacion=timestamp_generacion,
    )
    return archivo, None, carpeta


async def actualizar_actuaciones_desde_json(
    page_expediente: Page,
    expediente_datos: dict,
    ruta_json_existente: str,
) -> tuple[int, dict | None, str | None]:
    """Actualiza un JSON existente incorporando solo las actuaciones nuevas.

    Retorna una tupla con la cantidad de actuaciones agregadas, la estructura
    actualizada (o ``None`` si hubo error) y un mensaje de error en caso de fallos.
    """

    if not ruta_json_existente or not os.path.exists(ruta_json_existente):
        return 0, None, "El archivo de actuaciones especificado no existe."

    try:
        with open(ruta_json_existente, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:  # noqa: BLE001
        return 0, None, f"No se pudo leer el JSON existente: {type(e).__name__}: {str(e)}"

    actuaciones_existentes = data.get("Actuaciones")
    if not isinstance(actuaciones_existentes, list):
        actuaciones_existentes = []

    encabezado_existente = data.get("Expediente")
    if not isinstance(encabezado_existente, dict):
        encabezado_existente = {}

    hashes_existentes = {
        act.get("Hash")
        for act in actuaciones_existentes
        if isinstance(act, dict) and act.get("Hash")
    }

    nuevas_actuaciones = []
    pagina = 1
    indice_actual = 1
    tabla_id = "expediente:action-table"
    tabla_selector_css = _escape_selector_for_css(f"#{tabla_id}")

    while True:
        nuevas, error = await extraer_actuaciones_pagina(page_expediente, expediente_datos, indice_actual)
        if error:
            return 0, None, f"Error al obtener la página {pagina}: {error}"

        if not nuevas:
            break

        detener = False
        for actuacion in nuevas:
            hash_act = actuacion.get("Hash")
            if hash_act and hash_act in hashes_existentes:
                detener = True
                break
            nuevas_actuaciones.append(actuacion)

        if detener:
            break

        indice_actual += len(nuevas)

        boton_siguiente = await page_expediente.query_selector(
            "a:has(span[title='Siguiente']):not(.ui-state-disabled)"
        )
        if not boton_siguiente:
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
            return 0, None, f"⏳ Timeout al intentar avanzar a la página {pagina + 1}"
        except Exception as e:  # noqa: BLE001
            return 0, None, (
                "⚠️ Error inesperado al avanzar a la página "
                f"{pagina + 1}: {type(e).__name__}: {str(e)}"
            )

    if not nuevas_actuaciones:
        logger.info("ℹ️ No se detectaron actuaciones nuevas.")
        return 0, data, None

    logger.info("✨ Se encontraron %d actuaciones nuevas.", len(nuevas_actuaciones))

    actuaciones_actuales_existentes = [
        act
        for act in actuaciones_existentes
        if isinstance(act, dict) and not act.get("EsHistorica", False)
    ]
    actuaciones_historicas_existentes = [
        act
        for act in actuaciones_existentes
        if isinstance(act, dict) and act.get("EsHistorica", False)
    ]

    actuaciones_actualizadas = list(nuevas_actuaciones) + actuaciones_actuales_existentes

    for idx, actuacion in enumerate(actuaciones_actualizadas, start=1):
        actuacion["Indice"] = idx
        actuacion["EsHistorica"] = False

    indice_historico = len(actuaciones_actualizadas) + 1
    for actuacion in actuaciones_historicas_existentes:
        if not isinstance(actuacion, dict):
            continue
        actuacion["Indice"] = indice_historico
        actuacion["EsHistorica"] = True
        indice_historico += 1

    todas_actuaciones = actuaciones_actualizadas + actuaciones_historicas_existentes

    expediente_para_encabezado = dict(encabezado_existente)
    expediente_para_encabezado.update(expediente_datos or {})

    timestamp_generacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    encabezado_actualizado = construir_encabezado_actuaciones(
        expediente_para_encabezado,
        actuaciones_actuales=actuaciones_actualizadas,
        actuaciones_historicas=actuaciones_historicas_existentes,
        incluye_historicas=bool(actuaciones_historicas_existentes),
        timestamp_generacion=timestamp_generacion,
    )

    nuevo_payload = dict(data)
    nuevo_payload["Expediente"] = encabezado_actualizado
    nuevo_payload["Actuaciones"] = todas_actuaciones
    actualizar_metricas_descargas_en_json(nuevo_payload)

    try:
        with open(ruta_json_existente, "w", encoding="utf-8") as f:
            json.dump(nuevo_payload, f, indent=2, ensure_ascii=False)
    except Exception as e:  # noqa: BLE001
        return 0, None, f"No se pudo actualizar el JSON: {type(e).__name__}: {str(e)}"

    return len(nuevas_actuaciones), nuevo_payload, None


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
        numero_normalizado = normalizar_numero_expediente(expediente_datos.get("numero"))
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
                logger.warning(
                    "⚠️ Verificar numeración histórica: se esperaba que iniciara en "
                    "%d, pero comenzó en %d.", indice_historico_esperado, primer_indice_historico
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
        logger.info("📄 JSON generado: %s", json_path)

        return actuaciones_actuales, actuaciones_historicas, None

    except Exception as e:
        return [], [], f"Error general: {type(e).__name__}: {str(e)}"



async def aviso_si_tarda(idx, segundos):
    await asyncio.sleep(segundos)
    logger.warning("⏳ Descarga en curso para actuación %d... lleva más de %d segundos.", idx, segundos)

async def descargar_archivos_actuaciones(page: Page, actuaciones: list, carpeta_destino: str):
    if not actuaciones:
        logger.warning("⚠️ No se proporcionaron actuaciones para descargar.")
        return

    logger.info("📥 Iniciando descarga de archivos (%d actuaciones)...", len(actuaciones))
    os.makedirs(carpeta_destino, exist_ok=True)

    for idx, act in enumerate(actuaciones, start=1):
        archivo_url = act.get("Archivo", "N/A")
        if not archivo_url or archivo_url == "N/A":
            logger.debug("🚫 Actuación %d: sin archivo para descargar.", idx)
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
            logger.info("⏭️ Archivo ya existe: %s", nombre_archivo)
            continue

        ultimo_error = None
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

                logger.info("✅ Archivo descargado: %s", nombre_archivo)
                break  # éxito
            except (PlaywrightTimeout, asyncio.TimeoutError) as e:
                ultimo_error = e
                if intento == 2:
                    logger.error("❌ Timeout en descarga tras 3 intentos para actuación %d", idx)
                else:
                    logger.warning("⚠️ Timeout en actuación %d, reintentando (%d/3)...", idx, intento + 1)
                    await asyncio.sleep(4)
            except (OSError, IOError) as e:
                # Errores de I/O no deben reintentar
                logger.error("❌ Error de I/O al guardar archivo %s: %s", nombre_archivo, e)
                ultimo_error = e
                break
            except Exception as e:
                ultimo_error = e
                if intento == 2:
                    logger.error("❌ Error inesperado tras 3 intentos para actuación %d: %s", idx, e)
                else:
                    logger.warning("⚠️ Error en actuación %d, reintentando (%d/3)...", idx, intento + 1)
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
    if not carpeta_destino:
        logger.warning("⚠️ Carpeta destino no proporcionada para las descargas.")
        return

    os.makedirs(carpeta_destino, exist_ok=True)

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
                        logger.debug("🟡 Ya existe: %s", act['NombreArchivo'])

            if actuaciones_filtradas:
                logger.info("\n🔽 Descargando %d archivo(s)...", len(actuaciones_filtradas))
                await descargar_archivos_actuaciones(page, actuaciones_filtradas, carpeta_destino)
                for act in actuaciones_filtradas:
                    act["Descargado"] = True
            else:
                logger.info("✅ Todos los archivos ya existen.")

        # Guardar archivo actualizado
        actualizar_metricas_descargas_en_json(data)

        with open(ruta_json, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info("📝 JSON actualizado con estado de descarga.")
    else:
        logger.warning("⚠️ No se encontró archivo de actuaciones unificado.")
