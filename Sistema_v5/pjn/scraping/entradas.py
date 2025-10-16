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


# ===== Funciones auxiliares para extraer_entradas_datos =====

def _preparar_filtros_y_historial(
    fechas: Optional[Iterable[str]],
    fecha_desde: Optional[str],
    fecha_hasta: Optional[str],
    historial_existente: Optional[List[Entrada]],
) -> tuple[set[str], Optional[date], Optional[date], list[Dict[str, Any]], set[tuple], set[tuple]]:
    """Prepara filtros de fecha y estructuras de deduplicación basadas en historial.

    Args:
        fechas: Fechas exactas a filtrar (YYYY-MM-DD o DD/MM/YYYY).
        fecha_desde: Fecha inicio de rango (formato flexible).
        fecha_hasta: Fecha fin de rango (formato flexible).
        historial_existente: Lista de entradas previas para deduplicación.

    Returns:
        tuple[fechas_exactas, rango_desde, rango_hasta, historial_dicts, claves_hist_base, claves_hist_event]:
            - fechas_exactas: Set de fechas ISO normalizadas
            - rango_desde: Fecha inicio como date object (o None)
            - rango_hasta: Fecha fin como date object (o None)
            - historial_dicts: Lista de diccionarios del historial
            - claves_hist_base: Set de claves base del historial
            - claves_hist_event: Set de claves con evento del historial
    """
    # Normalizar filtros de fecha
    fechas_exactas = _parse_fechas_exactas(fechas)
    rango_desde = _parse_fecha_limite(fecha_desde)
    rango_hasta = _parse_fecha_limite(fecha_hasta)

    # Preparar historial para deduplicación
    historial_dicts: list[Dict[str, Any]] = []
    if historial_existente:
        historial_dicts = [e.to_dict() for e in historial_existente]

    claves_hist_base = set(
        _base_key(e) for e in historial_dicts
        if e.get("numero") and e.get("fecha") and e.get("caratula")
    )
    claves_hist_event = set(
        _event_key(e) for e in historial_dicts
        if e.get("numero") and e.get("fecha") and e.get("caratula")
    )

    return fechas_exactas, rango_desde, rango_hasta, historial_dicts, claves_hist_base, claves_hist_event


async def _configurar_pagina_scroll(page: Page) -> tuple:
    """Configura la página para scroll infinito y retorna locators necesarios.

    Args:
        page: Página de Playwright.

    Returns:
        tuple[cont, fin_loc, loading_loc]: Locators para contenedor, fin de lista y loading.

    Raises:
        ExtraccionError: Si el contenedor o tabla no son visibles.
    """
    from ..exceptions import ExtraccionError

    try:
        await page.wait_for_selector(SEL_ENTRADAS.CONTENEDOR_SCROLL, state="visible", timeout=15_000)
        await page.wait_for_selector(SEL_ENTRADAS.TABLA, state="visible", timeout=15_000)
    except Exception as exc:
        raise ExtraccionError("Contenedor o filas no visibles") from exc

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

    return cont, fin_loc, loading_loc


class ContadoresDiagnostico:
    """Clase para mantener contadores de diagnóstico durante la extracción."""

    def __init__(self):
        self.filas_procesadas = 0
        self.filas_sin_numero = 0
        self.filas_sin_caratula = 0
        self.filas_sin_celdas = 0
        self.filas_sin_fecha = 0
        self.filas_sin_evento = 0
        self.filas_filtradas_tipo = 0
        self.filas_filtradas_fecha = 0


async def _procesar_fila_entrada(
    fila,
    incluir_tipos: tuple[str, ...],
    fechas_exactas: set[str],
    rango_desde: Optional[date],
    rango_hasta: Optional[date],
    contadores: ContadoresDiagnostico,
) -> Optional[Entrada]:
    """Procesa una fila y retorna un modelo Entrada si pasa todos los filtros.

    Args:
        fila: ElementHandle de Playwright de la fila.
        incluir_tipos: Tupla de tipos de evento a incluir ('N', 'D').
        fechas_exactas: Set de fechas exactas permitidas (ISO).
        rango_desde: Fecha mínima del rango (o None).
        rango_hasta: Fecha máxima del rango (o None).
        contadores: Objeto con contadores de diagnóstico.

    Returns:
        Entrada: Modelo de entrada si pasa filtros, None si debe omitirse.
    """
    contadores.filas_procesadas += 1

    num_elem = await fila.query_selector(SEL_ENTRADAS.EXPEDIENTE_NUMERO)
    car_elem = await fila.query_selector(SEL_ENTRADAS.EXPEDIENTE_CARATULA)
    celdas = await fila.query_selector_all(SEL_ENTRADAS.CELDAS_FILA)

    if not num_elem:
        contadores.filas_sin_numero += 1
        return None
    if not car_elem:
        contadores.filas_sin_caratula += 1
        return None
    if len(celdas) < 3:
        contadores.filas_sin_celdas += 1
        return None

    numero = limpiar_texto(await num_elem.inner_text())
    caratula = limpiar_texto(await car_elem.inner_text())

    # Extraer fecha
    fecha_s = ""
    try:
        fecha_elem = await celdas[2].query_selector(SEL_ENTRADAS.FECHA_ELEMENTO)
        if fecha_elem:
            fecha_aria = await fecha_elem.get_attribute("aria-label")
            if fecha_aria:
                fecha_s = fecha_aria.split()[0] if " " in fecha_aria else fecha_aria
    except Exception:
        pass

    if not fecha_s:
        fecha_s = limpiar_texto(await celdas[2].inner_text())

    fecha_iso = _to_iso(fecha_s)
    if not fecha_iso:
        contadores.filas_sin_fecha += 1
        return None

    # Detectar tipo de evento
    evento, tipo_evento = await _detectar_indicador_evento(fila)
    if not evento:
        contadores.filas_sin_evento += 1
        return None
    if incluir_tipos and evento not in incluir_tipos:
        contadores.filas_filtradas_tipo += 1
        return None

    # Filtros de fecha
    if fechas_exactas:
        if fecha_iso not in fechas_exactas:
            contadores.filas_filtradas_fecha += 1
            return None
    else:
        f = datetime.strptime(fecha_iso, "%Y-%m-%d").date()
        if rango_desde and f < rango_desde:
            contadores.filas_filtradas_fecha += 1
            return None
        if rango_hasta and f > rango_hasta:
            contadores.filas_filtradas_fecha += 1
            return None

    # Crear modelo
    entrada_modelo = parse_entrada(
        numero=numero,
        caratula=caratula,
        fecha=fecha_iso,
        evento=evento,
        tipo_evento=tipo_evento,
        leida=False,
        extraida_en=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )

    # Logging de entrada capturada
    logger.debug(f"  -> Capturada: {fecha_iso} | {numero} | {tipo_evento}")

    return entrada_modelo


def _aplicar_deduplicacion(
    entrada_modelo: Entrada,
    historial_dicts: list[Dict[str, Any]],
    claves_hist_base: set[tuple],
    claves_hist_event: set[tuple],
    vistos_run_event: set[tuple],
) -> bool:
    """Aplica lógica de deduplicación y enriquecimiento de historial.

    Args:
        entrada_modelo: Modelo de entrada a verificar.
        historial_dicts: Lista de diccionarios del historial.
        claves_hist_base: Set de claves base del historial.
        claves_hist_event: Set de claves con evento del historial (se modifica in-place).
        vistos_run_event: Set de claves vistas en esta ejecución (se modifica in-place).

    Returns:
        bool: True si la entrada debe agregarse, False si es duplicada.
    """
    item_dict = entrada_modelo.to_dict()
    base_k = _base_key(item_dict)
    event_k = _event_key(item_dict)

    # Ya existe con evento
    if event_k in claves_hist_event or event_k in vistos_run_event:
        return False

    # Existe base sin evento → enriquecer
    if base_k in claves_hist_base and item_dict.get("evento"):
        for reg_dict in historial_dicts:
            if _base_key(reg_dict) == base_k and not reg_dict.get("evento"):
                reg_dict["evento"] = item_dict["evento"]
                reg_dict["tipo_evento"] = item_dict.get("tipo_evento")
        claves_hist_event.add(event_k)
        return False

    # Nueva entrada
    vistos_run_event.add(event_k)
    return True


async def _ejecutar_scroll_y_esperar(
    page: Page,
    cont_locator,
    loading_loc,
    ultima_fila_prev: str,
    _ultima_fila_texto_fn,
) -> tuple[str, bool]:
    """Ejecuta scroll, espera carga y verifica si hay nuevas filas.

    Args:
        page: Página de Playwright.
        cont_locator: Locator del contenedor.
        loading_loc: Locator del indicador de carga.
        ultima_fila_prev: Texto de la última fila antes del scroll.
        _ultima_fila_texto_fn: Función async para obtener texto de última fila.

    Returns:
        tuple[nueva_ultima_fila, debe_continuar]: Texto de última fila y si debe continuar scrolling.
    """
    # Avanzar
    await _scroll_step(page)
    await _wheel(page, cont_locator)

    # Esperar a que termine de cargar
    try:
        if await loading_loc.is_visible():
            await loading_loc.wait_for(state="hidden", timeout=10_000)
    except Exception:
        pass

    # Verificar si cambió el contenido
    ultima_fila_now = await _ultima_fila_texto_fn()
    if ultima_fila_now == ultima_fila_prev and not await _near_bottom(page):
        # Intentar scroll adicional
        for _ in range(2):
            await _wheel(page, cont_locator)
        ultima_fila_now = await _ultima_fila_texto_fn()

    return ultima_fila_now, True


def _loguear_diagnostico(nuevas_entradas: List[Entrada], contadores: ContadoresDiagnostico) -> None:
    """Loguea resumen de diagnóstico de la extracción.

    Args:
        nuevas_entradas: Lista de entradas extraídas.
        contadores: Objeto con contadores de diagnóstico.
    """
    logger.info("✅ Extracción completada. Nuevas entradas: %d", len(nuevas_entradas))
    logger.info("📊 Resumen de procesamiento:")
    logger.info("   - Filas procesadas: %d", contadores.filas_procesadas)
    if contadores.filas_sin_numero > 0:
        logger.warning("   - Filas sin número: %d", contadores.filas_sin_numero)
    if contadores.filas_sin_caratula > 0:
        logger.warning("   - Filas sin carátula: %d", contadores.filas_sin_caratula)
    if contadores.filas_sin_celdas > 0:
        logger.warning("   - Filas sin suficientes celdas: %d", contadores.filas_sin_celdas)
    if contadores.filas_sin_fecha > 0:
        logger.warning("   - Filas sin fecha válida: %d", contadores.filas_sin_fecha)
    if contadores.filas_sin_evento > 0:
        logger.warning("   - Filas sin indicador de evento: %d", contadores.filas_sin_evento)
    if contadores.filas_filtradas_tipo > 0:
        logger.info("   - Filtradas por tipo: %d", contadores.filas_filtradas_tipo)
    if contadores.filas_filtradas_fecha > 0:
        logger.info("   - Filtradas por fecha: %d", contadores.filas_filtradas_fecha)


# ===== FUNCIÓN PURA (sin I/O) =====
async def extraer_entradas_datos(
    page: Page,
    duplicados: bool = False,
    incluir_tipos: tuple[str, ...] = ("N", "D"),
    fechas: Optional[Iterable[str]] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    historial_existente: Optional[List[Entrada]] = None,
) -> List[Entrada]:
    """Extrae entradas del PJN y retorna lista de modelos (NO guarda archivos).

    Esta es la versión "pura" que NO persiste JSON/CSV. Útil para:
    - Procesamiento en memoria
    - Integración con otras rutinas
    - Testing

    Args:
        page: Playwright Page ya logueada y con la lista abierta.
        duplicados: False => dedup por (numero, fecha, caratula, evento).
                    True => retorna todas las apariciones.
        incluir_tipos: ('N',), ('D',) o ('N','D') (default).
        fechas: fecha(s) exactas (YYYY-MM-DD o DD/MM/YYYY).
        fecha_desde / fecha_hasta: rango inclusivo (mismos formatos).
        historial_existente: Lista de entradas previas para deduplicación.

    Returns:
        List[Entrada]: Lista de modelos de Entrada extraídos.

    Raises:
        ExtraccionError: Si no se puede acceder al contenedor de entradas.
    """
    logger.info("🔍 Extrayendo entradas del PJN...")

    # Preparar filtros y estructuras de deduplicación
    (
        fechas_exactas,
        rango_desde,
        rango_hasta,
        historial_dicts,
        claves_hist_base,
        claves_hist_event,
    ) = _preparar_filtros_y_historial(fechas, fecha_desde, fecha_hasta, historial_existente)

    # Configurar página para scroll infinito
    cont, fin_loc, loading_loc = await _configurar_pagina_scroll(page)

    # Inicializar variables de control
    nuevas_entradas: List[Entrada] = []
    vistos_run_event: set[tuple] = set()
    scrolled_count = 0
    iteracion = 0
    max_iter = 500
    contadores = ContadoresDiagnostico()

    # Función auxiliar para obtener texto de última fila
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

    # Bucle principal de extracción
    filas_consecutivas_antiguas = 0
    while iteracion < max_iter:
        iteracion += 1

        filas = await page.query_selector_all(SEL_ENTRADAS.TABLA)
        nuevas_en_esta_iter = 0

        for fila in filas:
            try:
                # Procesar fila y obtener entrada si pasa filtros
                entrada_modelo = await _procesar_fila_entrada(
                    fila,
                    incluir_tipos,
                    fechas_exactas,
                    rango_desde,
                    rango_hasta,
                    contadores,
                )

                if not entrada_modelo:
                    # Verificar si fue filtrada por ser más antigua que fecha_desde (para corte temprano)
                    if rango_desde:
                        try:
                            # Intentar extraer fecha de la fila para verificar si estamos fuera de rango
                            celdas = await fila.query_selector_all(SEL_ENTRADAS.CELDAS_FILA)
                            if len(celdas) >= 3:
                                fecha_elem = await celdas[2].query_selector(SEL_ENTRADAS.FECHA_ELEMENTO)
                                if fecha_elem:
                                    fecha_aria = await fecha_elem.get_attribute("aria-label")
                                    if fecha_aria:
                                        fecha_s = fecha_aria.split()[0] if " " in fecha_aria else fecha_aria
                                        fecha_iso = _to_iso(fecha_s)
                                        if fecha_iso:
                                            f = datetime.strptime(fecha_iso, "%Y-%m-%d").date()
                                            if f < rango_desde:
                                                filas_consecutivas_antiguas += 1
                                                logger.debug(f"  -> Filtrada (antigua): {fecha_iso} (consecutivas: {filas_consecutivas_antiguas})")
                                                # Corte temprano: si encontramos 10 filas consecutivas más antiguas que fecha_desde
                                                if filas_consecutivas_antiguas >= 10:
                                                    logger.info(f"Corte temprano: 10 filas consecutivas más antiguas que {rango_desde}")
                                                    break
                        except Exception:
                            pass
                    continue

                # Resetear contador si encontramos una entrada válida
                filas_consecutivas_antiguas = 0

                # Si se permiten duplicados, agregar directamente
                if duplicados:
                    nuevas_entradas.append(entrada_modelo)
                    nuevas_en_esta_iter += 1
                    continue

                # Aplicar deduplicación
                if _aplicar_deduplicacion(
                    entrada_modelo,
                    historial_dicts,
                    claves_hist_base,
                    claves_hist_event,
                    vistos_run_event,
                ):
                    nuevas_entradas.append(entrada_modelo)
                    nuevas_en_esta_iter += 1

            except Exception:
                continue

        # Si se activó el corte temprano, salir del while
        if rango_desde and filas_consecutivas_antiguas >= 10:
            break

        # Detección de fin
        if scrolled_count > 0 and await _near_bottom(page) and await fin_loc.is_visible():
            break

        # Ejecutar scroll y esperar carga
        ultima_fila_prev, _ = await _ejecutar_scroll_y_esperar(
            page,
            cont,
            loading_loc,
            ultima_fila_prev,
            _ultima_fila_texto,
        )
        scrolled_count += 1

    # Logging de diagnóstico
    _loguear_diagnostico(nuevas_entradas, contadores)

    return nuevas_entradas


# ===== FUNCIÓN CON PERSISTENCIA (compatibilidad) =====
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
    """Extrae entradas del PJN y persiste JSON/CSV (versión con persistencia).

    NOTA: Esta función mantiene compatibilidad con código existente.
    Para uso desde otras rutinas, considere usar extraer_entradas_datos()
    que no guarda archivos automáticamente.

    Args:
        page: Playwright Page ya logueada y con la lista abierta.
        destino: carpeta base (default ./datos_extraidos/monitoreo).
        duplicados: False => dedup por (numero, fecha, caratula, evento).
                    True => guarda todas las apariciones.
        incluir_tipos: ('N',), ('D',) o ('N','D') (default).
        fechas: fecha(s) exactas (YYYY-MM-DD o DD/MM/YYYY).
        fecha_desde / fecha_hasta: rango inclusivo (mismos formatos).
        coleccion_modelos: Lista opcional para recibir modelos extraídos.

    Returns:
        int: cantidad de registros NUEVOS agregados en esta corrida.

    Deprecated:
        Esta función será deprecada en favor de extraer_entradas_datos()
        + funciones de persistencia separadas.
    """
    # Destino y archivos
    base_dir = destino if destino else os.path.join(os.getcwd(), "datos_extraidos", "monitoreo")
    os.makedirs(base_dir, exist_ok=True)
    HISTORIAL_JSON = os.path.join(base_dir, "historial_notificaciones.json")
    HISTORIAL_CSV  = os.path.join(base_dir, "historial_notificaciones.csv")

    # Cargar historial existente
    historial_modelo: List[Entrada] = []
    historial_dicts: list[Dict[str, Any]] = []
    if os.path.exists(HISTORIAL_JSON):
        try:
            with open(HISTORIAL_JSON, "r", encoding="utf-8") as f:
                historial_dicts = json.load(f)
                historial_modelo = [Entrada.from_dict(e) for e in historial_dicts]
        except Exception as e:
            logger.warning("⚠️ Error leyendo JSON existente: %s. Se continúa con historial vacío.", e)
            historial_modelo = []
            historial_dicts = []

    # Usar la versión pura para extracción
    try:
        nuevas_entradas = await extraer_entradas_datos(
            page,
            duplicados=duplicados,
            incluir_tipos=incluir_tipos,
            fechas=fechas,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            historial_existente=historial_modelo,
        )
    except Exception as e:
        logger.error("❌ Error extrayendo entradas: %s", e)
        return 0

    # Poblar colección de modelos si se proporcionó
    if coleccion_modelos is not None:
        coleccion_modelos.extend(nuevas_entradas)

    # Convertir a dicts para persistencia
    nuevas_dicts = [e.to_dict() for e in nuevas_entradas]

    # Combinar con historial
    historial_actualizado: list[Dict[str, Any]]
    if duplicados:
        historial_actualizado = nuevas_dicts + historial_dicts
        nuevas_count = len(nuevas_dicts)
    else:
        if nuevas_dicts:
            historial_actualizado = nuevas_dicts + historial_dicts
            nuevas_count = len(nuevas_dicts)
        else:
            historial_actualizado = historial_dicts
            nuevas_count = 0

    # Persistir JSON
    try:
        with open(HISTORIAL_JSON, "w", encoding="utf-8") as f:
            json.dump(historial_actualizado, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error("❌ Error guardando JSON: %s", e)

    # Regenerar CSV completo
    try:
        with open(HISTORIAL_CSV, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Fecha", "Número", "Carátula", "Evento", "TipoEvento", "Leída", "Extraída En"])
            for e in historial_actualizado:
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

    logger.info("✅ Listo. Nuevas agregadas en esta corrida: %d", nuevas_count)
    logger.info("   Carpeta: %s", os.path.abspath(base_dir))

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
    """Extrae entradas con persistencia y devuelve modelos generados.

    Deprecated:
        Usar extraer_entradas_datos() para obtener solo modelos sin persistencia.
    """
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
