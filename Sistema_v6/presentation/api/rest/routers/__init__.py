"""API Routers - FastAPI routers for different resources."""

from . import (
    auth,
    config,
    expedientes,
    extraccion_masiva,
    health,
    monitoreo,
    workspaces,
)

__all__ = [
    "auth",
    "config",
    "expedientes",
    "extraccion_masiva",
    "health",
    "monitoreo",
    "workspaces",
]
