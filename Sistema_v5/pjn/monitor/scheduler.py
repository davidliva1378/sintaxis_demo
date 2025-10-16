"""Scheduler inteligente para el monitor PJN.

Este módulo gestiona la programación de verificaciones periódicas,
adaptando los intervalos según horario laboral y configuración.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import TYPE_CHECKING

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from ..utils.logging import get_logger

if TYPE_CHECKING:
    from .core import MonitorPJN
    from .config import MonitorConfig

logger = get_logger(__name__)

# Mapeo de nombres de días en español a números (0=lunes, 6=domingo)
DIAS_SEMANA = {
    "lunes": 0,
    "martes": 1,
    "miercoles": 2,
    "jueves": 3,
    "viernes": 4,
    "sabado": 5,
    "domingo": 6,
}


class SchedulerMonitor:
    """Gestiona scheduling inteligente del monitor.

    Este scheduler:
    - Determina si estamos en horario laboral
    - Calcula intervalos apropiados según configuración
    - Programa jobs periódicos para entradas y expedientes
    - Maneja los modos: automático, laboral, no_laboral
    """

    def __init__(self, monitor: MonitorPJN):
        """Inicializa el scheduler.

        Args:
            monitor: Instancia del monitor a programar
        """
        self.monitor = monitor
        self.config: MonitorConfig = monitor.config
        self.scheduler = AsyncIOScheduler()

        # Jobs programados (para poder reconfigurar dinámicamente)
        self.job_entradas = None
        self.job_expedientes = None

        logger.info("Scheduler inicializado")

    def _es_horario_laboral(self) -> bool:
        """Determina si estamos en horario laboral según configuración.

        Returns:
            bool: True si estamos en horario laboral

        """
        # Si modo no es automático, no importa el horario real
        if self.config.modo == "laboral":
            return True
        elif self.config.modo == "no_laboral":
            return False

        # Modo automático: verificar día y hora
        ahora = datetime.now()

        # Verificar día de la semana
        dia_actual = ahora.weekday()  # 0=lunes, 6=domingo
        dias_laborales_numeros = [
            DIAS_SEMANA.get(dia.lower(), -1)
            for dia in self.config.dias_laborales
        ]

        if dia_actual not in dias_laborales_numeros:
            return False

        # Verificar hora
        try:
            hora_inicio = datetime.strptime(self.config.hora_inicio, "%H:%M").time()
            hora_fin = datetime.strptime(self.config.hora_fin, "%H:%M").time()
            hora_actual = ahora.time()

            return hora_inicio <= hora_actual <= hora_fin

        except ValueError as e:
            logger.error(f"Error al parsear horas de configuración: {e}")
            # Fallback: considerar como no laboral
            return False

    def _calcular_intervalo_entradas(self) -> int:
        """Calcula el intervalo en minutos para verificar entradas.

        Returns:
            int: Intervalo en minutos
        """
        if self._es_horario_laboral():
            intervalo = self.config.intervalos_laboral_entradas
            logger.debug(f"Intervalo entradas (laboral): {intervalo} min")
            return intervalo
        else:
            intervalo = self.config.intervalos_no_laboral_entradas
            logger.debug(f"Intervalo entradas (no laboral): {intervalo} min")
            return intervalo

    def _calcular_intervalo_expedientes(self) -> int:
        """Calcula el intervalo en minutos para verificar expedientes.

        Returns:
            int: Intervalo en minutos
        """
        if self._es_horario_laboral():
            intervalo = self.config.intervalos_laboral_expedientes
            logger.debug(f"Intervalo expedientes (laboral): {intervalo} min")
            return intervalo
        else:
            intervalo = self.config.intervalos_no_laboral_expedientes
            logger.debug(f"Intervalo expedientes (no laboral): {intervalo} min")
            return intervalo

    async def _job_verificar_entradas(self):
        """Job wrapper para verificar entradas con manejo de errores."""
        try:
            logger.info("🔄 Ejecutando verificación de entradas...")
            nuevas = await self.monitor.verificar_entradas()

            if nuevas:
                logger.info(f"✅ Verificación completada - {len(nuevas)} nuevas entradas")
            else:
                logger.info("✅ Verificación completada - sin nuevas entradas")

        except Exception as e:
            logger.error(f"❌ Error en job de verificación de entradas: {e}", exc_info=True)

            # Si hay demasiados errores consecutivos, considerar detener
            if self.monitor.estado.errores_consecutivos_entradas >= self.config.max_reintentos_entradas:
                logger.critical(
                    f"⚠️ Máximo de errores consecutivos alcanzado para entradas "
                    f"({self.config.max_reintentos_entradas})"
                )

    async def _job_verificar_expedientes(self):
        """Job wrapper para verificar expedientes con manejo de errores."""
        try:
            logger.info("🔄 Ejecutando verificación de expedientes...")
            cambios = await self.monitor.verificar_expedientes()

            if cambios:
                logger.info(f"✅ Verificación completada - {len(cambios)} expedientes con cambios")
            else:
                logger.info("✅ Verificación completada - sin cambios en expedientes")

        except Exception as e:
            logger.error(f"❌ Error en job de verificación de expedientes: {e}", exc_info=True)

            # Si hay demasiados errores consecutivos, considerar detener
            if self.monitor.estado.errores_consecutivos_expedientes >= self.config.max_reintentos_expedientes:
                logger.critical(
                    f"⚠️ Máximo de errores consecutivos alcanzado para expedientes "
                    f"({self.config.max_reintentos_expedientes})"
                )

    def iniciar(self) -> None:
        """Inicia el scheduler con los jobs programados.

        Programa:
        - Verificación de entradas con su intervalo correspondiente
        - Verificación de expedientes con su intervalo correspondiente
        """
        logger.info("Iniciando scheduler...")

        # Calcular intervalos iniciales
        intervalo_entradas = self._calcular_intervalo_entradas()
        intervalo_expedientes = self._calcular_intervalo_expedientes()

        # Programar job de entradas
        self.job_entradas = self.scheduler.add_job(
            self._job_verificar_entradas,
            trigger=IntervalTrigger(minutes=intervalo_entradas),
            id="verificar_entradas",
            name="Verificación de entradas PJN",
            replace_existing=True,
        )
        logger.info(f"✅ Job 'entradas' programado cada {intervalo_entradas} minutos")

        # Programar job de expedientes
        self.job_expedientes = self.scheduler.add_job(
            self._job_verificar_expedientes,
            trigger=IntervalTrigger(minutes=intervalo_expedientes),
            id="verificar_expedientes",
            name="Verificación de expedientes PJN",
            replace_existing=True,
        )
        logger.info(f"✅ Job 'expedientes' programado cada {intervalo_expedientes} minutos")

        # Si modo es automático, programar job para re-evaluar intervalos cada hora
        if self.config.modo == "automatico":
            self.scheduler.add_job(
                self._recalcular_intervalos,
                trigger=IntervalTrigger(hours=1),
                id="recalcular_intervalos",
                name="Re-evaluación de intervalos",
                replace_existing=True,
            )
            logger.info("✅ Job de re-evaluación de intervalos programado cada 1 hora")

        # Iniciar scheduler
        self.scheduler.start()
        logger.info("🚀 Scheduler iniciado exitosamente")

    def _recalcular_intervalos(self) -> None:
        """Re-evalúa los intervalos y reprograma jobs si es necesario.

        Este método se llama periódicamente en modo automático para
        ajustar los intervalos cuando cambiamos entre horario laboral
        y no laboral.
        """
        logger.debug("Re-evaluando intervalos...")

        # Calcular nuevos intervalos
        nuevo_intervalo_entradas = self._calcular_intervalo_entradas()
        nuevo_intervalo_expedientes = self._calcular_intervalo_expedientes()

        # Comparar con intervalos actuales
        intervalo_actual_entradas = self.job_entradas.trigger.interval.total_seconds() / 60
        intervalo_actual_expedientes = self.job_expedientes.trigger.interval.total_seconds() / 60

        # Reprogramar si cambió
        if nuevo_intervalo_entradas != intervalo_actual_entradas:
            logger.info(
                f"🔄 Cambiando intervalo de entradas: {intervalo_actual_entradas:.0f}min → {nuevo_intervalo_entradas}min"
            )
            self.scheduler.reschedule_job(
                "verificar_entradas",
                trigger=IntervalTrigger(minutes=nuevo_intervalo_entradas),
            )

        if nuevo_intervalo_expedientes != intervalo_actual_expedientes:
            logger.info(
                f"🔄 Cambiando intervalo de expedientes: {intervalo_actual_expedientes:.0f}min → {nuevo_intervalo_expedientes}min"
            )
            self.scheduler.reschedule_job(
                "verificar_expedientes",
                trigger=IntervalTrigger(minutes=nuevo_intervalo_expedientes),
            )

    def detener(self) -> None:
        """Detiene el scheduler y todos sus jobs."""
        logger.info("Deteniendo scheduler...")
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("✅ Scheduler detenido")
        else:
            logger.warning("Scheduler ya estaba detenido")

    async def ejecutar_verificacion_inmediata(self) -> None:
        """Ejecuta una verificación inmediata de entradas y expedientes.

        Útil para testing o para forzar una verificación manual.
        """
        logger.info("⚡ Ejecutando verificación inmediata...")

        # Ejecutar ambas verificaciones en paralelo
        resultados = await asyncio.gather(
            self._job_verificar_entradas(),
            self._job_verificar_expedientes(),
            return_exceptions=True
        )

        # Log de resultados
        for i, resultado in enumerate(resultados):
            nombre = "entradas" if i == 0 else "expedientes"
            if isinstance(resultado, Exception):
                logger.error(f"Error en verificación inmediata de {nombre}: {resultado}")

        logger.info("✅ Verificación inmediata completada")


__all__ = ["SchedulerMonitor"]
