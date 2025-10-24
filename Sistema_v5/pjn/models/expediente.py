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

    def esta_activo(self, dias: int) -> bool:
        """Verifica si el expediente tuvo movimientos en los últimos N días.

        Args:
            dias: Número de días hacia atrás desde hoy

        Returns:
            True si ultima_actuacion está dentro del rango, False en caso contrario

        Example:
            >>> exp = ExpedienteResumen(..., ultima_actuacion="15/01/2025")
            >>> exp.esta_activo(30)  # True si hoy es antes del 14/02/2025
        """
        if not self.ultima_actuacion:
            return False

        from datetime import datetime, timedelta

        try:
            # Soporta formatos: YYYY-MM-DD, DD/MM/YYYY
            if "/" in self.ultima_actuacion:
                fecha = datetime.strptime(self.ultima_actuacion, "%d/%m/%Y").date()
            else:
                fecha = datetime.fromisoformat(self.ultima_actuacion).date()

            fecha_corte = datetime.now().date() - timedelta(days=dias)
            return fecha >= fecha_corte
        except (ValueError, AttributeError):
            return False


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
