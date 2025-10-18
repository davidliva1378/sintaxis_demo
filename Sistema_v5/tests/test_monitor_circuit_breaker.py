"""Tests para el circuit breaker del monitor.

Este módulo prueba el patrón Circuit Breaker y backoff exponencial.
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

from pjn.monitor.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    ExponentialBackoff,
)
from pjn.monitor.exceptions import SchedulerError


class TestCircuitBreaker:
    """Tests para la clase CircuitBreaker."""

    # =========================================================================
    # Tests de inicialización y configuración
    # =========================================================================

    def test_circuit_breaker_init_default(self):
        """Circuit breaker se inicializa con configuración por defecto."""
        cb = CircuitBreaker()

        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.success_count == 0
        assert cb.config.failure_threshold == 5
        assert cb.config.timeout == 60

    def test_circuit_breaker_init_custom_config(self):
        """Circuit breaker acepta configuración personalizada."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=2,
            timeout=30
        )
        cb = CircuitBreaker(config)

        assert cb.config.failure_threshold == 3
        assert cb.config.success_threshold == 2
        assert cb.config.timeout == 30

    # =========================================================================
    # Tests de transiciones de estado
    # =========================================================================

    def test_circuit_closed_to_open_on_failures(self):
        """Circuit breaker abre después de alcanzar umbral de fallos."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker(config)

        failing_func = Mock(side_effect=Exception("Fallo"))

        # Ejecutar 3 fallos
        for _ in range(3):
            with pytest.raises(Exception):
                cb.call(failing_func)

        # Debe estar OPEN
        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 3

    def test_circuit_open_rejects_calls(self):
        """Circuit breaker abierto rechaza llamadas."""
        config = CircuitBreakerConfig(failure_threshold=2, timeout=60)
        cb = CircuitBreaker(config)

        failing_func = Mock(side_effect=Exception("Fallo"))

        # Provocar apertura
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(failing_func)

        assert cb.state == CircuitState.OPEN

        # Intentar otra llamada - debe ser rechazada
        with pytest.raises(SchedulerError, match="Circuit breaker está abierto"):
            cb.call(Mock())

    def test_circuit_open_to_half_open_after_timeout(self):
        """Circuit breaker pasa a HALF_OPEN después del timeout."""
        config = CircuitBreakerConfig(failure_threshold=2, timeout=1)  # 1 segundo
        cb = CircuitBreaker(config)

        failing_func = Mock(side_effect=Exception("Fallo"))

        # Provocar apertura
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(failing_func)

        assert cb.state == CircuitState.OPEN

        # Esperar timeout
        time.sleep(1.1)

        # Siguiente llamada debe intentar recuperación
        success_func = Mock(return_value="success")
        result = cb.call(success_func)

        assert cb.state == CircuitState.HALF_OPEN
        assert result == "success"

    def test_circuit_half_open_to_closed_on_success(self):
        """Circuit breaker cierra después de éxitos en HALF_OPEN."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            success_threshold=2,
            timeout=1
        )
        cb = CircuitBreaker(config)

        # Provocar apertura
        failing_func = Mock(side_effect=Exception("Fallo"))
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(failing_func)

        assert cb.state == CircuitState.OPEN

        # Esperar timeout
        time.sleep(1.1)

        # Dos éxitos consecutivos para cerrar
        success_func = Mock(return_value="success")
        cb.call(success_func)
        assert cb.state == CircuitState.HALF_OPEN

        cb.call(success_func)
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_circuit_half_open_to_open_on_failure(self):
        """Circuit breaker vuelve a OPEN si falla en HALF_OPEN."""
        config = CircuitBreakerConfig(failure_threshold=2, timeout=1)
        cb = CircuitBreaker(config)

        # Provocar apertura
        failing_func = Mock(side_effect=Exception("Fallo"))
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(failing_func)

        # Esperar timeout
        time.sleep(1.1)

        # Primera llamada entra en HALF_OPEN
        success_func = Mock(return_value="success")
        cb.call(success_func)
        assert cb.state == CircuitState.HALF_OPEN

        # Fallo vuelve a abrir
        with pytest.raises(Exception):
            cb.call(failing_func)

        assert cb.state == CircuitState.OPEN

    # =========================================================================
    # Tests de call_async
    # =========================================================================

    @pytest.mark.asyncio
    async def test_circuit_call_async_success(self):
        """call_async() ejecuta función async correctamente."""
        cb = CircuitBreaker()

        async_func = AsyncMock(return_value="async_result")
        result = await cb.call_async(async_func)

        assert result == "async_result"
        async_func.assert_called_once()

    @pytest.mark.asyncio
    async def test_circuit_call_async_failures(self):
        """call_async() maneja fallos correctamente."""
        config = CircuitBreakerConfig(failure_threshold=2)
        cb = CircuitBreaker(config)

        async_fail = AsyncMock(side_effect=Exception("Async fallo"))

        # Dos fallos para abrir
        for _ in range(2):
            with pytest.raises(Exception):
                await cb.call_async(async_fail)

        assert cb.state == CircuitState.OPEN

    # =========================================================================
    # Tests de reset manual
    # =========================================================================

    def test_circuit_manual_reset(self):
        """reset() cierra el circuito manualmente."""
        config = CircuitBreakerConfig(failure_threshold=2)
        cb = CircuitBreaker(config)

        # Abrir circuito
        failing_func = Mock(side_effect=Exception("Fallo"))
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(failing_func)

        assert cb.state == CircuitState.OPEN

        # Reset manual
        cb.reset()

        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.success_count == 0

    # =========================================================================
    # Tests de estadísticas
    # =========================================================================

    def test_circuit_get_stats(self):
        """get_stats() retorna estadísticas correctas."""
        cb = CircuitBreaker()

        stats = cb.get_stats()

        assert stats["state"] == "closed"
        assert stats["failure_count"] == 0
        assert stats["success_count"] == 0
        assert "last_failure_time" in stats
        assert "last_state_change" in stats
        assert "time_in_current_state" in stats

    def test_circuit_stats_after_failures(self):
        """get_stats() refleja fallos acumulados."""
        config = CircuitBreakerConfig(failure_threshold=5)
        cb = CircuitBreaker(config)

        failing_func = Mock(side_effect=Exception("Fallo"))

        # 3 fallos (no alcanza threshold)
        for _ in range(3):
            with pytest.raises(Exception):
                cb.call(failing_func)

        stats = cb.get_stats()

        assert stats["state"] == "closed"  # Aún cerrado
        assert stats["failure_count"] == 3
        assert stats["last_failure_time"] is not None

    # =========================================================================
    # Tests de edge cases
    # =========================================================================

    def test_circuit_reset_failure_count_on_success(self):
        """Éxito en CLOSED resetea contador de fallos."""
        config = CircuitBreakerConfig(failure_threshold=5)
        cb = CircuitBreaker(config)

        failing_func = Mock(side_effect=Exception("Fallo"))
        success_func = Mock(return_value="ok")

        # 2 fallos
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(failing_func)

        assert cb.failure_count == 2

        # 1 éxito resetea
        cb.call(success_func)

        assert cb.failure_count == 0

    def test_circuit_multiple_calls_in_closed(self):
        """Múltiples llamadas exitosas en CLOSED."""
        cb = CircuitBreaker()

        success_func = Mock(return_value="ok")

        for _ in range(10):
            result = cb.call(success_func)
            assert result == "ok"

        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0


class TestExponentialBackoff:
    """Tests para la clase ExponentialBackoff."""

    # =========================================================================
    # Tests de cálculo de delays
    # =========================================================================

    def test_backoff_init_default(self):
        """Backoff se inicializa con valores por defecto."""
        backoff = ExponentialBackoff()

        assert backoff.base_delay == 1.0
        assert backoff.max_delay == 60.0
        assert backoff.multiplier == 2.0
        assert backoff.attempt == 0

    def test_backoff_get_delay_increases(self):
        """get_delay() incrementa exponencialmente."""
        backoff = ExponentialBackoff(base_delay=1.0)

        # Intento 0: 1.0 * 2^0 = 1.0
        assert backoff.get_delay() == 1.0

        backoff.attempt = 1
        # Intento 1: 1.0 * 2^1 = 2.0
        assert backoff.get_delay() == 2.0

        backoff.attempt = 2
        # Intento 2: 1.0 * 2^2 = 4.0
        assert backoff.get_delay() == 4.0

        backoff.attempt = 3
        # Intento 3: 1.0 * 2^3 = 8.0
        assert backoff.get_delay() == 8.0

    def test_backoff_respects_max_delay(self):
        """get_delay() no excede max_delay."""
        backoff = ExponentialBackoff(base_delay=10.0, max_delay=50.0)

        backoff.attempt = 10  # 10 * 2^10 = 10240, pero max es 50
        delay = backoff.get_delay()

        assert delay == 50.0

    def test_backoff_custom_multiplier(self):
        """Backoff funciona con multiplicador custom."""
        backoff = ExponentialBackoff(base_delay=1.0, multiplier=3.0)

        assert backoff.get_delay() == 1.0

        backoff.attempt = 1
        # 1.0 * 3^1 = 3.0
        assert backoff.get_delay() == 3.0

        backoff.attempt = 2
        # 1.0 * 3^2 = 9.0
        assert backoff.get_delay() == 9.0

    def test_backoff_wait_increments_attempt(self):
        """wait() incrementa el contador de intentos."""
        backoff = ExponentialBackoff(base_delay=0.01, max_delay=1.0)

        assert backoff.attempt == 0

        backoff.wait()  # Muy corto para testing
        assert backoff.attempt == 1

        backoff.wait()
        assert backoff.attempt == 2

    def test_backoff_reset(self):
        """reset() vuelve el contador a 0."""
        backoff = ExponentialBackoff()

        backoff.attempt = 5
        assert backoff.attempt == 5

        backoff.reset()
        assert backoff.attempt == 0

    # =========================================================================
    # Tests de edge cases
    # =========================================================================

    def test_backoff_zero_base_delay(self):
        """Backoff con base_delay = 0 siempre retorna 0."""
        backoff = ExponentialBackoff(base_delay=0.0)

        for attempt in range(10):
            backoff.attempt = attempt
            assert backoff.get_delay() == 0.0

    def test_backoff_fractional_delays(self):
        """Backoff maneja delays fraccionarios."""
        backoff = ExponentialBackoff(base_delay=0.5, max_delay=10.0)

        assert backoff.get_delay() == 0.5

        backoff.attempt = 1
        assert backoff.get_delay() == 1.0

        backoff.attempt = 2
        assert backoff.get_delay() == 2.0
