"""
Módulo de autenticación para servidor MCP.

Proporciona gestión de tokens Bearer para acceso remoto seguro
y rate limiting para prevenir abuso.
"""

from .token_manager import TokenManager, Token
from .rate_limiter import RateLimiter

__all__ = ["TokenManager", "Token", "RateLimiter"]
