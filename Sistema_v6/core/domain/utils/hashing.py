"""Utilidades puras para generación de hashes e identificadores.

Este módulo contiene funciones puras para generar hashes estables a partir
de datos del dominio, útiles para identificar únicamente actuaciones, archivos,
o cualquier otro objeto que requiera un identificador consistente.
"""

from __future__ import annotations

import hashlib

from .text import limpiar_texto


def generar_hash_identificador(*componentes: object, longitud: int = 6) -> str:
    """Genera un hash estable a partir de múltiples componentes.

    Crea un identificador hash SHA-256 combinando múltiples componentes de datos.
    Los componentes son limpiados de espacios redundantes y unidos con "::"
    antes de hashear. Los valores None son ignorados.

    Este hash es determinístico: los mismos componentes siempre producen el
    mismo hash, lo que permite identificar objetos de forma consistente entre
    ejecuciones.

    Args:
        *componentes: Componentes a hashear (pueden ser de cualquier tipo)
        longitud: Número de caracteres del hash a retornar (default: 6)

    Returns:
        String hexadecimal del hash truncado a la longitud especificada

    Example:
        >>> generar_hash_identificador("expediente", "123", "2025")
        'a1b2c3'
        >>> generar_hash_identificador("expediente", "123", "2025", longitud=8)
        'a1b2c3d4'
        >>> # Mismo input produce mismo hash
        >>> h1 = generar_hash_identificador("test", "123")
        >>> h2 = generar_hash_identificador("test", "123")
        >>> h1 == h2
        True
        >>> # None es ignorado
        >>> generar_hash_identificador("test", None, "123")
        'xyz789'
    """
    # Limpiar y unir componentes no-None
    base = "::".join(
        limpiar_texto(str(c)) for c in componentes if c is not None
    )

    # Generar hash SHA-256
    digest = hashlib.sha256(base.encode("utf-8")).hexdigest()

    # Retornar los primeros N caracteres
    return digest[:longitud]


def generar_hash_actuacion(
    indice: int | str,
    oficina: str | None = None,
    fecha: str | None = None,
    detalle: str | None = None,
    *,
    longitud: int = 6,
) -> str:
    """Genera un hash identificador para una actuación judicial.

    Wrapper conveniente de generar_hash_identificador para actuaciones.

    Args:
        indice: Índice de la actuación
        oficina: Oficina que registró la actuación
        fecha: Fecha de la actuación
        detalle: Detalle o descripción de la actuación
        longitud: Número de caracteres del hash a retornar

    Returns:
        Hash identificador de la actuación

    Example:
        >>> generar_hash_actuacion(1, "JUZGADO", "2025-01-15", "Resolución")
        'abc123'
    """
    return generar_hash_identificador(
        indice, oficina, fecha, detalle, longitud=longitud
    )


def generar_hash_archivo(
    numero_expediente: str,
    indice_actuacion: int | str,
    tipo_archivo: str | None = None,
    *,
    longitud: int = 8,
) -> str:
    """Genera un hash identificador para un archivo adjunto.

    Útil para nombrar archivos descargados de forma única y consistente.

    Args:
        numero_expediente: Número del expediente
        indice_actuacion: Índice de la actuación que contiene el archivo
        tipo_archivo: Extensión o tipo del archivo (ej: "pdf")
        longitud: Número de caracteres del hash a retornar

    Returns:
        Hash identificador del archivo

    Example:
        >>> generar_hash_archivo("FPA-000632-2017", 1, "pdf")
        'a1b2c3d4'
        >>> # Útil para nombrar archivos
        >>> hash_val = generar_hash_archivo("FPA-000632-2017", 1, "pdf")
        >>> nombre_archivo = f"actuacion_{hash_val}.pdf"
        >>> nombre_archivo
        'actuacion_a1b2c3d4.pdf'
    """
    return generar_hash_identificador(
        numero_expediente, indice_actuacion, tipo_archivo, longitud=longitud
    )


def verificar_hash(
    hash_generado: str,
    hash_esperado: str,
) -> bool:
    """Verifica si dos hashes coinciden.

    Útil para verificar la integridad de archivos o datos.

    Args:
        hash_generado: Hash calculado recientemente
        hash_esperado: Hash esperado (almacenado previamente)

    Returns:
        True si los hashes coinciden, False en caso contrario

    Example:
        >>> hash_val = generar_hash_identificador("test", "123")
        >>> verificar_hash(hash_val, hash_val)
        True
        >>> verificar_hash(hash_val, "diferente")
        False
    """
    return hash_generado == hash_esperado


def generar_hash_contenido(contenido: bytes, longitud: int = 32) -> str:
    """Genera un hash del contenido de un archivo.

    A diferencia de generar_hash_identificador, esta función hashea el contenido
    binario directamente, sin procesamiento de texto. Útil para verificar
    integridad de archivos descargados.

    Args:
        contenido: Contenido binario a hashear
        longitud: Número de caracteres del hash a retornar (default: 32)

    Returns:
        String hexadecimal del hash SHA-256

    Example:
        >>> contenido = b"Contenido del archivo PDF"
        >>> hash_val = generar_hash_contenido(contenido)
        >>> len(hash_val)
        32
        >>> # Mismo contenido produce mismo hash
        >>> h1 = generar_hash_contenido(b"test")
        >>> h2 = generar_hash_contenido(b"test")
        >>> h1 == h2
        True
    """
    digest = hashlib.sha256(contenido).hexdigest()
    return digest[:longitud]
