import asyncio
import json
import os
import re
import warnings
from contextlib import suppress
from datetime import datetime
from typing import Awaitable, Callable, Iterable, Mapping, TypeVar
from urllib.parse import urlparse

from playwright.async_api import ElementHandle, Page
from playwright.async_api import TimeoutError as PlaywrightTimeout

from ..exceptions import (
    ActuacionesNoDisponibles,
    DescargaFallida,
    ExtraccionError,
    PJNError,
    TimeoutExtraccion,
)
from ..models import Actuacion, ActuacionesArchivo
from ..parsers.actuaciones_parser import (
    EXTENSIONES_GENERICAS,
    _calcular_metricas_descargas,
    construir_actuaciones_archivo,
    construir_encabezado_actuaciones as parser_construir_encabezado_actuaciones,
    construir_nombre_archivo_normalizado,
    obtener_extension_valida,
    parse_actuacion_row,
)
from ..selectores import escapar_id_jsf_para_css, escapar_id_jsf_para_js
from ..utils.logging import get_logger
from .base import normalizar_numero_expediente

# Logger para este módulo
logger = get_logger(__name__)

TActuacion = TypeVar("TActuacion")

ActuacionBuilder = Callable[
    [Page, ElementHandle, int, str, bool], Awaitable[TActuacion | None]
]


# _calcular_metricas_descargas ahora se importa desde parsers.actuaciones_parser
# para evitar duplicación de código


def calcular_metricas_descargas_json(payload: dict) -> dict:
    """Recalcula los contadores de descargas y retorna una COPIA actualizada del payload.

    Args:
        payload: Estructura JSON con Expediente y Actuaciones.

    Returns:
        dict: Nueva copia del payload con métricas actualizadas.

    Note:
        Esta función NO modifica el payload original (sin side effects).
    """
    import copy

    if not payload or not isinstance(payload, dict):
        return payload

    # Crear copia profunda para evitar mutaciones
    nuevo_payload = copy.deepcopy(payload)

    encabezado = nuevo_payload.get("Expediente")
    actuaciones = nuevo_payload.get("Actuaciones")

    if not isinstance(encabezado, dict) or not isinstance(actuaciones, list):
        return nuevo_payload

    total_con_archivo, total_descargados, pendientes = _calcular_metricas_descargas(actuaciones)

    encabezado["Cantidad de Archivos Descargados"] = total_descargados
    encabezado["total_archivos_con_enlace"] = total_con_archivo
    encabezado["descargas_pendientes"] = pendientes

    return nuevo_payload


def actualizar_metricas_descargas_en_json(payload: dict) -> None:
    """Recalcula los contadores de descargas dentro de la estructura JSON.

    .. deprecated:: 5.6
        Esta función modifica el payload in-place (side effect).
        Usar :func:`calcular_metricas_descargas_json` que retorna una copia inmutable.
        Esta función será eliminada en la versión 6.0.

    Warning:
        Esta función MUTA el argumento payload. Para código nuevo, use
        ``calcular_metricas_descargas_json()`` que retorna una copia modificada
        sin alterar el original.

    Args:
        payload: Diccionario con estructura JSON de expediente.

    Example:
        >>> # ❌ MAL - Muta el original
        >>> actualizar_metricas_descargas_en_json(payload)
        >>>
        >>> # ✅ BIEN - Retorna copia
        >>> nuevo_payload = calcular_metricas_descargas_json(payload)
    """
    warnings.warn(
        "actualizar_metricas_descargas_en_json() está deprecated y será eliminada en v6.0. "
        "Use calcular_metricas_descargas_json() que retorna una copia sin mutar el original.",
        DeprecationWarning,
        stacklevel=2
    )

    if not payload or not isinstance(payload, dict):
        return

    encabezado = payload.get("Expediente")
    actuaciones = payload.get("Actuaciones")

    if not isinstance(encabezado, dict) or not isinstance(actuaciones, list):
        return

    total_con_archivo, total_descargados, pendientes = _calcular_metricas_descargas(actuaciones)

    # SIDE EFFECT: Modifica el dict original
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


# Las funciones de escape ahora están en selectores.py
# Se mantienen aquí como aliases por compatibilidad
_escape_selector_for_css = escapar_id_jsf_para_css
_escape_selector_for_js = escapar_id_jsf_para_js


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
) -> list[TActuacion]:
    """Extrae actuaciones de una página usando el builder especificado.

    Esta función interna ahora lanza excepciones en lugar de retornar tuplas.

    Args:
        page_expediente: Página de Playwright con el expediente abierto.
        expediente_datos: Datos del expediente.
        indice_inicial: Índice inicial para numerar actuaciones.
        builder: Función para construir objetos Actuacion desde filas HTML.

    Returns:
        list[TActuacion]: Lista de actuaciones extraídas.

    Raises:
        TimeoutExtraccion: Si no se encuentra la tabla en el tiempo esperado.
        ExtraccionError: Si hay errores durante la extracción de actuaciones.
    """
    actuaciones: list[TActuacion] = []

    try:
        await page_expediente.wait_for_selector(
            r"#expediente\:action-table tbody tr", timeout=8000
        )
    except PlaywrightTimeout as exc:
        raise TimeoutExtraccion(
            "Timeout esperando tabla de actuaciones"
        ) from exc

    filas = await page_expediente.query_selector_all(
        r"#expediente\:action-table tbody tr"
    )
    if not filas:
        return []

    normalizar_numero_expediente(
        expediente_datos.get("numero"), valor_por_defecto="desconocido"
    )

    timestamp_extraccion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        for idx, fila in enumerate(filas, start=indice_inicial):
            actuacion = await builder(
                page_expediente,
                fila,
                idx,
                timestamp_extraccion,
                es_historica=False,
            )
            if actuacion:
                actuaciones.append(actuacion)
        return actuaciones
    except Exception as exc:
        raise ExtraccionError(
            f"Error extrayendo actuaciones de la página: {type(exc).__name__}: {str(exc)}"
        ) from exc


async def extraer_actuaciones_pagina(
    page_expediente, expediente_datos, indice_inicial=1
) -> tuple[list[dict], str | None]:
    """Extrae actuaciones de la página actual (versión deprecated con tuple).

    DEPRECATED: Esta función mantiene el retorno tuple[result, error] por compatibilidad.
    Para nuevo código, use extraer_actuaciones_pagina_modelos() que lanza excepciones.

    Returns:
        tuple: (lista_actuaciones_dict, error_str_o_None)
    """
    try:
        actuaciones = await _extraer_actuaciones_pagina_generico(
            page_expediente,
            expediente_datos,
            indice_inicial,
            construir_actuacion_desde_fila,
        )
        return actuaciones, None
    except Exception as e:
        return [], f"{type(e).__name__}: {str(e)}"


async def extraer_actuaciones_pagina_modelos(
    page_expediente: Page,
    expediente_datos: Mapping[str, object] | dict,
    indice_inicial: int = 1,
) -> list[Actuacion]:
    """Extrae actuaciones de la página actual y retorna modelos Actuacion.

    Args:
        page_expediente: Página de Playwright con el expediente abierto.
        expediente_datos: Datos del expediente.
        indice_inicial: Índice inicial para numerar actuaciones.

    Returns:
        list[Actuacion]: Lista de modelos de actuaciones extraídas.

    Raises:
        TimeoutExtraccion: Si no se encuentra la tabla en el tiempo esperado.
        ExtraccionError: Si hay errores durante la extracción.
    """
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

    # Validar y crear carpeta si no existe
    try:
        os.makedirs(carpeta_actuaciones, exist_ok=True)
    except OSError as e:
        logger.error("❌ Error al crear carpeta %s: %s", carpeta_actuaciones, e)
        return todas, f"Error al crear carpeta: {e}", None

    # Validar permisos de escritura
    if not os.access(carpeta_actuaciones, os.W_OK):
        error_msg = f"Sin permisos de escritura en: {carpeta_actuaciones}"
        logger.error("❌ %s", error_msg)
        return todas, error_msg, None

    json_path = os.path.join(carpeta_actuaciones, f"actuaciones-{expediente_numero}.json")

    # Guardar archivo JSON con manejo de errores
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({"Expediente": encabezado, "Actuaciones": todas}, f, indent=2, ensure_ascii=False)
        logger.info("✅ Archivo JSON guardado: %s", json_path)
    except OSError as e:
        error_msg = f"Error al guardar archivo {json_path}: {e}"
        logger.error("❌ %s", error_msg)
        return todas, error_msg, None
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

    # Validar que la ruta fue proporcionada
    if not ruta_json_existente:
        return 0, None, "No se proporcionó ruta al archivo de actuaciones."

    # Validar que el archivo existe
    if not os.path.exists(ruta_json_existente):
        return 0, None, f"El archivo de actuaciones no existe: {ruta_json_existente}"

    # Validar que es un archivo regular
    if not os.path.isfile(ruta_json_existente):
        return 0, None, f"La ruta no es un archivo válido: {ruta_json_existente}"

    # Validar permisos de lectura
    if not os.access(ruta_json_existente, os.R_OK):
        return 0, None, f"Sin permisos de lectura para: {ruta_json_existente}"

    try:
        with open(ruta_json_existente, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return 0, None, f"El archivo no contiene JSON válido: {e}"
    except OSError as e:
        return 0, None, f"Error al leer el archivo: {e}"

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

    # Validar permisos de escritura antes de guardar
    carpeta_json = os.path.dirname(ruta_json_existente)
    if not os.access(carpeta_json, os.W_OK):
        return 0, None, f"Sin permisos de escritura en: {carpeta_json}"

    try:
        with open(ruta_json_existente, "w", encoding="utf-8") as f:
            json.dump(nuevo_payload, f, indent=2, ensure_ascii=False)
    except OSError as e:
        return 0, None, f"Error al guardar el archivo: {e}"

    return len(nuevas_actuaciones), nuevo_payload, None


async def _navegar_paginas_actuaciones(
    page: Page,
    tabla_id: str,
    expediente_datos: Mapping[str, object] | dict,
    indice_inicial: int = 1,
    es_historica: bool = False,
) -> list[Actuacion]:
    """Navega todas las páginas de una tabla y extrae actuaciones.

    Responsabilidad única: Manejar la paginación de una tabla de actuaciones.

    Args:
        page: Página de Playwright.
        tabla_id: ID de la tabla (ej: "expediente:action-table").
        expediente_datos: Datos del expediente.
        indice_inicial: Índice inicial para las actuaciones.
        es_historica: Si las actuaciones son históricas.

    Returns:
        Lista de actuaciones extraídas de todas las páginas.

    Raises:
        TimeoutExtraccion: Si hay timeout al navegar.
        ExtraccionError: Si hay error al extraer actuaciones.
    """
    actuaciones: list[Actuacion] = []
    indice_actual = indice_inicial
    pagina = 1
    tabla_selector_css = _escape_selector_for_css(f"#{tabla_id}")
    timestamp_extraccion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    tipo_actuacion = "históricas" if es_historica else "actuales"

    while True:
        logger.info("📄 Página %d (%s): extrayendo...", pagina, tipo_actuacion)

        if es_historica:
            # Para históricas, usar query_selector_all directamente
            filas_selector = f"{tabla_selector_css} tbody tr"
            filas = await page.query_selector_all(filas_selector)

            if not filas:
                break

            for fila in filas:
                actuacion = await construir_actuacion_modelo_desde_fila(
                    page,
                    fila,
                    indice_actual,
                    timestamp_extraccion,
                    es_historica=True,
                )
                if actuacion:
                    actuacion.descargado = False if actuacion.tiene_archivo else None
                    actuaciones.append(actuacion)
                    indice_actual += 1
        else:
            # Para actuales, usar la función existente
            try:
                nuevas = await extraer_actuaciones_pagina_modelos(
                    page, expediente_datos, indice_actual
                )
            except (TimeoutExtraccion, ExtraccionError) as exc:
                raise ExtraccionError(f"Error en página {pagina}: {str(exc)}") from exc

            if not nuevas:
                break

            actuaciones.extend(nuevas)
            indice_actual += len(nuevas)

        # Intentar navegar a la siguiente página
        if es_historica:
            boton_siguiente = await page.query_selector(
                "a[id^='expediente:j_idt']:not(.ui-state-disabled):has-text('Siguiente')"
            )
        else:
            boton_siguiente = await page.query_selector(
                "a:has(span[title='Siguiente']):not(.ui-state-disabled)"
            )

        if not boton_siguiente:
            break

        try:
            html_anterior = await page.inner_html(tabla_selector_css)
            paginador_selector_js, pagina_activa = await _obtener_paginador_activo(
                page, tabla_id
            )
            await boton_siguiente.click()
            await page.wait_for_load_state("domcontentloaded")

            if es_historica:
                # Para históricas, esperar selector de filas
                filas_selector = f"{tabla_selector_css} tbody tr"
                await page.wait_for_selector(filas_selector, timeout=8000)

            await _esperar_cambio_pagina(
                page,
                tabla_id,
                html_anterior,
                paginador_selector_js,
                pagina_activa,
            )
            pagina += 1
        except PlaywrightTimeout as exc:
            if es_historica:
                # Para históricas, solo logear y terminar
                logger.error("❌ No se pudo avanzar de página histórica: %s", exc)
                break
            else:
                raise TimeoutExtraccion(
                    f"Timeout al intentar avanzar a la página {pagina + 1}"
                ) from exc
        except Exception as exc:
            if es_historica:
                logger.error("❌ No se pudo avanzar de página histórica: %s", exc)
                break
            else:
                raise ExtraccionError(
                    f"Error inesperado al avanzar a la página {pagina + 1}: {type(exc).__name__}: {str(exc)}"
                ) from exc

    return actuaciones


async def _extraer_actuaciones_actuales(
    page: Page,
    expediente_datos: Mapping[str, object] | dict,
) -> list[Actuacion]:
    """Extrae solo actuaciones actuales (no históricas).

    Responsabilidad única: Extraer actuaciones actuales con paginación.

    Args:
        page: Página de Playwright con expediente abierto.
        expediente_datos: Datos del expediente.

    Returns:
        Lista de actuaciones actuales extraídas.

    Raises:
        ActuacionesNoDisponibles: Si no hay tabla de actuaciones.
        ExtraccionError: Si falla la extracción.
    """
    try:
        await page.wait_for_selector(
            r"#expediente\:action-table tbody tr", timeout=8000
        )
    except PlaywrightTimeout as exc:
        raise ActuacionesNoDisponibles(
            "No se encontró la tabla de actuaciones en el tiempo esperado"
        ) from exc

    actuaciones = await _navegar_paginas_actuaciones(
        page=page,
        tabla_id="expediente:action-table",
        expediente_datos=expediente_datos,
        indice_inicial=1,
        es_historica=False,
    )

    # Marcar como actuales y sin descargar
    for act in actuaciones:
        act.es_historica = False
        if act.tiene_archivo:
            act.descargado = False

    return actuaciones


async def _extraer_actuaciones_historicas(
    page: Page,
    expediente_datos: Mapping[str, object] | dict,
    indice_base: int,
) -> list[Actuacion]:
    """Extrae actuaciones históricas si existen.

    Responsabilidad única: Extraer actuaciones históricas con paginación.

    Args:
        page: Página de Playwright con expediente abierto.
        expediente_datos: Datos del expediente.
        indice_base: Índice inicial para las actuaciones históricas.

    Returns:
        Lista de actuaciones históricas (puede ser vacía).

    Raises:
        TimeoutExtraccion: Si hay timeout esperando tabla.
    """
    try:
        await page.click("a:has-text('Ver históricas')")
        await page.wait_for_selector(
            r"#expediente\:action-historic-table tbody tr, div.alert.white-panel",
            timeout=8000,
        )
    except PlaywrightTimeout as exc:
        raise TimeoutExtraccion(
            "Timeout esperando tabla o mensaje de actuaciones históricas"
        ) from exc

    # Verificar si hay mensaje de "no hay históricas"
    mensaje = await page.query_selector("div.alert.white-panel")
    if mensaje:
        texto = await mensaje.inner_text()
        texto_lower = texto.lower()
        if "no posee actuaciones históricas" in texto_lower or "no posee actuaciones" in texto_lower:
            logger.info("El expediente no posee actuaciones históricas.")
            return []
        else:
            logger.warning(
                "Mensaje inesperado en actuaciones históricas: '%s'. "
                "Continuando sin extraer históricas.",
                texto.strip()
            )
            return []

    # Extraer históricas paginadas
    actuaciones = await _navegar_paginas_actuaciones(
        page=page,
        tabla_id="expediente:action-historic-table",
        expediente_datos=expediente_datos,
        indice_inicial=indice_base,
        es_historica=True,
    )

    return actuaciones


async def extraer_actuaciones_datos(
    page_expediente: Page,
    expediente_datos: Mapping[str, object] | dict,
    incluir_historicas: bool = True,
) -> ActuacionesArchivo:
    """Extrae actuaciones actuales e históricas (opcional) y retorna modelo estructurado.

    Esta versión refactorizada delega en funciones especializadas para mayor
    claridad, testabilidad y mantenibilidad.

    Esta es la versión "pura" que NO guarda archivos. Útil para:
    - Procesamiento en memoria
    - Integración con otras rutinas
    - Testing

    Args:
        page_expediente: Página de Playwright con el expediente abierto.
        expediente_datos: Datos del expediente (número, carátula, etc.).
        incluir_historicas: Si True, incluye actuaciones históricas.

    Returns:
        ActuacionesArchivo: Modelo con encabezado y actuaciones.

    Raises:
        ExtraccionError: Si falla la extracción de actuaciones.
        ActuacionesNoDisponibles: Si no hay actuaciones disponibles.
    """
    # 1. Extraer actuaciones actuales
    actuaciones_actuales = await _extraer_actuaciones_actuales(
        page_expediente,
        expediente_datos
    )

    if not actuaciones_actuales:
        raise ActuacionesNoDisponibles(
            "No se encontraron actuaciones en el expediente"
        )

    # 2. Extraer históricas si se solicita
    actuaciones_historicas: list[Actuacion] = []
    if incluir_historicas:
        indice_base = len(actuaciones_actuales) + 1
        try:
            actuaciones_historicas = await _extraer_actuaciones_historicas(
                page_expediente,
                expediente_datos,
                indice_base
            )
        except (TimeoutExtraccion, ExtraccionError) as exc:
            logger.warning(
                "No se pudieron extraer históricas: %s. "
                "Continuando solo con actuaciones actuales.",
                exc
            )

    # 3. Construir archivo final
    timestamp_generacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    archivo = construir_actuaciones_archivo(
        expediente_datos,
        actuaciones_actuales,
        actuaciones_historicas,
        incluye_historicas=bool(actuaciones_historicas),
        timestamp_generacion=timestamp_generacion,
    )

    logger.info(
        "✅ Extraídas %d actuales + %d históricas",
        len(actuaciones_actuales),
        len(actuaciones_historicas)
    )

    return archivo


async def extraer_actuaciones_completas(
    page_expediente: Page,
    expediente_datos: dict,
    incluir_historicas: bool = True,
    directorio_base: str = "ActuacionesCompletas"
) -> tuple[list[dict], list[dict], str | None]:
    """Extrae actuaciones y las guarda como JSON (versión con persistencia).

    NOTA: Esta función mantiene compatibilidad con código existente.
    Para uso desde otras rutinas, considere usar extraer_actuaciones_datos()
    que no guarda archivos automáticamente.

    Args:
        page_expediente: Página de Playwright con el expediente abierto.
        expediente_datos: Datos del expediente (número, carátula, etc.).
        incluir_historicas: Si True, incluye actuaciones históricas.
        directorio_base: Carpeta base donde guardar los archivos.

    Returns:
        tuple: (actuaciones_actuales, actuaciones_historicas, error)
            - Si error es None, la extracción fue exitosa
            - Si error es str, contiene el mensaje de error

    Deprecated:
        Esta función será deprecada en favor de extraer_actuaciones_datos()
        + guardar_actuaciones_json() por separado.
    """
    try:
        # Usar la versión pura
        archivo = await extraer_actuaciones_datos(
            page_expediente,
            expediente_datos,
            incluir_historicas=incluir_historicas,
        )

        # Guardar a disco
        numero_normalizado = normalizar_numero_expediente(expediente_datos.get("numero"))
        carpeta_expte = os.path.join(directorio_base, numero_normalizado)
        os.makedirs(carpeta_expte, exist_ok=True)

        # Separar actuales de históricas y convertir a dicts para compatibilidad
        actuaciones_actuales = [act.to_dict() for act in archivo.actuaciones if not act.es_historica]
        actuaciones_historicas = [act.to_dict() for act in archivo.actuaciones if act.es_historica]
        todas = actuaciones_actuales + actuaciones_historicas

        estructura_json = {"Expediente": archivo.encabezado, "Actuaciones": todas}

        json_path = os.path.join(carpeta_expte, f"actuaciones-{numero_normalizado}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(estructura_json, f, indent=2, ensure_ascii=False)
        logger.info("📄 JSON generado: %s", json_path)

        return actuaciones_actuales, actuaciones_historicas, None

    except PJNError as e:
        # Excepciones de negocio esperadas
        return [], [], f"{type(e).__name__}: {str(e)}"
    except Exception as e:
        # Excepciones inesperadas
        logger.exception("Error inesperado extrayendo actuaciones")
        return [], [], f"Error general: {type(e).__name__}: {str(e)}"



async def aviso_si_tarda(idx, segundos):
    await asyncio.sleep(segundos)
    logger.warning("⏳ Descarga en curso para actuación %d... lleva más de %d segundos.", idx, segundos)

async def descargar_archivos_actuaciones_modelos(
    page: Page,
    actuaciones: list[Actuacion],
    carpeta_destino: str
) -> list[Actuacion]:
    """Descarga archivos y retorna lista actualizada de actuaciones (sin side effects).

    Args:
        page: Página de Playwright autenticada.
        actuaciones: Lista de modelos Actuacion.
        carpeta_destino: Carpeta donde guardar los archivos.

    Returns:
        list[Actuacion]: Nueva lista con actuaciones actualizadas (marca descargado=True).

    Note:
        Esta función NO modifica la lista original.
    """
    import copy

    if not actuaciones:
        logger.warning("⚠️ No se proporcionaron actuaciones para descargar.")
        return actuaciones

    logger.info("📥 Iniciando descarga de archivos (%d actuaciones)...", len(actuaciones))
    os.makedirs(carpeta_destino, exist_ok=True)

    # Crear copias para evitar mutaciones
    actuaciones_actualizadas = [copy.copy(act) for act in actuaciones]

    for idx, act in enumerate(actuaciones_actualizadas, start=1):
        if not act.archivo or act.archivo == "N/A":
            logger.debug("🚫 Actuación %d: sin archivo para descargar.", idx)
            continue

        # Resolver nombre de archivo
        nombre_archivo = construir_nombre_archivo_normalizado(
            act.nombre_archivo,
            act.tipo_archivo,
            idx
        )

        act.nombre_archivo = nombre_archivo
        # Actualizar tipo si se normalizó
        if nombre_archivo and "." in nombre_archivo:
            extension = os.path.splitext(nombre_archivo)[1]
            act.tipo_archivo = extension[1:] if extension.startswith(".") else extension

        ruta_archivo = os.path.join(carpeta_destino, nombre_archivo)

        if os.path.exists(ruta_archivo):
            logger.info("⏭️ Archivo ya existe: %s", nombre_archivo)
            act.descargado = True
            continue

        # Intentar descarga
        ultimo_error = None
        descarga_exitosa = False
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
                    """, act.archivo)

                download = await download_info.value
                advertencia = asyncio.create_task(aviso_si_tarda(idx, 30))
                await download.save_as(ruta_archivo)

                logger.info("✅ Archivo descargado: %s", nombre_archivo)
                act.descargado = True
                descarga_exitosa = True
                break
            except (PlaywrightTimeout, asyncio.TimeoutError) as e:
                ultimo_error = e
                if intento == 2:
                    logger.error("❌ Timeout en descarga tras 3 intentos para actuación %d", idx)
                else:
                    logger.warning("⚠️ Timeout en actuación %d, reintentando (%d/3)...", idx, intento + 1)
                    await asyncio.sleep(4)
            except (OSError, IOError) as e:
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

        if not descarga_exitosa:
            act.descargado = False

    return actuaciones_actualizadas


async def descargar_archivos_actuaciones(page: Page, actuaciones: list, carpeta_destino: str):
    """Descarga archivos de actuaciones (versión con side effects).

    .. deprecated:: 5.6
        Esta función modifica la lista de actuaciones in-place (side effect).
        Usar :func:`descargar_archivos_actuaciones_modelos` que trabaja con objetos
        inmutables y retorna una copia. Esta función será eliminada en la versión 6.0.

    Warning:
        Esta función MUTA los elementos de la lista actuaciones. Para código nuevo,
        use ``descargar_archivos_actuaciones_modelos()`` que trabaja con modelos
        Pydantic inmutables.

    Args:
        page: Página de Playwright para realizar las descargas.
        actuaciones: Lista de diccionarios con datos de actuaciones (SERÁ MUTADA).
        carpeta_destino: Ruta donde guardar los archivos descargados.

    Example:
        >>> # ❌ MAL - Muta la lista original
        >>> await descargar_archivos_actuaciones(page, actuaciones, carpeta)
        >>>
        >>> # ✅ BIEN - Trabaja con modelos inmutables
        >>> modelos = [Actuacion.from_dict(a) for a in actuaciones]
        >>> await descargar_archivos_actuaciones_modelos(page, modelos, carpeta)
    """
    warnings.warn(
        "descargar_archivos_actuaciones() está deprecated y será eliminada en v6.0. "
        "Use descargar_archivos_actuaciones_modelos() que trabaja con objetos inmutables.",
        DeprecationWarning,
        stacklevel=2
    )

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

        # SIDE EFFECT: Modifica el dict original
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




async def descargar_archivos_de_json(
    page,
    carpeta_json: str,
    carpeta_adjuntos: str | None = None,
):
    """Lee el archivo de actuaciones y descarga los adjuntos vinculados.

    Args:
        page: Página de Playwright desde la que se realizarán las descargas.
        carpeta_json: Directorio que contiene el archivo ``actuaciones-*.json``.
        carpeta_adjuntos: Carpeta en la que se guardarán los archivos descargados.
            Si no se proporciona se reutiliza ``carpeta_json``.
    """
    if not carpeta_json:
        logger.warning("⚠️ Carpeta de JSON no proporcionada para las descargas.")
        return

    if carpeta_adjuntos is None:
        carpeta_adjuntos = carpeta_json

    # Validar que la carpeta con los JSON existe
    if not os.path.exists(carpeta_json):
        try:
            os.makedirs(carpeta_json, exist_ok=True)
            logger.debug("📁 Carpeta creada: %s", carpeta_json)
        except OSError as e:
            logger.error("❌ Error al crear carpeta %s: %s", carpeta_json, e)
            return

    # Validar que es un directorio
    if not os.path.isdir(carpeta_json):
        logger.error("❌ La ruta no es un directorio: %s", carpeta_json)
        return

    # Validar carpeta de adjuntos
    if not os.path.exists(carpeta_adjuntos):
        try:
            os.makedirs(carpeta_adjuntos, exist_ok=True)
            logger.debug("📁 Carpeta creada para adjuntos: %s", carpeta_adjuntos)
        except OSError as e:
            logger.error("❌ Error al crear carpeta de adjuntos %s: %s", carpeta_adjuntos, e)
            return

    if not os.path.isdir(carpeta_adjuntos):
        logger.error("❌ La ruta de adjuntos no es un directorio: %s", carpeta_adjuntos)
        return

    # Buscar archivos JSON de actuaciones
    try:
        archivos_json = [
            f
            for f in os.listdir(carpeta_json)
            if f.startswith("actuaciones-") and f.endswith(".json")
        ]
    except OSError as e:
        logger.error("❌ Error al listar archivos en %s: %s", carpeta_json, e)
        return

    if archivos_json:
        ruta_json = os.path.join(carpeta_json, archivos_json[0])

        # Validar que el archivo existe
        if not os.path.exists(ruta_json):
            logger.error("❌ Archivo JSON no encontrado: %s", ruta_json)
            return

        # Validar que el archivo es legible
        if not os.access(ruta_json, os.R_OK):
            logger.error("❌ Sin permisos de lectura para: %s", ruta_json)
            return

        try:
            with open(ruta_json, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error("❌ El archivo no contiene JSON válido (%s): %s", ruta_json, e)
            return
        except OSError as e:
            logger.error("❌ Error al leer archivo %s: %s", ruta_json, e)
            return

        actuaciones = data.get("Actuaciones", [])
        actuaciones_filtradas = []

        for act in actuaciones:
            if act.get("TieneArchivo") and act.get("NombreArchivo"):
                archivo_path = os.path.join(carpeta_adjuntos, act["NombreArchivo"])
                if not os.path.exists(archivo_path):
                    actuaciones_filtradas.append(act)
                else:
                    act["Descargado"] = True
                    logger.debug("🟡 Ya existe: %s", act['NombreArchivo'])

        if actuaciones_filtradas:
            logger.info("\n🔽 Descargando %d archivo(s)...", len(actuaciones_filtradas))
            await descargar_archivos_actuaciones(page, actuaciones_filtradas, carpeta_adjuntos)
            for act in actuaciones_filtradas:
                act["Descargado"] = True
        else:
            logger.info("✅ Todos los archivos ya existen.")

        # Guardar archivo actualizado
        actualizar_metricas_descargas_en_json(data)

        # Validar permisos de escritura antes de guardar
        if not os.access(carpeta_json, os.W_OK):
            logger.error("❌ Sin permisos de escritura en: %s", carpeta_json)
            return

        try:
            with open(ruta_json, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("📝 JSON actualizado con estado de descarga.")
        except OSError as e:
            logger.error("❌ Error al guardar archivo %s: %s", ruta_json, e)
            return
    else:
        logger.warning("⚠️ No se encontró archivo de actuaciones unificado.")
