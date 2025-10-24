import os
import time
import csv
import json
from playwright.sync_api import Page

# Selectores
SELEC_TABLA = "div.MuiTableContainer-root tr"
SELEC_EXPEDIENTE_NUMERO = "p.MuiTypography-root.MuiTypography-body1.w-full.css-11dlpbt"
SELEC_EXPEDIENTE_CARATULA = "p.MuiTypography-root.MuiTypography-body1.w-full.italic.css-4icvzy"
SELEC_CONTENEDOR_SCROLL = "#LayoutScrollingContainer"

# 📂 Carpeta donde se guardarán los archivos
NOTIFICACIONES_DIR = r"C:\Users\aleja\OneDrive\Escritorio\Proyecto-Descargas\Notificaciones"
os.makedirs(NOTIFICACIONES_DIR, exist_ok=True)

# 📂 Archivos donde se guardarán los expedientes
ARCHIVO_CSV = os.path.join(NOTIFICACIONES_DIR, "expedientes.csv")
ARCHIVO_JSON = os.path.join(NOTIFICACIONES_DIR, "expedientes.json")

def limpiar_texto(texto):
    """Limpia los expedientes eliminando saltos de línea innecesarios."""
    return texto.replace("\n\n", " ").replace("\n", " ").strip()

def cargar_json_existente():
    """Carga el archivo JSON existente para mantener el estado de 'leída'."""
    if os.path.exists(ARCHIVO_JSON):
        with open(ARCHIVO_JSON, mode="r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardar_en_csv(expedientes_por_fecha):
    """Guarda los expedientes en un archivo CSV con el estado de lectura."""
    with open(ARCHIVO_CSV, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Fecha", "Número", "Carátula", "Leída"])  # Encabezado

        for fecha, expedientes in expedientes_por_fecha.items():
            for expediente in expedientes:
                estado_leido = "Sí" if expediente["leida"] else "No"
                writer.writerow([fecha, expediente["numero"], expediente["caratula"], estado_leido])

    print(f"✅ Notificaciones guardadas en {ARCHIVO_CSV}")

def guardar_en_json(expedientes_por_fecha):
    """Guarda los expedientes en JSON manteniendo el estado de lectura."""
    expedientes_previos = cargar_json_existente()

    for fecha, expedientes in expedientes_por_fecha.items():
        if fecha not in expedientes_previos:
            expedientes_previos[fecha] = []

        # Verificar si el expediente ya existe y mantener su estado de lectura
        expedientes_nuevos = []
        for exp in expedientes:
            # Buscar si el expediente ya existe en el JSON previo
            existente = next((e for e in expedientes_previos[fecha] if e["numero"] == exp["numero"]), None)
            if existente:
                exp["leida"] = existente["leida"]  # Mantener el estado anterior
            expedientes_nuevos.append(exp)

        expedientes_previos[fecha] = expedientes_nuevos

    with open(ARCHIVO_JSON, mode="w", encoding="utf-8") as f:
        json.dump(expedientes_previos, f, indent=4, ensure_ascii=False)

    print(f"✅ Notificaciones guardadas en {ARCHIVO_JSON}")

def capturar_lista_expedientes(page: Page):
    """Captura la lista completa de expedientes con scroll automático sin duplicados por fecha."""
    print("🔍 Buscando expedientes en la página...")

    page.wait_for_load_state("networkidle")

    # Obtener el contenedor principal con scroll
    contenedor_scroll = page.query_selector(SELEC_CONTENEDOR_SCROLL)
    if not contenedor_scroll:
        print("⚠️ No se encontró el contenedor de scroll.")
        return {}

    expedientes_por_fecha = {}  # 🔹 Diccionario para almacenar expedientes únicos por fecha
    intentos_sin_nuevos = 0
    max_intentos = 5  # 🔹 Aumentamos a 5 intentos sin nuevos expedientes

    while intentos_sin_nuevos < max_intentos:  # 🔹 Seguimos hasta que no haya nuevos expedientes
        # Obtener todas las filas de la tabla
        tabla_notificaciones = page.query_selector_all(SELEC_TABLA)

        nuevos_expedientes = 0
        for fila in tabla_notificaciones:
            numero_elemento = fila.query_selector(SELEC_EXPEDIENTE_NUMERO)
            caratula_elemento = fila.query_selector(SELEC_EXPEDIENTE_CARATULA)
            fecha_elemento = fila.query_selector_all("td")  # Obtener todas las celdas

            # Extraer el texto de los elementos si existen
            numero_expediente = limpiar_texto(numero_elemento.inner_text()) if numero_elemento else "Número desconocido"
            caratula_expediente = limpiar_texto(caratula_elemento.inner_text()) if caratula_elemento else "Carátula desconocida"
            fecha_expediente = limpiar_texto(fecha_elemento[2].inner_text()) if len(fecha_elemento) >= 3 else "Fecha desconocida"

            # Si la fecha aún no está en el diccionario, la creamos con una lista vacía
            if fecha_expediente not in expedientes_por_fecha:
                expedientes_por_fecha[fecha_expediente] = []

            # Si el expediente no está en la lista, lo agregamos con "leida": False
            expediente_data = {"numero": numero_expediente, "caratula": caratula_expediente, "leida": False}
            if expediente_data not in expedientes_por_fecha[fecha_expediente]:
                expedientes_por_fecha[fecha_expediente].append(expediente_data)
                nuevos_expedientes += 1

        if nuevos_expedientes > 0:
            print(f"📌 Se agregaron {nuevos_expedientes} nuevos expedientes únicos.")
            intentos_sin_nuevos = 0  # 🔹 Reiniciar intentos si se encontraron nuevos elementos
        else:
            intentos_sin_nuevos += 1
            print(f"⏳ No se detectaron nuevos expedientes. Intento {intentos_sin_nuevos}/{max_intentos}")

        # 📌 Hacer scroll en el contenedor principal con mayor distancia
        page.evaluate("(selector) => document.querySelector(selector).scrollBy(0, 1500);", SELEC_CONTENEDOR_SCROLL)
        time.sleep(1)  # 🔹 Reducimos la espera entre scrolls para mejorar la velocidad

    print(f"✅ Se encontraron expedientes únicos por fecha:")
    for fecha, expedientes in expedientes_por_fecha.items():
        print(f"📅 {fecha}: {len(expedientes)} expedientes")
        for exp in expedientes:
            estado_leido = "Sí" if exp["leida"] else "No"
            print(f"   📂 Número: {exp['numero']} | 📜 Carátula: {exp['caratula']} | 🔖 Leída: {estado_leido}")

    # 📂 Guardar los resultados
    guardar_en_csv(expedientes_por_fecha)
    guardar_en_json(expedientes_por_fecha)

    return expedientes_por_fecha
