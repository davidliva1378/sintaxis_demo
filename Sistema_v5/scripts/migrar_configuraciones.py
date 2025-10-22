"""Script para migrar configuraciones antiguas a SystemConfig.

Este script:
1. Lee config/monitor.json existente
2. Crea un SystemConfig con los valores migrados
3. Hace backup de la configuración anterior
4. Guarda la nueva configuración en config/sistema.json
"""

import sys
from pathlib import Path

from Sistema_v5.configuracion.core import SystemConfig


def migrar_configuracion(monitor_path: str = "config/monitor.json", output_path: str = "config/sistema.json"):
    """Migra configuración de monitor.json a sistema.json.

    Args:
        monitor_path: Ruta al archivo monitor.json existente
        output_path: Ruta donde guardar sistema.json
    """
    print("=" * 70)
    print("MIGRACIÓN DE CONFIGURACIÓN")
    print("=" * 70)
    print()

    monitor_file = Path(monitor_path)
    output_file = Path(output_path)

    # Verificar si monitor.json existe
    if not monitor_file.exists():
        print(f"❌ Archivo {monitor_path} no existe.")
        print("   Creando configuración por defecto...")
        config = SystemConfig()
    else:
        print(f"✅ Encontrado: {monitor_path}")
        print(f"   Migrando configuración...")

        # Migrar desde monitor.json
        config = SystemConfig.from_monitor_config(monitor_file)

        # Hacer backup de monitor.json
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)

        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"monitor_{timestamp}.json"

        import shutil
        shutil.copy2(monitor_file, backup_path)
        print(f"✅ Backup creado: {backup_path}")

    # Crear directorios definidos en la configuración
    print()
    print("Creando estructura de directorios...")
    config.crear_directorios()
    print("✅ Directorios creados")

    # Guardar nueva configuración
    print()
    print(f"Guardando nueva configuración en {output_path}...")
    config.to_file(output_file)
    print(f"✅ Configuración guardada: {output_path}")

    # Mostrar resumen
    print()
    print("=" * 70)
    print("RESUMEN DE LA CONFIGURACIÓN")
    print("=" * 70)
    print()
    print(f"📁 Directorios:")
    print(f"   - Extracción inicial:  {config.directorio_extraccion_inicial}")
    print(f"   - Expedientes:         {config.directorio_expedientes_base}")
    print(f"   - Comparaciones:       {config.directorio_comparaciones}")
    print(f"   - Reportes:            {config.directorio_reportes}")
    print(f"   - Logs:                {config.directorio_logs}")
    print(f"   - Cache:               {config.directorio_cache}")
    print(f"   - Descargas:           {config.directorio_descargas}")
    print(f"   - Monitor (datos):     {config.directorio_monitor_datos}")
    print()
    print(f"🔍 Monitoreo:")
    print(f"   - Modo:                {config.modo_monitor}")
    print(f"   - Horario laboral:     {config.hora_inicio} - {config.hora_fin}")
    print(f"   - Días laborales:      {', '.join(config.dias_laborales)}")
    print(f"   - Verificar entradas:  {config.verificar_entradas}")
    print(f"   - Verificar expedientes: {config.verificar_expedientes}")
    print()
    print(f"⚙️  Sistema:")
    print(f"   - Nivel de log:        {config.nivel_log}")
    print(f"   - Modo headless:       {config.headless}")
    print(f"   - Fecha inicio:        {config.fecha_inicio_sistema}")
    print()
    print("=" * 70)
    print("✅ MIGRACIÓN COMPLETADA")
    print("=" * 70)
    print()
    print(f"Para editar la configuración, use:")
    print(f"  python -m Sistema_v5.cli.configuracion wizard")
    print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrar configuración de monitor.json a sistema.json"
    )
    parser.add_argument(
        "--input",
        "-i",
        default="config/monitor.json",
        help="Ruta al archivo monitor.json (default: config/monitor.json)"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="config/sistema.json",
        help="Ruta de salida para sistema.json (default: config/sistema.json)"
    )

    args = parser.parse_args()

    try:
        migrar_configuracion(args.input, args.output)
    except Exception as e:
        print(f"\n❌ Error durante la migración: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
