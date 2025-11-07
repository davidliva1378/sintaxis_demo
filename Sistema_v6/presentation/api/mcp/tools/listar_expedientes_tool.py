"""Herramienta MCP para listar expedientes."""

from __future__ import annotations

from typing import Any

from infrastructure.di_container import DIContainer


async def listar_expedientes_tool(
    container: DIContainer,
    activos_solo: bool = False,
    dias: int = 30,
) -> dict[str, Any]:
    """Lista expedientes almacenados en el sistema.

    Args:
        container: Contenedor DI
        activos_solo: Solo expedientes activos
        dias: Días para considerar activo

    Returns:
        Lista de expedientes
    """
    # Obtener repositorio
    repo = container.expediente_repo

    # Obtener expedientes
    if activos_solo:
        expedientes = await repo.obtener_activos(dias=dias)
    else:
        expedientes = await repo.obtener_todos()

    # Convertir a dict
    expedientes_dict = [
        {
            "numero": exp.numero,
            "dependencia": exp.dependencia,
            "caratula": exp.caratula,
            "situacion": exp.situacion,
            "ultima_actuacion": exp.ultima_actuacion,
        }
        for exp in expedientes
    ]

    return {"total": len(expedientes_dict), "expedientes": expedientes_dict}
