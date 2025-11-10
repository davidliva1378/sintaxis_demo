"""Utilidades puras para procesamiento y normalización de texto.

Este módulo contiene funciones puras (sin efectos secundarios) para limpiar,
normalizar y procesar texto extraído del Portal Judicial Nacional.
"""

from __future__ import annotations

import re
import unicodedata


def limpiar_texto(texto: str | None) -> str:
    """Elimina saltos de línea y espacios redundantes.

    Convierte todos los espacios en blanco múltiples (espacios, tabs, saltos
    de línea) en un único espacio, y elimina espacios al inicio y final.

    Args:
        texto: Texto a limpiar (puede ser None)

    Returns:
        Texto limpio sin espacios redundantes, o cadena vacía si el input es None

    Example:
        >>> limpiar_texto("  Hola\\n  Mundo  ")
        'Hola Mundo'
        >>> limpiar_texto(None)
        ''
        >>> limpiar_texto("texto\\r\\ncon\\tsaltos")
        'texto con saltos'
    """
    if texto is None:
        return ""

    # Reemplazar \r por espacio y luego colapsar todos los espacios múltiples
    resultado = re.sub(r"\s+", " ", str(texto).replace("\r", " "))
    return resultado.strip()


def normalizar_texto(texto: str | None) -> str:
    """Normaliza el texto a minúsculas ASCII sin acentos.

    Útil para comparaciones case-insensitive y accent-insensitive, o para
    generar identificadores seguros.

    Args:
        texto: Texto a normalizar (puede ser None)

    Returns:
        Texto normalizado en minúsculas ASCII sin acentos

    Example:
        >>> normalizar_texto("JOSÉ García")
        'jose garcia'
        >>> normalizar_texto("Número: 123")
        'numero: 123'
        >>> normalizar_texto(None)
        ''
        >>> normalizar_texto("  CAFÉ  ")
        'cafe'
    """
    texto_limpio = limpiar_texto(texto)
    if not texto_limpio:
        return ""

    # Normalizar a NFD (descomponer caracteres acentuados)
    # Codificar a ASCII ignorando caracteres no-ASCII (elimina acentos)
    # Decodificar de vuelta a UTF-8
    return (
        unicodedata.normalize("NFKD", texto_limpio.lower())
        .encode("ascii", "ignore")
        .decode("utf-8")
    )


def normalizar_numero_expediente(
    valor: object,
    *,
    valor_por_defecto: str = "expediente",
) -> str:
    """Convierte un número de expediente en un nombre seguro para rutas.

    Reemplaza todos los caracteres que no sean letras, números, guiones o
    guiones bajos por guiones bajos. Útil para crear nombres de archivo o
    directorios a partir de números de expediente.

    Args:
        valor: Número de expediente (cualquier objeto convertible a string)
        valor_por_defecto: Valor a usar si el input es None o vacío

    Returns:
        String seguro para usar en nombres de archivo/directorio

    Example:
        >>> normalizar_numero_expediente("FPA-000632/2017")
        'FPA-000632_2017'
        >>> normalizar_numero_expediente("Expediente N° 123")
        'Expediente_N___123'
        >>> normalizar_numero_expediente(None)
        'expediente'
        >>> normalizar_numero_expediente("")
        'expediente'
    """
    if valor is None:
        numero = valor_por_defecto
    else:
        numero = limpiar_texto(str(valor))
        if not numero:
            numero = valor_por_defecto

    # Reemplazar caracteres no-word (excepto guiones) por guión bajo
    return re.sub(r"[^\w-]", "_", numero)


def descomponer_numero_expediente(
    valor: str | None,
) -> tuple[str | None, str | None, str | None]:
    """Obtiene jurisdicción, número y año desde una cadena de expediente.

    Soporta múltiples formatos comunes del PJN:
    - Con prefijos alfabéticos: "FPA 21002641/2010"
    - Con jurisdicción: "3-21002641-23"
    - Con incidentes: "21002641/2010/I" (los incidentes se ignoran)

    Los incidentes (sufijos como /I, /CA1, /1) se ignoran. Los años de dos o
    tres dígitos se expanden a cuatro cuando es posible.

    Args:
        valor: Número de expediente completo (puede ser None)

    Returns:
        Tupla (jurisdiccion, numero, anio) donde cada componente puede ser None

    Example:
        >>> descomponer_numero_expediente("FPA 21002641/2010")
        (None, '21002641', '2010')
        >>> descomponer_numero_expediente("3-21002641-23")
        ('3', '21002641', '2023')
        >>> descomponer_numero_expediente("21002641/2010/I")
        (None, '21002641', '2010')
        >>> descomponer_numero_expediente("123/24")
        (None, '123', '2024')
        >>> descomponer_numero_expediente(None)
        (None, None, None)
    """
    if not valor:
        return None, None, None

    texto = limpiar_texto(str(valor))
    if not texto:
        return None, None, None

    # Remover prefijo alfabético si existe
    texto = re.sub(r"^[^0-9]+", "", texto)
    if not texto:
        return None, None, None

    # Remover espacios
    texto = re.sub(r"\s+", "", texto)

    # Remover incidentes (sufijos como /I, /CA1, /1, etc.)
    texto = _remover_incidentes(texto)

    # Extraer todos los bloques numéricos
    bloques = re.findall(r"\d+", texto)
    if not bloques:
        return None, None, None

    jurisdiccion: str | None = None
    numero: str | None = None
    anio: str | None = None

    # Interpretar bloques según cantidad
    if len(bloques) >= 3:
        # Formato: jurisdiccion-numero-anio
        jurisdiccion, numero, anio = bloques[-3], bloques[-2], bloques[-1]
    elif len(bloques) == 2:
        # Formato: numero/anio
        numero, anio = bloques
    elif len(bloques) == 1:
        # Solo número
        numero = bloques[0]

    numero = numero or None
    anio = _expandir_anio(anio) if anio else None

    return jurisdiccion, numero, anio


def _remover_incidentes(cadena: str) -> str:
    """Remueve sufijos de incidentes de un número de expediente.

    Los incidentes son sufijos como /I, /CA1, /1, etc. que indican incidentes
    o actuaciones derivadas del expediente principal.

    Args:
        cadena: Número de expediente que puede contener incidentes

    Returns:
        Número de expediente sin sufijos de incidentes

    Example:
        >>> _remover_incidentes("21002641/2010/I")
        '21002641/2010'
        >>> _remover_incidentes("21002641/2010/CA1")
        '21002641/2010'
        >>> _remover_incidentes("21002641/2010/I/2")
        '21002641/2010'
    """
    while True:
        # Buscar sufijo /XXX al final (letras o números)
        match = re.search(r"/(?:[A-Za-z]+[A-Za-z0-9]*|\d+)$", cadena)
        if not match:
            break

        # Si no hay otra barra antes del sufijo, es parte del número principal
        if cadena[: match.start()].count("/") == 0:
            break

        # Remover el sufijo
        cadena = cadena[: match.start()]

    # Remover también sufijos con guión (ej: -CA1, -I)
    return re.sub(r"(?:[-][A-Za-z]+[A-Za-z0-9]*)+$", "", cadena)


def _expandir_anio(anio: str | None) -> str | None:
    """Convierte un componente de año de 1-3 dígitos en un año de 4 dígitos.

    Intenta determinar el año completo basándose en el año actual. Por ejemplo,
    "23" podría expandirse a "2023" si estamos en 2024 o posterior.

    Args:
        anio: String con 1-3 dígitos representando un año

    Returns:
        String con 4 dígitos del año, o None si no se puede expandir

    Example:
        >>> _expandir_anio("23")  # Si estamos en 2024+
        '2023'
        >>> _expandir_anio("2010")
        '2010'
        >>> _expandir_anio("5")
        '2005'
        >>> _expandir_anio(None)
        None
    """
    if not anio:
        return None

    # Extraer solo dígitos
    digitos = re.sub(r"\D", "", anio)
    if not digitos:
        return None

    # Si ya tiene 4+ dígitos, tomar los últimos 4
    if len(digitos) >= 4:
        return digitos[-4:]

    # Intentar expandir basándose en el año actual
    from datetime import datetime

    sufijo = digitos
    sufijo_len = len(sufijo)
    actual = datetime.now().year
    sufijo_normalizado = sufijo.zfill(sufijo_len)

    # Buscar el año más reciente que termine en ese sufijo
    for year in range(actual + 1, 1899, -1):
        if str(year).endswith(sufijo_normalizado):
            return f"{year:04d}"

    # Si no se encuentra, rellenar con ceros
    return sufijo.zfill(4)[-4:]
