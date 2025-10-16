"""Detección de cambios en entradas y expedientes.

Este módulo compara estados actuales vs anteriores para detectar novedades.
"""

from __future__ import annotations

from ..models import Entrada, ExpedienteResumen
from ..utils.logging import get_logger

logger = get_logger(__name__)


class DetectorCambios:
    """Detecta diferencias entre estados de entradas y expedientes."""

    def detectar_nuevas_entradas(
        self,
        actuales: list[Entrada],
        conocidas: list[Entrada]
    ) -> list[Entrada]:
        """Detecta entradas nuevas comparando con las conocidas.

        Args:
            actuales: Entradas actuales extraídas
            conocidas: Entradas conocidas previamente

        Returns:
            list[Entrada]: Entradas que no están en conocidas
        """
        # Crear conjunto de tuplas (numero, fecha, evento) para comparación rápida
        conjunto_conocidas = {
            (e.numero, e.fecha, e.evento)
            for e in conocidas
        }

        nuevas = [
            e for e in actuales
            if (e.numero, e.fecha, e.evento) not in conjunto_conocidas
        ]

        logger.debug(
            f"Detectadas {len(nuevas)} nuevas entradas de {len(actuales)} actuales "
            f"({len(conocidas)} conocidas)"
        )

        return nuevas

    def detectar_cambios_expedientes(
        self,
        actuales: list[ExpedienteResumen],
        anteriores: list[ExpedienteResumen]
    ) -> list[ExpedienteResumen]:
        """Detecta expedientes con ultima_actuacion diferente.

        Args:
            actuales: Expedientes actuales extraídos
            anteriores: Expedientes del estado anterior

        Returns:
            list[ExpedienteResumen]: Expedientes con cambios en ultima_actuacion
        """
        # Mapear anteriores por número de expediente
        mapa_anterior = {
            exp.numero: exp.ultima_actuacion
            for exp in anteriores
        }

        # Detectar cambios
        cambios = []
        for exp in actuales:
            if exp.numero in mapa_anterior:
                # Expediente ya conocido - verificar si cambió
                if mapa_anterior[exp.numero] != exp.ultima_actuacion:
                    cambios.append(exp)
            # Si no está en mapa_anterior, es nuevo (no cuenta como cambio)

        logger.debug(
            f"Detectados {len(cambios)} expedientes con cambios de {len(actuales)} actuales "
            f"({len(anteriores)} anteriores)"
        )

        return cambios


__all__ = ["DetectorCambios"]
