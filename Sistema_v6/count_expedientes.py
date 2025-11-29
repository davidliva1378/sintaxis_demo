import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def count_expedientes():
    conn = mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        port=int(os.getenv('MYSQL_PORT', '3306')),
        database=os.getenv('MYSQL_DATABASE', 'sintaxis'),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', ''),
    )
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM expedientes")
    count = cursor.fetchone()[0]
    print(f"Total expedientes in DB: {count}")
    conn.close()

if __name__ == "__main__":
    count_expedientes()
