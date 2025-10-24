from __future__ import annotations

"""Funciones de logging centralizadas."""

from datetime import datetime
import os


def registrar_log(mensaje: str) -> None:
    """Registra mensajes en un archivo y los imprime por consola."""
    try:
        os.makedirs("impresion_logs", exist_ok=True)
        with open("impresion_logs/log_monitoreo.txt", "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {mensaje}\n")
    except Exception as e:  # pragma: no cover - errores de logging no deben detener el flujo
        print(f"Error al registrar log: {e}")
    print(mensaje)


__all__ = ["registrar_log"]
