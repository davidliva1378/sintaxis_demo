#!/usr/bin/env python3
"""CLI para ejecutar el ciclo de prueba del extractor inicial."""

from __future__ import annotations

import argparse
from setup_path import incluir_ruta_base

incluir_ruta_base()

from extractor_inicial import run_ciclo_prueba  # noqa: E402  (import después de ajustar sys.path)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ejecuta el ciclo de prueba del extractor inicial del PJN.",
    )
    parser.add_argument(
        "--config-sistema",
        default="config/sistema.json",
        help="Ruta al archivo sistema.json (por defecto: config/sistema.json)",
    )
    parser.add_argument(
        "--config-monitor",
        default="config/monitor.json",
        help="Ruta al archivo monitor.json (por defecto: config/monitor.json)",
    )
    parser.add_argument(
        "--salida-extraccion",
        help="Directorio donde se guardará la extracción inicial.",
    )
    parser.add_argument(
        "--datos-monitor",
        help="Directorio de historiales del monitor a usar durante el ciclo.",
    )
    parser.add_argument(
        "--sin-formularios",
        action="store_true",
        help="Omite la apertura de formularios interactivos (útil para pruebas automatizadas).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    run_ciclo_prueba(
        args.config_sistema,
        args.config_monitor,
        directorio_extraccion=args.salida_extraccion,
        directorio_datos_monitor=args.datos_monitor,
        mostrar_formulario_directorios=not args.sin_formularios,
        mostrar_formulario_filtrado=not args.sin_formularios,
    )


if __name__ == "__main__":
    main()
