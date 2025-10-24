"""Detección de cambios en entradas y expedientes.

Este módulo compara estados actuales vs anteriores para detectar novedades.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..models import Entrada, ExpedienteResumen
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CambioExpediente:
    """Representa un cambio detectado en un expediente.

    Wrapper que contiene el expediente y metadata sobre el cambio.
    """
    expediente: ExpedienteResumen
    tipo_cambio: str
    campos_cambiados: list[str]
    valores_anteriores: dict[str, str | None]


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
    ) -> list[CambioExpediente]:
        """Detecta expedientes con cambios en cualquier campo relevante.

        Detecta cambios en: ultima_actuacion, situacion, dependencia, caratula

        Args:
            actuales: Expedientes actuales extraídos
            anteriores: Expedientes del estado anterior

        Returns:
            list[CambioExpediente]: Lista de cambios detectados, cada uno con el
                expediente y metadata sobre el tipo de cambio.
        """
        # Mapear anteriores por número de expediente con todos los campos relevantes
        mapa_anterior = {
            exp.numero: {
                "ultima_actuacion": exp.ultima_actuacion,
                "situacion": exp.situacion,
                "dependencia": exp.dependencia,
                "caratula": exp.caratula,
            }
            for exp in anteriores
        }

        # Detectar cambios
        cambios = []
        for exp in actuales:
            if exp.numero in mapa_anterior:
                # Expediente ya conocido - verificar si cambió algún campo
                anterior = mapa_anterior[exp.numero]

                campos_cambiados = []
                if exp.ultima_actuacion != anterior["ultima_actuacion"]:
                    campos_cambiados.append("ultima_actuacion")
                if exp.situacion != anterior["situacion"]:
                    campos_cambiados.append("situacion")
                if exp.dependencia != anterior["dependencia"]:
                    campos_cambiados.append("dependencia")
                if exp.caratula != anterior["caratula"]:
                    campos_cambiados.append("caratula")

                if campos_cambiados:
                    # Clasificar tipo de cambio
                    tipo_cambio = self._clasificar_cambio(campos_cambiados)

                    # Crear objeto CambioExpediente con toda la información
                    cambio = CambioExpediente(
                        expediente=exp,
                        tipo_cambio=tipo_cambio,
                        campos_cambiados=campos_cambiados,
                        valores_anteriores=anterior,
                    )

                    cambios.append(cambio)
            # Si no está en mapa_anterior, es nuevo (no cuenta como cambio)

        logger.debug(
            f"Detectados {len(cambios)} expedientes con cambios de {len(actuales)} actuales "
            f"({len(anteriores)} anteriores)"
        )

        return cambios

    def _clasificar_cambio(self, campos_cambiados: list[str]) -> str:
        """Clasifica el tipo de cambio según los campos modificados.

        Args:
            campos_cambiados: Lista de nombres de campos que cambiaron

        Returns:
            str: Tipo de cambio clasificado
        """
        if len(campos_cambiados) > 1:
            return "multiples_cambios"
        elif "ultima_actuacion" in campos_cambiados:
            return "nueva_actuacion"
        elif "situacion" in campos_cambiados:
            return "cambio_situacion"
        elif "dependencia" in campos_cambiados:
            return "cambio_dependencia"
        elif "caratula" in campos_cambiados:
            return "cambio_caratula"
        else:
            return "cambio_desconocido"


__all__ = ["DetectorCambios", "CambioExpediente"]
