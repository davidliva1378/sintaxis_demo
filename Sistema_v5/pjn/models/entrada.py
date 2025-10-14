"""Modelos de dominio para entradas y notificaciones del PJN."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from ._utils import coerce_bool, coerce_str, get_first


@dataclass(slots=True)
class Entrada:
    """Evento de notificación o despacho registrado en el portal."""

    numero: str
    caratula: str
    fecha: str
    evento: str | None = None
    tipo_evento: str | None = None
    leida: bool = False
    extraida_en: str | None = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Entrada":
        return cls(
            numero=coerce_str(get_first(data, "numero", "Numero")) or "",
            caratula=coerce_str(get_first(data, "caratula", "Caratula")) or "",
            fecha=coerce_str(get_first(data, "fecha", "Fecha")) or "",
            evento=coerce_str(get_first(data, "evento", "Evento")),
            tipo_evento=coerce_str(get_first(data, "tipo_evento", "TipoEvento")),
            leida=coerce_bool(get_first(data, "leida", "Leida"), default=False),
            extraida_en=coerce_str(get_first(data, "extraida_en", "ExtraidaEn")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "numero": self.numero,
            "caratula": self.caratula,
            "fecha": self.fecha,
            "evento": self.evento,
            "tipo_evento": self.tipo_evento,
            "leida": self.leida,
            "extraida_en": self.extraida_en,
        }
