"""Use Cases - Lógica de aplicación.

Este paquete contiene los casos de uso que implementan la lógica de negocio
del sistema.

Los use cases orquestan las operaciones entre entidades de dominio, repositorios
y servicios externos para completar flujos de trabajo específicos.

Use cases principales (workflow):
1. ExtraerExpedientesUseCase: Extraer lista completa → JSON "base"
2. FiltrarExpedientesUseCase: Usuario selecciona → JSON "sistema"
3. CrearWorkspacesUseCase: Generar directorios de expedientes
4. MonitorearExpedientesUseCase: Mantener actualizado el sistema
"""

from .crear_workspaces_use_case import CrearWorkspacesUseCase
from .extraer_expedientes_use_case import ExtraerExpedientesUseCase
from .filtrar_expedientes_use_case import FiltrarExpedientesUseCase
from .monitorear_expedientes_use_case import MonitorearExpedientesUseCase

__all__ = [
    "ExtraerExpedientesUseCase",
    "FiltrarExpedientesUseCase",
    "CrearWorkspacesUseCase",
    "MonitorearExpedientesUseCase",
]
