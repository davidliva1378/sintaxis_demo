"""Herramienta MCP para obtener un expediente específico."""

from __future__ import annotations

from typing import Any

from infrastructure.di_container import DIContainer


async def obtener_expediente_tool(
    container: DIContainer,
    numero: str,
) -> dict[str, Any]:
    """Obtiene detalles de un expediente específico.

    Args:
        container: Contenedor DI
        numero: Número del expediente

    Returns:
        Datos del expediente

    Raises:
        ValueError: Si el expediente no existe
    """
    # Obtener repositorio
    repo = container.expediente_repo

    # Buscar expediente
    expediente = await repo.obtener_por_numero(numero)

    if expediente is None:
        raise ValueError(f"Expediente {numero} no encontrado")

    return {
        "numero": expediente.numero,
        "dependencia": expediente.dependencia,
        "caratula": expediente.caratula,
        "situacion": expediente.situacion,
        "ultima_actuacion": expediente.ultima_actuacion,
    }
