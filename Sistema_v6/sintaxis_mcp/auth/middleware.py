"""
Middleware de autenticación para servidor MCP SSE.

Valida tokens Bearer en requests HTTP antes de procesar.
"""

import logging
from typing import Optional, Callable, Awaitable
from aiohttp import web

from .token_manager import TokenManager, Token

logger = logging.getLogger(__name__)


class AuthMiddleware:
    """
    Middleware de autenticación para aiohttp.

    Valida tokens Bearer en el header Authorization.
    Permite rutas públicas configurables (ej: /health).
    """

    def __init__(
        self,
        token_manager: TokenManager,
        public_paths: Optional[list[str]] = None,
        enabled: bool = True
    ):
        """
        Inicializa el middleware.

        Args:
            token_manager: Instancia de TokenManager
            public_paths: Rutas que no requieren autenticación
            enabled: Si False, permite todo el tráfico
        """
        self.token_manager = token_manager
        self.public_paths = public_paths or ["/health", "/"]
        self.enabled = enabled

    def _is_public_path(self, path: str) -> bool:
        """Verifica si la ruta es pública."""
        return any(
            path == public or path.startswith(f"{public}/")
            for public in self.public_paths
        )

    def _extract_token(self, request: web.Request) -> Optional[str]:
        """Extrae token del header Authorization."""
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]
        return None

    @web.middleware
    async def middleware(
        self,
        request: web.Request,
        handler: Callable[[web.Request], Awaitable[web.Response]]
    ) -> web.Response:
        """
        Middleware principal de autenticación.

        Args:
            request: Request HTTP
            handler: Handler del siguiente middleware/endpoint

        Returns:
            Response HTTP
        """
        # Si está deshabilitado, continuar
        if not self.enabled:
            return await handler(request)

        # Rutas públicas
        if self._is_public_path(request.path):
            return await handler(request)

        # Extraer y validar token
        token_str = self._extract_token(request)
        if not token_str:
            logger.warning(f"Request sin token: {request.method} {request.path}")
            return web.json_response(
                {"error": "Authorization header required", "code": "AUTH_REQUIRED"},
                status=401
            )

        token = self.token_manager.validate_token(token_str)
        if not token:
            logger.warning(f"Token inválido: {request.method} {request.path}")
            return web.json_response(
                {"error": "Invalid or expired token", "code": "INVALID_TOKEN"},
                status=401
            )

        # Guardar token en request para uso posterior
        request["auth_token"] = token
        request["auth_token_name"] = token.name

        logger.debug(f"Request autenticado: {token.name} -> {request.method} {request.path}")
        return await handler(request)


def create_auth_middleware(
    token_manager: TokenManager,
    public_paths: Optional[list[str]] = None,
    enabled: bool = True
) -> web.middleware:
    """
    Factory para crear middleware de autenticación.

    Args:
        token_manager: Instancia de TokenManager
        public_paths: Rutas públicas
        enabled: Si está habilitado

    Returns:
        Middleware configurado
    """
    auth = AuthMiddleware(token_manager, public_paths, enabled)
    return auth.middleware


def get_current_token(request: web.Request) -> Optional[Token]:
    """
    Obtiene el token del request actual.

    Args:
        request: Request HTTP

    Returns:
        Token o None si no autenticado
    """
    return request.get("auth_token")


def require_permission(permission: str):
    """
    Decorador para requerir un permiso específico.

    Usage:
        @require_permission("tools:execute")
        async def handle_call_tool(request):
            ...
    """
    def decorator(handler):
        async def wrapper(request: web.Request) -> web.Response:
            token = get_current_token(request)
            if not token:
                return web.json_response(
                    {"error": "Authentication required", "code": "AUTH_REQUIRED"},
                    status=401
                )

            # Verificar permiso usando TokenManager
            token_manager: TokenManager = request.app.get("token_manager")
            if token_manager and not token_manager.has_permission(token, permission):
                logger.warning(f"Permiso denegado: {token.name} no tiene '{permission}'")
                return web.json_response(
                    {"error": f"Permission denied: {permission}", "code": "PERMISSION_DENIED"},
                    status=403
                )

            return await handler(request)
        return wrapper
    return decorator
