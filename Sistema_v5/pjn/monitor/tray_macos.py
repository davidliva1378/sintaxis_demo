"""Sistema de bandeja para macOS usando rumps.

Este módulo es específico para macOS y usa rumps (Ridiculously Uncomplicated macOS Python Statusbar apps)
que es más confiable que pystray en macOS.

Requiere: rumps
"""

from __future__ import annotations

import asyncio
import subprocess
import threading
from pathlib import Path
from typing import TYPE_CHECKING

from ..utils.logging import get_logger

if TYPE_CHECKING:
    from .core import MonitorPJN
    from .scheduler import SchedulerMonitor

logger = get_logger(__name__)

# Intentar importar rumps
try:
    import rumps
    RUMPS_AVAILABLE = True
except ImportError:
    RUMPS_AVAILABLE = False
    logger.warning(
        "rumps no instalado - bandeja del sistema no disponible. "
        "Instalar con: pip install rumps"
    )


class MonitorStatusBarApp(rumps.App):
    """Aplicación de status bar para macOS.

    Esta clase hereda de rumps.App y gestiona el icono en la barra de menú.
    """

    def __init__(self, monitor: MonitorPJN, scheduler: SchedulerMonitor | None = None):
        """Inicializa la aplicación de status bar.

        Args:
            monitor: Instancia del monitor
            scheduler: Instancia del scheduler (opcional)
        """
        # Icono simple de texto (rumps lo renderiza automáticamente)
        super().__init__(
            name="Monitor PJN",
            title="🟢",  # Círculo verde como icono inicial
            quit_button=None  # Desactivar botón de salir por defecto
        )

        self.monitor = monitor
        self.scheduler = scheduler
        self.loop = None

        # Crear menú
        self.menu = [
            rumps.MenuItem("Verificar ahora", callback=self.verificar_ahora),
            rumps.MenuItem("Estado", callback=self.mostrar_estado),
            rumps.separator,
            rumps.MenuItem("Abrir carpeta de datos", callback=self.abrir_datos),
            rumps.separator,
            rumps.MenuItem("Salir", callback=self.salir),
        ]

        logger.info("Status bar app inicializada")

    def verificar_ahora(self, sender):
        """Handler para verificar ahora."""
        logger.info("Verificación manual solicitada")

        # Cambiar icono a amarillo
        self.title = "🟡"

        # Ejecutar verificación en thread
        def _verificar():
            try:
                # Crear un nuevo event loop para este thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                # Ejecutar verificaciones
                if self.monitor.config.verificar_entradas:
                    nuevas = loop.run_until_complete(self.monitor.verificar_entradas())
                    if nuevas:
                        rumps.notification(
                            title="Nuevas Entradas",
                            subtitle=f"{len(nuevas)} entradas detectadas",
                            message="",
                            sound=True
                        )

                if self.monitor.config.verificar_expedientes:
                    cambios = loop.run_until_complete(self.monitor.verificar_expedientes())
                    if cambios:
                        rumps.notification(
                            title="Cambios en Expedientes",
                            subtitle=f"{len(cambios)} expedientes con cambios",
                            message="",
                            sound=True
                        )

                # Volver a verde después de 2 segundos
                import time
                time.sleep(2)
                self.title = "🟢"

            except Exception as e:
                logger.error(f"Error en verificación: {e}", exc_info=True)
                self.title = "🔴"
                import time
                time.sleep(2)
                self.title = "🟢"

        # Ejecutar en thread separado
        thread = threading.Thread(target=_verificar, daemon=True)
        thread.start()

    def mostrar_estado(self, sender):
        """Handler para mostrar estado."""
        estado = self.monitor.estado

        mensaje = (
            f"Running: {self.monitor.running}\n"
            f"Última verificación entradas:\n  {estado.ultima_verificacion_entradas or 'Nunca'}\n"
            f"Última verificación expedientes:\n  {estado.ultima_verificacion_expedientes or 'Nunca'}\n"
            f"Errores consecutivos:\n"
            f"  Entradas: {estado.errores_consecutivos_entradas}\n"
            f"  Expedientes: {estado.errores_consecutivos_expedientes}"
        )

        rumps.alert(
            title="Estado del Monitor PJN",
            message=mensaje,
            ok="OK"
        )

    def abrir_datos(self, sender):
        """Handler para abrir carpeta de datos."""
        directorio = Path(self.monitor.config.directorio_datos)
        directorio.mkdir(parents=True, exist_ok=True)

        logger.info(f"Abriendo carpeta: {directorio}")
        subprocess.run(["open", str(directorio)])

    def salir(self, sender):
        """Handler para salir."""
        logger.info("Salida solicitada")

        # Detener scheduler
        if self.scheduler:
            self.scheduler.detener()

        # Detener monitor
        if self.monitor:
            self.monitor.detener()

        # Cerrar app
        rumps.quit_application()

    def update_icon(self, color: str = "green"):
        """Actualiza el color del icono.

        Args:
            color: Color del icono ("green", "yellow", "red", "gray")
        """
        color_map = {
            "green": "🟢",
            "yellow": "🟡",
            "red": "🔴",
            "gray": "⚪",
            "blue": "🔵",
        }

        emoji = color_map.get(color, "⚪")
        self.title = emoji


class MonitorStatusBar:
    """Wrapper para ejecutar la app de status bar.

    Esta clase permite integrar la app de rumps con el monitor existente.
    """

    def __init__(
        self,
        monitor: MonitorPJN,
        scheduler: SchedulerMonitor | None = None
    ):
        """Inicializa el status bar.

        Args:
            monitor: Instancia del monitor
            scheduler: Instancia del scheduler (opcional)

        Raises:
            ImportError: Si rumps no está instalado
        """
        if not RUMPS_AVAILABLE:
            raise ImportError(
                "rumps es requerido para la bandeja del sistema en macOS. "
                "Instalar con: pip install rumps"
            )

        self.monitor = monitor
        self.scheduler = scheduler
        self.app = MonitorStatusBarApp(monitor, scheduler)
        self._running = False

        logger.info("Status bar wrapper inicializado")

    def run(self):
        """Inicia el status bar (bloqueante).

        Este método bloquea hasta que se cierra la app.
        """
        self._running = True

        logger.info("=" * 60)
        logger.info("🚀 MONITOR PJN - STATUS BAR ACTIVO")
        logger.info("=" * 60)
        logger.info("")
        logger.info("✅ Busca el icono 🟢 en la barra de menú superior derecha")
        logger.info("   (junto al reloj, WiFi, batería, etc.)")
        logger.info("")
        logger.info("   Haz click en el icono para ver el menú:")
        logger.info("   • Verificar ahora - Ejecuta verificación inmediata")
        logger.info("   • Estado - Ver información del monitor")
        logger.info("   • Abrir carpeta de datos - Ver archivos guardados")
        logger.info("   • Salir - Detener monitor")
        logger.info("")
        logger.info("=" * 60)

        # Ejecutar app (bloqueante)
        self.app.run()

        logger.info("Status bar detenido")
        self._running = False

    def stop(self):
        """Detiene el status bar."""
        logger.info("Deteniendo status bar...")

        if self.scheduler:
            self.scheduler.detener()

        if self.monitor:
            self.monitor.detener()

        rumps.quit_application()
        self._running = False

    def update_icon(self, color: str = "green"):
        """Actualiza el color del icono.

        Args:
            color: Color del icono
        """
        self.app.update_icon(color)


__all__ = ["MonitorStatusBar", "MonitorStatusBarApp", "RUMPS_AVAILABLE"]
