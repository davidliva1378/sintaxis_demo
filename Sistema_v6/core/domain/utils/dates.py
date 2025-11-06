"""Utilidades puras para procesamiento y normalización de fechas.

Este módulo contiene funciones puras para convertir y normalizar fechas
extraídas del Portal Judicial Nacional a formatos estándar.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Sequence

from .text import limpiar_texto


def normalizar_fecha(
    valor: str | date | datetime | None,
    *,
    formato_salida: str = "%Y-%m-%d",
    formatos_entrada: Sequence[str] | None = None,
) -> str | None:
    """Convierte fechas comunes del PJN al formato deseado.

    Soporta múltiples formatos de entrada y convierte a un formato estándar.
    Si el valor es un objeto date/datetime, lo convierte directamente.
    Si es un string, intenta parsearlo con varios formatos comunes.

    Args:
        valor: Fecha a normalizar (string, date, datetime, o None)
        formato_salida: Formato de salida en notación strftime (default: ISO YYYY-MM-DD)
        formatos_entrada: Lista de formatos a intentar para parsear strings.
                         Si es None, usa formatos comunes del PJN.

    Returns:
        Fecha normalizada en el formato especificado, o None si el valor es None.
        Si no puede interpretarse, devuelve el texto original limpiado.

    Example:
        >>> normalizar_fecha("15/01/2025")
        '2025-01-15'
        >>> normalizar_fecha("15-01-2025")
        '2025-01-15'
        >>> normalizar_fecha("2025-01-15")
        '2025-01-15'
        >>> normalizar_fecha("15/01/25")
        '2025-01-15'
        >>> from datetime import date
        >>> normalizar_fecha(date(2025, 1, 15))
        '2025-01-15'
        >>> normalizar_fecha(None)
        None
        >>> normalizar_fecha("texto invalido")
        'texto invalido'
    """
    if valor is None:
        return None

    # Si es datetime, convertir directamente
    if isinstance(valor, datetime):
        return valor.strftime(formato_salida)

    # Si es date, convertir a datetime y luego a string
    if isinstance(valor, date):
        return datetime.combine(valor, datetime.min.time()).strftime(formato_salida)

    # Si es string, limpiar y parsear
    texto = limpiar_texto(str(valor))
    if not texto:
        return None

    # Formatos comunes del PJN
    formatos = formatos_entrada or (
        "%Y-%m-%d",  # ISO: 2025-01-15
        "%d/%m/%Y",  # DD/MM/YYYY: 15/01/2025
        "%d-%m-%Y",  # DD-MM-YYYY: 15-01-2025
        "%d/%m/%y",  # DD/MM/YY: 15/01/25
        "%d-%m-%y",  # DD-MM-YY: 15-01-25
    )

    # Intentar parsear con cada formato
    for fmt in formatos:
        try:
            return datetime.strptime(texto, fmt).strftime(formato_salida)
        except ValueError:
            continue

    # Si no se pudo parsear con ningún formato, devolver el texto original
    return texto


def parsear_fecha(
    valor: str | date | datetime | None,
    *,
    formatos_entrada: Sequence[str] | None = None,
) -> datetime | None:
    """Convierte un valor a datetime, o None si no es posible.

    Similar a normalizar_fecha pero retorna un objeto datetime en lugar de string.

    Args:
        valor: Fecha a parsear (string, date, datetime, o None)
        formatos_entrada: Lista de formatos a intentar para parsear strings

    Returns:
        Objeto datetime, o None si no se pudo parsear

    Example:
        >>> from datetime import datetime
        >>> result = parsear_fecha("15/01/2025")
        >>> result == datetime(2025, 1, 15)
        True
        >>> parsear_fecha(None) is None
        True
        >>> parsear_fecha("texto invalido") is None
        True
    """
    if valor is None:
        return None

    if isinstance(valor, datetime):
        return valor

    if isinstance(valor, date):
        return datetime.combine(valor, datetime.min.time())

    texto = limpiar_texto(str(valor))
    if not texto:
        return None

    formatos = formatos_entrada or (
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d/%m/%y",
        "%d-%m-%y",
    )

    for fmt in formatos:
        try:
            return datetime.strptime(texto, fmt)
        except ValueError:
            continue

    return None


def formatear_fecha(
    valor: str | date | datetime | None,
    formato: str,
) -> str | None:
    """Formatea una fecha a un formato específico.

    Wrapper conveniente de normalizar_fecha para especificar el formato de salida.

    Args:
        valor: Fecha a formatear
        formato: Formato de salida en notación strftime

    Returns:
        Fecha formateada, o None si el valor es None o no se pudo parsear

    Example:
        >>> formatear_fecha("15/01/2025", "%d de %B de %Y")
        '15 de January de 2025'
        >>> formatear_fecha("2025-01-15", "%d/%m/%Y")
        '15/01/2025'
    """
    fecha_normalizada = normalizar_fecha(valor, formato_salida="%Y-%m-%d")
    if not fecha_normalizada:
        return None

    try:
        dt = datetime.strptime(fecha_normalizada, "%Y-%m-%d")
        return dt.strftime(formato)
    except ValueError:
        return None


def es_fecha_valida(
    valor: str | date | datetime | None,
    *,
    formatos_entrada: Sequence[str] | None = None,
) -> bool:
    """Verifica si un valor es una fecha válida.

    Args:
        valor: Valor a verificar
        formatos_entrada: Lista de formatos a intentar para parsear strings

    Returns:
        True si el valor es una fecha válida, False en caso contrario

    Example:
        >>> es_fecha_valida("15/01/2025")
        True
        >>> es_fecha_valida("texto invalido")
        False
        >>> es_fecha_valida(None)
        False
        >>> from datetime import date
        >>> es_fecha_valida(date(2025, 1, 15))
        True
    """
    return parsear_fecha(valor, formatos_entrada=formatos_entrada) is not None
