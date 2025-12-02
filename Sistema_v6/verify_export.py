
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

try:
    from application.services.monitoreo_service import MonitoreoService
    from presentation.api.rest.routers.monitoreo import exportar_expedientes
    print("Imports successful")
except Exception as e:
    print(f"Import failed: {e}")
