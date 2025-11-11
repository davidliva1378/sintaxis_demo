"""Modelos de dominio para representar actuaciones del PJN."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from Sistema_v6.core.domain.utils.coercion import coerce_bool, coerce_int, coerce_str, get_first


@dataclass(slots=True)
class Actuacion:
    """Representa una actuación individual extraída del PJN."""

    indice: int
    oficina: str
    oficina_completa: str | None = None
    fecha: str | None = None
    tipo: str | None = None
    detalle: str | None = None
    foja: str | None = None
    archivo: str | None = None
    nombre_archivo: str | None = None
    tiene_archivo: bool = False
    tipo_archivo: str | None = None
    hash: str | None = None
    extraida_en: str | None = None
    es_historica: bool = False
    descargado: bool = False

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Actuacion":
        """Construye una :class:`Actuacion` a partir de un diccionario."""

        return cls(
            indice=coerce_int(get_first(data, "Indice", "indice"), default=0) or 0,
            oficina=coerce_str(get_first(data, "Oficina", "oficina")) or "",
            oficina_completa=coerce_str(
                get_first(data, "OficinaCompleta", "oficina_completa")
            ),
            fecha=coerce_str(get_first(data, "Fecha", "fecha")),
            tipo=coerce_str(get_first(data, "Tipo", "tipo")),
            detalle=coerce_str(get_first(data, "Detalle", "detalle")),
            foja=coerce_str(get_first(data, "Foja", "foja")),
            archivo=coerce_str(get_first(data, "Archivo", "archivo")),
            nombre_archivo=coerce_str(
                get_first(data, "NombreArchivo", "nombre_archivo")
            ),
            tiene_archivo=coerce_bool(
                get_first(data, "TieneArchivo", "tiene_archivo"), default=False
            ),
            tipo_archivo=coerce_str(
                get_first(data, "TipoArchivo", "tipo_archivo", "extension")
            ),
            hash=coerce_str(get_first(data, "Hash", "hash")),
            extraida_en=coerce_str(get_first(data, "ExtraidaEn", "extraida_en")),
            es_historica=coerce_bool(
                get_first(data, "EsHistorica", "es_historica"), default=False
            ),
            descargado=coerce_bool(
                get_first(data, "Descargado", "descargado"), default=False
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serializa la actuación utilizando las claves históricas."""

        return {
            "Indice": self.indice,
            "Oficina": self.oficina,
            "OficinaCompleta": self.oficina_completa,
            "Fecha": self.fecha,
            "Tipo": self.tipo,
            "Detalle": self.detalle,
            "Foja": self.foja,
            "Archivo": self.archivo,
            "NombreArchivo": self.nombre_archivo,
            "TieneArchivo": self.tiene_archivo,
            "TipoArchivo": self.tipo_archivo,
            "Hash": self.hash,
            "ExtraidaEn": self.extraida_en,
            "EsHistorica": self.es_historica,
            "Descargado": self.descargado,
        }

    def to_json_ready(self) -> dict[str, Any]:
        """Alias explícito de :meth:`to_dict` para compatibilidad con dumps."""

        return self.to_dict()


@dataclass(slots=True)
class ActuacionesArchivo:
    """Agrupa el encabezado y la colección de actuaciones para exportar JSON."""

    encabezado: Mapping[str, Any]
    actuaciones: tuple[Actuacion, ...]

    def to_dict(self) -> dict[str, Any]:
        """Devuelve una estructura serializable compatible con versiones previas."""

        return {
            "Expediente": dict(self.encabezado),
            "Actuaciones": [act.to_dict() for act in self.actuaciones],
        }
