# notificaciones_control_v5_4_async.py
# Corte determinístico al final de la lista sin usar el botón "Refrescar".
# Mantiene compatibilidad con v4: historial JSON/CSV, deduplicación y campos existentes.

import os
import json
import csv
import re
import asyncio
import unicodedata
from datetime import datetime, timedelta
from typing import Optional
from playwright.async_api import Page

# ================================
# Selectores y utilidades
# ================================

SELEC_TABLA = "div.MuiTableContainer-root tr"
SELEC_EXPEDIENTE_NUMERO = "p.MuiTypography-root.MuiTypography-body1.w-full.css-11dlpbt"
SELEC_EXPEDIENTE_CARATULA = "p.MuiTypography-root.MuiTypography-body1.w-full.italic.css-4icvzy"
SELEC_CONTENEDOR_SCROLL = "#LayoutScrollingContainer"

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
    # Paso grande (pantalla completa o 600px mínimo)
    await page.evaluate(
        "(sel)=>{const el=document.querySelector(sel); if(el){"
        " const paso=Math.max(el.clientHeight*0.9,600);"
        " el.scrollTop=Math.min(el.scrollTop+paso, el.scrollHeight-el.clientHeight);"
        "}}", SELEC_CONTENEDOR_SCROLL
    )

async def _wheel(page: Page, cont_locator):
    # Refuerzo por si la UI engancha eventos de rueda
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
# Funciones principales
# ================================

async def actualizar_notificaciones_nuevas(page: Page, destino: Optional[str] = None) -> int:
    """
    Extrae notificaciones nuevas y las agrega al historial.

    Corta solo cuando:
      - se scrolleó al menos una vez,
      - se está al fondo del contenedor,
      - y es visible el heading 'No hay más eventos' (dentro del contenedor).
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

    # Deduplicación (igual criterio que v4)
    claves_historial = set(
        (normalizar_texto(n.get("numero", "")), n.get("fecha", ""), normalizar_texto(n.get("caratula", "")))
        for n in historial if "numero" in n and "fecha" in n and "caratula" in n
    )

    # Asegurar contenedor/lista
    try:
        await page.wait_for_selector(SELEC_CONTENEDOR_SCROLL, state="visible", timeout=15_000)
        await page.wait_for_selector(SELEC_TABLA, state="visible", timeout=15_000)
    except Exception:
        print("❌ Contenedor o filas no visibles.")
        return 0

    cont = page.locator(SELEC_CONTENEDOR_SCROLL)
    await cont.scroll_into_view_if_needed()

    # Señales scopeadas al contenedor (solo heading de fin)
    fin_loc = cont.get_by_role("heading", name=re.compile(r"No hay m[aá]s eventos", re.I))
    loading_loc = cont.get_by_text(re.compile(r"Cargando m[aá]s eventos", re.I))

    nuevas = []
    claves_vistas = set()

    # Control general
    max_iter = 250                 # límite por seguridad
    scrolled_count = 0
    intentos_sin_nuevos = 0
    max_intentos_sin_nuevos = 10   # respaldo suave para evitar loops si la página no cambia nada

    # Para confirmar avance de tramo (lista virtualizada)
    async def _ultima_fila_texto() -> str:
        filas = await page.query_selector_all(SELEC_TABLA)
        if not filas:
            return ""
        textos = []
        for fila in filas[-2:]:
            try:
                t = limpiar_texto(await fila.inner_text())
            except Exception:
                t = ""
            textos.append(t)
        return " || ".join(textos)

    ultima_fila_prev = await _ultima_fila_texto()

    # Posicionar el mouse dentro del contenedor para el wheel
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

                # "dd/mm/YYYY" -> "YYYY-mm-dd"
                fecha = datetime.strptime(fecha_str, "%d/%m/%Y").strftime("%Y-%m-%d")

                # Validaciones mínimas
                if numero == "N/D" or caratula == "N/D" or fecha == "1900-01-01":
                    continue

                clave = (normalizar_texto(numero), fecha, normalizar_texto(caratula))
                if clave in claves_historial or clave in claves_vistas:
                    continue

                claves_vistas.add(clave)
                nuevas.append({
                    "numero": numero,
                    "caratula": caratula,
                    "fecha": fecha,
                    "leida": False,
                    "extraida_en": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                nuevos_en_scroll += 1

            except Exception as e:
                print(f"⚠️ Error en fila: {e}")

        if nuevos_en_scroll > 0:
            print(f"➕ Nuevas notificaciones detectadas: {nuevos_en_scroll}")
            intentos_sin_nuevos = 0
        else:
            intentos_sin_nuevos += 1
            print(f"⏳ Intento {intentos_sin_nuevos}/{max_intentos_sin_nuevos} sin novedades en este tramo.")

        # 2) ¿Cortamos? — solo con fondo + heading visible + al menos un scroll
        fin_visible_local = await fin_loc.is_visible()
        if scrolled_count > 0 and (await _near_bottom(page)) and fin_visible_local:
            print("🏁 Fin detectado al llegar al fondo (heading 'No hay más eventos').")
            break

        # 3) Avanzar tramo: scroll grande + rueda, esperar loader si aparece
        await _scroll_step(page)
        scrolled_count += 1
        await _wheel(page, cont)

        # Sincronizar con loader si está
        try:
            if await loading_loc.is_visible():
                await loading_loc.wait_for(state="hidden", timeout=10_000)
        except Exception:
            pass

        # 4) Confirmar avance de tramo: cambió la última fila visible
        ultima_fila_now = await _ultima_fila_texto()
        if ultima_fila_now == ultima_fila_prev and not await _near_bottom(page):
            # No avanzó el render; empujones extra
            for _ in range(2):
                await _wheel(page, cont)
                await asyncio.sleep(0.2)
            ultima_fila_now = await _ultima_fila_texto()
        ultima_fila_prev = ultima_fila_now

        # Ritmo
        await asyncio.sleep(0.3)

    # ================================
    # Persistencia
    # ================================
    if nuevas:
        historial = nuevas + historial  # prepend (compatibilidad v4)
        try:
            with open(HISTORIAL_JSON, "w", encoding="utf-8") as f:
                json.dump(historial, f, indent=4, ensure_ascii=False)
            print(f"✅ {len(nuevas)} notificaciones nuevas agregadas al historial.")
        except Exception as e:
            print(f"❌ Error guardando historial JSON: {e}")

        try:
            with open(HISTORIAL_CSV, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Fecha", "Número", "Carátula", "Leída", "Extraída En"])
                for e in historial:
                    writer.writerow([
                        e.get("fecha", ""),
                        e.get("numero", ""),
                        e.get("caratula", ""),
                        "Sí" if e.get("leida", False) else "No",
                        e.get("extraida_en", "")
                    ])
            print("✅ Historial CSV actualizado.")
        except Exception as e:
            print(f"❌ Error guardando CSV: {e}")
    else:
        print("📂 No se encontraron notificaciones nuevas.")

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
