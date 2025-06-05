import mysql.connector
from mysql.connector import Error
import os
import pandas as pd
from datetime import datetime
from src.configuracion_v1 import  JSON_PATH
from src.database_v1 import conectar_bd
from src.procesador_json_v1 import cargar_json
from src.reportes_v1 import  guardar_en_excel

#--------------------------------------------------CODIGO REORDENADO -----------------------------------------
def buscar_expediente(numero):
    """Busca un expediente en la base de datos."""
    conexion = conectar_bd()
    if not conexion:
        return None

    try:
        cursor = conexion.cursor(dictionary=True)
        sql = """
                SELECT e.id_expediente, e.caratula, e.ultima_actuacion, COALESCE(s.descripcion, 'N/A') AS situacion
                FROM Expedientes e
                LEFT JOIN Situaciones s ON e.situacion_id = s.id_situacion
                WHERE e.numero = %s
            """
        cursor.execute(sql, (numero,))
        resultado = cursor.fetchall()
        return resultado if resultado else None
    except Error as err:
        print(f"\u274c Error al buscar expediente {numero}: {err}")
        return None
    finally:
        cursor.close()
        conexion.close()
# def buscar_expediente(numero):
#     """Busca un expediente en la base de datos."""
#     conexion = conectar_bd()
#     if not conexion:
#         return None
#
#     try:
#         cursor = conexion.cursor(dictionary=True)
#         sql = """
#                 SELECT e.id_expediente, e.caratula, e.ultima_actuacion, s.descripcion AS situacion
#                 FROM Expedientes e
#                 LEFT JOIN Situaciones s ON e.situacion_id = s.id_situacion
#                 WHERE e.numero = %s
#             """
#         cursor.execute(sql, (numero,))
#         resultado = cursor.fetchall()
#         return resultado if resultado else None
#     except Error as err:
#         print(f"\u274c Error al buscar expediente {numero}: {err}")
#         return None
#     finally:
#         cursor.close()
#         conexion.close()

def obtener_expedientes():
    """Obtiene todos los expedientes de la base de datos."""
    conexion = conectar_bd()
    if not conexion:
        return None

    try:
        cursor = conexion.cursor(dictionary=True)
        sql = "SELECT id_expediente, numero, caratula FROM Expedientes"
        cursor.execute(sql)
        expedientes = cursor.fetchall()
        return expedientes if expedientes else []
    except Error as err:
        print(f"\u274c Error al obtener expedientes: {err}")
        return []
    finally:
        cursor.close()
        conexion.close()

def actualizar_situacion(id_expediente, nueva_situacion):
    """Actualiza la situación de un expediente en la base de datos."""
    conexion = conectar_bd()
    if not conexion:
        return False

    try:
        cursor = conexion.cursor()
        sql_select = "SELECT id_situacion FROM Situaciones WHERE descripcion = %s"
        cursor.execute(sql_select, (nueva_situacion,))
        resultado = cursor.fetchone()

        if resultado:
            id_situacion = resultado[0]
            sql_update = "UPDATE Expedientes SET situacion_id = %s WHERE id_expediente = %s"
            cursor.execute(sql_update, (id_situacion, id_expediente))
            conexion.commit()
            print(f"\u2705 Situación del expediente {id_expediente} actualizada a '{nueva_situacion}' (ID: {id_situacion})")
            return True
        else:
            print(f"\u26a0\ufe0f No se encontró la situación '{nueva_situacion}' en la base de datos.")
            return False
    except Error as err:
        print(f"\u274c Error al actualizar la situación del expediente {id_expediente}: {err}")
        return False
    finally:
        cursor.close()
        conexion.close()

def actualizar_caratula(id_expediente, nueva_caratula):
    """Actualiza la carátula de un expediente en la base de datos."""
    conexion = conectar_bd()
    if not conexion:
        return False

    cursor = None
    try:
        cursor = conexion.cursor()
        sql = """
            UPDATE Expedientes
            SET caratula = %s
            WHERE id_expediente = %s
        """
        cursor.execute(sql, (nueva_caratula, id_expediente))
        conexion.commit()
        filas_afectadas = cursor.rowcount

        if filas_afectadas > 0:
            print(f"✅ Carátula actualizada a '{nueva_caratula}' para el expediente ID {id_expediente}.")
            return True
        else:
            print(f"⚠️ No se encontró el expediente ID {id_expediente} o la carátula no cambió.")
            return False

    except Error as err:
        print(f"❌ Error al actualizar carátula del expediente {id_expediente}: {err}")
        return False

    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

def integrar_expedientes_json_bd():
    """Función principal que coordina el proceso de integración de expedientes desde un JSON a la BD.
        Compara los expedientes en la base de datos y retorna los cambios encontrados como DataFrame"""
    print("\U0001F504 Cargando expedientes desde JSON...")
    nuevos_expedientes = cargar_json()

    if nuevos_expedientes:
        print(f"\u2705 Se encontraron {len(nuevos_expedientes)} expedientes en el JSON.")
        print("🔍 Comparando con la base de datos...")
        df_cambios = comparar_expedientes(nuevos_expedientes)

        # Mostrar el DataFrame por consola
        if not df_cambios.empty:
            print(df_cambios)
        else:
            print("✅ No se detectaron cambios importantes en los expedientes.")



        if os.path.exists(JSON_PATH):
            os.remove(JSON_PATH)
            print(f"\U0001F5D1️ Archivo {JSON_PATH} eliminado después de la verificación.")

        return df_cambios

    else:
        print("⚠️ No hay expedientes para procesar.")


def comparar_expedientes(nuevos_expedientes):
    """Compara expedientes nuevos con los existentes en la base de datos y devuelve un DataFrame con los cambios."""
    registros = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for nuevo in nuevos_expedientes:
        numero = nuevo["numero"]
        caratula = nuevo["caratula"].strip().upper()
        nueva_situacion = nuevo.get("situacion", "N/A")
        nueva_ultima_actuacion = nuevo.get("ultima_actuacion", "N/A")

        expedientes_db = buscar_expediente(numero)

        if not expedientes_db:
            # Expediente nuevo
            cambios_detectados = {
                "Fecha": timestamp,
                "Número Expediente": numero,
                "ID Expediente": "Nuevo",
                "Situación Anterior": "N/A",
                "Situación Nueva": nueva_situacion,
                "Última Actuación Anterior": "N/A",
                "Última Actuación Nueva": nueva_ultima_actuacion,
                "Carátula Anterior": "N/A",
                "Carátula en Base de Datos": "N/A",
                "Carátula Nueva": caratula,
                "Tipo de Cambio": "🟢 Expediente Nuevo"
            }
            registros.append(cambios_detectados)
        else:
            for expediente in expedientes_db:
                id_expediente = expediente["id_expediente"]
                caratula_bd = expediente["caratula"].strip().upper() if expediente["caratula"] else "N/A"
                situacion_existente = expediente.get("situacion", "N/A")
                ultima_actuacion_existente = expediente.get("ultima_actuacion", "N/A")
                tipo_cambio = []

                if situacion_existente != nueva_situacion:
                    tipo_cambio.append("🟠 Cambio en la Situación")
                if ultima_actuacion_existente != nueva_ultima_actuacion:
                    tipo_cambio.append("🔵 Cambio en la Última Actuación")
                if caratula_bd != caratula:
                    tipo_cambio.append("🟣 Cambio en la Carátula")

                if tipo_cambio:
                    cambios_detectados = {
                        "Fecha": timestamp,
                        "Número Expediente": numero,
                        "ID Expediente": id_expediente,
                        "Situación Anterior": situacion_existente,
                        "Situación Nueva": nueva_situacion,
                        "Última Actuación Anterior": ultima_actuacion_existente,
                        "Última Actuación Nueva": nueva_ultima_actuacion,
                        "Carátula Anterior": caratula_bd,
                        "Carátula en Base de Datos": caratula_bd,
                        "Carátula Nueva": caratula,
                        "Tipo de Cambio": "⚪ Múltiples Cambios" if len(tipo_cambio) > 1 else tipo_cambio[0]
                    }
                    registros.append(cambios_detectados)

    df = pd.DataFrame(registros)

    if not df.empty:
        guardar_en_excel(df)
    return df

def cargar_expediente(
    numero, caratula, tipo_proceso=None, situacion_id=None, dependencia_id=None,
    observacion=None, instancia="Primera", fecha_inicio=None, fecha_actualizacion=None,
    ultima_actuacion=None, jurisdiccion_nombre=None
):
    """Inserta un nuevo expediente en la base de datos, asegurando que la jurisdicción exista."""
    conexion = conectar_bd()
    if not conexion:
        return False

    try:
        cursor = conexion.cursor()

        # ✅ Asegurar que la jurisdicción existe y obtener su ID
        jurisdiccion_id = None
        if jurisdiccion_nombre:
            jurisdiccion_id = obtener_o_insertar_jurisdiccion(jurisdiccion_nombre)

        sql = """
            INSERT INTO Expedientes (
                numero, caratula, tipo_proceso, situacion_id, 
                dependencia_id, observacion, instancia, fecha_inicio, 
                fecha_actualizacion, ultima_actuacion, jurisdiccion_id
            ) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        valores = (
            numero, caratula, tipo_proceso, situacion_id, dependencia_id,
            observacion, instancia, fecha_inicio, fecha_actualizacion, ultima_actuacion, jurisdiccion_id
        )

        cursor.execute(sql, valores)
        conexion.commit()

        nuevo_id = cursor.lastrowid
        print(f"✅ Expediente '{numero}' insertado correctamente con ID {nuevo_id}.")
        return nuevo_id

    except Error as err:
        print(f"❌ Error al insertar expediente '{numero}': {err}")
        return None

    finally:
        cursor.close()
        conexion.close()

#---------------------------------------- cargar un expediente con todos los campos de la base de datos ---------------------
def cargar_expediente_v2(
    numero, numero_solo, anio, incidental, caratula, ultima_actuacion,
    fecha_inicio, situacion_id, dependencia_id, prefijo_id
):
    """Inserta o actualiza un expediente en la base de datos."""
    conexion = conectar_bd()
    if not conexion:
        print("❌ No se pudo conectar a la base de datos.")
        return False

    cursor = None
    try:
        cursor = conexion.cursor()
        sql = """
        INSERT INTO expedientes (numero, numero_solo, anio, incidental, caratula, ultima_actuacion, fecha_inicio, 
                                jurisdiccion_id, situacion_id, dependencia_id, prefijo_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 1, %s, %s, %s)  -- Jurisdiccion_id = 1 (SIN ASIGNAR)
        ON DUPLICATE KEY UPDATE
            incidental = VALUES(incidental),
            caratula = VALUES(caratula),
            ultima_actuacion = VALUES(ultima_actuacion),
            fecha_inicio = VALUES(fecha_inicio),
            situacion_id = VALUES(situacion_id),
            dependencia_id = VALUES(dependencia_id),
            prefijo_id = VALUES(prefijo_id);
        """
        valores = (
            numero, numero_solo, anio, incidental, caratula,
            ultima_actuacion if ultima_actuacion and ultima_actuacion.upper() != "NULL" else None,
            fecha_inicio, situacion_id, dependencia_id, prefijo_id
        )

        cursor.execute(sql, valores)
        conexion.commit()

        print(f"✅ Expediente '{numero}' insertado o actualizado correctamente.")
        return True

    except Error as err:
        print(f"❌ Error al insertar/actualizar expediente '{numero}': {err}")
        return False

    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

def obtener_o_insertar_jurisdiccion(nombre_jurisdiccion):
    """Obtiene el ID de la jurisdicción si existe; si no, la inserta en la base de datos."""
    if not nombre_jurisdiccion:
        print("⚠️ Error: No se proporcionó un nombre de jurisdicción válido.")
        return None

    print(f"🔍 Buscando jurisdicción en la base de datos: {nombre_jurisdiccion}")

    conexion = conectar_bd()
    cursor = conexion.cursor()

    try:
        # Verificar si ya existe la jurisdicción
        sql_select = "SELECT id_jurisdiccion FROM Jurisdicciones WHERE nombre = %s"
        cursor.execute(sql_select, (nombre_jurisdiccion,))
        resultado = cursor.fetchone()

        if resultado:
            print(f"✅ Jurisdicción '{nombre_jurisdiccion}' ya existe con ID {resultado[0]}")
            return resultado[0]

        else:
            print(f"🆕 Insertando nueva jurisdicción: {nombre_jurisdiccion}")

            # Insertar nueva jurisdicción
            sql_insert = "INSERT INTO Jurisdicciones (nombre) VALUES (%s)"
            cursor.execute(sql_insert, (nombre_jurisdiccion,))
            conexion.commit()

            jurisdiccion_id = cursor.lastrowid  # Obtener el ID generado
            print(f"✅ Jurisdicción '{nombre_jurisdiccion}' insertada con ID {jurisdiccion_id}")

            return jurisdiccion_id

    except mysql.connector.Error as err:
        print(f"❌ Error al insertar jurisdicción '{nombre_jurisdiccion}': {err}")
        return None

    finally:
        cursor.close()
        conexion.close()

def actualizar_jurisdiccion_expediente(expediente_id, nueva_jurisdiccion):
    """Actualiza la jurisdicción de un expediente si está en NULL, 'SIN ASIGNAR' o es diferente."""
    if not nueva_jurisdiccion:
        print(f"⚠️ No se proporcionó una nueva jurisdicción para el expediente {expediente_id}.")
        return False

    conexion = conectar_bd()
    cursor = conexion.cursor()

    try:
        # Obtener la jurisdicción actual del expediente
        sql_select = "SELECT jurisdiccion_id FROM Expedientes WHERE id_expediente = %s"
        cursor.execute(sql_select, (expediente_id,))
        resultado = cursor.fetchone()

        if resultado:
            jurisdiccion_actual_id = resultado[0]

            # Obtener el ID de la nueva jurisdicción o insertarla si no existe
            print(f"🔍 Buscando ID de jurisdicción: '{nueva_jurisdiccion}' en la base de datos.")
            nueva_juris_id = obtener_o_insertar_jurisdiccion(nueva_jurisdiccion)

            if nueva_juris_id:
                print(f"✅ Se obtuvo el ID {nueva_juris_id} para la jurisdicción '{nueva_jurisdiccion}'.")
                if jurisdiccion_actual_id is None or jurisdiccion_actual_id == "SIN ASIGNAR" or jurisdiccion_actual_id != nueva_juris_id:
                    sql_update = "UPDATE Expedientes SET jurisdiccion_id = %s WHERE id_expediente = %s"
                    cursor.execute(sql_update, (nueva_juris_id, expediente_id))
                    conexion.commit()
                    print(f"🔄 Jurisdicción del expediente ID {expediente_id} actualizada a '{nueva_jurisdiccion}'.")
                else:
                    print(f"✅ La jurisdicción del expediente ID {expediente_id} ya está correctamente asignada.")
            else:
                print(f"❌ No se pudo obtener un ID para la jurisdicción '{nueva_jurisdiccion}'.")
        else:
            print(f"⚠️ No se encontró el expediente con ID {expediente_id}.")

    except mysql.connector.Error as err:
        print(f"❌ Error al actualizar jurisdicción para expediente {expediente_id}: {err}")

    finally:
        cursor.close()
        conexion.close()

