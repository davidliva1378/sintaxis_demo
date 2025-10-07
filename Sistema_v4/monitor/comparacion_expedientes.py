"""Herramientas para comparar expedientes extraídos con la base histórica."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

try:
    from core.gestion_expedientes.comparar_expedientes import comparar_con_base
    from core.gestion_expedientes.guardar_comparacion import (
        guardar_comparacion_json,
    )
except ImportError:  # pragma: no cover - compatibilidad con versiones anteriores
    comparar_con_base = None  # type: ignore[assignment]
    guardar_comparacion_json = None  # type: ignore[assignment]

try:
    from .configuracion_modo import cargar_config_monitor, obtener_fecha_corte
except ImportError:  # pragma: no cover - ejecución directa
    try:  # type: ignore[no-redef]
        from configuracion_modo import (  # type: ignore[import-not-found]
            cargar_config_monitor,
            obtener_fecha_corte,
        )
    except ImportError:  # pragma: no cover - helper opcional
        obtener_fecha_corte = None  # type: ignore[assignment]
        cargar_config_monitor = None  # type: ignore[assignment]


MODO_COMPARACION_PARCIAL = "parcial"
MODO_COMPARACION_TOTAL = "total"
MODOS_COMPARACION_VALIDOS: tuple[str, ...] = (
    MODO_COMPARACION_PARCIAL,
    MODO_COMPARACION_TOTAL,
)


@dataclass(frozen=True)
class RutasComparacion:
    """Ubicaciones necesarias para ejecutar la comparación."""

    archivo_actual: Path
    archivo_base: Path
    carpeta_reportes: Path


@dataclass
class ResultadoComparacion:
    """Resultado estructurado de la comparación de expedientes."""

    nuevos: list
    modificados: list
    eliminados: list
    informe: Path | None = None
    faltantes: list[str] = field(default_factory=list)
    excepcion: Exception | None = None
    avisos: list[str] = field(default_factory=list)

    @property
    def total_cambios(self) -> int:
        return len(self.nuevos) + len(self.modificados) + len(self.eliminados)

    def mensajes_faltantes(self) -> Iterable[str]:
        """Devuelve mensajes legibles para cada recurso que falte."""

        return [f"No se encontró: {detalle}" for detalle in self.faltantes]


def obtener_rutas(
    base_dir: Path | None = None, config: dict | None = None
) -> RutasComparacion:
    """Resuelve las rutas estándar utilizadas por el monitor."""

    base = _resolver_base_monitoreo(base_dir, config)
    return RutasComparacion(
        archivo_actual=base / "expedientes_monitor.json",
        archivo_base=base / "expedientes_monitor - base.json",
        carpeta_reportes=base / "reportes",
    )


def comparar_expedientes(
    base_dir: Path | None = None, *, config: dict | None = None
) -> ResultadoComparacion:
    """Ejecuta la comparación y captura errores habituales."""

    rutas = obtener_rutas(base_dir, config=config)

    avisos: list[str] = []
    config_resuelta = _resolver_config_general(config)
    modo_comparacion, avisos_config = _resolver_modo_comparacion(config_resuelta)
    avisos.extend(avisos_config)
    if modo_comparacion == MODO_COMPARACION_PARCIAL:
        avisos.append(
            "Modo de comparación seleccionado: parcial (filtra la base según la fecha de corte)."
        )
    else:
        avisos.append(
            "Modo de comparación seleccionado: total (se compara contra toda la base histórica)."
        )

    faltantes: list[str] = []
    if not rutas.archivo_actual.exists():
        faltantes.append(str(rutas.archivo_actual))
    if not rutas.archivo_base.exists():
        faltantes.append(str(rutas.archivo_base))

    if faltantes:
        return ResultadoComparacion(
            [], [], [], None, faltantes=faltantes, avisos=avisos
        )

    if comparar_con_base is None or guardar_comparacion_json is None:
        return ResultadoComparacion(
            [],
            [],
            [],
            None,
            excepcion=ImportError(
                "Dependencias de comparación no disponibles en esta instalación."
            ),
            avisos=avisos,
        )

    try:
        with rutas.archivo_actual.open("r", encoding="utf-8") as archivo:
            expedientes_actuales = json.load(archivo)
        with rutas.archivo_base.open("r", encoding="utf-8") as archivo:
            expedientes_base = json.load(archivo)
    except Exception as exc:  # pragma: no cover - lectura defensiva
        return ResultadoComparacion([], [], [], None, excepcion=exc, avisos=avisos)

    if not isinstance(expedientes_actuales, list) or not isinstance(
        expedientes_base, list
    ):
        return ResultadoComparacion(
            [],
            [],
            [],
            None,
            excepcion=ValueError(
                "Los archivos de expedientes deben contener listas JSON válidas."
            ),
            avisos=avisos,
        )

    fecha_corte = None
    if modo_comparacion == MODO_COMPARACION_PARCIAL:
        fecha_corte = _resolver_fecha_corte(config_resuelta)
        if fecha_corte is None:
            avisos.append(
                "No se obtuvo una fecha de corte válida; la comparación parcial usará la base completa."
            )

    if fecha_corte is not None:
        expedientes_base_filtrados = _filtrar_por_fecha(expedientes_base, fecha_corte)
        descartados = len(expedientes_base) - len(expedientes_base_filtrados)
        if descartados > 0:
            avisos.append(
                "Se ignoraron %s expedientes de la base anteriores al corte %s." % (
                    descartados,
                    fecha_corte.strftime("%Y-%m-%d"),
                )
            )
        expedientes_base = expedientes_base_filtrados

    try:
        nuevos, modificados, eliminados = comparar_con_base(
            expedientes_actuales, expedientes_base
        )
    except Exception as exc:  # pragma: no cover - manejo defensivo
        return ResultadoComparacion([], [], [], None, excepcion=exc, avisos=avisos)

    informe = None
    if nuevos or modificados or eliminados:
        rutas.carpeta_reportes.mkdir(parents=True, exist_ok=True)
        try:
            informe_path = guardar_comparacion_json(
                nuevos, modificados, eliminados, str(rutas.carpeta_reportes)
            )
        except Exception as exc:  # pragma: no cover - escritura defensiva
            avisos.append(f"No se pudo guardar el informe de comparación: {exc}")
        else:
            informe = Path(informe_path)

    return ResultadoComparacion(
        nuevos,
        modificados,
        eliminados,
        informe,
        avisos=avisos,
    )


def _resolver_config_general(config: dict | None) -> dict | None:
    """Obtiene la configuración completa si está disponible."""

    if isinstance(config, dict):
        return config

    if cargar_config_monitor is None:
        return None

    try:
        return cargar_config_monitor()
    except Exception:  # pragma: no cover - lectura defensiva
        return None


def _resolver_modo_comparacion(config: dict | None) -> tuple[str, list[str]]:
    """Determina el modo de comparación configurado y avisos asociados."""

    avisos: list[str] = []
    modo = MODO_COMPARACION_PARCIAL

    comparacion_config = None
    if isinstance(config, dict):
        comparacion_config = config.get("comparacion")

    if isinstance(comparacion_config, dict):
        modo_config = comparacion_config.get("modo")
        if isinstance(modo_config, str):
            normalizado = modo_config.strip().lower()
            if normalizado in MODOS_COMPARACION_VALIDOS:
                modo = normalizado
            elif normalizado:
                avisos.append(
                    "Modo de comparación '%s' no reconocido; se utilizará 'parcial'."
                    % modo_config
                )
        elif modo_config is not None:
            avisos.append(
                "Modo de comparación con formato inválido; se utilizará 'parcial'."
            )
    elif comparacion_config is not None:
        avisos.append(
            "Bloque de configuración 'comparacion' inválido; se utilizará 'parcial'."
        )

    return modo, avisos


def _resolver_base_monitoreo(
    base_dir: Path | None, config: dict | None
) -> Path:
    """Determina la carpeta base a utilizar para la comparación."""

    if base_dir is not None:
        return Path(base_dir)

    if isinstance(config, dict):
        rutas = config.get("rutas")
        if isinstance(rutas, dict):
            destino = rutas.get("monitoreo")
            if isinstance(destino, str) and destino.strip():
                ruta = Path(destino).expanduser()
                if not ruta.is_absolute():
                    return (Path.cwd() / ruta).resolve()
                return ruta.resolve()

    return (Path.cwd() / "datos_extraidos" / "monitoreo").resolve()


def _resolver_fecha_corte(config: dict | None = None) -> date | None:
    """Obtiene la fecha de corte configurada como objeto ``date``."""

    if obtener_fecha_corte is None:
        return None

    try:
        fecha_iso = obtener_fecha_corte(config)
    except Exception:  # pragma: no cover - helper opcional
        return None

    if not fecha_iso:
        return None

    try:
        fecha = datetime.strptime(fecha_iso, "%Y-%m-%d")
    except ValueError:
        return None

    return fecha.date()


def _filtrar_por_fecha(expedientes: list, fecha_corte: date) -> list:
    """Devuelve una nueva lista sin expedientes anteriores al corte."""

    resultado: list = []
    for expediente in expedientes:
        ultima_act = _parsear_fecha(expediente.get("ultima_actuacion"))
        if ultima_act is None or ultima_act >= fecha_corte:
            resultado.append(expediente)

    return resultado


def _parsear_fecha(valor: object) -> datetime.date | None:
    """Convierte cadenas conocidas a ``date`` para comparar filtros."""

    if not isinstance(valor, str):
        return None

    valor = valor.strip()
    if not valor:
        return None

    for formato in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(valor, formato).date()
        except ValueError:
            continue
    return None
