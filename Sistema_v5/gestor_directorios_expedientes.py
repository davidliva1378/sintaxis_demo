"""Compatibilidad retro: reexporta el gestor de expedientes desde el nuevo paquete."""

from .gestor_directorios.expedientes import (  # noqa: F401
    ESTRUCTURA_POR_DEFECTO,
    GestorDirectoriosExpedientes,
)

__all__ = ["ESTRUCTURA_POR_DEFECTO", "GestorDirectoriosExpedientes"]
