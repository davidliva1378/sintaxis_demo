"""Modelos de dominio para entradas y notificaciones del PJN.

Este módulo contiene las entidades relacionadas con notificaciones y despachos
que aparecen en el Portal Judicial Nacional.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from ..utils.coercion import coerce_bool, coerce_str, get_first


@dataclass(frozen=True, slots=True)
class Entrada:
    """Representa una notificación o despacho en el Portal Judicial Nacional.

    Una entrada es un evento que notifica al usuario sobre cambios o actualizaciones
    en un expediente. Puede ser una notificación de despacho, un evento procesal,
    o cualquier otro tipo de comunicación judicial.

    Attributes:
        numero: Número de expediente asociado (ej: "FPA-000632-2017")
        caratula: Carátula del expediente
        fecha: Fecha del evento en formato string (ISO o DD/MM/YYYY)
        evento: Descripción del evento o acción (opcional)
        tipo_evento: Categoría o tipo del evento (opcional)
        leida: Indica si la entrada ya fue leída por el usuario
        extraida_en: Timestamp de cuando fue extraída del portal (opcional)

    Example:
        >>> entrada = Entrada(
        ...     numero="FPA-000632-2017",
        ...     caratula="EXPEDIENTE JUDICIAL",
        ...     fecha="2025-01-15",
        ...     evento="Notificación de despacho",
        ...     tipo_evento="DESPACHO",
        ...     leida=False
        ... )
        >>> entrada.numero
        'FPA-000632-2017'
        >>> entrada.leida
        False
    """

    numero: str
    caratula: str
    fecha: str
    evento: str | None = None
    tipo_evento: str | None = None
    leida: bool = False
    extraida_en: str | None = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Entrada:
        """Crea una Entrada desde un diccionario.

        Args:
            data: Diccionario con los datos de la entrada.
                  Acepta claves con diferentes variaciones (minúsculas, mayúsculas, camelCase).

        Returns:
            Instancia de Entrada

        Example:
            >>> data = {
            ...     "numero": "FPA-000632-2017",
            ...     "caratula": "EXPEDIENTE JUDICIAL",
            ...     "fecha": "2025-01-15",
            ...     "evento": "Notificación",
            ...     "leida": False
            ... }
            >>> entrada = Entrada.from_dict(data)
            >>> entrada.numero
            'FPA-000632-2017'
        """
        return cls(
            numero=coerce_str(get_first(data, "numero", "Numero")) or "",
            caratula=coerce_str(get_first(data, "caratula", "Caratula")) or "",
            fecha=coerce_str(get_first(data, "fecha", "Fecha")) or "",
            evento=coerce_str(get_first(data, "evento", "Evento")),
            tipo_evento=coerce_str(get_first(data, "tipo_evento", "TipoEvento", "tipoEvento")),
            leida=coerce_bool(get_first(data, "leida", "Leida"), default=False),
            extraida_en=coerce_str(get_first(data, "extraida_en", "ExtraidaEn", "extraidaEn")),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convierte la entrada a un diccionario.

        Returns:
            Diccionario con los atributos de la entrada

        Example:
            >>> entrada = Entrada(...)
            >>> entrada.to_dict()
            {'numero': 'FPA-000632-2017', 'caratula': '...', ...}
        """
        return {
            "numero": self.numero,
            "caratula": self.caratula,
            "fecha": self.fecha,
            "evento": self.evento,
            "tipo_evento": self.tipo_evento,
            "leida": self.leida,
            "extraida_en": self.extraida_en,
        }

    def marcar_como_leida(self) -> Entrada:
        """Crea una nueva entrada marcada como leída.

        Como la entidad es inmutable, este método retorna una nueva instancia
        con el campo 'leida' en True.

        Returns:
            Nueva instancia de Entrada con leida=True

        Example:
            >>> entrada = Entrada(..., leida=False)
            >>> entrada_leida = entrada.marcar_como_leida()
            >>> entrada_leida.leida
            True
            >>> entrada.leida  # La original no cambió
            False
        """
        return Entrada(
            numero=self.numero,
            caratula=self.caratula,
            fecha=self.fecha,
            evento=self.evento,
            tipo_evento=self.tipo_evento,
            leida=True,
            extraida_en=self.extraida_en,
        )

    def __eq__(self, other: object) -> bool:
        """Compara dos entradas por número, fecha y evento.

        Dos entradas son iguales si tienen el mismo número de expediente,
        la misma fecha y el mismo evento (o ambos None).

        Args:
            other: Otro objeto a comparar

        Returns:
            True si ambas entradas representan el mismo evento
        """
        if not isinstance(other, Entrada):
            return NotImplemented
        return (
            self.numero == other.numero
            and self.fecha == other.fecha
            and self.evento == other.evento
        )

    def __hash__(self) -> int:
        """Calcula hash de la entrada basado en número, fecha y evento.

        Returns:
            Hash de la tupla (numero, fecha, evento)
        """
        return hash((self.numero, self.fecha, self.evento))

    def __repr__(self) -> str:
        """Representación string de la entrada.

        Returns:
            String con información resumida de la entrada
        """
        evento_str = self.evento[:30] + "..." if self.evento and len(self.evento) > 30 else self.evento
        return (
            f"Entrada(numero='{self.numero}', "
            f"fecha='{self.fecha}', "
            f"evento='{evento_str}', "
            f"leida={self.leida})"
        )
