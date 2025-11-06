"""CLI Module - Command Line Interface with Click and Rich.

Este módulo implementa la interfaz de línea de comandos del sistema
utilizando Click para la estructura de comandos y Rich para la
presentación visual.

Comandos disponibles:
    - extraer: Extrae expedientes del PJN
    - filtrar: Filtra expedientes por selección
    - workspace: Crea workspaces para expedientes
    - monitorear: Monitorea cambios en expedientes
    - info: Muestra información del sistema
"""

from .main import cli

__all__ = ["cli"]
