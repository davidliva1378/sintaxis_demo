
import sys
import os

# Add project root to path
sys.path.insert(0, os.getcwd())

try:
    from application.services.ia.ia_integration_service import get_ia_integration_service
    print("IAIntegrationService imported successfully")
    service = get_ia_integration_service()
    print(f"Service initialized: {service}")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
