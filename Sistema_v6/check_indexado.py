import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def check_indexado_status(numero):
    conn = mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        port=int(os.getenv('MYSQL_PORT', '3306')),
        database=os.getenv('MYSQL_DATABASE', 'sintaxis'),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', ''),
    )
    cursor = conn.cursor(dictionary=True)
    
    print(f"\n--- Checking 'indexado_rag' for '{numero}' ---")
    query = "SELECT id, tipo, indexado_rag FROM actuaciones WHERE expediente_numero LIKE %s LIMIT 10"
    cursor.execute(query, (f"%{numero}%",))
    rows = cursor.fetchall()
    
    if not rows:
        print("❌ No actuaciones found.")
    else:
        print(f"✅ Found {len(rows)} sample actuaciones.")
        for row in rows:
            print(row)
            
    conn.close()

if __name__ == "__main__":
    check_indexado_status("3449")
