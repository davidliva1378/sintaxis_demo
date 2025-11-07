"""API Routers - FastAPI routers for different resources."""

from . import (
    auth,
    config,
    expedientes,
    # extraccion_masiva,  # Temporalmente deshabilitado
    health,
    monitoreo,
    workspaces,
)

__all__ = [
    "auth",
    "config",
    "expedientes",
    # "extraccion_masiva",  # Temporalmente deshabilitado
    "health",
    "monitoreo",
    "workspaces",
]
