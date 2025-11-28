"""Interfaces de repositorios para persistencia de datos.

Este módulo define los contratos (interfaces) que deben implementar los repositorios
de la capa de infraestructura para el almacenamiento y recuperación de entidades.

Siguiendo el principio de Inversión de Dependencias, la capa de aplicación define
estas interfaces y la capa de infraestructura las implementa.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from core.domain.entities import (
    Actuacion,
    ActuacionesArchivo,
    Entrada,
    ExpedienteResumen,
)


class IExpedienteRepository(ABC):
    """Interfaz para repositorio de expedientes.

    Define las operaciones de persistencia y consulta de expedientes.
    """

    @abstractmethod
    async def guardar(self, expediente: ExpedienteResumen) -> None:
        """Guarda un expediente en el repositorio.

        Args:
            expediente: Expediente a guardar
        """
        pass

    @abstractmethod
    async def guardar_varios(self, expedientes: Sequence[ExpedienteResumen]) -> None:
        """Guarda múltiples expedientes en el repositorio.

        Args:
            expedientes: Lista de expedientes a guardar
        """
        pass

    @abstractmethod
    async def obtener_por_numero(self, numero: str) -> ExpedienteResumen | None:
        """Obtiene un expediente por su número.

        Args:
            numero: Número del expediente (ej: "FPA-000632-2017")

        Returns:
            Expediente encontrado o None si no existe
        """
        pass

    @abstractmethod
    async def obtener_todos(self) -> list[ExpedienteResumen]:
        """Obtiene todos los expedientes del repositorio.

        Returns:
            Lista de todos los expedientes
        """
        pass

    @abstractmethod
    async def obtener_por_estado(self, estado: str) -> list[ExpedienteResumen]:
        """Obtiene expedientes filtrados por estado de monitoreo.

        Args:
            estado: Estado a filtrar (ej: 'activo', 'pausado')

        Returns:
            Lista de expedientes con ese estado
        """
        pass

    @abstractmethod
    async def obtener_activos(self, dias: int = 30) -> list[ExpedienteResumen]:
        """Obtiene expedientes con movimientos recientes.

        Args:
            dias: Número de días hacia atrás para considerar "activo"

        Returns:
            Lista de expedientes activos
        """
        pass

    @abstractmethod
    async def recargar(self) -> None:
        """Recarga los expedientes desde el almacenamiento, invalidando la caché."""
        pass

    @abstractmethod
    async def filtrar_por_dependencia(self, dependencia: str) -> list[ExpedienteResumen]:
        """Filtra expedientes por dependencia.

        Args:
            dependencia: Nombre de la dependencia (puede ser parcial)

        Returns:
            Lista de expedientes de esa dependencia
        """
        pass

    @abstractmethod
    async def existe(self, numero: str) -> bool:
        """Verifica si existe un expediente con el número dado.

        Args:
            numero: Número del expediente

        Returns:
            True si existe, False en caso contrario
        """
        pass

    @abstractmethod
    async def eliminar(self, numero: str) -> bool:
        """Elimina un expediente del repositorio.

        Args:
            numero: Número del expediente a eliminar

        Returns:
            True si se eliminó, False si no existía
        """
        pass

    @abstractmethod
    async def contar(self) -> int:
        """Cuenta el total de expedientes en el repositorio.

        Returns:
            Número total de expedientes
        """
        pass


class IActuacionRepository(ABC):
    """Interfaz para repositorio de actuaciones.

    Define las operaciones de persistencia y consulta de actuaciones judiciales.
    """

    @abstractmethod
    async def guardar_archivo(
        self, numero_expediente: str, archivo: ActuacionesArchivo
    ) -> None:
        """Guarda un archivo completo de actuaciones para un expediente.

        Args:
            numero_expediente: Número del expediente
            archivo: Archivo con encabezado y actuaciones
        """
        pass

    @abstractmethod
    async def obtener_archivo(
        self, numero_expediente: str
    ) -> ActuacionesArchivo | None:
        """Obtiene el archivo de actuaciones de un expediente.

        Args:
            numero_expediente: Número del expediente

        Returns:
            Archivo de actuaciones o None si no existe
        """
        pass

    @abstractmethod
    async def obtener_actuaciones(
        self, numero_expediente: str
    ) -> tuple[Actuacion, ...] | None:
        """Obtiene solo las actuaciones de un expediente (sin encabezado).

        Args:
            numero_expediente: Número del expediente

        Returns:
            Tupla de actuaciones o None si no existe
        """
        pass

    @abstractmethod
    async def obtener_por_indice(
        self, numero_expediente: str, indice: int
    ) -> Actuacion | None:
        """Obtiene una actuación específica por índice.

        Args:
            numero_expediente: Número del expediente
            indice: Índice de la actuación

        Returns:
            Actuación encontrada o None
        """
        pass

    @abstractmethod
    async def obtener_con_archivo(
        self, numero_expediente: str
    ) -> tuple[Actuacion, ...]:
        """Obtiene actuaciones que tienen archivo adjunto.

        Args:
            numero_expediente: Número del expediente

        Returns:
            Tupla de actuaciones con archivo
        """
        pass

    @abstractmethod
    async def existe(self, numero_expediente: str) -> bool:
        """Verifica si existen actuaciones para un expediente.

        Args:
            numero_expediente: Número del expediente

        Returns:
            True si existen actuaciones, False en caso contrario
        """
        pass


class IEntradaRepository(ABC):
    """Interfaz para repositorio de entradas (notificaciones y despachos).

    Define las operaciones de persistencia y consulta de entradas del PJN.
    """

    @abstractmethod
    async def guardar(self, entrada: Entrada) -> None:
        """Guarda una entrada en el repositorio.

        Args:
            entrada: Entrada a guardar
        """
        pass

    @abstractmethod
    async def guardar_varias(self, entradas: Sequence[Entrada]) -> None:
        """Guarda múltiples entradas en el repositorio.

        Args:
            entradas: Lista de entradas a guardar
        """
        pass

    @abstractmethod
    async def obtener_todas(self) -> list[Entrada]:
        """Obtiene todas las entradas del repositorio.

        Returns:
            Lista de todas las entradas
        """
        pass

    @abstractmethod
    async def obtener_por_expediente(self, numero: str) -> list[Entrada]:
        """Obtiene todas las entradas de un expediente específico.

        Args:
            numero: Número del expediente

        Returns:
            Lista de entradas del expediente
        """
        pass

    @abstractmethod
    async def obtener_no_leidas(self) -> list[Entrada]:
        """Obtiene entradas que no han sido marcadas como leídas.

        Returns:
            Lista de entradas no leídas
        """
        pass

    @abstractmethod
    async def marcar_como_leida(self, entrada: Entrada) -> None:
        """Marca una entrada como leída.

        Args:
            entrada: Entrada a marcar como leída
        """
        pass

    @abstractmethod
    async def contar(self) -> int:
        """Cuenta el total de entradas en el repositorio.

        Returns:
            Número total de entradas
        """
        pass

    @abstractmethod
    async def contar_no_leidas(self) -> int:
        """Cuenta el total de entradas no leídas.

        Returns:
            Número de entradas no leídas
        """
        pass
