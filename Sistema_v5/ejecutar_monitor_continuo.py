#!/usr/bin/env python3
"""Script para ejecutar el monitor PJN en modo continuo.

Soporta tanto monitor.json (legacy) como sistema.json (nuevo).
"""

import asyncio
import signal
import sys
from pathlib import Path

# Agregar directorio al path
sys.path.insert(0, str(Path(__file__).parent))

from pjn import SystemConfig
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

    # Cargar configuracion - priorizar sistema.json si existe
    sistema_path = Path("config/sistema.json")
    monitor_path = Path("config/monitor.json")

    if sistema_path.exists():
        logger.info("Cargando configuración desde sistema.json")
        config = SystemConfig.from_file(sistema_path)
        modo = config.modo_monitor
        verificar_entradas = config.verificar_entradas
        verificar_expedientes = config.verificar_expedientes
    elif monitor_path.exists():
        logger.info("Cargando configuración desde monitor.json (legacy)")
        config = MonitorConfig.from_file(monitor_path)
        modo = config.modo
        verificar_entradas = config.verificar_entradas
        verificar_expedientes = config.verificar_expedientes
    else:
        logger.error("No se encontró archivo de configuración (sistema.json o monitor.json)")
        return 1

    logger.info(f"Configuracion cargada - Modo: {modo}")
    logger.info(f"Verificar entradas: {verificar_entradas}")
    logger.info(f"Verificar expedientes: {verificar_expedientes}")

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
