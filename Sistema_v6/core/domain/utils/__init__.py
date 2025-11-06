"""Utils module - Funciones puras de utilidad.

Contiene funciones auxiliares reutilizables sin side effects:
- text.py: Normalización y limpieza de texto
- dates.py: Normalización de fechas
- hashing.py: Generación de hashes
- coercion.py: Coerción de tipos
"""

from .coercion import coerce_bool, coerce_int, coerce_str, get_first
from .dates import (
    es_fecha_valida,
    formatear_fecha,
    normalizar_fecha,
    parsear_fecha,
)
from .hashing import (
    generar_hash_actuacion,
    generar_hash_archivo,
    generar_hash_contenido,
    generar_hash_identificador,
    verificar_hash,
)
from .text import (
    descomponer_numero_expediente,
    limpiar_texto,
    normalizar_numero_expediente,
    normalizar_texto,
)

__all__ = [
    # Coercion
    "coerce_bool",
    "coerce_int",
    "coerce_str",
    "get_first",
    # Text
    "descomponer_numero_expediente",
    "limpiar_texto",
    "normalizar_numero_expediente",
    "normalizar_texto",
    # Dates
    "es_fecha_valida",
    "formatear_fecha",
    "normalizar_fecha",
    "parsear_fecha",
    # Hashing
    "generar_hash_actuacion",
    "generar_hash_archivo",
    "generar_hash_contenido",
    "generar_hash_identificador",
    "verificar_hash",
]
