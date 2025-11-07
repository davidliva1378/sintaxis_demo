"""Dataclass para información de expedientes."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ExpedienteInfo:
    """Información de un expediente para procesamiento en batch."""

    numero: str
    caratula: str
    juzgado: str | None = None
    fecha: str | None = None
    tipo: str | None = None

    # Metadata adicional
    metadata: dict[str, Any] = field(default_factory=dict)

    # Campos de seguimiento
    fecha_registro: datetime = field(default_factory=datetime.now)
    ultima_actualizacion: datetime | None = None

    def __post_init__(self):
        """Validar datos al crear instancia."""
        if not self.numero:
            raise ValueError("El número de expediente es obligatorio")
        if not self.caratula:
            raise ValueError("La carátula es obligatoria")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExpedienteInfo":
        """Crea instancia desde diccionario.

        Args:
            data: Diccionario con datos del expediente

        Returns:
            Instancia de ExpedienteInfo
        """
        return cls(
            numero=data.get("numero", ""),
            caratula=data.get("caratula", ""),
            juzgado=data.get("juzgado"),
            fecha=data.get("fecha"),
            tipo=data.get("tipo"),
            metadata=data.get("metadata", {})
        )

    def to_dict(self) -> dict[str, Any]:
        """Convierte la instancia a diccionario.

        Returns:
            Diccionario con todos los campos
        """
        return {
            "numero": self.numero,
            "caratula": self.caratula,
            "juzgado": self.juzgado,
            "fecha": self.fecha,
            "tipo": self.tipo,
            "metadata": self.metadata,
            "fecha_registro": self.fecha_registro.isoformat() if self.fecha_registro else None,
            "ultima_actualizacion": self.ultima_actualizacion.isoformat() if self.ultima_actualizacion else None
        }
