"""Utilidades de persistencia para el extractor inicial."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

from ..pjn.models.expediente import ExpedienteResumen
from ..pjn.monitor.storage import StorageManager

__all__ = ["cargar_historial_simulado", "guardar_historial_simulado"]


def _create_storage(directorio: Path | str) -> StorageManager:
    return StorageManager(Path(directorio))


def cargar_historial_simulado(directorio: Path | str) -> list[ExpedienteResumen]:
    """Carga el historial simulado de expedientes."""

    storage = _create_storage(directorio)
    return storage.cargar_expedientes_conocidos()


def guardar_historial_simulado(
    expedientes: Sequence[ExpedienteResumen] | Iterable[ExpedienteResumen],
    directorio: Path | str,
) -> None:
    """Guarda el historial simulado de expedientes."""

    storage = _create_storage(directorio)
    storage.guardar_expedientes(list(expedientes))
