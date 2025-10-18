"""Sistema de notificaciones multiplataforma para el monitor.

Este módulo proporciona notificaciones usando plyer (multiplataforma)
con fallback a consola si plyer no está disponible.
"""

from __future__ import annotations

from ..utils.logging import get_logger
from .exceptions import NotificationError

logger = get_logger(__name__)


class NotificadorPlyer:
    """Notificador multiplataforma usando plyer.

    Intenta usar plyer para notificaciones nativas del sistema.
    Si plyer no está disponible, usa logging como fallback.
    """

    def __init__(self):
        """Inicializa el notificador y verifica disponibilidad de plyer."""
        self.disponible = False

        try:
            from plyer import notification
            self.notification = notification
            self.disponible = True
            logger.info("Notificaciones habilitadas (plyer)")
        except ImportError:
            logger.warning(
                "plyer no instalado - notificaciones solo en consola. "
                "Instalar con: pip install plyer"
            )
            self.notification = None

    def notificar(self, titulo: str, mensaje: str, timeout: int = 10) -> None:
        """Envía una notificación al sistema.

        Args:
            titulo: Título de la notificación
            mensaje: Mensaje de la notificación
            timeout: Segundos que permanecerá visible (default: 10)
        """
        # Log siempre
        logger.info(f"NOTIFICACIÓN: {titulo} - {mensaje}")

        if not self.disponible or not self.notification:
            # Fallback: solo console output
            print(f"\n{'='*50}")
            print(f"🔔 {titulo}")
            print(f"   {mensaje}")
            print(f"{'='*50}\n")
            return

        try:
            self.notification.notify(
                title=titulo,
                message=mensaje,
                app_name="Monitor PJN",
                timeout=timeout
            )
        except ImportError as e:
            # Backend de notificaciones no disponible
            logger.warning(f"Backend de notificaciones no disponible: {e}")
            # Fallback a consola (no es un error crítico)
            print(f"\n{'='*50}")
            print(f"🔔 {titulo}")
            print(f"   {mensaje}")
            print(f"{'='*50}\n")
        except PermissionError as e:
            # Sin permisos para notificaciones (ej: macOS sin permisos)
            logger.error(f"Sin permisos para notificaciones: {e}")
            raise NotificationError(f"Sin permisos para enviar notificaciones: {e}") from e
        except Exception as e:
            # Otros errores de notificación (último recurso)
            logger.error(f"Error inesperado al enviar notificación: {e}", exc_info=True)
            # Fallback a consola en lugar de fallar
            print(f"\n{'='*50}")
            print(f"🔔 {titulo}")
            print(f"   {mensaje}")
            print(f"{'='*50}\n")


__all__ = ["NotificadorPlyer"]
