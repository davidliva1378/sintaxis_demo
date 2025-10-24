import json
import re
import os
from datetime import date, datetime
from src.database_v1 import conectar_bd

async def extraer_datos_expediente(page_expediente):
    """Extrae los datos del expediente en la pestaña activa y busca en la base de datos."""
    print("⏳ Detectando pestaña activa...")
    selector_expediente = "#expediente\\:j_idt96\\:detailCover"
    elemento = await page_expediente.query_selector(selector_expediente)
    if not elemento:
        print("⚠️ No se detectó el selector clave del expediente. Puede que no estés en un expediente activo.")
        return None


    if not page_expediente:
        print("❌ No hay una pestaña activa.")
        return None

    await page_expediente.wait_for_load_state("load")
    await page_expediente.wait_for_load_state("networkidle")

    print(f"✅ Pestaña lista. Extrayendo datos de: {page_expediente.url}")

    # Selectores para extraer información del expediente
    selectores = {
        "numero": "span[style='color:#000000;']",
        "jurisdiccion": "#expediente\\:j_idt96\\:detailCamera",
        "dependencia": "#expediente\\:j_idt96\\:detailDependencia",
        "situacion": "#expediente\\:j_idt96\\:detailSituation",
        "caratula": "#expediente\\:j_idt96\\:detailCover"
    }

    expediente = {}
    for campo, selector in selectores.items():
        elemento = await page_expediente.query_selector(selector)
        expediente[campo] = await elemento.inner_text().strip() if elemento else "No encontrado"

    # Extraer número y carátula del expediente
    numero_expediente = expediente.get("numero", None)
    caratula_expediente = expediente.get("caratula", None)

    if not numero_expediente:
        print("❌ No se pudo extraer el número de expediente.")
        return None

    # Conexión a la base de datos
    conexion = conectar_bd()
    if not conexion:
        print("❌ No se pudo conectar a la base de datos.")
        return None

    try:
        cursor = conexion.cursor(dictionary=True)

        # Buscar expediente en la base de datos por número
        cursor.execute("""
            SELECT id_expediente, numero, caratula, jurisdiccion_id, dependencia_id, situacion_id 
            FROM expedientes 
            WHERE numero = %s
        """, (numero_expediente,))
        expediente_db = cursor.fetchone()

        # Si no se encuentra por número, buscar por carátula
        if not expediente_db and caratula_expediente and caratula_expediente != "No encontrado":
            cursor.execute("""
                SELECT id_expediente, numero, caratula, jurisdiccion_id, dependencia_id, situacion_id 
                FROM expedientes 
                WHERE caratula = %s
            """, (caratula_expediente,))
            expediente_db = cursor.fetchone()

        cursor.close()
        conexion.close()

        if expediente_db:
            print(f"✅ Expediente encontrado en BD: {expediente_db}")
            return expediente_db  # 🔹 Se devuelve con el id_expediente

        print("❌ Expediente no encontrado en la base de datos.")
        return None  # 🔹 Si no se encontró el expediente, se devuelve None

    except Exception as err:
        print(f"❌ Error al ejecutar la consulta: {err}")
        return None



async def obtener_actuaciones(page_expediente, expediente_datos):
    """Descarga todas las actuaciones y genera un archivo JSON."""
    print("⏳ Descargando actuaciones...")

    if not page_expediente:
        print("❌ No se encontró una pestaña activa.")
        return

    expediente_numero = expediente_datos.get("numero", "desconocido")
    expediente_numero = re.sub(r'[^a-zA-Z0-9_-]', '_', expediente_numero)

    carpeta_actuaciones = os.path.join(os.getcwd(), "descargas", expediente_numero)
    os.makedirs(carpeta_actuaciones, exist_ok=True)

    actuaciones = []
    archivos_descargados = 0
    filas = await page_expediente.query_selector_all("#expediente\\:action-table tbody tr")

    for idx, fila in enumerate(filas, start=1):
        celdas = await fila.query_selector_all("td")

        def limpiar_texto(texto):
            return re.sub(r'^(Oficina:|Fecha:|Tipo actuacion:|Detalle:|Foja:)\s*', '', texto.strip().replace("\n", " "))

        enlace = await fila.query_selector("a i.fa-download")
        archivo_url = None
        nombre_archivo = None

        if enlace:
            try:
                link_handle = await page_expediente.evaluate_handle("(el) => el.closest('a')", enlace)
                if link_handle:
                    archivo_url = await link_handle.get_attribute("href")
                    nombre_archivo = await link_handle.get_attribute("download") or f"documento_{idx}.pdf"

                    if archivo_url:
                        nombre_archivo = f"{expediente_numero}_Acto_{idx}_{nombre_archivo.split('/')[-1]}"
                        ruta_archivo = os.path.join(carpeta_actuaciones, nombre_archivo)

                        with page_expediente.expect_download() as download_info:
                            link_handle.click()
                        download = download_info.value
                        await download.save_as(ruta_archivo)
                        archivos_descargados += 1
                        print(f"📥 Archivo guardado en: {ruta_archivo}")
            except Exception as e:
                print(f"❌ Error al procesar la descarga en la fila {idx}: {e}")

        actuaciones.append({
            "Oficina": limpiar_texto(celdas[1].inner_text()) if len(celdas) > 1 else "N/A",
            "Fecha": limpiar_texto(celdas[2].inner_text()) if len(celdas) > 2 else "N/A",
            "Tipo": limpiar_texto(celdas[3].inner_text()) if len(celdas) > 3 else "N/A",
            "Detalle": limpiar_texto(celdas[4].inner_text()) if len(celdas) > 4 else "N/A",
            "Foja": limpiar_texto(celdas[5].inner_text()) if len(celdas) > 5 else "N/A",
            "Archivo": archivo_url if archivo_url else "N/A",
            "NombreArchivo": nombre_archivo if archivo_url else "N/A"
        })

    expediente_datos["Cantidad de Actuaciones Obtenidas"] = len(actuaciones)
    expediente_datos["Cantidad de Archivos Descargados"] = archivos_descargados

    # 🔹 Convertir fechas en expediente_datos a string antes de serializar
    for key, value in expediente_datos.items():
        if isinstance(value, (date, datetime)):
            expediente_datos[key] = value.strftime("%Y-%m-%d")

    datos = {"Expediente": expediente_datos, "Actuaciones": actuaciones}

    json_filename = os.path.join(carpeta_actuaciones, f"actuaciones-{expediente_numero}.json")
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)

    print(f"✅ Archivo JSON guardado: {json_filename}")
    print(f"📂 Todos los archivos están en: {carpeta_actuaciones}")
    return actuaciones

def comparar_actuaciones(expediente_id, actuaciones_nuevas):
    """Compara las actuaciones obtenidas del sitio web con las almacenadas en la base de datos."""
    conexion = conectar_bd()
    if not conexion:
        print("❌ No se pudo conectar a la base de datos.")
        return []

    try:
        cursor = conexion.cursor(dictionary=True)
        query = """
            SELECT a.fecha, t.nombre AS tipo_actuacion, a.detalle 
            FROM actuaciones a
            JOIN tipos_actuaciones t ON a.tipo_actuacion_id = t.id_tipo_actuacion
            WHERE a.expediente_id = %s
        """
        cursor.execute(query, (expediente_id,))
        actuaciones_bd = cursor.fetchall()
        cursor.close()
        conexion.close()
    except Exception as err:
        print(f"❌ Error al obtener actuaciones de la base de datos: {err}")
        return []

    print(f"📂 Actuaciones en la base de datos ({len(actuaciones_bd)}):")
    for act in actuaciones_bd:
        print(f"   📌 {act['fecha']} | {act['tipo_actuacion']} | {act['detalle']}")

    print(f"🌐 Actuaciones obtenidas de la web ({len(actuaciones_nuevas)}):")
    for act in actuaciones_nuevas:
        print(f"   🌍 {act['Fecha']} | {act['Tipo']} | {act['Detalle']}")

    # Función para normalizar fechas y evitar errores de formato
    def normalizar_fecha(fecha):
        if isinstance(fecha, date):  # Si ya es un objeto date, lo dejamos igual
            return fecha.strftime("%Y-%m-%d")
        try:
            return datetime.strptime(fecha, "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError:
            return fecha  # Si no es una fecha válida, devolver tal cual

    # Función para normalizar textos (mayúsculas, sin espacios extra)
    def limpiar_texto(texto):
        return re.sub(r'\s+', ' ', texto.strip().upper())

    actuaciones_existentes = {
        (normalizar_fecha(act["fecha"]), limpiar_texto(act["tipo_actuacion"]), limpiar_texto(act["detalle"]))
        for act in actuaciones_bd
    }
    nuevas_actuaciones = []

    for act in actuaciones_nuevas:
        clave = (normalizar_fecha(act["Fecha"]), limpiar_texto(act["Tipo"]), limpiar_texto(act["Detalle"]))
        if clave not in actuaciones_existentes:
            nuevas_actuaciones.append(act)

    if nuevas_actuaciones:
        print(f"✅ Se encontraron {len(nuevas_actuaciones)} actuaciones nuevas:")
        for act in nuevas_actuaciones:
            print(f"   ➕ {act['Fecha']} | {act['Tipo']} | {act['Detalle']}")
    else:
        print("📂 No hay nuevas actuaciones.")

    return nuevas_actuaciones