#!/usr/bin/env python3
"""Script personalizado del monitor basado en la configuración unificada.

Prioriza variables de entorno ``SISTEMA_*`` y luego ``config/sistema.json``.
"""

import asyncio
import os
import sys
from pathlib import Path

from Sistema_v5.pjn import SystemConfig
from Sistema_v5.pjn.monitor.config import MonitorConfig
from Sistema_v5.pjn.monitor.core import MonitorPJN
from Sistema_v5.pjn.system_config import ENV_FIELD_MAP
from Sistema_v5.pjn.utils.logging import get_logger, setup_logging

# ==== CONFIGURACION PERSONALIZADA ====

# Nivel de logging: "DEBUG", "INFO", "WARNING", "ERROR"
NIVEL_LOG = "INFO"

# Archivo de configuración unificada
CONFIG_FILE = "config/sistema.json"

# Prefijo para variables de entorno que sobrescriben la configuración
ENV_PREFIX = "SISTEMA_"

# ======================================

setup_logging(level=NIVEL_LOG)
logger = get_logger(__name__)


async def main():
    """Ejecuta el monitor con configuracion personalizada."""

    # Detectar si existen overrides por variables de entorno
    env_overrides = [
        f"{ENV_PREFIX}{suffix}" for suffix in ENV_FIELD_MAP.values()
        if os.getenv(f"{ENV_PREFIX}{suffix}") is not None
    ]

    if env_overrides:
        logger.info(
            "Usando configuración unificada desde variables de entorno (%s)",
            ", ".join(sorted(env_overrides)),
        )
        system_config = SystemConfig.from_env(prefix=ENV_PREFIX)
        config_source = f"variables de entorno ({ENV_PREFIX}*)"
    else:
        config_path = Path(CONFIG_FILE)

        if config_path.exists():
            logger.info("Usando configuración unificada desde %s", config_path)
            system_config = SystemConfig.from_file(config_path)
            config_source = str(config_path)
        else:
            logger.warning(
                "No se encontró %s. Generando configuración por defecto.",
                config_path,
            )
            system_config = SystemConfig()
            system_config.to_file(config_path)
            logger.info("Archivo creado en %s", config_path)
            config_source = str(config_path)

    config = MonitorConfig.from_system_config(system_config)

    logger.info("Iniciando monitor...")
    logger.info("  Fuente configuración: %s", config_source)
    logger.info("  Modo: %s", config.modo)
    logger.info("  Headless: %s", config.headless)
    logger.info("  Verificar entradas: %s", config.verificar_entradas)
    logger.info("  Verificar expedientes: %s", config.verificar_expedientes)

    if config.fecha_desde_entradas or config.fecha_hasta_entradas:
        logger.info(
            "  Rango fechas: %s - %s",
            config.fecha_desde_entradas,
            config.fecha_hasta_entradas,
        )

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
