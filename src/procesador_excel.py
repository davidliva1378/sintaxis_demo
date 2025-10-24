from src.database_v1 import conectar_bd
import mysql.connector
import pandas as pd

def obtener_mapeos_bd(conn):
    """
    Obtiene los mapeos de Juzgados, Secretarías, Situaciones, Dependencias y Prefijos desde la base de datos.
    """
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id_juzgado, nombre FROM juzgados;")
    juzgados = {row["nombre"]: row["id_juzgado"] for row in cursor.fetchall()}

    cursor.execute("SELECT id_secretaria, nombre FROM secretarias;")
    secretarias = {row["nombre"]: row["id_secretaria"] for row in cursor.fetchall()}

    cursor.execute("SELECT id_dependencia, juzgado_id, secretaria_id FROM dependencias;")
    dependencias = {(row["juzgado_id"], row["secretaria_id"]): row["id_dependencia"] for row in cursor.fetchall()}

    cursor.execute("SELECT id_situacion, descripcion FROM situaciones;")
    situaciones = {row["descripcion"]: row["id_situacion"] for row in cursor.fetchall()}

    cursor.execute("SELECT id_prefijo, codigo FROM prefijo_jurisdiccion;")
    prefijos = {row["codigo"]: row["id_prefijo"] for row in cursor.fetchall()}

    return juzgados, secretarias, dependencias, situaciones, prefijos


def crear_dependencia_si_no_existe(conn, juzgado_id, secretaria_id):
    """
    Crea una nueva dependencia en la base de datos si no existe.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO dependencias (juzgado_id, secretaria_id)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE id_dependencia = LAST_INSERT_ID(id_dependencia);
        """, (juzgado_id, secretaria_id)
    )
    conn.commit()
    cursor.execute("SELECT LAST_INSERT_ID();")
    return cursor.fetchone()[0]


def generar_script_insercion_sql_con_dependencias(df_expedientes):
    """
    Genera un script SQL para insertar o actualizar expedientes en la base de datos,
    incluyendo la asignación de dependencias, situaciones y prefijos desde la base de datos.
    """
    conn = conectar_bd()
    if conn is None:
        print("❌ No se pudo conectar a la base de datos.")
        return None

    juzgados, secretarias, dependencias, situaciones, prefijos = obtener_mapeos_bd(conn)

    sql_inserts = []
    for _, row in df_expedientes.iterrows():
        situacion_id = situaciones.get(row["Situación"], "NULL")
        ultima_actuacion = row["Última Actuación"].strftime('%Y-%m-%d') if pd.notnull(
            row["Última Actuación"]) else "NULL"
        fecha_inicio = f"{row['Año']}-01-01"  # Asignar 01/01/Año

        # Obtener prefijo_id desde la columna "ID-Jurisdiccion"
        prefijo_codigo = row["ID-Jurisdiccion"]
        prefijo_id = prefijos.get(prefijo_codigo, "NULL")

        juzgado_id = juzgados.get(row["Juzgado"], None)
        secretaria_id = secretarias.get(row["Secretaria"], None)

        # Verificar si la dependencia existe, si no, crearla
        if (juzgado_id, secretaria_id) not in dependencias:
            dependencia_id = crear_dependencia_si_no_existe(conn, juzgado_id, secretaria_id)
            dependencias[(juzgado_id, secretaria_id)] = dependencia_id
        else:
            dependencia_id = dependencias[(juzgado_id, secretaria_id)]

        sql = f"""
        INSERT INTO expedientes (numero, numero_solo, anio, incidental, caratula, ultima_actuacion, fecha_inicio, jurisdiccion_id, situacion_id, dependencia_id, prefijo_id)
        VALUES ('{row['Numero']}', {row['Numero_solo']}, {row['Año']}, 
                '{row['Incidental']}', '{row['Carátula']}', {f"'{ultima_actuacion}'" if ultima_actuacion != "NULL" else "NULL"}, 
                '{fecha_inicio}',
                1,  -- Se asigna el id_jurisdiccion = 1 (SIN ASIGNAR)
                {situacion_id},
                {dependencia_id},
                {prefijo_id})
        ON DUPLICATE KEY UPDATE
            incidental = VALUES(incidental),
            caratula = VALUES(caratula),
            ultima_actuacion = VALUES(ultima_actuacion),
            fecha_inicio = VALUES(fecha_inicio),
            situacion_id = VALUES(situacion_id),
            dependencia_id = VALUES(dependencia_id),
            prefijo_id = VALUES(prefijo_id);
        """
        sql_inserts.append(sql.strip())

    conn.close()
    return "\n".join(sql_inserts)
