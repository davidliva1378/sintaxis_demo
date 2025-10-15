# extractor_entradas.py
# Función única y simple para extraer entradas del PJN.
# - Scroll robusto + loader + corte determinístico por heading "No hay más eventos"
# - Filtros por tipo (N/D) y fecha(s)
# - Duplicados: True => guarda todo | False => dedup + enriquece historial
# - Persiste JSON/CSV (compatibilidad con versiones previas)

import os
import re
import csv
import json
from datetime import datetime, date
from typing import Optional, Iterable, Tuple, Dict, Any, List
from playwright.async_api import Page

from .base import limpiar_texto, normalizar_texto
from ..models import Entrada
from ..parsers.entradas_parser import parse_entrada
from ..selectores import SEL_ENTRADAS
from ..utils.logging import get_logger

logger = get_logger(__name__)

RE_FIN     = re.compile(r"No hay m[aá]s eventos", re.I)
RE_LOADING = re.compile(r"Cargando m[aá]s eventos", re.I)

# Evento por aria-label del Avatar
RE_EVENTO_NOTIF = re.compile(r"evento\s+notificaci[oó]n", re.I)
RE_EVENTO_DESP  = re.compile(r"evento\s+despacho", re.I)

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

async def _near_bottom(page: Page, tol: int = 24) -> bool:
    # Pasamos ambos parámetros en un único objeto "args"
    return await page.evaluate(
        "(args) => {"
        "  const el = document.querySelector(args.sel);"
        "  if (!el) return false;"
        "  return (el.scrollTop + el.clientHeight) >= (el.scrollHeight - args.tol);"
        "}",
        {"sel": SEL_ENTRADAS.CONTENEDOR_SCROLL, "tol": tol},
    )


async def _scroll_step(page: Page):
    await page.evaluate(
        "(sel)=>{const el=document.querySelector(sel); if(el){"
        " const paso=Math.max(el.clientHeight*0.9,600);"
        " el.scrollTop=Math.min(el.scrollTop+paso, el.scrollHeight-el.clientHeight);"
        "}}", SEL_ENTRADAS.CONTENEDOR_SCROLL
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

async def _detectar_indicador_evento(fila) -> Tuple[Optional[str], Optional[str]]:
    """Devuelve (evento, tipo_evento): 'N'/'D' y 'NOTIFICACION'/'DESPACHO' (o None/None)."""
    # 1) aria-label (robusto)
    try:
        con_aria = await fila.query_selector_all(SEL_ENTRADAS.ELEMENTOS_CON_ARIA)
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
        avatar_p = await fila.query_selector(SEL_ENTRADAS.AVATAR_LETRA)
        if avatar_p:
            ch = (await avatar_p.inner_text()).strip().lower()
            if ch == "n":
                return "N", "NOTIFICACION"
            if ch == "d":
                return "D", "DESPACHO"
    except Exception:
        pass
    return None, None

def _base_key(e: Dict[str, Any]) -> tuple:
    return (normalizar_texto(e.get("numero","")), e.get("fecha",""), normalizar_texto(e.get("caratula","")))

def _event_key(e: Dict[str, Any]) -> tuple:
    return _base_key(e) + (e.get("evento","") or "",)

# ===== FUNCIÓN ÚNICA =====
async def extraer_entradas_pjn(
    page: Page,
    destino: Optional[str] = None,
    duplicados: bool = False,
    incluir_tipos: tuple[str, ...] = ("N", "D"),
    fechas: Optional[Iterable[str]] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    coleccion_modelos: Optional[List[Entrada]] = None,
) -> int:
    """
    Recorre la lista del PJN y persiste JSON/CSV.
    - page: Playwright Page ya logueada y con la lista abierta.
    - destino: carpeta base (default ./datos_extraidos/monitoreo).
    - duplicados: False => dedup por (numero, fecha, caratula, evento) + enriquece históricos.
                  True  => guarda todas las apariciones.
    - incluir_tipos: ('N',), ('D',) o ('N','D') (default).
    - fechas: fecha(s) exactas (YYYY-MM-DD o DD/MM/YYYY). Si se indica, se ignoran los rangos.
    - fecha_desde / fecha_hasta: rango inclusivo (mismos formatos).

    Retorna: cantidad de registros NUEVOS agregados en esta corrida
             (si duplicados=True, cantidad agregada tal cual).
    """
    logger.info("🔍 Extrayendo entradas del PJN...")

    # Normalizar filtros de fecha
    fechas_exactas = _parse_fechas_exactas(fechas)
    rango_desde = _parse_fecha_limite(fecha_desde)
    rango_hasta = _parse_fecha_limite(fecha_hasta)

    # Destino y archivos
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
            logger.warning("⚠️ Error leyendo JSON existente: %s. Se continúa con historial vacío.", e)
            historial = []

    claves_hist_base  = set(_base_key(e) for e in historial if e.get("numero") and e.get("fecha") and e.get("caratula"))
    claves_hist_event = set(_event_key(e) for e in historial if e.get("numero") and e.get("fecha") and e.get("caratula"))

    # Asegurar contenedor y filas
    try:
        await page.wait_for_selector(SEL_ENTRADAS.CONTENEDOR_SCROLL, state="visible", timeout=15_000)
        await page.wait_for_selector(SEL_ENTRADAS.TABLA, state="visible", timeout=15_000)
    except Exception:
        logger.error("❌ Contenedor o filas no visibles. Abortando.")
        return 0

    cont = page.locator(SEL_ENTRADAS.CONTENEDOR_SCROLL)
    await cont.scroll_into_view_if_needed()

    fin_loc = cont.get_by_role("heading", name=re.compile(r"No hay m[aá]s eventos", re.I))
    loading_loc = cont.get_by_text(RE_LOADING)

    # Posicionar mouse para wheel
    try:
        box = await cont.bounding_box()
        if box:
            await page.mouse.move(
                box["x"] + min(20, box["width"] / 2),
                box["y"] + min(20, box["height"] / 2)
            )
    except Exception:
        pass

    nuevas_run: list[Dict[str, Any]] = []
    vistos_run_event: set[tuple] = set()
    scrolled_count = 0
    iteracion = 0
    max_iter = 500  # safety

    # Contadores de diagnóstico
    filas_procesadas = 0
    filas_sin_numero = 0
    filas_sin_caratula = 0
    filas_sin_celdas = 0
    filas_sin_fecha = 0
    filas_sin_evento = 0
    filas_filtradas_tipo = 0
    filas_filtradas_fecha = 0
    filas_duplicadas = 0

    # Para confirmar avance (listas virtualizadas)
    async def _ultima_fila_texto() -> str:
        filas = await page.query_selector_all(SEL_ENTRADAS.TABLA)
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

    while iteracion < max_iter:
        iteracion += 1

        # 1) Procesar filas visibles
        filas = await page.query_selector_all(SEL_ENTRADAS.TABLA)
        for fila in filas:
            try:
                filas_procesadas += 1

                num_elem = await fila.query_selector(SEL_ENTRADAS.EXPEDIENTE_NUMERO)
                car_elem = await fila.query_selector(SEL_ENTRADAS.EXPEDIENTE_CARATULA)
                celdas   = await fila.query_selector_all(SEL_ENTRADAS.CELDAS_FILA)

                if not num_elem:
                    filas_sin_numero += 1
                    continue
                if not car_elem:
                    filas_sin_caratula += 1
                    continue
                if len(celdas) < 3:
                    filas_sin_celdas += 1
                    continue

                numero   = limpiar_texto(await num_elem.inner_text())
                caratula = limpiar_texto(await car_elem.inner_text())

                # Extraer fecha desde aria-label (formato: "DD/MM/YYYY HH:MM")
                fecha_s = ""
                try:
                    fecha_elem = await celdas[2].query_selector(SEL_ENTRADAS.FECHA_ELEMENTO)
                    if fecha_elem:
                        fecha_aria = await fecha_elem.get_attribute("aria-label")
                        if fecha_aria:
                            # Extraer solo la fecha (primera parte antes del espacio)
                            fecha_s = fecha_aria.split()[0] if " " in fecha_aria else fecha_aria
                except Exception:
                    pass

                # Fallback: usar inner_text si no se encontró aria-label
                if not fecha_s:
                    fecha_s = limpiar_texto(await celdas[2].inner_text())

                fecha_iso = _to_iso(fecha_s)
                if not fecha_iso:
                    filas_sin_fecha += 1
                    logger.debug("Fila sin fecha válida. Texto extraído: '%s'", fecha_s)
                    continue

                evento, tipo_evento = await _detectar_indicador_evento(fila)
                if not evento:
                    filas_sin_evento += 1
                    logger.debug("Fila sin indicador de evento. Número: %s", numero[:20])
                    continue
                if incluir_tipos and evento not in incluir_tipos:
                    filas_filtradas_tipo += 1
                    continue

                # Filtros de fecha
                if fechas_exactas:
                    if fecha_iso not in fechas_exactas:
                        filas_filtradas_fecha += 1
                        continue
                else:
                    f = datetime.strptime(fecha_iso, "%Y-%m-%d").date()
                    if rango_desde and f < rango_desde:
                        filas_filtradas_fecha += 1
                        continue
                    if rango_hasta and f > rango_hasta:
                        filas_filtradas_fecha += 1
                        continue

                entrada_modelo = parse_entrada(
                    numero=numero,
                    caratula=caratula,
                    fecha=fecha_iso,
                    evento=evento,
                    tipo_evento=tipo_evento,
                    leida=False,
                    extraida_en=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                )
                item = entrada_modelo.to_dict()
                if coleccion_modelos is not None:
                    coleccion_modelos.append(entrada_modelo)

                if duplicados:
                    nuevas_run.append(item)
                    continue

                # sin duplicados: dedup por evento
                base_k  = _base_key(item)
                event_k = _event_key(item)

                # ya existe exactamente este evento
                if event_k in claves_hist_event or event_k in vistos_run_event:
                    continue

                # existe la base pero sin 'evento' => enriquecer historial
                if base_k in claves_hist_base and item.get("evento"):
                    for reg in historial:
                        if _base_key(reg) == base_k and not reg.get("evento"):
                            reg["evento"] = item["evento"]
                            reg["tipo_evento"] = item.get("tipo_evento")
                    claves_hist_event.add(event_k)
                    continue

                # nuevo real
                nuevas_run.append(item)
                vistos_run_event.add(event_k)

            except Exception:
                # error puntual de parse: seguir
                continue

        # 2) ¿fin al fondo con heading visible?
        if scrolled_count > 0 and await _near_bottom(page) and await fin_loc.is_visible():
            break

        # 3) Avanzar tramo: scroll + wheel + sync loader
        await _scroll_step(page)
        scrolled_count += 1
        await _wheel(page, cont)

        try:
            if await loading_loc.is_visible():
                await loading_loc.wait_for(state="hidden", timeout=10_000)
        except Exception:
            pass

        # 4) Confirmar avance
        ultima_fila_now = await _ultima_fila_texto()
        if ultima_fila_now == ultima_fila_prev and not await _near_bottom(page):
            for _ in range(2):
                await _wheel(page, cont)
            ultima_fila_now = await _ultima_fila_texto()
        ultima_fila_prev = ultima_fila_now

    # ===== Persistencia =====
    nuevas_count = 0
    if duplicados:
        historial = nuevas_run + historial
        nuevas_count = len(nuevas_run)
    else:
        if nuevas_run:
            historial = nuevas_run + historial
            nuevas_count = len(nuevas_run)

    # Guardar JSON
    try:
        with open(HISTORIAL_JSON, "w", encoding="utf-8") as f:
            json.dump(historial, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error("❌ Error guardando JSON: %s", e)

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
        logger.error("❌ Error guardando CSV: %s", e)

    # Resumen de diagnóstico
    logger.info("✅ Listo. Nuevas agregadas en esta corrida: %d", nuevas_count)
    logger.info("   Carpeta: %s", os.path.abspath(base_dir))
    logger.info("\n📊 Resumen de procesamiento:")
    logger.info("   - Filas procesadas: %d", filas_procesadas)
    if filas_sin_numero > 0:
        logger.warning("   - Filas sin número: %d", filas_sin_numero)
    if filas_sin_caratula > 0:
        logger.warning("   - Filas sin carátula: %d", filas_sin_caratula)
    if filas_sin_celdas > 0:
        logger.warning("   - Filas sin suficientes celdas: %d", filas_sin_celdas)
    if filas_sin_fecha > 0:
        logger.warning("   - Filas sin fecha válida: %d", filas_sin_fecha)
    if filas_sin_evento > 0:
        logger.warning("   - Filas sin indicador de evento: %d", filas_sin_evento)
    if filas_filtradas_tipo > 0:
        logger.info("   - Filtradas por tipo: %d", filas_filtradas_tipo)
    if filas_filtradas_fecha > 0:
        logger.info("   - Filtradas por fecha: %d", filas_filtradas_fecha)

    return nuevas_count


async def extraer_entradas_pjn_modelos(
    page: Page,
    destino: Optional[str] = None,
    duplicados: bool = False,
    incluir_tipos: tuple[str, ...] = ("N", "D"),
    fechas: Optional[Iterable[str]] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
) -> tuple[int, List[Entrada]]:
    """Devuelve también los modelos :class:`Entrada` generados."""

    modelos: List[Entrada] = []
    cantidad = await extraer_entradas_pjn(
        page,
        destino=destino,
        duplicados=duplicados,
        incluir_tipos=incluir_tipos,
        fechas=fechas,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        coleccion_modelos=modelos,
    )
    return cantidad, modelos
