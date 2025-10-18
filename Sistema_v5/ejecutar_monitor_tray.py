#!/usr/bin/env python3
"""Ejecuta el monitor con indicador de bandeja del sistema.

Este script inicia el monitor PJN con un icono en la bandeja del sistema
que permite:
- Verificar manualmente
- Ver estado
- Controlar el scheduler
- Salir del monitor

Requisitos:
    pip install pystray pillow

Uso:
    python ejecutar_monitor_tray.py
"""

import asyncio
import signal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pjn.monitor.config import MonitorConfig
from pjn.monitor.core import MonitorPJN
from pjn.monitor.scheduler import SchedulerMonitor
from pjn.monitor.tray import MonitorSystemTray, TRAY_AVAILABLE
from pjn.utils.logging import setup_logging, get_logger

setup_logging(level="INFO")
logger = get_logger(__name__)


async def run_monitor_with_tray():
    """Ejecuta el monitor con system tray."""

    # Verificar que pystray esté disponible
    if not TRAY_AVAILABLE:
        logger.error(
            "[ERROR] pystray y pillow son requeridos para la bandeja del sistema.\n"
            "   Instalar con: pip install pystray pillow\n"
            "   O usar: python scripts/monitor_cli.py"
        )
        return 1

    logger.info("=" * 60)
    logger.info("MONITOR PJN - CON BANDEJA DEL SISTEMA")
    logger.info("=" * 60)

    # Cargar configuración
    try:
        config = MonitorConfig.from_file("config/monitor.json")
        logger.info(f"[OK] Configuración cargada desde config/monitor.json")
    except Exception as e:
        logger.warning(f"[ADVERTENCIA] Error al cargar configuración: {e}")
        logger.info("[INFO] Creando configuración por defecto...")
        config = MonitorConfig()
        config.to_file("config/monitor.json")

    # Configuración recomendada para tray
    config.headless = True  # Siempre headless con tray
    logger.info(f"  Modo: {config.modo}")
    logger.info(f"  Headless: {config.headless}")
    logger.info(f"  Verificar entradas: {config.verificar_entradas}")
    logger.info(f"  Verificar expedientes: {config.verificar_expedientes}")
    logger.info("=" * 60)

    # Crear monitor y scheduler
    monitor = MonitorPJN(config)
    monitor.running = True
    scheduler = SchedulerMonitor(monitor)

    # Crear system tray
    tray = MonitorSystemTray(monitor, scheduler)

    # Obtener event loop actual
    loop = asyncio.get_event_loop()

    # Configurar señales para shutdown graceful
    def signal_handler(signum, frame):
        logger.info(f"\n[ADVERTENCIA] Señal {signum} recibida, deteniendo...")
        tray.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Ejecutar verificación inicial
        logger.info("\n>>> Ejecutando verificación inicial...")

        if config.verificar_entradas:
            nuevas = await monitor.verificar_entradas()
            if nuevas:
                logger.info(f"[OK] {len(nuevas)} nuevas entradas detectadas")
                tray.update_icon("yellow")
                await asyncio.sleep(2)
                tray.update_icon("green")
            else:
                logger.info("[OK] Sin nuevas entradas")

        if config.verificar_expedientes:
            cambios = await monitor.verificar_expedientes()
            if cambios:
                logger.info(f"[OK] {len(cambios)} expedientes con cambios")
                tray.update_icon("yellow")
                await asyncio.sleep(2)
                tray.update_icon("green")
            else:
                logger.info("[OK] Sin cambios en expedientes")

        # Iniciar scheduler
        logger.info("\n[TIMER] Iniciando scheduler...")
        scheduler.iniciar()
        logger.info("[OK] Scheduler iniciado")

        logger.info("\n" + "=" * 60)
        logger.info("[OK] MONITOR ACTIVO")
        logger.info("=" * 60)
        logger.info("\n* Busca el icono en la bandeja del sistema")
        logger.info("   Click derecho para ver opciones:\n")
        logger.info("   - Verificar ahora - Ejecuta verificación inmediata")
        logger.info("   - Estado - Ver estado del monitor")
        logger.info("   - Abrir carpeta de datos - Ver archivos guardados")
        logger.info("   - Salir - Detener monitor\n")
        logger.info("=" * 60)

        # Ejecutar tray en thread separado
        tray.run_detached(loop)

        # Mantener el programa corriendo
        while monitor.running and tray._running:
            await asyncio.sleep(1)

        logger.info("\n[ADVERTENCIA] Monitor detenido")
        return 0

    except KeyboardInterrupt:
        logger.info("\n[ADVERTENCIA] Interrupción por teclado")
        tray.stop()
        return 0

    except Exception as e:
        logger.error(f"\n[ERROR] Error fatal: {e}", exc_info=True)
        tray.stop()
        return 1

    finally:
        # Cleanup
        if scheduler:
            scheduler.detener()
        if monitor:
            monitor.detener()


def main():
    """Punto de entrada principal."""
    try:
        exit_code = asyncio.run(run_monitor_with_tray())
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"[ERROR] Error fatal: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
