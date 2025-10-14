"""Modelos de dominio compartidos para interactuar con el portal del PJN."""
from .actuacion import Actuacion, ActuacionesArchivo
from .entrada import Entrada
from .expediente import ExpedienteIdentificacion, ExpedienteResumen

__all__ = [
    "Actuacion",
    "ActuacionesArchivo",
    "Entrada",
    "ExpedienteIdentificacion",
    "ExpedienteResumen",
]
