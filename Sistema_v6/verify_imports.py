import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

try:
    print("Attempting to import infrastructure.scrapers.gestion_actuaciones.procesamiento...")
    from infrastructure.scrapers.gestion_actuaciones import procesamiento
    print("SUCCESS: Module imported.")
    
    if procesamiento.PROCESADOR_DISPONIBLE:
        print("SUCCESS: PROCESADOR_DISPONIBLE is True")
    else:
        print("FAILURE: PROCESADOR_DISPONIBLE is False")
        sys.exit(1)
        
except ImportError as e:
    print(f"FAILURE: ImportError: {e}")
    sys.exit(1)
except Exception as e:
    print(f"FAILURE: Exception: {e}")
    sys.exit(1)
