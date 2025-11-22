"""
Módulo de administración del sistema.

Proporciona funcionalidades para:
- Reseteo del sistema con múltiples niveles
- Gestión de backups
- Estadísticas del sistema
- Limpieza de cache
"""

from .gestor_reseteo import GestorReseteo, NivelReseteo

__all__ = ["GestorReseteo", "NivelReseteo"]
