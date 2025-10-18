#!/usr/bin/env python3
"""Script personalizado del monitor - Ajusta segun tus necesidades."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pjn.monitor.config import MonitorConfig
from pjn.monitor.core import MonitorPJN
from pjn.utils.logging import setup_logging, get_logger

# ==== CONFIGURACION PERSONALIZADA ====

# Nivel de logging: "DEBUG", "INFO", "WARNING", "ERROR"
NIVEL_LOG = "INFO"

# Archivo de configuracion
CONFIG_FILE = "config/monitor.json"

# ======================================

setup_logging(level=NIVEL_LOG)
logger = get_logger(__name__)


async def main():
    """Ejecuta el monitor con configuracion personalizada."""

    # Opcion 1: Cargar desde archivo JSON
    #config = MonitorConfig.from_file(CONFIG_FILE)

    # Opcion 2: Crear configuracion programaticamente (descomentar si prefieres esto)
    config = MonitorConfig(
        modo="automatico",
        headless=False,
        verificar_entradas=True,
        verificar_expedientes=False,
        intervalos_laboral_entradas=10,
        fecha_desde_entradas="13/10/2025",
        fecha_hasta_entradas="17/10/2025",
        notificar_nuevas_entradas=True,
        notificar_errores=True
    )

    logger.info("Iniciando monitor...")
    logger.info(f"  Modo: {config.modo}")
    logger.info(f"  Headless: {config.headless}")
    logger.info(f"  Verificar entradas: {config.verificar_entradas}")
    logger.info(f"  Verificar expedientes: {config.verificar_expedientes}")

    if config.fecha_desde_entradas or config.fecha_hasta_entradas:
        logger.info(f"  Rango fechas: {config.fecha_desde_entradas} - {config.fecha_hasta_entradas}")

    monitor = MonitorPJN(config)

    try:
        # Verificar entradas
        if config.verificar_entradas:
            logger.info("\n--- Verificando entradas ---")
            nuevas = await monitor.verificar_entradas()

            if nuevas:
                logger.info(f"\n✓ {len(nuevas)} nuevas entradas:")
                for i, entrada in enumerate(nuevas, 1):
                    logger.info(f"{i}. {entrada.numero}")
                    logger.info(f"   Fecha: {entrada.fecha}")
                    logger.info(f"   Evento: {entrada.evento}")
                    logger.info(f"   Tipo: {entrada.tipo_evento}")
                    logger.info("")
            else:
                logger.info("\n✓ Sin nuevas entradas")

        # Verificar expedientes
        if config.verificar_expedientes:
            logger.info("\n--- Verificando expedientes ---")
            cambios = await monitor.verificar_expedientes()

            if cambios:
                logger.info(f"\n✓ {len(cambios)} expedientes con cambios:")
                for i, exp in enumerate(cambios, 1):
                    logger.info(f"{i}. {exp.numero}")
                    logger.info(f"   Dependencia: {exp.dependencia}")
                    logger.info(f"   Ultima actuacion: {exp.ultima_actuacion}")
                    logger.info("")
            else:
                logger.info("\n✓ Sin cambios en expedientes")

        logger.info("\n✓ Verificacion completada exitosamente")
        return 0

    except Exception as e:
        logger.error(f"\n✗ Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    resultado = asyncio.run(main())
    sys.exit(resultado)
