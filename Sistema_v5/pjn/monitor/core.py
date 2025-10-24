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
from .detector import DetectorCambios, CambioExpediente
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

    def _actualizar_manifests_expedientes(self, cambios: list[CambioExpediente]) -> None:
        """Actualiza los manifests de expedientes que tuvieron cambios.

        Args:
            cambios: Lista de cambios detectados con información de qué campos cambiaron
        """
        try:
            # Importación lazy para evitar dependencia circular
            from ...gestor_directorios import GestorDirectoriosExpedientes
            from ...configuracion.core import SystemConfig

            # Cargar SystemConfig si existe, o usar valores por defecto
            base_dir = Path(self.config.directorio_datos).parent.parent
            config_path = base_dir / "config" / "sistema.json"

            if config_path.exists():
                system_config = SystemConfig.from_file(config_path)
                gestor = GestorDirectoriosExpedientes.desde_config(config=system_config)
            else:
                # Fallback: crear gestor con directorio de expedientes del monitor
                expedientes_dir = Path(self.config.directorio_datos).parent / "expedientes"
                gestor = GestorDirectoriosExpedientes(str(expedientes_dir))

            actualizados = 0
            for cambio in cambios:
                exp = cambio.expediente

                # Preparar estado_portal con los datos actuales
                estado_portal = {
                    "dependencia": exp.dependencia,
                    "caratula": exp.caratula,
                    "situacion": exp.situacion,
                    "ultima_actuacion": exp.ultima_actuacion,
                }

                try:
                    # Actualizar manifest con información del cambio
                    gestor.actualizar_desde_monitor(
                        numero_expediente=exp.numero,
                        estado_portal=estado_portal,
                        tipo_cambio=cambio.tipo_cambio,
                        campos_cambiados=cambio.campos_cambiados,
                        valores_anteriores=cambio.valores_anteriores,
                    )
                    actualizados += 1
                    logger.debug(
                        f"Manifest actualizado para {exp.numero} "
                        f"(tipo: {cambio.tipo_cambio})"
                    )
                except Exception as e:
                    logger.warning(
                        f"No se pudo actualizar manifest para {exp.numero}: {e}"
                    )
                    # Continuar con los demás expedientes

            if actualizados > 0:
                logger.info(
                    f"✅ Actualizados {actualizados}/{len(cambios)} manifests con cambios detectados"
                )

        except Exception as e:
            logger.error(
                f"Error al actualizar manifests de expedientes: {e}",
                exc_info=True
            )
            # No lanzar excepción para no detener el monitoreo

    async def _actualizar_actuaciones_expedientes(self, cambios: list[CambioExpediente]) -> None:
        """Actualiza las actuaciones de expedientes que tuvieron cambios relevantes.

        Este método se ejecuta automáticamente cuando el monitor detecta cambios en expedientes
        y la configuración `actualizar_actuaciones_automaticamente` está habilitada.

        Solo actualiza expedientes con cambios de tipo:
        - nueva_actuacion: Cambió la fecha de última actuación
        - cambio_situacion: Cambió el estado del expediente (ej: "En trámite" → "EN LETRA")
        - multiples_cambios: Si incluye nueva_actuacion o cambio_situacion

        Funcionamiento:
        1. Filtra cambios relevantes
        2. Abre cada expediente en el portal usando búsqueda por número/año
        3. Extrae actuaciones actualizadas y descarga adjuntos
        4. Reintenta hasta `max_reintentos_actualizacion_actuaciones` veces por expediente
        5. Registra estadísticas de éxito/fallo sin detener el monitoreo

        Args:
            cambios: Lista de cambios detectados por el detector

        Note:
            - No lanza excepciones para evitar detener el ciclo de monitoreo
            - Registra errores con nivel ERROR en los logs
            - Usa la misma sesión de browser para todos los expedientes
            - Regresa a la página de consultas antes de cada reintento
        """
        # Filtrar cambios relevantes para actualización de actuaciones
        cambios_relevantes = [
            c for c in cambios
            if c.tipo_cambio in ("nueva_actuacion", "cambio_situacion")
            or (
                c.tipo_cambio == "multiples_cambios"
                and any(
                    campo in c.campos_cambiados
                    for campo in ["ultima_actuacion", "situacion"]
                )
            )
        ]

        if not cambios_relevantes:
            logger.debug("No hay cambios relevantes para actualizar actuaciones")
            return

        logger.info(
            f"🔄 Actualizando actuaciones de {len(cambios_relevantes)} expediente(s) "
            f"(de {len(cambios)} cambios totales)"
        )

        try:
            # Importaciones lazy
            from ...pjn.scraping.base import obtener_pagina_autenticada, descomponer_numero_expediente
            from ...pjn.scraping.expedientes import buscar_expedientes, mostrar_y_elegir_expediente
            from ...pjn.services.actuaciones import procesar_actuaciones_expediente
            from ...gestor_directorios import GestorDirectoriosExpedientes
            from ...configuracion.core import SystemConfig

            # Cargar gestor de directorios
            base_dir = Path(self.config.directorio_datos).parent.parent
            config_path = base_dir / "config" / "sistema.json"

            if config_path.exists():
                system_config = SystemConfig.from_file(config_path)
                gestor = GestorDirectoriosExpedientes.desde_config(config=system_config)
            else:
                expedientes_dir = Path(self.config.directorio_datos).parent / "expedientes"
                gestor = GestorDirectoriosExpedientes(str(expedientes_dir))

            max_reintentos = self.config.max_reintentos_actualizacion_actuaciones
            actualizados = 0
            fallidos = 0

            async with obtener_pagina_autenticada(headless=self.config.headless) as (
                page,
                _,
                _,
            ):
                # Navegar a la página de consultas una sola vez
                await page.goto(
                    "https://scw.pjn.gov.ar/scw/consultaListaRelacionados.seam"
                )

                for cambio in cambios_relevantes:
                    exp = cambio.expediente

                    # Intentos de actualización con reintentos
                    for intento in range(1, max_reintentos + 1):
                        try:
                            logger.debug(
                                f"Actualizando actuaciones de {exp.numero} "
                                f"(intento {intento}/{max_reintentos})"
                            )

                            # Descomponer número de expediente
                            _, numero, anio = descomponer_numero_expediente(exp.numero)

                            if not numero or not anio:
                                raise Exception(f"No se pudo descomponer el número: {exp.numero}")

                            # Buscar expediente en el portal
                            filas = await buscar_expedientes(
                                page,
                                numero=numero,
                                anio=anio,
                                caratula=exp.caratula,
                            )

                            if not filas:
                                raise Exception(f"Expediente no encontrado en el portal")

                            # Abrir expediente (abre la primera fila o la que coincide con carátula)
                            datos = await mostrar_y_elegir_expediente(page, filas)

                            if not datos:
                                raise Exception(f"No se pudo abrir el expediente")

                            # Preparar datos del expediente
                            datos_expediente = {
                                "page": page,
                                "numero": exp.numero,
                                "dependencia": exp.dependencia,
                                "caratula": exp.caratula,
                                "situacion": exp.situacion,
                            }

                            # Procesar actuaciones con descarga de adjuntos
                            json_path, resultado = await procesar_actuaciones_expediente(
                                datos_expediente,
                                descargar_adjuntos=True,
                            )

                            if resultado.error:
                                raise Exception(resultado.error)

                            logger.info(
                                f"✅ Actuaciones actualizadas para {exp.numero} "
                                f"({resultado.total_actuaciones} actuaciones)"
                            )
                            actualizados += 1
                            break  # Éxito, salir del loop de reintentos

                        except Exception as e:
                            if intento < max_reintentos:
                                logger.warning(
                                    f"Error al actualizar {exp.numero} (intento {intento}): {e}"
                                )
                                await asyncio.sleep(2)  # Esperar antes de reintentar

                                # Regresar a la página de consultas para reintentar
                                await page.goto(
                                    "https://scw.pjn.gov.ar/scw/consultaListaRelacionados.seam"
                                )
                            else:
                                logger.error(
                                    f"❌ Fallo definitivo al actualizar {exp.numero} "
                                    f"tras {max_reintentos} intentos: {e}"
                                )
                                fallidos += 1

            if actualizados > 0 or fallidos > 0:
                logger.info(
                    f"📊 Resumen actualización de actuaciones: "
                    f"{actualizados} exitosos, {fallidos} fallidos "
                    f"(de {len(cambios_relevantes)} expedientes)"
                )

        except Exception as e:
            logger.error(
                f"Error general al actualizar actuaciones: {e}",
                exc_info=True,
            )
            # No lanzar excepción para no detener el monitoreo

    async def _verificar_expedientes_internal(self, retornar_todos: bool = False) -> list[ExpedienteResumen]:
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

            # Si retornar_todos=True, retornar TODOS los expedientes sin filtrar
            if retornar_todos:
                logger.info(f"📊 Extracción inicial: retornando todos los {len(expedientes)} expedientes")
                # Actualizar historial para que futuras verificaciones funcionen
                self.storage.guardar_expedientes(expedientes)
                self.estado.ultima_verificacion_expedientes = datetime.now().isoformat()
                self.estado.errores_consecutivos_expedientes = 0
                self.storage.guardar_estado(self.estado)
                return expedientes

            # Modo normal: detectar cambios
            cambios = self.detector.detectar_cambios_expedientes(
                expedientes,
                expedientes_conocidos
            )

            # Procesar cambios detectados
            if cambios:
                logger.info(f"📊 Detectados {len(cambios)} expedientes con cambios")

                # Actualizar manifests de expedientes con cambios
                self._actualizar_manifests_expedientes(cambios)

                # Actualizar actuaciones si está configurado
                if self.config.actualizar_actuaciones_automaticamente:
                    await self._actualizar_actuaciones_expedientes(cambios)

                # Actualizar historial
                self.storage.guardar_expedientes(expedientes)
                logger.debug("Historial de expedientes actualizado")

                # Notificar
                if self.config.notificar_cambios_expedientes:
                    # Clasificar tipos de cambios para notificación más informativa
                    tipos_cambios = {}
                    for cambio in cambios:
                        tipo = cambio.tipo_cambio
                        tipos_cambios[tipo] = tipos_cambios.get(tipo, 0) + 1

                    mensaje_detalle = ", ".join(
                        f"{count} {tipo.replace('_', ' ')}"
                        for tipo, count in tipos_cambios.items()
                    )

                    self.notificador.notificar(
                        titulo="Cambios en Expedientes PJN",
                        mensaje=f"{len(cambios)} expedientes con cambios: {mensaje_detalle}"
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

    async def extraer_listado_inicial(
        self,
        destino: Path | None = None,
        *,
        exportar_csv: bool = False,
        nombre_archivo: str | None = None,
    ) -> tuple[list[ExpedienteResumen], Path]:
        """Extrae el listado completo de expedientes para inicialización.

        Este método reutiliza la infraestructura del monitor para obtener
        el listado completo de expedientes del portal PJN, ideal para la
        fase inicial de configuración del sistema.

        Args:
            destino: Directorio donde guardar el JSON. Si es None, usa
                directorio_extraccion_inicial de la configuración
            exportar_csv: Si True, genera también un archivo CSV paralelo
                para facilitar filtrado en herramientas externas
            nombre_archivo: Nombre personalizado del archivo (sin extensión).
                Por defecto: expedientes_YYYYMMDD_HHMMSS

        Returns:
            Tupla con: (lista de expedientes, ruta del JSON generado)

        Raises:
            VerificationError: Si falla la extracción
            AuthenticationError: Si falla la autenticación

        Example:
            >>> monitor = MonitorPJN(config)
            >>> expedientes, json_path = await monitor.extraer_listado_inicial()
            >>> print(f"Extraídos {len(expedientes)} expedientes en {json_path}")
        """
        import json
        from datetime import datetime

        logger.info("🚀 Iniciando extracción del listado completo de expedientes")

        # Determinar directorio destino
        if destino is None:
            # Intentar usar directorio de extracción inicial de la config
            destino_str = getattr(self.config, "directorio_extraccion_inicial", None)
            if destino_str:
                destino = Path(destino_str)
            else:
                # Fallback: subdirectorio en directorio de datos
                destino = Path(self.config.directorio_datos).parent / "extraccion_inicial"

        destino.mkdir(parents=True, exist_ok=True)

        # Generar nombre de archivo
        if nombre_archivo is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"expedientes_{timestamp}"

        json_path = destino / f"{nombre_archivo}.json"

        # Extraer expedientes usando el método interno (SIN filtrar por cambios)
        try:
            expedientes = await self._verificar_expedientes_internal(retornar_todos=True)
        except Exception as exc:
            logger.error(f"❌ Error durante la extracción del listado: {exc}")
            raise VerificationError(f"Fallo en extracción del listado inicial: {exc}") from exc

        # Preparar metadata
        metadata = {
            "version": "2.0",
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "total_expedientes": len(expedientes),
            "config_utilizada": {
                "fecha_desde": self.config.fecha_desde_expedientes,
                "fecha_hasta": self.config.fecha_hasta_expedientes,
                "dias_atras": self.config.dias_atras_expedientes,
                "extraccion_completa": getattr(
                    self.config, "extraccion_expedientes_completa", True
                ),
                "orden": self.config.expedientes_orden,
            },
        }

        # Guardar JSON
        payload = {
            "metadata": metadata,
            "expedientes": [exp.to_dict() for exp in expedientes],
        }

        json_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        logger.info(f"✅ Listado guardado en: {json_path}")
        logger.info(f"📊 Total expedientes extraídos: {len(expedientes)}")

        # Exportar CSV si se solicita
        if exportar_csv:
            csv_path = destino / f"{nombre_archivo}.csv"
            try:
                self._exportar_csv(expedientes, csv_path)
                logger.info(f"📄 CSV exportado en: {csv_path}")
            except Exception as exc:
                logger.warning(f"⚠️  No se pudo exportar CSV: {exc}")

        return expedientes, json_path

    def _exportar_csv(self, expedientes: list[ExpedienteResumen], csv_path: Path) -> None:
        """Exporta expedientes a formato CSV para filtrado externo.

        Args:
            expedientes: Lista de expedientes a exportar
            csv_path: Ruta donde guardar el CSV
        """
        import csv

        with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = ["numero", "dependencia", "caratula", "situacion", "ultima_actuacion"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for exp in expedientes:
                writer.writerow({
                    "numero": exp.numero,
                    "dependencia": exp.dependencia,
                    "caratula": exp.caratula,
                    "situacion": exp.situacion or "",
                    "ultima_actuacion": exp.ultima_actuacion or "",
                })


__all__ = ["MonitorPJN"]
