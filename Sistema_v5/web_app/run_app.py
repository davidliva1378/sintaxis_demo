#!/usr/bin/env python3
r"""
Script para ejecutar la aplicación web del Monitor PJN.

Este script configura automáticamente el puerto 8080 para evitar conflictos
con AirPlay Receiver en macOS (que usa el puerto 5000 por defecto).

Uso:
    # Linux/macOS
    python3 Sistema_v5/web_app/run_app.py

    # Windows
    python Sistema_v5\web_app\run_app.py

Variables de entorno personalizables:
    FLASK_PORT      - Puerto del servidor (default: 8080)
    FLASK_HOST      - Host del servidor (default: 127.0.0.1)
    FLASK_DEBUG     - Modo debug true/false (default: true)

Ejemplos:
    # Cambiar puerto
    FLASK_PORT=9000 python3 Sistema_v5/web_app/run_app.py

    # Modo producción
    FLASK_DEBUG=false python3 Sistema_v5/web_app/run_app.py

    # Accesible desde red local
    FLASK_HOST=0.0.0.0 python3 Sistema_v5/web_app/run_app.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Configurar variables de entorno con valores por defecto
os.environ.setdefault('FLASK_PORT', '8080')
os.environ.setdefault('FLASK_HOST', '127.0.0.1')
os.environ.setdefault('FLASK_DEBUG', 'true')

# Agregar directorio base al path de Python
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

def main():
    """Función principal que ejecuta la aplicación Flask."""
    # Obtener configuración de variables de entorno
    port = os.environ['FLASK_PORT']
    host = os.environ['FLASK_HOST']
    debug = os.environ['FLASK_DEBUG']

    # Mostrar información de inicio
    print("=" * 70)
    print("🚀 Aplicación Web del Monitor PJN")
    print("=" * 70)
    print()
    print(f"📍 Directorio base: {BASE_DIR}")
    print(f"🌐 Servidor: http://{host}:{port}")
    print(f"🔧 Modo debug: {debug}")
    print(f"💻 Plataforma: {sys.platform}")
    print()
    print("📋 Rutas principales:")
    print(f"   • Dashboard:     http://{host}:{port}/dashboard")
    print(f"   • Entradas:      http://{host}:{port}/entradas")
    print(f"   • Expedientes:   http://{host}:{port}/expedientes")
    print(f"   • Configuración: http://{host}:{port}/config")
    print()
    print("⌨️  Presiona Ctrl+C para detener el servidor")
    print("=" * 70)
    print()

    # Importar y ejecutar la aplicación Flask
    try:
        from web_app.app import app
    except ImportError as e:
        print(f"❌ Error al importar la aplicación: {e}")
        print()
        print("Solución:")
        print(f"   1. Asegúrate de ejecutar desde: {BASE_DIR.parent}")
        print(f"   2. Verifica que existe: {BASE_DIR / 'web_app' / 'app.py'}")
        sys.exit(1)

    # Convertir y validar parámetros
    try:
        port_int = int(port)
        if not (1 <= port_int <= 65535):
            raise ValueError(f"Puerto {port_int} fuera de rango (1-65535)")
    except ValueError as e:
        print(f"❌ Error en FLASK_PORT: {e}")
        sys.exit(1)

    debug_bool = debug.lower() in ('true', '1', 'yes', 'on')

    # Ejecutar servidor Flask
    try:
        app.run(debug=debug_bool, host=host, port=port_int)
    except OSError as e:
        if "Address already in use" in str(e):
            print()
            print(f"❌ Error: El puerto {port_int} ya está en uso")
            print()
            print("Soluciones:")
            print(f"   1. Usa otro puerto: FLASK_PORT=9000 python {__file__}")
            print(f"   2. Detén el proceso que usa el puerto {port_int}")
            if sys.platform == "darwin" and port_int == 5000:
                print("   3. En macOS: Desactiva AirPlay Receiver en Ajustes del Sistema")
        else:
            print(f"❌ Error al iniciar servidor: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print()
        print("👋 Servidor detenido por el usuario")
        sys.exit(0)

if __name__ == '__main__':
    main()