#!/usr/bin/env python3
"""
Script de inicialización de base de datos SQLite.
Crea las tablas definidas en los modelos si no existen.
"""

import sys
import os

# Agregar directorio raíz al path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from infrastructure.persistence.database import Base, engine
from infrastructure.persistence.database.models import Usuario, Expediente, Actuacion, Vencimiento, EntidadExtraida

def init_db():
    """Crea las tablas en la base de datos."""
    print(f"Iniciando creación de tablas en {engine.url}...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas creadas exitosamente:")
        for table in Base.metadata.tables:
            print(f"   - {table}")
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_db()
