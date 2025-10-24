"""Circuit breaker para prevenir cascadas de errores.

Este módulo implementa el patrón Circuit Breaker para proteger
el monitor de fallos en cascada cuando el portal PJN no responde.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Any

from ..utils.logging import get_logger
from .exceptions import SchedulerError

logger = get_logger(__name__)


class CircuitState(Enum):
    """Estados posibles del circuit breaker."""
    CLOSED = "closed"      # Funcionamiento normal
    OPEN = "open"          # Circuito abierto, rechaza llamadas
    HALF_OPEN = "half_open"  # Prueba de recuperación


@dataclass
class CircuitBreakerConfig:
    """Configuración del circuit breaker.

    Attributes:
        failure_threshold: Número de fallos consecutivos antes de abrir
        success_threshold: Número de éxitos en half-open antes de cerrar
        timeout: Segundos que el circuito permanece abierto
        expected_exception: Tipo de excepción que cuenta como fallo
    """
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout: int = 60  # segundos
    expected_exception: type = Exception


class CircuitBreaker:
    """Implementación del patrón Circuit Breaker.

    El circuit breaker tiene tres estados:
    - CLOSED: Funcionamiento normal, todas las llamadas pasan
    - OPEN: Circuito abierto, rechaza todas las llamadas
    - HALF_OPEN: Permite algunas llamadas para probar recuperación

    Transiciones:
    - CLOSED → OPEN: Cuando se alcanzan failure_threshold fallos consecutivos
    - OPEN → HALF_OPEN: Después de timeout segundos
    - HALF_OPEN → CLOSED: Cuando se alcanzan success_threshold éxitos
    - HALF_OPEN → OPEN: Si falla una llamada de prueba
    """

    def __init__(self, config: CircuitBreakerConfig | None = None):
        """Inicializa el circuit breaker.

        Args:
            config: Configuración del circuit breaker
        """
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: datetime | None = None
        self.last_state_change: datetime = datetime.now()

        logger.info(
            f"CircuitBreaker inicializado - "
            f"failure_threshold={self.config.failure_threshold}, "
            f"timeout={self.config.timeout}s"
        )

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Ejecuta una función protegida por el circuit breaker.

        Args:
            func: Función a ejecutar
            *args: Argumentos posicionales
            **kwargs: Argumentos con nombre

        Returns:
            Resultado de la función

        Raises:
            SchedulerError: Si el circuito está abierto
            Exception: Si la función falla
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info("Circuit breaker: Intentando recuperación (HALF_OPEN)")
                self._transition_to_half_open()
            else:
                # Calcular tiempo restante
                time_since_failure = (
                    datetime.now() - self.last_failure_time
                ).total_seconds() if self.last_failure_time else 0
                remaining = max(0, self.config.timeout - time_since_failure)

                logger.warning(
                    f"Circuit breaker OPEN - Rechazando llamada "
                    f"(reintento en {remaining:.0f}s)"
                )
                raise SchedulerError(
                    f"Circuit breaker está abierto. "
                    f"Demasiados fallos consecutivos ({self.failure_count}). "
                    f"Reintentando en {remaining:.0f} segundos."
                )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exception as e:
            self._on_failure()
            raise

    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """Versión asíncrona de call().

        Args:
            func: Función async a ejecutar
            *args: Argumentos posicionales
            **kwargs: Argumentos con nombre

        Returns:
            Resultado de la función

        Raises:
            SchedulerError: Si el circuito está abierto
            Exception: Si la función falla
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info("Circuit breaker: Intentando recuperación (HALF_OPEN)")
                self._transition_to_half_open()
            else:
                time_since_failure = (
                    datetime.now() - self.last_failure_time
                ).total_seconds() if self.last_failure_time else 0
                remaining = max(0, self.config.timeout - time_since_failure)

                logger.warning(
                    f"Circuit breaker OPEN - Rechazando llamada "
                    f"(reintento en {remaining:.0f}s)"
                )
                raise SchedulerError(
                    f"Circuit breaker está abierto. "
                    f"Demasiados fallos consecutivos ({self.failure_count}). "
                    f"Reintentando en {remaining:.0f} segundos."
                )

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exception as e:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        """Maneja un éxito de la función."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            logger.debug(
                f"Circuit breaker: Éxito en HALF_OPEN "
                f"({self.success_count}/{self.config.success_threshold})"
            )

            if self.success_count >= self.config.success_threshold:
                logger.info("Circuit breaker: Recuperado, cerrando circuito")
                self._transition_to_closed()

        elif self.state == CircuitState.CLOSED:
            # Reset failure count en estado normal
            if self.failure_count > 0:
                logger.debug(f"Circuit breaker: Reseteando contador de fallos")
                self.failure_count = 0

    def _on_failure(self) -> None:
        """Maneja un fallo de la función."""
        self.last_failure_time = datetime.now()

        if self.state == CircuitState.HALF_OPEN:
            logger.warning("Circuit breaker: Fallo en HALF_OPEN, reabriendo circuito")
            self._transition_to_open()

        elif self.state == CircuitState.CLOSED:
            self.failure_count += 1
            logger.warning(
                f"Circuit breaker: Fallo registrado "
                f"({self.failure_count}/{self.config.failure_threshold})"
            )

            if self.failure_count >= self.config.failure_threshold:
                logger.error(
                    f"Circuit breaker: Umbral de fallos alcanzado, "
                    f"abriendo circuito"
                )
                self._transition_to_open()

    def _should_attempt_reset(self) -> bool:
        """Determina si se debe intentar recuperación.

        Returns:
            bool: True si ha pasado el timeout desde el último fallo
        """
        if self.last_failure_time is None:
            return False

        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.config.timeout

    def _transition_to_closed(self) -> None:
        """Transiciona a estado CLOSED."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_state_change = datetime.now()
        logger.info("Circuit breaker: CLOSED")

    def _transition_to_open(self) -> None:
        """Transiciona a estado OPEN."""
        self.state = CircuitState.OPEN
        self.success_count = 0
        self.last_state_change = datetime.now()
        logger.warning(
            f"Circuit breaker: OPEN - "
            f"Bloqueando llamadas por {self.config.timeout}s"
        )

    def _transition_to_half_open(self) -> None:
        """Transiciona a estado HALF_OPEN."""
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        self.failure_count = 0
        self.last_state_change = datetime.now()
        logger.info("Circuit breaker: HALF_OPEN - Probando recuperación")

    def reset(self) -> None:
        """Resetea manualmente el circuit breaker a estado CLOSED.

        Útil para testing o intervención manual.
        """
        logger.info("Circuit breaker: Reset manual")
        self._transition_to_closed()

    def get_stats(self) -> dict[str, Any]:
        """Obtiene estadísticas del circuit breaker.

        Returns:
            dict: Estadísticas actuales
        """
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_state_change": self.last_state_change.isoformat(),
            "time_in_current_state": (datetime.now() - self.last_state_change).total_seconds(),
        }


class ExponentialBackoff:
    """Implementa backoff exponencial para reintentos.

    Calcula tiempos de espera crecientes entre reintentos:
    - Intento 1: base_delay segundos
    - Intento 2: base_delay * 2 segundos
    - Intento 3: base_delay * 4 segundos
    - etc.

    Con un máximo de max_delay segundos.
    """

    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        multiplier: float = 2.0
    ):
        """Inicializa el backoff exponencial.

        Args:
            base_delay: Delay inicial en segundos
            max_delay: Delay máximo en segundos
            multiplier: Factor de multiplicación
        """
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.attempt = 0

    def get_delay(self) -> float:
        """Calcula el delay para el intento actual.

        Returns:
            float: Segundos a esperar
        """
        delay = self.base_delay * (self.multiplier ** self.attempt)
        return min(delay, self.max_delay)

    def wait(self) -> None:
        """Espera el tiempo calculado y aumenta el contador.

        Útil para usar en loops de reintento.
        """
        delay = self.get_delay()
        logger.debug(f"Backoff: Esperando {delay:.1f}s (intento {self.attempt + 1})")
        time.sleep(delay)
        self.attempt += 1

    def reset(self) -> None:
        """Resetea el contador de intentos."""
        self.attempt = 0


__all__ = [
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitState",
    "ExponentialBackoff",
]
