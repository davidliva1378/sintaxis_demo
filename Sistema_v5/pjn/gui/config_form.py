"""Capa de compatibilidad para el formulario de configuración GUI.

Este módulo permite seguir importando/ejecutando ``Sistema_v5.pjn.gui.config_form``
como en versiones anteriores, aunque la implementación real vive en
``Sistema_v5.configuracion.gui.config_form``. Se recomienda migrar a la nueva
ruta cuando sea posible.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

if __package__ in (None, ""):
    _PROJECT_ROOT = Path(__file__).resolve().parents[3]
    project_root_str = str(_PROJECT_ROOT)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)

from Sistema_v5.configuracion.gui.config_form import ConfigForm, main as _run_main

__all__ = ["ConfigForm", "main"]


def main(argv: Sequence[str] | None = None) -> None:
    """Ejecuta el formulario de configuración (modo legado)."""
    _run_main(argv)


if __name__ == "__main__":
    main()
