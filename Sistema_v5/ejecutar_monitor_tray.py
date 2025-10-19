#!/usr/bin/env python3
"""Ejecuta el monitor con indicador de bandeja usando configuración unificada.

El script lee overrides desde variables ``SISTEMA_*`` o desde ``config/sistema.json``
y sólo recurre a ``config/monitor.json`` en modo legacy. Muestra un icono en la bandeja
para controlar el monitor.
"""

import asyncio
import os
import signal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pjn import SystemConfig
from pjn.monitor.config import MonitorConfig
from pjn.monitor.core import MonitorPJN
from pjn.monitor.scheduler import SchedulerMonitor
from pjn.monitor.tray import MonitorSystemTray, TRAY_AVAILABLE
from pjn.system_config import ENV_FIELD_MAP
from pjn.utils.logging import setup_logging, get_logger

setup_logging(level="INFO")
logger = get_logger(__name__)


def cargar_configuracion() -> tuple[MonitorConfig, str]:
    """Obtiene la configuración del monitor y la fuente utilizada."""

    sistema_path = Path("config/sistema.json")
    monitor_path = Path("config/monitor.json")
    env_prefix = "SISTEMA_"

    env_overrides = [
        f"{env_prefix}{suffix}" for suffix in ENV_FIELD_MAP.values()
        if os.getenv(f"{env_prefix}{suffix}") is not None
    ]

    if env_overrides:
        logger.info(
            "[OK] Configuración unificada desde variables de entorno (prefijo %s)",
            env_prefix,
        )
        system_config = SystemConfig.from_env(prefix=env_prefix)
        return MonitorConfig.from_system_config(system_config), "variables de entorno"

    if sistema_path.exists():
        logger.info("[OK] Configuración unificada desde %s", sistema_path)
        system_config = SystemConfig.from_file(sistema_path)
        return MonitorConfig.from_system_config(system_config), str(sistema_path)

    if monitor_path.exists():
        logger.warning(
            "[ADVERTENCIA] No se encontró %s. Usando configuración legacy %s",
            sistema_path,
            monitor_path,
        )
        return MonitorConfig.from_file(monitor_path), str(monitor_path)

    logger.warning(
        "[ADVERTENCIA] No existe configuración. Creando %s con valores por defecto.",
        sistema_path,
    )
    system_config = SystemConfig()
    sistema_path.parent.mkdir(parents=True, exist_ok=True)
    system_config.to_file(sistema_path)
    return MonitorConfig.from_system_config(system_config), str(sistema_path)


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
    config, fuente = cargar_configuracion()

    # Mostrar configuración
    logger.info(f"  Fuente: {fuente}")
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
        # IMPORTANTE: Iniciar el tray PRIMERO para que el icono sea visible inmediatamente
        logger.info("\n* Iniciando icono en bandeja del sistema...")
        tray.run_detached(loop)
        logger.info("* Icono iniciado - búscalo en la bandeja del sistema (esquina inferior derecha)")
        logger.info("  Si no lo ves, haz click en la flecha ^ para expandir iconos ocultos\n")

        # Ejecutar verificación inicial
        logger.info(">>> Ejecutando verificación inicial...")

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
        logger.info("\n* El icono en la bandeja del sistema tiene estas opciones:")
        logger.info("   Click derecho para ver:\n")
        logger.info("   - Verificar ahora - Ejecuta verificación inmediata")
        logger.info("   - Estado - Ver estado del monitor")
        logger.info("   - Abrir carpeta de datos - Ver archivos guardados")
        logger.info("   - Salir - Detener monitor\n")
        logger.info("=" * 60)

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
