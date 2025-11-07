"""Configuración de pytest para tests del sistema.

Este archivo contiene fixtures y configuraciones compartidas para todos los tests.
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path para poder importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent))
