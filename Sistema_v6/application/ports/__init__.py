"""Ports - Interfaces que define la Application Layer.

Este paquete contiene todas las interfaces (contratos) que la capa de aplicación
define para comunicarse con la capa de infraestructura.

Siguiendo el Principio de Inversión de Dependencias (DIP), las dependencias
apuntan hacia adentro: la aplicación define las interfaces y la infraestructura
las implementa.

Módulos:
- repositories.py: Interfaces de repositorios para persistencia
- services.py: Interfaces de servicios externos (scraping, storage, notificaciones)
"""

from .repositories import (
    IActuacionRepository,
    IEntradaRepository,
    IExpedienteRepository,
)
from .services import (
    INotificacionPort,
    IScraperPort,
    IStoragePort,
    IWorkspacePort,
)

__all__ = [
    # Repositories
    "IExpedienteRepository",
    "IActuacionRepository",
    "IEntradaRepository",
    # Services
    "IScraperPort",
    "IStoragePort",
    "INotificacionPort",
    "IWorkspacePort",
]
