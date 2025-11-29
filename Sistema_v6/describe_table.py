import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def describe_table(table_name):
    conn = mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        port=int(os.getenv('MYSQL_PORT', '3306')),
        database=os.getenv('MYSQL_DATABASE', 'sintaxis'),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', ''),
    )
    cursor = conn.cursor()
    cursor.execute(f"DESCRIBE {table_name}")
    columns = cursor.fetchall()
    print(f"--- Columns in {table_name} ---")
    for col in columns:
        print(col)
    conn.close()

if __name__ == "__main__":
    describe_table("actuaciones")
