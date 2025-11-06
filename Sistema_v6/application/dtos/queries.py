"""Queries de aplicación (Query pattern).

Las queries encapsulan solicitudes de información sin modificar el estado del sistema.

Siguiendo el patrón CQRS (Command Query Responsibility Segregation), las queries
representan operaciones de solo lectura.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ObtenerExpedienteQuery:
    """Query para obtener un expediente por su número.

    Attributes:
        numero: Número del expediente (ej: "FPA-000632-2017")
    """

    numero: str


@dataclass(frozen=True)
class ListarExpedientesQuery:
    """Query para listar todos los expedientes.

    Attributes:
        filtro_dependencia: Filtrar por dependencia (opcional)
        filtro_situacion: Filtrar por situación (opcional)
        solo_activos: Si True, solo expedientes con movimientos recientes
        dias_actividad: Días hacia atrás para considerar "activo"
    """

    filtro_dependencia: str | None = None
    filtro_situacion: str | None = None
    solo_activos: bool = False
    dias_actividad: int = 30


@dataclass(frozen=True)
class ObtenerActuacionesQuery:
    """Query para obtener actuaciones de un expediente.

    Attributes:
        numero_expediente: Número del expediente
        solo_con_archivo: Si True, solo actuaciones con archivo adjunto
    """

    numero_expediente: str
    solo_con_archivo: bool = False


@dataclass(frozen=True)
class ObtenerEntradasQuery:
    """Query para obtener entradas (notificaciones/despachos).

    Attributes:
        numero_expediente: Filtrar por expediente (None para todas)
        solo_no_leidas: Si True, solo entradas no leídas
    """

    numero_expediente: str | None = None
    solo_no_leidas: bool = False


@dataclass(frozen=True)
class VerificarWorkspaceQuery:
    """Query para verificar si existe el workspace de un expediente.

    Attributes:
        numero_expediente: Número del expediente
        base_path: Directorio base de workspaces
    """

    numero_expediente: str
    base_path: Path


@dataclass(frozen=True)
class ListarWorkspacesQuery:
    """Query para listar todos los workspaces existentes.

    Attributes:
        base_path: Directorio base de workspaces
    """

    base_path: Path


@dataclass(frozen=True)
class ObtenerEstadisticasQuery:
    """Query para obtener estadísticas del sistema.

    Attributes:
        incluir_expedientes: Si True, incluye estadísticas de expedientes
        incluir_actuaciones: Si True, incluye estadísticas de actuaciones
        incluir_entradas: Si True, incluye estadísticas de entradas
    """

    incluir_expedientes: bool = True
    incluir_actuaciones: bool = True
    incluir_entradas: bool = True


@dataclass(frozen=True)
class BuscarExpedientesQuery:
    """Query para buscar expedientes por criterios flexibles.

    Attributes:
        texto: Buscar en número, carátula o dependencia
        fecha_desde: Filtrar por fecha de última actuación desde
        fecha_hasta: Filtrar por fecha de última actuación hasta
        limite: Número máximo de resultados (None = sin límite)
    """

    texto: str | None = None
    fecha_desde: str | None = None
    fecha_hasta: str | None = None
    limite: int | None = None
