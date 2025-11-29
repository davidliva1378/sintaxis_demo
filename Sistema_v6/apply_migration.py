import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def apply_migration():
    conn = mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        port=int(os.getenv('MYSQL_PORT', '3306')),
        database=os.getenv('MYSQL_DATABASE', 'sintaxis'),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', ''),
    )
    cursor = conn.cursor()
    try:
        print("Applying migration: ALTER TABLE actuaciones MODIFY COLUMN metodo_extraccion VARCHAR(255)")
        cursor.execute("ALTER TABLE actuaciones MODIFY COLUMN metodo_extraccion VARCHAR(255)")
        conn.commit()
        print("Migration applied successfully.")
    except Exception as e:
        print(f"Error applying migration: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    apply_migration()
