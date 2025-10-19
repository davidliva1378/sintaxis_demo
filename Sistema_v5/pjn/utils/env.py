"""Utilidades para leer configuraciones desde variables de entorno.

Este módulo centraliza la lógica de parseo usada por las configuraciones del
monitor y del sistema, permitiendo reutilizar criterios consistentes para
valores booleanos, numéricos y listas definidas en variables de entorno.
"""

from __future__ import annotations

import json
from typing import Iterable

__all__ = [
    "parse_bool",
    "parse_int",
    "parse_float",
    "parse_str_list",
]


TRUE_VALUES: Iterable[str] = ("1", "true", "yes", "y", "on")
FALSE_VALUES: Iterable[str] = ("0", "false", "no", "n", "off")


def parse_bool(value: str) -> bool:
    """Convierte una cadena en booleano.

    Cualquier valor dentro de :data:`TRUE_VALUES` se interpreta como ``True`` y
    todos los demás como ``False`` para mantener compatibilidad con el
    comportamiento previo del monitor.
    """

    normalized = value.strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    # Compatibilidad retro: cualquier otro valor se considera falsy
    return False


def parse_int(value: str) -> int:
    """Convierte una cadena en entero, delegando en ``int`` para validar."""

    return int(value.strip())


def parse_float(value: str) -> float:
    """Convierte una cadena en ``float``."""

    return float(value.strip())


def parse_str_list(value: str) -> list[str]:
    """Convierte una cadena en lista de strings.

    Soporta valores separados por coma (``"lunes,martes"``) o listas en formato
    JSON (``"[\"lunes\", \"martes\"]"``).
    """

    cleaned = value.strip()
    if not cleaned:
        return []

    if cleaned.startswith("["):
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            parsed = None
        else:
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]

    return [item.strip() for item in cleaned.split(",") if item.strip()]
