import os
import sys
import mysql.connector
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

def get_db_config():
    return {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "database": os.getenv("MYSQL_DATABASE", "sintaxis"),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
    }

def debug_db():
    config = get_db_config()
    print(f"Conectando a {config['database']}...")
    
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)
        
        # 1. Listar expedientes recientes
        print("\n--- Expedientes Recientes ---")
        cursor.execute("SELECT id, numero_normalizado, caratula, fecha_creacion FROM expedientes ORDER BY id DESC LIMIT 5")
        expedientes = cursor.fetchall()
        
        if not expedientes:
            print("No se encontraron expedientes.")
            return

        for exp in expedientes:
            print(f"ID: {exp['id']}, Numero: {exp['numero_normalizado']}, Caratula: {exp['caratula']}")
            
            # 2. Contar actuaciones para este expediente
            cursor.execute("SELECT COUNT(*) as total FROM actuaciones WHERE expediente_id = %s", (exp['id'],))
            count = cursor.fetchone()['total']
            print(f"  Total Actuaciones (por ID): {count}")
            
            cursor.execute("SELECT COUNT(*) as total FROM actuaciones WHERE expediente_numero = %s", (exp['numero_normalizado'],))
            count_num = cursor.fetchone()['total']
            print(f"  Total Actuaciones (por Numero): {count_num}")
            
            # 3. Ver muestra de actuaciones
            if count > 0:
                cursor.execute("SELECT id, indice, tipo, fecha_clasificacion FROM actuaciones WHERE expediente_id = %s LIMIT 5", (exp['id'],))
                acts = cursor.fetchall()
                for act in acts:
                    print(f"    - ActID: {act['id']}, Indice: {act['indice']}, Tipo: {act['tipo']}")
            else:
                print("    (Sin actuaciones)")

        # Total global
        cursor.execute("SELECT COUNT(*) FROM actuaciones")
        total_global = cursor.fetchone()[0]
        print(f"\nTotal Global Actuaciones en DB: {total_global}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    debug_db()
