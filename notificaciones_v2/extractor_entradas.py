# pjn_extractor_v2.py
# Extracción general de entradas de la lista del PJN (Notificaciones/Despachos)
# - Capa baja: iterar_entradas_pjn(...)  -> async generator (no persiste)
# - Capa alta: extraer_entradas_pjn(...) -> persiste JSON/CSV + dedupe/filtros + stats
#
# Requiere: Playwright Async (Page ya autenticada y con la lista abierta)

import os
import re
import csv
import json
import asyncio
import unicodedata
from datetime import datetime, date
from typing import Optional, Tuple, Iterable, AsyncGenerator, Dict, Any
from playwright.async_api import Page

# ================================
# Selectores del PJN (ajusta si cambian)
# ================================
SELEC_TABLA = "div.MuiTableContainer-root tr"
SELEC_EXPEDIENTE_NUMERO = "p.MuiTypography-root.MuiTypography-body1.w-full.css-11dlpbt"
SELEC_EXPEDIENTE_CARATULA = "p.MuiTypography-root.MuiTypography-body1.w-full.italic.css-4icvzy"
SELEC_CONTENEDOR_SCROLL = "#LayoutScrollingContainer"

# Señales dentro del contenedor
RE_FIN      = re.compile(r"No hay m[aá]s eventos", re.I)
RE_LOADING  = re.compile(r"Cargando m[aá]s eventos", re.I)

# Evento por aria-label del Avatar
RE_EVENTO_NOTIF = re.compile(r"evento\s+notificaci[oó]n", re.I)
RE_EVENTO_DESP  = re.compile(r"evento\s+despacho", re.I)

# ================================
# Utilidades
# ================================
def limpiar_texto(texto: str) -> str:
    return texto.replace("\n\n", " ").replace("\n", " ").strip()

def normalizar_texto(t: str) -> str:
    return unicodedata.normalize("NFKD", t.strip().lower()).encode("ascii", "ignore").decode("utf-8")

def _to_iso(fecha_str: str) -> Optional[str]:
    """Acepta 'YYYY-MM-DD' o 'DD/MM/YYYY' y devuelve 'YYYY-MM-DD'."""
    if not fecha_str:
        return None
    fecha_str = fecha_str.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(fecha_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None

def _parse_fechas_exactas(fechas: Optional[Iterable[str]]) -> set[str]:
    """Normaliza a conjunto de 'YYYY-MM-DD'."""
    out = set()
    if not fechas:
        return out
    if isinstance(fechas, (str,)):
        fechas = [fechas]
    for f in fechas:
        iso = _to_iso(f)
        if iso:
            out.add(iso)
    return out

def _parse_fecha_limite(f: Optional[str]) -> Optional[date]:
    iso = _to_iso(f) if f else None
    return datetime.strptime(iso, "%Y-%m-%d").date() if iso else None

# ================================
# Scroll helpers
# ================================
async def _near_bottom(page: Page, tol: int = 24) -> bool:
    return await page.evaluate(
        "(sel,t)=>{const el=document.querySelector(sel);if(!el) return false;"
        "return (el.scrollTop+el.clientHeight)>=(el.scrollHeight-t);}",
        SELEC_CONTENEDOR_SCROLL, tol
    )

async def _scroll_step(page: Page):
    await page.evaluate(
        "(sel)=>{const el=document.querySelector(sel); if(el){"
        " const paso=Math.max(el.clientHeight*0.9,600);"
        " el.scrollTop=Math.min(el.scrollTop+paso, el.scrollHeight-el.clientHeight);"
        "}}", SELEC_CONTENEDOR_SCROLL
    )

async def _wheel(page: Page, cont_locator):
    try:
        box = await cont_locator.bounding_box()
        if box:
            await page.mouse.move(
                box["x"] + min(20, box["width"] / 2),
                box["y"] + min(20, box["height"] / 2)
            )
            await page.mouse.wheel(0, 900)
    except Exception:
        pass

# ================================
# Detección de "N"/"D" en la fila
# ================================
async def _detectar_indicador_evento(fila) -> Tuple[Optional[str], Optional[str]]:
    """
    Devuelve (evento, tipo_evento):
        evento: 'N' / 'D' / None
        tipo_evento: 'NOTIFICACION' / 'DESPACHO' / None
    """
    # 1) aria-label (robusto)
    try:
        con_aria = await fila.query_selector_all("[aria-label]")
        for el in con_aria:
            al = await el.get_attribute("aria-label") or ""
            if RE_EVENTO_NOTIF.search(al):
                return "N", "NOTIFICACION"
            if RE_EVENTO_DESP.search(al):
                return "D", "DESPACHO"
    except Exception:
        pass
    # 2) Fallback: letra en el Avatar
    try:
        avatar_p = await fila.query_selector(".MuiAvatar-root p")
        if avatar_p:
            ch = (await avatar_p.inner_text()).strip().lower()
            if ch == "n":
                return "N", "NOTIFICACION"
            if ch == "d":
                return "D", "DESPACHO"
    except Exception:
        pass
    return None, None

# ================================
# Capa baja (streaming): iterador
# ================================
async def iterar_entradas_pjn(
    page: Page,
    incluir_tipos: tuple[str, ...] = ("N", "D"),
    fechas: Optional[Iterable[str]] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    stop_at_date: Optional[str] = None,
    stop_after_n_items: Optional[int] = None,
    delay_render: float = 0.3,
    near_bottom_tol: int = 24,
    debug: bool = False,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Recorre la lista del PJN y va rindiendo ítems uno por uno (NO persiste).
    - Aplica filtros (tipos y fechas).
    - Corta determinísticamente al fondo + heading "No hay más eventos".
    - Opcional: stop_after_n_items y stop_at_date (YYYY-MM-DD o DD/MM/YYYY).
    """
    # Normalización de filtros de fecha
    fechas_exactas = _parse_fechas_exactas(fechas)
    rango_desde = _parse_fecha_limite(fecha_desde)
    rango_hasta = _parse_fecha_limite(fecha_hasta)
    stop_at = _parse_fecha_limite(stop_at_date)

    # Verificar contenedor y primera fila
    await page.wait_for_selector(SELEC_CONTENEDOR_SCROLL, state="visible", timeout=15_000)
    await page.wait_for_selector(SELEC_TABLA, state="visible", timeout=15_000)

    cont = page.locator(SELEC_CONTENEDOR_SCROLL)
    await cont.scroll_into_view_if_needed()

    fin_loc = cont.get_by_role("heading", name=re.compile(r"No hay m[aá]s eventos", re.I))
    loading_loc = cont.get_by_text(RE_LOADING)

    # Posicionar mouse dentro del contenedor para wheel
    try:
        box = await cont.bounding_box()
        if box:
            await page.mouse.move(
                box["x"] + min(20, box["width"] / 2),
                box["y"] + min(20, box["height"] / 2)
            )
    except Exception:
        pass

    scrolled_count = 0
    yielded = 0
    loader_hits = 0

    # Para confirmar avance en listas virtualizadas
    async def _ultima_fila_texto() -> str:
        filas = await page.query_selector_all(SELEC_TABLA)
        if not filas:
            return ""
        textos = []
        for fila in filas[-2:]:
            try:
                textos.append(limpiar_texto(await fila.inner_text()))
            except Exception:
                textos.append("")
        return " || ".join(textos)

    ultima_fila_prev = await _ultima_fila_texto()
    iteracion = 0
    max_iter = 500  # safety

    while iteracion < max_iter:
        iteracion += 1
        # 1) Procesar filas visibles
        filas = await page.query_selector_all(SELEC_TABLA)
        for fila in filas:
            try:
                num_elem = await fila.query_selector(SELEC_EXPEDIENTE_NUMERO)
                car_elem = await fila.query_selector(SELEC_EXPEDIENTE_CARATULA)
                celdas = await fila.query_selector_all("td")
                if not num_elem or not car_elem or len(celdas) < 3:
                    continue

                numero = limpiar_texto(await num_elem.inner_text())
                caratula = limpiar_texto(await car_elem.inner_text())
                fecha_str = limpiar_texto(await celdas[2].inner_text())
                if not fecha_str:
                    continue

                evento, tipo_evento = await _detectar_indicador_evento(fila)
                if not evento:
                    # Si no detectamos tipo, lo omitimos (evita ruido)
                    continue

                if incluir_tipos and evento not in incluir_tipos:
                    continue

                fecha_iso = _to_iso(fecha_str)
                if not fecha_iso:
                    continue

                # Filtros de fecha
                if fechas_exactas:
                    if fecha_iso not in fechas_exactas:
                        continue
                else:
                    if rango_desde and datetime.strptime(fecha_iso, "%Y-%m-%d").date() < rango_desde:
                        continue
                    if rango_hasta and datetime.strptime(fecha_iso, "%Y-%m-%d").date() > rango_hasta:
                        continue

                item = {
                    "numero": numero,
                    "caratula": caratula,
                    "fecha": fecha_iso,
                    "evento": evento,
                    "tipo_evento": tipo_evento,
                    "leida": False,
                    "extraida_en": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }

                yield item
                yielded += 1

                if stop_after_n_items and yielded >= stop_after_n_items:
                    return

                # Criterio de corte por stop_at_date (lista usualmente descendente)
                if stop_at and datetime.strptime(fecha_iso, "%Y-%m-%d").date() < stop_at:
                    return

            except Exception:
                # Falla de parse puntual -> seguimos con la siguiente fila
                continue

        # 2) ¿Fin visible + al fondo + scrolled?
        if scrolled_count > 0 and await _near_bottom(page, near_bottom_tol) and await fin_loc.is_visible():
            return

        # 3) Avanzar tramo: scroll + wheel + sincronizar loader
        await _scroll_step(page)
        scrolled_count += 1
        await _wheel(page, cont)

        try:
            if await loading_loc.is_visible():
                loader_hits += 1
                await loading_loc.wait_for(state="hidden", timeout=10_000)
        except Exception:
            pass

        # 4) Confirmar avance (lista virtualizada)
        ultima_fila_now = await _ultima_fila_texto()
        if ultima_fila_now == ultima_fila_prev and not await _near_bottom(page, near_bottom_tol):
            for _ in range(2):
                await _wheel(page, cont)
                await asyncio.sleep(0.2)
            ultima_fila_now = await _ultima_fila_texto()
        ultima_fila_prev = ultima_fila_now

        await asyncio.sleep(delay_render)

# ================================
# Capa alta (orquestador): persistencia + dedupe
# ================================
def _base_key(e: Dict[str, Any]) -> tuple:
    return (normalizar_texto(e.get("numero","")), e.get("fecha",""), normalizar_texto(e.get("caratula","")))

def _event_key(e: Dict[str, Any]) -> tuple:
    return _base_key(e) + (e.get("evento","") or "",)

async def extraer_entradas_pjn(
    page: Page,
    destino: Optional[str] = None,
    duplicados: bool = False,
    incluir_tipos: tuple[str, ...] = ("N", "D"),
    fechas: Optional[Iterable[str]] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    stop_at_date: Optional[str] = None,
    stop_after_n_items: Optional[int] = None,
    return_items: bool = False,
    error_policy: str = "collect",   # "raise" | "collect" | "log"
    delay_render: float = 0.3,
    near_bottom_tol: int = 24,
    debug: bool = False,
) -> Dict[str, Any]:
    """
    Usa el iterador, aplica dedupe y persiste JSON/CSV.
    Devuelve: {stats, meta, warnings, errors, items?}
    """
    started_at = datetime.now()

    base_dir = destino if destino else os.path.join(os.getcwd(), "datos_extraidos", "monitoreo")
    os.makedirs(base_dir, exist_ok=True)
    HISTORIAL_JSON = os.path.join(base_dir, "historial_notificaciones.json")
    HISTORIAL_CSV  = os.path.join(base_dir, "historial_notificaciones.csv")

    # Cargar historial
    historial: list[Dict[str, Any]] = []
    if os.path.exists(HISTORIAL_JSON):
        try:
            with open(HISTORIAL_JSON, "r", encoding="utf-8") as f:
                historial = json.load(f)
        except Exception as e:
            if error_policy == "raise":
                raise
            elif error_policy == "collect":
                # arrancar vacío pero registrar el error
                historial = []
            else:
                print(f"⚠️ Error leyendo JSON: {e}")

    claves_hist_base  = set(_base_key(e) for e in historial if e.get("numero") and e.get("fecha") and e.get("caratula"))
    claves_hist_event = set(_event_key(e) for e in historial if e.get("numero") and e.get("fecha") and e.get("caratula"))

    warnings: list[str] = []
    errors: list[str] = []
    nuevas: list[Dict[str, Any]] = []
    vistos_run_event: set[tuple] = set()

    total_seen = 0
    total_saved = 0
    filtered_by_type = 0
    filtered_by_date = 0
    dedup_skipped = 0

    # Consumir el iterador
    try:
        async for item in iterar_entradas_pjn(
            page=page,
            incluir_tipos=incluir_tipos,
            fechas=fechas,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            stop_at_date=stop_at_date,
            stop_after_n_items=stop_after_n_items,
            delay_render=delay_render,
            near_bottom_tol=near_bottom_tol,
            debug=debug,
        ):
            total_seen += 1

            # (Los filtros ya se aplicaron en el iterador, mantenemos contadores por si en el futuro
            #   se mueven aquí; ahora quedan en cero.)
            # filtered_by_type / filtered_by_date se usan si movemos parte del filtrado aquí.

            if duplicados:
                nuevas.append(item)
                total_saved += 1
                continue

            # DEDUPE (por evento)
            base_k = _base_key(item)
            event_k = _event_key(item)

            # ¿ya existe exactamente este evento?
            if event_k in claves_hist_event or event_k in vistos_run_event:
                dedup_skipped += 1
                continue

            # ¿existe la base en historial pero sin 'evento'? => enriquecer
            if base_k in claves_hist_base and item.get("evento"):
                for reg in historial:
                    if _base_key(reg) == base_k and not reg.get("evento"):
                        reg["evento"] = item["evento"]
                        reg["tipo_evento"] = item.get("tipo_evento")
                claves_hist_event.add(event_k)
                # no contamos como "nueva" en disco porque enriquecimos existente
                continue

            # nuevo
            nuevas.append(item)
            vistos_run_event.add(event_k)
            total_saved += 1

    except Exception as e:
        msg = f"❌ Error al iterar: {e}"
        if error_policy == "raise":
            raise
        elif error_policy == "collect":
            errors.append(msg)
        else:
            print(msg)

    # Persistencia
    if duplicados:
        historial = nuevas + historial  # prepend todo
    else:
        if nuevas:
            historial = nuevas + historial

    # Guardar JSON
    try:
        with open(HISTORIAL_JSON, "w", encoding="utf-8") as f:
            json.dump(historial, f, indent=4, ensure_ascii=False)
    except Exception as e:
        msg = f"❌ Error guardando JSON: {e}"
        if error_policy == "raise":
            raise
        elif error_policy == "collect":
            errors.append(msg)
        else:
            print(msg)

    # Regenerar CSV completo
    try:
        with open(HISTORIAL_CSV, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Fecha", "Número", "Carátula", "Evento", "TipoEvento", "Leída", "Extraída En"])
            for e in historial:
                w.writerow([
                    e.get("fecha",""),
                    e.get("numero",""),
                    e.get("caratula",""),
                    e.get("evento","") or "",
                    e.get("tipo_evento","") or "",
                    "Sí" if e.get("leida", False) else "No",
                    e.get("extraida_en",""),
                ])
    except Exception as e:
        msg = f"❌ Error guardando CSV: {e}"
        if error_policy == "raise":
            raise
        elif error_policy == "collect":
            errors.append(msg)
        else:
            print(msg)

    ended_at = datetime.now()
    result: Dict[str, Any] = {
        "stats": {
            "total_vistos": total_seen,
            "total_guardados": total_saved,
            "dedup_omitidos": dedup_skipped,
            "filtrados_tipo": filtered_by_type,
            "filtrados_fecha": filtered_by_date,
            "nuevas_en_esta_corrida": len(nuevas),
        },
        "meta": {
            "started_at": started_at.strftime("%Y-%m-%d %H:%M:%S"),
            "ended_at": ended_at.strftime("%Y-%m-%d %H:%M:%S"),
            "destino": base_dir,
            "params": {
                "duplicados": duplicados,
                "incluir_tipos": incluir_tipos,
                "fechas": list(_parse_fechas_exactas(fechas)) if fechas else None,
                "fecha_desde": _to_iso(fecha_desde) if fecha_desde else None,
                "fecha_hasta": _to_iso(fecha_hasta) if fecha_hasta else None,
                "stop_at_date": _to_iso(stop_at_date) if stop_at_date else None,
                "stop_after_n_items": stop_after_n_items,
                "near_bottom_tol": near_bottom_tol,
            },
            "schema_version": "2.0",
        },
        "warnings": warnings,
        "errors": errors,
    }

    if return_items:
        result["items"] = nuevas

    return result

# ================================
# Wrapper de compatibilidad
# ================================
async def actualizar_notificaciones_nuevas(page: Page, destino: Optional[str] = None) -> int:
    """
    Compatibilidad con tu flujo actual:
    - Dedupe activado
    - Captura N y D
    - Sin filtros de fechas
    Retorna: cantidad de nuevas agregadas en esta corrida (no duplicadas)
    """
    res = await extraer_entradas_pjn(
        page=page,
        destino=destino,
        duplicados=False,
        incluir_tipos=("N","D"),
        fechas=None,
        fecha_desde=None,
        fecha_hasta=None,
        stop_at_date=None,
        stop_after_n_items=None,
        return_items=False,
        error_policy="collect",
        delay_render=0.3,
        near_bottom_tol=24,
        debug=False,
    )
    return int(res["stats"]["nuevas_en_esta_corrida"])
