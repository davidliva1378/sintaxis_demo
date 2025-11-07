"""Scraping adapters."""

from . import parsers
from .pagination import (
    DEFAULT_PAGINATION_STRATEGY,
    PaginationStrategy,
    PrimeFacesPaginationStrategy,
)
from .playwright_scraper_adapter import PlaywrightScraperAdapter
from .session_manager import SessionManager, obtener_sesion_autenticada
from .expedientes_batch_extractor import extraer_expedientes

__all__ = [
    "PlaywrightScraperAdapter",
    "SessionManager",
    "obtener_sesion_autenticada",
    "PaginationStrategy",
    "PrimeFacesPaginationStrategy",
    "DEFAULT_PAGINATION_STRATEGY",
    "parsers",
    "extraer_expedientes",
]
