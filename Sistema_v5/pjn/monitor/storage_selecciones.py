"""Gestor de persistencia para selecciones del monitor PJN."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from ..utils.logging import get_logger
from .exceptions import StorageError

logger = get_logger(__name__)


class SeleccionesStorageManager:
    """Gestiona la persistencia de selecciones manuales del monitor."""

    def __init__(self, directorio: Path | str) -> None:
        self.directorio = Path(directorio)
        self.directorio.mkdir(parents=True, exist_ok=True)
        self.archivo = self.directorio / "selecciones_monitor.json"
        logger.debug(
            "SeleccionesStorageManager inicializado en %s", self.directorio
        )

    def _normalizar_ids(self, valores: Iterable[object]) -> list[str]:
        ids: list[str] = []
        for valor in valores:
            if valor is None:
                continue
            ids.append(str(valor))
        return ids

    def _leer_archivo(self) -> dict:
        if not self.archivo.exists():
            logger.debug("No existe archivo de selecciones, devolviendo vacío")
            return {}

        try:
            with self.archivo.open("r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.debug("Archivo de selecciones no encontrado al leer")
            return {}
        except json.JSONDecodeError as exc:
            logger.error("JSON inválido en selecciones del monitor: %s", exc)
            raise StorageError(f"Archivo de selecciones corrupto: {exc}") from exc
        except PermissionError as exc:
            logger.error("Sin permisos para leer selecciones del monitor: %s", exc)
            raise StorageError(f"Sin permisos de lectura: {exc}") from exc
        except OSError as exc:
            logger.error("Error de I/O al leer selecciones del monitor: %s", exc)
            raise StorageError(f"Error de I/O: {exc}") from exc

    def cargar_selecciones(self) -> tuple[list[str], list[str]]:
        """Carga selecciones de entradas y expedientes."""

        data = self._leer_archivo()
        entradas_raw = data.get("entradas_ids", [])
        expedientes_raw = data.get("expedientes_ids", [])

        if not isinstance(entradas_raw, list):
            logger.warning(
                "Formato inválido para entradas_ids en selecciones; usando lista vacía"
            )
            entradas_raw = []
        if not isinstance(expedientes_raw, list):
            logger.warning(
                "Formato inválido para expedientes_ids en selecciones; usando lista vacía"
            )
            expedientes_raw = []

        entradas_ids = [str(valor) for valor in entradas_raw if valor is not None]
        expedientes_ids = [
            str(valor) for valor in expedientes_raw if valor is not None
        ]

        logger.debug(
            "Cargadas %d selecciones de entradas y %d de expedientes",
            len(entradas_ids),
            len(expedientes_ids),
        )
        return entradas_ids, expedientes_ids

    def guardar_selecciones(
        self,
        entradas_ids: Iterable[object] | None = None,
        expedientes_ids: Iterable[object] | None = None,
    ) -> None:
        """Persiste selecciones de entradas y expedientes."""

        payload = {
            "entradas_ids": self._normalizar_ids(entradas_ids or []),
            "expedientes_ids": self._normalizar_ids(expedientes_ids or []),
        }

        try:
            with self.archivo.open("w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            logger.debug(
                "Selecciones guardadas (%d entradas, %d expedientes)",
                len(payload["entradas_ids"]),
                len(payload["expedientes_ids"]),
            )
        except PermissionError as exc:
            logger.error("Sin permisos para escribir selecciones del monitor: %s", exc)
            raise StorageError(f"Sin permisos de escritura: {exc}") from exc
        except OSError as exc:
            logger.error("Error de I/O al guardar selecciones del monitor: %s", exc)
            raise StorageError(f"Error de I/O: {exc}") from exc


__all__ = ["SeleccionesStorageManager"]
