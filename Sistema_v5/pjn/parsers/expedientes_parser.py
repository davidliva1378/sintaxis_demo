"""Parsers para filas del listado de expedientes del PJN."""
from __future__ import annotations

from datetime import datetime
from typing import Sequence

from ..models import ExpedienteResumen


def normalizar_fecha_actuacion(valor: str | None) -> str | None:
    """Normaliza fechas ``dd/mm/yyyy`` a ``YYYY-MM-DD`` si es posible."""

    if not valor:
        return None

    texto = valor.strip()
    if not texto:
        return None

    for formato in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(texto, formato).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return texto


def parse_expediente_resumen(valores: Sequence[str]) -> ExpedienteResumen | None:
    """Interpreta la fila plana del listado de expedientes."""

    if len(valores) < 5:
        return None

    numero = valores[0].strip()
    dependencia = valores[1].strip()
    caratula = valores[2].strip()
    situacion = valores[3].strip() or None
    ultima_actuacion = normalizar_fecha_actuacion(valores[4])

    if not numero or not caratula:
        return None

    return ExpedienteResumen(
        numero=numero,
        dependencia=dependencia,
        caratula=caratula,
        situacion=situacion,
        ultima_actuacion=ultima_actuacion,
    )


__all__ = ["parse_expediente_resumen", "normalizar_fecha_actuacion"]
