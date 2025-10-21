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


def _create_storage_manager(config_path: Path | str) -> StorageManager:
    """Crea un ``StorageManager`` a partir de un archivo de configuración."""
    config = MonitorConfig.from_file(config_path)
    datos_dir = Path(config.directorio_datos)
    return StorageManager(datos_dir)


def cargar_historiales_monitor(
    config_path: Path | str = Path("config/monitor.json"),
) -> tuple[list[Entrada], list[ExpedienteResumen]]:
    """Carga los historiales persistidos para ser usados por la GUI."""
    storage = _create_storage_manager(config_path)
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


__all__ = [
    "cargar_historiales_monitor",
    "guardar_historiales_monitor",
]
