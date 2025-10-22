#!/usr/bin/env python3
"""Script simple para ejecutar el monitor PJN.

Soporta tanto monitor.json (legacy) como sistema.json (nuevo).
"""

import asyncio
import sys
from pathlib import Path

from Sistema_v5.pjn import SystemConfig
from Sistema_v5.pjn.monitor.config import MonitorConfig
from Sistema_v5.pjn.monitor.core import MonitorPJN
from Sistema_v5.pjn.utils.logging import get_logger, setup_logging

# Configurar logging
setup_logging(level="INFO")
logger = get_logger(__name__)


async def main():
    """Ejecuta una verificacion del monitor."""
    logger.info("=" * 60)
    logger.info("INICIANDO MONITOR PJN")
    logger.info("=" * 60)

    # Cargar configuracion - priorizar sistema.json si existe
    sistema_path = Path("config/sistema.json")
    monitor_path = Path("config/monitor.json")

    if sistema_path.exists():
        logger.info("Cargando configuración desde sistema.json")
        config = SystemConfig.from_file(sistema_path)
        modo = config.modo_monitor
    elif monitor_path.exists():
        logger.info("Cargando configuración desde monitor.json (legacy)")
        config = MonitorConfig.from_file(monitor_path)
        modo = config.modo
    else:
        logger.error("No se encontró archivo de configuración (sistema.json o monitor.json)")
        return 1

    logger.info(f"Configuracion cargada - Modo: {modo}")

    # Crear monitor
    monitor = MonitorPJN(config)

    # Determinar flags de verificación según tipo de config
    if isinstance(config, SystemConfig):
        verificar_entradas = config.verificar_entradas
        verificar_expedientes = config.verificar_expedientes
    else:
        verificar_entradas = config.verificar_entradas
        verificar_expedientes = config.verificar_expedientes

    try:
        # Verificar entradas si esta habilitado
        if verificar_entradas:
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
        if verificar_expedientes:
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
