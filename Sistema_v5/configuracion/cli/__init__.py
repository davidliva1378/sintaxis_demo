"""CLI para gestión de configuración del Sistema PJN.

Este módulo proporciona herramientas de línea de comandos para:
- Ver configuración actual
- Editar configuración mediante wizard interactivo
- Actualizar campos específicos
- Crear backups manuales
"""

from __future__ import annotations

from .configuracion import main

__all__ = ["main"]
