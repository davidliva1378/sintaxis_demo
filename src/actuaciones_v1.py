import os
import json
import mysql.connector
from datetime import datetime
from openpyxl import Workbook, load_workbook
import shutil  # Para mover archivos
from src.reportes_v1 import guardar_reporte_actuaciones
from src.database_v1 import *
from src.configuracion_v1 import *
from src.expedientes_v1 import  actualizar_jurisdiccion_expediente
#CARPETA_ORIGEN = "C:\\Users\\aleja\\OneDrive\\Escritorio\\Proyecto-Descargas"  # Carpeta donde están los archivos descargados
# CARPETA_EXPEDIENTES = "E:\\Sistema\\Expedientes"  # Carpeta base donde están los expedientes
# CARPETA_REPORTES = "C:\\Users\\aleja\\OneDrive\\Escritorio\\Proyecto-Descargas\\Reportes"
# EXCEL_PATH_2 = os.path.join(CARPETA_REPORTES, "reporte_actuaciones.xlsx")

#todas las funciones son usadas por procesar_actuaciones

# 📌 FUNCIÓN PARA ACTUALIZAR LA ÚLTIMA ACTUACIÓN DE UN EXPEDIENTE
def actualizar_ultima_actuacion(id_expediente, nueva_fecha):
    """Actualiza la fecha de la última actuación de un expediente."""
    conexion = conectar_bd()
    cursor = conexion.cursor()

    sql = """
        UPDATE Expedientes
        SET ultima_actuacion = %s
        WHERE id_expediente = %s
    """

    cursor.execute(sql, (nueva_fecha, id_expediente))
    conexion.commit()
    filas_afectadas = cursor.rowcount

    conexion.close()

    if filas_afectadas > 0:
        print(f"✅ Última actuación actualizada a '{nueva_fecha}' para el expediente ID {id_expediente}.")
    else:
        print(f"⚠️ No se encontró el expediente ID {id_expediente} o la fecha no cambió.")


# 📌 FUNCIÓN PARA OBTENER EL ID DE UN EXPEDIENTE POR SU NÚMERO
def obtener_id_expediente(numero_expediente):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    sql = "SELECT id_expediente FROM Expedientes WHERE numero = %s"
    cursor.execute(sql, (numero_expediente,))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado[0] if resultado else None

# 📌 FUNCIÓN PARA OBTENER O INSERTAR UN TIPO DE ACTUACIÓN
def obtener_o_insertar_tipo_actuacion(nombre_tipo):
    """Obtiene el ID del tipo de actuación. Si no existe, lo inserta en la base de datos."""
    conexion = conectar_bd()
    cursor = conexion.cursor()

    sql_select = "SELECT id_tipo_actuacion FROM Tipos_Actuaciones WHERE nombre = %s"
    cursor.execute(sql_select, (nombre_tipo,))
    resultado = cursor.fetchone()

    if resultado:
        tipo_actuacion_id = resultado[0]
    else:
        sql_insert = "INSERT INTO Tipos_Actuaciones (nombre) VALUES (%s)"
        cursor.execute(sql_insert, (nombre_tipo,))
        conexion.commit()
        tipo_actuacion_id = cursor.lastrowid
        print(f"🆕 Tipo de actuación '{nombre_tipo}' agregado con ID {tipo_actuacion_id}")

    conexion.close()
    return tipo_actuacion_id


# 📌 FUNCIÓN PARA VERIFICAR SI UNA ACTUACIÓN YA EXISTE
def existe_actuacion(expediente_id, fecha, tipo_actuacion_id, detalle):
    """Verifica si una actuación ya está registrada en la base de datos."""
    conexion = conectar_bd()
    cursor = conexion.cursor()

    sql = """
        SELECT COUNT(*) FROM Actuaciones
        WHERE expediente_id = %s AND fecha = %s AND tipo_actuacion_id = %s AND detalle = %s
    """
    cursor.execute(sql, (expediente_id, fecha, tipo_actuacion_id, detalle))
    resultado = cursor.fetchone()[0]

    conexion.close()
    return resultado > 0


# 📌 FUNCIÓN PARA INSERTAR UNA ACTUACIÓN
def insertar_actuacion(expediente_id, oficina, fecha, tipo_actuacion_id, detalle, foja, archivo, usuario_id=None):
    """Inserta una nueva actuación en la base de datos."""
    if existe_actuacion(expediente_id, fecha, tipo_actuacion_id, detalle):
        print(f"⚠️ La actuación del {fecha} ya existe en la base de datos.")
        return False

    conexion = conectar_bd()
    cursor = conexion.cursor()

    sql = """
        INSERT INTO Actuaciones (expediente_id, oficina, fecha, tipo_actuacion_id, detalle, foja, archivo, usuario_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    cursor.execute(sql, (expediente_id, oficina, fecha, tipo_actuacion_id, detalle, foja, archivo, usuario_id))
    conexion.commit()
    filas_afectadas = cursor.rowcount

    conexion.close()

    if filas_afectadas > 0:
        print(f"✅ Actuación del {fecha} insertada.")
        return True
    else:
        print(f"❌ Error al insertar la actuación del {fecha}.")
        return False


# 📌 FUNCIÓN PARA MOVER ARCHIVOS A LA CARPETA "DOCUMENTOS" DEL EXPEDIENTE
def mover_archivo(nombre_archivo, expediente_id):
    """Mueve el archivo de actuación desde la carpeta de descargas a la carpeta 'Documentos' dentro del expediente."""
    if not nombre_archivo:
        print("⚠️ No hay archivo asociado para mover.")
        return None

    # Ruta de origen del archivo en la carpeta de descargas
    origen = os.path.join(CARPETA_ORIGEN, nombre_archivo)

    # Carpeta de destino dentro del expediente
    carpeta_destino = os.path.join(CARPETA_EXPEDIENTES, str(expediente_id), "Documentos")

    # Asegurar que la carpeta "Documentos" existe dentro del expediente
    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)

    # Ruta de destino del archivo
    destino = os.path.join(carpeta_destino, nombre_archivo)

    if os.path.exists(origen):
        shutil.move(origen, destino)
        print(f"📂 Archivo {nombre_archivo} movido a {destino}")
        return destino  # Retorna la nueva ubicación del archivo
    else:
        print(f"⚠️ Archivo {nombre_archivo} no encontrado en {origen}.")
        return None  # Si el archivo no existe, retorna None

# 📌 FUNCIÓN PARA PROCESAR UN ARCHIVO JSON DE ACTUACIONES
def procesar_actuaciones(json_path):
    """Procesa el archivo JSON de actuaciones e inserta nuevas actuaciones en la base de datos."""
    try:
        with open(json_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        expediente_numero = data["Expediente"]["Número de Expediente"]
        expediente_id = obtener_id_expediente(expediente_numero)

        if expediente_id is None:
            print(f"⚠️ El expediente {expediente_numero} no está en la base de datos.")
            return

        nueva_jurisdiccion = data["Expediente"].get("Jurisdicción")
        if nueva_jurisdiccion:
            if nueva_jurisdiccion:
                print(f"🔍 Se encontró la jurisdicción '{nueva_jurisdiccion}' en el JSON.")
                actualizar_jurisdiccion_expediente(expediente_id, nueva_jurisdiccion)
                print(f"✅ Se ejecutó la actualización de jurisdicción para el expediente {expediente_id}.")



        nuevas_actuaciones = []

        for act in data["Actuaciones"]:
            oficina = act["Oficina"]
            fecha = datetime.strptime(act["Fecha"], "%d/%m/%Y").date()
            tipo_actuacion_id = obtener_o_insertar_tipo_actuacion(act["Tipo"])
            detalle = act["Detalle"]
            foja = act.get("Foja", "N/A")
            nombre_archivo = act.get("NombreArchivo", None)

            # Mover archivo si existe
            ruta_archivo = mover_archivo(nombre_archivo, expediente_id) if nombre_archivo else None

            if insertar_actuacion(expediente_id, oficina, fecha, tipo_actuacion_id, detalle, foja, ruta_archivo):
                nuevas_actuaciones.append(
                    [expediente_numero, oficina, fecha, act["Tipo"], detalle, foja, nombre_archivo])

        if nuevas_actuaciones:
            guardar_reporte_actuaciones(nuevas_actuaciones)

    except FileNotFoundError:
        print("❌ Error: No se encontró el archivo JSON.")
    except json.JSONDecodeError:
        print("❌ Error: El archivo JSON tiene un formato incorrecto.")
    except Exception as e:
        print(f"❌ Otro error ocurrió: {e}")
