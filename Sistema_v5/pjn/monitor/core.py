"""Motor principal del sistema de monitoreo PJN.

Este módulo contiene la lógica central del monitor que coordina
la verificación de entradas y expedientes.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ..scraping.base import obtener_pagina_autenticada
from ..scraping.entradas import extraer_entradas_datos
from ..scraping.expedientes import extraer_expedientes_completos_modelos
from ..models import Entrada, ExpedienteResumen
from ..utils.logging import get_logger

from .config import MonitorConfig
from .detector import DetectorCambios
from .notifier import NotificadorPlyer
from .storage import StorageManager, EstadoMonitor

logger = get_logger(__name__)


class MonitorPJN:
    """Motor principal del monitor de expedientes y entradas PJN.

    Este motor coordina la verificación periódica del portal PJN,
    detecta cambios y envía notificaciones según configuración.
    """

    def __init__(self, config: MonitorConfig):
        """Inicializa el monitor.

        Args:
            config: Configuración del monitor
        """
        self.config = config
        self.storage = StorageManager(Path(config.directorio_datos))
        self.detector = DetectorCambios()
        self.notificador = NotificadorPlyer()
        self.estado = self.storage.cargar_estado()
        self.running = False

        logger.info(f"Monitor PJN inicializado - Modo: {config.modo}")
        logger.info(f"Directorio de datos: {config.directorio_datos}")

    async def verificar_entradas(self) -> list[Entrada]:
        """Verifica si hay nuevas entradas/notificaciones.

        Este método:
        1. Extrae las entradas actuales del portal
        2. Las compara con las conocidas
        3. Detecta las nuevas
        4. Actualiza el historial
        5. Envía notificación si corresponde

        Returns:
            list[Entrada]: Lista de entradas nuevas detectadas

        Raises:
            Exception: Si falla la extracción o hay error en la sesión
        """
        logger.info("Verificando entradas...")

        try:
            # Extraer entradas actuales
            async with obtener_pagina_autenticada(
                headless=self.config.headless
            ) as (page, _, _):
                logger.debug("Sesión autenticada, navegando a bandeja de entradas")
                await page.goto("https://portalpjn.pjn.gov.ar/inicio")

                entradas_actuales = await extraer_entradas_datos(
                    page,
                    duplicados=False,
                    incluir_tipos=("N",),  # Solo notificaciones
                    fecha_desde=self.config.fecha_desde_entradas,
                    fecha_hasta=self.config.fecha_hasta_entradas
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

        except Exception as e:
            logger.error(f"❌ Error al verificar entradas: {e}", exc_info=True)

            # Incrementar contador de errores
            self.estado.errores_consecutivos_entradas += 1
            self.storage.guardar_estado(self.estado)

            # Notificar error si está configurado
            if self.config.notificar_errores:
                self.notificador.notificar(
                    titulo="Error Monitor PJN",
                    mensaje=f"Error al verificar entradas: {e}"
                )

            raise

    async def verificar_expedientes(self) -> list[ExpedienteResumen]:
        """Verifica si hay cambios en expedientes.

        Este método:
        1. Extrae los expedientes actuales
        2. Los compara con los conocidos
        3. Detecta expedientes con cambios en ultima_actuacion
        4. Actualiza el historial
        5. Envía notificación si corresponde

        Returns:
            list[ExpedienteResumen]: Lista de expedientes con cambios

        Raises:
            Exception: Si falla la extracción o hay error en la sesión
        """
        logger.info("Verificando expedientes...")

        try:
            # Determinar fecha de corte (priorizar fecha_desde_expedientes)
            fecha_corte = (
                self.config.fecha_desde_expedientes
                or self.config.fecha_corte_expedientes
            )

            if fecha_corte:
                logger.debug(f"Usando fecha de corte para expedientes: {fecha_corte}")

            # Extraer expedientes actuales
            async with obtener_pagina_autenticada(
                headless=self.config.headless
            ) as (page, _, _):
                logger.debug("Sesión autenticada, navegando a consultas")
                await page.goto("https://scw.pjn.gov.ar/scw/consultaListaRelacionados.seam")

                expedientes, motivo, metadata = await extraer_expedientes_completos_modelos(
                    page,
                    max_paginas=50,
                    orden="fecha",
                    fecha_corte=fecha_corte
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

        except Exception as e:
            logger.error(f"❌ Error al verificar expedientes: {e}", exc_info=True)

            # Incrementar contador de errores
            self.estado.errores_consecutivos_expedientes += 1
            self.storage.guardar_estado(self.estado)

            # Notificar error si está configurado
            if self.config.notificar_errores:
                self.notificador.notificar(
                    titulo="Error Monitor PJN",
                    mensaje=f"Error al verificar expedientes: {e}"
                )

            raise

    def detener(self) -> None:
        """Detiene el monitor.

        Marca el flag running como False para que los loops se detengan.
        """
        logger.info("Deteniendo monitor...")
        self.running = False


__all__ = ["MonitorPJN"]
