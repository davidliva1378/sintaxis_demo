"""Parser para eventos de la bandeja de entradas del PJN.

Este módulo contiene funciones para interpretar los datos de eventos
(notificaciones y despachos) del portal PJN y convertirlos en objetos del dominio.

Migrado de: Sistema_v5/pjn/parsers/entradas_parser.py
"""

from __future__ import annotations

from typing import Iterable

from core.domain.entities import Entrada
from core.domain.utils.dates import normalizar_fecha


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
    """Crea una Entrada a partir de datos parseados del HTML.

    Args:
        numero: Número del expediente
        caratula: Carátula del expediente
        fecha: Fecha del evento (se normalizará automáticamente)
        evento: Descripción del evento (opcional)
        tipo_evento: Tipo de evento clasificado (opcional)
        leida: Si la entrada fue marcada como leída (default: False)
        extraida_en: Timestamp de extracción (opcional)

    Returns:
        Entrada: Objeto del dominio con los datos normalizados

    Example:
        >>> entrada = parse_entrada(
        ...     "CNM 0001/2024",
        ...     "CASO X C/ Y",
        ...     "15/01/2024",
        ...     "Providencia",
        ...     "PROVIDENCIA"
        ... )
        >>> print(entrada.numero)
        'CNM 0001/2024'
    """
    # Normalizar fecha
    fecha_normalizada = normalizar_fecha(
        fecha, formatos_entrada=["%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y"]
    )

    # Si no se pudo normalizar, usar el valor original
    if fecha_normalizada is None:
        fecha_normalizada = fecha.strip()

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
    """Genera claves únicas para detectar duplicados en el historial.

    Útil para comparar historiales y detectar nuevos eventos sin procesar
    los mismos eventos múltiples veces.

    Args:
        historial: Iterable de entradas a deduplicar

    Returns:
        Set de tuplas (numero, fecha, caratula, evento) que identifican
        unívocamente cada entrada

    Example:
        >>> entradas = [
        ...     Entrada("CNM 0001/2024", "CASO X", "2024-01-15", "Providencia", None),
        ...     Entrada("CNM 0001/2024", "CASO X", "2024-01-15", "Providencia", None),
        ... ]
        >>> claves = deduplicar_historial(entradas)
        >>> len(claves)  # Solo una clave única
        1
    """
    claves: set[tuple[str, str, str, str | None]] = set()
    for entrada in historial:
        claves.add(
            (
                entrada.numero,
                entrada.fecha,
                entrada.caratula,
                entrada.evento,
            )
        )
    return claves


__all__ = ["parse_entrada", "deduplicar_historial"]
