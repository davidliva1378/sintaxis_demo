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
from typing import TYPE_CHECKING, Any

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
        notification_service: Any = None,
    ):
        """Inicializa el servicio de scheduler.

        Args:
            monitorear_use_case: Use case de monitoreo de expedientes
            config: Configuración de monitoreo
            json_sistema_path: Ruta al JSON sistema
            workspaces_dir: Directorio base de workspaces
            monitoreo_service: Servicio de monitoreo para registrar cambios (opcional)
            notification_service: Servicio de notificaciones (WebSocket) (opcional)
        """
        self._use_case = monitorear_use_case
        self._config = config
        self._json_sistema_path = json_sistema_path
        self._workspaces_dir = workspaces_dir
        self._monitoreo_service = monitoreo_service
        self._notification_service = notification_service

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
        if self._notification_service:
            await self._notification_service.broadcast({"type": "scheduler_status", "status": "started"})

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
        if self._notification_service:
            await self._notification_service.broadcast({"type": "scheduler_status", "status": "stopped"})

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
            if self._notification_service:
                await self._notification_service.broadcast({"type": "verificacion_inicio"})

            # Crear comando
            from application.dtos import MonitorearExpedientesCommand

            # Obtener opciones de extracción desde MySQL si el servicio está disponible
            # Si no, usar defaults de .env como fallback
            fecha_corte_dias = self._config.fecha_corte_dias
            max_paginas = self._config.max_paginas_monitoreo
            tiempo_maximo_segundos = self._config.tiempo_maximo_extraccion
            detener_en_duplicado = self._config.detener_en_duplicado
            orden_extraccion = self._config.orden_extraccion
            mostrar_navegador = False  # Default: no mostrar navegador

            if self._monitoreo_service:
                try:
                    # Obtener configuración del usuario admin (usuario_id=1)
                    # NOTA: En el futuro esto debería parametrizarse por usuario
                    config_db = self._monitoreo_service.repository.obtener_configuracion(usuario_id=1)
                    if config_db:
                        # Usar valores de MySQL si están disponibles, sino usar defaults de .env
                        fecha_corte_dias = config_db.get('fecha_corte_dias') or self._config.fecha_corte_dias
                        max_paginas = config_db.get('max_paginas_monitoreo') or self._config.max_paginas_monitoreo
                        tiempo_maximo_segundos = config_db.get('tiempo_maximo_extraccion') or self._config.tiempo_maximo_extraccion
                        detener_en_duplicado = config_db.get('detener_en_duplicado') or self._config.detener_en_duplicado
                        orden_extraccion = config_db.get('orden_extraccion') or self._config.orden_extraccion
                        mostrar_navegador = config_db.get('mostrar_navegador_monitoreo', False)
                        logger.debug(f"Usando opciones de extracción desde MySQL: fecha_corte_dias={fecha_corte_dias}, max_paginas={max_paginas}, mostrar_navegador={mostrar_navegador}")
                except Exception as e:
                    logger.warning(f"Error obteniendo configuración desde MySQL, usando defaults de .env: {e}")

            command = MonitorearExpedientesCommand(
                json_sistema=self._json_sistema_path,
                base_path=self._workspaces_dir,
                notificar_cambios=self._config.notificar_cambios,
                descargar_nuevos_archivos=self._config.descargar_archivos,
                headless=not mostrar_navegador,  # Usar configuración de MySQL
                # Opciones de extracción (MySQL → .env fallback)
                fecha_corte_dias=fecha_corte_dias,
                max_paginas=max_paginas,
                tiempo_maximo_segundos=tiempo_maximo_segundos,
                detener_en_duplicado=detener_en_duplicado,
                orden_extraccion=orden_extraccion,
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

                # Actualizar ultima_verificacion para todos los expedientes verificados
                if self._monitoreo_service and response.expedientes_verificados > 0:
                    try:
                        ahora = datetime.now()
                        logger.debug(f"Actualizando ultima_verificacion para {response.expedientes_verificados} expedientes...")

                        # Obtener todos los expedientes monitoreados activos
                        expedientes_mysql = self._monitoreo_service.repository.obtener_expedientes(
                            usuario_id=1,
                            solo_activos=True
                        )

                        # Actualizar cada expediente
                        for exp_mysql in expedientes_mysql:
                            try:
                                self._monitoreo_service.repository.actualizar_expediente(
                                    expediente_id=exp_mysql['id'],
                                    ultima_verificacion=ahora
                                )
                            except Exception as e:
                                logger.warning(
                                    f"Error actualizando ultima_verificacion para expediente {exp_mysql.get('expediente_numero', 'desconocido')}: {e}"
                                )

                        logger.debug(f"ultima_verificacion actualizada exitosamente")
                    except Exception as e:
                        logger.error(f"Error general actualizando ultima_verificacion: {e}")
            else:
                logger.error(
                    f"Error en verificación (duración: {duracion:.2f}s): "
                    f"{resultado.error}"
                )

            if self._notification_service:
                await self._notification_service.broadcast({
                    "type": "verificacion_fin",
                    "success": resultado.success,
                    "cambios": response.total_cambios if resultado.success else 0,
                    "duracion": duracion
                })

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

    def _convertir_frecuencia_a_minutos(self, frecuencia: str) -> int:
        """Convierte string de frecuencia a minutos.

        Args:
            frecuencia: String con formato "5min", "30min", "1hora", "3horas", etc.

        Returns:
            Número de minutos correspondiente

        Example:
            >>> self._convertir_frecuencia_a_minutos("30min")
            30
            >>> self._convertir_frecuencia_a_minutos("1hora")
            60
            >>> self._convertir_frecuencia_a_minutos("3horas")
            180
        """
        # Mapeo de frecuencias a minutos
        mapeo_frecuencias = {
            "5min": 5,
            "15min": 15,
            "30min": 30,
            "1hora": 60,
            "3horas": 180,
            "6horas": 360,
            "12horas": 720,
            "24horas": 1440,
        }

        minutos = mapeo_frecuencias.get(frecuencia)
        if minutos is None:
            logger.warning(
                f"Frecuencia '{frecuencia}' no reconocida, usando 30 minutos por defecto"
            )
            return 30

        return minutos

    def _obtener_intervalo_actual_expedientes(self) -> int | None:
        """Obtiene el intervalo de expedientes según horario actual.

        Lee primero de configuración en .env (backward compatibility),
        si no está disponible consulta MySQL, y si tampoco usa fallback de 30 min.

        Returns:
            Intervalo en minutos, o None si no está configurado
        """
        # 1. Intentar obtener de configuración .env (backward compatibility)
        if self._es_horario_laboral():
            intervalo_env = self._config.intervalos_laboral_expedientes
        else:
            intervalo_env = self._config.intervalos_no_laboral_expedientes

        if intervalo_env is not None:
            logger.debug(f"Usando intervalo de .env: {intervalo_env} minutos")
            return intervalo_env

        # 2. Si no hay en .env, consultar MySQL
        if self._monitoreo_service:
            try:
                logger.debug("Consultando intervalo desde MySQL...")
                config_db = self._monitoreo_service.repository.obtener_configuracion(
                    usuario_id=1
                )
                if config_db:
                    frecuencia = config_db.get("frecuencia", "30min")
                    intervalo_mysql = self._convertir_frecuencia_a_minutos(frecuencia)
                    logger.debug(
                        f"Usando intervalo de MySQL: {intervalo_mysql} minutos (frecuencia={frecuencia})"
                    )
                    return intervalo_mysql
            except Exception as e:
                logger.warning(
                    f"Error obteniendo intervalo desde MySQL, usando fallback: {e}"
                )

        # 3. Fallback: retornar None (se usará default de 15 min en _programar_expedientes)
        return None

    def _es_horario_laboral_legacy(self) -> bool:
        """Método legacy que usa configuración de .env como fallback.

        Se usa solo si falla la lectura de MySQL.

        Returns:
            True si es horario laboral según .env, False en caso contrario
        """
        ahora = datetime.now()

        # Verificar día de la semana usando .env
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
                return hora_actual >= hora_inicio or hora_actual <= hora_fin

        except ValueError as e:
            logger.error(f"Error al parsear horas de configuración: {e}")
            return True

    def _es_horario_laboral(self) -> bool:
        """Determina si la hora actual está en horario laboral.

        Lee la configuración de dias_semana desde MySQL en lugar de .env,
        permitiendo que el usuario configure días desde la interfaz.

        Returns:
            True si es horario laboral, False en caso contrario
        """
        try:
            ahora = datetime.now()

            # 1. Obtener configuración de días desde MySQL
            # Crear instancia temporal de MonitoreoRepository para evitar
            # problemas con hot-reload de uvicorn
            try:
                from infrastructure.persistence.monitoreo_repository import MonitoreoRepository

                repo = MonitoreoRepository()
                config_mysql = repo.obtener_o_crear_configuracion(usuario_id=1)
                dias_semana_mysql = config_mysql.get('dias_semana', [1, 2, 3, 4, 5])

                logger.debug(f"Días semana desde MySQL: {dias_semana_mysql}")
            except Exception as e:
                logger.warning(f"Error al leer dias_semana de MySQL, usando .env: {e}")
                return self._es_horario_laboral_legacy()

            # 2. Convertir día actual de Python a formato MySQL
            # Python weekday(): 0=lunes, 1=martes, ..., 6=domingo
            # MySQL: 0=domingo, 1=lunes, 2=martes, ..., 6=sábado
            dia_python = ahora.weekday()  # 0-6 (lunes-domingo)
            dia_mysql = (dia_python + 1) % 7  # Convertir a 0-6 (domingo-sábado)

            logger.debug(f"Día actual: Python={dia_python}, MySQL={dia_mysql}")

            # 3. Verificar si el día actual está en los días configurados
            if dia_mysql not in dias_semana_mysql:
                logger.debug(
                    f"Fuera de horario laboral: día {dia_mysql} no está en {dias_semana_mysql}"
                )
                return False

            # 4. Verificar hora
            try:
                # Usar strftime para parsear horas desde MySQL que pueden no tener padding (ej: '8:00:00')
                from datetime import datetime as dt

                hora_inicio_str = str(config_mysql.get('hora_inicio', self._config.hora_inicio))
                hora_fin_str = str(config_mysql.get('hora_fin', self._config.hora_fin))

                # Parsear con strptime que es más flexible con el formato
                hora_inicio = dt.strptime(hora_inicio_str, '%H:%M:%S').time()
                hora_fin = dt.strptime(hora_fin_str, '%H:%M:%S').time()
                hora_actual = ahora.time()

                # Detectar si el horario cruza la medianoche
                if hora_inicio <= hora_fin:
                    # Horario normal en el mismo día (ej: 08:00 - 18:00)
                    en_horario = hora_inicio <= hora_actual <= hora_fin
                else:
                    # Cruce de medianoche (ej: 22:00 - 06:00, o 08:00 - 07:59 para 24h)
                    en_horario = hora_actual >= hora_inicio or hora_actual <= hora_fin

                logger.debug(
                    f"Verificación hora: {hora_inicio} - {hora_fin}, actual={hora_actual}, "
                    f"en_horario={en_horario}"
                )
                return en_horario

            except ValueError as e:
                logger.error(f"Error al parsear horas de configuración: {e}")
                # Por defecto, considerar horario laboral
                return True

        except Exception as e:
            logger.error(f"Error general en _es_horario_laboral: {e}")
            # Fallback a método legacy si algo sale mal
            return self._es_horario_laboral_legacy()

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

        # Obtener opciones desde MySQL con fallback a .env
        fecha_corte_dias = self._config.fecha_corte_dias
        max_paginas = self._config.max_paginas_monitoreo
        tiempo_maximo_segundos = self._config.tiempo_maximo_extraccion
        detener_en_duplicado = self._config.detener_en_duplicado
        orden_extraccion = self._config.orden_extraccion
        mostrar_navegador = False  # Default: no mostrar navegador

        if self._monitoreo_service:
            try:
                config_db = self._monitoreo_service.repository.obtener_configuracion(usuario_id=1)
                if config_db:
                    fecha_corte_dias = config_db.get('fecha_corte_dias') or fecha_corte_dias
                    max_paginas = config_db.get('max_paginas_monitoreo') or max_paginas
                    tiempo_maximo_segundos = config_db.get('tiempo_maximo_extraccion') or tiempo_maximo_segundos
                    detener_en_duplicado = config_db.get('detener_en_duplicado') or detener_en_duplicado
                    orden_extraccion = config_db.get('orden_extraccion') or orden_extraccion
                    mostrar_navegador = config_db.get('mostrar_navegador_monitoreo', False)
                    logger.info(f"Usando opciones desde MySQL para verificación manual: fecha_corte_dias={fecha_corte_dias}, max_paginas={max_paginas}, mostrar_navegador={mostrar_navegador}")
            except Exception as e:
                logger.warning(f"Error obteniendo configuración desde MySQL: {e}. Usando valores de .env")

        command = MonitorearExpedientesCommand(
            json_sistema=self._json_sistema_path,
            base_path=self._workspaces_dir,
            notificar_cambios=self._config.notificar_cambios,
            descargar_nuevos_archivos=self._config.descargar_archivos,
            headless=not mostrar_navegador,
            # Opciones de extracción desde MySQL
            fecha_corte_dias=fecha_corte_dias,
            max_paginas=max_paginas,
            tiempo_maximo_segundos=tiempo_maximo_segundos,
            detener_en_duplicado=detener_en_duplicado,
            orden_extraccion=orden_extraccion,
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

            # Actualizar ultima_verificacion para todos los expedientes verificados
            if self._monitoreo_service and response.expedientes_verificados > 0:
                try:
                    ahora = datetime.now()
                    logger.debug(f"Actualizando ultima_verificacion para {response.expedientes_verificados} expedientes (manual)...")

                    # Obtener todos los expedientes monitoreados activos
                    expedientes_mysql = self._monitoreo_service.repository.obtener_expedientes(
                        usuario_id=1,
                        solo_activos=True
                    )

                    # Actualizar cada expediente
                    for exp_mysql in expedientes_mysql:
                        try:
                            self._monitoreo_service.repository.actualizar_expediente(
                                expediente_id=exp_mysql['id'],
                                ultima_verificacion=ahora
                            )
                        except Exception as e:
                            logger.warning(
                                f"Error actualizando ultima_verificacion para expediente {exp_mysql.get('expediente_numero', 'desconocido')}: {e}"
                            )

                    logger.debug(f"ultima_verificacion actualizada exitosamente (manual)")
                except Exception as e:
                    logger.error(f"Error general actualizando ultima_verificacion (manual): {e}")

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
