"""Utilidades de coerción de tipos.

Funciones puras para convertir valores a tipos específicos de forma segura.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Mapping


def get_first(mapping: Mapping[str, Any], *keys: str, default: Any = None) -> Any:
    """Obtiene el primer valor disponible para las claves dadas.

    Args:
        mapping: Diccionario donde buscar
        *keys: Claves a buscar en orden de prioridad
        default: Valor por defecto si ninguna clave existe

    Returns:
        El valor de la primera clave encontrada, o default si ninguna existe

    Example:
        >>> data = {"nombre": "Juan", "apellido": "Pérez"}
        >>> get_first(data, "name", "nombre")
        'Juan'
        >>> get_first(data, "age", "edad", default=0)
        0
    """
    for key in keys:
        if key in mapping:
            return mapping[key]
    return default


def coerce_str(value: Any) -> str | None:
    """Convierte un valor a string de forma segura.

    Args:
        value: Valor a convertir

    Returns:
        String limpio (sin espacios en blanco) o None si el valor es vacío

    Example:
        >>> coerce_str("  hello  ")
        'hello'
        >>> coerce_str("")
        None
        >>> coerce_str(None)
        None
        >>> coerce_str(123)
        '123'
    """
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


def coerce_int(value: Any, default: int | None = None) -> int | None:
    """Convierte un valor a entero de forma segura.

    Args:
        value: Valor a convertir
        default: Valor por defecto si la conversión falla

    Returns:
        Entero convertido o default si falla

    Example:
        >>> coerce_int("123")
        123
        >>> coerce_int("abc", default=0)
        0
        >>> coerce_int(True)
        1
    """
    if value is None:
        return default
    if isinstance(value, bool):
        return int(value)
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def coerce_bool(value: Any, default: bool = False) -> bool:
    """Convierte un valor a booleano de forma segura.

    Args:
        value: Valor a convertir
        default: Valor por defecto si el valor es None o vacío

    Returns:
        Booleano convertido

    Example:
        >>> coerce_bool("true")
        True
        >>> coerce_bool("si")
        True
        >>> coerce_bool("1")
        True
        >>> coerce_bool("no")
        False
        >>> coerce_bool("")
        False
    """
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if not normalized:
            return default
        if normalized in {"1", "true", "t", "yes", "y", "si", "sí"}:
            return True
        if normalized in {"0", "false", "f", "no", "n"}:
            return False
    return default
