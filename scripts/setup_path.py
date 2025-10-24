import sys
import os

def incluir_ruta_base():
    ruta_base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if ruta_base not in sys.path:
        sys.path.append(ruta_base)