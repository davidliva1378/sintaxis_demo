"""Monitor Scheduler Service.

Servicio de programación continua de monitoreo de expedientes y entradas.
Basado en Sistema_v5/pjn/monitor/scheduler.py con mejoras.

Características:
- APScheduler para ejecución periódica
- Diferenciación horario laboral/no laboral
- Intervalos configurables por tipo de monitoreo
- Manejo de estado (activo/pausado)
- Lock para prevenir ejecuciones simultáneas
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, time
from pathlib import Path
from typing import TYPE_CHECKING

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

if TYPE_CHECKING:
    from application.dtos import MonitorearExpedientesCommand
    from application.use_cases import MonitorearExpedientesUseCase
    from application.services.monitoreo_service import MonitoreoService
    from infrastructure.config import MonitoreoSettings

logger = logging.getLogger(__name__)


class MonitorSchedulerService:
    """Servicio de programación continua de monitoreo.

    Gestiona la ejecución periódica del monitoreo de expedientes
    con diferenciación entre horario laboral y no laboral.

    Example:
        >>> scheduler = MonitorSchedulerService(
        ...     monitorear_use_case=use_case,
        ...     config=settings.monitoreo,
        ...     json_sistema_path=Path("data/expedientes_sistema.json"),
        ...     workspaces_dir=Path("workspaces")
        ... )
        >>> await scheduler.start()
        >>> # ... el monitoreo se ejecuta automáticamente
        >>> await scheduler.stop()
    """

    def __init__(
        self,
        monitorear_use_case: MonitorearExpedientesUseCase,
        config: MonitoreoSettings,
        json_sistema_path: Path,
        workspaces_dir: Path,
        monitoreo_service: "MonitoreoService | None" = None,
    ):
        """Inicializa el servicio de scheduler.

        Args:
            monitorear_use_case: Use case de monitoreo de expedientes
            config: Configuración de monitoreo
            json_sistema_path: Ruta al JSON sistema
            workspaces_dir: Directorio base de workspaces
            monitoreo_service: Servicio de monitoreo para registrar cambios (opcional)
        """
        self._use_case = monitorear_use_case
        self._config = config
        self._json_sistema_path = json_sistema_path
        self._workspaces_dir = workspaces_dir
        self._monitoreo_service = monitoreo_service

        # Scheduler
        self.scheduler = AsyncIOScheduler()
        self._activo = False
        self._ejecutando = False  # Lock para prevenir ejecuciones simultáneas

        # Jobs programados
        self._job_expedientes = None

        logger.info("MonitorSchedulerService inicializado")

    async def start(self) -> None:
        """Inicia el scheduler y programa los jobs de monitoreo.

        Raises:
            RuntimeError: Si el scheduler ya está activo
        """
        if self._activo:
            raise RuntimeError("Scheduler ya está activo")

        logger.info("Iniciando MonitorSchedulerService...")

        # Iniciar scheduler
        self.scheduler.start()
        self._activo = True

        # Programar job de expedientes si está habilitado
        if self._config.verificar_expedientes:
            await self._programar_expedientes()

        logger.info("MonitorSchedulerService iniciado correctamente")

    async def stop(self) -> None:
        """Detiene el scheduler y limpia los jobs.

        Espera a que termine cualquier ejecución en curso.
        """
        if not self._activo:
            logger.warning("Scheduler ya está detenido")
            return

        logger.info("Deteniendo MonitorSchedulerService...")

        # Esperar a que termine ejecución actual
        if self._ejecutando:
            logger.info("Esperando a que termine la ejecución actual...")
            max_wait = 60  # segundos
            waited = 0
            while self._ejecutando and waited < max_wait:
                await asyncio.sleep(1)
                waited += 1

            if self._ejecutando:
                logger.warning(
                    f"Ejecución aún en curso después de {max_wait}s, forzando detención"
                )

        # Detener scheduler
        self.scheduler.shutdown(wait=True)
        self._activo = False
        self._job_expedientes = None

        logger.info("MonitorSchedulerService detenido")

    async def _programar_expedientes(self) -> None:
        """Programa el job de monitoreo de expedientes.

        Usa intervalos configurables según horario laboral/no laboral.
        """
        # Obtener intervalo actual
        intervalo_minutos = self._obtener_intervalo_actual_expedientes()

        if intervalo_minutos is None:
            logger.warning(
                "No se configuró intervalo para expedientes, usando 15 minutos por defecto"
            )
            intervalo_minutos = 15

        # Crear trigger con intervalo
        trigger = IntervalTrigger(minutes=intervalo_minutos)

        # Programar job
        self._job_expedientes = self.scheduler.add_job(
            self._ejecutar_verificacion_expedientes,
            trigger=trigger,
            id="monitoreo_expedientes",
            name="Monitoreo de Expedientes",
            replace_existing=True,
        )

        logger.info(
            f"Job de expedientes programado: cada {intervalo_minutos} minutos "
            f"(horario {'laboral' if self._es_horario_laboral() else 'no laboral'})"
        )

    async def _ejecutar_verificacion_expedientes(self) -> None:
        """Ejecuta la verificación de expedientes (callback del scheduler).

        Usa lock para prevenir ejecuciones simultáneas.
        """
        if self._ejecutando:
            logger.warning("Verificación ya en curso, saltando esta ejecución")
            return

        self._ejecutando = True
        inicio = datetime.now()

        try:
            logger.info("=== Ejecutando verificación programada de expedientes ===")

            # Crear comando
            from application.dtos import MonitorearExpedientesCommand

            command = MonitorearExpedientesCommand(
                json_sistema=self._json_sistema_path,
                base_path=self._workspaces_dir,
                notificar_cambios=self._config.notificar_cambios,
                descargar_nuevos_archivos=self._config.descargar_archivos,
                headless=True,  # Scheduler siempre usa headless
                # Opciones de extracción
                fecha_corte_dias=self._config.fecha_corte_dias,
                max_paginas=self._config.max_paginas_monitoreo,
                tiempo_maximo_segundos=self._config.tiempo_maximo_extraccion,
                detener_en_duplicado=self._config.detener_en_duplicado,
                orden_extraccion=self._config.orden_extraccion,
            )

            # Ejecutar use case
            resultado = await self._use_case.execute(command)

            # Log resultado
            duracion = (datetime.now() - inicio).total_seconds()

            if resultado.success:
                response = resultado.value
                logger.info(
                    f"Verificación completada en {duracion:.2f}s: "
                    f"{response.total_cambios} cambios detectados, "
                    f"{response.expedientes_verificados} expedientes verificados"
                )

                # Registrar cambios en la base de datos si hay servicio disponible
                if self._monitoreo_service and response.cambios_detectados:
                    logger.info(f"Registrando {len(response.cambios_detectados)} cambios en la base de datos")
                    for cambio in response.cambios_detectados:
                        try:
                            detalles = cambio.datos_adicionales if hasattr(cambio, 'datos_adicionales') else {}

                            # Verificar si el expediente existe en monitoreo, si no, crearlo
                            try:
                                self._monitoreo_service.registrar_cambio(
                                    usuario_id=1,
                                    expediente_numero=cambio.numero_expediente,
                                    tipo_cambio=cambio.tipo,
                                    descripcion=cambio.descripcion,
                                    detalles=detalles,
                                )
                            except ValueError as ve:
                                # El expediente no existe en monitoreo, crearlo automáticamente
                                if "no está siendo monitoreado" in str(ve):
                                    logger.info(f"Creando expediente {cambio.numero_expediente} en monitoreo automáticamente")
                                    caratula = getattr(cambio, 'caratula', '') or detalles.get('caratula', '')
                                    dependencia = getattr(cambio, 'dependencia', '') or detalles.get('dependencia', '')

                                    self._monitoreo_service.agregar_expediente(
                                        usuario_id=1,
                                        expediente_numero=cambio.numero_expediente,
                                        expediente_caratula=caratula,
                                        expediente_dependencia=dependencia,
                                    )

                                    # Ahora sí registrar el cambio
                                    self._monitoreo_service.registrar_cambio(
                                        usuario_id=1,
                                        expediente_numero=cambio.numero_expediente,
                                        tipo_cambio=cambio.tipo,
                                        descripcion=cambio.descripcion,
                                        detalles=detalles,
                                    )
                                else:
                                    raise

                            logger.debug(f"Cambio registrado: {cambio.numero_expediente} - {cambio.tipo}")
                        except Exception as e:
                            logger.error(f"Error al registrar cambio {cambio.numero_expediente}: {e}")
            else:
                logger.error(
                    f"Error en verificación (duración: {duracion:.2f}s): "
                    f"{resultado.error}"
                )

            # Re-programar si cambió el intervalo (horario laboral <-> no laboral)
            await self._verificar_y_actualizar_intervalo()

        except Exception as e:
            duracion = (datetime.now() - inicio).total_seconds()
            logger.error(
                f"Excepción en verificación (duración: {duracion:.2f}s): {e}",
                exc_info=True,
            )

        finally:
            self._ejecutando = False

    async def _verificar_y_actualizar_intervalo(self) -> None:
        """Verifica si el intervalo actual debe cambiar y re-programa si es necesario.

        Esto permite cambiar automáticamente entre horario laboral y no laboral.
        """
        if self._job_expedientes is None:
            return

        # Obtener intervalo actual configurado en el job
        intervalo_actual_job = None
        if self._job_expedientes.trigger and hasattr(self._job_expedientes.trigger, "interval"):
            intervalo_actual_job = int(
                self._job_expedientes.trigger.interval.total_seconds() / 60
            )

        # Obtener intervalo que debería tener según horario
        intervalo_esperado = self._obtener_intervalo_actual_expedientes()

        # Si son diferentes, re-programar
        if intervalo_esperado and intervalo_actual_job != intervalo_esperado:
            logger.info(
                f"Cambio de horario detectado: {intervalo_actual_job} min → {intervalo_esperado} min"
            )
            self.scheduler.remove_job("monitoreo_expedientes")
            await self._programar_expedientes()

    def _obtener_intervalo_actual_expedientes(self) -> int | None:
        """Obtiene el intervalo de expedientes según horario actual.

        Returns:
            Intervalo en minutos, o None si no está configurado
        """
        if self._es_horario_laboral():
            return self._config.intervalos_laboral_expedientes
        else:
            return self._config.intervalos_no_laboral_expedientes

    def _es_horario_laboral(self) -> bool:
        """Determina si la hora actual está en horario laboral.

        Returns:
            True si es horario laboral, False en caso contrario
        """
        ahora = datetime.now()

        # Verificar día de la semana
        dias_semana = [
            "lunes",
            "martes",
            "miercoles",
            "jueves",
            "viernes",
            "sabado",
            "domingo",
        ]
        dia_actual = dias_semana[ahora.weekday()]

        if dia_actual not in self._config.dias_laborales:
            return False

        # Verificar hora
        try:
            hora_inicio = time.fromisoformat(self._config.hora_inicio)
            hora_fin = time.fromisoformat(self._config.hora_fin)
            hora_actual = ahora.time()

            # Detectar si el horario cruza la medianoche
            if hora_inicio <= hora_fin:
                # Horario normal en el mismo día (ej: 08:00 - 18:00)
                return hora_inicio <= hora_actual <= hora_fin
            else:
                # Cruce de medianoche (ej: 22:00 - 06:00, o 06:00 - 05:59 para casi 24h)
                # En este caso, es horario laboral si:
                # - La hora actual es >= hora_inicio (después de las 22:00)
                # - O la hora actual es <= hora_fin (antes de las 06:00)
                return hora_actual >= hora_inicio or hora_actual <= hora_fin

        except ValueError as e:
            logger.error(f"Error al parsear horas de configuración: {e}")
            # Por defecto, considerar horario laboral
            return True

    def obtener_estado(self) -> dict:
        """Obtiene el estado actual del scheduler.

        Returns:
            Diccionario con información del estado:
            - activo: Si el scheduler está corriendo
            - ejecutando: Si hay una verificación en curso
            - intervalo_actual_minutos: Intervalo actual de expedientes
            - es_horario_laboral: Si está en horario laboral
            - proxima_ejecucion: Timestamp de la próxima ejecución (si aplica)
            - jobs_programados: Número de jobs programados
        """
        estado = {
            "activo": self._activo,
            "ejecutando": self._ejecutando,
            "intervalo_actual_minutos": self._obtener_intervalo_actual_expedientes(),
            "es_horario_laboral": self._es_horario_laboral(),
            "proxima_ejecucion": None,
            "jobs_programados": len(self.scheduler.get_jobs()) if self._activo else 0,
        }

        # Obtener próxima ejecución si hay job programado
        if self._job_expedientes and self._job_expedientes.next_run_time:
            estado["proxima_ejecucion"] = self._job_expedientes.next_run_time.isoformat()

        return estado

    async def ejecutar_verificacion_manual(self, headless: bool = True) -> dict:
        """Ejecuta una verificación manual inmediata.

        No afecta el scheduling automático.

        Args:
            headless: Si True, ejecuta el navegador sin interfaz gráfica.
                      Si False, muestra el navegador para depuración visual.

        Returns:
            Resultado de la verificación
        """
        logger.info(f"Ejecutando verificación manual (headless={headless})...")

        # Crear comando
        from application.dtos import MonitorearExpedientesCommand

        command = MonitorearExpedientesCommand(
            json_sistema=self._json_sistema_path,
            base_path=self._workspaces_dir,
            notificar_cambios=self._config.notificar_cambios,
            descargar_nuevos_archivos=self._config.descargar_archivos,
            headless=headless,
            # Opciones de extracción
            fecha_corte_dias=self._config.fecha_corte_dias,
            max_paginas=self._config.max_paginas_monitoreo,
            tiempo_maximo_segundos=self._config.tiempo_maximo_extraccion,
            detener_en_duplicado=self._config.detener_en_duplicado,
            orden_extraccion=self._config.orden_extraccion,
        )

        # Ejecutar use case
        resultado = await self._use_case.execute(command)

        if resultado.success:
            response = resultado.value

            # Registrar cambios en la base de datos si hay servicio disponible
            if self._monitoreo_service and response.cambios_detectados:
                logger.info(f"Registrando {len(response.cambios_detectados)} cambios en la base de datos")
                for cambio in response.cambios_detectados:
                    try:
                        # Preparar detalles JSON
                        detalles = cambio.datos_adicionales if hasattr(cambio, 'datos_adicionales') else {}

                        # Verificar si el expediente existe en monitoreo, si no, crearlo
                        try:
                            self._monitoreo_service.registrar_cambio(
                                usuario_id=1,
                                expediente_numero=cambio.numero_expediente,
                                tipo_cambio=cambio.tipo,
                                descripcion=cambio.descripcion,
                                detalles=detalles,
                            )
                        except ValueError as ve:
                            # El expediente no existe en monitoreo, crearlo automáticamente
                            if "no está siendo monitoreado" in str(ve):
                                logger.info(f"Creando expediente {cambio.numero_expediente} en monitoreo automáticamente")
                                caratula = getattr(cambio, 'caratula', '') or detalles.get('caratula', '')
                                dependencia = getattr(cambio, 'dependencia', '') or detalles.get('dependencia', '')

                                self._monitoreo_service.agregar_expediente(
                                    usuario_id=1,
                                    expediente_numero=cambio.numero_expediente,
                                    expediente_caratula=caratula,
                                    expediente_dependencia=dependencia,
                                )

                                # Ahora sí registrar el cambio
                                self._monitoreo_service.registrar_cambio(
                                    usuario_id=1,
                                    expediente_numero=cambio.numero_expediente,
                                    tipo_cambio=cambio.tipo,
                                    descripcion=cambio.descripcion,
                                    detalles=detalles,
                                )
                            else:
                                raise

                        logger.debug(f"Cambio registrado: {cambio.numero_expediente} - {cambio.tipo}")
                    except Exception as e:
                        logger.error(f"Error al registrar cambio {cambio.numero_expediente}: {e}")

            return {
                "exito": True,
                "cambios_detectados": response.total_cambios,
                "expedientes_verificados": response.expedientes_verificados,
                "notificaciones_enviadas": response.notificaciones_enviadas,
                "cambios": [
                    {
                        "numero_expediente": c.numero_expediente,
                        "tipo": c.tipo,
                        "descripcion": c.descripcion,
                    }
                    for c in response.cambios_detectados
                ],
            }
        else:
            return {
                "exito": False,
                "error": resultado.error,
                "error_code": resultado.error_code,
            }
