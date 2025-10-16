"""Gestión de persistencia del estado del monitor.

Este módulo maneja el almacenamiento y recuperación del estado del monitor,
así como el historial de entradas y expedientes.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from ..models import Entrada, ExpedienteResumen
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class EstadoMonitor:
    """Estado persistente del monitor.

    Attributes:
        ultima_verificacion_expedientes: ISO timestamp de última verificación
        ultima_verificacion_entradas: ISO timestamp de última verificación
        errores_consecutivos_expedientes: Contador de errores seguidos
        errores_consecutivos_entradas: Contador de errores seguidos
    """

    ultima_verificacion_expedientes: str | None = None
    ultima_verificacion_entradas: str | None = None
    errores_consecutivos_expedientes: int = 0
    errores_consecutivos_entradas: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EstadoMonitor":
        """Crea instancia desde diccionario.

        Args:
            data: Diccionario con datos del estado

        Returns:
            EstadoMonitor: Instancia creada
        """
        return cls(
            ultima_verificacion_expedientes=data.get("ultima_verificacion_expedientes"),
            ultima_verificacion_entradas=data.get("ultima_verificacion_entradas"),
            errores_consecutivos_expedientes=data.get("errores_consecutivos_expedientes", 0),
            errores_consecutivos_entradas=data.get("errores_consecutivos_entradas", 0),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convierte a diccionario.

        Returns:
            dict: Estado como diccionario
        """
        return asdict(self)


class StorageManager:
    """Gestiona la persistencia de datos del monitor.

    Este gestor maneja tres tipos de archivos:
    - estado_monitor.json: Estado actual del monitor
    - historial_entradas.json: Lista de todas las entradas conocidas
    - historial_expedientes.json: Lista de todos los expedientes conocidos
    """

    def __init__(self, directorio: Path | str):
        """Inicializa el gestor de storage.

        Args:
            directorio: Directorio base donde guardar los datos
        """
        self.directorio = Path(directorio)
        self.directorio.mkdir(parents=True, exist_ok=True)

        self.archivo_estado = self.directorio / "estado_monitor.json"
        self.archivo_entradas = self.directorio / "historial_entradas.json"
        self.archivo_expedientes = self.directorio / "historial_expedientes.json"

        logger.debug(f"StorageManager inicializado en {self.directorio}")

    def cargar_estado(self) -> EstadoMonitor:
        """Carga el estado del monitor desde disco.

        Returns:
            EstadoMonitor: Estado cargado o nuevo si no existe

        """
        if not self.archivo_estado.exists():
            logger.debug("No existe archivo de estado, creando nuevo")
            return EstadoMonitor()

        try:
            with self.archivo_estado.open("r", encoding="utf-8") as f:
                data = json.load(f)
            logger.debug("Estado cargado desde disco")
            return EstadoMonitor.from_dict(data)
        except Exception as e:
            logger.error(f"Error al cargar estado: {e}, creando nuevo")
            return EstadoMonitor()

    def guardar_estado(self, estado: EstadoMonitor) -> None:
        """Guarda el estado del monitor a disco.

        Args:
            estado: Estado a guardar
        """
        try:
            with self.archivo_estado.open("w", encoding="utf-8") as f:
                json.dump(estado.to_dict(), f, indent=2, ensure_ascii=False)
            logger.debug("Estado guardado a disco")
        except Exception as e:
            logger.error(f"Error al guardar estado: {e}")

    def cargar_entradas_conocidas(self) -> list[Entrada]:
        """Carga el historial de entradas conocidas.

        Returns:
            list[Entrada]: Lista de entradas conocidas

        """
        if not self.archivo_entradas.exists():
            logger.debug("No existe historial de entradas")
            return []

        try:
            with self.archivo_entradas.open("r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                logger.warning("Historial de entradas tiene formato inválido")
                return []

            entradas = [Entrada.from_dict(item) for item in data if isinstance(item, dict)]
            logger.debug(f"Cargadas {len(entradas)} entradas desde historial")
            return entradas

        except Exception as e:
            logger.error(f"Error al cargar historial de entradas: {e}")
            return []

    def guardar_entradas(self, entradas: list[Entrada]) -> None:
        """Guarda el historial de entradas a disco.

        Args:
            entradas: Lista de entradas a guardar
        """
        try:
            data = [entrada.to_dict() for entrada in entradas]

            with self.archivo_entradas.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.debug(f"Guardadas {len(entradas)} entradas a disco")
        except Exception as e:
            logger.error(f"Error al guardar entradas: {e}")

    def cargar_expedientes_conocidos(self) -> list[ExpedienteResumen]:
        """Carga el historial de expedientes conocidos.

        Returns:
            list[ExpedienteResumen]: Lista de expedientes conocidos
        """
        if not self.archivo_expedientes.exists():
            logger.debug("No existe historial de expedientes")
            return []

        try:
            with self.archivo_expedientes.open("r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                logger.warning("Historial de expedientes tiene formato inválido")
                return []

            expedientes = [
                ExpedienteResumen.from_dict(item)
                for item in data
                if isinstance(item, dict)
            ]
            logger.debug(f"Cargados {len(expedientes)} expedientes desde historial")
            return expedientes

        except Exception as e:
            logger.error(f"Error al cargar historial de expedientes: {e}")
            return []

    def guardar_expedientes(self, expedientes: list[ExpedienteResumen]) -> None:
        """Guarda el historial de expedientes a disco.

        Args:
            expedientes: Lista de expedientes a guardar
        """
        try:
            data = [exp.to_dict() for exp in expedientes]

            with self.archivo_expedientes.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.debug(f"Guardados {len(expedientes)} expedientes a disco")
        except Exception as e:
            logger.error(f"Error al guardar expedientes: {e}")


__all__ = ["EstadoMonitor", "StorageManager"]
