"""Parsers para datos del portal PJN.

Este módulo contiene parsers especializados para convertir datos HTML
del portal PJN en objetos del dominio.

Módulos:
    - expedientes_parser: Parser para listados de expedientes
    - entradas_parser: Parser para bandeja de entradas/notificaciones
    - actuaciones_parser: Parser complejo para actuaciones judiciales
"""

from .actuaciones_parser import (
    construir_actuaciones_archivo,
    construir_encabezado_actuaciones,
    construir_nombre_archivo_normalizado,
    generar_hash_archivo,
    limpiar_texto_actuacion,
    normalizar_fecha_actuacion,
    normalizar_nombre_expediente,
    obtener_extension_valida,
    parse_actuacion_row,
)
from .entradas_parser import deduplicar_historial, parse_entrada
from .expedientes_parser import parse_expediente_resumen

__all__ = [
    # Expedientes
    "parse_expediente_resumen",
    # Entradas
    "parse_entrada",
    "deduplicar_historial",
    # Actuaciones
    "parse_actuacion_row",
    "construir_actuaciones_archivo",
    "construir_encabezado_actuaciones",
    "construir_nombre_archivo_normalizado",
    "normalizar_nombre_expediente",
    "obtener_extension_valida",
    "generar_hash_archivo",
    "limpiar_texto_actuacion",
    "normalizar_fecha_actuacion",
]
