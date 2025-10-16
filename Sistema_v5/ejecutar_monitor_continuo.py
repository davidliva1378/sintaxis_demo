#!/usr/bin/env python3
"""Script para ejecutar el monitor PJN en modo continuo."""

import asyncio
import signal
import sys
from pathlib import Path

# Agregar directorio al path
sys.path.insert(0, str(Path(__file__).parent))

from pjn.monitor.config import MonitorConfig
from pjn.monitor.core import MonitorPJN
from pjn.monitor.scheduler import SchedulerMonitor
from pjn.utils.logging import setup_logging, get_logger

# Configurar logging con archivo
setup_logging(level="INFO", log_file="logs/monitor.log")
logger = get_logger(__name__)


def signal_handler(signum, frame):
    """Maneja señales de interrupcion."""
    logger.info("\nSeñal de interrupcion recibida. Deteniendo monitor...")
    sys.exit(0)


async def main():
    """Ejecuta el monitor en modo continuo con scheduler."""
    logger.info("=" * 60)
    logger.info("INICIANDO MONITOR PJN - MODO CONTINUO")
    logger.info("=" * 60)

    # Cargar configuracion
    config = MonitorConfig.from_file("config/monitor.json")
    logger.info(f"Configuracion cargada - Modo: {config.modo}")
    logger.info(f"Verificar entradas: {config.verificar_entradas}")
    logger.info(f"Verificar expedientes: {config.verificar_expedientes}")

    # Crear monitor
    monitor = MonitorPJN(config)
    scheduler = SchedulerMonitor(monitor)

    # Configurar manejador de señales
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Iniciar scheduler
        scheduler.iniciar()
        logger.info("\n" + "=" * 60)
        logger.info("MONITOR INICIADO")
        logger.info("Presiona Ctrl+C para detener")
        logger.info("=" * 60 + "\n")

        # Mantener ejecutando
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("\nCtrl+C detectado. Deteniendo...")
    finally:
        scheduler.detener()
        logger.info("Monitor detenido.")


if __name__ == "__main__":
    asyncio.run(main())
