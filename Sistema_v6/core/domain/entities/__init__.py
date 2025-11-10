"""Entities module - Entidades del dominio.

Contiene los modelos de negocio principales del sistema:
- expediente.py: ExpedienteResumen, ExpedienteIdentificacion
- entrada.py: Entrada (notificaciones/despachos)
- actuacion.py: Actuacion, ActuacionesArchivo
- estado.py: EstadoExpediente
"""

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
