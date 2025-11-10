"""Modelos de dominio para expedientes del PJN.

Este módulo contiene las entidades relacionadas con expedientes judiciales.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Mapping

from ..utils.coercion import coerce_str, get_first


@dataclass(frozen=True, slots=True)
class ExpedienteResumen:
    """Representa un expediente en el listado del Portal Judicial Nacional.

    Attributes:
        numero: Número de expediente (ej: "FPA-000632-2017")
        dependencia: Juzgado o dependencia a cargo
        caratula: Carátula del expediente
        situacion: Situación procesal actual (opcional)
        ultima_actuacion: Fecha de última actuación en formato ISO (opcional)

    Example:
        >>> exp = ExpedienteResumen(
        ...     numero="FPA-000632-2017",
        ...     dependencia="JUZGADO FEDERAL N°1",
        ...     caratula="EXPEDIENTE JUDICIAL",
        ...     situacion="EN TRAMITE",
        ...     ultima_actuacion="2025-01-15"
        ... )
        >>> exp.numero
        'FPA-000632-2017'
    """

    numero: str
    dependencia: str
    caratula: str
    situacion: str | None = None
    ultima_actuacion: str | None = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ExpedienteResumen:
        """Crea un ExpedienteResumen desde un diccionario.

        Args:
            data: Diccionario con los datos del expediente.
                  Acepta claves con diferentes variaciones (minúsculas, mayúsculas, camelCase).

        Returns:
            Instancia de ExpedienteResumen

        Example:
            >>> data = {
            ...     "numero": "FPA-000632-2017",
            ...     "dependencia": "JUZGADO FEDERAL N°1",
            ...     "caratula": "EXPEDIENTE JUDICIAL"
            ... }
            >>> exp = ExpedienteResumen.from_dict(data)
        """
        return cls(
            numero=coerce_str(get_first(data, "numero", "Numero")) or "",
            dependencia=coerce_str(get_first(data, "dependencia", "Dependencia")) or "",
            caratula=coerce_str(get_first(data, "caratula", "Caratula")) or "",
            situacion=coerce_str(get_first(data, "situacion", "Situacion")),
            ultima_actuacion=coerce_str(
                get_first(data, "ultima_actuacion", "UltimaActuacion", "ultimaActuacion")
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convierte el expediente a un diccionario.

        Returns:
            Diccionario con los atributos del expediente

        Example:
            >>> exp = ExpedienteResumen(...)
            >>> exp.to_dict()
            {'numero': 'FPA-000632-2017', ...}
        """
        return {
            "numero": self.numero,
            "dependencia": self.dependencia,
            "caratula": self.caratula,
            "situacion": self.situacion,
            "ultima_actuacion": self.ultima_actuacion,
        }

    def esta_activo(self, dias: int) -> bool:
        """Verifica si el expediente tuvo movimientos recientes.

        Args:
            dias: Número de días hacia atrás desde hoy para considerar "activo"

        Returns:
            True si ultima_actuacion está dentro del rango de días, False en caso contrario

        Example:
            >>> from datetime import datetime, timedelta
            >>> fecha_reciente = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
            >>> exp = ExpedienteResumen(
            ...     numero="FPA-000632-2017",
            ...     dependencia="JUZGADO",
            ...     caratula="EXPEDIENTE",
            ...     ultima_actuacion=fecha_reciente
            ... )
            >>> exp.esta_activo(30)
            True
            >>> exp.esta_activo(5)
            False
        """
        if not self.ultima_actuacion:
            return False

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

    def __eq__(self, other: object) -> bool:
        """Compara dos expedientes por número.

        Args:
            other: Otro objeto a comparar

        Returns:
            True si ambos expedientes tienen el mismo número
        """
        if not isinstance(other, ExpedienteResumen):
            return NotImplemented
        return self.numero == other.numero

    def __hash__(self) -> int:
        """Calcula hash del expediente basado en su número.

        Returns:
            Hash del número de expediente
        """
        return hash(self.numero)

    def __repr__(self) -> str:
        """Representación string del expediente.

        Returns:
            String con información resumida del expediente
        """
        return (
            f"ExpedienteResumen(numero='{self.numero}', "
            f"dependencia='{self.dependencia}', "
            f"caratula='{self.caratula[:50]}...')"
        )


@dataclass(frozen=True, slots=True)
class ExpedienteIdentificacion:
    """Identificación mínima de un expediente para búsqueda.

    Attributes:
        numero: Número del expediente (sin prefijos ni año)
        anio: Año del expediente

    Example:
        >>> ident = ExpedienteIdentificacion(numero="000632", anio="2017")
        >>> ident.numero
        '000632'
    """

    numero: str
    anio: str

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ExpedienteIdentificacion:
        """Crea una identificación desde un diccionario.

        Args:
            data: Diccionario con numero y anio

        Returns:
            Instancia de ExpedienteIdentificacion
        """
        return cls(
            numero=coerce_str(get_first(data, "numero", "Numero")) or "",
            anio=coerce_str(get_first(data, "anio", "Anio", "año", "Año")) or "",
        )

    def to_dict(self) -> dict[str, str]:
        """Convierte la identificación a diccionario.

        Returns:
            Diccionario con numero y anio
        """
        return {"numero": self.numero, "anio": self.anio}

    def __repr__(self) -> str:
        """Representación string de la identificación.

        Returns:
            String con número y año
        """
        return f"ExpedienteIdentificacion(numero='{self.numero}', anio='{self.anio}')"
