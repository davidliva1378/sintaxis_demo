"""Motor principal del sistema de monitoreo PJN.

Este módulo contiene la lógica central del monitor que coordina
la verificación de entradas y expedientes.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from playwright.async_api import TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError

from ..scraping.base import obtener_pagina_autenticada
from ..scraping.entradas import extraer_entradas_datos
from ..scraping.expedientes import extraer_expedientes_completos_modelos
from ..models import Entrada, ExpedienteResumen
from ..utils.logging import get_logger
from ..exceptions import CredencialesFaltantes, ExtraccionError, TimeoutExtraccion

from .config import MonitorConfig
from .detector import DetectorCambios
from .notifier import NotificadorPlyer
from .storage import StorageManager, EstadoMonitor
from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig, ExponentialBackoff
from .exceptions import (
    VerificationError,
    AuthenticationError,
    ExtractionError as MonitorExtractionError,
    NetworkError,
)

# Para type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..system_config import SystemConfig

logger = get_logger(__name__)


class MonitorPJN:
    """Motor principal del monitor de expedientes y entradas PJN.

    Este motor coordina la verificación periódica del portal PJN,
    detecta cambios y envía notificaciones según configuración.

    Acepta tanto MonitorConfig como SystemConfig para máxima flexibilidad.
    """

    def __init__(self, config: "MonitorConfig | SystemConfig"):
        """Inicializa el monitor.

        Args:
            config: Configuración del monitor (MonitorConfig o SystemConfig)

        Example:
            >>> # Con MonitorConfig (legacy)
            >>> from pjn.monitor import MonitorConfig, MonitorPJN
            >>> config = MonitorConfig.from_file("config/monitor.json")
            >>> monitor = MonitorPJN(config)

            >>> # Con SystemConfig (recomendado)
            >>> from pjn import SystemConfig
            >>> from pjn.monitor import MonitorPJN
            >>> system_config = SystemConfig.from_file("config/sistema.json")
            >>> monitor = MonitorPJN(system_config)
        """
        # Si recibimos SystemConfig, convertir a MonitorConfig
        if type(config).__name__ == "SystemConfig":
            logger.info("SystemConfig detectado, convirtiendo a MonitorConfig")
            config = MonitorConfig.from_system_config(config)

        self.config = config
        self.storage = StorageManager(Path(config.directorio_datos))
        self.detector = DetectorCambios()
        self.notificador = NotificadorPlyer()
        self.estado = self.storage.cargar_estado()
        self.running = False

        # Circuit breakers para entradas y expedientes
        cb_config = CircuitBreakerConfig(
            failure_threshold=config.max_reintentos_entradas,
            success_threshold=2,
            timeout=config.espera_reintentos_entradas * 2,  # Timeout más largo
            expected_exception=Exception
        )
        self.circuit_breaker_entradas = CircuitBreaker(cb_config)

        cb_config_exp = CircuitBreakerConfig(
            failure_threshold=config.max_reintentos_expedientes,
            success_threshold=2,
            timeout=config.espera_reintentos_expedientes * 2,
            expected_exception=Exception
        )
        self.circuit_breaker_expedientes = CircuitBreaker(cb_config_exp)

        # Backoff para reintentos
        self.backoff_entradas = ExponentialBackoff(
            base_delay=config.espera_reintentos_entradas / 2,
            max_delay=config.espera_reintentos_entradas * 4
        )
        self.backoff_expedientes = ExponentialBackoff(
            base_delay=config.espera_reintentos_expedientes / 2,
            max_delay=config.espera_reintentos_expedientes * 4
        )

        logger.info(f"Monitor PJN inicializado - Modo: {config.modo}")
        logger.info(f"Directorio de datos: {config.directorio_datos}")
        logger.info(f"Circuit breaker habilitado - Umbral fallos: {config.max_reintentos_entradas}")

    async def _verificar_entradas_internal(self) -> list[Entrada]:
        """Método interno de verificación de entradas (sin circuit breaker).

        Returns:
            list[Entrada]: Lista de entradas nuevas detectadas

        Raises:
            Exception: Si falla la extracción
        """

        try:
            # Calcular fechas dinámicamente si dias_atras_entradas está configurado
            fecha_desde = self.config.fecha_desde_entradas
            fecha_hasta = self.config.fecha_hasta_entradas

            if self.config.dias_atras_entradas is not None:
                # Calcular fecha_desde como N días hacia atrás desde hoy
                hoy = datetime.now().date()
                fecha_desde_calculada = hoy - timedelta(days=self.config.dias_atras_entradas)
                fecha_desde = fecha_desde_calculada.strftime("%Y-%m-%d")
                # fecha_hasta = hoy por defecto (None deja que el extractor use todas)
                logger.info(
                    f"📅 Usando días hacia atrás: {self.config.dias_atras_entradas} días "
                    f"(desde {fecha_desde})"
                )

            # Extraer entradas actuales
            async with obtener_pagina_autenticada(
                headless=self.config.headless
            ) as (page, _, _):
                logger.debug("Sesión autenticada, navegando a bandeja de entradas")
                await page.goto("https://portalpjn.pjn.gov.ar/inicio")

                entradas_actuales = await extraer_entradas_datos(
                    page,
                    duplicados=False,
                    incluir_tipos=self.config.tipos_entradas,
                    fecha_desde=fecha_desde,
                    fecha_hasta=fecha_hasta
                )

            logger.info(f"Extraídas {len(entradas_actuales)} entradas del portal")

            # Cargar entradas conocidas
            entradas_conocidas = self.storage.cargar_entradas_conocidas()
            logger.debug(f"Historial tiene {len(entradas_conocidas)} entradas conocidas")

            # Detectar nuevas
            nuevas = self.detector.detectar_nuevas_entradas(
                entradas_actuales,
                entradas_conocidas
            )

            if nuevas:
                logger.info(f"🔔 Detectadas {len(nuevas)} nuevas entradas")

                # Actualizar historial
                self.storage.guardar_entradas(entradas_actuales)
                logger.debug("Historial de entradas actualizado")

                # Notificar
                if self.config.notificar_nuevas_entradas:
                    self.notificador.notificar(
                        titulo="Nuevas Entradas PJN",
                        mensaje=f"{len(nuevas)} nuevas notificaciones detectadas"
                    )
            else:
                logger.info("Sin nuevas entradas detectadas")

            # Actualizar estado
            self.estado.ultima_verificacion_entradas = datetime.now().isoformat()
            self.estado.errores_consecutivos_entradas = 0
            self.storage.guardar_estado(self.estado)

            return nuevas

        except CredencialesFaltantes as e:
            logger.error(f"❌ Credenciales faltantes: {e}", exc_info=True)
            self.estado.errores_consecutivos_entradas += 1
            self.storage.guardar_estado(self.estado)

            if self.config.notificar_errores:
                self.notificador.notificar(
                    titulo="Error Monitor PJN",
                    mensaje=f"Error al verificar entradas: {e}"
                )
            raise AuthenticationError(f"Faltan credenciales: {e}") from e

        except (PlaywrightTimeoutError, TimeoutExtraccion) as e:
            logger.error(f"❌ Timeout al verificar entradas: {e}", exc_info=True)
            self.estado.errores_consecutivos_entradas += 1
            self.storage.guardar_estado(self.estado)

            if self.config.notificar_errores:
                self.notificador.notificar(
                    titulo="Error Monitor PJN",
                    mensaje=f"Timeout al verificar entradas: {e}"
                )
            raise NetworkError(f"Timeout de red: {e}") from e

        except (PlaywrightError, ExtraccionError) as e:
            logger.error(f"❌ Error de extracción en entradas: {e}", exc_info=True)
            self.estado.errores_consecutivos_entradas += 1
            self.storage.guardar_estado(self.estado)

            if self.config.notificar_errores:
                self.notificador.notificar(
                    titulo="Error Monitor PJN",
                    mensaje=f"Error al verificar entradas: {e}"
                )
            raise MonitorExtractionError(f"Error extrayendo entradas: {e}") from e

        except Exception as e:
            # Capturar errores inesperados (último recurso)
            logger.error(f"❌ Error inesperado al verificar entradas: {e}", exc_info=True)
            self.estado.errores_consecutivos_entradas += 1
            self.storage.guardar_estado(self.estado)

            if self.config.notificar_errores:
                self.notificador.notificar(
                    titulo="Error Monitor PJN",
                    mensaje=f"Error inesperado: {e}"
                )
            raise VerificationError(f"Error inesperado en verificación: {e}") from e

    async def verificar_entradas(self) -> list[Entrada]:
        """Verifica si hay nuevas entradas/notificaciones.

        Este método usa circuit breaker para prevenir cascadas de errores.

        Este método:
        1. Extrae las entradas actuales del portal
        2. Las compara con las conocidas
        3. Detecta las nuevas
        4. Actualiza el historial
        5. Envía notificación si corresponde

        Returns:
            list[Entrada]: Lista de entradas nuevas detectadas

        Raises:
            SchedulerError: Si el circuit breaker está abierto
            Exception: Si falla la extracción o hay error en la sesión
        """
        logger.info("Verificando entradas...")

        try:
            # Usar circuit breaker para proteger la llamada
            resultado = await self.circuit_breaker_entradas.call_async(
                self._verificar_entradas_internal
            )
        except Exception:
            raise
        else:
            # Reset backoff en caso de éxito después de errores
            if self.circuit_breaker_entradas.state.value == "closed":
                self.backoff_entradas.reset()
            return resultado

    async def _verificar_expedientes_internal(self) -> list[ExpedienteResumen]:
        """Método interno de verificación de expedientes (sin circuit breaker).

        Returns:
            list[ExpedienteResumen]: Lista de expedientes con cambios

        Raises:
            Exception: Si falla la extracción
        """

        try:
            # Determinar fecha de corte (priorizar fecha_desde_expedientes)
            fecha_corte = (
                self.config.fecha_desde_expedientes
                or self.config.fecha_corte_expedientes
            )

            # Calcular fecha_corte dinámicamente si dias_atras_expedientes está configurado
            if self.config.dias_atras_expedientes is not None:
                hoy = datetime.now().date()
                fecha_corte_calculada = hoy - timedelta(days=self.config.dias_atras_expedientes)
                fecha_corte = fecha_corte_calculada.strftime("%Y-%m-%d")
                logger.info(
                    f"📅 Usando días hacia atrás para expedientes: {self.config.dias_atras_expedientes} días "
                    f"(desde {fecha_corte})"
                )

            if fecha_corte:
                logger.debug(f"Usando fecha de corte para expedientes: {fecha_corte}")

            # Determinar configuraciones de extracción
            max_paginas = self.config.expedientes_max_paginas
            if max_paginas is None:
                max_paginas = None if self.config.extraccion_expedientes_completa else 50

            orden = self.config.expedientes_orden or "fecha"
            detener_duplicados = self.config.expedientes_detener_duplicados

            logger.debug(
                f"Configuración de extracción: max_paginas={max_paginas}, "
                f"orden={orden}, detener_duplicados={detener_duplicados}, "
                f"completa={self.config.extraccion_expedientes_completa}"
            )

            # Extraer expedientes actuales
            async with obtener_pagina_autenticada(
                headless=self.config.headless
            ) as (page, _, _):
                logger.debug("Sesión autenticada, navegando a consultas")
                await page.goto("https://scw.pjn.gov.ar/scw/consultaListaRelacionados.seam")

                expedientes, motivo, metadata = await extraer_expedientes_completos_modelos(
                    page,
                    max_paginas=max_paginas,
                    orden=orden,
                    fecha_corte=fecha_corte,
                    detener_en_duplicado=detener_duplicados
                )

            logger.info(
                f"Extraídos {len(expedientes)} expedientes del portal "
                f"(motivo: {motivo})"
            )

            # Cargar expedientes conocidos
            expedientes_conocidos = self.storage.cargar_expedientes_conocidos()
            logger.debug(f"Historial tiene {len(expedientes_conocidos)} expedientes conocidos")

            # Detectar cambios
            cambios = self.detector.detectar_cambios_expedientes(
                expedientes,
                expedientes_conocidos
            )

            if cambios:
                logger.info(f"📊 Detectados {len(cambios)} expedientes con cambios")

                # Actualizar historial
                self.storage.guardar_expedientes(expedientes)
                logger.debug("Historial de expedientes actualizado")

                # Notificar
                if self.config.notificar_cambios_expedientes:
                    self.notificador.notificar(
                        titulo="Cambios en Expedientes PJN",
                        mensaje=f"{len(cambios)} expedientes con nuevas actuaciones"
                    )
            else:
                logger.info("Sin cambios en expedientes detectados")
                # Actualizar historial de todas formas para capturar nuevos
                if len(expedientes) > len(expedientes_conocidos):
                    self.storage.guardar_expedientes(expedientes)
                    logger.debug("Historial actualizado (expedientes nuevos agregados)")

            # Actualizar estado
            self.estado.ultima_verificacion_expedientes = datetime.now().isoformat()
            self.estado.errores_consecutivos_expedientes = 0
            self.storage.guardar_estado(self.estado)

            return cambios

        except CredencialesFaltantes as e:
            logger.error(f"❌ Credenciales faltantes: {e}", exc_info=True)
            self.estado.errores_consecutivos_expedientes += 1
            self.storage.guardar_estado(self.estado)

            if self.config.notificar_errores:
                self.notificador.notificar(
                    titulo="Error Monitor PJN",
                    mensaje=f"Error al verificar expedientes: {e}"
                )
            raise AuthenticationError(f"Faltan credenciales: {e}") from e

        except (PlaywrightTimeoutError, TimeoutExtraccion) as e:
            logger.error(f"❌ Timeout al verificar expedientes: {e}", exc_info=True)
            self.estado.errores_consecutivos_expedientes += 1
            self.storage.guardar_estado(self.estado)

            if self.config.notificar_errores:
                self.notificador.notificar(
                    titulo="Error Monitor PJN",
                    mensaje=f"Timeout al verificar expedientes: {e}"
                )
            raise NetworkError(f"Timeout de red: {e}") from e

        except (PlaywrightError, ExtraccionError) as e:
            logger.error(f"❌ Error de extracción en expedientes: {e}", exc_info=True)
            self.estado.errores_consecutivos_expedientes += 1
            self.storage.guardar_estado(self.estado)

            if self.config.notificar_errores:
                self.notificador.notificar(
                    titulo="Error Monitor PJN",
                    mensaje=f"Error al verificar expedientes: {e}"
                )
            raise MonitorExtractionError(f"Error extrayendo expedientes: {e}") from e

        except Exception as e:
            # Capturar errores inesperados (último recurso)
            logger.error(f"❌ Error inesperado al verificar expedientes: {e}", exc_info=True)
            self.estado.errores_consecutivos_expedientes += 1
            self.storage.guardar_estado(self.estado)

            if self.config.notificar_errores:
                self.notificador.notificar(
                    titulo="Error Monitor PJN",
                    mensaje=f"Error inesperado: {e}"
                )
            raise VerificationError(f"Error inesperado en verificación: {e}") from e

    async def verificar_expedientes(self) -> list[ExpedienteResumen]:
        """Verifica si hay cambios en expedientes.

        Este método usa circuit breaker para prevenir cascadas de errores.

        Este método:
        1. Extrae los expedientes actuales
        2. Los compara con los conocidos
        3. Detecta expedientes con cambios en ultima_actuacion
        4. Actualiza el historial
        5. Envía notificación si corresponde

        Returns:
            list[ExpedienteResumen]: Lista de expedientes con cambios

        Raises:
            SchedulerError: Si el circuit breaker está abierto
            Exception: Si falla la extracción o hay error en la sesión
        """
        logger.info("Verificando expedientes...")

        try:
            # Usar circuit breaker para proteger la llamada
            resultado = await self.circuit_breaker_expedientes.call_async(
                self._verificar_expedientes_internal
            )
        except Exception:
            raise
        else:
            # Reset backoff en caso de éxito después de errores
            if self.circuit_breaker_expedientes.state.value == "closed":
                self.backoff_expedientes.reset()
            return resultado

    def detener(self) -> None:
        """Detiene el monitor.

        Marca el flag running como False para que los loops se detengan.
        """
        logger.info("Deteniendo monitor...")
        self.running = False


__all__ = ["MonitorPJN"]
