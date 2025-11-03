#!/usr/bin/env python3
"""
Script de ejecución principal para extracción de expedientes del PJN.

Este script proporciona una interfaz CLI simple para ejecutar la extracción
incremental de expedientes con o sin procesamiento de procesador_pdf.

Uso:
    python ejecutar_extraccion.py
    python ejecutar_extraccion.py --procesar
    python ejecutar_extraccion.py --procesar --dias-urgentes 3

Para más opciones, ejecuta:
    python ejecutar_extraccion.py --help
"""

import sys
from pathlib import Path

# Agregar raíz del proyecto al path
proyecto_raiz = Path(__file__).parent
sys.path.insert(0, str(proyecto_raiz))

# Ejecutar el script principal
if __name__ == "__main__":
    from core.flujo_inicial.main_extraccion import main
    main()
