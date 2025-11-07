"""Repository adapters."""

from .json_actuacion_repository import JsonActuacionRepository
from .json_entrada_repository import JsonEntradaRepository
from .json_expediente_repository import JsonExpedienteRepository

__all__ = [
    "JsonExpedienteRepository",
    "JsonActuacionRepository",
    "JsonEntradaRepository",
]
