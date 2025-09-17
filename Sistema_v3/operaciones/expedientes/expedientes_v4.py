import re
from datetime import datetime
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

# --- Config por defecto (ajustables por parámetro) ---
SEL_TABLA = "table.table-striped"
SEL_TBODY = f"{SEL_TABLA} tbody"
# Varios selectores posibles de "Siguiente" (ajustá según tu portal)
SEL_SIGUIENTE = (
    "a[aria-label='Siguiente'], button[aria-label='Siguiente'], "
    ".pagination li.next:not(.disabled) a, .pagination a:has-text('Siguiente'), "
    ".rf-ds-btn-next"
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


async def _tbody_fingerprint(page: Page, sel_tbody: str = SEL_TBODY) -> str:
    """Crea un fingerprint simple del tbody para detectar cambio de página."""
    html = await page.locator(sel_tbody).inner_html()
    return _build_fingerprint(html)

async def extraer_expedientes_completos(
    page: Page,
    sel_tabla: str = SEL_TABLA,
    sel_siguiente: str = SEL_SIGUIENTE,
    max_paginas: int = 200,
) -> list[dict]:
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
    """
    resultados: list[dict] = []

    sel_tbody = f"{sel_tabla} tbody"

    # Aseguramos presencia de tabla
    tabla = page.locator(sel_tabla)
    await tabla.wait_for(state="visible", timeout=25_000)

    paginas_recorridas = 0
    while True:
        paginas_recorridas += 1

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
            resultados.append({
                "numero":           cols[0],
                "dependencia":      cols[1],
                "caratula":         cols[2],
                "situacion":        cols[3],
                "ultima_actuacion": _norm_fecha(cols[4]),
            })

        # 3) Intentar ir a la siguiente página; cortar si no hay
        if paginas_recorridas >= max_paginas:
            break

        next_btn = page.locator(sel_siguiente)
        if await next_btn.count() == 0:
            break  # no hay control de siguiente

        # Fingerprint antes del click para confirmar cambio real
        antes = await _tbody_fingerprint(page, sel_tbody=sel_tbody)
        try:
            await next_btn.first.click()
        except Exception:
            break

        # Esperar a que cambie el tbody (evita loops)
        try:
            await page.wait_for_function(
                """(sel, prev, maxLen) => {
                    const el = document.querySelector(sel);
                    if (!el) return false;
                    const html = el.innerHTML ?? "";
                    const signature = String(html.length) + '::' + html;
                    const truncated = maxLen == null ? signature : signature.slice(0, maxLen);
                    return truncated !== prev;
                }""",
                arg=(sel_tbody, antes, _FP_MAX_LEN),
                timeout=12_000
            )
        except PlaywrightTimeoutError:
            # No cambió el contenido → estamos al final
            break

    return resultados
