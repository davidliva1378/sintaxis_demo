import re
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

async def extraer_expedientes_completos(
    page: Page,
    sel_tabla: str = SEL_TABLA,
    sel_siguiente: str = SEL_SIGUIENTE,
    max_paginas: int = 200,
    *,
    fecha_corte: str | None = None,
    tiempo_maximo_segundos: int | None = None,
) -> tuple[list[dict], str]:
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

    Retorna
    -------
    tuple[list[dict], str]
        La lista de expedientes junto con un código que indica por qué se
        detuvo el recorrido. Los posibles valores actuales son:

        * ``"fin_listado"``: se alcanzó el final natural del paginado.
        * ``"limite_paginas"``: se alcanzó ``max_paginas``.
        * ``"limite_fecha"``: se superó el umbral ``fecha_corte``.
        * ``"limite_tiempo"``: se superó ``tiempo_maximo_segundos``.
        * ``"sin_siguiente"``: no existe control para pasar de página.
        * ``"sin_siguiente_habilitado"``: no hay botón "Siguiente" habilitado.
        * ``"siguiente_timeout"``: el botón "Siguiente" no apareció a tiempo.
        * ``"siguiente_deshabilitado"``: el botón se deshabilitó al intentar usarlo.
        * ``"error_click"``: falló el clic en "Siguiente".
    """
    resultados: list[dict] = []

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
    tbody_locator = tabla.locator("tbody")

    paginas_recorridas = 0
    while True:
        if _excedio_tiempo():
            return resultados, "limite_tiempo"

        paginas_recorridas += 1
        print(f"Procesando página {paginas_recorridas}")

        # 1) Extraer filas visibles de ESTA página en un solo evaluate
        filas: list[list[str]] = await tabla.evaluate(
            """table => Array.from(
                   table.querySelectorAll('tbody tr'),
                   tr => Array.from(tr.cells, c => c.innerText.trim())
               )"""
        )

        # 2) Mapear a dicts usando las 5 columnas útiles
        for cols in filas:
            if len(cols) < 5:
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

            if fecha_corte_dt and ultima_dt and ultima_dt < fecha_corte_dt:
                return resultados, "limite_fecha"

            resultados.append({
                "numero":           cols[0],
                "dependencia":      cols[1],
                "caratula":         cols[2],
                "situacion":        cols[3],
                "ultima_actuacion": ultima_actuacion_norm,
            })

            if _excedio_tiempo():
                return resultados, "limite_tiempo"

        # 3) Intentar ir a la siguiente página; cortar si no hay
        if paginas_recorridas >= max_paginas:
            return resultados, "limite_paginas"

        next_btn = page.locator(sel_siguiente)
        btn_count = await next_btn.count()
        if btn_count <= 0:
            return resultados, "sin_siguiente"  # no hay control de siguiente

        boton: Locator | None = None
        for idx in range(btn_count):
            candidato = next_btn.nth(idx)
            if await _is_locator_enabled(candidato) and await candidato.is_visible():
                boton = candidato
                break

        if boton is None:
            return resultados, "sin_siguiente_habilitado"

        try:
            await boton.wait_for(state="visible", timeout=10_000)
        except TimeoutError as exc:
            print(f"Botón 'Siguiente' no visible: {exc}")
            return resultados, "siguiente_timeout"

        if not await _is_locator_enabled(boton):
            return resultados, "siguiente_deshabilitado"

        # Fingerprint antes del click para confirmar cambio real
        antes = await _tbody_fingerprint(tbody_locator)
        try:
            await boton.click()
        except (TimeoutError, Error) as exc:
            print(f"Fallo al hacer clic en 'Siguiente': {exc}")
            return resultados, "error_click"

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
            return resultados, "fin_listado"

        if _excedio_tiempo():
            return resultados, "limite_tiempo"

    return resultados, "fin_listado"
