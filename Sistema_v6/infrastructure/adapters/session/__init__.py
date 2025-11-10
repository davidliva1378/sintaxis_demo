"""Session Management Adapters - Gestión de sesiones del portal PJN.

Este módulo contiene adaptadores para la gestión de sesiones de usuario
en el portal PJN, incluyendo login automático y reutilización de sesiones.
"""

from .playwright_session_manager import reutilizar_sesion_async, iniciar_sesion

__all__ = ["reutilizar_sesion_async", "iniciar_sesion"]
