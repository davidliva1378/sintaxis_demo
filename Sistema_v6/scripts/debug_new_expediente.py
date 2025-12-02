import os
import sys
import mysql.connector
from dotenv import load_dotenv

# Load .env explicitly
load_dotenv()

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        database=os.getenv("MYSQL_DATABASE", "sintaxis"),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", "")
    )

def check_expediente(numero):
    print(f"--- Checking Expediente: {numero} ---")
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. Check Actuaciones
        query_act = """
            SELECT id, indice, tipo, tiene_archivo, ruta_pdf, tiene_texto_extraido
            FROM actuaciones 
            WHERE expediente_numero = %s 
            ORDER BY indice ASC 
            LIMIT 5
        """
        cursor.execute(query_act, (numero,))
        actuaciones = cursor.fetchall()
        print(f"\n[Actuaciones Found: {len(actuaciones)} (showing first 5)]")
        for act in actuaciones:
            print(act)

        # 2. Check Estadisticas
        query_stats = "SELECT * FROM procesamiento_estadisticas WHERE expediente_numero = %s"
        cursor.execute(query_stats, (numero,))
        stats = cursor.fetchall()
        print(f"\n[Estadisticas Found: {len(stats)}]")
        for stat in stats:
            print(stat)

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_expediente("FPA_005846_2019")
