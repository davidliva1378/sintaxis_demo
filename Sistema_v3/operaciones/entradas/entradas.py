
import os
import json
import asyncio
import csv
from datetime import datetime, timedelta
from typing import Optional
from playwright.async_api import Page
from .utils import limpiar_texto, normalizar_texto

async def extraer_entradas(page: Page, destino: Optional[str] = None) -> int:
    print("\U0001F50D Iniciando actualización de notificaciones...")

    NOTIF_DIR = destino or os.path.join(os.getcwd(), "datos_extraidos", "monitoreo")
    os.makedirs(NOTIF_DIR, exist_ok=True)

    HISTORIAL_JSON = os.path.join(NOTIF_DIR, "historial_notificaciones.json")
    HISTORIAL_CSV = os.path.join(NOTIF_DIR, "historial_notificaciones.csv")

    historial = []
    if os.path.exists(HISTORIAL_JSON):
        with open(HISTORIAL_JSON, "r", encoding="utf-8") as f:
            historial = json.load(f)

    claves_historial = set(
        (normalizar_texto(n["numero"]), n["fecha"], normalizar_texto(n["caratula"]))
        for n in historial if "numero" in n and "fecha" in n and "caratula" in n
    )

    SELEC_TABLA = "div.MuiTableContainer-root tr"
    SELEC_EXPEDIENTE_NUMERO = "p.MuiTypography-root.MuiTypography-body1.w-full.css-11dlpbt"
    SELEC_EXPEDIENTE_CARATULA = "p.MuiTypography-root.MuiTypography-body1.w-full.italic.css-4icvzy"
    SELEC_CONTENEDOR_SCROLL = "#LayoutScrollingContainer"

    scroll_contenedor = await page.query_selector(SELEC_CONTENEDOR_SCROLL)
    if not scroll_contenedor:
        print("❌ Contenedor de scroll no encontrado.")
        return 0

    nuevas, claves_vistas, intentos_sin_nuevos = [], set(), 0
    while intentos_sin_nuevos < 5:
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
                fecha = datetime.strptime(fecha_str, "%d/%m/%Y").strftime("%Y-%m-%d")
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
            print(f"➕ {nuevos_en_scroll} nuevas notificaciones.")
            intentos_sin_nuevos = 0
        else:
            intentos_sin_nuevos += 1
            print(f"⏳ Intento {intentos_sin_nuevos}/5 sin novedades.")
        try:
            await page.evaluate("(sel) => document.querySelector(sel).scrollBy(0, 1500);", SELEC_CONTENEDOR_SCROLL)
        except Exception:
            break
        await asyncio.sleep(1)

    if nuevas:
        historial = nuevas + historial
        with open(HISTORIAL_JSON, "w", encoding="utf-8") as f:
            json.dump(historial, f, indent=4, ensure_ascii=False)
        with open(HISTORIAL_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Fecha", "Número", "Carátula", "Leída", "Extraída En"])
            for e in historial:
                writer.writerow([e["fecha"], e["numero"], e["caratula"], "Sí" if e["leida"] else "No", e["extraida_en"]])
        print(f"✅ Historial actualizado.")
    else:
        print("📂 No se encontraron nuevas notificaciones.")
    return len(nuevas)

def notificaciones_proximas_a_vencer(destino: Optional[str] = None, horas: int = 48) -> list[dict]:
    notif_dir = destino or os.path.join(os.getcwd(), "datos_extraidos", "monitoreo")
    path = os.path.join(notif_dir, "historial_notificaciones.json")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        historial = json.load(f)
    ahora, limite = datetime.now(), datetime.now() + timedelta(hours=horas)
    return [n for n in historial if "fecha" in n and ahora <= datetime.strptime(n["fecha"], "%Y-%m-%d") <= limite]
