"""Utilidades para gestionar estructuras de directorios compartidas."""

from .expedientes import (
    ESTRUCTURA_POR_DEFECTO,
    GestorDirectoriosExpedientes,
    inicializar_directorio_base,
)

__all__ = [
    "ESTRUCTURA_POR_DEFECTO",
    "GestorDirectoriosExpedientes",
    "inicializar_directorio_base",
]
