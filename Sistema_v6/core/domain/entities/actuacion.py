"""Modelos de dominio para representar actuaciones del PJN.

Este módulo contiene las entidades relacionadas con actuaciones judiciales
(movimientos procesales dentro de un expediente) y su agrupación en archivos.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from ..utils.coercion import coerce_bool, coerce_int, coerce_str, get_first


@dataclass(frozen=True, slots=True)
class Actuacion:
    """Representa una actuación individual extraída del Portal Judicial Nacional.

    Una actuación es un movimiento procesal registrado en un expediente, que puede
    incluir resoluciones, oficios, cédulas, u otros actos judiciales.

    Attributes:
        indice: Número de orden de la actuación (índice secuencial)
        oficina: Nombre corto de la oficina que registró la actuación
        oficina_completa: Nombre completo de la oficina (opcional)
        fecha: Fecha de la actuación en formato string (opcional)
        tipo: Tipo de actuación (ej: "Resolución", "Oficio") (opcional)
        detalle: Descripción o detalle de la actuación (opcional)
        foja: Número de foja donde se registra (opcional)
        archivo: URL o referencia al archivo adjunto (opcional)
        nombre_archivo: Nombre del archivo adjunto (opcional)
        tiene_archivo: Indica si la actuación tiene archivo adjunto
        tipo_archivo: Extensión o tipo del archivo (ej: "pdf", "doc") (opcional)
        hash: Hash identificador del archivo (opcional)
        extraida_en: Timestamp de cuando fue extraída (opcional)
        es_historica: Indica si es una actuación histórica (anterior a cierta fecha)
        descargado: Indica si el archivo adjunto ya fue descargado

    Example:
        >>> actuacion = Actuacion(
        ...     indice=1,
        ...     oficina="JUZGADO N°1",
        ...     fecha="2025-01-15",
        ...     tipo="Resolución",
        ...     detalle="Se resuelve...",
        ...     tiene_archivo=True,
        ...     tipo_archivo="pdf"
        ... )
        >>> actuacion.indice
        1
        >>> actuacion.tiene_archivo
        True
    """

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
    def from_dict(cls, data: Mapping[str, Any]) -> Actuacion:
        """Crea una Actuacion desde un diccionario.

        Args:
            data: Diccionario con los datos de la actuación.
                  Acepta claves con diferentes variaciones (minúsculas, mayúsculas, camelCase).

        Returns:
            Instancia de Actuacion

        Example:
            >>> data = {
            ...     "indice": 1,
            ...     "oficina": "JUZGADO N°1",
            ...     "fecha": "2025-01-15",
            ...     "tipo": "Resolución"
            ... }
            >>> actuacion = Actuacion.from_dict(data)
            >>> actuacion.indice
            1
        """
        return cls(
            indice=coerce_int(get_first(data, "indice", "Indice"), default=0) or 0,
            oficina=coerce_str(get_first(data, "oficina", "Oficina")) or "",
            oficina_completa=coerce_str(
                get_first(data, "oficina_completa", "OficinaCompleta", "oficinaCompleta")
            ),
            fecha=coerce_str(get_first(data, "fecha", "Fecha")),
            tipo=coerce_str(get_first(data, "tipo", "Tipo")),
            detalle=coerce_str(get_first(data, "detalle", "Detalle")),
            foja=coerce_str(get_first(data, "foja", "Foja")),
            archivo=coerce_str(get_first(data, "archivo", "Archivo")),
            nombre_archivo=coerce_str(
                get_first(data, "nombre_archivo", "NombreArchivo", "nombreArchivo")
            ),
            tiene_archivo=coerce_bool(
                get_first(data, "tiene_archivo", "TieneArchivo", "tieneArchivo"), default=False
            ),
            tipo_archivo=coerce_str(
                get_first(data, "tipo_archivo", "TipoArchivo", "tipoArchivo", "extension")
            ),
            hash=coerce_str(get_first(data, "hash", "Hash")),
            extraida_en=coerce_str(
                get_first(data, "extraida_en", "ExtraidaEn", "extraidaEn")
            ),
            es_historica=coerce_bool(
                get_first(data, "es_historica", "EsHistorica", "esHistorica"), default=False
            ),
            descargado=coerce_bool(
                get_first(data, "descargado", "Descargado"), default=False
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convierte la actuación a un diccionario con claves en minúsculas.

        Returns:
            Diccionario con los atributos de la actuación

        Example:
            >>> actuacion = Actuacion(...)
            >>> actuacion.to_dict()
            {'indice': 1, 'oficina': 'JUZGADO N°1', ...}
        """
        return {
            "indice": self.indice,
            "oficina": self.oficina,
            "oficina_completa": self.oficina_completa,
            "fecha": self.fecha,
            "tipo": self.tipo,
            "detalle": self.detalle,
            "foja": self.foja,
            "archivo": self.archivo,
            "nombre_archivo": self.nombre_archivo,
            "tiene_archivo": self.tiene_archivo,
            "tipo_archivo": self.tipo_archivo,
            "hash": self.hash,
            "extraida_en": self.extraida_en,
            "es_historica": self.es_historica,
            "descargado": self.descargado,
        }

    def to_legacy_dict(self) -> dict[str, Any]:
        """Serializa la actuación utilizando las claves históricas en mayúsculas.

        Este método mantiene compatibilidad con el formato JSON usado en Sistema_v5.

        Returns:
            Diccionario con claves en formato legacy (mayúsculas)

        Example:
            >>> actuacion = Actuacion(...)
            >>> actuacion.to_legacy_dict()
            {'Indice': 1, 'Oficina': 'JUZGADO N°1', ...}
        """
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

    def marcar_como_descargado(self) -> Actuacion:
        """Crea una nueva actuación marcada como descargada.

        Como la entidad es inmutable, este método retorna una nueva instancia
        con el campo 'descargado' en True.

        Returns:
            Nueva instancia de Actuacion con descargado=True

        Example:
            >>> actuacion = Actuacion(..., descargado=False)
            >>> actuacion_descargada = actuacion.marcar_como_descargado()
            >>> actuacion_descargada.descargado
            True
            >>> actuacion.descargado  # La original no cambió
            False
        """
        return Actuacion(
            indice=self.indice,
            oficina=self.oficina,
            oficina_completa=self.oficina_completa,
            fecha=self.fecha,
            tipo=self.tipo,
            detalle=self.detalle,
            foja=self.foja,
            archivo=self.archivo,
            nombre_archivo=self.nombre_archivo,
            tiene_archivo=self.tiene_archivo,
            tipo_archivo=self.tipo_archivo,
            hash=self.hash,
            extraida_en=self.extraida_en,
            es_historica=self.es_historica,
            descargado=True,
        )

    def __eq__(self, other: object) -> bool:
        """Compara dos actuaciones por índice y hash.

        Dos actuaciones son iguales si tienen el mismo índice y hash (o ambos None).

        Args:
            other: Otro objeto a comparar

        Returns:
            True si ambas actuaciones representan la misma actuación
        """
        if not isinstance(other, Actuacion):
            return NotImplemented
        return self.indice == other.indice and self.hash == other.hash

    def __hash__(self) -> int:
        """Calcula hash de la actuación basado en índice y hash.

        Returns:
            Hash de la tupla (indice, hash)
        """
        return hash((self.indice, self.hash))

    def __repr__(self) -> str:
        """Representación string de la actuación.

        Returns:
            String con información resumida de la actuación
        """
        detalle_str = (
            self.detalle[:40] + "..." if self.detalle and len(self.detalle) > 40 else self.detalle
        )
        return (
            f"Actuacion(indice={self.indice}, "
            f"oficina='{self.oficina}', "
            f"fecha='{self.fecha}', "
            f"tipo='{self.tipo}', "
            f"detalle='{detalle_str}')"
        )


@dataclass(frozen=True, slots=True)
class ActuacionesArchivo:
    """Agrupa el encabezado y la colección de actuaciones para exportar a JSON.

    Esta clase representa el formato completo de un archivo JSON que contiene
    las actuaciones de un expediente junto con su información de encabezado.

    Attributes:
        encabezado: Diccionario con información del expediente (número, carátula, etc.)
        actuaciones: Tupla inmutable de actuaciones del expediente

    Example:
        >>> encabezado = {
        ...     "numero": "FPA-000632-2017",
        ...     "caratula": "EXPEDIENTE JUDICIAL"
        ... }
        >>> actuaciones = (
        ...     Actuacion(indice=1, oficina="JUZGADO", fecha="2025-01-15"),
        ...     Actuacion(indice=2, oficina="JUZGADO", fecha="2025-01-16"),
        ... )
        >>> archivo = ActuacionesArchivo(encabezado=encabezado, actuaciones=actuaciones)
        >>> len(archivo.actuaciones)
        2
    """

    encabezado: Mapping[str, Any]
    actuaciones: tuple[Actuacion, ...]

    def to_dict(self) -> dict[str, Any]:
        """Convierte a estructura serializable con claves en minúsculas.

        Returns:
            Diccionario con 'expediente' y 'actuaciones'

        Example:
            >>> archivo = ActuacionesArchivo(...)
            >>> data = archivo.to_dict()
            >>> 'expediente' in data
            True
            >>> 'actuaciones' in data
            True
        """
        return {
            "expediente": dict(self.encabezado),
            "actuaciones": [act.to_dict() for act in self.actuaciones],
        }

    def to_legacy_dict(self) -> dict[str, Any]:
        """Convierte a estructura compatible con Sistema_v5 (claves mayúsculas).

        Returns:
            Diccionario con 'Expediente' y 'Actuaciones'

        Example:
            >>> archivo = ActuacionesArchivo(...)
            >>> data = archivo.to_legacy_dict()
            >>> 'Expediente' in data
            True
            >>> 'Actuaciones' in data
            True
        """
        return {
            "Expediente": dict(self.encabezado),
            "Actuaciones": [act.to_legacy_dict() for act in self.actuaciones],
        }

    def contar_con_archivo(self) -> int:
        """Cuenta cuántas actuaciones tienen archivo adjunto.

        Returns:
            Número de actuaciones con tiene_archivo=True

        Example:
            >>> archivo = ActuacionesArchivo(...)
            >>> archivo.contar_con_archivo()
            5
        """
        return sum(1 for act in self.actuaciones if act.tiene_archivo)

    def contar_descargados(self) -> int:
        """Cuenta cuántas actuaciones tienen el archivo descargado.

        Returns:
            Número de actuaciones con descargado=True

        Example:
            >>> archivo = ActuacionesArchivo(...)
            >>> archivo.contar_descargados()
            3
        """
        return sum(1 for act in self.actuaciones if act.descargado)

    def filtrar_por_tipo(self, tipo: str) -> tuple[Actuacion, ...]:
        """Filtra actuaciones por tipo.

        Args:
            tipo: Tipo de actuación a filtrar (ej: "Resolución")

        Returns:
            Tupla con actuaciones del tipo especificado

        Example:
            >>> archivo = ActuacionesArchivo(...)
            >>> resoluciones = archivo.filtrar_por_tipo("Resolución")
            >>> len(resoluciones)
            3
        """
        return tuple(act for act in self.actuaciones if act.tipo == tipo)

    def __len__(self) -> int:
        """Retorna el número de actuaciones.

        Returns:
            Cantidad de actuaciones
        """
        return len(self.actuaciones)

    def __repr__(self) -> str:
        """Representación string del archivo de actuaciones.

        Returns:
            String con información resumida
        """
        numero = self.encabezado.get("numero", self.encabezado.get("Numero", "N/A"))
        return (
            f"ActuacionesArchivo(expediente='{numero}', "
            f"actuaciones={len(self.actuaciones)})"
        )
