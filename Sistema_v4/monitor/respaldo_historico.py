"""Herramientas para generar respaldos con sello temporal de los resultados."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

ARCHIVOS_PREDETERMINADOS: tuple[str, ...] = (
    "expedientes_monitor.json",
    "historial_notificaciones.json",
    "historial_notificaciones.csv",
)


@dataclass
class ResultadoRespaldo:
    """Representa el resultado de ejecutar un respaldo histórico."""

    destino: Path
    copiados: list[Path]
    omitidos: list[tuple[Path, str]]


def _normalizar_archivos(archivos: Iterable[str | Path] | None) -> list[Path]:
    if not archivos:
        return [Path(nombre) for nombre in ARCHIVOS_PREDETERMINADOS]
    resultado: list[Path] = []
    for elemento in archivos:
        ruta = Path(elemento)
        if ruta.name:
            resultado.append(Path(ruta))
    return resultado


def generar_respaldo_monitoreo(
    origen: Path,
    destino_base: Path,
    archivos: Iterable[str | Path] | None = None,
) -> ResultadoRespaldo:
    """Copia los archivos solicitados dentro de una carpeta con timestamp."""

    origen = origen.expanduser().resolve()
    destino_base = destino_base.expanduser().resolve()
    archivos_respaldo = _normalizar_archivos(archivos)

    if not archivos_respaldo:
        raise ValueError("No se recibieron archivos para respaldar.")

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    destino = destino_base / timestamp
    destino.mkdir(parents=True, exist_ok=True)

    copiados: list[Path] = []
    omitidos: list[tuple[Path, str]] = []

    for relativo in archivos_respaldo:
        origen_archivo = origen / relativo
        destino_archivo = destino / relativo.name
        try:
            if not origen_archivo.exists():
                omitidos.append((origen_archivo, "no_encontrado"))
                continue
            shutil.copy2(origen_archivo, destino_archivo)
            copiados.append(destino_archivo)
        except Exception as error:  # pragma: no cover - logging desde el monitor
            omitidos.append((origen_archivo, str(error)))

    return ResultadoRespaldo(destino=destino, copiados=copiados, omitidos=omitidos)


__all__ = [
    "ARCHIVOS_PREDETERMINADOS",
    "ResultadoRespaldo",
    "generar_respaldo_monitoreo",
]
