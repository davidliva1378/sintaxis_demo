import sys
import os

# Agregar directorio raíz al path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from infrastructure.persistence.database import SessionLocal
from infrastructure.persistence.database.models import Usuario

def check_users():
    db = SessionLocal()
    try:
        count = db.query(Usuario).count()
        print(f"Total usuarios: {count}")
        users = db.query(Usuario).all()
        for u in users:
            print(f" - {u.username} ({u.email})")
    finally:
        db.close()

if __name__ == "__main__":
    check_users()
