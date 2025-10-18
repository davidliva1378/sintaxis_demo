"""Agenda jurídica y utilidades de plazos para Sistema_v5.

El objetivo del módulo es centralizar la gestión de actividades
relacionadas con expedientes: vencimientos, audiencias, tareas,
recordatorios y cualquier otra actividad personalizada definida por el
usuario. El módulo está orientado a composición funcional, provee un
servicio sencillo para integrar con el resto del sistema y cuenta con
utilidades de fechas para calcular plazos en días hábiles y corridos.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, MutableSequence, Sequence
from uuid import uuid4

CategoriaAgenda = str

_NO_CAMBIO = object()

# Categorías sugeridas para uso inmediato dentro del sistema. El usuario
# puede agregar más a través del servicio expuesto.
CATEGORIAS_BASE: set[CategoriaAgenda] = {
    "vencimiento",
    "tarea",
    "nota",
    "audiencia",
    "recordatorio",
    "reunion",
    "presentacion",
    "consulta",
}


@dataclass(slots=True, frozen=True)
class AgendaItem:
    """Representa un elemento dentro de la agenda."""

    id: str
    tipo: CategoriaAgenda
    titulo: str
    fecha_inicio: date
    fecha_vencimiento: date
    descripcion: str | None = None
    etiquetas: tuple[str, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] | None = None

    def dias_restantes(self, referencia: date | None = None) -> int:
        """Calcula los días corridos restantes hasta la fecha de vencimiento."""

        referencia = referencia or date.today()
        return (self.fecha_vencimiento - referencia).days

    def esta_vencido(self, referencia: date | None = None) -> bool:
        """Indica si el elemento está vencido respecto a la fecha de referencia."""

        referencia = referencia or date.today()
        return self.fecha_vencimiento < referencia


@dataclass(slots=True)
class AgendaQuery:
    """Filtro sencillo para consultar la agenda desde otros módulos."""

    tipos: tuple[CategoriaAgenda, ...] | None = None
    desde: date | None = None
    hasta: date | None = None
    etiquetas: tuple[str, ...] | None = None
    texto: str | None = None


class AgendaRepository:
    """Repositorio en memoria para almacenar elementos de agenda."""

    def __init__(self) -> None:
        self._items: dict[str, AgendaItem] = {}

    def add(self, item: AgendaItem) -> None:
        if item.id in self._items:
            raise ValueError(f"Ya existe un ítem con id '{item.id}'")
        self._items[item.id] = item

    def update(self, item: AgendaItem) -> None:
        if item.id not in self._items:
            raise KeyError(f"El ítem '{item.id}' no existe y no puede actualizarse")
        self._items[item.id] = item

    def get(self, item_id: str) -> AgendaItem | None:
        return self._items.get(item_id)

    def remove(self, item_id: str) -> None:
        self._items.pop(item_id, None)

    def all(self) -> tuple[AgendaItem, ...]:
        return tuple(self._items.values())

    def filter(self, query: AgendaQuery) -> tuple[AgendaItem, ...]:
        resultados: MutableSequence[AgendaItem] = []
        for item in self._items.values():
            if query.tipos and item.tipo not in query.tipos:
                continue
            if query.desde and item.fecha_inicio < query.desde:
                continue
            if query.hasta and item.fecha_vencimiento > query.hasta:
                continue
            if query.etiquetas and not set(query.etiquetas).issubset(item.etiquetas):
                continue
            if query.texto:
                texto = query.texto.lower()
                if texto not in item.titulo.lower() and texto not in (
                    item.descripcion or ""
                ).lower():
                    continue
            resultados.append(item)
        return tuple(resultados)

    def __iter__(self) -> Iterator[AgendaItem]:
        yield from self._items.values()


def _item_to_dict(item: AgendaItem) -> dict[str, Any]:
    return {
        "id": item.id,
        "tipo": item.tipo,
        "titulo": item.titulo,
        "fecha_inicio": item.fecha_inicio.isoformat(),
        "fecha_vencimiento": item.fecha_vencimiento.isoformat(),
        "descripcion": item.descripcion,
        "etiquetas": list(item.etiquetas),
        "metadata": dict(item.metadata) if item.metadata is not None else None,
    }


def _item_from_dict(data: Mapping[str, Any]) -> AgendaItem:
    metadata = data.get("metadata")
    if metadata is not None and not isinstance(metadata, Mapping):
        raise ValueError("El campo 'metadata' debe ser un objeto JSON")
    return AgendaItem(
        id=str(data["id"]),
        tipo=str(data["tipo"]),
        titulo=str(data["titulo"]),
        fecha_inicio=date.fromisoformat(str(data["fecha_inicio"])),
        fecha_vencimiento=date.fromisoformat(str(data["fecha_vencimiento"])),
        descripcion=data.get("descripcion") or None,
        etiquetas=tuple(str(valor) for valor in (data.get("etiquetas", []) or ())),
        metadata=dict(metadata) if metadata is not None else None,
    )


def _json_default(value: Any) -> Any:
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, timedelta):
        return value.total_seconds()
    return str(value)


def _normalizar_etiquetas(etiquetas: Sequence[str] | None) -> tuple[str, ...]:
    if not etiquetas:
        return ()
    normalizadas = {etiqueta.strip().lower() for etiqueta in etiquetas if etiqueta and etiqueta.strip()}
    return tuple(sorted(normalizadas))


class JSONAgendaRepository(AgendaRepository):
    """Repositorio respaldado por un archivo JSON para simular persistencia."""

    def __init__(self, archivo: str | Path, *, auto_flush: bool = True) -> None:
        super().__init__()
        self._ruta = Path(archivo)
        self._auto_flush = auto_flush
        self._ruta.parent.mkdir(parents=True, exist_ok=True)
        self._cargar_desde_disco()

    def add(self, item: AgendaItem) -> None:  # type: ignore[override]
        super().add(item)
        if self._auto_flush:
            self.flush()

    def remove(self, item_id: str) -> None:  # type: ignore[override]
        super().remove(item_id)
        if self._auto_flush:
            self.flush()

    def update(self, item: AgendaItem) -> None:  # type: ignore[override]
        super().update(item)
        if self._auto_flush:
            self.flush()

    def flush(self) -> None:
        """Guarda el estado actual en el archivo JSON."""

        datos = [_item_to_dict(item) for item in self._items.values()]
        temporal = self._ruta.parent / f"{self._ruta.name}.tmp"
        with temporal.open("w", encoding="utf-8") as salida:
            json.dump(datos, salida, ensure_ascii=False, indent=2, default=_json_default)
        temporal.replace(self._ruta)

    def _cargar_desde_disco(self) -> None:
        if not self._ruta.exists():
            return
        try:
            contenido = self._ruta.read_text(encoding="utf-8")
            if not contenido.strip():
                return
            datos = json.loads(contenido)
        except FileNotFoundError:
            return
        except JSONDecodeError as exc:  # pragma: no cover - error crítico
            raise ValueError(
                f"El archivo de agenda JSON está corrupto: {self._ruta}"
            ) from exc

        if not isinstance(datos, list):
            raise ValueError(
                "El archivo de agenda JSON debe contener una lista de elementos"
            )

        self._items = {}
        for registro in datos:
            if not isinstance(registro, Mapping):
                raise ValueError(
                    "Cada elemento del archivo de agenda debe ser un objeto JSON"
                )
            item = _item_from_dict(registro)
            if item.id in self._items:
                raise ValueError(
                    f"El archivo contiene IDs duplicados: '{item.id}'"
                )
            self._items[item.id] = item


class AgendaService:
    """Servicio principal para interactuar con la agenda."""

    def __init__(
        self,
        repository: AgendaRepository | None = None,
        *,
        feriados: Iterable[date] | None = None,
        categorias: Iterable[CategoriaAgenda] | None = None,
    ) -> None:
        self._repository = repository or AgendaRepository()
        self._feriados: set[date] = set(feriados or [])
        self._categorias: set[CategoriaAgenda] = set(categorias or CATEGORIAS_BASE)

    # ------------------------------------------------------------------
    # Gestión de categorías
    # ------------------------------------------------------------------
    def agregar_categoria(self, categoria: CategoriaAgenda) -> None:
        """Registra una nueva categoría disponible para la agenda."""

        categoria_normalizada = categoria.strip().lower()
        if not categoria_normalizada:
            raise ValueError("La categoría no puede estar vacía")
        self._categorias.add(categoria_normalizada)

    def categorias_disponibles(self) -> tuple[CategoriaAgenda, ...]:
        """Devuelve las categorías disponibles para registrar eventos."""

        return tuple(sorted(self._categorias))

    def eliminar_categoria(self, categoria: CategoriaAgenda) -> None:
        """Permite retirar una categoría personalizada."""

        categoria_normalizada = categoria.strip().lower()
        if categoria_normalizada in CATEGORIAS_BASE:
            raise ValueError("No se pueden eliminar las categorías base del sistema")
        self._categorias.discard(categoria_normalizada)

    # ------------------------------------------------------------------
    # Gestión de feriados
    # ------------------------------------------------------------------
    def sincronizar_feriados(self, feriados: Iterable[date]) -> None:
        """Reemplaza la lista actual de feriados por la colección indicada."""

        self._feriados = set(feriados)

    def agregar_feriados(self, feriados: Iterable[date]) -> None:
        """Agrega varios feriados al calendario en memoria."""

        self._feriados.update(feriados)

    def agregar_feriado(self, feriado: date) -> None:
        """Agrega un único feriado al calendario."""

        self._feriados.add(feriado)

    def quitar_feriado(self, feriado: date) -> None:
        """Elimina un feriado del calendario, si existe."""

        self._feriados.discard(feriado)

    def listar_feriados(self) -> tuple[date, ...]:
        """Devuelve los feriados registrados ordenados cronológicamente."""

        return tuple(sorted(self._feriados))

    # ------------------------------------------------------------------
    # Gestión de ítems
    # ------------------------------------------------------------------
    def registrar_item(
        self,
        *,
        tipo: CategoriaAgenda,
        titulo: str,
        fecha_inicio: date,
        fecha_vencimiento: date | None = None,
        descripcion: str | None = None,
        etiquetas: Sequence[str] | None = None,
        metadata: Mapping[str, Any] | None = None,
        identificador: str | None = None,
    ) -> AgendaItem:
        """Registra un ítem en la agenda con validaciones básicas."""

        tipo_normalizado = tipo.strip().lower()
        if tipo_normalizado not in self._categorias:
            raise ValueError(
                f"La categoría '{tipo}' no está registrada. "
                "Use 'agregar_categoria' para habilitarla."
            )
        if not titulo.strip():
            raise ValueError("El título es obligatorio")

        fecha_vencimiento = fecha_vencimiento or fecha_inicio
        if fecha_vencimiento < fecha_inicio:
            raise ValueError("La fecha de vencimiento no puede ser anterior al inicio")

        if metadata is not None and not isinstance(metadata, Mapping):
            raise TypeError("metadata debe ser un mapeo (dict, Mapping)")

        item = AgendaItem(
            id=_resolver_identificador(identificador, fecha_inicio, titulo, tipo_normalizado),
            tipo=tipo_normalizado,
            titulo=titulo.strip(),
            fecha_inicio=fecha_inicio,
            fecha_vencimiento=fecha_vencimiento,
            descripcion=descripcion.strip() if descripcion else None,
            etiquetas=_normalizar_etiquetas(etiquetas),
            metadata=dict(metadata) if metadata is not None else None,
        )
        self._repository.add(item)
        return item

    def registrar_vencimiento(
        self,
        *,
        titulo: str,
        fecha_inicio: date,
        dias: int,
        tipo_plazo: str = "habiles",
        descripcion: str | None = None,
        etiquetas: Sequence[str] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> AgendaItem:
        """Atajo para registrar vencimientos calculando la fecha automáticamente."""

        fecha_vencimiento = calcular_fecha_plazo(
            fecha_inicio,
            dias,
            tipo_plazo,
            feriados=self._feriados,
        )
        return self.registrar_item(
            tipo="vencimiento",
            titulo=titulo,
            fecha_inicio=fecha_inicio,
            fecha_vencimiento=fecha_vencimiento,
            descripcion=descripcion,
            etiquetas=etiquetas,
            metadata=metadata,
        )

    def registrar_audiencia(
        self,
        *,
        titulo: str,
        fecha: date,
        descripcion: str | None = None,
        etiquetas: Sequence[str] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> AgendaItem:
        return self.registrar_item(
            tipo="audiencia",
            titulo=titulo,
            fecha_inicio=fecha,
            fecha_vencimiento=fecha,
            descripcion=descripcion,
            etiquetas=etiquetas,
            metadata=metadata,
        )

    def registrar_tarea(
        self,
        *,
        titulo: str,
        fecha_inicio: date,
        fecha_vencimiento: date | None = None,
        descripcion: str | None = None,
        etiquetas: Sequence[str] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> AgendaItem:
        return self.registrar_item(
            tipo="tarea",
            titulo=titulo,
            fecha_inicio=fecha_inicio,
            fecha_vencimiento=fecha_vencimiento,
            descripcion=descripcion,
            etiquetas=etiquetas,
            metadata=metadata,
        )

    def registrar_nota(
        self,
        *,
        titulo: str,
        fecha: date,
        descripcion: str | None = None,
        etiquetas: Sequence[str] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> AgendaItem:
        return self.registrar_item(
            tipo="nota",
            titulo=titulo,
            fecha_inicio=fecha,
            fecha_vencimiento=fecha,
            descripcion=descripcion,
            etiquetas=etiquetas,
            metadata=metadata,
        )

    def registrar_recordatorio(
        self,
        *,
        titulo: str,
        fecha: date,
        descripcion: str | None = None,
        etiquetas: Sequence[str] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> AgendaItem:
        return self.registrar_item(
            tipo="recordatorio",
            titulo=titulo,
            fecha_inicio=fecha,
            fecha_vencimiento=fecha,
            descripcion=descripcion,
            etiquetas=etiquetas,
            metadata=metadata,
        )

    def obtener(self, item_id: str) -> AgendaItem | None:
        return self._repository.get(item_id)

    def listar(self) -> tuple[AgendaItem, ...]:
        return self._repository.all()

    def buscar(self, query: AgendaQuery) -> tuple[AgendaItem, ...]:
        return self._repository.filter(query)

    def eliminar(self, item_id: str) -> None:
        self._repository.remove(item_id)

    def actualizar_item(
        self,
        item_id: str,
        *,
        tipo: CategoriaAgenda | None = None,
        titulo: str | None = None,
        fecha_inicio: date | None = None,
        fecha_vencimiento: date | None = None,
        descripcion: str | None | object = _NO_CAMBIO,
        etiquetas: Sequence[str] | None | object = _NO_CAMBIO,
        metadata: Mapping[str, Any] | None | object = _NO_CAMBIO,
    ) -> AgendaItem:
        """Actualiza un ítem existente aplicando las mismas validaciones básicas."""

        original = self._repository.get(item_id)
        if original is None:
            raise KeyError(f"No existe un ítem con id '{item_id}'")

        nuevo_tipo = original.tipo if tipo is None else tipo.strip().lower()
        if nuevo_tipo not in self._categorias:
            raise ValueError(
                f"La categoría '{nuevo_tipo}' no está registrada. Use 'agregar_categoria' para habilitarla."
            )

        nuevo_titulo = original.titulo if titulo is None else titulo.strip()
        if not nuevo_titulo:
            raise ValueError("El título es obligatorio")

        nuevo_inicio = original.fecha_inicio if fecha_inicio is None else fecha_inicio
        nuevo_vencimiento = (
            original.fecha_vencimiento if fecha_vencimiento is None else fecha_vencimiento
        )
        if nuevo_vencimiento < nuevo_inicio:
            raise ValueError("La fecha de vencimiento no puede ser anterior al inicio")

        if metadata is _NO_CAMBIO:
            nuevo_metadata = original.metadata
        else:
            if metadata is not None and not isinstance(metadata, Mapping):
                raise TypeError("metadata debe ser un mapeo (dict, Mapping)")
            nuevo_metadata = dict(metadata) if metadata is not None else None

        if descripcion is _NO_CAMBIO:
            nueva_descripcion = original.descripcion
        else:
            nueva_descripcion = descripcion.strip() if descripcion else None

        if etiquetas is _NO_CAMBIO:
            nuevas_etiquetas = original.etiquetas
        else:
            nuevas_etiquetas = _normalizar_etiquetas(etiquetas)

        actualizado = replace(
            original,
            tipo=nuevo_tipo,
            titulo=nuevo_titulo,
            fecha_inicio=nuevo_inicio,
            fecha_vencimiento=nuevo_vencimiento,
            descripcion=nueva_descripcion,
            etiquetas=nuevas_etiquetas,
            metadata=nuevo_metadata,
        )

        self._repository.update(actualizado)
        return actualizado

    # ------------------------------------------------------------------
    # Utilidades de fechas expuestas a otros módulos
    # ------------------------------------------------------------------
    def contar_dias_habiles(self, inicio: date, fin: date) -> int:
        return contar_dias_habiles(inicio, fin, feriados=self._feriados)

    def contar_dias_corridos(self, inicio: date, fin: date) -> int:
        return contar_dias_corridos(inicio, fin)

    def calcular_fecha_plazo(
        self,
        fecha_inicio: date,
        dias: int,
        tipo_plazo: str = "habiles",
    ) -> date:
        return calcular_fecha_plazo(fecha_inicio, dias, tipo_plazo, feriados=self._feriados)


def _resolver_identificador(
    identificador: str | None, fecha: date, titulo: str, tipo: str
) -> str:
    if identificador is not None:
        limpio = identificador.strip()
        if not limpio:
            raise ValueError("El identificador no puede estar vacío")
        return limpio
    return _generar_identificador(fecha, titulo, tipo)


def _generar_identificador(fecha: date, titulo: str, tipo: str) -> str:
    base = f"{fecha.isoformat()}-{tipo}-{titulo}".lower().replace(" ", "-")
    sufijo = uuid4().hex[:8]
    return f"{base}-{sufijo}"


# ----------------------------------------------------------------------
# Utilidades de fechas
# ----------------------------------------------------------------------

def es_dia_habil(dia: date, feriados: set[date]) -> bool:
    return dia.weekday() < 5 and dia not in feriados


def calcular_fecha_plazo(
    fecha_inicio: date,
    dias: int,
    tipo_plazo: str = "habiles",
    *,
    feriados: Iterable[date] | None = None,
) -> date:
    """Calcula la fecha de vencimiento desde una fecha inicial.

    Args:
        fecha_inicio: Fecha desde la que se computa el plazo.
        dias: Cantidad de días a sumar.
        tipo_plazo: "habiles" o "corridos".
        feriados: Colección de feriados considerados inhábiles.

    El cómputo excluye el día inicial y suma días completos hasta
    alcanzar el plazo indicado.
    """

    if dias < 0:
        raise ValueError("La cantidad de días no puede ser negativa")

    tipo_normalizado = tipo_plazo.lower()
    feriados_set = set(feriados or [])

    if dias == 0:
        return fecha_inicio

    actual = fecha_inicio
    acumulados = 0
    while acumulados < dias:
        actual += timedelta(days=1)
        if tipo_normalizado == "habiles":
            if es_dia_habil(actual, feriados_set):
                acumulados += 1
        elif tipo_normalizado == "corridos":
            acumulados += 1
        else:
            raise ValueError("tipo_plazo debe ser 'habiles' o 'corridos'")
    return actual


def dias_habiles_entre(
    inicio: date,
    fin: date,
    *,
    feriados: Iterable[date] | None = None,
) -> int:
    """Calcula la cantidad de días hábiles entre dos fechas inclusive."""

    return contar_dias_habiles(inicio, fin, feriados=feriados)


def dias_corridos_entre(inicio: date, fin: date) -> int:
    """Calcula la cantidad de días corridos entre dos fechas inclusive."""

    return contar_dias_corridos(inicio, fin)


def contar_dias_habiles(
    inicio: date,
    fin: date,
    *,
    feriados: Iterable[date] | None = None,
) -> int:
    """Cuenta la cantidad de días hábiles entre dos fechas inclusive."""

    if fin < inicio:
        raise ValueError("La fecha final no puede ser anterior a la inicial")

    feriados_set = set(feriados or [])
    contador = 0
    actual = inicio
    while actual <= fin:
        if es_dia_habil(actual, feriados_set):
            contador += 1
        actual += timedelta(days=1)
    return contador


def contar_dias_corridos(inicio: date, fin: date) -> int:
    """Cuenta la cantidad de días corridos entre dos fechas inclusive."""

    if fin < inicio:
        raise ValueError("La fecha final no puede ser anterior a la inicial")
    return (fin - inicio).days + 1


# ----------------------------------------------------------------------
# Helpers para agenda global compartida
# ----------------------------------------------------------------------

_AGENDA_GLOBAL: AgendaService | None = None


def crear_agenda_default(
    *,
    feriados: Iterable[date] | None = None,
    repository: AgendaRepository | None = None,
    categorias: Iterable[CategoriaAgenda] | None = None,
) -> AgendaService:
    """Crea un servicio de agenda listo para usar con opciones personalizadas."""

    return AgendaService(
        repository=repository,
        feriados=feriados,
        categorias=categorias,
    )


def obtener_agenda_global() -> AgendaService:
    """Devuelve una instancia única compartida para todo el sistema."""

    global _AGENDA_GLOBAL
    if _AGENDA_GLOBAL is None:
        _AGENDA_GLOBAL = AgendaService()
    return _AGENDA_GLOBAL


def registrar_vencimiento(**kwargs: Any) -> AgendaItem:
    """Atajo para registrar vencimientos en la agenda global."""

    return obtener_agenda_global().registrar_vencimiento(**kwargs)


def registrar_tarea(**kwargs: Any) -> AgendaItem:
    """Atajo para registrar tareas en la agenda global."""

    return obtener_agenda_global().registrar_tarea(**kwargs)


def registrar_audiencia(**kwargs: Any) -> AgendaItem:
    """Atajo para registrar audiencias en la agenda global."""

    return obtener_agenda_global().registrar_audiencia(**kwargs)


def registrar_nota(**kwargs: Any) -> AgendaItem:
    """Atajo para registrar notas en la agenda global."""

    return obtener_agenda_global().registrar_nota(**kwargs)


def registrar_recordatorio(**kwargs: Any) -> AgendaItem:
    """Atajo para registrar recordatorios en la agenda global."""

    return obtener_agenda_global().registrar_recordatorio(**kwargs)
