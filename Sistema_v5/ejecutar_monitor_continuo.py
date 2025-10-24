"""Monitor continuo del PJN usando la configuración unificada (`config/sistema.json`).

El script verifica primero variables de entorno con el prefijo ``SISTEMA_`` para
sobrescribir valores y, si no hay overrides, lee ``config/sistema.json``. Si el
archivo no existe se genera con valores por defecto. Para compatibilidad con
entornos heredados se acepta ``config/monitor.json``.
"""

from __future__ import annotations

import asyncio
import os
import signal
import sys
from pathlib import Path
from typing import Tuple

# Agregar directorio al path
sys.path.insert(0, str(Path(__file__).parent))

from pjn import SystemConfig
from pjn.monitor.config import MonitorConfig
from pjn.monitor.core import MonitorPJN
from pjn.monitor.scheduler import SchedulerMonitor
from pjn.system_config import ENV_FIELD_MAP
from pjn.utils.logging import setup_logging, get_logger

# Configurar logging con archivo
setup_logging(level="INFO", log_file="logs/monitor.log")
logger = get_logger(__name__)


def signal_handler(signum, frame):  # type: ignore[override]
    """Maneja señales de interrupcion."""

    logger.info("\nSeñal de interrupcion recibida. Deteniendo monitor...")
    sys.exit(0)


def cargar_configuracion() -> Tuple[MonitorConfig, str]:
    """Obtiene la configuración del monitor y describe la fuente utilizada."""

    sistema_path = Path("config/sistema.json")
    monitor_path = Path("config/monitor.json")
    env_prefix = "SISTEMA_"

    env_overrides = [
        f"{env_prefix}{suffix}" for suffix in ENV_FIELD_MAP.values()
        if os.getenv(f"{env_prefix}{suffix}") is not None
    ]

    if env_overrides:
        logger.info(
            "Cargando configuración unificada desde variables de entorno (prefijo %s)",
            env_prefix,
        )
        system_config = SystemConfig.from_env(prefix=env_prefix)
        return MonitorConfig.from_system_config(system_config), "variables de entorno"

    if sistema_path.exists():
        logger.info("Cargando configuración unificada desde %s", sistema_path)
        system_config = SystemConfig.from_file(sistema_path)
        return MonitorConfig.from_system_config(system_config), str(sistema_path)

    if monitor_path.exists():
        logger.warning(
            "No se encontró %s. Usando configuración legacy %s", sistema_path, monitor_path
        )
        return MonitorConfig.from_file(monitor_path), str(monitor_path)

    logger.warning(
        "No se encontró configuración. Creando %s con valores por defecto.", sistema_path
    )
    system_config = SystemConfig()
    sistema_path.parent.mkdir(parents=True, exist_ok=True)
    system_config.to_file(sistema_path)
    return MonitorConfig.from_system_config(system_config), str(sistema_path)


async def main() -> int:
    """Ejecuta el monitor en modo continuo con scheduler."""

    logger.info("=" * 60)
    logger.info("INICIANDO MONITOR PJN - MODO CONTINUO")
    logger.info("=" * 60)

    config, fuente = cargar_configuracion()

    logger.info("Configuración cargada desde: %s", fuente)
    logger.info("Modo: %s", config.modo)
    logger.info("Verificar entradas: %s", config.verificar_entradas)
    logger.info("Verificar expedientes: %s", config.verificar_expedientes)

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

    return 0


if __name__ == "__main__":
    asyncio.run(main())
