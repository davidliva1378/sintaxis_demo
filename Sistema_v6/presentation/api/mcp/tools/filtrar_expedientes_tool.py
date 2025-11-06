"""Herramienta MCP para filtrar expedientes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from application.dtos import FiltrarExpedientesCommand
from infrastructure.di_container import DIContainer


async def filtrar_expedientes_tool(
    container: DIContainer,
    numeros_seleccionados: list[str],
    origen: str,
    destino: str | None = None,
    incluir_activos: bool = False,
    dias_actividad: int = 30,
) -> dict[str, Any]:
    """Filtra expedientes según selección del usuario.

    Args:
        container: Contenedor DI
        numeros_seleccionados: Lista de números de expedientes
        origen: Path del JSON origen
        destino: Path del JSON destino
        incluir_activos: Incluir expedientes activos
        dias_actividad: Días para considerar activo

    Returns:
        Resultado del filtrado
    """
    # Preparar comando
    command = FiltrarExpedientesCommand(
        numeros_seleccionados=numeros_seleccionados,
        origen=Path(origen),
        destino=Path(destino) if destino else None,
        incluir_activos=incluir_activos,
        dias_actividad=dias_actividad,
    )

    # Ejecutar use case
    use_case = container.filtrar_expedientes_use_case()
    result = await use_case.execute(command)

    if result.success:
        response = result.value
        return {
            "total_origen": response.total_origen,
            "total_filtrados": response.total_filtrados,
            "archivo_guardado": str(response.archivo_guardado) if response.archivo_guardado else None,
        }
    else:
        raise RuntimeError(result.error or "Error desconocido en filtrado")
