"""Sistema de bandeja (system tray) para el monitor PJN.

Este módulo proporciona un indicador en la bandeja del sistema con:
- Icono personalizable
- Menú contextual
- Notificaciones visuales
- Control del monitor (iniciar/detener/verificar)

Requiere: pystray, pillow
"""

from __future__ import annotations

import asyncio
import logging
import os
import threading
from pathlib import Path
from typing import TYPE_CHECKING

from ..utils.logging import get_logger

if TYPE_CHECKING:
    from .core import MonitorPJN
    from .scheduler import SchedulerMonitor

logger = get_logger(__name__)

# Intentar importar dependencias opcionales
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    logger.warning(
        "pystray o pillow no instalados - bandeja del sistema no disponible. "
        "Instalar con: pip install pystray pillow"
    )


def create_icon_image(color: str = "green", size: int = 64) -> "Image.Image | None":
    """Crea una imagen de icono simple para la bandeja.

    Args:
        color: Color del icono ("green", "yellow", "red", "gray")
        size: Tamaño del icono en píxeles

    Returns:
        Image: Imagen PIL para el icono, o None si PIL no está disponible
    """
    if not TRAY_AVAILABLE:
        return None

    # Mapear colores
    color_map = {
        "green": (0, 200, 0),
        "yellow": (255, 200, 0),
        "red": (200, 0, 0),
        "gray": (128, 128, 128),
        "blue": (0, 100, 200),
    }
    rgb_color = color_map.get(color, (128, 128, 128))

    # Crear imagen con fondo transparente (mejor para macOS)
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Dibujar círculo más grande y visible
    margin = size // 10  # Margen más pequeño = círculo más grande
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill=rgb_color + (255,),  # Agregar alpha
        outline=(0, 0, 0, 255),
        width=3  # Borde más grueso
    )

    # Agregar punto blanco en el centro para mejor visibilidad
    center = size // 2
    inner_radius = size // 6
    draw.ellipse(
        [center - inner_radius, center - inner_radius,
         center + inner_radius, center + inner_radius],
        fill=(255, 255, 255, 200),
        outline=None
    )

    return image


class MonitorSystemTray:
    """Indicador de bandeja del sistema para el monitor PJN.

    Este indicador muestra:
    - Estado del monitor (activo/inactivo)
    - Menú con opciones de control
    - Notificaciones visuales de cambios de estado

    Attributes:
        monitor: Instancia del monitor
        scheduler: Instancia del scheduler (opcional)
        icon: Icono de pystray
        loop: Event loop de asyncio para operaciones async
    """

    def __init__(
        self,
        monitor: MonitorPJN,
        scheduler: SchedulerMonitor | None = None
    ):
        """Inicializa el indicador de bandeja.

        Args:
            monitor: Instancia del monitor
            scheduler: Instancia del scheduler (opcional)

        Raises:
            ImportError: Si pystray o pillow no están instalados
        """
        if not TRAY_AVAILABLE:
            raise ImportError(
                "pystray y pillow son requeridos para la bandeja del sistema. "
                "Instalar con: pip install pystray pillow"
            )

        self.monitor = monitor
        self.scheduler = scheduler
        self.icon = None
        self.loop = None
        self._running = False

        logger.info("System tray inicializado")

    def _create_menu(self) -> pystray.Menu:
        """Crea el menú contextual del icono.

        Returns:
            pystray.Menu: Menú con opciones
        """
        return pystray.Menu(
            pystray.MenuItem(
                "Monitor PJN",
                lambda: None,  # Título, no clickeable
                enabled=False
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Verificar ahora",
                self._on_verificar_ahora,
                enabled=lambda item: self.monitor.running
            ),
            pystray.MenuItem(
                "Estado",
                self._on_mostrar_estado
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                self._get_scheduler_label(),
                self._on_toggle_scheduler,
                visible=lambda item: self.scheduler is not None,
                enabled=lambda item: self.scheduler is not None,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Abrir carpeta de datos",
                self._on_abrir_datos
            ),
            pystray.MenuItem(
                "Ver logs",
                self._on_ver_logs
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Salir",
                self._on_salir
            ),
        )

    def _on_verificar_ahora(self, icon, item):
        """Handler para 'Verificar ahora'."""
        logger.info("Verificación manual solicitada desde tray")

        if not self.monitor.running:
            logger.warning("Monitor no está corriendo")
            return

        # Ejecutar verificación en el event loop
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self._verificar_ahora_async(),
                self.loop
            )
        else:
            logger.error("Event loop no disponible")

    async def _verificar_ahora_async(self):
        """Ejecuta verificación inmediata (async)."""
        try:
            logger.info("Ejecutando verificación inmediata...")

            # Verificar entradas y expedientes en paralelo
            if self.monitor.config.verificar_entradas:
                nuevas = await self.monitor.verificar_entradas()
                if nuevas:
                    self.update_icon("yellow")
                    logger.info(f"[OK] {len(nuevas)} nuevas entradas")

            if self.monitor.config.verificar_expedientes:
                cambios = await self.monitor.verificar_expedientes()
                if cambios:
                    self.update_icon("yellow")
                    logger.info(f"[OK] {len(cambios)} expedientes con cambios")

            # Volver a verde después de 3 segundos
            await asyncio.sleep(3)
            self.update_icon("green")

        except Exception as e:
            logger.error(f"Error en verificación: {e}", exc_info=True)
            self.update_icon("red")
            await asyncio.sleep(3)
            self.update_icon("green")

    def _on_mostrar_estado(self, icon, item):
        """Handler para 'Estado'."""
        estado = self.monitor.estado

        info = [
            "=== Estado del Monitor PJN ===",
            f"Running: {self.monitor.running}",
            f"Última verificación entradas: {estado.ultima_verificacion_entradas or 'Nunca'}",
            f"Última verificación expedientes: {estado.ultima_verificacion_expedientes or 'Nunca'}",
            f"Errores consecutivos (entradas): {estado.errores_consecutivos_entradas}",
            f"Errores consecutivos (expedientes): {estado.errores_consecutivos_expedientes}",
        ]

        for line in info:
            logger.info(line)

        # Mostrar notificación
        if self.icon:
            self.icon.notify(
                "\n".join(info[1:]),  # Sin título
                "Estado del Monitor"
            )

    def _on_toggle_scheduler(self, icon, item):
        """Handler para 'Iniciar/Detener'."""
        if not self.scheduler:
            logger.warning("Scheduler no disponible")
            return

        logger.info("Toggle scheduler solicitado")

        mensaje = ""
        try:
            if self._is_scheduler_running():
                logger.info("Deteniendo scheduler desde tray")
                self.scheduler.detener()
                self.monitor.detener()
                self.update_icon("gray")
                self.monitor.running = False
                mensaje = "Scheduler detenido"
            else:
                logger.info("Iniciando scheduler desde tray")
                self.monitor.running = True
                self.scheduler.iniciar()
                self.update_icon("green")
                mensaje = "Scheduler iniciado"
        except Exception as exc:  # pragma: no cover - protección runtime
            logger.error(f"Error al alternar scheduler: {exc}", exc_info=True)

            # Intentar recrear el scheduler como fallback
            try:
                from .scheduler import SchedulerMonitor

                logger.info("Recreando instancia de scheduler tras error")
                self.scheduler = SchedulerMonitor(self.monitor)
                self.monitor.running = True
                self.scheduler.iniciar()
                self.update_icon("green")
                mensaje = "Scheduler reiniciado"
            except Exception as inner_exc:  # pragma: no cover - doble fallo
                logger.error(
                    f"No se pudo recuperar el scheduler: {inner_exc}",
                    exc_info=True
                )
                self.update_icon("red")
                self.monitor.running = False
                mensaje = "Error al controlar el scheduler"

        self._refresh_menu()

        if self.icon and mensaje:
            self.icon.notify(mensaje, "Monitor PJN")

    def _on_abrir_datos(self, icon, item):
        """Handler para 'Abrir carpeta de datos'."""
        import subprocess
        import sys

        directorio = Path(self.monitor.config.directorio_datos)
        directorio.mkdir(parents=True, exist_ok=True)

        logger.info(f"Abriendo carpeta de datos: {directorio}")

        # Abrir explorador de archivos según OS
        if sys.platform == "win32":
            subprocess.run(["explorer", str(directorio)])
        elif sys.platform == "darwin":
            subprocess.run(["open", str(directorio)])
        else:  # Linux
            subprocess.run(["xdg-open", str(directorio)])

    def _on_ver_logs(self, icon, item):
        """Handler para 'Ver logs'."""
        import subprocess
        import sys

        logger.info("Ver logs solicitado")

        log_target = self._find_log_target()
        if log_target.is_file():
            log_target.parent.mkdir(parents=True, exist_ok=True)
            if not log_target.exists():
                log_target.touch()
            mensaje = "Abriendo archivo de logs"
        else:
            log_target.mkdir(parents=True, exist_ok=True)
            mensaje = "Abriendo carpeta de logs"

        logger.info(f"Abriendo logs en: {log_target}")

        try:
            if sys.platform == "win32":
                os.startfile(str(log_target))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.run(["open", str(log_target)], check=False)
            else:
                subprocess.run(["xdg-open", str(log_target)], check=False)
        except Exception as exc:  # pragma: no cover - interacción SO
            logger.error(f"No se pudo abrir los logs: {exc}", exc_info=True)
            if self.icon:
                self.icon.notify(
                    "No se pudo abrir los logs",
                    "Monitor PJN"
                )
        else:
            if self.icon:
                self.icon.notify(mensaje, "Monitor PJN")

    def _on_salir(self, icon, item):
        """Handler para 'Salir'."""
        logger.info("Salida solicitada desde tray")
        self.stop()

    def update_icon(self, color: str = "green"):
        """Actualiza el color del icono.

        Args:
            color: Color del icono ("green", "yellow", "red", "gray")
        """
        if not self.icon:
            return

        new_image = create_icon_image(color)
        if new_image:
            self.icon.icon = new_image

    def run(self, event_loop: asyncio.AbstractEventLoop | None = None):
        """Inicia el indicador de bandeja.

        Este método bloquea hasta que se cierra el icono.

        Args:
            event_loop: Event loop de asyncio para operaciones async
        """
        self.loop = event_loop
        self._running = True

        # Crear icono
        image = create_icon_image("green")
        menu = self._create_menu()

        self.icon = pystray.Icon(
            name="monitor_pjn",
            icon=image,
            title="Monitor PJN - Click aquí",  # Más descriptivo
            menu=menu
        )

        logger.info("Iniciando system tray (bloqueante)...")
        logger.info("BUSCANDO ICONO:")
        logger.info("   Windows: Busca en la bandeja del sistema (esquina inferior derecha)")
        logger.info("   macOS: Busca en la barra superior DERECHA (menu bar)")
        logger.info("   Puede estar al lado del reloj, WiFi, batería, etc.")
        logger.info("   Si no lo ves, intenta hacer click en el icono de la flecha ^ para expandir")
        logger.info("   El icono es un CÍRCULO VERDE")
        logger.info("")
        logger.info("   Una vez que lo veas:")
        logger.info("   - Click DERECHO (o Control + Click) para ver menú")
        logger.info("   - Opciones: Verificar ahora, Estado, Salir")

        # Ejecutar (bloqueante)
        self.icon.run()

        logger.info("System tray detenido")
        self._running = False

    def run_detached(self, event_loop: asyncio.AbstractEventLoop):
        """Inicia el indicador en un thread separado.

        Args:
            event_loop: Event loop de asyncio para operaciones async
        """
        def _run_in_thread():
            self.run(event_loop)

        thread = threading.Thread(target=_run_in_thread, daemon=True)
        thread.start()

        logger.info("System tray iniciado en thread separado")

    def stop(self):
        """Detiene el indicador de bandeja."""
        logger.info("Deteniendo system tray...")

        if self.icon:
            self.icon.stop()

        # Detener monitor y scheduler
        if self.scheduler:
            self.scheduler.detener()

        if self.monitor:
            self.monitor.detener()

        self._running = False

    def _is_scheduler_running(self) -> bool:
        """Indica si el scheduler está actualmente en ejecución."""
        if not self.scheduler:
            return False

        try:
            return bool(getattr(self.scheduler.scheduler, "running", False))
        except Exception:  # pragma: no cover - defensa
            return False

    def _get_scheduler_label(self) -> str:
        """Obtiene la etiqueta dinámica para el control del scheduler."""
        if not self.scheduler:
            return "Scheduler no disponible"

        return "Detener scheduler" if self._is_scheduler_running() else "Iniciar scheduler"

    def _refresh_menu(self) -> None:
        """Regenera el menú cuando cambia el estado del scheduler."""
        if self.icon:
            self.icon.menu = self._create_menu()

    def _find_log_target(self) -> Path:
        """Determina el archivo o carpeta de logs a abrir."""
        for handler in logging.getLogger().handlers:
            if isinstance(handler, logging.FileHandler):
                try:
                    return Path(handler.baseFilename)
                except AttributeError:
                    continue

        candidatos = [
            Path(self.monitor.config.directorio_datos) / "logs" / "monitor.log",
            Path("logs") / "monitor.log",
        ]

        for candidato in candidatos:
            if candidato.exists():
                return candidato

        return Path(self.monitor.config.directorio_datos) / "logs"


__all__ = ["MonitorSystemTray", "create_icon_image", "TRAY_AVAILABLE"]
