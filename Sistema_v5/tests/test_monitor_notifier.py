"""Tests para el sistema de notificaciones del monitor.

Este módulo prueba el notificador multiplataforma.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from pjn.monitor.notifier import NotificadorPlyer
from pjn.monitor.exceptions import NotificationError


class TestNotificadorPlyer:
    """Tests para la clase NotificadorPlyer."""

    # =========================================================================
    # Tests de inicialización
    # =========================================================================

    def test_init_con_plyer_disponible(self):
        """Inicialización con plyer disponible."""
        with patch("pjn.monitor.notifier.notification") as mock_notif:
            notificador = NotificadorPlyer()

            assert notificador.disponible is True
            assert notificador.notification is not None

    def test_init_sin_plyer_disponible(self):
        """Inicialización sin plyer (ImportError)."""
        with patch("pjn.monitor.notifier.notification", side_effect=ImportError("plyer not found")):
            # Forzar ImportError en el import dentro de __init__
            with patch.dict("sys.modules", {"plyer": None}):
                notificador = NotificadorPlyer()

                # Debe marcar como no disponible
                assert notificador.disponible is False
                assert notificador.notification is None

    # =========================================================================
    # Tests de notificar() - Casos exitosos
    # =========================================================================

    def test_notificar_con_plyer_disponible(self):
        """notificar() envía notificación si plyer disponible."""
        with patch("pjn.monitor.notifier.notification") as mock_module:
            mock_notify = Mock()
            mock_module.notify = mock_notify

            notificador = NotificadorPlyer()
            notificador.notification = mock_module
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
        with patch("pjn.monitor.notifier.notification") as mock_module:
            mock_notify = Mock()
            mock_module.notify = mock_notify

            notificador = NotificadorPlyer()
            notificador.notification = mock_module
            notificador.disponible = True

            notificador.notificar("Title", "Message", timeout=30)

            mock_notify.assert_called_once_with(
                title="Title",
                message="Message",
                app_name="Monitor PJN",
                timeout=30
            )

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

    # =========================================================================
    # Tests de manejo de errores
    # =========================================================================

    def test_notificar_import_error_usa_fallback(self, capsys):
        """notificar() usa fallback si ImportError durante notify."""
        with patch("pjn.monitor.notifier.notification") as mock_module:
            mock_notify = Mock(side_effect=ImportError("Backend not available"))
            mock_module.notify = mock_notify

            notificador = NotificadorPlyer()
            notificador.notification = mock_module
            notificador.disponible = True

            # No debe lanzar excepción, usa fallback
            notificador.notificar("Title", "Message")

            # Verificar fallback a consola
            captured = capsys.readouterr()
            assert "Title" in captured.out
            assert "Message" in captured.out

    def test_notificar_permission_error_lanza_exception(self):
        """notificar() lanza NotificationError si PermissionError."""
        with patch("pjn.monitor.notifier.notification") as mock_module:
            mock_notify = Mock(side_effect=PermissionError("No permissions"))
            mock_module.notify = mock_notify

            notificador = NotificadorPlyer()
            notificador.notification = mock_module
            notificador.disponible = True

            with pytest.raises(NotificationError, match="Sin permisos"):
                notificador.notificar("Title", "Message")

    def test_notificar_exception_generica_usa_fallback(self, capsys):
        """notificar() usa fallback si excepción genérica."""
        with patch("pjn.monitor.notifier.notification") as mock_module:
            mock_notify = Mock(side_effect=RuntimeError("Unknown error"))
            mock_module.notify = mock_notify

            notificador = NotificadorPlyer()
            notificador.notification = mock_module
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
        with patch("pjn.monitor.notifier.notification") as mock_module:
            mock_notify = Mock()
            mock_module.notify = mock_notify

            notificador = NotificadorPlyer()
            notificador.notification = mock_module
            notificador.disponible = True

            notificador.notificar("Title", "")

            mock_notify.assert_called_once()
            assert mock_notify.call_args[1]["message"] == ""

    def test_notificar_titulo_vacio(self):
        """notificar() acepta título vacío."""
        with patch("pjn.monitor.notifier.notification") as mock_module:
            mock_notify = Mock()
            mock_module.notify = mock_notify

            notificador = NotificadorPlyer()
            notificador.notification = mock_module
            notificador.disponible = True

            notificador.notificar("", "Message")

            mock_notify.assert_called_once()
            assert mock_notify.call_args[1]["title"] == ""

    def test_notificar_caracteres_especiales(self):
        """notificar() maneja caracteres especiales."""
        with patch("pjn.monitor.notifier.notification") as mock_module:
            mock_notify = Mock()
            mock_module.notify = mock_notify

            notificador = NotificadorPlyer()
            notificador.notification = mock_module
            notificador.disponible = True

            titulo_especial = "Título con ñ, á, é"
            mensaje_especial = "Mensaje con símbolos: €, ¿, ¡"

            notificador.notificar(titulo_especial, mensaje_especial)

            mock_notify.assert_called_once()
            assert mock_notify.call_args[1]["title"] == titulo_especial
            assert mock_notify.call_args[1]["message"] == mensaje_especial

    def test_notificar_mensaje_largo(self):
        """notificar() acepta mensajes largos."""
        with patch("pjn.monitor.notifier.notification") as mock_module:
            mock_notify = Mock()
            mock_module.notify = mock_notify

            notificador = NotificadorPlyer()
            notificador.notification = mock_module
            notificador.disponible = True

            mensaje_largo = "A" * 1000  # 1000 caracteres

            notificador.notificar("Title", mensaje_largo)

            mock_notify.assert_called_once()
            assert mock_notify.call_args[1]["message"] == mensaje_largo

    def test_multiples_notificaciones_consecutivas(self):
        """Enviar múltiples notificaciones consecutivas."""
        with patch("pjn.monitor.notifier.notification") as mock_module:
            mock_notify = Mock()
            mock_module.notify = mock_notify

            notificador = NotificadorPlyer()
            notificador.notification = mock_module
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
        with patch("pjn.monitor.notifier.notification") as mock_module:
            mock_notify = Mock()
            mock_module.notify = mock_notify

            notificador = NotificadorPlyer()
            notificador.notification = mock_module
            notificador.disponible = True

            with caplog.at_level("INFO"):
                notificador.notificar("Test", "Message")

            # Verificar que se logueó
            assert any("NOTIFICACIÓN" in record.message for record in caplog.records)
            assert any("Test" in record.message for record in caplog.records)

    def test_notificar_loguea_errores(self, caplog):
        """notificar() loguea errores cuando ocurren."""
        with patch("pjn.monitor.notifier.notification") as mock_module:
            mock_notify = Mock(side_effect=RuntimeError("Test error"))
            mock_module.notify = mock_notify

            notificador = NotificadorPlyer()
            notificador.notification = mock_module
            notificador.disponible = True

            with caplog.at_level("ERROR"):
                notificador.notificar("Title", "Message")

            # Verificar que se logueó el error
            assert any("Error inesperado al enviar notificación" in record.message for record in caplog.records)
