"""Launcher principal para el configurador GUI del sistema PJN."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

if __package__ in (None, ""):
    _PROJECT_ROOT = Path(__file__).resolve().parents[2]
    project_root_str = str(_PROJECT_ROOT)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)

from Sistema_v5.configuracion.gui.config_form import main as _run_gui


def main(argv: Sequence[str] | None = None) -> None:
    """Ejecuta el configurador GUI conservando compatibilidad histórica."""
    _run_gui(argv)


if __name__ == "__main__":
    main()
