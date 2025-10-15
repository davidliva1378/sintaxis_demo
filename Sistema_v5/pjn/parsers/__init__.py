"""Parsers para transformar HTML del PJN en modelos de dominio."""

from .actuaciones_parser import (
    construir_actuaciones_archivo,
    construir_encabezado_actuaciones,
    construir_nombre_archivo_normalizado,
    normalizar_nombre_expediente,
    obtener_extension_valida,
    parse_actuacion_row,
    EXTENSIONES_GENERICAS,
)
from .expedientes_parser import parse_expediente_resumen
from .entradas_parser import parse_entrada

__all__ = [
    "construir_actuaciones_archivo",
    "construir_encabezado_actuaciones",
    "construir_nombre_archivo_normalizado",
    "normalizar_nombre_expediente",
    "obtener_extension_valida",
    "parse_actuacion_row",
    "EXTENSIONES_GENERICAS",
    "parse_expediente_resumen",
    "parse_entrada",
]
