import os
import json
import csv
import time
import unicodedata
from datetime import datetime, timedelta
from playwright.async_api import Page
from typing import Optional

SELEC_TABLA = "div.MuiTableContainer-root tr"
SELEC_EXPEDIENTE_NUMERO = "p.MuiTypography-root.MuiTypography-body1.w-full.css-11dlpbt"
SELEC_EXPEDIENTE_CARATULA = "p.MuiTypography-root.MuiTypography-body1.w-full.italic.css-4icvzy"
SELEC_CONTENEDOR_SCROLL = "#LayoutScrollingContainer"

def limpiar_texto(texto):
    return texto.replace("\n\n", " ").replace("\n", " ").strip()

def normalizar_texto(t):
    return unicodedata.normalize("NFKD", t.strip().lower()).encode("ascii", "ignore").decode("utf-8")

async def actualizar_notificaciones_nuevas(page: Page, destino: Optional[str] = None):

    print("\U0001F50D Iniciando actualización de notificaciones...")

    if destino:
        NOTIF_DIR = destino
    else:
        NOTIF_DIR = os.path.join(os.getcwd(), "datos_extraidos", "monitoreo")

    os.makedirs(NOTIF_DIR, exist_ok=True)

    HISTORIAL_JSON = os.path.join(NOTIF_DIR, "historial_notificaciones.json")
    HISTORIAL_CSV = os.path.join(NOTIF_DIR, "historial_notificaciones.csv")

    if os.path.exists(HISTORIAL_JSON):
        with open(HISTORIAL_JSON, "r", encoding="utf-8") as f:
            historial = json.load(f)
    else:
        historial = []

    claves_historial = set(
        (normalizar_texto(n["numero"]), n["fecha"], normalizar_texto(n["caratula"]))
        for n in historial if "numero" in n and "fecha" in n and "caratula" in n
    )

    scroll_contenedor = await page.query_selector(SELEC_CONTENEDOR_SCROLL)
    if not scroll_contenedor:
        print("❌ Contenedor de scroll no encontrado.")
        return

    nuevas = []
    intentos_sin_nuevos = 0
    max_intentos = 5
    claves_vistas = set()

    while intentos_sin_nuevos < max_intentos:
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

                # Validar campos obligatorios
                if numero == "N/D" or caratula == "N/D" or fecha == "1900-01-01":
                    continue

                clave_normalizada = (normalizar_texto(numero), fecha, normalizar_texto(caratula))
                if clave_normalizada in claves_historial or clave_normalizada in claves_vistas:
                    continue

                claves_vistas.add(clave_normalizada)

                nueva_notif = {
                    "numero": numero,
                    "caratula": caratula,
                    "fecha": fecha,
                    "leida": False,
                    "extraida_en": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                nuevas.append(nueva_notif)
                nuevos_en_scroll += 1

            except Exception as e:
                print(f"⚠️ Error en fila: {e}")

        if nuevos_en_scroll > 0:
            print(f"➕ Nuevas notificaciones detectadas: {nuevos_en_scroll}")
            intentos_sin_nuevos = 0
        else:
            intentos_sin_nuevos += 1
            print(f"⏳ Intento {intentos_sin_nuevos}/{max_intentos} sin novedades.")

        try:
            await page.evaluate("(sel) => document.querySelector(sel).scrollBy(0, 1500);", SELEC_CONTENEDOR_SCROLL)
        except Exception as e:
            print(f"⚠️ Error al hacer scroll: {e}")
            break  # ⚠️ Importante: salimos del bucle para evitar loops infinitos

        time.sleep(1)

    if nuevas:
        historial = nuevas + historial
        with open(HISTORIAL_JSON, "w", encoding="utf-8") as f:
            json.dump(historial, f, indent=4, ensure_ascii=False)
        print(f"✅ {len(nuevas)} notificaciones nuevas agregadas al historial.")

        with open(HISTORIAL_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Fecha", "Número", "Carátula", "Leída", "Extraída En"])
            for e in historial:
                writer.writerow([e["fecha"], e["numero"], e["caratula"], "Sí" if e["leida"] else "No", e.get("extraida_en", "")])
        print(f"✅ Historial CSV actualizado.")
    else:
        print("📂 No se encontraron notificaciones nuevas.")

    return len(nuevas)

