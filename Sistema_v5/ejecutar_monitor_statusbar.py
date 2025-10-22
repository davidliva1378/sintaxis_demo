"""Monitor PJN con barra de menú para macOS usando configuración unificada.

El script prioriza overrides en variables ``SISTEMA_*`` y luego lee
``config/sistema.json``. Sólo si no existen recursos utiliza el legacy
``config/monitor.json``.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Tuple

from Sistema_v5.pjn import SystemConfig
from Sistema_v5.pjn.monitor.config import MonitorConfig
from Sistema_v5.pjn.monitor.core import MonitorPJN
from Sistema_v5.pjn.monitor.scheduler import SchedulerMonitor
from Sistema_v5.pjn.monitor.tray_macos import RUMPS_AVAILABLE, MonitorStatusBar
from Sistema_v5.pjn.system_config import ENV_FIELD_MAP
from Sistema_v5.pjn.utils.logging import get_logger, setup_logging

setup_logging(level="INFO")
logger = get_logger(__name__)


async def verificacion_inicial(monitor: MonitorPJN, statusbar: MonitorStatusBar) -> None:
    """Ejecuta verificación inicial del monitor."""

    logger.info("🚀 Ejecutando verificación inicial...")

    try:
        if monitor.config.verificar_entradas:
            nuevas = await monitor.verificar_entradas()
            if nuevas:
                logger.info(f"✅ {len(nuevas)} nuevas entradas detectadas")
                statusbar.update_icon("yellow")
                await asyncio.sleep(2)
                statusbar.update_icon("green")
            else:
                logger.info("✅ Sin nuevas entradas")

        if monitor.config.verificar_expedientes:
            cambios = await monitor.verificar_expedientes()
            if cambios:
                logger.info(f"✅ {len(cambios)} expedientes con cambios")
                statusbar.update_icon("yellow")
                await asyncio.sleep(2)
                statusbar.update_icon("green")
            else:
                logger.info("✅ Sin cambios en expedientes")

    except Exception as e:  # pragma: no cover - logging para debug
        logger.error(f"❌ Error en verificación inicial: {e}", exc_info=True)
        statusbar.update_icon("red")
        await asyncio.sleep(2)
        statusbar.update_icon("green")


def _resolver_ruta_config(nombre: str) -> tuple[Path, bool]:
    """Busca ``config/<nombre>`` en ubicaciones conocidas."""

    relativo = Path("config") / nombre
    archivo_actual = Path(__file__).resolve()

    posibles_bases: list[Path] = []

    for base in (Path.cwd(), archivo_actual.parent):
        if base not in posibles_bases:
            posibles_bases.append(base)

    for indice in range(1, 3):
        if len(archivo_actual.parents) > indice:
            candidato = archivo_actual.parents[indice]
            if candidato not in posibles_bases:
                posibles_bases.append(candidato)

    for base in posibles_bases:
        candidato = base / relativo
        if candidato.exists():
            return candidato, True

    destino_base = (
        archivo_actual.parents[1]
        if len(archivo_actual.parents) > 1
        else archivo_actual.parent
    )
    return destino_base / relativo, False


def cargar_configuracion() -> Tuple[MonitorConfig, str]:
    """Obtiene la configuración del monitor y su origen."""

    sistema_path, existe_sistema = _resolver_ruta_config("sistema.json")
    monitor_path, existe_monitor = _resolver_ruta_config("monitor.json")
    env_prefix = "SISTEMA_"

    env_overrides = [
        f"{env_prefix}{suffix}" for suffix in ENV_FIELD_MAP.values()
        if os.getenv(f"{env_prefix}{suffix}") is not None
    ]

    if env_overrides:
        logger.info(
            "✅ Configuración unificada desde variables de entorno (prefijo %s)",
            env_prefix,
        )
        system_config = SystemConfig.from_env(prefix=env_prefix)
        return MonitorConfig.from_system_config(system_config), "variables de entorno"

    if existe_sistema:
        logger.info("✅ Configuración unificada desde %s", sistema_path)
        system_config = SystemConfig.from_file(sistema_path)
        return MonitorConfig.from_system_config(system_config), str(sistema_path)

    if existe_monitor:
        logger.warning(
            "⚠️  No se encontró %s. Usando configuración legacy %s", sistema_path, monitor_path
        )
        return MonitorConfig.from_file(monitor_path), str(monitor_path)

    logger.warning(
        "⚠️  No existe configuración. Creando %s con valores por defecto.", sistema_path
    )
    system_config = SystemConfig()
    sistema_path.parent.mkdir(parents=True, exist_ok=True)
    system_config.to_file(sistema_path)
    return MonitorConfig.from_system_config(system_config), str(sistema_path)


def main() -> int:
    """Función principal."""

    # Verificar que rumps esté disponible
    if not RUMPS_AVAILABLE:
        logger.error(
            "❌ rumps es requerido para la barra de menú en macOS.\n"
            "   Instalar con: pip install rumps\n"
            "   O usar: python scripts/monitor_cli.py"
        )
        return 1

    logger.info("=" * 60)
    logger.info("MONITOR PJN - STATUS BAR (macOS)")
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

    # Crear status bar
    statusbar = MonitorStatusBar(monitor, scheduler)

    # Ejecutar verificación inicial y scheduler en background
    import threading

    def run_async_loop() -> None:
        """Ejecuta el event loop asyncio en un thread separado."""

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def startup() -> None:
            """Inicializa el monitor y scheduler."""

            # Ejecutar verificación inicial
            await verificacion_inicial(monitor, statusbar)

            # Iniciar scheduler (debe hacerse con el loop corriendo)
            logger.info("\n⏰ Iniciando scheduler...")
            scheduler.iniciar()
            logger.info("✅ Scheduler iniciado\n")

        # Programar startup
        loop.create_task(startup())

        # Mantener el loop corriendo para que el scheduler funcione
        try:
            loop.run_forever()
        except KeyboardInterrupt:  # pragma: no cover - interrupción manual
            pass
        finally:
            loop.close()

    # Iniciar loop asyncio en thread separado
    async_thread = threading.Thread(target=run_async_loop, daemon=True)
    async_thread.start()

    # Esperar un momento para que se inicialice
    import time

    time.sleep(2)

    # Ejecutar status bar (bloqueante - este es el main loop)
    try:
        statusbar.run()
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupción por teclado")
        statusbar.stop()
        return 0
    except Exception as e:  # pragma: no cover - logging para debug
        logger.error(f"\n❌ Error fatal: {e}", exc_info=True)
        statusbar.stop()
        return 1

    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:  # pragma: no cover - logging para debug
        logger.error(f"❌ Error fatal: {e}", exc_info=True)
        sys.exit(1)
