"""Compatibilidad con imports legacy del CLI de configuración.

⚠️  DEPRECADO: Este módulo se ha movido a Sistema_v5.configuracion.cli.configuracion

Por favor actualiza tus imports:
    Antes: from Sistema_v5.cli.configuracion import main
    Ahora:  from Sistema_v5.configuracion.cli import main

Este wrapper se mantendrá por compatibilidad pero será removido en futuras versiones.
"""

from __future__ import annotations

import warnings
import sys

warnings.warn(
    "Importing from cli.configuracion is deprecated. "
    "Use 'from Sistema_v5.configuracion.cli import main' instead.",
    DeprecationWarning,
    stacklevel=2
)

from Sistema_v5.configuracion.cli.configuracion import main

if __name__ == "__main__":
    main(sys.argv[1:])

__all__ = ["main"]
