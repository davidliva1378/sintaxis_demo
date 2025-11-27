import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

print("Attempting to import presentation.api.rest.main:app...")
try:
    from presentation.api.rest.main import app
    print("SUCCESS: Module app imported from presentation.api.rest.main.")
except ImportError as e:
    print(f"FAILURE: {e}")
    sys.exit(1)
except Exception as e:
    print(f"FAILURE: {e}")
    sys.exit(1)
