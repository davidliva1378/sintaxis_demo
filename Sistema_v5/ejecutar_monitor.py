#!/usr/bin/env python3
"""Script simple para ejecutar el monitor PJN."""

import asyncio
import sys
from pathlib import Path

# Agregar directorio al path si es necesario
sys.path.insert(0, str(Path(__file__).parent))

from pjn.monitor.config import MonitorConfig
from pjn.monitor.core import MonitorPJN
from pjn.utils.logging import setup_logging, get_logger

# Configurar logging
setup_logging(level="INFO")
logger = get_logger(__name__)


async def main():
    """Ejecuta una verificacion del monitor."""
    logger.info("=" * 60)
    logger.info("INICIANDO MONITOR PJN")
    logger.info("=" * 60)

    # Cargar configuracion
    config = MonitorConfig.from_file("config/monitor.json")
    logger.info(f"Configuracion cargada - Modo: {config.modo}")

    # Crear monitor
    monitor = MonitorPJN(config)

    try:
        # Verificar entradas si esta habilitado
        if config.verificar_entradas:
            logger.info("\nVerificando entradas...")
            nuevas_entradas = await monitor.verificar_entradas()

            if nuevas_entradas:
                logger.info(f"✓ {len(nuevas_entradas)} nuevas entradas detectadas:")
                for entrada in nuevas_entradas[:5]:
                    logger.info(f"  - {entrada.numero}: {entrada.evento}")
                if len(nuevas_entradas) > 5:
                    logger.info(f"  ... y {len(nuevas_entradas) - 5} mas")
            else:
                logger.info("✓ Sin nuevas entradas")

        # Verificar expedientes si esta habilitado
        if config.verificar_expedientes:
            logger.info("\nVerificando expedientes...")
            cambios = await monitor.verificar_expedientes()

            if cambios:
                logger.info(f"✓ {len(cambios)} expedientes con cambios:")
                for exp in cambios[:5]:
                    logger.info(f"  - {exp.numero}: {exp.ultima_actuacion}")
                if len(cambios) > 5:
                    logger.info(f"  ... y {len(cambios) - 5} mas")
            else:
                logger.info("✓ Sin cambios en expedientes")

        logger.info("\n" + "=" * 60)
        logger.info("VERIFICACION COMPLETADA")
        logger.info("=" * 60)
        return 0

    except Exception as e:
        logger.error(f"\n✗ Error durante verificacion: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
