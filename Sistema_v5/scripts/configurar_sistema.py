"""Launcher principal para el configurador GUI del sistema PJN."""

from __future__ import annotations

from typing import Sequence

from Sistema_v5.configuracion.gui.config_form import main as _run_gui


def main(argv: Sequence[str] | None = None) -> None:
    """Ejecuta el configurador GUI conservando compatibilidad histórica."""
    _run_gui(argv)


if __name__ == "__main__":
    main()
