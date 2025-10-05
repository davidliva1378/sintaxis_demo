import re
from collections.abc import Callable
from datetime import datetime
from time import perf_counter

from playwright.async_api import (
    ElementHandle,
    Error,
    Locator,
    Page,
    TimeoutError,
)

# --- Config por defecto (ajustables por parámetro) ---
SEL_TABLA = "table.table-striped"
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

EXPEDIENTES_POR_PAGINA = 15

_ORDEN_MAP = {
    "fecha": "FECHA",
    "caratula": "CARATULA",
    "oficina": "OFICINA",
    "situacion": "SITUACION",
}

_SEL_ORDEN_SELECT = "#j_idt150\\:order_by_form\\:camara"
_SEL_ORDENAR_LINK = "a:has-text('Ordenar')"


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
    max_paginas: int = 200,
    omitir_duplicados: bool = True,
    detener_en_duplicado: bool = True,
    *,
    fecha_corte: str | None = None,
    tiempo_maximo_segundos: int | None = None,
    orden: str | None = None,
) -> tuple[list[dict], str, dict[str, object]]:
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
    resultados: list[dict] = []
    huellas: set[tuple[str, str, str]] = set()
    paginas_visitadas: dict[str, int] = {}
    metadata: dict[str, object] = {}
    paginas_esperadas: int | None = None
    filas_descartadas = 0
    duplicados_descartados = 0

    def _finalizar(motivo: str) -> tuple[list[dict], str, dict[str, object]]:
        metadata["filas_descartadas"] = filas_descartadas
        metadata["duplicados_descartados"] = duplicados_descartados
        metadata["paginas_recorridas"] = paginas_recorridas
        if paginas_esperadas is not None:
            metadata["paginas_esperadas"] = paginas_esperadas
        return resultados, motivo, metadata

    fecha_corte_dt: datetime | None = None
    if fecha_corte:
        fecha_corte_norm = _norm_fecha(fecha_corte)
        try:
            fecha_corte_dt = datetime.strptime(fecha_corte_norm, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError(
                "fecha_corte debe tener formato 'YYYY-MM-DD' o 'DD/MM/AAAA'"
            ) from exc

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

    if orden:
        valor_orden = _resolver_valor_orden(orden)
        if not valor_orden:
            print(
                f"⚠️ Valor de orden desconocido ({orden}). Se mantiene el orden actual."
            )
        else:
            try:
                await page.select_option(_SEL_ORDEN_SELECT, value=valor_orden)
                await page.locator(_SEL_ORDENAR_LINK).click()
                try:
                    await tabla.wait_for(state="hidden", timeout=5_000)
                except TimeoutError:
                    pass
                await tabla.wait_for(state="visible", timeout=25_000)
                print(f"🔽 Tabla ordenada por {orden.upper()}")
            except TimeoutError as exc:
                print(
                    f"⚠️ El reordenamiento por {orden} no se completó a tiempo: {exc}"
                )
            except Error as exc:
                print(f"⚠️ No se pudo reordenar la tabla por {orden}: {exc}")

    tbody_locator = page.locator(sel_tbody)

    paginas_recorridas = 0
    while True:
        if _excedio_tiempo():
            return _finalizar("limite_tiempo")

        paginas_recorridas += 1
        print(f"Procesando página {paginas_recorridas}")

        fingerprint_actual = await _tbody_fingerprint(tbody_locator)
        if fingerprint_actual in paginas_visitadas:
            pagina_prev = paginas_visitadas[fingerprint_actual]
            print(
                f"🔁 Página {paginas_recorridas} coincide con la ya vista en la "
                f"página {pagina_prev}. Finalizando para evitar bucles."
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

        # 2) Mapear a dicts usando las 5 columnas útiles
        for cols in filas:
            if len(cols) < 5:
                filas_descartadas += 1
                continue
            ultima_actuacion_norm = _norm_fecha(cols[4])
            ultima_dt: datetime | None = None
            if ultima_actuacion_norm:
                try:
                    ultima_dt = datetime.strptime(
                        ultima_actuacion_norm, "%Y-%m-%d"
                    )
                except ValueError:
                    ultima_dt = None

            numero = cols[0]
            dependencia = cols[1]
            caratula = cols[2]

            huella = (numero, caratula, dependencia)
            duplicado = huella in huellas

            if duplicado and detener_en_duplicado:
                return _finalizar("duplicado_encontrado")

            if fecha_corte_dt and ultima_dt and ultima_dt < fecha_corte_dt:
                return _finalizar("limite_fecha")

            if duplicado and omitir_duplicados:
                duplicados_descartados += 1
                continue

            if not duplicado:
                huellas.add(huella)

            resultados.append({
                "numero":           numero,
                "dependencia":      dependencia,
                "caratula":         caratula,
                "situacion":        cols[3],
                "ultima_actuacion": ultima_actuacion_norm,
            })

            if _excedio_tiempo():
                return _finalizar("limite_tiempo")

        # 3) Intentar ir a la siguiente página; cortar si no hay
        if paginas_recorridas >= max_paginas:
            return _finalizar("limite_paginas")

        next_btn = page.locator(sel_siguiente)
        btn_count = await next_btn.count()
        if btn_count <= 0:
            return _finalizar("sin_siguiente")  # no hay control de siguiente

        boton: Locator | None = None
        for idx in range(btn_count):
            candidato = next_btn.nth(idx)
            if await _is_locator_enabled(candidato) and await candidato.is_visible():
                boton = candidato
                break

        if boton is None:
            return _finalizar("sin_siguiente_habilitado")

        try:
            await boton.wait_for(state="visible", timeout=10_000)
        except TimeoutError as exc:
            print(f"Botón 'Siguiente' no visible: {exc}")
            return _finalizar("siguiente_timeout")

        if not await _is_locator_enabled(boton):
            return _finalizar("siguiente_deshabilitado")

        # Fingerprint antes del click para confirmar cambio real
        antes = fingerprint_actual
        try:
            await boton.click()
        except (TimeoutError, Error) as exc:
            print(f"Fallo al hacer clic en 'Siguiente': {exc}")
            return _finalizar("error_click")

        # Esperar a que cambie el tbody (evita loops)
        max_wait_ms = 12_000
        poll_interval_ms = 400
        elapsed_ms = 0
        fingerprint_cambio = False
        while elapsed_ms < max_wait_ms:
            despues = await _tbody_fingerprint(tbody_locator)
            if despues != antes:
                fingerprint_cambio = True
                break
            wait_time = min(poll_interval_ms, max_wait_ms - elapsed_ms)
            if wait_time <= 0:
                break
            await page.wait_for_timeout(wait_time)
            elapsed_ms += wait_time

        if not fingerprint_cambio:
            # No cambió el contenido → estamos al final
            return _finalizar("fin_listado")

        if _excedio_tiempo():
            return _finalizar("limite_tiempo")
    return _finalizar("fin_listado")


async def extraer_datos_expediente(page: Page) -> dict[str, str] | None:
    """Extrae los campos principales del expediente actualmente abierto."""

    try:
        await page.wait_for_load_state("load")
        await page.wait_for_timeout(2_000)

        numero = await page.query_selector("span[style='color:#000000;']")
        caratula = await page.query_selector(r"#expediente\:j_idt96\:detailCover")
        dependencia = await page.query_selector(r"#expediente\:j_idt96\:detailDependencia")
        jurisdiccion = await page.query_selector(r"#expediente\:j_idt96\:detailCamera")
        situacion = await page.query_selector(r"#expediente\:j_idt96\:detailSituation")

        return {
            "numero": await numero.inner_text() if numero else "No encontrado",
            "caratula": await caratula.inner_text() if caratula else "No encontrada",
            "dependencia": await dependencia.inner_text() if dependencia else "No encontrada",
            "jurisdiccion": await jurisdiccion.inner_text() if jurisdiccion else "No encontrada",
            "situacion": await situacion.inner_text() if situacion else "No encontrada",
        }
    except Exception as exc:  # noqa: BLE001 - queremos loguear cualquier falla
        print(f"⚠️ Error al extraer datos del expediente: {exc}")
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
        print("❌ No se proporcionó ninguna fila válida.")
        return None

    enlace = await fila.query_selector("a")
    if not enlace:
        print("⚠️ No se encontró enlace para abrir el expediente en la fila.")
        return None

    print("👁 Haciendo clic para abrir el expediente...")
    await enlace.click()
    await page.wait_for_load_state("load")
    await page.wait_for_timeout(2_000)

    datos = await extraer_datos_expediente(page)
    if datos:
        print("✅ Datos del expediente extraídos correctamente.")
        return datos

    print("⚠️ No se pudieron extraer datos. Posible error de apertura.")
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
        print("❌ No hay filas disponibles para seleccionar.")
        return None

    descripcion_final = descripcion_estrategia or (
        "automática" if estrategia_seleccion is None else "personalizada"
    )

    if len(filas) == 1:
        print(
            "✅ Solo un expediente encontrado. "
            f"La estrategia '{descripcion_final}' no es necesaria."
        )
        fila = filas[0]
    else:
        print(
            "🔎 Se encontraron múltiples expedientes. "
            f"Aplicando estrategia '{descripcion_final}'."
        )
        opciones_filas: list[ElementHandle | Locator] = []
        opciones_datos: list[dict[str, str]] = []

        for idx, fila in enumerate(filas, start=1):
            columnas = await fila.query_selector_all("td")
            if len(columnas) >= 3:
                nro = (await columnas[0].inner_text()).strip()
                anio_fila = (await columnas[1].inner_text()).strip()
                caratula_fila = (await columnas[2].inner_text()).strip()
                print(
                    f"[{idx}] Número: {nro} / Año: {anio_fila} / Carátula: {caratula_fila}"
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
            print("❌ No se pudieron obtener opciones válidas para seleccionar.")
            return None

        estrategia = estrategia_seleccion or _seleccionar_primera_opcion
        indice = estrategia(opciones_datos)

        if indice is None:
            print(
                "❌ La estrategia de selección no devolvió ninguna opción válida."
            )
            return None

        if not isinstance(indice, int) or indice < 0 or indice >= len(opciones_filas):
            print(
                "❌ La estrategia devolvió un índice fuera de rango: "
                f"{indice} (opciones disponibles: {len(opciones_filas)})."
            )
            return None

        print(
            f"🎯 Estrategia '{descripcion_final}' seleccionó la opción {indice + 1}."
        )
        fila = opciones_filas[indice]

    datos = await abrir_expediente_desde_fila(fila, page)
    if not datos:
        print("⚠️ No se pudo abrir el expediente seleccionado.")
        return None

    print("✅ Datos extraídos correctamente del expediente.")
    return datos


async def buscar_expediente_por_numero(
    page: Page, numero: str, anio: str, timeout: int = 8_000
) -> tuple[bool, str]:
    try:
        print(f"🔎 Buscando expediente {numero}/{anio} usando el formulario...")

        await page.click("a[href='#collapseOne']")
        await page.wait_for_selector("#collapseOne.collapse.in", timeout=5_000)

        await page.fill("#j_idt83\\:consultaExpediente\\:j_idt116\\:numero", numero)
        await page.fill("#j_idt83\\:consultaExpediente\\:j_idt118\\:anio", anio)

        await page.click("#j_idt83\\:consultaExpediente\\:consultaFiltroSearchButtonSAU")

        try:
            await page.wait_for_selector(
                "text=No se han encontrado expedientes", timeout=3_000
            )
            print(f"❗ Expediente {numero}/{anio} no encontrado.")
            return False, "no_encontrado"
        except TimeoutError:
            pass

        await page.wait_for_selector("table.table-striped", timeout=timeout)
        print(f"✅ Resultados cargados correctamente para {numero}/{anio}.")
        return True, "OK"

    except TimeoutError:
        print(f"⏳ Tiempo de espera agotado buscando expediente {numero}/{anio}.")
        return False, "timeout"

    except Exception as exc:  # noqa: BLE001
        print(f"❌ Error general buscando expediente {numero}/{anio}: {exc}")
        return False, "error"


async def buscar_expedientes_por_caratula(
    page: Page, caratula: str
) -> list[ElementHandle]:
    """Realiza la búsqueda de expedientes utilizando sólo la carátula."""

    if not caratula:
        print("❌ Debe indicar una carátula válida para utilizar este modo de búsqueda.")
        return []

    print(
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

    assert numero is not None and anio is not None
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

    if caratula:
        filas_filtradas: list[ElementHandle] = []
        for fila in filas:
            columnas = await fila.query_selector_all("td")
            if len(columnas) >= 3:
                caratula_texto = (await columnas[2].inner_text()).strip().lower()
                if caratula_texto == caratula.lower():
                    filas_filtradas.append(fila)
        return filas_filtradas

    return filas
