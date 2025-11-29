
import sys
import os
import mysql.connector
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.getcwd())

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        port=int(os.getenv('MYSQL_PORT', '3306')),
        database=os.getenv('MYSQL_DATABASE', 'sintaxis'),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', '')
    )

def check_status(search_term):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    print(f"--- Buscando expediente que contenga: '{search_term}' ---")

    # 1. Buscar Expediente
    cursor.execute("SELECT id, numero_normalizado, caratula FROM expedientes WHERE numero_normalizado LIKE %s OR caratula LIKE %s", (f"%{search_term}%", f"%{search_term}%"))
    expedientes = cursor.fetchall()

    if not expedientes:
        print("❌ No se encontró ningún expediente.")
        return

    for exp in expedientes:
        exp_id = exp['id']
        numero = exp['numero_normalizado']
        print(f"\n📁 Expediente Encontrado: {numero}")
        print(f"   ID: {exp_id}")
        print(f"   Carátula: {exp['caratula']}")

        # 2. Contar Actuaciones
        cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN texto_extraido IS NOT NULL THEN 1 ELSE 0 END) as con_texto FROM actuaciones WHERE expediente_id = %s", (exp_id,))
        act_stats = cursor.fetchone()
        print(f"   📄 Actuaciones: {act_stats['total']} (Con texto extraído: {act_stats['con_texto']})")

        # 3. Contar Entidades
        # Nota: EntidadesRepository usa expediente_numero, no expediente_id
        cursor.execute("SELECT COUNT(*) as total FROM entidades_extraidas WHERE expediente_numero = %s", (numero,))
        ent_stats = cursor.fetchone()
        print(f"   🧠 Entidades Extraídas: {ent_stats['total']}")
        
        if ent_stats['total'] > 0:
             cursor.execute("SELECT entity_type, COUNT(*) as cant FROM entidades_extraidas WHERE expediente_numero = %s GROUP BY entity_type", (numero,))
             types = cursor.fetchall()
             types_str = ", ".join([f"{t['entity_type']}: {t['cant']}" for t in types])
             print(f"      Desglose: {types_str}")

        # 4. Contar Vencimientos
        cursor.execute("SELECT COUNT(*) as total FROM vencimientos WHERE expediente_id = %s", (exp_id,))
        venc_stats = cursor.fetchone()
        print(f"   ⏰ Vencimientos: {venc_stats['total']}")

    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python check_expediente_status.py <numero_o_parte_del_numero>")
        sys.exit(1)
    
    check_status(sys.argv[1])
