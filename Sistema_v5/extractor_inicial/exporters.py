"""Exportadores de listados de expedientes a diferentes formatos.

Este módulo provee funciones para exportar listados de expedientes
a formatos JSON, CSV y (futuro) Excel, facilitando el análisis y
filtrado con herramientas externas.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

from ..pjn.models.expediente import ExpedienteResumen


def exportar_json(
    expedientes: Sequence[ExpedienteResumen],
    path: Path,
    *,
    incluir_metadata: bool = True,
    indent: int = 2,
) -> None:
    """Exporta expedientes a formato JSON.

    Args:
        expedientes: Secuencia de expedientes a exportar
        path: Ruta del archivo JSON de salida
        incluir_metadata: Si True, incluye metadata (timestamp, total, etc.)
        indent: Espacios de indentación (2 por defecto para legibilidad)

    Example:
        >>> expedientes = [...]
        >>> exportar_json(expedientes, Path("expedientes.json"))
    """
    expedientes_list = list(expedientes)

    if incluir_metadata:
        payload: dict[str, Any] = {
            "metadata": {
                "version": "2.0",
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "total_expedientes": len(expedientes_list),
            },
            "expedientes": [exp.to_dict() for exp in expedientes_list],
        }
    else:
        payload = [exp.to_dict() for exp in expedientes_list]

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=indent, ensure_ascii=False),
        encoding="utf-8",
    )


def exportar_csv(
    expedientes: Sequence[ExpedienteResumen],
    path: Path,
    *,
    incluir_header: bool = True,
    delimiter: str = ",",
    campos_personalizados: list[str] | None = None,
) -> None:
    """Exporta expedientes a formato CSV.

    Args:
        expedientes: Secuencia de expedientes a exportar
        path: Ruta del archivo CSV de salida
        incluir_header: Si True, incluye fila de encabezados
        delimiter: Delimitador a usar (coma por defecto)
        campos_personalizados: Lista de nombres de campos a exportar.
            Si None, exporta todos los campos estándar.

    Example:
        >>> expedientes = [...]
        >>> exportar_csv(expedientes, Path("expedientes.csv"))
        >>> # Con campos personalizados:
        >>> exportar_csv(
        ...     expedientes,
        ...     Path("expedientes_simple.csv"),
        ...     campos_personalizados=["numero", "situacion"]
        ... )
    """
    expedientes_list = list(expedientes)

    if not expedientes_list:
        # Crear archivo vacío con header
        path.parent.mkdir(parents=True, exist_ok=True)
        if incluir_header:
            path.write_text("numero,dependencia,caratula,situacion,ultima_actuacion\n", encoding="utf-8")
        else:
            path.touch()
        return

    # Determinar campos a exportar
    if campos_personalizados:
        fieldnames = campos_personalizados
    else:
        fieldnames = ["numero", "dependencia", "caratula", "situacion", "ultima_actuacion"]

    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=fieldnames,
            delimiter=delimiter,
            extrasaction="ignore",  # Ignorar campos extra
        )

        if incluir_header:
            writer.writeheader()

        for exp in expedientes_list:
            row_data = exp.to_dict()
            # Reemplazar None con strings vacíos para mejor compatibilidad
            row_data = {k: (v if v is not None else "") for k, v in row_data.items()}
            writer.writerow(row_data)


def cargar_json(path: Path) -> tuple[list[ExpedienteResumen], dict[str, Any]]:
    """Carga expedientes desde un archivo JSON exportado.

    Args:
        path: Ruta del archivo JSON a cargar

    Returns:
        Tupla con: (lista de expedientes, metadata del archivo)

    Raises:
        FileNotFoundError: Si el archivo no existe
        json.JSONDecodeError: Si el JSON es inválido
        KeyError: Si faltan campos obligatorios

    Example:
        >>> expedientes, metadata = cargar_json(Path("expedientes.json"))
        >>> print(f"Cargados {len(expedientes)} expedientes")
        >>> print(f"Fecha extracción: {metadata['timestamp']}")
    """
    contenido = json.loads(path.read_text(encoding="utf-8"))

    # Soportar formato con/sin metadata
    if isinstance(contenido, dict) and "expedientes" in contenido:
        expedientes_data = contenido["expedientes"]
        metadata = contenido.get("metadata", {})
    else:
        # Asumir que el JSON es directamente la lista
        expedientes_data = contenido
        metadata = {}

    expedientes = [
        ExpedienteResumen.from_dict(exp_dict)
        for exp_dict in expedientes_data
    ]

    return expedientes, metadata


def cargar_csv(path: Path, *, delimiter: str = ",") -> list[ExpedienteResumen]:
    """Carga expedientes desde un archivo CSV.

    Args:
        path: Ruta del archivo CSV a cargar
        delimiter: Delimitador usado en el CSV

    Returns:
        Lista de expedientes cargados

    Raises:
        FileNotFoundError: Si el archivo no existe

    Example:
        >>> expedientes = cargar_csv(Path("expedientes.csv"))
        >>> print(f"Cargados {len(expedientes)} expedientes")
    """
    expedientes: list[ExpedienteResumen] = []

    with open(path, "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=delimiter)

        for row in reader:
            # Convertir strings vacíos a None
            row_cleaned = {
                k: (v if v.strip() else None)
                for k, v in row.items()
            }
            expedientes.append(ExpedienteResumen.from_dict(row_cleaned))

    return expedientes


def exportar_excel(
    expedientes: Sequence[ExpedienteResumen],
    path: Path,
    *,
    incluir_metadata: bool = True,
    nombre_hoja: str = "Expedientes",
) -> None:
    """Exporta expedientes a formato Excel (XLSX).

    **Nota:** Requiere la biblioteca `openpyxl` instalada.

    Args:
        expedientes: Secuencia de expedientes a exportar
        path: Ruta del archivo Excel de salida
        incluir_metadata: Si True, crea hoja adicional con metadata
        nombre_hoja: Nombre de la hoja principal

    Raises:
        ImportError: Si openpyxl no está instalado

    Example:
        >>> expedientes = [...]
        >>> exportar_excel(expedientes, Path("expedientes.xlsx"))
    """
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill
    except ImportError as exc:
        raise ImportError(
            "La exportación a Excel requiere 'openpyxl'. "
            "Instálalo con: pip install openpyxl"
        ) from exc

    expedientes_list = list(expedientes)

    wb = Workbook()
    ws = wb.active
    ws.title = nombre_hoja

    # Encabezados con formato
    headers = ["Número", "Dependencia", "Carátula", "Situación", "Última Actuación"]
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="CCE5FF", end_color="CCE5FF", fill_type="solid")

    # Datos
    for row_num, exp in enumerate(expedientes_list, 2):
        ws.cell(row=row_num, column=1, value=exp.numero)
        ws.cell(row=row_num, column=2, value=exp.dependencia)
        ws.cell(row=row_num, column=3, value=exp.caratula)
        ws.cell(row=row_num, column=4, value=exp.situacion or "")
        ws.cell(row=row_num, column=5, value=exp.ultima_actuacion or "")

    # Ajustar anchos de columna
    ws.column_dimensions["A"].width = 20
    ws.column_dimensions["B"].width = 30
    ws.column_dimensions["C"].width = 50
    ws.column_dimensions["D"].width = 20
    ws.column_dimensions["E"].width = 18

    # Hoja de metadata (opcional)
    if incluir_metadata:
        ws_meta = wb.create_sheet("Metadata")
        metadata = [
            ("Timestamp", datetime.now().isoformat(timespec="seconds")),
            ("Total Expedientes", len(expedientes_list)),
            ("Versión", "2.0"),
        ]
        for row_num, (key, value) in enumerate(metadata, 1):
            ws_meta.cell(row=row_num, column=1, value=key).font = Font(bold=True)
            ws_meta.cell(row=row_num, column=2, value=str(value))

    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


__all__ = [
    "exportar_json",
    "exportar_csv",
    "exportar_excel",
    "cargar_json",
    "cargar_csv",
]
