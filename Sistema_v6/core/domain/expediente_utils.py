"""Utilidades para trabajar con expedientes.

Funciones de normalización y validación de números de expediente.
"""

import re


def normalizar_numero_expediente(numero: str) -> str:
    """
    Normaliza un número de expediente a un formato consistente.

    Convierte formatos como:
    - "FPA 015960/2018" -> "FPA-015960-2018"
    - "FPA 015960 2018" -> "FPA-015960-2018"
    - "FRE 004413/2021" -> "FRE-004413-2021"

    Args:
        numero: Número de expediente en cualquier formato

    Returns:
        Número normalizado con guiones

    Examples:
        >>> normalizar_numero_expediente("FPA 015960/2018")
        'FPA-015960-2018'
        >>> normalizar_numero_expediente("FRE-004413-2021")
        'FRE-004413-2021'
    """
    if not numero:
        return numero

    # Remover espacios extras al inicio y final
    numero = numero.strip()

    # Reemplazar espacios y barras por guiones
    # Regex: uno o más espacios o barras
    numero_normalizado = re.sub(r'[\s/]+', '-', numero)

    return numero_normalizado


def desnormalizar_numero_expediente(numero: str) -> str:
    """
    Convierte un número normalizado al formato original del PJN.

    Convierte:
    - "FPA-015960-2018" -> "FPA 015960/2018"

    Args:
        numero: Número normalizado con guiones

    Returns:
        Número en formato PJN (espacio y barra)
    """
    if not numero or '-' not in numero:
        return numero

    partes = numero.split('-')
    if len(partes) == 3:
        # Formato típico: AAA-NNNNNN-AAAA
        return f"{partes[0]} {partes[1]}/{partes[2]}"

    # Si no coincide con el formato esperado, retornar sin cambios
    return numero
