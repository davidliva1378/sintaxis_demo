"""Modelos de dominio compartidos para interactuar con el portal del PJN."""
from .actuacion import Actuacion, ActuacionesArchivo
from .entrada import Entrada
from .expediente import ExpedienteIdentificacion, ExpedienteResumen
from .extraccion_config import ExtraccionExpedientesConfig

__all__ = [
    "Actuacion",
    "ActuacionesArchivo",
    "Entrada",
    "ExpedienteIdentificacion",
    "ExpedienteResumen",
    "ExtraccionExpedientesConfig",
]
