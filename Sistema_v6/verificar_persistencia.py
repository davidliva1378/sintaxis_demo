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

def check_persistence(numero_expediente):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    print(f"\n--- Verificando persistencia para {numero_expediente} ---")
    
    # 1. Expediente Metadata
    cursor.execute("SELECT id, fecha_ultimo_procesamiento, numero_normalizado FROM expedientes WHERE numero_normalizado LIKE %s", (f"%{numero_expediente}%",))
    exp = cursor.fetchone()
    if not exp:
        print("❌ Expediente no encontrado en tabla 'expedientes'")
        conn.close()
        return
    print(f"✅ Expediente ID: {exp['id']} (Found: {exp['numero_normalizado']})")
    print(f"   Último procesamiento: {exp['fecha_ultimo_procesamiento']}")

    # Use the found number for exact queries on other tables
    numero_exacto = exp['numero_normalizado']

    # 2. Actuaciones & Texto Extraído
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN tiene_texto_extraido = 1 THEN 1 ELSE 0 END) as con_texto,
            SUM(CASE WHEN tipo_ia IS NOT NULL THEN 1 ELSE 0 END) as con_ia,
            SUM(CASE WHEN indexado_rag = 1 THEN 1 ELSE 0 END) as en_rag
        FROM actuaciones 
        WHERE expediente_numero = %s
    """, (numero_exacto,))
    stats = cursor.fetchone()
    print(f"✅ Actuaciones: {stats['total']}")
    print(f"   - Con texto extraído: {stats['con_texto']}")
    print(f"   - Clasificadas por IA: {stats['con_ia']}")
    print(f"   - Indexadas en RAG: {stats['en_rag']}")

    # 3. Vencimientos
    cursor.execute("SELECT COUNT(*) as total FROM vencimientos WHERE expediente_numero = %s", (numero_expediente,))
    vencs = cursor.fetchone()['total']
    print(f"✅ Vencimientos detectados: {vencs}")

    # 4. Entidades (NER)
    # Check table existence first just in case
    try:
        cursor.execute("SELECT COUNT(*) as total FROM entidades_extraidas WHERE expediente_numero = %s", (numero_expediente,))
        ents = cursor.fetchone()['total']
        print(f"✅ Entidades extraídas (NER): {ents}")
    except Exception as e:
        print(f"⚠️ Error consultando entidades: {e}")

    conn.close()

if __name__ == "__main__":
    check_persistence("FPA_001961_2024")
    check_persistence("FRE_004125_2021")
