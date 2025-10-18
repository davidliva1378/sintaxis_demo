#!/usr/bin/env python3
"""Ejecuta el monitor con status bar en macOS (usando rumps).

Este script es específico para macOS y usa rumps en lugar de pystray
para una mejor compatibilidad con la barra de menú de macOS.

Requisitos:
    pip install rumps

Uso:
    python ejecutar_monitor_statusbar.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pjn.monitor.config import MonitorConfig
from pjn.monitor.core import MonitorPJN
from pjn.monitor.scheduler import SchedulerMonitor
from pjn.monitor.tray_macos import MonitorStatusBar, RUMPS_AVAILABLE
from pjn.utils.logging import setup_logging, get_logger

setup_logging(level="INFO")
logger = get_logger(__name__)


async def verificacion_inicial(monitor: MonitorPJN, statusbar: MonitorStatusBar):
    """Ejecuta verificación inicial del monitor."""
    logger.info("🚀 Ejecutando verificación inicial...")

    try:
        if monitor.config.verificar_entradas:
            nuevas = await monitor.verificar_entradas()
            if nuevas:
                logger.info(f"✅ {len(nuevas)} nuevas entradas detectadas")
                statusbar.update_icon("yellow")
                await asyncio.sleep(2)
                statusbar.update_icon("green")
            else:
                logger.info("✅ Sin nuevas entradas")

        if monitor.config.verificar_expedientes:
            cambios = await monitor.verificar_expedientes()
            if cambios:
                logger.info(f"✅ {len(cambios)} expedientes con cambios")
                statusbar.update_icon("yellow")
                await asyncio.sleep(2)
                statusbar.update_icon("green")
            else:
                logger.info("✅ Sin cambios en expedientes")

    except Exception as e:
        logger.error(f"❌ Error en verificación inicial: {e}", exc_info=True)
        statusbar.update_icon("red")
        await asyncio.sleep(2)
        statusbar.update_icon("green")


def main():
    """Función principal."""

    # Verificar que rumps esté disponible
    if not RUMPS_AVAILABLE:
        logger.error(
            "❌ rumps es requerido para la barra de menú en macOS.\n"
            "   Instalar con: pip install rumps\n"
            "   O usar: python scripts/monitor_cli.py"
        )
        return 1

    logger.info("=" * 60)
    logger.info("MONITOR PJN - STATUS BAR (macOS)")
    logger.info("=" * 60)

    # Cargar configuración
    try:
        config = MonitorConfig.from_file("config/monitor.json")
        logger.info(f"✅ Configuración cargada desde config/monitor.json")
    except Exception as e:
        logger.warning(f"⚠️  Error al cargar configuración: {e}")
        logger.info("📝 Creando configuración por defecto...")
        config = MonitorConfig()
        config.to_file("config/monitor.json")

    # Mostrar configuración
    logger.info(f"  Modo: {config.modo}")
    logger.info(f"  Headless: {config.headless}")
    logger.info(f"  Verificar entradas: {config.verificar_entradas}")
    logger.info(f"  Verificar expedientes: {config.verificar_expedientes}")
    logger.info("=" * 60)

    # Crear monitor y scheduler
    monitor = MonitorPJN(config)
    monitor.running = True
    scheduler = SchedulerMonitor(monitor)

    # Crear status bar
    statusbar = MonitorStatusBar(monitor, scheduler)

    # Ejecutar verificación inicial y scheduler en background
    import threading

    def run_async_loop():
        """Ejecuta el event loop asyncio en un thread separado."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def startup():
            """Inicializa el monitor y scheduler."""
            # Ejecutar verificación inicial
            await verificacion_inicial(monitor, statusbar)

            # Iniciar scheduler (debe hacerse con el loop corriendo)
            logger.info("\n⏰ Iniciando scheduler...")
            scheduler.iniciar()
            logger.info("✅ Scheduler iniciado\n")

        # Programar startup
        loop.create_task(startup())

        # Mantener el loop corriendo para que el scheduler funcione
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            loop.close()

    # Iniciar loop asyncio en thread separado
    async_thread = threading.Thread(target=run_async_loop, daemon=True)
    async_thread.start()

    # Esperar un momento para que se inicialice
    import time
    time.sleep(2)

    # Ejecutar status bar (bloqueante - este es el main loop)
    try:
        statusbar.run()
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupción por teclado")
        statusbar.stop()
        return 0
    except Exception as e:
        logger.error(f"\n❌ Error fatal: {e}", exc_info=True)
        statusbar.stop()
        return 1

    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}", exc_info=True)
        sys.exit(1)
