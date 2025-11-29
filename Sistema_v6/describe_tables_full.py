import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def describe_tables():
    try:
        conn = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            port=int(os.getenv('MYSQL_PORT', '3306')),
            database=os.getenv('MYSQL_DATABASE', 'sintaxis'),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', ''),
        )
        cursor = conn.cursor()
        
        tables = ["vencimientos", "duplicados_detectados", "entidades_extraidas"]
        
        for table in tables:
            print(f"\n--- Columns in {table} ---")
            cursor.execute(f"DESCRIBE {table}")
            for col in cursor.fetchall():
                print(col)
                
            print(f"\n--- Indexes in {table} ---")
            cursor.execute(f"SHOW INDEX FROM {table}")
            for idx in cursor.fetchall():
                # Table, Non_unique, Key_name, Seq_in_index, Column_name, ...
                print(f"Key: {idx[2]}, Unique: {not idx[1]}, Column: {idx[4]}")

        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    describe_tables()
