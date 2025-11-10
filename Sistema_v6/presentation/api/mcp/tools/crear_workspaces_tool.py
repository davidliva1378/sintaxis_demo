"""Herramienta MCP para crear workspaces."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from application.dtos import CrearWorkspacesCommand
from infrastructure.di_container import DIContainer


async def crear_workspaces_tool(
    container: DIContainer,
    archivo_sistema: str,
    workspaces_dir: str | None = None,
    extraer_actuaciones: bool = False,
    descargar_archivos: bool = False,
) -> dict[str, Any]:
    """Crea workspaces para expedientes del sistema.

    Args:
        container: Contenedor DI
        archivo_sistema: Path del JSON sistema
        workspaces_dir: Directorio base para workspaces
        extraer_actuaciones: Extraer actuaciones al crear
        descargar_archivos: Descargar archivos adjuntos

    Returns:
        Resultado de la creación
    """
    # Preparar comando
    command = CrearWorkspacesCommand(
        archivo_sistema=Path(archivo_sistema),
        workspaces_dir=Path(workspaces_dir) if workspaces_dir else None,
        extraer_actuaciones=extraer_actuaciones,
        descargar_archivos=descargar_archivos,
    )

    # Ejecutar use case
    use_case = container.crear_workspaces_use_case()
    result = await use_case.execute(command)

    if result.success:
        response = result.value
        return {
            "total_expedientes": response.total_expedientes,
            "workspaces_creados": response.workspaces_creados,
            "errores": response.errores,
        }
    else:
        raise RuntimeError(result.error or "Error desconocido en creación de workspaces")
