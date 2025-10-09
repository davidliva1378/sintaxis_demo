"""API de alto nivel para consumir archivos de actuaciones generados por el scraper v4.

Este módulo evita dependencias con Playwright y expone utilidades pensadas para
aplicaciones externas que sólo necesitan leer, inspeccionar, filtrar o actualizar
los archivos JSON producidos por ``actuaciones_v4``.

Funciones clave:
* :func:`cargar_expediente_actuaciones` lee un JSON y lo convierte en una
  estructura tipada.
* :class:`ActuacionesExpediente` ofrece helpers para filtrar actuaciones,
  recalcular métricas y persistir cambios.
* :class:`Actuacion` encapsula una actuación individual manteniendo los campos
  originales y metadatos derivados.

El formato soportado corresponde a las versiones ``1.0`` y ``1.1`` del esquema
interno documentado en ``Sistema_v4/documentacion/actuaciones_v4_metadata.md``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence


VERSIONES_COMPATIBLES = {"1.0", "1.1"}


def _asegurar_dict(datos: Any, *, llave: str) -> Dict[str, Any]:
    if not isinstance(datos, dict):
        raise ValueError(f"Se esperaba un objeto con la llave '{llave}'.")
    return datos


def _asegurar_lista_actuaciones(datos: Any) -> List[Dict[str, Any]]:
    if not isinstance(datos, list):
        raise ValueError("La llave 'Actuaciones' debe contener una lista.")
    return [a for a in datos if isinstance(a, dict)]


def _parsear_fecha(valor: Optional[str]) -> Optional[datetime]:
    if not valor:
        return None
    for formato in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):  # tolera variantes antiguas
        try:
            return datetime.strptime(valor, formato)
        except ValueError:
            continue
    return None


def _contar_adjuntos(actuaciones: Sequence["Actuacion"]) -> tuple[int, int, int]:
    total_con_enlace = sum(1 for act in actuaciones if act.tiene_archivo)
    total_descargados = sum(1 for act in actuaciones if act.descargado)
    pendientes = max(total_con_enlace - total_descargados, 0)
    return total_con_enlace, total_descargados, pendientes


@dataclass
class Actuacion:
    """Representa una actuación individual del expediente."""

    indice: Optional[int]
    oficina: str
    oficina_completa: str
    fecha: str
    tipo: str
    detalle: str
    foja: str
    archivo: str
    nombre_archivo: str
    tiene_archivo: bool
    tipo_archivo: str
    hash: Optional[str]
    extraida_en: str
    es_historica: bool
    descargado: bool
    datos_adicionales: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, datos: Dict[str, Any]) -> "Actuacion":
        conocidos = {
            "Indice",
            "Oficina",
            "OficinaCompleta",
            "Fecha",
            "Tipo",
            "Detalle",
            "Foja",
            "Archivo",
            "NombreArchivo",
            "TieneArchivo",
            "TipoArchivo",
            "Hash",
            "ExtraidaEn",
            "EsHistorica",
            "Descargado",
        }
        extras = {k: v for k, v in datos.items() if k not in conocidos}
        return cls(
            indice=datos.get("Indice"),
            oficina=datos.get("Oficina", "N/A"),
            oficina_completa=datos.get("OficinaCompleta", datos.get("Oficina", "N/A")),
            fecha=datos.get("Fecha", "N/A"),
            tipo=datos.get("Tipo", "N/A"),
            detalle=datos.get("Detalle", "N/A"),
            foja=datos.get("Foja", "N/A"),
            archivo=datos.get("Archivo", "N/A"),
            nombre_archivo=datos.get("NombreArchivo", "N/A"),
            tiene_archivo=bool(datos.get("TieneArchivo")),
            tipo_archivo=datos.get("TipoArchivo", "N/A"),
            hash=datos.get("Hash"),
            extraida_en=datos.get("ExtraidaEn", ""),
            es_historica=bool(datos.get("EsHistorica")),
            descargado=bool(datos.get("Descargado")),
            datos_adicionales=extras,
        )

    def to_dict(self) -> Dict[str, Any]:
        datos = {
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
        datos.update(self.datos_adicionales)
        return datos

    def marcar_descargado(self, *, nombre_archivo: Optional[str] = None, estado: bool = True) -> None:
        """Actualiza la bandera de descarga y opcionalmente el nombre del archivo."""

        self.descargado = estado
        if nombre_archivo:
            self.nombre_archivo = nombre_archivo

    @property
    def es_actual(self) -> bool:
        return not self.es_historica


@dataclass
class ActuacionesExpediente:
    """Contenedor de actuaciones y metadatos de un expediente."""

    metadata: Dict[str, Any]
    actuaciones: List[Actuacion]

    @classmethod
    def from_dict(cls, datos: Dict[str, Any]) -> "ActuacionesExpediente":
        encabezado = _asegurar_dict(datos.get("Expediente"), llave="Expediente")
        actuaciones = [Actuacion.from_dict(item) for item in _asegurar_lista_actuaciones(datos.get("Actuaciones"))]
        instancia = cls(metadata=dict(encabezado), actuaciones=actuaciones)
        instancia._validar_version()
        return instancia

    @classmethod
    def cargar_desde_archivo(cls, ruta: str | Path) -> "ActuacionesExpediente":
        ruta = Path(ruta)
        if not ruta.exists():
            raise FileNotFoundError(f"No se encontró el archivo de actuaciones: {ruta}")
        with ruta.open("r", encoding="utf-8") as fh:
            datos = json.load(fh)
        instancia = cls.from_dict(datos)
        instancia.metadata.setdefault("_origen_archivo", str(ruta))
        return instancia

    def guardar(self, ruta: str | Path | None = None, *, indent: int = 2) -> Path:
        """Persiste el expediente en disco, recalculando métricas antes de guardar."""

        self.recalcular_metricas()
        destino = Path(ruta) if ruta else Path(self.metadata.get("_origen_archivo", "actuaciones.json"))
        destino.parent.mkdir(parents=True, exist_ok=True)
        with destino.open("w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=indent, ensure_ascii=False)
        return destino

    def to_dict(self) -> Dict[str, Any]:
        self.recalcular_metricas()
        return {
            "Expediente": dict(self.metadata),
            "Actuaciones": [act.to_dict() for act in self.actuaciones],
        }

    def _validar_version(self) -> None:
        version = self.metadata.get("version_formato")
        if version and version not in VERSIONES_COMPATIBLES:
            raise ValueError(
                f"Versión de formato no soportada: {version}. Compatibles: {sorted(VERSIONES_COMPATIBLES)}"
            )

    def obtener_fecha_extraccion(self) -> Optional[datetime]:
        return _parsear_fecha(self.metadata.get("fecha_extraccion"))

    def filtrar_actuaciones(
        self,
        *,
        historicas: Optional[bool] = None,
        con_archivo: Optional[bool] = None,
        descargadas: Optional[bool] = None,
    ) -> List[Actuacion]:
        """Devuelve actuaciones filtradas según los parámetros indicados."""

        resultado: List[Actuacion] = []
        for act in self.actuaciones:
            if historicas is not None and act.es_historica != historicas:
                continue
            if con_archivo is not None and act.tiene_archivo != con_archivo:
                continue
            if descargadas is not None and act.descargado != descargadas:
                continue
            resultado.append(act)
        return resultado

    def iter_actuaciones(self, **filtros: Any) -> Iterator[Actuacion]:
        """Iterador lazily filtrado utilizando :meth:`filtrar_actuaciones`."""

        for act in self.filtrar_actuaciones(**filtros):
            yield act

    def obtener_por_hash(self, hash_valor: str) -> Optional[Actuacion]:
        return next((act for act in self.actuaciones if act.hash == hash_valor), None)

    def obtener_por_indice(self, indice: int) -> Optional[Actuacion]:
        return next((act for act in self.actuaciones if act.indice == indice), None)

    def marcar_descargado(
        self,
        *,
        hash_valor: Optional[str] = None,
        indice: Optional[int] = None,
        nombre_archivo: Optional[str] = None,
        estado: bool = True,
    ) -> Actuacion:
        """Actualiza el estado de descarga de una actuación identificada por hash o índice."""

        objetivo: Optional[Actuacion] = None
        if hash_valor:
            objetivo = self.obtener_por_hash(hash_valor)
        if objetivo is None and indice is not None:
            objetivo = self.obtener_por_indice(indice)
        if objetivo is None:
            raise KeyError("No se encontró la actuación solicitada por hash ni por índice.")
        objetivo.marcar_descargado(nombre_archivo=nombre_archivo, estado=estado)
        self.recalcular_metricas()
        return objetivo

    def resumen_descargas(self) -> Dict[str, int]:
        """Obtiene los contadores de adjuntos y descargas vigentes."""

        total_con, total_descargados, pendientes = _contar_adjuntos(self.actuaciones)
        return {
            "total_con_enlace": total_con,
            "total_descargados": total_descargados,
            "pendientes": pendientes,
        }

    def recalcular_metricas(self) -> None:
        """Sincroniza los contadores del encabezado con el listado actual de actuaciones."""

        total_actuaciones = len(self.actuaciones)
        total_historicas = sum(1 for act in self.actuaciones if act.es_historica)
        total_actuales = total_actuaciones - total_historicas

        total_con, total_descargados, pendientes = _contar_adjuntos(self.actuaciones)

        self.metadata.setdefault("version_formato", "1.1")
        self.metadata.setdefault("incluye_historicas", total_historicas > 0)
        self.metadata.setdefault("fecha_extraccion", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        self.metadata["total_actuaciones"] = total_actuaciones
        self.metadata["total_actuales"] = total_actuales
        self.metadata["total_historicas"] = total_historicas
        self.metadata["Cantidad de Actuaciones Obtenidas"] = total_actuaciones
        self.metadata["total_archivos_con_enlace"] = total_con
        self.metadata["Cantidad de Archivos Descargados"] = total_descargados
        self.metadata["descargas_pendientes"] = pendientes

        actuales = [act for act in self.actuaciones if act.es_actual]
        if actuales:
            self.metadata["ultimo_hash_actual"] = actuales[0].hash
            self.metadata["ultima_fecha_actual"] = actuales[0].fecha
        else:
            self.metadata["ultimo_hash_actual"] = None
            self.metadata["ultima_fecha_actual"] = None

    def exportar_actuaciones(self) -> List[Dict[str, Any]]:
        """Devuelve las actuaciones como diccionarios listos para serializar."""

        return [act.to_dict() for act in self.actuaciones]


def cargar_expediente_actuaciones(ruta: str | Path) -> ActuacionesExpediente:
    """Carga un expediente desde disco y devuelve la estructura tipada correspondiente."""

    return ActuacionesExpediente.cargar_desde_archivo(ruta)


__all__ = [
    "Actuacion",
    "ActuacionesExpediente",
    "cargar_expediente_actuaciones",
    "VERSIONES_COMPATIBLES",
]
