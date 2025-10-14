from __future__ import annotations

import re

from .base import generar_hash_identificador, limpiar_texto as _limpiar_texto_base
from .base import normalizar_fecha as _normalizar_fecha_base

_PREFIXES = re.compile(
    r"^(?:Oficina:|Fecha:|Tipo actuacion:|Detalle:|Foja:)\s*",
    re.IGNORECASE,
)


def limpiar_texto(texto: str | None) -> str:
    """Normaliza texto de celdas de actuaciones removiendo etiquetas iniciales."""

    base = _limpiar_texto_base(texto)
    if not base:
        return ""
    return _PREFIXES.sub("", base, count=1)


def normalizar_fecha(texto: str | None) -> str:
    """Adapta fechas dd/mm/YYYY al formato ISO, manteniendo valores originales."""

    normalizada = _normalizar_fecha_base(texto)
    if normalizada is None:
        return ""
    return normalizada


def generar_hash_archivo(
    fecha: str | None, tipo: str | None, detalle: str | None, longitud: int = 6
) -> str:
    """Genera un hash corto para identificar actuaciones con archivo adjunto."""

    return generar_hash_identificador(fecha, tipo, detalle, longitud=longitud)

