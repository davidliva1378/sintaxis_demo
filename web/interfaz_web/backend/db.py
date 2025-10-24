import mysql.connector

def conectar():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="admin",
        database="test_v2"
    )

def obtener_expedientes():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id_expediente, numero, caratula FROM expedientes")
    datos = cursor.fetchall()
    conn.close()
    return datos
