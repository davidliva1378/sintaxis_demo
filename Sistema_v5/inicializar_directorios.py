"""Utilidad para crear las carpetas esperadas por ``SystemConfig``.

El script lee ``config/sistema.json`` (creando una configuración por
 defecto si no existe), normaliza las rutas y asegura que cada directorio
 definido esté presente en el árbol del proyecto.
"""

from __future__ import annotations

from dataclasses import fields
from pathlib import Path
from typing import Iterable

from pjn.system_config import SystemConfig


def _resolve_directories(config: SystemConfig, base_dir: Path) -> Iterable[tuple[str, Path]]:
    """Devuelve pares (nombre_de_campo, ruta_resuelta) para directorios."""

    for field in fields(SystemConfig):
        if not field.name.startswith("directorio_"):
            continue

        raw_path = getattr(config, field.name)
        path = Path(raw_path)
        if not path.is_absolute():
            path = base_dir / path
        yield field.name, path


def _crear_directorios(directorios: Iterable[tuple[str, Path]]) -> tuple[list[Path], list[Path]]:
    """Crea los directorios si no existen y clasifica el resultado."""

    creados: list[Path] = []
    existentes: list[Path] = []

    for _, ruta in directorios:
        if ruta.exists():
            existentes.append(ruta)
            continue

        ruta.mkdir(parents=True, exist_ok=True)
        creados.append(ruta)

    return creados, existentes


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    config_path = project_root / "config" / "sistema.json"

    config = SystemConfig.from_file(config_path)
    directorios = list(_resolve_directories(config, project_root))
    creados, existentes = _crear_directorios(directorios)

    if creados:
        print("📁 Directorios creados:")
        for ruta in creados:
            print(f" - {ruta}")
    else:
        print("✅ Todos los directorios ya existían.")

    if existentes:
        print("ℹ️ Directorios detectados (sin cambios):")
        for ruta in existentes:
            print(f" - {ruta}")


if __name__ == "__main__":
    main()
