"""Modelos del módulo pjn.

Re-exporta modelos desde el dominio principal.
"""

from __future__ import annotations

from Sistema_v6.core.domain.entities.expediente import ExpedienteResumen
from .actuacion import Actuacion, ActuacionesArchivo

__all__ = [
    "ExpedienteResumen",
    "Actuacion",
    "ActuacionesArchivo",
]