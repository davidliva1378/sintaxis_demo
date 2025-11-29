import sys
import os

# Agregar directorio raíz al path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from infrastructure.persistence.database import SessionLocal
from infrastructure.persistence.database.models import EntidadExtraida, Actuacion

def check_entities():
    db = SessionLocal()
    try:
        count = db.query(EntidadExtraida).count()
        print(f"Total entidades extraidas: {count}")
        
        # Check if any actuacion has text extracted
        actuaciones_con_texto = db.query(Actuacion).filter(Actuacion.texto_extraido.isnot(None)).count()
        print(f"Actuaciones con texto extraido: {actuaciones_con_texto}")
        
    finally:
        db.close()

if __name__ == "__main__":
    check_entities()
