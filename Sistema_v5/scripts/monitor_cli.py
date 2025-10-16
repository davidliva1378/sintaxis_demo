#!/usr/bin/env python3
"""Monitor CLI para verificaciones periódicas de PJN.

Este script ejecuta el monitor en modo CLI (sin interfaz gráfica),
ideal para ejecutar en segundo plano o en servidores.

Uso:
    python scripts/monitor_cli.py [opciones]

Opciones:
    --config PATH       Ruta al archivo de configuración (default: config/monitor.json)
    --verificar-ahora   Ejecuta una verificación inmediata y sale
    --modo MODE         Sobrescribe el modo (automatico/laboral/no_laboral)
    --headless          Ejecuta browser en modo headless (default)
    --no-headless       Ejecuta browser con interfaz visible
    --verbose           Log detallado (DEBUG level)
    --quiet             Solo errores (ERROR level)
"""

from __future__ import annotations

import argparse
import asyncio
import signal
import sys
from pathlib import Path

# Agregar directorio raíz al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pjn.monitor.config import MonitorConfig
from pjn.monitor.core import MonitorPJN
from pjn.monitor.scheduler import SchedulerMonitor
from pjn.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)


def parsear_argumentos() -> argparse.Namespace:
    """Parsea argumentos de línea de comandos.

    Returns:
        argparse.Namespace: Argumentos parseados
    """
    parser = argparse.ArgumentParser(
        description="Monitor CLI para verificaciones periódicas de PJN",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Ejecutar con configuración por defecto
  python scripts/monitor_cli.py

  # Ejecutar verificación inmediata
  python scripts/monitor_cli.py --verificar-ahora

  # Ejecutar en modo laboral con logs detallados
  python scripts/monitor_cli.py --modo laboral --verbose

  # Ejecutar con configuración personalizada
  python scripts/monitor_cli.py --config mi_config.json
        """
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config/monitor.json",
        help="Ruta al archivo de configuración (default: config/monitor.json)"
    )

    parser.add_argument(
        "--verificar-ahora",
        action="store_true",
        help="Ejecuta una verificación inmediata y sale (no inicia scheduler)"
    )

    parser.add_argument(
        "--modo",
        type=str,
        choices=["automatico", "laboral", "no_laboral"],
        help="Sobrescribe el modo de configuración"
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="Ejecuta browser en modo headless (default)"
    )

    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Ejecuta browser con interfaz visible"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Log detallado (DEBUG level)"
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Solo errores (ERROR level)"
    )

    return parser.parse_args()


async def verificar_inmediato(monitor: MonitorPJN) -> int:
    """Ejecuta una verificación inmediata de entradas y expedientes.

    Args:
        monitor: Instancia del monitor

    Returns:
        int: Código de salida (0=éxito, 1=error)
    """
    logger.info("=" * 60)
    logger.info("VERIFICACIÓN INMEDIATA")
    logger.info("=" * 60)

    try:
        # Verificar entradas
        logger.info("\n📥 Verificando entradas...")
        nuevas_entradas = await monitor.verificar_entradas()

        if nuevas_entradas:
            logger.info(f"✅ {len(nuevas_entradas)} nuevas entradas detectadas:")
            for entrada in nuevas_entradas[:5]:  # Mostrar hasta 5
                logger.info(f"  - {entrada.numero}: {entrada.evento}")
            if len(nuevas_entradas) > 5:
                logger.info(f"  ... y {len(nuevas_entradas) - 5} más")
        else:
            logger.info("✅ Sin nuevas entradas")

        # Verificar expedientes
        logger.info("\n📊 Verificando expedientes...")
        cambios_expedientes = await monitor.verificar_expedientes()

        if cambios_expedientes:
            logger.info(f"✅ {len(cambios_expedientes)} expedientes con cambios:")
            for exp in cambios_expedientes[:5]:  # Mostrar hasta 5
                logger.info(f"  - {exp.numero}: {exp.ultima_actuacion}")
            if len(cambios_expedientes) > 5:
                logger.info(f"  ... y {len(cambios_expedientes) - 5} más")
        else:
            logger.info("✅ Sin cambios en expedientes")

        logger.info("\n" + "=" * 60)
        logger.info("VERIFICACIÓN COMPLETADA EXITOSAMENTE")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"\n❌ Error durante verificación: {e}", exc_info=True)
        logger.info("\n" + "=" * 60)
        logger.info("VERIFICACIÓN FALLÓ")
        logger.info("=" * 60)
        return 1


async def ejecutar_monitor_continuo(monitor: MonitorPJN, config: MonitorConfig) -> int:
    """Ejecuta el monitor en modo continuo con scheduler.

    Args:
        monitor: Instancia del monitor
        config: Configuración del monitor

    Returns:
        int: Código de salida
    """
    logger.info("=" * 60)
    logger.info("MONITOR PJN - MODO CONTINUO")
    logger.info("=" * 60)
    logger.info(f"Modo: {config.modo}")
    logger.info(f"Directorio de datos: {config.directorio_datos}")
    logger.info(f"Notificaciones entradas: {'✅' if config.notificar_nuevas_entradas else '❌'}")
    logger.info(f"Notificaciones expedientes: {'✅' if config.notificar_cambios_expedientes else '❌'}")
    logger.info(f"Headless: {'✅' if config.headless else '❌'}")

    if config.modo == "automatico":
        logger.info(f"\nIntervalos laborales:")
        logger.info(f"  - Entradas: {config.intervalos_laboral_entradas} min")
        logger.info(f"  - Expedientes: {config.intervalos_laboral_expedientes} min")
        logger.info(f"\nIntervalos no laborales:")
        logger.info(f"  - Entradas: {config.intervalos_no_laboral_entradas} min")
        logger.info(f"  - Expedientes: {config.intervalos_no_laboral_expedientes} min")
    elif config.modo == "laboral":
        logger.info(f"\nIntervalos:")
        logger.info(f"  - Entradas: {config.intervalos_laboral_entradas} min")
        logger.info(f"  - Expedientes: {config.intervalos_laboral_expedientes} min")
    else:
        logger.info(f"\nIntervalos:")
        logger.info(f"  - Entradas: {config.intervalos_no_laboral_entradas} min")
        logger.info(f"  - Expedientes: {config.intervalos_no_laboral_expedientes} min")

    logger.info("=" * 60)

    # Crear scheduler
    scheduler = SchedulerMonitor(monitor)

    # Configurar señales para detener gracefully
    loop = asyncio.get_event_loop()

    def signal_handler(signum, frame):
        logger.info(f"\n⚠️  Señal {signum} recibida, deteniendo monitor...")
        scheduler.detener()
        monitor.detener()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Ejecutar verificación inicial
        logger.info("\n🚀 Ejecutando verificación inicial...")
        await scheduler.ejecutar_verificacion_inmediata()

        # Iniciar scheduler
        logger.info("\n⏰ Iniciando scheduler...")
        scheduler.iniciar()

        logger.info("\n✅ Monitor activo. Presiona Ctrl+C para detener.\n")

        # Mantener el programa corriendo
        while monitor.running:
            await asyncio.sleep(1)

        return 0

    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupción por teclado, deteniendo...")
        scheduler.detener()
        monitor.detener()
        return 0

    except Exception as e:
        logger.error(f"\n❌ Error fatal en monitor: {e}", exc_info=True)
        scheduler.detener()
        monitor.detener()
        return 1


async def main() -> int:
    """Función principal del CLI.

    Returns:
        int: Código de salida
    """
    args = parsear_argumentos()

    # Configurar logging
    if args.verbose:
        nivel = "DEBUG"
    elif args.quiet:
        nivel = "ERROR"
    else:
        nivel = "INFO"

    setup_logging(level=nivel)

    # Cargar configuración
    try:
        config = MonitorConfig.from_file(args.config)
        logger.info(f"📁 Configuración cargada desde {args.config}")
    except FileNotFoundError:
        logger.warning(f"⚠️  Archivo de configuración no encontrado: {args.config}")
        logger.info("📝 Creando configuración por defecto...")
        config = MonitorConfig()
        config.to_file(args.config)
        logger.info(f"✅ Configuración por defecto guardada en {args.config}")
    except Exception as e:
        logger.error(f"❌ Error al cargar configuración: {e}")
        return 1

    # Aplicar overrides de argumentos
    if args.modo:
        config.modo = args.modo  # type: ignore
        logger.info(f"🔄 Modo sobrescrito: {args.modo}")

    if args.no_headless:
        config.headless = False
        logger.info("🔄 Headless desactivado")

    # Crear monitor
    monitor = MonitorPJN(config)
    monitor.running = True

    # Ejecutar según modo
    if args.verificar_ahora:
        return await verificar_inmediato(monitor)
    else:
        return await ejecutar_monitor_continuo(monitor, config)


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}", exc_info=True)
        sys.exit(1)
