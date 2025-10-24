"""Tests para el scheduler del monitor.

Este módulo prueba la lógica de scheduling y determinación de intervalos.
Nota: Tests de ejecución async completa están en test_monitor_integration.py
"""

import pytest
from datetime import datetime, time
from unittest.mock import Mock, patch, AsyncMock

from configuracion.monitor import MonitorConfig
from pjn.monitor.core import MonitorPJN
from pjn.monitor.scheduler import SchedulerMonitor


class TestSchedulerMonitor:
    """Tests para la clase SchedulerMonitor."""

    @pytest.fixture
    def monitor_mock(self):
        """Fixture con monitor mockeado."""
        config = MonitorConfig(
            modo="automatico",
            intervalos_laboral_expedientes=15,
            intervalos_laboral_entradas=10,
            intervalos_no_laboral_expedientes=60,
            intervalos_no_laboral_entradas=30,
            dias_laborales=["lunes", "martes", "miercoles", "jueves", "viernes"],
            hora_inicio="08:00",
            hora_fin="18:00"
        )
        monitor = Mock(spec=MonitorPJN)
        monitor.config = config
        monitor.estado = Mock()
        monitor.estado.errores_consecutivos_entradas = 0
        monitor.estado.errores_consecutivos_expedientes = 0
        return monitor

    @pytest.fixture
    def scheduler(self, monitor_mock):
        """Fixture con scheduler."""
        return SchedulerMonitor(monitor_mock)

    # =========================================================================
    # Tests de inicialización
    # =========================================================================

    def test_scheduler_init(self, scheduler, monitor_mock):
        """Scheduler se inicializa correctamente."""
        assert scheduler.monitor == monitor_mock
        assert scheduler.config == monitor_mock.config
        assert scheduler.scheduler is not None
        assert scheduler.job_entradas is None
        assert scheduler.job_expedientes is None

    # =========================================================================
    # Tests de _es_horario_laboral()
    # =========================================================================

    def test_es_horario_laboral_modo_laboral_siempre_true(self, monitor_mock):
        """Modo 'laboral' siempre retorna True."""
        monitor_mock.config.modo = "laboral"
        scheduler = SchedulerMonitor(monitor_mock)

        # Independiente de la hora real
        assert scheduler._es_horario_laboral() is True

    def test_es_horario_laboral_modo_no_laboral_siempre_false(self, monitor_mock):
        """Modo 'no_laboral' siempre retorna False."""
        monitor_mock.config.modo = "no_laboral"
        scheduler = SchedulerMonitor(monitor_mock)

        assert scheduler._es_horario_laboral() is False

    def test_es_horario_laboral_modo_automatico_dia_laboral(self, monitor_mock):
        """Modo 'automatico' verifica día y hora correctamente."""
        monitor_mock.config.modo = "automatico"
        scheduler = SchedulerMonitor(monitor_mock)

        # Simular lunes a las 10:00
        with patch("pjn.monitor.scheduler.datetime") as mock_datetime:
            mock_now = Mock()
            mock_now.weekday.return_value = 0  # Lunes
            mock_now.time.return_value = time(10, 0)  # 10:00
            mock_datetime.now.return_value = mock_now
            mock_datetime.strptime = datetime.strptime

            result = scheduler._es_horario_laboral()

            # Es lunes entre 08:00 y 18:00
            assert result is True

    def test_es_horario_laboral_modo_automatico_dia_no_laboral(self, monitor_mock):
        """Modo 'automatico' retorna False en sábado/domingo."""
        monitor_mock.config.modo = "automatico"
        scheduler = SchedulerMonitor(monitor_mock)

        # Simular sábado a las 10:00
        with patch("pjn.monitor.scheduler.datetime") as mock_datetime:
            mock_now = Mock()
            mock_now.weekday.return_value = 5  # Sábado
            mock_now.time.return_value = time(10, 0)
            mock_datetime.now.return_value = mock_now

            result = scheduler._es_horario_laboral()

            # Sábado no es laboral
            assert result is False

    def test_es_horario_laboral_modo_automatico_fuera_de_horario(self, monitor_mock):
        """Modo 'automatico' retorna False fuera del horario laboral."""
        monitor_mock.config.modo = "automatico"
        scheduler = SchedulerMonitor(monitor_mock)

        # Simular lunes a las 20:00 (fuera de horario)
        with patch("pjn.monitor.scheduler.datetime") as mock_datetime:
            mock_now = Mock()
            mock_now.weekday.return_value = 0  # Lunes
            mock_now.time.return_value = time(20, 0)  # 20:00
            mock_datetime.now.return_value = mock_now
            mock_datetime.strptime = datetime.strptime

            result = scheduler._es_horario_laboral()

            # Lunes pero después de las 18:00
            assert result is False

    def test_es_horario_laboral_modo_automatico_antes_de_horario(self, monitor_mock):
        """Modo 'automatico' retorna False antes del horario laboral."""
        monitor_mock.config.modo = "automatico"
        scheduler = SchedulerMonitor(monitor_mock)

        # Simular lunes a las 07:00 (antes de horario)
        with patch("pjn.monitor.scheduler.datetime") as mock_datetime:
            mock_now = Mock()
            mock_now.weekday.return_value = 0  # Lunes
            mock_now.time.return_value = time(7, 0)  # 07:00
            mock_datetime.now.return_value = mock_now
            mock_datetime.strptime = datetime.strptime

            result = scheduler._es_horario_laboral()

            # Lunes pero antes de las 08:00
            assert result is False

    def test_es_horario_laboral_error_parseando_hora_retorna_false(self, monitor_mock):
        """_es_horario_laboral() retorna False si error parseando horas."""
        monitor_mock.config.modo = "automatico"
        monitor_mock.config.hora_inicio = "invalid"  # Hora inválida
        scheduler = SchedulerMonitor(monitor_mock)

        # Debe retornar False por error
        result = scheduler._es_horario_laboral()
        assert result is False

    # =========================================================================
    # Tests de _calcular_intervalo_entradas()
    # =========================================================================

    def test_calcular_intervalo_entradas_horario_laboral(self, scheduler):
        """Intervalo de entradas en horario laboral."""
        with patch.object(scheduler, "_es_horario_laboral", return_value=True):
            intervalo = scheduler._calcular_intervalo_entradas()
            assert intervalo == 10  # intervalos_laboral_entradas

    def test_calcular_intervalo_entradas_horario_no_laboral(self, scheduler):
        """Intervalo de entradas fuera de horario laboral."""
        with patch.object(scheduler, "_es_horario_laboral", return_value=False):
            intervalo = scheduler._calcular_intervalo_entradas()
            assert intervalo == 30  # intervalos_no_laboral_entradas

    # =========================================================================
    # Tests de _calcular_intervalo_expedientes()
    # =========================================================================

    def test_calcular_intervalo_expedientes_horario_laboral(self, scheduler):
        """Intervalo de expedientes en horario laboral."""
        with patch.object(scheduler, "_es_horario_laboral", return_value=True):
            intervalo = scheduler._calcular_intervalo_expedientes()
            assert intervalo == 15  # intervalos_laboral_expedientes

    def test_calcular_intervalo_expedientes_horario_no_laboral(self, scheduler):
        """Intervalo de expedientes fuera de horario laboral."""
        with patch.object(scheduler, "_es_horario_laboral", return_value=False):
            intervalo = scheduler._calcular_intervalo_expedientes()
            assert intervalo == 60  # intervalos_no_laboral_expedientes

    # =========================================================================
    # Tests de _job_verificar_entradas() - Manejo de errores
    # =========================================================================

    @pytest.mark.asyncio
    async def test_job_verificar_entradas_exitoso(self, scheduler, monitor_mock):
        """_job_verificar_entradas() llama al monitor correctamente."""
        monitor_mock.verificar_entradas = AsyncMock(return_value=[])

        await scheduler._job_verificar_entradas()

        # Verificar que llamó al monitor
        monitor_mock.verificar_entradas.assert_called_once()

    @pytest.mark.asyncio
    async def test_job_verificar_entradas_con_lock_ocupado(self, scheduler, monitor_mock):
        """_job_verificar_entradas() omite ejecución si lock ocupado."""
        monitor_mock.verificar_entradas = AsyncMock()

        # Adquirir el lock manualmente
        await scheduler._lock_entradas.acquire()

        try:
            # Intentar ejecutar job (debe salir temprano)
            await scheduler._job_verificar_entradas()

            # No debe haber llamado al monitor
            monitor_mock.verificar_entradas.assert_not_called()
        finally:
            scheduler._lock_entradas.release()

    @pytest.mark.asyncio
    async def test_job_verificar_entradas_maneja_excepciones(self, scheduler, monitor_mock):
        """_job_verificar_entradas() captura excepciones del monitor."""
        from pjn.monitor.exceptions import NetworkError

        monitor_mock.verificar_entradas = AsyncMock(side_effect=NetworkError("Timeout"))

        # No debe lanzar excepción hacia afuera
        await scheduler._job_verificar_entradas()

        # Verificó que se llamó al monitor
        monitor_mock.verificar_entradas.assert_called_once()

    # =========================================================================
    # Tests de _job_verificar_expedientes() - Manejo de errores
    # =========================================================================

    @pytest.mark.asyncio
    async def test_job_verificar_expedientes_exitoso(self, scheduler, monitor_mock):
        """_job_verificar_expedientes() llama al monitor correctamente."""
        monitor_mock.verificar_expedientes = AsyncMock(return_value=[])

        await scheduler._job_verificar_expedientes()

        monitor_mock.verificar_expedientes.assert_called_once()

    @pytest.mark.asyncio
    async def test_job_verificar_expedientes_con_lock_ocupado(self, scheduler, monitor_mock):
        """_job_verificar_expedientes() omite ejecución si lock ocupado."""
        monitor_mock.verificar_expedientes = AsyncMock()

        await scheduler._lock_expedientes.acquire()

        try:
            await scheduler._job_verificar_expedientes()
            monitor_mock.verificar_expedientes.assert_not_called()
        finally:
            scheduler._lock_expedientes.release()

    @pytest.mark.asyncio
    async def test_job_verificar_expedientes_maneja_excepciones(self, scheduler, monitor_mock):
        """_job_verificar_expedientes() captura excepciones del monitor."""
        from pjn.monitor.exceptions import AuthenticationError

        monitor_mock.verificar_expedientes = AsyncMock(
            side_effect=AuthenticationError("Auth failed")
        )

        await scheduler._job_verificar_expedientes()

        monitor_mock.verificar_expedientes.assert_called_once()

    # =========================================================================
    # Tests de edge cases
    # =========================================================================

    def test_scheduler_con_config_custom(self):
        """Scheduler funciona con configuración personalizada."""
        config = MonitorConfig(
            modo="laboral",
            intervalos_laboral_expedientes=5,
            intervalos_laboral_entradas=3
        )
        monitor = Mock(spec=MonitorPJN)
        monitor.config = config
        monitor.estado = Mock()
        monitor.estado.errores_consecutivos_entradas = 0

        scheduler = SchedulerMonitor(monitor)

        # Verificar que usa la config correcta
        assert scheduler.config.intervalos_laboral_expedientes == 5
        assert scheduler.config.intervalos_laboral_entradas == 3

    def test_dias_laborales_customizables(self, monitor_mock):
        """Días laborales se pueden personalizar."""
        monitor_mock.config.dias_laborales = ["lunes", "miercoles"]
        scheduler = SchedulerMonitor(monitor_mock)

        # Simular martes (no laboral ahora)
        with patch("pjn.monitor.scheduler.datetime") as mock_datetime:
            mock_now = Mock()
            mock_now.weekday.return_value = 1  # Martes
            mock_now.time.return_value = time(10, 0)
            mock_datetime.now.return_value = mock_now

            result = scheduler._es_horario_laboral()

            # Martes no está en días laborales
            assert result is False

    def test_horario_laboral_limite_inicio(self, monitor_mock):
        """Hora exacta de inicio cuenta como laboral."""
        monitor_mock.config.modo = "automatico"
        scheduler = SchedulerMonitor(monitor_mock)

        # Exactamente 08:00
        with patch("pjn.monitor.scheduler.datetime") as mock_datetime:
            mock_now = Mock()
            mock_now.weekday.return_value = 0  # Lunes
            mock_now.time.return_value = time(8, 0)  # 08:00 exacto
            mock_datetime.now.return_value = mock_now
            mock_datetime.strptime = datetime.strptime

            result = scheduler._es_horario_laboral()

            # 08:00 está incluido (<=)
            assert result is True

    def test_horario_laboral_limite_fin(self, monitor_mock):
        """Hora exacta de fin cuenta como laboral."""
        monitor_mock.config.modo = "automatico"
        scheduler = SchedulerMonitor(monitor_mock)

        # Exactamente 18:00
        with patch("pjn.monitor.scheduler.datetime") as mock_datetime:
            mock_now = Mock()
            mock_now.weekday.return_value = 0  # Lunes
            mock_now.time.return_value = time(18, 0)  # 18:00 exacto
            mock_datetime.now.return_value = mock_now
            mock_datetime.strptime = datetime.strptime

            result = scheduler._es_horario_laboral()

            # 18:00 está incluido (<=)
            assert result is True
