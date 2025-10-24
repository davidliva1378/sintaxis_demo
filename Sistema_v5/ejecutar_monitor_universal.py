#!/usr/bin/env python3
"""Script universal para ejecutar el monitor con system tray.

Este script detecta automáticamente el sistema operativo y usa
la implementación más adecuada:
- macOS: rumps (nativo de macOS)
- Windows/Linux: pystray (multiplataforma)

Uso:
    python -m Sistema_v5.ejecutar_monitor_universal
"""

import sys
import platform


def main():
    """Detecta el sistema operativo y ejecuta el script apropiado."""
    os_name = platform.system()

    print("=" * 60)
    print("MONITOR PJN - LAUNCHER UNIVERSAL")
    print("=" * 60)
    print(f"Sistema operativo: {os_name}")
    print("")

    if os_name == "Darwin":  # macOS
        print("[OK] Usando implementación nativa de macOS (rumps)")
        print("   Script: ejecutar_monitor_statusbar.py")
        print("")
        print("Requisitos:")
        print("  pip install rumps")
        print("")

        try:
            import rumps
        except ImportError:
            print("[ERROR] rumps no está instalado")
            print("   Ejecuta: pip install rumps")
            return 1

        # Importar y ejecutar la versión de macOS
        from Sistema_v5 import ejecutar_monitor_statusbar

        return ejecutar_monitor_statusbar.main()

    elif os_name in ("Windows", "Linux"):
        print(f"[OK] Usando implementación multiplataforma (pystray)")
        print("   Script: ejecutar_monitor_tray.py")
        print("")
        print("Requisitos:")
        print("  pip install pystray pillow")
        print("")

        try:
            import pystray
            from PIL import Image
        except ImportError:
            print("[ERROR] pystray o pillow no están instalados")
            print("   Ejecuta: pip install pystray pillow")
            return 1

        # Importar y ejecutar la versión multiplataforma
        from Sistema_v5 import ejecutar_monitor_tray

        # Necesitamos hacer asyncio.run del main
        import asyncio
        return asyncio.run(ejecutar_monitor_tray.main())

    else:
        print(f"[ERROR] Sistema operativo no soportado: {os_name}")
        print("   Soportados: Windows, macOS, Linux")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n[ADVERTENCIA] Cancelado por usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
