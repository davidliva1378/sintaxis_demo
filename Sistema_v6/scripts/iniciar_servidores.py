#!/usr/bin/env python3
"""Script para iniciar servidores de backend y frontend del Sistema PJN v6.

Este script inicia ambos servidores en paralelo:
- Backend: FastAPI en http://127.0.0.1:8000
- Frontend: React + Vite en http://localhost:5174

Uso:
    python scripts/iniciar_servidores.py

    O hacerlo ejecutable:
    chmod +x scripts/iniciar_servidores.py
    ./scripts/iniciar_servidores.py

Para detener ambos servidores: Ctrl+C
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def encontrar_base_proyecto() -> Path:
    """Encuentra el directorio base del proyecto (sintaXis)."""
    script_dir = Path(__file__).resolve().parent
    # scripts/ -> Sistema_v6/ -> sintaXis/
    return script_dir.parent.parent


def main():
    """Inicia ambos servidores en paralelo."""
    # Obtener rutas
    base_proyecto = encontrar_base_proyecto()
    sistema_v6 = base_proyecto / "Sistema_v6"
    frontend_dir = sistema_v6 / "frontend"
    venv_python = base_proyecto / ".venv1" / "bin" / "python"

    # Verificar que existen los directorios
    if not sistema_v6.exists():
        print(f"❌ Error: No existe el directorio {sistema_v6}")
        sys.exit(1)

    if not frontend_dir.exists():
        print(f"❌ Error: No existe el directorio {frontend_dir}")
        sys.exit(1)

    if not venv_python.exists():
        print(f"❌ Error: No existe el entorno virtual en {venv_python}")
        print("   Usando python del sistema...")
        venv_python = "python3"

    # Configurar variables de entorno para el backend
    env_backend = os.environ.copy()
    env_backend["PYTHONPATH"] = str(base_proyecto)

    # Comandos
    backend_cmd = [
        str(venv_python),
        "-m",
        "uvicorn",
        "presentation.api.rest.main:app",
        "--reload",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
    ]

    frontend_cmd = ["npm", "run", "dev"]

    print("🚀 Iniciando servidores del Sistema PJN v6...\n")
    print(f"📁 Directorio base: {base_proyecto}")
    print(f"📁 Sistema v6: {sistema_v6}")
    print(f"📁 Frontend: {frontend_dir}\n")

    # Iniciar procesos
    procesos = []

    try:
        # Iniciar backend
        print("🔧 Iniciando backend (FastAPI)...")
        print(f"   Comando: {' '.join(backend_cmd)}")
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=str(sistema_v6),
            env=env_backend,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        procesos.append(("Backend", backend_proc))
        print("   ✓ Backend iniciado (PID: {})\n".format(backend_proc.pid))

        # Dar tiempo al backend para iniciar
        time.sleep(2)

        # Iniciar frontend
        print("🎨 Iniciando frontend (React + Vite)...")
        print(f"   Comando: {' '.join(frontend_cmd)}")
        frontend_proc = subprocess.Popen(
            frontend_cmd,
            cwd=str(frontend_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        procesos.append(("Frontend", frontend_proc))
        print("   ✓ Frontend iniciado (PID: {})\n".format(frontend_proc.pid))

        print("=" * 60)
        print("✅ Ambos servidores iniciados correctamente\n")
        print("🌐 URLs:")
        print("   Backend API: http://127.0.0.1:8000")
        print("   Backend Docs: http://127.0.0.1:8000/docs")
        print("   Frontend: http://localhost:5174\n")
        print("📝 Para detener ambos servidores: Ctrl+C")
        print("=" * 60)
        print("\n📋 Logs:\n")

        # Mostrar logs de ambos procesos intercalados
        while True:
            # Leer logs del backend
            if backend_proc.poll() is None:
                line = backend_proc.stdout.readline()
                if line:
                    print(f"[BACKEND] {line.rstrip()}")

            # Leer logs del frontend
            if frontend_proc.poll() is None:
                line = frontend_proc.stdout.readline()
                if line:
                    print(f"[FRONTEND] {line.rstrip()}")

            # Si ambos procesos terminaron, salir
            if backend_proc.poll() is not None and frontend_proc.poll() is not None:
                break

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\n🛑 Deteniendo servidores...")

        # Detener procesos gracefully
        for nombre, proceso in procesos:
            if proceso.poll() is None:
                print(f"   Deteniendo {nombre} (PID: {proceso.pid})...")
                try:
                    proceso.send_signal(signal.SIGTERM)
                    proceso.wait(timeout=5)
                    print(f"   ✓ {nombre} detenido")
                except subprocess.TimeoutExpired:
                    print(f"   ⚠️  {nombre} no respondió, forzando cierre...")
                    proceso.kill()
                    proceso.wait()
                    print(f"   ✓ {nombre} forzado a cerrar")

        print("\n✅ Servidores detenidos correctamente")

    except Exception as e:
        print(f"\n❌ Error: {e}")

        # Limpiar procesos en caso de error
        for nombre, proceso in procesos:
            if proceso.poll() is None:
                proceso.kill()
                proceso.wait()

        sys.exit(1)


if __name__ == "__main__":
    main()