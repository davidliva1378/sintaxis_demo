"""Punto de entrada temporal para abrir el formulario del monitor PJN.

Si los historiales no aparecen automáticamente al abrir la ventana, utilice el
botón «Cargar historiales…» de la interfaz para seleccionar manualmente los
archivos de ``Sistema_v5/data/monitor``.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from Sistema_v5.ui.gui_monitor_form import launch_monitor_form


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Abre el formulario temporal del monitor PJN para revisar historiales y selecciones. "
            "Si los historiales no aparecen, utilice el botón 'Cargar historiales…' para"
            " apuntar a Sistema_v5/data/monitor."
        ),
    )
    parser.add_argument(
        "--config",
        default="config/monitor.json",
        type=Path,
        help="Ruta al archivo de configuración monitor.json a utilizar.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    launch_monitor_form(args.config)


if __name__ == "__main__":  # pragma: no cover - ejecución directa
    main()
