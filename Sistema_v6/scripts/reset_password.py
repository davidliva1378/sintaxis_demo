import sys
import os
import bcrypt

# Agregar directorio raíz al path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from infrastructure.persistence.database import SessionLocal
from infrastructure.persistence.database.models import Usuario

def reset_password(username, new_password):
    db = SessionLocal()
    try:
        user = db.query(Usuario).filter(Usuario.username == username).first()
        if not user:
            print(f"❌ Usuario {username} no encontrado.")
            return

        # Hash password using bcrypt directly
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), salt).decode('utf-8')
        
        user.hashed_password = hashed_password
        db.commit()
        print(f"✅ Contraseña para '{username}' actualizada a '{new_password}'.")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_password("admin", "admin123")
