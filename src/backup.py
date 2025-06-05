#---------------------------expedientes_v1---------------------------
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
#         print(f"❌ Error al buscar expediente {numero}: {err}")
#         return None
#     finally:
#         cursor.close()
#         conexion.close()

# def obtener_expedientes():
#     """Obtiene todos los expedientes de la base de datos."""
#     conexion = conectar_bd()
#     if not conexion:
#         return None
#
#     try:
#         cursor = conexion.cursor(dictionary=True)
#         sql = "SELECT id_expediente, numero, caratula FROM Expedientes"
#         cursor.execute(sql)
#         expedientes = cursor.fetchall()
#         return expedientes if expedientes else []
#     except Error as err:
#         print(f"❌ Error al obtener expedientes: {err}")
#         return []
#     finally:
#         cursor.close()
#         conexion.close()

# def actualizar_situacion(id_expediente, nueva_situacion):
#     """Actualiza la situación de un expediente en la base de datos."""
#     conexion = conectar_bd()
#     if not conexion:
#         return False
#
#     try:
#         cursor = conexion.cursor()
#
#         # Buscar el ID de la nueva situación en la tabla Situaciones
#         sql_select = "SELECT id_situacion FROM Situaciones WHERE descripcion = %s"
#         cursor.execute(sql_select, (nueva_situacion,))
#         resultado = cursor.fetchone()
#
#         if resultado:
#             id_situacion = resultado[0]
#
#             # Actualizar la situación en la tabla Expedientes
#             sql_update = "UPDATE Expedientes SET situacion_id = %s WHERE id_expediente = %s"
#             cursor.execute(sql_update, (id_situacion, id_expediente))
#             conexion.commit()
#
#             print(f"✅ Situación del expediente {id_expediente} actualizada a '{nueva_situacion}' (ID: {id_situacion})")
#             return True
#         else:
#             print(f"⚠️ No se encontró la situación '{nueva_situacion}' en la base de datos.")
#             return False
#
#     except Error as err:
#         print(f"❌ Error al actualizar la situación del expediente {id_expediente}: {err}")
#         return False
#
#     finally:
#         cursor.close()
#         conexion.close()

    # 📌 FUNCIÓN PARA COMPARAR EXPEDIENTES Y CONSOLIDAR CAMBIOS
    # def comparar_expedientes(nuevos_expedientes):
    #     """Compara expedientes nuevos con los existentes en la base de datos y consolida los cambios en una sola fila."""
    #     registros_excel = []
    #     timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Fecha y hora actual
    #
    #     for nuevo in nuevos_expedientes:
    #         numero = nuevo["numero"]
    #         caratula = nuevo["caratula"]
    #         nueva_situacion = nuevo["situacion"]
    #         nueva_ultima_actuacion = nuevo["ultima_actuacion"]
    #
    #         expedientes_db = buscar_expediente(numero)
    #
    #         if not expedientes_db:
    #             registros_excel.append([timestamp, numero, "Nuevo",
    #                                     "N/A", nueva_situacion,
    #                                     "N/A", nueva_ultima_actuacion,
    #                                     "N/A", caratula])
    #         else:
    #             for expediente in expedientes_db:
    #                 id_expediente = expediente["id_expediente"]
    #                 caratula_existente = expediente["caratula"]
    #                 situacion_existente = expediente["situacion"]
    #                 ultima_actuacion_existente = expediente["ultima_actuacion"]
    #
    #                 # Consolidar todos los cambios en una sola fila
    #                 cambios_detectados = [
    #                     timestamp, numero, id_expediente,
    #                     situacion_existente if situacion_existente != nueva_situacion else "Sin cambios",
    #                     nueva_situacion if situacion_existente != nueva_situacion else "Sin cambios",
    #                     ultima_actuacion_existente if ultima_actuacion_existente != nueva_ultima_actuacion else "Sin cambios",
    #                     nueva_ultima_actuacion if ultima_actuacion_existente != nueva_ultima_actuacion else "Sin cambios",
    #                     caratula_existente.upper() if caratula_existente.upper() != caratula.upper() else "Sin cambios",
    #                     caratula if caratula_existente.upper() != caratula.upper() else "Sin cambios"
    #                 ]
    #
    #                 registros_excel.append(cambios_detectados)
    #
    #     # Guardar los cambios en Excel
    #     if registros_excel:
    #         guardar_en_excel(registros_excel)
    #     else:
    #         print("✅ No se detectaron cambios importantes.")

    # 📌 FUNCIÓN PARA EJECUTAR TODO EL PROCESO  (en el codigo nuevo se llama integrar_expedientes_json_bd
    # def main():
    #     """Función principal que coordina todo el proceso."""
    #     print("🔄 Cargando expedientes desde JSON...")
    #     nuevos_expedientes = cargar_json()
    #
    #     if nuevos_expedientes:
    #         print(f"✅ Se encontraron {len(nuevos_expedientes)} expedientes en el JSON.")
    #         print("🔍 Comparando con la base de datos...")
    #         comparar_expedientes(nuevos_expedientes)
    #
    #         # Borrar JSON después de procesarlo
    #         if os.path.exists(JSON_PATH):
    #             os.remove(JSON_PATH)
    #             print(f"🗑️ Archivo {JSON_PATH} eliminado después de la verificación.")
    #     else:
    #         print("⚠️ No hay expedientes para procesar.")

# 📌 FUNCIÓN PARA ACTUALIZAR LA CARÁTULA DE UN EXPEDIENTE
# def actualizar_caratula(id_expediente, nueva_caratula):
#     """Actualiza la carátula de un expediente en la base de datos."""
#     conexion = conectar_bd()
#     cursor = conexion.cursor()
#
#     sql = """
#         UPDATE Expedientes
#         SET caratula = %s
#         WHERE id_expediente = %s
#     """
#
#     cursor.execute(sql, (nueva_caratula, id_expediente))
#     conexion.commit()
#     filas_afectadas = cursor.rowcount
#
#     conexion.close()
#
#     if filas_afectadas > 0:
#         print(f"✅ Carátula actualizada a '{nueva_caratula}' para el expediente ID {id_expediente}.")
#     else:
#         print(f"⚠️ No se encontró el expediente ID {id_expediente} o la carátula no cambió.")

# def cargar_expediente(
#     numero, caratula, tipo_proceso=None, situacion_id=None, dependencia_id=None,
#     observacion=None, instancia="Primera", fecha_inicio=None, fecha_actualizacion=None,
#     ultima_actuacion=None, jurisdiccion_nombre=None
# ):
#     """Inserta un nuevo expediente en la base de datos, asegurando que la jurisdicción exista."""
#     conexion = conectar_bd()
#     if not conexion:
#         return False
#
#     try:
#         cursor = conexion.cursor()
#
#         # ✅ Asegurar que la jurisdicción existe y obtener su ID
#         jurisdiccion_id = None
#         if jurisdiccion_nombre:
#             jurisdiccion_id = obtener_o_insertar_jurisdiccion(jurisdiccion_nombre)
#
#         sql = """
#             INSERT INTO Expedientes (
#                 numero, caratula, tipo_proceso, situacion_id,
#                 dependencia_id, observacion, instancia, fecha_inicio,
#                 fecha_actualizacion, ultima_actuacion, jurisdiccion_id
#             )
#             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#         """
#
#         valores = (
#             numero, caratula, tipo_proceso, situacion_id, dependencia_id,
#             observacion, instancia, fecha_inicio, fecha_actualizacion, ultima_actuacion, jurisdiccion_id
#         )
#
#         cursor.execute(sql, valores)
#         conexion.commit()
#
#         nuevo_id = cursor.lastrowid
#         print(f"✅ Expediente '{numero}' insertado correctamente con ID {nuevo_id}.")
#         return nuevo_id
#
#     except Error as err:
#         print(f"❌ Error al insertar expediente '{numero}': {err}")
#         return None
#
#     finally:
#         cursor.close()
#         conexion.close()


# def obtener_o_insertar_jurisdiccion(nombre_jurisdiccion):
#     """Obtiene el ID de la jurisdicción si existe; si no, la inserta en la base de datos."""
#     if not nombre_jurisdiccion:
#         print("⚠️ Error: No se proporcionó un nombre de jurisdicción válido.")
#         return None
#
#     print(f"🔍 Buscando jurisdicción en la base de datos: {nombre_jurisdiccion}")
#
#     conexion = conectar_bd()
#     cursor = conexion.cursor()
#
#     try:
#         # Verificar si ya existe la jurisdicción
#         sql_select = "SELECT id_jurisdiccion FROM Jurisdicciones WHERE nombre = %s"
#         cursor.execute(sql_select, (nombre_jurisdiccion,))
#         resultado = cursor.fetchone()
#
#         if resultado:
#             print(f"✅ Jurisdicción '{nombre_jurisdiccion}' ya existe con ID {resultado[0]}")
#             return resultado[0]
#
#         else:
#             print(f"🆕 Insertando nueva jurisdicción: {nombre_jurisdiccion}")
#
#             # Insertar nueva jurisdicción
#             sql_insert = "INSERT INTO Jurisdicciones (nombre) VALUES (%s)"
#             cursor.execute(sql_insert, (nombre_jurisdiccion,))
#             conexion.commit()
#
#             jurisdiccion_id = cursor.lastrowid  # Obtener el ID generado
#             print(f"✅ Jurisdicción '{nombre_jurisdiccion}' insertada con ID {jurisdiccion_id}")
#
#             return jurisdiccion_id
#
#     except mysql.connector.Error as err:
#         print(f"❌ Error al insertar jurisdicción '{nombre_jurisdiccion}': {err}")
#         return None
#
#     finally:
#         cursor.close()
#         conexion.close()
#
# def actualizar_jurisdiccion_expediente(expediente_id, nueva_jurisdiccion):
#     """Actualiza la jurisdicción de un expediente si está en NULL, 'SIN ASIGNAR' o es diferente."""
#     if not nueva_jurisdiccion:
#         print(f"⚠️ No se proporcionó una nueva jurisdicción para el expediente {expediente_id}.")
#         return
#
#     conexion = conectar_bd()
#     cursor = conexion.cursor()
#
#     try:
#         # Obtener la jurisdicción actual del expediente
#         sql_select = "SELECT jurisdiccion_id FROM Expedientes WHERE id_expediente = %s"
#         cursor.execute(sql_select, (expediente_id,))
#         resultado = cursor.fetchone()
#
#         if resultado:
#             jurisdiccion_actual_id = resultado[0]
#
#             # Obtener el ID de la nueva jurisdicción o insertarla si no existe
#             print(f"🔍 Buscando ID de jurisdicción: '{nueva_jurisdiccion}' en la base de datos.")
#             nueva_juris_id = obtener_o_insertar_jurisdiccion(nueva_jurisdiccion)
#
#             if nueva_juris_id:
#                 print(f"✅ Se obtuvo el ID {nueva_juris_id} para la jurisdicción '{nueva_jurisdiccion}'.")
#                 if jurisdiccion_actual_id is None or jurisdiccion_actual_id == "SIN ASIGNAR" or jurisdiccion_actual_id != nueva_juris_id:
#                     sql_update = "UPDATE Expedientes SET jurisdiccion_id = %s WHERE id_expediente = %s"
#                     cursor.execute(sql_update, (nueva_juris_id, expediente_id))
#                     conexion.commit()
#                     print(f"🔄 Jurisdicción del expediente ID {expediente_id} actualizada a '{nueva_jurisdiccion}'.")
#                 else:
#                     print(f"✅ La jurisdicción del expediente ID {expediente_id} ya está correctamente asignada.")
#             else:
#                 print(f"❌ No se pudo obtener un ID para la jurisdicción '{nueva_jurisdiccion}'.")
#         else:
#             print(f"⚠️ No se encontró el expediente con ID {expediente_id}.")
#
#     except mysql.connector.Error as err:
#         print(f"❌ Error al actualizar jurisdicción para expediente {expediente_id}: {err}")
#
#     finally:
#         cursor.close()
#         conexion.close()