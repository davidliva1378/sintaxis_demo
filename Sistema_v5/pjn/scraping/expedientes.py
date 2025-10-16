import re
from collections.abc import Callable
from datetime import datetime
from time import perf_counter
from typing import Mapping, Sequence, TypeVar

from playwright.async_api import (
    ElementHandle,
    Error,
    Locator,
    Page,
    TimeoutError,
)

from ..config import get_config
from ..models import ExpedienteResumen
from ..parsers.expedientes_parser import parse_expediente_resumen
from ..selectores import SEL_EXPEDIENTES
from ..utils.logging import get_logger
from .pagination import PaginationStrategy, DEFAULT_PAGINATION_STRATEGY

logger = get_logger(__name__)
_config = get_config()

# --- Config por defecto (ajustables por parámetro) ---
SEL_TABLA = SEL_EXPEDIENTES.TABLA_RESULTADOS
SEL_TBODY = f"{SEL_TABLA} tbody"
# Varios selectores posibles de "Siguiente" (ajustá según tu portal)
SEL_SIGUIENTE = ", ".join(
    [
        "a[aria-label='Siguiente']",
        "button[aria-label='Siguiente']",
        "a:has(span[title='Siguiente'])",
        "button:has(span[title='Siguiente'])",
        ".pagination li.next:not(.disabled) a",
        ".pagination a:has-text('Siguiente')",
        ".rf-ds-btn-next",
    ]
)

EXPEDIENTES_POR_PAGINA = _config.scraping.expedientes_por_pagina

_ORDEN_MAP = {
    "fecha": "FECHA",
    "caratula": "CARATULA",
    "oficina": "OFICINA",
    "situacion": "SITUACION",
}

_SEL_ORDEN_SELECT = "#j_idt150\\:order_by_form\\:camara"
_SEL_ORDENAR_LINK = "a:has-text('Ordenar')"


TResumen = TypeVar("TResumen")


def _parsear_fecha_corte(fecha_corte: str | None) -> datetime | None:
    """Parsea y valida la fecha de corte.

    Args:
        fecha_corte: Fecha en formato 'YYYY-MM-DD' o 'DD/MM/AAAA'.

    Returns:
        datetime object si la fecha es válida, None si no se proporciona fecha.

    Raises:
        ValueError: Si el formato de fecha es inválido.
    """
    if not fecha_corte:
        return None

    fecha_corte_norm = _norm_fecha(fecha_corte)
    try:
        return datetime.strptime(fecha_corte_norm, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(
            "fecha_corte debe tener formato 'YYYY-MM-DD' o 'DD/MM/AAAA'"
        ) from exc


def _resolver_valor_orden(orden: str | None) -> str | None:
    if not orden:
        return None
    return _ORDEN_MAP.get(orden.lower())

def _norm_fecha(s: str) -> str:
    """Convierte dd/mm/yyyy o d/m/yyyy a YYYY-MM-DD. Si no matchea, devuelve original."""
    s = (s or "").strip()
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2,4})$", s)
    if not m:
        return s
    d, m_, y = m.groups()
    if len(y) == 2:
        y = "20" + y
    try:
        return datetime(int(y), int(m_), int(d)).strftime("%Y-%m-%d")
    except ValueError:
        return s  # por si viene algo raro

_FP_MAX_LEN = 4_096


def _build_fingerprint(html: str, max_len: int | None = _FP_MAX_LEN) -> str:
    signature = f"{len(html)}::{html}"
    if max_len is None:
        return signature
    return signature[:max_len]


_FORM_CONTROL_TAGS = {
    "button",
    "input",
    "select",
    "textarea",
    "option",
    "optgroup",
}


SeleccionEstrategia = Callable[[list[dict[str, str]]], int | None]


async def _is_locator_enabled(locator: Locator) -> bool:
    """Determina si un locator corresponde a un control habilitado."""

    try:
        tag_name = await locator.evaluate("el => el.tagName.toLowerCase()")
    except Error:
        return False

    if tag_name in _FORM_CONTROL_TAGS:
        try:
            return await locator.is_enabled()
        except Error:
            pass

    try:
        aria_disabled = (await locator.get_attribute("aria-disabled")) or ""
        if aria_disabled.strip().lower() in {"true", "1"}:
            return False

        if await locator.get_attribute("disabled") is not None:
            return False

        class_attr = (await locator.get_attribute("class")) or ""
    except Error:
        return False

    if re.search(r"\\bdisabled\\b", class_attr, re.IGNORECASE):
        return False

    return True


async def _tbody_fingerprint(tbody: Locator | ElementHandle) -> str:
    """
    Crea un fingerprint simple del tbody para detectar cambio de página.

    Al recibir directamente el locator/handle podemos usar cualquier motor de
    selectores soportados por Playwright (css=, xpath=, text=, etc.).
    """
    html = await tbody.inner_html()
    return _build_fingerprint(html)

_SEL_TOTAL_EXPEDIENTES = "strong:has-text('Se han encontrado')"


async def _navegar_siguiente_pagina(
    page: Page,
    tbody_locator: Locator,
    sel_siguiente: str,
    fingerprint_actual: str,
    estrategia: PaginationStrategy | None = None,
) -> tuple[bool, str | None]:
    """Intenta navegar a la siguiente página y verifica que haya cambiado el contenido.

    Args:
        page: Página de Playwright.
        tbody_locator: Locator del tbody para verificar cambios.
        sel_siguiente: Selector del botón "Siguiente" (usado si no hay estrategia).
        fingerprint_actual: Fingerprint del tbody antes de hacer clic.
        estrategia: Estrategia de paginación a usar. Si es None, usa lógica legacy.

    Returns:
        tuple[exito, motivo_fallo]:
            - exito: True si navegó correctamente y cambió el contenido
            - motivo_fallo: Código de error si falló, None si tuvo éxito

    Note:
        Si se proporciona una estrategia, el parámetro sel_siguiente se ignora
        ya que la estrategia maneja sus propios selectores.
    """
    # Si se proporciona estrategia, delegar a ella
    if estrategia is not None:
        return await estrategia.navegar_siguiente(page, tbody_locator, fingerprint_actual)

    # Código legacy (compatible con versiones anteriores)
    next_btn = page.locator(sel_siguiente)
    btn_count = await next_btn.count()
    if btn_count <= 0:
        return False, "sin_siguiente"

    # Buscar botón habilitado y visible
    boton: Locator | None = None
    for idx in range(btn_count):
        candidato = next_btn.nth(idx)
        if await _is_locator_enabled(candidato) and await candidato.is_visible():
            boton = candidato
            break

    if boton is None:
        return False, "sin_siguiente_habilitado"

    # Esperar que sea visible
    try:
        await boton.wait_for(state="visible", timeout=10_000)
    except TimeoutError as exc:
        logger.warning("Botón 'Siguiente' no visible: %s", exc)
        return False, "siguiente_timeout"

    if not await _is_locator_enabled(boton):
        return False, "siguiente_deshabilitado"

    # Hacer clic
    try:
        await boton.click()
    except (TimeoutError, Error) as exc:
        logger.error("Fallo al hacer clic en 'Siguiente': %s", exc)
        return False, "error_click"

    # Esperar a que cambie el tbody
    max_wait_ms = 12_000
    poll_interval_ms = 400
    elapsed_ms = 0
    fingerprint_cambio = False

    while elapsed_ms < max_wait_ms:
        despues = await _tbody_fingerprint(tbody_locator)
        if despues != fingerprint_actual:
            fingerprint_cambio = True
            break
        wait_time = min(poll_interval_ms, max_wait_ms - elapsed_ms)
        if wait_time <= 0:
            break
        await page.wait_for_timeout(wait_time)
        elapsed_ms += wait_time

    if not fingerprint_cambio:
        return False, "fin_listado"

    return True, None


def _procesar_expediente_resumen(
    resumen: ExpedienteResumen,
    fecha_corte_dt: datetime | None,
    huellas: set[tuple[str, str, str]],
    omitir_duplicados: bool,
    detener_en_duplicado: bool,
) -> tuple[bool, bool, bool]:
    """Procesa un resumen de expediente y determina si debe agregarse.

    Args:
        resumen: Resumen del expediente extraído.
        fecha_corte_dt: Fecha de corte para filtrar (None = sin filtro).
        huellas: Set de huellas ya vistas (numero, caratula, dependencia).
        omitir_duplicados: Si True, no agrega duplicados.
        detener_en_duplicado: Si True, detiene extracción al encontrar duplicado.

    Returns:
        tuple[agregar, detener, es_duplicado]:
            - agregar: True si debe agregarse a resultados
            - detener: True si debe detenerse la extracción
            - es_duplicado: True si es un duplicado
    """
    # Parsear fecha de última actuación
    ultima_actuacion_norm = resumen.ultima_actuacion
    ultima_dt: datetime | None = None
    if ultima_actuacion_norm:
        try:
            ultima_dt = datetime.strptime(ultima_actuacion_norm, "%Y-%m-%d")
        except ValueError:
            ultima_dt = None

    # Crear huella para detectar duplicados
    huella = (resumen.numero, resumen.caratula, resumen.dependencia)
    es_duplicado = huella in huellas

    # Verificar si debe detenerse por duplicado
    if es_duplicado and detener_en_duplicado:
        return False, True, True

    # Verificar si supera fecha de corte
    if fecha_corte_dt and ultima_dt and ultima_dt < fecha_corte_dt:
        return False, True, False

    # Verificar si debe omitirse por duplicado
    if es_duplicado and omitir_duplicados:
        return False, False, True

    # Agregar huella si no es duplicado
    if not es_duplicado:
        huellas.add(huella)

    return True, False, es_duplicado


async def _aplicar_ordenamiento_tabla(
    page: Page,
    tabla: Locator,
    orden: str | None,
) -> None:
    """Aplica ordenamiento a la tabla de expedientes si se especifica.

    Args:
        page: Página de Playwright.
        tabla: Locator de la tabla de expedientes.
        orden: Criterio de orden ('fecha', 'caratula', 'oficina', 'situacion').

    Raises:
        No lanza excepciones, solo loguea warnings si falla el ordenamiento.
    """
    if not orden:
        return

    valor_orden = _resolver_valor_orden(orden)
    if not valor_orden:
        logger.warning(
            "⚠️ Valor de orden desconocido (%s). Se mantiene el orden actual.", orden
        )
        return

    try:
        await page.select_option(_SEL_ORDEN_SELECT, value=valor_orden)
        await page.locator(_SEL_ORDENAR_LINK).click()
        try:
            await tabla.wait_for(state="hidden", timeout=5_000)
        except TimeoutError:
            pass
        await tabla.wait_for(state="visible", timeout=25_000)
        logger.info("🔽 Tabla ordenada por %s", orden.upper())
    except TimeoutError as exc:
        logger.warning(
            "⚠️ El reordenamiento por %s no se completó a tiempo: %s", orden, exc
        )
    except Error as exc:
        logger.warning("⚠️ No se pudo reordenar la tabla por %s: %s", orden, exc)


async def _extraer_total_esperado(page: Page) -> int | None:
    """Intenta leer el total anunciado en el encabezado del listado."""

    try:
        total_locator = page.locator(_SEL_TOTAL_EXPEDIENTES)
        if await total_locator.count() <= 0:
            return None
        texto = await total_locator.first.inner_text()
    except Error:
        return None

    coincidencia = re.search(r"total de\s*([\d.,]+)", texto)
    if not coincidencia:
        coincidencia = re.search(r"([\d][\d.,]*)", texto)

    if not coincidencia:
        return None

    numero = re.sub(r"[^\d]", "", coincidencia.group(1))
    if not numero:
        return None

    try:
        return int(numero)
    except ValueError:
        return None


async def extraer_expedientes_completos(
    page: Page,
    sel_tabla: str = SEL_TABLA,
    sel_tbody: str = SEL_TBODY,
    sel_siguiente: str = SEL_SIGUIENTE,
    max_paginas: int | None = None,
    omitir_duplicados: bool = True,
    detener_en_duplicado: bool = True,
    *,
    fecha_corte: str | None = None,
    tiempo_maximo_segundos: int | None = None,
    orden: str | None = None,
    mapper: Callable[[ExpedienteResumen], TResumen] | None = None,
    pagination_strategy: PaginationStrategy | None = None,
) -> tuple[list[TResumen], str, dict[str, object]]:
    """
    Extrae TODAS las páginas del listado de expedientes y devuelve:
    [
      {
        "numero": "...",
        "dependencia": "...",
        "caratula": "...",
        "situacion": "...",
        "ultima_actuacion": "YYYY-MM-DD",
      },
      ...
    ]

    `sel_tabla` puede utilizar cualquier motor de selectores soportado por
    Playwright (css=, xpath=, text=, etc.).

    Selectores por defecto
    ----------------------
    ==================  =========================  =====================================
    Constante           Valor por defecto          Propósito
    ==================  =========================  =====================================
    ``SEL_TABLA``       ``"table.table-striped"``  Tabla principal del listado.
    ``SEL_TBODY``       ``f"{SEL_TABLA} tbody"``   Valor por defecto del parámetro
                                                ``sel_tbody``; apunta al cuerpo de la
                                                tabla desde donde se leen las filas.
    ``SEL_SIGUIENTE``   Cadena con múltiples       Control que avanza a la página
                        selectores                 siguiente del paginado.
    ==================  =========================  =====================================

    Parámetros posicionales
    -----------------------
    page (Page):
        Página de Playwright ya posicionada sobre el listado de expedientes.
    sel_tabla (str, predeterminado=``SEL_TABLA``):
        Selector del elemento ``<table>`` que contiene el paginado de expedientes.
    sel_tbody (str, predeterminado=``SEL_TBODY``):
        Selector (CSS) del contenedor que agrupa las filas dentro de la tabla. Se
        utiliza para ubicar las filas como ``f"{sel_tbody} tr"``. Si el listado no
        utiliza ``<tbody>``, ajustá este selector al nodo que contenga las filas.
    sel_siguiente (str, predeterminado=``SEL_SIGUIENTE``):
        Selector (o conjunto de selectores) para ubicar el control "Siguiente".
    max_paginas (int, predeterminado=``200``):
        Límite máximo de páginas a recorrer antes de abortar la extracción.

    Parámetros opcionales
    ---------------------
    fecha_corte:
        Fecha mínima (inclusive) en formato ``YYYY-MM-DD`` o ``DD/MM/AAAA``.
        Cuando la columna ``ultima_actuacion`` cae por debajo de este umbral se
        finaliza la extracción inmediatamente y se retorna el motivo
        ``"limite_fecha"``.
    tiempo_maximo_segundos:
        Límite máximo de duración del scraping. Al superarse se devuelve lo
        acumulado hasta el momento con motivo ``"limite_tiempo"``.
    omitir_duplicados:
        Cuando es ``True`` (valor por defecto) evita agregar filas duplicadas
        detectadas a partir de la combinación (``numero``, ``caratula``,
        ``dependencia``).
    detener_en_duplicado:
        Si está activo y se detecta un duplicado, finaliza inmediatamente la
        extracción devolviendo el motivo ``"duplicado_encontrado"`` junto con lo
        acumulado hasta el momento.
    orden:
        Permite reordenar el listado antes de comenzar la extracción.
        Actualmente acepta ``"fecha"``, ``"caratula"``, ``"oficina"`` y
        ``"situacion"`` (sin distinción entre mayúsculas y minúsculas).
    pagination_strategy:
        Estrategia de paginación a usar (opcional). Si se proporciona, reemplaza
        la lógica de navegación por defecto. Útil para adaptar el scraper a
        diferentes frameworks de paginación (e.g., Bootstrap, Material-UI, etc.).
        Si es None, usa la lógica legacy basada en selectores CSS.
        Ver ``pjn.scraping.pagination.PaginationStrategy`` para implementar
        estrategias personalizadas.

    Retorna
    -------
    tuple[list[dict], str, dict[str, object]]
        Una tupla ``(expedientes, motivo, metadata)`` donde ``expedientes`` es la
        lista de diccionarios extraídos, ``motivo`` el código de finalización y
        ``metadata`` un diccionario con información adicional recolectada durante
        la extracción. Actualmente incluye la clave ``"total_esperado"`` cuando
        el portal anuncia explícitamente el total de expedientes disponibles.
        Los códigos de motivo actuales son:

        * ``"fin_listado"``: se alcanzó el final natural del paginado.
        * ``"limite_paginas"``: se alcanzó ``max_paginas``.
        * ``"limite_fecha"``: se superó el umbral ``fecha_corte``.
        * ``"limite_tiempo"``: se superó ``tiempo_maximo_segundos``.
        * ``"sin_siguiente"``: no existe control para pasar de página.
        * ``"sin_siguiente_habilitado"``: no hay botón "Siguiente" habilitado.
        * ``"siguiente_timeout"``: el botón "Siguiente" no apareció a tiempo.
        * ``"siguiente_deshabilitado"``: el botón se deshabilitó al intentar usarlo.
        * ``"error_click"``: falló el clic en "Siguiente".
        * ``"duplicado_encontrado"``: se detectó un expediente repetido.
        * ``"bucle_detectado"``: se detectó un ciclo al intentar avanzar.
    """
    # Resolver max_paginas desde config si no se especificó
    if max_paginas is None:
        max_paginas = _config.scraping.max_paginas_expedientes

    resultados: list[TResumen] = []
    huellas: set[tuple[str, str, str]] = set()
    paginas_visitadas: dict[str, int] = {}
    metadata: dict[str, object] = {}
    paginas_esperadas: int | None = None
    filas_descartadas = 0
    duplicados_descartados = 0
    paginas_recorridas = 0

    resumen_mapper: Callable[[ExpedienteResumen], TResumen]
    if mapper is None:
        resumen_mapper = lambda resumen: resumen.to_dict()  # type: ignore[return-value]
    else:
        resumen_mapper = mapper

    def _finalizar(motivo: str) -> tuple[list[dict], str, dict[str, object]]:
        metadata["filas_descartadas"] = filas_descartadas
        metadata["duplicados_descartados"] = duplicados_descartados
        metadata["paginas_recorridas"] = paginas_recorridas
        if paginas_esperadas is not None:
            metadata["paginas_esperadas"] = paginas_esperadas
        return resultados, motivo, metadata

    # Validar y parsear fecha de corte
    fecha_corte_dt = _parsear_fecha_corte(fecha_corte)

    inicio = perf_counter()

    def _excedio_tiempo() -> bool:
        return (
            tiempo_maximo_segundos is not None
            and (perf_counter() - inicio) > tiempo_maximo_segundos
        )

    # Aseguramos presencia de tabla
    tabla = page.locator(sel_tabla)
    await tabla.wait_for(state="visible", timeout=25_000)

    total_esperado = await _extraer_total_esperado(page)
    if total_esperado is not None:
        metadata["total_esperado"] = total_esperado
        if isinstance(total_esperado, int):
            paginas_esperadas = (
                (total_esperado + EXPEDIENTES_POR_PAGINA - 1)
                // EXPEDIENTES_POR_PAGINA
            )

    # Aplicar ordenamiento si se especifica
    await _aplicar_ordenamiento_tabla(page, tabla, orden)

    tbody_locator = page.locator(sel_tbody)

    while True:
        if _excedio_tiempo():
            return _finalizar("limite_tiempo")

        paginas_recorridas += 1
        logger.info("Procesando página %d", paginas_recorridas)

        fingerprint_actual = await _tbody_fingerprint(tbody_locator)
        if fingerprint_actual in paginas_visitadas:
            pagina_prev = paginas_visitadas[fingerprint_actual]
            logger.warning(
                "🔁 Página %d coincide con la ya vista en la página %d. Finalizando para evitar bucles.",
                paginas_recorridas, pagina_prev
            )
            return _finalizar("bucle_detectado")

        paginas_visitadas[fingerprint_actual] = paginas_recorridas

        # 1) Extraer filas visibles de ESTA página en un solo evaluate
        filas: list[list[str]] = await page.evaluate(
            """(tbodySelector) => Array.from(
                    document.querySelectorAll(`${tbodySelector} tr`),
                    tr => Array.from(tr.cells, c => c.innerText.trim())
                )""",
            sel_tbody,
        )

        # 2) Mapear a objetos usando las columnas útiles
        for cols in filas:
            resumen = parse_expediente_resumen(cols)
            if resumen is None:
                filas_descartadas += 1
                continue

            # Procesar expediente y determinar si agregarlo
            agregar, detener, es_duplicado = _procesar_expediente_resumen(
                resumen,
                fecha_corte_dt,
                huellas,
                omitir_duplicados,
                detener_en_duplicado,
            )

            if detener:
                motivo = "duplicado_encontrado" if es_duplicado else "limite_fecha"
                return _finalizar(motivo)

            if es_duplicado:
                duplicados_descartados += 1

            if agregar:
                resultados.append(resumen_mapper(resumen))

            if _excedio_tiempo():
                return _finalizar("limite_tiempo")

        # 3) Intentar ir a la siguiente página; cortar si no hay
        if paginas_recorridas >= max_paginas:
            return _finalizar("limite_paginas")

        # Navegar a siguiente página
        exito, motivo = await _navegar_siguiente_pagina(
            page,
            tbody_locator,
            sel_siguiente,
            fingerprint_actual,
            estrategia=pagination_strategy,
        )

        if not exito:
            return _finalizar(motivo)

        if _excedio_tiempo():
            return _finalizar("limite_tiempo")

    return _finalizar("fin_listado")


async def extraer_expedientes_completos_modelos(
    page: Page,
    sel_tabla: str = SEL_TABLA,
    sel_tbody: str = SEL_TBODY,
    sel_siguiente: str = SEL_SIGUIENTE,
    max_paginas: int | None = None,
    omitir_duplicados: bool = True,
    detener_en_duplicado: bool = True,
    *,
    fecha_corte: str | None = None,
    tiempo_maximo_segundos: int | None = None,
    orden: str | None = None,
    pagination_strategy: PaginationStrategy | None = None,
) -> tuple[list[ExpedienteResumen], str, dict[str, object]]:
    """Versión que devuelve :class:`ExpedienteResumen` en lugar de dicts.

    Args:
        Ver documentación de :func:`extraer_expedientes_completos`.

    Returns:
        tuple[list[ExpedienteResumen], str, dict]: Lista de modelos ExpedienteResumen,
        motivo de finalización y metadata.
    """

    mapper = lambda resumen: resumen
    resultados, motivo, metadata = await extraer_expedientes_completos(
        page,
        sel_tabla=sel_tabla,
        sel_tbody=sel_tbody,
        sel_siguiente=sel_siguiente,
        max_paginas=max_paginas,
        omitir_duplicados=omitir_duplicados,
        detener_en_duplicado=detener_en_duplicado,
        fecha_corte=fecha_corte,
        tiempo_maximo_segundos=tiempo_maximo_segundos,
        orden=orden,
        mapper=mapper,
        pagination_strategy=pagination_strategy,
    )
    return resultados, motivo, metadata



async def extraer_datos_expediente(page: Page) -> dict[str, str] | None:
    """Extrae los campos principales del expediente actualmente abierto."""

    try:
        await page.wait_for_load_state("load")
        await page.wait_for_timeout(2_000)

        numero = await page.query_selector(SEL_EXPEDIENTES.NUMERO_DETALLE)
        caratula = await page.query_selector(SEL_EXPEDIENTES.CARATULA_DETALLE)
        dependencia = await page.query_selector(SEL_EXPEDIENTES.DEPENDENCIA_DETALLE)
        jurisdiccion = await page.query_selector(SEL_EXPEDIENTES.JURISDICCION_DETALLE)
        situacion = await page.query_selector(SEL_EXPEDIENTES.SITUACION_DETALLE)

        return {
            "numero": await numero.inner_text() if numero else "No encontrado",
            "caratula": await caratula.inner_text() if caratula else "No encontrada",
            "dependencia": await dependencia.inner_text() if dependencia else "No encontrada",
            "jurisdiccion": await jurisdiccion.inner_text() if jurisdiccion else "No encontrada",
            "situacion": await situacion.inner_text() if situacion else "No encontrada",
        }
    except Exception as exc:  # noqa: BLE001 - queremos loguear cualquier falla
        logger.error("⚠️ Error al extraer datos del expediente: %s", exc)
        return None


async def abrir_expediente_desde_fila(
    fila: ElementHandle | Locator | None, page: Page
) -> dict[str, str] | None:
    """
    Abre el expediente asociado a ``fila`` y devuelve los datos extraídos.

    Estas utilidades complementan a ``extraer_expedientes_completos`` y se
    mantienen para compatibilidad con flujos que operan fila a fila.
    """

    if not fila:
        logger.error("❌ No se proporcionó ninguna fila válida.")
        return None

    enlace = await fila.query_selector(SEL_EXPEDIENTES.ENLACE_EXPEDIENTE)
    if not enlace:
        logger.warning("⚠️ No se encontró enlace para abrir el expediente en la fila.")
        return None

    logger.info("👁 Haciendo clic para abrir el expediente...")
    await enlace.click()
    await page.wait_for_load_state("load")
    await page.wait_for_timeout(2_000)

    datos = await extraer_datos_expediente(page)
    if datos:
        logger.info("✅ Datos del expediente extraídos correctamente.")
        return datos

    logger.warning("⚠️ No se pudieron extraer datos. Posible error de apertura.")
    return None


def _seleccionar_primera_opcion(opciones: list[dict[str, str]]) -> int | None:
    """Estrategia por defecto: selecciona la primera opción disponible."""

    return 0 if opciones else None


async def mostrar_y_elegir_expediente(
    page: Page,
    filas: list[ElementHandle | Locator],
    *,
    estrategia_seleccion: SeleccionEstrategia | None = None,
    descripcion_estrategia: str | None = None,
) -> dict[str, str] | None:
    """Muestra las filas encontradas y abre la opción seleccionada."""

    if not filas:
        logger.error("❌ No hay filas disponibles para seleccionar.")
        return None

    descripcion_final = descripcion_estrategia or (
        "automática" if estrategia_seleccion is None else "personalizada"
    )

    if len(filas) == 1:
        logger.info(
            "✅ Solo un expediente encontrado. La estrategia '%s' no es necesaria.",
            descripcion_final
        )
        fila = filas[0]
    else:
        logger.info(
            "🔎 Se encontraron múltiples expedientes. Aplicando estrategia '%s'.",
            descripcion_final
        )
        opciones_filas: list[ElementHandle | Locator] = []
        opciones_datos: list[dict[str, str]] = []

        for idx, fila in enumerate(filas, start=1):
            columnas = await fila.query_selector_all(SEL_EXPEDIENTES.COLUMNAS_FILA)
            if len(columnas) >= 3:
                nro = (await columnas[0].inner_text()).strip()
                anio_fila = (await columnas[1].inner_text()).strip()
                caratula_fila = (await columnas[2].inner_text()).strip()
                logger.info(
                    "[%d] Número: %s / Año: %s / Carátula: %s",
                    idx, nro, anio_fila, caratula_fila
                )
                opciones_filas.append(fila)
                opciones_datos.append(
                    {
                        "indice": str(idx - 1),
                        "numero": nro,
                        "anio": anio_fila,
                        "caratula": caratula_fila,
                    }
                )

        if not opciones_filas:
            logger.error("❌ No se pudieron obtener opciones válidas para seleccionar.")
            return None

        estrategia = estrategia_seleccion or _seleccionar_primera_opcion
        indice = estrategia(opciones_datos)

        if indice is None:
            logger.error(
                "❌ La estrategia de selección no devolvió ninguna opción válida."
            )
            return None

        if not isinstance(indice, int) or indice < 0 or indice >= len(opciones_filas):
            logger.error(
                "❌ La estrategia devolvió un índice fuera de rango: %d (opciones disponibles: %d).",
                indice, len(opciones_filas)
            )
            return None

        logger.info(
            "🎯 Estrategia '%s' seleccionó la opción %d.", descripcion_final, indice + 1
        )
        fila = opciones_filas[indice]

    datos = await abrir_expediente_desde_fila(fila, page)
    if not datos:
        logger.warning("⚠️ No se pudo abrir el expediente seleccionado.")
        return None

    logger.info("✅ Datos extraídos correctamente del expediente.")
    return datos


async def buscar_expediente_por_numero(
    page: Page, numero: str, anio: str, timeout: int = 8_000
) -> tuple[bool, str]:
    try:
        logger.info("🔎 Buscando expediente %s/%s usando el formulario...", numero, anio)

        await page.click("a[href='#collapseOne']")
        await page.wait_for_selector("#collapseOne.collapse.in", timeout=5_000)

        await page.fill("#j_idt83\\:consultaExpediente\\:j_idt116\\:numero", numero)
        await page.fill("#j_idt83\\:consultaExpediente\\:j_idt118\\:anio", anio)

        await page.click("#j_idt83\\:consultaExpediente\\:consultaFiltroSearchButtonSAU")

        try:
            await page.wait_for_selector(
                "text=No se han encontrado expedientes", timeout=3_000
            )
            logger.warning("❗ Expediente %s/%s no encontrado.", numero, anio)
            return False, "no_encontrado"
        except TimeoutError:
            pass

        await page.wait_for_selector("table.table-striped", timeout=timeout)
        logger.info("✅ Resultados cargados correctamente para %s/%s.", numero, anio)
        return True, "OK"

    except TimeoutError:
        logger.error("⏳ Tiempo de espera agotado buscando expediente %s/%s.", numero, anio)
        return False, "timeout"

    except Exception as exc:  # noqa: BLE001
        logger.error("❌ Error general buscando expediente %s/%s: %s", numero, anio, exc)
        return False, "error"


async def buscar_expedientes_por_caratula(
    page: Page, caratula: str
) -> list[ElementHandle]:
    """Realiza la búsqueda de expedientes utilizando sólo la carátula."""

    if not caratula:
        logger.error("❌ Debe indicar una carátula válida para utilizar este modo de búsqueda.")
        return []

    logger.info(
        "ℹ️ La búsqueda exclusiva por carátula no está automatizada aún. "
        "Se devuelve una lista vacía para permitir un manejo seguro."
    )
    return []


async def buscar_expedientes(
    page: Page,
    numero: str | None = None,
    anio: str | None = None,
    caratula: str | None = None,
) -> list[ElementHandle]:
    """Busca expedientes en el portal PJN según los filtros indicados."""

    numero = numero.strip() if numero and numero.strip() else None
    anio = anio.strip() if anio and anio.strip() else None
    caratula = caratula.strip() if caratula and caratula.strip() else None

    if numero and not anio:
        logger.error("❌ Para buscar por número debe indicar también el año del expediente.")
        return []

    if anio and not numero:
        logger.error("❌ Para buscar por año debe indicar también el número del expediente.")
        return []

    if not numero and not caratula:
        logger.error(
            "❌ Debe proporcionar un número y año del expediente o bien una carátula para realizar la búsqueda."
        )
        return []

    if not numero and caratula:
        return await buscar_expedientes_por_caratula(page, caratula)

    assert numero is not None and anio is not None
    exito, motivo = await buscar_expediente_por_numero(page, numero, anio)

    if not exito:
        if motivo == "no_encontrado":
            logger.warning("❗ No se encontraron expedientes para los datos ingresados.")
        elif motivo == "timeout":
            logger.error("⏳ La búsqueda tardó demasiado en cargar.")
        else:
            logger.error("❌ Error inesperado durante la búsqueda: %s", motivo)
        return []

    tabla = await page.query_selector("table.table-striped")
    if not tabla:
        logger.warning("⚠️ No se encontró la tabla de resultados.")
        return []

    filas = await tabla.query_selector_all("tbody tr")
    if not filas:
        logger.error("❌ No se encontraron filas en la tabla de resultados.")
        return []

    if caratula:
        filas_filtradas: list[ElementHandle] = []
        for fila in filas:
            columnas = await fila.query_selector_all(SEL_EXPEDIENTES.COLUMNAS_FILA)
            if len(columnas) >= 3:
                caratula_texto = (await columnas[2].inner_text()).strip().lower()
                if caratula_texto == caratula.lower():
                    filas_filtradas.append(fila)
        return filas_filtradas

    return filas
