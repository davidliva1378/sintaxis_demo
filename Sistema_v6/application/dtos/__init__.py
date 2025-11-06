"""DTOs - Data Transfer Objects.

Este paquete contiene los objetos de transferencia de datos usados para
comunicación entre capas:

- commands.py: Comandos (operaciones que modifican estado)
- queries.py: Consultas (operaciones de solo lectura)
- responses.py: Respuestas estructuradas de use cases

Los DTOs siguen el patrón CQRS (Command Query Responsibility Segregation)
separando comandos (escritura) de queries (lectura).
"""

from .commands import (
    CrearWorkspaceCommand,
    CrearWorkspacesCommand,
    DescargarArchivoCommand,
    ExtraerActuacionesCommand,
    ExtraerEntradasCommand,
    ExtraerExpedientesCommand,
    FiltrarExpedientesCommand,
    MarcarEntradaLeidaCommand,
    MonitorearExpedientesCommand,
)
from .queries import (
    BuscarExpedientesQuery,
    ListarExpedientesQuery,
    ListarWorkspacesQuery,
    ObtenerActuacionesQuery,
    ObtenerEntradasQuery,
    ObtenerEstadisticasQuery,
    ObtenerExpedienteQuery,
    VerificarWorkspaceQuery,
)
from .responses import (
    CambioDetectado,
    CrearWorkspaceResponse,
    CrearWorkspacesResponse,
    DescargarArchivoResponse,
    EstadisticasSistema,
    ExtraerActuacionesResponse,
    ExtraerEntradasResponse,
    ExtraerExpedientesResponse,
    FiltrarExpedientesResponse,
    MonitorearExpedientesResponse,
    Result,
)

__all__ = [
    # Commands
    "ExtraerExpedientesCommand",
    "ExtraerEntradasCommand",
    "ExtraerActuacionesCommand",
    "FiltrarExpedientesCommand",
    "CrearWorkspaceCommand",
    "CrearWorkspacesCommand",
    "MonitorearExpedientesCommand",
    "DescargarArchivoCommand",
    "MarcarEntradaLeidaCommand",
    # Queries
    "ObtenerExpedienteQuery",
    "ListarExpedientesQuery",
    "ObtenerActuacionesQuery",
    "ObtenerEntradasQuery",
    "VerificarWorkspaceQuery",
    "ListarWorkspacesQuery",
    "ObtenerEstadisticasQuery",
    "BuscarExpedientesQuery",
    # Responses
    "Result",
    "ExtraerExpedientesResponse",
    "ExtraerEntradasResponse",
    "ExtraerActuacionesResponse",
    "FiltrarExpedientesResponse",
    "CrearWorkspaceResponse",
    "CrearWorkspacesResponse",
    "MonitorearExpedientesResponse",
    "DescargarArchivoResponse",
    "CambioDetectado",
    "EstadisticasSistema",
]
