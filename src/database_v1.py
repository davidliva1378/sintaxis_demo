import mysql.connector
from mysql.connector import Error
#import os
#import json
from src.configuracion_v1 import DB_CONFIG

def conectar_bd():
    """Establece conexión con la base de datos."""
    try:
        conexion = mysql.connector.connect(**DB_CONFIG)
        return conexion
    except Error as err:
        print(f"❌ Error de conexión a la base de datos: {err}")
        return None
