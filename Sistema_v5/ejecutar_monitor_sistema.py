"""Ejecutar monitor usando SystemConfig (configuración unificada).

Este script es la forma recomendada de ejecutar el monitor,
usando la configuración unificada del sistema.

Uso:
    python ejecutar_monitor_sistema.py
    python ejecutar_monitor_sistema.py --config config/sistema.json
"""

import asyncio
import sys
from pathlib import Path

# Agregar al path si es necesario
sys.path.insert(0, str(Path(__file__).parent))

from pjn import SystemConfig
from pjn.monitor import MonitorPJN, SchedulerMonitor


async def main():
    """Función principal."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Monitor PJN usando SystemConfig"
    )
    parser.add_argument(
        "--config",
        "-c",
        default="config/sistema.json",
        help="Ruta al archivo sistema.json (default: config/sistema.json)"
    )
    parser.add_argument(
        "--verificar-ahora",
        "-v",
        action="store_true",
        help="Ejecutar verificación inmediata y salir"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("MONITOR PJN - USANDO SYSTEMCONFIG")
    print("=" * 70)
    print()

    # Cargar configuración unificada
    try:
        print(f"📁 Cargando configuración desde: {args.config}")
        config = SystemConfig.from_file(args.config)
        print(f"✅ Configuración cargada")
        print()
    except FileNotFoundError:
        print(f"❌ Archivo no encontrado: {args.config}")
        print()
        print("Creando configuración por defecto...")
        config = SystemConfig()
        config.to_file(args.config)
        print(f"✅ Configuración por defecto creada en: {args.config}")
        print()
        print("Por favor edita la configuración y vuelve a ejecutar.")
        print(f"  python scripts/configurar_sistema.py --config {args.config}")
        return

    # Mostrar configuración
    print("⚙️  Configuración del Monitor:")
    print(f"   - Modo:                {config.modo_monitor}")
    print(f"   - Headless:            {config.headless}")
    print(f"   - Verificar entradas:  {config.verificar_entradas}")
    print(f"   - Verificar expedientes: {config.verificar_expedientes}")
    print(f"   - Horario laboral:     {config.hora_inicio} - {config.hora_fin}")
    print(f"   - Días laborales:      {', '.join(config.dias_laborales)}")
    print(f"   - Directorio datos:    {config.directorio_monitor_datos}")
    print()

    # Crear monitor
    print("🔧 Inicializando monitor...")
    monitor = MonitorPJN(config)
    print("✅ Monitor inicializado")
    print()

    if args.verificar_ahora:
        # Modo de verificación inmediata
        print("🔍 Ejecutando verificación inmediata...")
        print()

        try:
            if config.verificar_entradas:
                print("📧 Verificando entradas...")
                nuevas_entradas = await monitor.verificar_entradas()
                print(f"   ✅ {len(nuevas_entradas)} nuevas entradas detectadas")
                print()

            if config.verificar_expedientes:
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
        print(f"   - Intervalo laboral (expedientes):     {config.intervalos_laboral_expedientes} min")
        print(f"   - Intervalo laboral (entradas):        {config.intervalos_laboral_entradas} min")
        print(f"   - Intervalo no laboral (expedientes):  {config.intervalos_no_laboral_expedientes} min")
        print(f"   - Intervalo no laboral (entradas):     {config.intervalos_no_laboral_entradas} min")
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
