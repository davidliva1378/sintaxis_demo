"""Herramientas para comparar expedientes extraídos con la base histórica."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

try:
    from core.gestion_expedientes.comparar_expedientes_monitor import (
        comparar_expedientes_monitor,
    )
except ImportError:  # pragma: no cover - compatibilidad con versiones anteriores
    from Sistema_v3.gestion_expedientes.comparar_expedientes_monitor import (  # type: ignore[import-not-found]
        comparar_expedientes_monitor,
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

    @property
    def total_cambios(self) -> int:
        return len(self.nuevos) + len(self.modificados) + len(self.eliminados)

    def mensajes_faltantes(self) -> Iterable[str]:
        """Devuelve mensajes legibles para cada recurso que falte."""

        return [f"No se encontró: {detalle}" for detalle in self.faltantes]


def obtener_rutas(base_dir: Path | None = None) -> RutasComparacion:
    """Resuelve las rutas estándar utilizadas por el monitor."""

    base = Path(base_dir) if base_dir is not None else Path.cwd() / "datos_extraidos" / "monitoreo"
    return RutasComparacion(
        archivo_actual=base / "expedientes_monitor.json",
        archivo_base=base / "expedientes_monitor - base.json",
        carpeta_reportes=base / "reportes",
    )


def comparar_expedientes(base_dir: Path | None = None) -> ResultadoComparacion:
    """Ejecuta la comparación y captura errores habituales."""

    rutas = obtener_rutas(base_dir)

    faltantes: list[str] = []
    if not rutas.archivo_actual.exists():
        faltantes.append(str(rutas.archivo_actual))
    if not rutas.archivo_base.exists():
        faltantes.append(str(rutas.archivo_base))

    if faltantes:
        return ResultadoComparacion([], [], [], None, faltantes=faltantes)

    rutas.carpeta_reportes.mkdir(parents=True, exist_ok=True)

    try:
        nuevos, modificados, eliminados = comparar_expedientes_monitor(
            str(rutas.archivo_actual),
            str(rutas.archivo_base),
            str(rutas.carpeta_reportes),
        )
    except Exception as exc:  # pragma: no cover - dependencias externas
        return ResultadoComparacion([], [], [], None, excepcion=exc)

    informe = None
    if (nuevos or modificados or eliminados) and rutas.carpeta_reportes.exists():
        informe = max(
            rutas.carpeta_reportes.glob("comparacion_*.json"),
            default=None,
            key=lambda ruta: ruta.stat().st_mtime,
        )

    return ResultadoComparacion(nuevos, modificados, eliminados, informe)
