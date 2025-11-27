import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

try:
    print("Attempting to import app...")
    import app
    print("SUCCESS: Module app imported.")
    
    print("Attempting to create app instance...")
    application = app.create_app()
    print("SUCCESS: App instance created.")
        
except ImportError as e:
    print(f"FAILURE: ImportError: {e}")
    sys.exit(1)
except Exception as e:
    print(f"FAILURE: Exception: {e}")
    sys.exit(1)
