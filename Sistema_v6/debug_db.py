import os
import mysql.connector
from infrastructure.config.settings import get_settings

settings = get_settings()

try:
    conn = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        database=os.getenv("MYSQL_DATABASE", "sintaxis"),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", "")
    )
    cursor = conn.cursor(dictionary=True)
    
    query = "SELECT * FROM procesamiento_estadisticas WHERE expediente_numero LIKE '%13980%2017%'"
    cursor.execute(query)
    results = cursor.fetchall()
    
    print(f"Found {len(results)} records:")
    for row in results:
        print(row)
        
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
