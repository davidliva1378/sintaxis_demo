"""Modelos de dominio para expedientes del PJN."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from ._utils import coerce_str, get_first


@dataclass(slots=True)
class ExpedienteResumen:
    """Representa una fila del listado de expedientes."""

    numero: str
    dependencia: str
    caratula: str
    situacion: str | None = None
    ultima_actuacion: str | None = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ExpedienteResumen":
        return cls(
            numero=coerce_str(get_first(data, "numero", "Numero")) or "",
            dependencia=coerce_str(get_first(data, "dependencia", "Dependencia"))
            or "",
            caratula=coerce_str(get_first(data, "caratula", "Caratula")) or "",
            situacion=coerce_str(get_first(data, "situacion", "Situacion")),
            ultima_actuacion=coerce_str(
                get_first(data, "ultima_actuacion", "UltimaActuacion", "ultimaActuacion")
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "numero": self.numero,
            "dependencia": self.dependencia,
            "caratula": self.caratula,
            "situacion": self.situacion,
            "ultima_actuacion": self.ultima_actuacion,
        }


@dataclass(slots=True)
class ExpedienteIdentificacion:
    """Datos mínimos para localizar un expediente puntual."""

    numero: str
    anio: str

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ExpedienteIdentificacion":
        return cls(
            numero=coerce_str(get_first(data, "numero", "Numero")) or "",
            anio=coerce_str(get_first(data, "anio", "Anio", "año", "Año")) or "",
        )

    def to_dict(self) -> dict[str, str]:
        return {"numero": self.numero, "anio": self.anio}
