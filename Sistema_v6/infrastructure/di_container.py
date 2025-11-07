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
            archivo = self.settings.storage.base_path / self.settings.storage.json_base_file
            self._expediente_repo = JsonExpedienteRepository(
                storage=self.storage,
                archivo_json=archivo,
            )
            logger.debug(f"JsonExpedienteRepository inicializado: {archivo}")
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
        )

    def cleanup(self) -> None:
        """Limpia recursos del contenedor."""
        # TODO: Cerrar conexiones, liberar recursos si es necesario
        logger.debug("DI Container cleanup")


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
