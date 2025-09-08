# notificaciones_control_v5_6_async.py
# - Agrega 'evento' ("N"/"D") y 'tipo_evento' ("NOTIFICACION"/"DESPACHO") a JSON/CSV.
# - Dedupe compatible con históricos sin 'evento' (los enriquece si puede).
# - Mantiene gating de fin por heading local + fondo + al menos un scroll.

import os
import json
import csv
import re
import asyncio
import unicodedata
from datetime import datetime, timedelta
from typing import Optional, Tuple
from playwright.async_api import Page

# ================================
# Selectores y utilidades
# ================================

SELEC_TABLA = "div.MuiTableContainer-root tr"
SELEC_EXPEDIENTE_NUMERO = "p.MuiTypography-root.MuiTypography-body1.w-full.css-11dlpbt"
SELEC_EXPEDIENTE_CARATULA = "p.MuiTypography-root.MuiTypography-body1.w-full.italic.css-4icvzy"
SELEC_CONTENEDOR_SCROLL = "#LayoutScrollingContainer"

# regex robustas para aria-label del Avatar
RE_EVENTO_NOTIF = re.compile(r"evento\s+notificaci[oó]n", re.I)
RE_EVENTO_DESP  = re.compile(r"evento\s+despacho", re.I)

def limpiar_texto(texto: str) -> str:
    return texto.replace("\n\n", " ").replace("\n", " ").strip()

def normalizar_texto(t: str) -> str:
    return unicodedata.normalize("NFKD", t.strip().lower()).encode("ascii", "ignore").decode("utf-8")

# ================================
# Helpers de scroll / estado
# ================================

async def _near_bottom(page: Page) -> bool:
    return await page.evaluate(
        "(sel)=>{const el=document.querySelector(sel);if(!el) return false;"
        "const tol=24; return (el.scrollTop+el.clientHeight)>=(el.scrollHeight-tol);}",
        SELEC_CONTENEDOR_SCROLL
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
# Detección de indicador N/D por fila
# ================================

async def _detectar_indicador_evento(fila) -> Tuple[Optional[str], Optional[str]]:
    """
    Devuelve (evento, tipo_evento):
        evento: 'N' / 'D' / None
        tipo_evento: 'NOTIFICACION' / 'DESPACHO' / None
    Estrategia:
      1) Buscar cualquier hijo con aria-label que matchee 'Evento Notificación' o 'Evento Despacho'
      2) Fallback: dentro del Avatar, leer el <p> 'n'/'d'
    """
    try:
        # 1) Por aria-label (más robusto)
        con_aria = await fila.query_selector_all("[aria-label]")
        for el in con_aria:
            al = await el.get_attribute("aria-label") or ""
            if RE_EVENTO_NOTIF.search(al):
                return "N", "NOTIFICACION"
            if RE_EVENTO_DESP.search(al):
                return "D", "DESPACHO"
    except Exception:
        pass

    # 2) Fallback: letra en el Avatar (minúscula)
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
# Función principal
# ================================

async def actualizar_notificaciones_nuevas(page: Page, destino: Optional[str] = None) -> int:
    """
    Extrae notificaciones/despachos y agrega/actualiza el historial (JSON/CSV).
    - Añade 'evento' y 'tipo_evento' a cada registro nuevo.
    - Si existe en historial el mismo (numero, fecha, caratula) sin 'evento', lo enriquece.
    - Corta solo con: scroll>=1 + fondo + heading local 'No hay más eventos'.
    """

    print("🔍 Iniciando actualización de notificaciones...")

    NOTIF_DIR = destino if destino else os.path.join(os.getcwd(), "datos_extraidos", "monitoreo")
    os.makedirs(NOTIF_DIR, exist_ok=True)
    HISTORIAL_JSON = os.path.join(NOTIF_DIR, "historial_notificaciones.json")
    HISTORIAL_CSV  = os.path.join(NOTIF_DIR, "historial_notificaciones.csv")

    # Cargar historial
    if os.path.exists(HISTORIAL_JSON):
        try:
            with open(HISTORIAL_JSON, "r", encoding="utf-8") as f:
                historial = json.load(f)
        except Exception as e:
            print(f"⚠️ Error leyendo historial JSON: {e}. Se parte de lista vacía.")
            historial = []
    else:
        historial = []

    # Conjuntos de dedupe
    def _base_key(e):
        return (normalizar_texto(e.get("numero","")), e.get("fecha",""), normalizar_texto(e.get("caratula","")))

    def _event_key(e):
        return _base_key(e) + (e.get("evento","") or "",)

    claves_historial_base  = set(_base_key(e) for e in historial if e.get("numero") and e.get("fecha") and e.get("caratula"))
    claves_historial_event = set(_event_key(e) for e in historial if e.get("numero") and e.get("fecha") and e.get("caratula"))

    # Asegurar contenedor/lista
    try:
        await page.wait_for_selector(SELEC_CONTENEDOR_SCROLL, state="visible", timeout=15_000)
        await page.wait_for_selector(SELEC_TABLA, state="visible", timeout=15_000)
    except Exception:
        print("❌ Contenedor o filas no visibles.")
        return 0

    cont = page.locator(SELEC_CONTENEDOR_SCROLL)
    await cont.scroll_into_view_if_needed()

    # Señales scopeadas al contenedor
    fin_loc = cont.get_by_role("heading", name=re.compile(r"No hay m[aá]s eventos", re.I))
    loading_loc = cont.get_by_text(re.compile(r"Cargando m[aá]s eventos", re.I))

    nuevas = []
    claves_vistas_event = set()

    # Control general
    max_iter = 250
    scrolled_count = 0
    intentos_sin_nuevos = 0
    max_intentos_sin_nuevos = 10

    # Para confirmar avance (lista virtualizada)
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

    # Posicionar el mouse dentro del contenedor para wheel
    try:
        box = await cont.bounding_box()
        if box:
            await page.mouse.move(
                box["x"] + min(20, box["width"] / 2),
                box["y"] + min(20, box["height"] / 2)
            )
    except Exception:
        pass

    iteracion = 0
    while iteracion < max_iter and intentos_sin_nuevos < max_intentos_sin_nuevos:
        iteracion += 1

        # 1) Procesar filas visibles
        filas = await page.query_selector_all(SELEC_TABLA)
        nuevos_en_scroll = 0

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

                # Tipo de evento (N/D)
                evento, tipo_evento = await _detectar_indicador_evento(fila)

                # "dd/mm/YYYY" -> "YYYY-mm-dd"
                fecha = datetime.strptime(fecha_str, "%d/%m/%Y").strftime("%Y-%m-%d")

                if numero == "N/D" or caratula == "N/D" or fecha == "1900-01-01":
                    continue

                base_key = (normalizar_texto(numero), fecha, normalizar_texto(caratula))
                event_key = base_key + ((evento or ""),)

                # ¿ya existe exactamente este evento?
                if event_key in claves_historial_event or event_key in claves_vistas_event:
                    continue

                # ¿existe la base en historial pero sin 'evento'? => enriquecer
                if base_key in claves_historial_base and evento:
                    # actualizar en lista historial para añadir el evento
                    for reg in historial:
                        if (normalizar_texto(reg.get("numero","")), reg.get("fecha",""), normalizar_texto(reg.get("caratula",""))) == base_key:
                            if not reg.get("evento"):
                                reg["evento"] = evento
                                reg["tipo_evento"] = tipo_evento
                    # marcar como visto para no volver a intentar añadir
                    claves_historial_event.add(event_key)
                    continue

                # si no está, agregamos como nuevo
                claves_vistas_event.add(event_key)
                nuevas.append({
                    "numero": numero,
                    "caratula": caratula,
                    "fecha": fecha,
                    "evento": evento,                 # 'N' / 'D' / None
                    "tipo_evento": tipo_evento,       # 'NOTIFICACION' / 'DESPACHO' / None
                    "leida": False,
                    "extraida_en": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                nuevos_en_scroll += 1

            except Exception as e:
                print(f"⚠️ Error en fila: {e}")

        if nuevos_en_scroll > 0:
            print(f"➕ Nuevas filas detectadas: {nuevos_en_scroll}")
            intentos_sin_nuevos = 0
        else:
            intentos_sin_nuevos += 1
            print(f"⏳ Intento {intentos_sin_nuevos}/{max_intentos_sin_nuevos} sin novedades en este tramo.")

        # 2) ¿Cortamos? — solo con fondo + heading visible + al menos un scroll
        fin_visible_local = await fin_loc.is_visible()
        if scrolled_count > 0 and (await _near_bottom(page)) and fin_visible_local:
            print("🏁 Fin detectado al llegar al fondo (heading 'No hay más eventos').")
            break

        # 3) Avanzar tramo: scroll + wheel, sync con loader
        await _scroll_step(page)
        scrolled_count += 1
        await _wheel(page, cont)

        try:
            if await loading_loc.is_visible():
                await loading_loc.wait_for(state="hidden", timeout=10_000)
        except Exception:
            pass

        # 4) Confirmar avance: cambió la última fila visible
        ultima_fila_now = await _ultima_fila_texto()
        if ultima_fila_now == ultima_fila_prev and not await _near_bottom(page):
            for _ in range(2):
                await _wheel(page, cont)
                await asyncio.sleep(0.2)
            ultima_fila_now = await _ultima_fila_texto()
        ultima_fila_prev = ultima_fila_now

        await asyncio.sleep(0.3)

    # ================================
    # Persistencia (JSON/CSV)
    # ================================
    hubo_nuevas = len(nuevas) > 0
    if hubo_nuevas:
        historial = nuevas + historial  # prepend
    # Guardar JSON
    try:
        with open(HISTORIAL_JSON, "w", encoding="utf-8") as f:
            json.dump(historial, f, indent=4, ensure_ascii=False)
        if hubo_nuevas:
            print(f"✅ {len(nuevas)} filas nuevas agregadas al historial.")
        else:
            print("ℹ️ Historial actualizado (enriquecido) sin filas nuevas.")
    except Exception as e:
        print(f"❌ Error guardando historial JSON: {e}")

    # Regenerar CSV completo desde historial
    try:
        with open(HISTORIAL_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Fecha", "Número", "Carátula", "Evento", "TipoEvento", "Leída", "Extraída En"])
            for e in historial:
                writer.writerow([
                    e.get("fecha", ""),
                    e.get("numero", ""),
                    e.get("caratula", ""),
                    e.get("evento", "") or "",
                    e.get("tipo_evento", "") or "",
                    "Sí" if e.get("leida", False) else "No",
                    e.get("extraida_en", "")
                ])
        print("✅ Historial CSV actualizado.")
    except Exception as e:
        print(f"❌ Error guardando CSV: {e}")

    return len(nuevas)


def notificaciones_proximas_a_vencer(destino: Optional[str] = None, horas: int = 48):
    """Devuelve las notificaciones cuyo vencimiento es dentro de las próximas `horas` horas."""
    notif_dir = destino if destino else os.path.join(os.getcwd(), "datos_extraidos", "monitoreo")
    historial_path = os.path.join(notif_dir, "historial_notificaciones.json")
    if not os.path.exists(historial_path):
        return []
    try:
        with open(historial_path, "r", encoding="utf-8") as f:
            historial = json.load(f)
    except Exception as e:
        print(f"⚠️ Error leyendo historial JSON: {e}")
        return []
    ahora = datetime.now()
    limite = ahora + timedelta(hours=horas)
    proximas = []
    for notif in historial:
        if (notif.get("evento") or "").upper() != "N":
            continue  # solo notificaciones para agenda/vencimientos
        fecha_str = notif.get("fecha")
        if not fecha_str:
            continue
        try:
            venc = datetime.strptime(fecha_str, "%Y-%m-%d")
        except ValueError:
            continue
        if ahora <= venc <= limite:
            proximas.append(notif)
    return proximas
