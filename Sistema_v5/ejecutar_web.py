#!/usr/bin/env python3
"""Script para ejecutar la interfaz web del Monitor PJN."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from web_app.app import app

if __name__ == '__main__':
    print("=" * 60)
    print("MONITOR PJN - INTERFAZ WEB")
    print("=" * 60)
    print()
    print("La interfaz web estará disponible en:")
    print("  http://localhost:5000")
    print("  http://127.0.0.1:5000")
    print()
    print("Presiona Ctrl+C para detener el servidor")
    print("=" * 60)
    print()

    app.run(debug=True, host='0.0.0.0', port=5000)
