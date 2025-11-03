#!/usr/bin/env python3
"""
Script de ejecución para procesar archivos JSON de actuaciones existentes.

Este script permite clasificar y analizar actuaciones que ya fueron extraídas
previamente del PJN, sin necesidad de volver a extraerlas.

Uso:
    python ejecutar_procesamiento_json.py <ruta_json>
    python ejecutar_procesamiento_json.py <ruta_json> --dias-urgentes 5
    python ejecutar_procesamiento_json.py <carpeta> --recursivo

Para más opciones, ejecuta:
    python ejecutar_procesamiento_json.py --help
"""

import sys
from pathlib import Path

# Agregar raíz del proyecto al path
proyecto_raiz = Path(__file__).parent
sys.path.insert(0, str(proyecto_raiz))

# Ejecutar el script de procesamiento
if __name__ == "__main__":
    from core.flujo_inicial.procesar_actuaciones_json import main
    main()
