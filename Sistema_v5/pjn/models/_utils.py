"""Utilidades internas para normalizar valores en modelos PJN."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Mapping


def get_first(mapping: Mapping[str, Any], *keys: str, default: Any = None) -> Any:
    """Obtiene el primer valor disponible para las ``keys`` dadas."""

    for key in keys:
        if key in mapping:
            return mapping[key]
    return default


def coerce_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


def coerce_int(value: Any, default: int | None = None) -> int | None:
    if value is None:
        return default
    if isinstance(value, bool):
        return int(value)
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def coerce_bool(value: Any, default: bool = False) -> bool:
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
