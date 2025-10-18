"""Script launcher para el configurador del sistema PJN.

Este script abre la interfaz gráfica de configuración del sistema.

Uso:
    python scripts/configurar_sistema.py
    python scripts/configurar_sistema.py --config config/mi_config.json
"""

import sys
from pathlib import Path

# Agregar el directorio padre al path para importar pjn
sys.path.insert(0, str(Path(__file__).parent.parent))

from pjn.gui.config_form import ConfigForm


def main():
    """Función principal."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Configurador del Sistema PJN"
    )
    parser.add_argument(
        "--config",
        "-c",
        default="config/sistema.json",
        help="Ruta al archivo de configuración (default: config/sistema.json)"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("CONFIGURADOR DEL SISTEMA PJN")
    print("=" * 70)
    print()
    print(f"Archivo de configuración: {args.config}")
    print()
    print("Abriendo interfaz gráfica...")
    print()

    # Crear y ejecutar la aplicación
    try:
        app = ConfigForm(config_path=args.config)
        app.mainloop()
    except Exception as e:
        print(f"\n❌ Error al iniciar el configurador: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
