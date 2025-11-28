"""Dependency Injection Container.

Este módulo implementa un contenedor de inyección de dependencias simple
que crea e inicializa todos los componentes del sistema.
"""

from __future__ import annotations

import logging
from pathlib import Path

from application.ports import (
    IActuacionRepository,
    IEntradaRepository,
    IExpedienteRepository,
    INotificacionPort,
    IScraperPort,
    IStoragePort,
    IWorkspacePort,
)
from application.use_cases import (
    CrearWorkspacesUseCase,
    ExtraerExpedientesUseCase,
    ExtraccionMasivaUseCase,
    FiltrarExpedientesUseCase,
    MonitorearExpedientesUseCase,
)

from .adapters.notificaciones import NotificacionAdapter
from .adapters.repositories import (
    JsonActuacionRepository,
    JsonEntradaRepository,
    JsonExpedienteRepository,
)
from .adapters.scraping import PlaywrightScraperAdapter
from .adapters.storage import FileStorageAdapter
from .adapters.workspace import WorkspaceAdapter
from .config import Settings, get_settings
from .services.gestor_sesiones_service import get_gestor_sesiones

logger = logging.getLogger(__name__)


class DIContainer:
    """Contenedor de inyección de dependencias.

    Este contenedor crea e inicializa todos los componentes del sistema,
    conectando las capas de aplicación e infraestructura.

    Sigue el patrón Composition Root para centralizar la creación de
    dependencias.

    Attributes:
        settings: Configuración del sistema
    """

    def __init__(self, settings: Settings | None = None):
        """Inicializa el contenedor.

        Args:
            settings: Configuración del sistema (None para usar default)
        """
        self.settings = settings or get_settings()

        # Inicializar componentes
        self._storage: IStoragePort | None = None
        self._workspace: IWorkspacePort | None = None
        self._scraper: IScraperPort | None = None
        self._notificacion: INotificacionPort | None = None

        self._expediente_repo: IExpedienteRepository | None = None
        self._actuacion_repo: IActuacionRepository | None = None
        self._entrada_repo: IEntradaRepository | None = None

        # Servicios de aplicación
        self._detector_cambios = None
        self._gestor_estados = None
        self._monitor_scheduler = None
        self._monitoreo_service = None

    # === Adapters ===

    @property
    def storage(self) -> IStoragePort:
        """Obtiene el adapter de almacenamiento."""
        if self._storage is None:
            self._storage = FileStorageAdapter(
                pretty_json=self.settings.storage.pretty_json,
                ensure_ascii=self.settings.storage.ensure_ascii,
            )
            logger.debug("FileStorageAdapter inicializado")
        return self._storage

    @property
    def workspace(self) -> IWorkspacePort:
        """Obtiene el adapter de workspaces."""
        if self._workspace is None:
            self._workspace = WorkspaceAdapter()
            logger.debug("WorkspaceAdapter inicializado")
        return self._workspace

    @property
    def scraper(self) -> IScraperPort:
        """Obtiene el adapter de scraping."""
        if self._scraper is None:
            session_file = (
                self.settings.storage.base_path / self.settings.auth.session_file_name
            )
            self._scraper = PlaywrightScraperAdapter(
                login_url=self.settings.auth.login_url,
                session_file=session_file,
            )
            logger.debug("PlaywrightScraperAdapter inicializado")
        return self._scraper

    @property
    def notificacion(self) -> INotificacionPort:
        """Obtiene el adapter de notificaciones."""
        if self._notificacion is None:
            self._notificacion = NotificacionAdapter(
                settings=self.settings.notificaciones,
            )
            logger.debug("NotificacionAdapter inicializado")
        return self._notificacion

    # === Repositorios ===

    @property
    def expediente_repo(self) -> IExpedienteRepository:
        """Obtiene el repositorio de expedientes."""
        if self._expediente_repo is None:
            # Usar repositorio MySQL como fuente primaria
            from infrastructure.persistence.expedientes_mysql import get_expedientes_repository
            self._expediente_repo = get_expedientes_repository()
            logger.debug("ExpedientesRepository (MySQL) inicializado")
        return self._expediente_repo

    @property
    def actuacion_repo(self) -> IActuacionRepository:
        """Obtiene el repositorio de actuaciones."""
        if self._actuacion_repo is None:
            workspaces_base = (
                self.settings.storage.base_path / self.settings.storage.workspaces_dir
            )
            self._actuacion_repo = JsonActuacionRepository(
                storage=self.storage,
                workspaces_base=workspaces_base,
            )
            logger.debug(f"JsonActuacionRepository inicializado: {workspaces_base}")
        return self._actuacion_repo

    @property
    def entrada_repo(self) -> IEntradaRepository:
        """Obtiene el repositorio de entradas."""
        if self._entrada_repo is None:
            archivo = self.settings.storage.base_path / "entradas.json"
            self._entrada_repo = JsonEntradaRepository(
                storage=self.storage,
                archivo_json=archivo,
            )
            logger.debug(f"JsonEntradaRepository inicializado: {archivo}")
        return self._entrada_repo

    # === Servicios de Aplicación ===

    @property
    def detector_cambios(self):
        """Obtiene el detector de cambios multi-campo."""
        if self._detector_cambios is None:
            from application.services.detector_cambios import DetectorCambios

            self._detector_cambios = DetectorCambios()
            logger.debug("DetectorCambios inicializado")
        return self._detector_cambios

    @property
    def gestor_estados(self):
        """Obtiene el gestor de estados de expedientes."""
        if self._gestor_estados is None:
            from infrastructure.persistence.estados_expedientes import (
                GestorEstadosExpedientes,
            )

            data_dir = self.settings.storage.base_path
            self._gestor_estados = GestorEstadosExpedientes(data_dir)
            logger.debug(f"GestorEstadosExpedientes inicializado: {data_dir}")
        return self._gestor_estados

    @property
    def monitoreo_service(self):
        """Obtiene el servicio de monitoreo para MySQL."""
        if self._monitoreo_service is None:
            from application.services.monitoreo_service import MonitoreoService

            self._monitoreo_service = MonitoreoService()
            logger.debug("MonitoreoService inicializado")
        return self._monitoreo_service

    @property
    def monitor_scheduler(self):
        """Obtiene el servicio de scheduler de monitoreo."""
        if self._monitor_scheduler is None:
            from application.services.monitor_scheduler_service import (
                MonitorSchedulerService,
            )

            json_sistema_path = (
                self.settings.storage.base_path / self.settings.storage.json_sistema_file
            )
            workspaces_dir = (
                self.settings.storage.base_path / self.settings.storage.workspaces_dir
            )

            self._monitor_scheduler = MonitorSchedulerService(
                monitorear_use_case=self.monitorear_expedientes_use_case(),
                config=self.settings.monitoreo,
                json_sistema_path=json_sistema_path,
                workspaces_dir=workspaces_dir,
                monitoreo_service=self.monitoreo_service,
            )
            logger.debug("MonitorSchedulerService inicializado")
        return self._monitor_scheduler

    # === Use Cases ===

    def extraer_expedientes_use_case(self) -> ExtraerExpedientesUseCase:
        """Crea el use case de extracción de expedientes."""
        return ExtraerExpedientesUseCase(
            scraper=self.scraper,
            repository=self.expediente_repo,
            storage=self.storage,
        )

    def filtrar_expedientes_use_case(self) -> FiltrarExpedientesUseCase:
        """Crea el use case de filtrado de expedientes."""
        return FiltrarExpedientesUseCase(
            repository=self.expediente_repo,
            storage=self.storage,
        )

    def crear_workspaces_use_case(self) -> CrearWorkspacesUseCase:
        """Crea el use case de creación de workspaces."""
        return CrearWorkspacesUseCase(
            workspace_port=self.workspace,
            storage=self.storage,
            scraper=self.scraper,
            actuacion_repo=self.actuacion_repo,
        )

    def monitorear_expedientes_use_case(self) -> MonitorearExpedientesUseCase:
        """Crea el use case de monitoreo de expedientes."""
        return MonitorearExpedientesUseCase(
            scraper=self.scraper,
            expediente_repo=self.expediente_repo,
            actuacion_repo=self.actuacion_repo,
            storage=self.storage,
            workspace_port=self.workspace,
            notificacion_port=self.notificacion,
            detector_cambios=self.detector_cambios,
            gestor_estados=self.gestor_estados,
            settings=self.settings,
        )

    def extraccion_masiva_use_case(self) -> ExtraccionMasivaUseCase:
        """Crea el use case de extracción masiva."""
        return ExtraccionMasivaUseCase(
            storage=self.storage,
            repository=self.expediente_repo,
            gestor_sesiones=get_gestor_sesiones(),
        )

    async def cleanup_async(self) -> None:
        """Limpia recursos del contenedor (async)."""
        logger.debug("DI Container cleanup (async)")

        # Detener scheduler si está activo
        if self._monitor_scheduler is not None:
            try:
                await self._monitor_scheduler.stop()
                logger.debug("MonitorSchedulerService detenido")
            except Exception as e:
                logger.error(f"Error al detener scheduler: {e}")

    def cleanup(self) -> None:
        """Limpia recursos del contenedor (sync wrapper)."""
        import asyncio

        logger.debug("DI Container cleanup")

        # Ejecutar cleanup async si hay scheduler
        if self._monitor_scheduler is not None:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Si el loop está corriendo, crear tarea
                    asyncio.create_task(self.cleanup_async())
                else:
                    # Si no, ejecutar directamente
                    loop.run_until_complete(self.cleanup_async())
            except Exception as e:
                logger.error(f"Error en cleanup: {e}")


# Singleton instance
_container: DIContainer | None = None


def get_container(settings: Settings | None = None) -> DIContainer:
    """Obtiene la instancia singleton del contenedor.

    Args:
        settings: Configuración del sistema (None para usar default)

    Returns:
        Instancia de DIContainer
    """
    global _container
    if _container is None:
        _container = DIContainer(settings)
        logger.info("DI Container inicializado")
    return _container


def reset_container() -> None:
    """Resetea el contenedor (útil para testing)."""
    global _container
    if _container:
        _container.cleanup()
    _container = None
    logger.debug("DI Container reseteado")
