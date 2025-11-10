"""Herramienta MCP para extraer expedientes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from application.dtos import ExtraerExpedientesCommand
from infrastructure.di_container import DIContainer


async def extraer_expedientes_tool(
    container: DIContainer,
    usuario: str | None = None,
    contrasena: str | None = None,
    headless: bool = True,
    guardar_en: str | None = None,
) -> dict[str, Any]:
    """Extrae expedientes del Portal Judicial Nacional.

    Args:
        container: Contenedor DI
        usuario: Usuario del PJN
        contrasena: Contraseña del PJN
        headless: Ejecutar navegador sin interfaz
        guardar_en: Path donde guardar el JSON

    Returns:
        Resultado de la extracción
    """
    # Preparar comando
    guardar_path = Path(guardar_en) if guardar_en else None
    command = ExtraerExpedientesCommand(
        usuario=usuario,
        contrasena=contrasena,
        headless=headless,
        guardar_en=guardar_path,
    )

    # Ejecutar use case
    use_case = container.extraer_expedientes_use_case()
    result = await use_case.execute(command)

    if result.success:
        response = result.value
        return {
            "total": response.total,
            "archivo_guardado": str(response.archivo_guardado) if response.archivo_guardado else None,
        }
    else:
        raise RuntimeError(result.error or "Error desconocido en extracción")
