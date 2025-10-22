"""Servicios de alto nivel para gestionar actuaciones de un expediente.

Esta capa coordina la preparación de directorios, la extracción de
actuaciones y la descarga opcional de adjuntos, manteniendo separada la
lógica de scraping de los scripts interactivos.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, TypedDict

from Sistema_v5.gestor_directorios import GestorDirectoriosExpedientes
from Sistema_v5.pjn.scraping import normalizar_numero_expediente
from Sistema_v5.pjn.scraping.actuaciones import (
    descargar_archivos_de_json,
    extraer_actuaciones_completas,
)


class ResultadoProcesamiento(TypedDict, total=False):
    """Resumen de la ejecución de :func:`procesar_actuaciones_expediente`."""

    actuaciones_actuales: int
    actuaciones_historicas: int
    error: str | None
    carpeta_expediente: str
    carpeta_json: str | None
    carpeta_actuaciones: str | None
    carpeta_adjuntos: str | None
    descargas_ejecutadas: bool
    manifest: dict[str, Any]


async def procesar_actuaciones_expediente(
    datos_expediente: dict[str, Any],
    *,
    descargar_adjuntos: bool = False,
) -> tuple[Path | None, ResultadoProcesamiento]:
    """Extrae actuaciones completas y gestiona la descarga de adjuntos.

    La función espera que ``datos_expediente`` contenga los metadatos del
    expediente y una referencia a la página de Playwright en la clave
    ``"page"``. El diccionario puede incluir otros campos auxiliares que se
    preservarán durante la extracción.

    Args:
        datos_expediente: Información del expediente junto con la página de
            Playwright bajo la clave ``"page"``.
        descargar_adjuntos: Si es ``True`` se descarga el contenido asociado
            al JSON generado tras la extracción.

    Returns:
        tuple: Una tupla ``(ruta_json, resumen)`` donde ``ruta_json`` es la
        ruta al archivo generado (o ``None`` si no se creó) y ``resumen``
        detalla el resultado de la operación.

    Raises:
        ValueError: Si no se proporciona la página de Playwright o el número
            del expediente.
        TypeError: Si ``datos_expediente`` no es un diccionario.
    """

    if not isinstance(datos_expediente, dict):
        raise TypeError("datos_expediente debe ser un diccionario")

    page = datos_expediente.get("page")
    if page is None:
        raise ValueError(
            "datos_expediente debe incluir la clave 'page' con la instancia de Playwright"
        )

    expediente_info = {
        key: value
        for key, value in datos_expediente.items()
        if key != "page"
    }

    numero_expediente = (
        expediente_info.get("numero")
        or expediente_info.get("Numero")
        or expediente_info.get("expediente")
    )
    if not numero_expediente:
        raise ValueError("datos_expediente debe incluir el número del expediente")

    numero_normalizado = normalizar_numero_expediente(numero_expediente)

    gestor = GestorDirectoriosExpedientes.desde_config()
    carpeta_expediente, manifest = gestor.crear_para_expediente(numero_expediente)

    carpeta_json = carpeta_expediente / "json"
    carpeta_actuaciones = carpeta_expediente / "actuaciones"
    carpeta_adjuntos = carpeta_actuaciones

    actuales, historicas, error = await extraer_actuaciones_completas(
        page_expediente=page,
        expediente_datos=expediente_info,
        incluir_historicas=True,
        directorio_base=str(carpeta_json),
    )

    json_path: Path | None = None
    if not error:
        json_path = carpeta_json / f"actuaciones-{numero_normalizado}.json"
        if not json_path.exists():
            json_path = None

    descargas_ejecutadas = False
    if descargar_adjuntos and not error and json_path is not None:
        await descargar_archivos_de_json(
            page,
            str(carpeta_json),
            str(carpeta_adjuntos),
        )
        descargas_ejecutadas = True

    resumen: ResultadoProcesamiento = {
        "actuaciones_actuales": len(actuales),
        "actuaciones_historicas": len(historicas),
        "error": error,
        "carpeta_expediente": str(carpeta_expediente),
        "carpeta_json": str(carpeta_json) if json_path else None,
        "carpeta_actuaciones": str(carpeta_actuaciones),
        "carpeta_adjuntos": str(carpeta_adjuntos),
        "descargas_ejecutadas": descargas_ejecutadas,
        "manifest": manifest,
    }

    return json_path, resumen


__all__ = ["procesar_actuaciones_expediente", "ResultadoProcesamiento"]
