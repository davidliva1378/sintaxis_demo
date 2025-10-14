"""Parsers para eventos de la bandeja de entradas del PJN."""
from __future__ import annotations

from datetime import datetime
from typing import Iterable

from ..models import Entrada


def normalizar_fecha(valor: str | None) -> str | None:
    if not valor:
        return None

    texto = valor.strip()
    if not texto:
        return None

    for formato in ("%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(texto, formato).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return texto


def parse_entrada(
    numero: str,
    caratula: str,
    fecha: str,
    evento: str | None,
    tipo_evento: str | None,
    *,
    leida: bool = False,
    extraida_en: str | None = None,
) -> Entrada:
    fecha_normalizada = normalizar_fecha(fecha) or fecha
    return Entrada(
        numero=numero.strip(),
        caratula=caratula.strip(),
        fecha=fecha_normalizada,
        evento=evento,
        tipo_evento=tipo_evento,
        leida=leida,
        extraida_en=extraida_en,
    )


def deduplicar_historial(
    historial: Iterable[Entrada],
) -> set[tuple[str, str, str, str | None]]:
    """Genera la clave base utilizada para detectar duplicados."""

    claves: set[tuple[str, str, str, str | None]] = set()
    for entrada in historial:
        claves.add((
            entrada.numero,
            entrada.fecha,
            entrada.caratula,
            entrada.evento,
        ))
    return claves


__all__ = ["deduplicar_historial", "normalizar_fecha", "parse_entrada"]
