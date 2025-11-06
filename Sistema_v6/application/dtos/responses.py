"""Respuestas de use cases.

Los responses encapsulan los resultados de ejecutar comandos o queries,
proporcionando información estructurada sobre el éxito o fallo de la operación.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generic, TypeVar

from core.domain.entities import (
    Actuacion,
    ActuacionesArchivo,
    Entrada,
    ExpedienteResumen,
)

T = TypeVar("T")


@dataclass(frozen=True)
class Result(Generic[T]):
    """Resultado genérico de una operación.

    Encapsula el éxito o fallo de una operación, siguiendo el patrón Result/Either.

    Attributes:
        success: True si la operación fue exitosa
        value: Valor de retorno si fue exitosa (None si falló)
        error: Mensaje de error si falló (None si fue exitosa)
        error_code: Código de error específico (opcional)
    """

    success: bool
    value: T | None = None
    error: str | None = None
    error_code: str | None = None

    @staticmethod
    def ok(value: T) -> Result[T]:
        """Crea un resultado exitoso.

        Args:
            value: Valor de retorno

        Returns:
            Result exitoso con el valor
        """
        return Result(success=True, value=value)

    @staticmethod
    def fail(error: str, error_code: str | None = None) -> Result[T]:
        """Crea un resultado de fallo.

        Args:
            error: Mensaje de error
            error_code: Código de error (opcional)

        Returns:
            Result fallido con el error
        """
        return Result(success=False, error=error, error_code=error_code)


@dataclass(frozen=True)
class ExtraerExpedientesResponse:
    """Respuesta del comando ExtraerExpedientes.

    Attributes:
        expedientes: Lista de expedientes extraídos
        total: Total de expedientes extraídos
        archivo_guardado: Path del archivo JSON donde se guardó (si aplica)
    """

    expedientes: list[ExpedienteResumen]
    total: int
    archivo_guardado: Path | None = None


@dataclass(frozen=True)
class ExtraerEntradasResponse:
    """Respuesta del comando ExtraerEntradas.

    Attributes:
        entradas: Lista de entradas extraídas
        total: Total de entradas extraídas
        archivo_guardado: Path del archivo JSON donde se guardó (si aplica)
    """

    entradas: list[Entrada]
    total: int
    archivo_guardado: Path | None = None


@dataclass(frozen=True)
class ExtraerActuacionesResponse:
    """Respuesta del comando ExtraerActuaciones.

    Attributes:
        archivo: Archivo con encabezado y actuaciones
        total_actuaciones: Total de actuaciones extraídas
        total_con_archivo: Total de actuaciones con archivo adjunto
        archivo_guardado: Path del archivo JSON donde se guardó (si aplica)
    """

    archivo: ActuacionesArchivo
    total_actuaciones: int
    total_con_archivo: int
    archivo_guardado: Path | None = None


@dataclass(frozen=True)
class FiltrarExpedientesResponse:
    """Respuesta del comando FiltrarExpedientes.

    Attributes:
        expedientes_seleccionados: Lista de expedientes seleccionados
        total: Total de expedientes seleccionados
        archivo_guardado: Path del archivo JSON "sistema" creado
    """

    expedientes_seleccionados: list[ExpedienteResumen]
    total: int
    archivo_guardado: Path


@dataclass(frozen=True)
class CrearWorkspaceResponse:
    """Respuesta del comando CrearWorkspace.

    Attributes:
        workspace_path: Path del workspace creado
        actuaciones_extraidas: Total de actuaciones extraídas (si aplica)
        archivos_descargados: Total de archivos descargados (si aplica)
    """

    workspace_path: Path
    actuaciones_extraidas: int = 0
    archivos_descargados: int = 0


@dataclass(frozen=True)
class CrearWorkspacesResponse:
    """Respuesta del comando CrearWorkspaces.

    Attributes:
        workspaces_creados: Lista de paths de workspaces creados
        total_creados: Total de workspaces creados exitosamente
        total_fallidos: Total de workspaces que fallaron
        errores: Lista de errores ocurridos (numero_expediente, error)
    """

    workspaces_creados: list[Path]
    total_creados: int
    total_fallidos: int
    errores: list[tuple[str, str]]


@dataclass(frozen=True)
class CambioDetectado:
    """Representa un cambio detectado en un expediente.

    Attributes:
        numero_expediente: Número del expediente
        tipo: Tipo de cambio ("nueva_actuacion", "actuacion_modificada", "archivo_nuevo")
        descripcion: Descripción del cambio
        datos_adicionales: Datos adicionales del cambio
    """

    numero_expediente: str
    tipo: str
    descripcion: str
    datos_adicionales: dict[str, Any] | None = None


@dataclass(frozen=True)
class MonitorearExpedientesResponse:
    """Respuesta del comando MonitorearExpedientes.

    Attributes:
        expedientes_verificados: Total de expedientes verificados
        cambios_detectados: Lista de cambios detectados
        total_cambios: Total de cambios detectados
        notificaciones_enviadas: Total de notificaciones enviadas
    """

    expedientes_verificados: int
    cambios_detectados: list[CambioDetectado]
    total_cambios: int
    notificaciones_enviadas: int


@dataclass(frozen=True)
class DescargarArchivoResponse:
    """Respuesta del comando DescargarArchivo.

    Attributes:
        archivo_descargado: Path del archivo descargado
        tamano_bytes: Tamaño del archivo en bytes
        hash: Hash del contenido del archivo
    """

    archivo_descargado: Path
    tamano_bytes: int
    hash: str


@dataclass(frozen=True)
class EstadisticasSistema:
    """Estadísticas generales del sistema.

    Attributes:
        total_expedientes: Total de expedientes en el sistema
        expedientes_activos: Total de expedientes con movimientos recientes
        total_actuaciones: Total de actuaciones (suma de todos los expedientes)
        total_archivos_adjuntos: Total de archivos adjuntos disponibles
        total_archivos_descargados: Total de archivos ya descargados
        total_entradas: Total de entradas (notificaciones/despachos)
        entradas_no_leidas: Total de entradas no leídas
        total_workspaces: Total de workspaces creados
        espacio_utilizado_mb: Espacio en disco utilizado (MB)
    """

    total_expedientes: int
    expedientes_activos: int
    total_actuaciones: int
    total_archivos_adjuntos: int
    total_archivos_descargados: int
    total_entradas: int
    entradas_no_leidas: int
    total_workspaces: int
    espacio_utilizado_mb: float
