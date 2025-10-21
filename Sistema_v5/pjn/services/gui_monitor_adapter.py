"""Adaptadores entre la GUI y el almacenamiento del monitor PJN."""
from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
import sys

if __package__ in {None, ""}:
    # Permite ejecutar el módulo directamente resolviendo la raíz del proyecto.
    project_root = Path(__file__).resolve().parents[3]
    if str(project_root) not in sys.path:
        sys.path.append(str(project_root))

from Sistema_v5.configuracion.monitor.config import MonitorConfig
from Sistema_v5.pjn.models import Entrada, ExpedienteResumen
from Sistema_v5.pjn.monitor.storage import StorageManager
from Sistema_v5.pjn.monitor.storage_selecciones import SeleccionesStorageManager


def _create_storage_manager(config_path: Path | str) -> StorageManager:
    """Crea un ``StorageManager`` a partir de un archivo de configuración."""
    config = MonitorConfig.from_file(config_path)
    datos_dir = Path(config.directorio_datos)
    return StorageManager(datos_dir)


def _create_storage_manager_from_directory(datos_dir: Path | str) -> StorageManager:
    """Crea un ``StorageManager`` directamente desde un directorio de datos."""

    return StorageManager(Path(datos_dir))


def _create_selecciones_manager(
    config_path: Path | str,
) -> SeleccionesStorageManager:
    """Crea un ``SeleccionesStorageManager`` a partir de la configuración."""

    config = MonitorConfig.from_file(config_path)
    datos_dir = Path(config.directorio_datos)
    return SeleccionesStorageManager(datos_dir)


def _create_selecciones_manager_from_directory(
    datos_dir: Path | str,
) -> SeleccionesStorageManager:
    """Crea un ``SeleccionesStorageManager`` desde un directorio de datos."""

    return SeleccionesStorageManager(Path(datos_dir))


def cargar_historiales_monitor(
    config_path: Path | str = Path("config/monitor.json"),
) -> tuple[list[Entrada], list[ExpedienteResumen]]:
    """Carga los historiales persistidos para ser usados por la GUI."""
    storage = _create_storage_manager(config_path)
    entradas = storage.cargar_entradas_conocidas()
    expedientes = storage.cargar_expedientes_conocidos()
    return entradas, expedientes


def cargar_historiales_desde_directorio(
    datos_dir: Path | str,
) -> tuple[list[Entrada], list[ExpedienteResumen]]:
    """Carga los historiales usando directamente un directorio de datos."""

    storage = _create_storage_manager_from_directory(datos_dir)
    entradas = storage.cargar_entradas_conocidas()
    expedientes = storage.cargar_expedientes_conocidos()
    return entradas, expedientes


def guardar_historiales_monitor(
    config_path: Path | str,
    entradas: Iterable[Entrada] | None = None,
    expedientes: Iterable[ExpedienteResumen] | None = None,
) -> None:
    """Persiste los historiales desde la GUI usando la configuración existente."""
    storage = _create_storage_manager(config_path)
    entradas_list = list(entradas or [])
    expedientes_list = list(expedientes or [])
    storage.guardar_entradas(entradas_list)
    storage.guardar_expedientes(expedientes_list)


def guardar_historiales_en_directorio(
    datos_dir: Path | str,
    entradas: Iterable[Entrada] | None = None,
    expedientes: Iterable[ExpedienteResumen] | None = None,
) -> None:
    """Persiste los historiales directamente en un directorio de datos."""

    storage = _create_storage_manager_from_directory(datos_dir)
    entradas_list = list(entradas or [])
    expedientes_list = list(expedientes or [])
    storage.guardar_entradas(entradas_list)
    storage.guardar_expedientes(expedientes_list)


def cargar_selecciones_monitor(
    config_path: Path | str = Path("config/monitor.json"),
) -> tuple[list[str], list[str]]:
    """Obtiene las selecciones persistidas para la interfaz."""

    storage = _create_selecciones_manager(config_path)
    return storage.cargar_selecciones()


def cargar_selecciones_desde_directorio(
    datos_dir: Path | str,
) -> tuple[list[str], list[str]]:
    """Obtiene las selecciones persistidas desde un directorio específico."""

    storage = _create_selecciones_manager_from_directory(datos_dir)
    return storage.cargar_selecciones()


def guardar_selecciones_monitor(
    config_path: Path | str,
    entradas_ids: Iterable[object] | None = None,
    expedientes_ids: Iterable[object] | None = None,
) -> None:
    """Persiste las selecciones realizadas desde la interfaz."""

    storage = _create_selecciones_manager(config_path)
    storage.guardar_selecciones(entradas_ids, expedientes_ids)


def guardar_selecciones_en_directorio(
    datos_dir: Path | str,
    entradas_ids: Iterable[object] | None = None,
    expedientes_ids: Iterable[object] | None = None,
) -> None:
    """Persiste las selecciones realizadas directamente en un directorio."""

    storage = _create_selecciones_manager_from_directory(datos_dir)
    storage.guardar_selecciones(entradas_ids, expedientes_ids)


__all__ = [
    "cargar_historiales_monitor",
    "guardar_historiales_monitor",
    "cargar_selecciones_monitor",
    "guardar_selecciones_monitor",
    "cargar_historiales_desde_directorio",
    "guardar_historiales_en_directorio",
    "cargar_selecciones_desde_directorio",
    "guardar_selecciones_en_directorio",
]
