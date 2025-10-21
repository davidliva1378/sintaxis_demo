"""Servicios orquestadores para el módulo PJN."""

from .actuaciones import ResultadoProcesamiento, procesar_actuaciones_expediente

__all__ = ["procesar_actuaciones_expediente", "ResultadoProcesamiento"]
