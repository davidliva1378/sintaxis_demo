"""
Rate Limiter para servidor MCP SSE.

Limita el número de requests por IP/token para prevenir abuso.
Usa algoritmo de Token Bucket en memoria.
"""

import time
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class TokenBucket:
    """Token Bucket para rate limiting."""

    capacity: int  # Máximo de tokens
    refill_rate: float  # Tokens por segundo
    tokens: float = field(default=0)
    last_refill: float = field(default_factory=time.time)

    def __post_init__(self):
        self.tokens = float(self.capacity)

    def consume(self, tokens: int = 1) -> bool:
        """
        Intenta consumir tokens.

        Args:
            tokens: Número de tokens a consumir

        Returns:
            True si se pudieron consumir, False si no hay suficientes
        """
        now = time.time()
        elapsed = now - self.last_refill

        # Refill tokens
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.refill_rate
        )
        self.last_refill = now

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def time_until_available(self, tokens: int = 1) -> float:
        """Calcula segundos hasta que haya tokens disponibles."""
        if self.tokens >= tokens:
            return 0
        needed = tokens - self.tokens
        return needed / self.refill_rate


class RateLimiter:
    """
    Rate limiter con soporte para múltiples claves (IP, token).

    Características:
    - Límites por IP
    - Límites por token (más permisivo para autenticados)
    - Whitelist de IPs
    - Cleanup automático de buckets viejos
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_minute_authenticated: int = 120,
        burst_size: int = 10,
        cleanup_interval: int = 300
    ):
        """
        Inicializa el rate limiter.

        Args:
            requests_per_minute: Límite por minuto para IPs no autenticadas
            requests_per_minute_authenticated: Límite para tokens autenticados
            burst_size: Tamaño máximo de ráfaga permitido
            cleanup_interval: Segundos entre limpiezas de buckets
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_minute_auth = requests_per_minute_authenticated
        self.burst_size = burst_size
        self.cleanup_interval = cleanup_interval

        self._buckets: Dict[str, TokenBucket] = {}
        self._lock = Lock()
        self._last_cleanup = time.time()

        # Whitelist de IPs (localhost siempre permitido)
        self.ip_whitelist = {"127.0.0.1", "::1", "localhost"}

        logger.info(
            f"RateLimiter inicializado: {requests_per_minute}/min (anon), "
            f"{requests_per_minute_authenticated}/min (auth)"
        )

    def _get_bucket(self, key: str, authenticated: bool = False) -> TokenBucket:
        """Obtiene o crea un bucket para la clave."""
        if key not in self._buckets:
            rpm = self.requests_per_minute_auth if authenticated else self.requests_per_minute
            refill_rate = rpm / 60.0  # Tokens por segundo

            self._buckets[key] = TokenBucket(
                capacity=self.burst_size,
                refill_rate=refill_rate
            )
        return self._buckets[key]

    def _cleanup(self):
        """Limpia buckets inactivos."""
        now = time.time()
        if now - self._last_cleanup < self.cleanup_interval:
            return

        with self._lock:
            # Eliminar buckets sin uso en los últimos 5 minutos
            cutoff = now - 300
            keys_to_delete = [
                key for key, bucket in self._buckets.items()
                if bucket.last_refill < cutoff
            ]
            for key in keys_to_delete:
                del self._buckets[key]

            if keys_to_delete:
                logger.debug(f"Limpiados {len(keys_to_delete)} buckets inactivos")

            self._last_cleanup = now

    def is_allowed(
        self,
        ip: str,
        token_name: Optional[str] = None
    ) -> Tuple[bool, Optional[float]]:
        """
        Verifica si un request está permitido.

        Args:
            ip: IP del cliente
            token_name: Nombre del token (si autenticado)

        Returns:
            (allowed, retry_after) - retry_after es segundos hasta disponible
        """
        # Cleanup periódico
        self._cleanup()

        # Whitelist
        if ip in self.ip_whitelist:
            return True, None

        # Determinar clave y si es autenticado
        if token_name:
            key = f"token:{token_name}"
            authenticated = True
        else:
            key = f"ip:{ip}"
            authenticated = False

        with self._lock:
            bucket = self._get_bucket(key, authenticated)

            if bucket.consume(1):
                return True, None
            else:
                retry_after = bucket.time_until_available(1)
                logger.warning(
                    f"Rate limit excedido para {key}: "
                    f"retry_after={retry_after:.1f}s"
                )
                return False, retry_after

    def add_to_whitelist(self, ip: str):
        """Agrega una IP a la whitelist."""
        self.ip_whitelist.add(ip)
        logger.info(f"IP agregada a whitelist: {ip}")

    def remove_from_whitelist(self, ip: str):
        """Remueve una IP de la whitelist."""
        self.ip_whitelist.discard(ip)
        logger.info(f"IP removida de whitelist: {ip}")

    def get_stats(self) -> dict:
        """Obtiene estadísticas del rate limiter."""
        with self._lock:
            return {
                "active_buckets": len(self._buckets),
                "ip_whitelist_size": len(self.ip_whitelist),
                "requests_per_minute": self.requests_per_minute,
                "requests_per_minute_auth": self.requests_per_minute_auth,
                "burst_size": self.burst_size
            }
