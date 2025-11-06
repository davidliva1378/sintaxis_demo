"""Adapter de notificaciones.

Implementa INotificacionPort para enviar notificaciones por diferentes canales.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from application.ports import INotificacionPort

if TYPE_CHECKING:
    from infrastructure.config import NotificacionesSettings

logger = logging.getLogger(__name__)


class NotificacionAdapter(INotificacionPort):
    """Implementación de INotificacionPort para envío de notificaciones.

    Este adapter envía notificaciones por múltiples canales según configuración.

    Attributes:
        settings: Configuración de notificaciones
    """

    def __init__(self, settings: NotificacionesSettings):
        """Inicializa el adapter.

        Args:
            settings: Configuración de notificaciones
        """
        self._settings = settings

    async def notificar_escritorio(
        self,
        titulo: str,
        mensaje: str,
        *,
        urgencia: str = "normal",
    ) -> None:
        """Envía una notificación del sistema operativo.

        Args:
            titulo: Título de la notificación
            mensaje: Cuerpo del mensaje
            urgencia: Nivel de urgencia ("normal", "alta", "critica")

        Raises:
            NotificacionError: Si ocurre un error al enviar
        """
        if not self._settings.habilitar_escritorio:
            logger.debug("Notificaciones de escritorio deshabilitadas")
            return

        try:
            # Usar plyer para notificaciones de escritorio
            from plyer import notification

            notification.notify(
                title=titulo,
                message=mensaje,
                app_name="Sistema PJN",
                timeout=10,
            )
            logger.info(f"Notificación de escritorio enviada: {titulo}")
        except Exception as e:
            logger.error(f"Error al enviar notificación de escritorio: {e}")
            raise

    async def notificar_email(
        self,
        destinatario: str,
        asunto: str,
        cuerpo: str,
        *,
        html: bool = False,
    ) -> None:
        """Envía una notificación por email.

        Args:
            destinatario: Dirección de email del destinatario
            asunto: Asunto del email
            cuerpo: Cuerpo del mensaje
            html: Si True, el cuerpo es HTML

        Raises:
            NotificacionError: Si ocurre un error al enviar
        """
        if not self._settings.habilitar_email:
            logger.debug("Notificaciones por email deshabilitadas")
            return

        if not self._settings.email_smtp_host:
            logger.warning("SMTP no configurado, no se puede enviar email")
            return

        try:
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText

            # Crear mensaje
            msg = MIMEMultipart("alternative")
            msg["Subject"] = asunto
            msg["From"] = self._settings.email_from or "noreply@sistemapjn.com"
            msg["To"] = destinatario

            # Añadir cuerpo
            mime_type = "html" if html else "plain"
            part = MIMEText(cuerpo, mime_type)
            msg.attach(part)

            # Enviar
            with smtplib.SMTP(
                self._settings.email_smtp_host, self._settings.email_smtp_port
            ) as server:
                server.starttls()
                if self._settings.email_password:
                    server.login(
                        self._settings.email_from or "",
                        self._settings.email_password,
                    )
                server.send_message(msg)

            logger.info(f"Email enviado a {destinatario}: {asunto}")
        except Exception as e:
            logger.error(f"Error al enviar email: {e}")
            raise

    async def notificar_telegram(
        self,
        mensaje: str,
        *,
        chat_id: str | None = None,
    ) -> None:
        """Envía una notificación por Telegram.

        Args:
            mensaje: Mensaje a enviar (soporta Markdown)
            chat_id: ID del chat (None para usar default de config)

        Raises:
            NotificacionError: Si ocurre un error al enviar
        """
        if not self._settings.habilitar_telegram:
            logger.debug("Notificaciones por Telegram deshabilitadas")
            return

        if not self._settings.telegram_bot_token:
            logger.warning("Bot de Telegram no configurado")
            return

        try:
            import httpx

            # Usar chat_id proporcionado o default de config
            target_chat_id = chat_id or self._settings.telegram_chat_id

            if not target_chat_id:
                logger.warning("Chat ID de Telegram no configurado")
                return

            # Enviar mensaje via API de Telegram
            url = f"https://api.telegram.org/bot{self._settings.telegram_bot_token}/sendMessage"
            data = {
                "chat_id": target_chat_id,
                "text": mensaje,
                "parse_mode": "Markdown",
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data)
                response.raise_for_status()

            logger.info(f"Mensaje de Telegram enviado a chat {target_chat_id}")
        except Exception as e:
            logger.error(f"Error al enviar mensaje de Telegram: {e}")
            raise
