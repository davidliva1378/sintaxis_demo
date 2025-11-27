#!/usr/bin/env python3
"""
sintaXis Launcher - Inicia el sistema completo con splash screen animado.

Este launcher:
1. Muestra la animacion splash de bienvenida
2. Inicia el backend (uvicorn) en background mientras se muestra el splash
3. Inicia el frontend (npm run dev) en background
4. Al finalizar el splash, abre el navegador en la aplicacion

Uso:
    python launcher.py [--no-splash] [--no-browser] [--backend-only] [--frontend-only]

Opciones:
    --no-splash     Omitir animacion de splash
    --no-browser    No abrir navegador automaticamente
    --backend-only  Solo iniciar backend
    --frontend-only Solo iniciar frontend
    --port PORT     Puerto del backend (default: 8000)
    --frontend-port Puerto del frontend (default: 5173)
"""

import sys
import os
import subprocess
import webbrowser
import time
import signal
import argparse
import socket
from pathlib import Path
from typing import Optional, List

# Directorio base del proyecto
BASE_DIR = Path(__file__).parent.absolute()
FRONTEND_DIR = BASE_DIR / "frontend"

# Configuracion por defecto
DEFAULT_BACKEND_PORT = 8000
DEFAULT_FRONTEND_PORT = 5173
FRONTEND_URL = "http://localhost:{port}"
BACKEND_HEALTH_URL = "http://localhost:{port}/api/v1/health"

# Procesos globales para cleanup
backend_process: Optional[subprocess.Popen] = None
frontend_process: Optional[subprocess.Popen] = None


def is_port_in_use(port: int) -> bool:
    """Verifica si un puerto esta en uso."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def wait_for_backend(port: int, timeout: int = 30) -> bool:
    """Espera a que el backend este disponible."""
    import urllib.request
    import urllib.error

    url = BACKEND_HEALTH_URL.format(port=port)
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return True
        except (urllib.error.URLError, urllib.error.HTTPError, socket.timeout):
            pass
        time.sleep(0.5)

    return False


def start_backend(port: int = DEFAULT_BACKEND_PORT) -> Optional[subprocess.Popen]:
    """Inicia el servidor backend (uvicorn)."""
    global backend_process

    if is_port_in_use(port):
        print(f"[INFO] Backend ya corriendo en puerto {port}")
        return None

    # Configurar PYTHONPATH
    pythonpath = f"{BASE_DIR.parent}:{BASE_DIR}:{os.environ.get('PYTHONPATH', '')}"

    env = os.environ.copy()
    env['PYTHONPATH'] = pythonpath

    # Comando uvicorn
    cmd = [
        sys.executable, "-m", "uvicorn",
        "presentation.api.rest.main:app",
        "--host", "0.0.0.0",
        "--port", str(port),
        "--reload"
    ]

    print(f"[INFO] Iniciando backend en puerto {port}...")

    backend_process = subprocess.Popen(
        cmd,
        cwd=str(BASE_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True
    )

    return backend_process


def start_frontend(port: int = DEFAULT_FRONTEND_PORT) -> Optional[subprocess.Popen]:
    """Inicia el servidor frontend (npm run dev)."""
    global frontend_process

    if is_port_in_use(port):
        print(f"[INFO] Frontend ya corriendo en puerto {port}")
        return None

    if not FRONTEND_DIR.exists():
        print(f"[ERROR] Directorio frontend no encontrado: {FRONTEND_DIR}")
        return None

    env = os.environ.copy()
    env['PORT'] = str(port)

    cmd = ["npm", "run", "dev"]

    print(f"[INFO] Iniciando frontend en puerto {port}...")

    frontend_process = subprocess.Popen(
        cmd,
        cwd=str(FRONTEND_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True
    )

    return frontend_process


def show_splash() -> bool:
    """Muestra el splash screen animado."""
    try:
        from PySide6.QtWidgets import QApplication
        from Plan_ia.splash import AnimatedSplashScreen

        app = QApplication(sys.argv)
        app.setApplicationName("sintaXis")
        app.setApplicationVersion("6.0")

        splash = AnimatedSplashScreen(width=1200, height=800, cols=50, rows=30)
        splash.show()
        app.processEvents()

        # Conectar senal de finalizacion
        splash.animation_complete.connect(app.quit)

        # Ejecutar el loop de eventos
        app.exec()

        return True

    except ImportError as e:
        print(f"[WARN] PySide6 no disponible, omitiendo splash: {e}")
        return False
    except Exception as e:
        print(f"[WARN] Error mostrando splash: {e}")
        return False


def cleanup(signum=None, frame=None):
    """Limpia procesos al salir."""
    global backend_process, frontend_process

    print("\n[INFO] Cerrando servicios...")

    if backend_process and backend_process.poll() is None:
        try:
            os.killpg(os.getpgid(backend_process.pid), signal.SIGTERM)
            print("[INFO] Backend detenido")
        except (ProcessLookupError, PermissionError):
            pass

    if frontend_process and frontend_process.poll() is None:
        try:
            os.killpg(os.getpgid(frontend_process.pid), signal.SIGTERM)
            print("[INFO] Frontend detenido")
        except (ProcessLookupError, PermissionError):
            pass

    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="sintaXis Launcher - Inicia el sistema completo"
    )
    parser.add_argument(
        "--no-splash",
        action="store_true",
        help="Omitir animacion de splash"
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="No abrir navegador automaticamente"
    )
    parser.add_argument(
        "--backend-only",
        action="store_true",
        help="Solo iniciar backend"
    )
    parser.add_argument(
        "--frontend-only",
        action="store_true",
        help="Solo iniciar frontend"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_BACKEND_PORT,
        help=f"Puerto del backend (default: {DEFAULT_BACKEND_PORT})"
    )
    parser.add_argument(
        "--frontend-port",
        type=int,
        default=DEFAULT_FRONTEND_PORT,
        help=f"Puerto del frontend (default: {DEFAULT_FRONTEND_PORT})"
    )

    args = parser.parse_args()

    # Registrar handler de cleanup
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    print("=" * 50)
    print("  sintaXis - Sistema de Gestion Judicial v6")
    print("=" * 50)
    print()

    # Iniciar servicios segun opciones
    if not args.frontend_only:
        start_backend(args.port)

    if not args.backend_only:
        start_frontend(args.frontend_port)

    # Mostrar splash (bloquea hasta que termine la animacion)
    if not args.no_splash:
        print("[INFO] Mostrando splash screen...")
        show_splash()
    else:
        # Si no hay splash, esperar un poco para que los servicios inicien
        print("[INFO] Esperando que los servicios inicien...")
        time.sleep(3)

    # Esperar a que el backend este disponible
    if not args.frontend_only:
        print("[INFO] Verificando backend...")
        if wait_for_backend(args.port, timeout=15):
            print("[OK] Backend disponible")
        else:
            print("[WARN] Backend no responde (puede seguir iniciando)")

    # Abrir navegador
    if not args.no_browser and not args.backend_only:
        url = FRONTEND_URL.format(port=args.frontend_port)
        print(f"[INFO] Abriendo navegador: {url}")
        time.sleep(1)  # Dar tiempo al frontend
        webbrowser.open(url)

    print()
    print("=" * 50)
    print("  Sistema iniciado correctamente")
    print(f"  Frontend: http://localhost:{args.frontend_port}")
    print(f"  Backend:  http://localhost:{args.port}")
    print("  Presiona Ctrl+C para detener")
    print("=" * 50)

    # Mantener el proceso vivo
    try:
        while True:
            time.sleep(1)
            # Verificar si los procesos siguen vivos
            if backend_process and backend_process.poll() is not None:
                print("[WARN] Backend se detuvo inesperadamente")
            if frontend_process and frontend_process.poll() is not None:
                print("[WARN] Frontend se detuvo inesperadamente")
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()
