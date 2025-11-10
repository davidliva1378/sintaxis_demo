"""
Routers REST API para Sistema v6.
"""

from .extraccion_masiva import router as extraccion_masiva_router

__all__ = ["extraccion_masiva_router"]
