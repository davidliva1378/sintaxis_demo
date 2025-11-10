"""Herramienta MCP para monitorear expedientes."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from application.dtos import MonitorearExpedientesCommand
from infrastructure.di_container import DIContainer


async def monitorear_expedientes_tool(
    container: DIContainer,
    archivo_sistema: str,
    workspaces_dir: str | None = None,
    intervalo_minutos: int = 60,
    notificar: bool = True,
) -> dict[str, Any]:
    """Monitorea expedientes para detectar cambios (verificación única).

    Args:
        container: Contenedor DI
        archivo_sistema: Path del JSON sistema
        workspaces_dir: Directorio base para workspaces
        intervalo_minutos: Intervalo de verificación
        notificar: Enviar notificaciones

    Returns:
        Resultado del monitoreo con cambios detectados
    """
    # Preparar comando
    command = MonitorearExpedientesCommand(
        archivo_sistema=Path(archivo_sistema),
        workspaces_dir=Path(workspaces_dir) if workspaces_dir else None,
        intervalo_minutos=intervalo_minutos,
        notificar=notificar,
    )

    # Ejecutar use case (una verificación)
    use_case = container.monitorear_expedientes_use_case()
    result = await use_case.execute(command)

    if result.success:
        response = result.value

        # Convertir cambios a formato legible
        cambios = [
            {
                "numero_expediente": cambio.get("numero_expediente", ""),
                "tipo_cambio": cambio.get("tipo_cambio", "desconocido"),
                "descripcion": cambio.get("descripcion", ""),
                "fecha_deteccion": cambio.get("fecha_deteccion", datetime.now().isoformat()),
            }
            for cambio in response.cambios
        ]

        return {
            "total_expedientes": response.total_expedientes,
            "cambios_detectados": response.cambios_detectados,
            "cambios": cambios,
        }
    else:
        raise RuntimeError(result.error or "Error desconocido en monitoreo")
