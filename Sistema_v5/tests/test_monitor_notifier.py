"""Tests para el sistema de notificaciones del monitor.

Este módulo prueba el notificador multiplataforma.
"""

import pytest
from unittest.mock import Mock

from pjn.monitor.notifier import NotificadorPlyer
from pjn.monitor.exceptions import NotificationError


class TestNotificadorPlyer:
    """Tests para la clase NotificadorPlyer."""

    # =========================================================================
    # Tests de notificar() - Casos exitosos
    # =========================================================================

    def test_notificar_sin_plyer_usa_fallback(self, capsys):
        """notificar() usa fallback a consola si plyer no disponible."""
        notificador = NotificadorPlyer()
        notificador.disponible = False
        notificador.notification = None

        notificador.notificar("Test Title", "Test Message")

        # Verificar output en consola (fallback)
        captured = capsys.readouterr()
        assert "Test Title" in captured.out
        assert "Test Message" in captured.out
        assert "🔔" in captured.out

    def test_notificar_con_plyer_disponible(self):
        """notificar() envía notificación si plyer disponible."""
        notificador = NotificadorPlyer()

        # Mock del notification module
        mock_notify = Mock()
        mock_notification = Mock()
        mock_notification.notify = mock_notify

        notificador.notification = mock_notification
        notificador.disponible = True

        notificador.notificar("Test Title", "Test Message")

        # Verificar que notify fue llamado
        mock_notify.assert_called_once_with(
            title="Test Title",
            message="Test Message",
            app_name="Monitor PJN",
            timeout=10
        )

    def test_notificar_con_timeout_custom(self):
        """notificar() usa timeout personalizado."""
        notificador = NotificadorPlyer()

        mock_notify = Mock()
        mock_notification = Mock()
        mock_notification.notify = mock_notify

        notificador.notification = mock_notification
        notificador.disponible = True

        notificador.notificar("Title", "Message", timeout=30)

        mock_notify.assert_called_once_with(
            title="Title",
            message="Message",
            app_name="Monitor PJN",
            timeout=30
        )

    # =========================================================================
    # Tests de manejo de errores
    # =========================================================================

    def test_notificar_import_error_usa_fallback(self, capsys):
        """notificar() usa fallback si ImportError durante notify."""
        notificador = NotificadorPlyer()

        mock_notify = Mock(side_effect=ImportError("Backend not available"))
        mock_notification = Mock()
        mock_notification.notify = mock_notify

        notificador.notification = mock_notification
        notificador.disponible = True

        # No debe lanzar excepción, usa fallback
        notificador.notificar("Title", "Message")

        # Verificar fallback a consola
        captured = capsys.readouterr()
        assert "Title" in captured.out
        assert "Message" in captured.out

    def test_notificar_permission_error_lanza_exception(self):
        """notificar() lanza NotificationError si PermissionError."""
        notificador = NotificadorPlyer()

        mock_notify = Mock(side_effect=PermissionError("No permissions"))
        mock_notification = Mock()
        mock_notification.notify = mock_notify

        notificador.notification = mock_notification
        notificador.disponible = True

        with pytest.raises(NotificationError, match="Sin permisos"):
            notificador.notificar("Title", "Message")

    def test_notificar_exception_generica_usa_fallback(self, capsys):
        """notificar() usa fallback si excepción genérica."""
        notificador = NotificadorPlyer()

        mock_notify = Mock(side_effect=RuntimeError("Unknown error"))
        mock_notification = Mock()
        mock_notification.notify = mock_notify

        notificador.notification = mock_notification
        notificador.disponible = True

        # No debe lanzar excepción, usa fallback
        notificador.notificar("Title", "Message")

        # Verificar fallback a consola
        captured = capsys.readouterr()
        assert "Title" in captured.out
        assert "Message" in captured.out

    # =========================================================================
    # Tests de edge cases
    # =========================================================================

    def test_notificar_mensaje_vacio(self):
        """notificar() acepta mensaje vacío."""
        notificador = NotificadorPlyer()

        mock_notify = Mock()
        mock_notification = Mock()
        mock_notification.notify = mock_notify

        notificador.notification = mock_notification
        notificador.disponible = True

        notificador.notificar("Title", "")

        mock_notify.assert_called_once()
        assert mock_notify.call_args[1]["message"] == ""

    def test_notificar_titulo_vacio(self):
        """notificar() acepta título vacío."""
        notificador = NotificadorPlyer()

        mock_notify = Mock()
        mock_notification = Mock()
        mock_notification.notify = mock_notify

        notificador.notification = mock_notification
        notificador.disponible = True

        notificador.notificar("", "Message")

        mock_notify.assert_called_once()
        assert mock_notify.call_args[1]["title"] == ""

    def test_notificar_caracteres_especiales(self):
        """notificar() maneja caracteres especiales."""
        notificador = NotificadorPlyer()

        mock_notify = Mock()
        mock_notification = Mock()
        mock_notification.notify = mock_notify

        notificador.notification = mock_notification
        notificador.disponible = True

        titulo_especial = "Título con ñ, á, é"
        mensaje_especial = "Mensaje con símbolos: €, ¿, ¡"

        notificador.notificar(titulo_especial, mensaje_especial)

        mock_notify.assert_called_once()
        assert mock_notify.call_args[1]["title"] == titulo_especial
        assert mock_notify.call_args[1]["message"] == mensaje_especial

    def test_multiples_notificaciones_consecutivas(self):
        """Enviar múltiples notificaciones consecutivas."""
        notificador = NotificadorPlyer()

        mock_notify = Mock()
        mock_notification = Mock()
        mock_notification.notify = mock_notify

        notificador.notification = mock_notification
        notificador.disponible = True

        notificador.notificar("Title 1", "Message 1")
        notificador.notificar("Title 2", "Message 2")
        notificador.notificar("Title 3", "Message 3")

        # Debe haber llamado 3 veces
        assert mock_notify.call_count == 3

    # =========================================================================
    # Tests de integración con logging
    # =========================================================================

    def test_notificar_siempre_loguea(self, caplog):
        """notificar() siempre loguea, tenga o no plyer."""
        notificador = NotificadorPlyer()

        mock_notify = Mock()
        mock_notification = Mock()
        mock_notification.notify = mock_notify

        notificador.notification = mock_notification
        notificador.disponible = True

        with caplog.at_level("INFO"):
            notificador.notificar("Test", "Message")

        # Verificar que se logueó
        assert any("NOTIFICACIÓN" in record.message for record in caplog.records)
        assert any("Test" in record.message for record in caplog.records)

    def test_notificar_loguea_errores(self, caplog):
        """notificar() loguea errores cuando ocurren."""
        notificador = NotificadorPlyer()

        mock_notify = Mock(side_effect=RuntimeError("Test error"))
        mock_notification = Mock()
        mock_notification.notify = mock_notify

        notificador.notification = mock_notification
        notificador.disponible = True

        with caplog.at_level("ERROR"):
            notificador.notificar("Title", "Message")

        # Verificar que se logueó el error
        assert any("Error inesperado al enviar notificación" in record.message for record in caplog.records)
