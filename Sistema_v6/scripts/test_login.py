import sys
import os
import bcrypt

# Agregar directorio raíz al path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from infrastructure.persistence.database import SessionLocal
from infrastructure.persistence.database.models import Usuario
from infrastructure.security.password import verify_password

def test_login(username, password):
    db = SessionLocal()
    try:
        print(f"Testing login for user: {username}")
        user = db.query(Usuario).filter(Usuario.username == username).first()
        
        if not user:
            print("❌ Usuario no encontrado")
            return

        print(f"Usuario encontrado: {user.username}")
        print(f"Hash en DB: {user.hashed_password}")
        
        is_valid = verify_password(password, user.hashed_password)
        
        if is_valid:
            print("✅ Contraseña CORRECTA")
        else:
            print("❌ Contraseña INCORRECTA")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_login("admin", "admin123")
