import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        port=int(os.getenv('MYSQL_PORT', '3306')),
        database=os.getenv('MYSQL_DATABASE', 'sintaxis'),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', ''),
    )

def inspect_expediente(numero_partial):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    print(f"\n--- Inspecting Expediente matching '{numero_partial}' ---")

    # 1. Check expedientes table
    query_exp = f"SELECT * FROM expedientes WHERE numero_normalizado LIKE '%{numero_partial}%' OR numero_original LIKE '%{numero_partial}%'"
    cursor.execute(query_exp)
    exps = cursor.fetchall()
    
    if not exps:
        print("❌ No expediente found in 'expedientes' table.")
    else:
        for exp in exps:
            print(f"✅ Found Expediente: ID={exp['id']}, Norm='{exp['numero_normalizado']}', Orig='{exp['numero_original']}', Procesado='{exp['fecha_ultimo_procesamiento']}'")
            
            # 2. Check actuaciones table
            query_act = "SELECT COUNT(*) as count, SUM(CASE WHEN tiene_texto_extraido=1 THEN 1 ELSE 0 END) as con_texto FROM actuaciones WHERE expediente_numero = %s"
            cursor.execute(query_act, (exp['numero_normalizado'],))
            stats_norm = cursor.fetchone()
            
            cursor.execute(query_act, (exp['numero_original'],))
            stats_orig = cursor.fetchone()
            
            print(f"   Actuaciones (by Norm '{exp['numero_normalizado']}'): Total={stats_norm['count']}, Con Texto={stats_norm['con_texto']}")
            print(f"   Actuaciones (by Orig '{exp['numero_original']}'): Total={stats_orig['count']}, Con Texto={stats_orig['con_texto']}")

            # 3. Check sample actuacion
            if stats_norm['count'] > 0:
                cursor.execute("SELECT * FROM actuaciones WHERE expediente_numero = %s LIMIT 1", (exp['numero_normalizado'],))
                act = cursor.fetchone()
                print(f"   Sample Actuacion (Norm): ID={act['id']}, Tipo='{act['tipo']}', TextoLen={len(act['texto_extraido']) if act['texto_extraido'] else 0}")
            
            if stats_orig['count'] > 0:
                cursor.execute("SELECT * FROM actuaciones WHERE expediente_numero = %s LIMIT 1", (exp['numero_original'],))
                act = cursor.fetchone()
                print(f"   Sample Actuacion (Orig): ID={act['id']}, Tipo='{act['tipo']}', TextoLen={len(act['texto_extraido']) if act['texto_extraido'] else 0}")

            # 4. Check Vencimientos
            cursor.execute("SELECT COUNT(*) as total FROM vencimientos WHERE expediente_numero = %s", (exp['numero_normalizado'],))
            vencs = cursor.fetchone()['total']
            print(f"   Vencimientos (Norm): {vencs}")

            # 5. Check Entidades
            try:
                cursor.execute("SELECT COUNT(*) as total FROM entidades_extraidas WHERE expediente_numero = %s", (exp['numero_normalizado'],))
                ents = cursor.fetchone()['total']
                print(f"   Entidades (Norm): {ents}")
            except:
                print("   Entidades table not found or error")

    conn.close()

import sys

if __name__ == "__main__":
    if len(sys.argv) > 1:
        inspect_expediente(sys.argv[1])
    else:
        inspect_expediente("1961")
        inspect_expediente("4125")
