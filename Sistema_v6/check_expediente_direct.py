import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def check_expediente_direct(numero):
    conn = mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        port=int(os.getenv('MYSQL_PORT', '3306')),
        database=os.getenv('MYSQL_DATABASE', 'sintaxis'),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', ''),
    )
    cursor = conn.cursor(dictionary=True)
    
    print(f"\n--- Checking Expedientes for '{numero}' ---")
    query = "SELECT * FROM expedientes WHERE numero_normalizado LIKE %s OR numero_original LIKE %s"
    cursor.execute(query, (f"%{numero}%", f"%{numero}%"))
    rows = cursor.fetchall()
    
    if not rows:
        print("❌ No expediente found in 'expedientes' table.")
    else:
        print(f"✅ Found {len(rows)} expedientes.")
        for row in rows:
            print(row)
            
    conn.close()

if __name__ == "__main__":
    check_expediente_direct("3449")
