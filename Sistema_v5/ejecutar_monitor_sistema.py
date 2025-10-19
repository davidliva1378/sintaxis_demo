"""Ejecutar el monitor usando la configuración unificada (`config/sistema.json`).

El script soporta overrides mediante variables ``SISTEMA_*`` (personalizables con
``--env-prefix``) antes de leer el archivo indicado. Genera el archivo con valores
por defecto si no existe.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Agregar al path si es necesario
sys.path.insert(0, str(Path(__file__).parent))

from pjn import SystemConfig
from pjn.monitor import MonitorConfig, MonitorPJN, SchedulerMonitor
from pjn.system_config import ENV_FIELD_MAP


async def main():
    """Función principal."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Monitor PJN usando SystemConfig/MonitorConfig unificados"
    )
    parser.add_argument(
        "--config",
        "-c",
        default="config/sistema.json",
        help="Ruta al archivo sistema.json (default: config/sistema.json)",
    )
    parser.add_argument(
        "--verificar-ahora",
        "-v",
        action="store_true",
        help="Ejecutar verificación inmediata y salir"
    )
    parser.add_argument(
        "--env-prefix",
        default="SISTEMA_",
        help="Prefijo para variables de entorno que sobreescriben la configuración",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("MONITOR PJN - CONFIGURACIÓN UNIFICADA")
    print("=" * 70)
    print()

    env_overrides = [
        f"{args.env_prefix}{suffix}" for suffix in ENV_FIELD_MAP.values()
        if os.getenv(f"{args.env_prefix}{suffix}") is not None
    ]

    # Cargar configuración unificada
    if env_overrides:
        print(f"🌱 Usando variables de entorno con prefijo {args.env_prefix}")
        system_config = SystemConfig.from_env(prefix=args.env_prefix)
        fuente = f"variables de entorno ({args.env_prefix}*)"
    else:
        try:
            print(f"📁 Cargando configuración desde: {args.config}")
            system_config = SystemConfig.from_file(args.config)
            print("✅ Configuración cargada")
            fuente = args.config
            print()
        except FileNotFoundError:
            print(f"❌ Archivo no encontrado: {args.config}")
            print()
            print("Creando configuración por defecto...")
            system_config = SystemConfig()
            system_config.to_file(args.config)
            print(f"✅ Configuración por defecto creada en: {args.config}")
            print()
            print("Por favor edita la configuración y vuelve a ejecutar.")
            print(
                "  python -m Sistema_v5.cli.configuracion wizard "
                f"--config {args.config}"
            )
            return

    monitor_config = MonitorConfig.from_system_config(system_config)

    # Mostrar configuración
    print("⚙️  Configuración del Monitor:")
    print(f"   - Fuente:              {fuente}")
    print(f"   - Modo:                {monitor_config.modo}")
    print(f"   - Headless:            {monitor_config.headless}")
    print(f"   - Verificar entradas:  {monitor_config.verificar_entradas}")
    print(f"   - Verificar expedientes: {monitor_config.verificar_expedientes}")
    print(f"   - Horario laboral:     {monitor_config.hora_inicio} - {monitor_config.hora_fin}")
    print(f"   - Días laborales:      {', '.join(monitor_config.dias_laborales)}")
    print(f"   - Directorio datos:    {monitor_config.directorio_datos}")
    print()

    # Crear monitor
    print("🔧 Inicializando monitor...")
    monitor = MonitorPJN(monitor_config)
    print("✅ Monitor inicializado")
    print()

    if args.verificar_ahora:
        # Modo de verificación inmediata
        print("🔍 Ejecutando verificación inmediata...")
        print()

        try:
            if monitor_config.verificar_entradas:
                print("📧 Verificando entradas...")
                nuevas_entradas = await monitor.verificar_entradas()
                print(f"   ✅ {len(nuevas_entradas)} nuevas entradas detectadas")
                print()

            if monitor_config.verificar_expedientes:
                print("📊 Verificando expedientes...")
                expedientes_cambios = await monitor.verificar_expedientes()
                print(f"   ✅ {len(expedientes_cambios)} expedientes con cambios")
                print()

            print("✅ Verificación completada")

        except Exception as e:
            print(f"❌ Error durante verificación: {e}")
            import traceback
            traceback.print_exc()

    else:
        # Modo continuo con scheduler
        print("⏰ Iniciando modo continuo con scheduler...")
        print()
        print("El monitor verificará automáticamente según los intervalos configurados:")
        print(f"   - Intervalo laboral (expedientes):     {monitor_config.intervalos_laboral_expedientes} min")
        print(f"   - Intervalo laboral (entradas):        {monitor_config.intervalos_laboral_entradas} min")
        print(f"   - Intervalo no laboral (expedientes):  {monitor_config.intervalos_no_laboral_expedientes} min")
        print(f"   - Intervalo no laboral (entradas):     {monitor_config.intervalos_no_laboral_entradas} min")
        print()
        print("Presiona Ctrl+C para detener el monitor")
        print()

        # Crear scheduler
        scheduler = SchedulerMonitor(monitor)

        try:
            # Ejecutar scheduler
            await scheduler.ejecutar()
        except KeyboardInterrupt:
            print()
            print("⏹️  Deteniendo monitor...")
            monitor.detener()
            print("✅ Monitor detenido")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
