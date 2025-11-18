"""Servicios de alto nivel para gestionar actuaciones de un expediente.

Esta capa coordina la preparación de directorios, la extracción de
actuaciones y la descarga opcional de adjuntos, manteniendo separada la
lógica de scraping de los scripts interactivos.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, TypedDict

from gestor_directorios import GestorDirectoriosExpedientes
from pjn.scraping import normalizar_numero_expediente
from pjn.scraping.actuaciones import (
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

    # Determinar base_dir correctamente (directorio raíz del proyecto)
    import sys
    from pathlib import Path

    # Si estamos en Sistema_v6/pjn/services/actuaciones.py, subir 2 niveles
    base_dir = Path(__file__).resolve().parent.parent.parent

    gestor = GestorDirectoriosExpedientes.desde_config(base_dir=base_dir)
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

    # Actualizar metadatos de procesamiento en manifest.json
    if not error and json_path is not None:
        from datetime import datetime
        import json

        total_actuaciones = len(actuales) + len(historicas)

        # Contar adjuntos descargados
        total_adjuntos = 0
        if descargas_ejecutadas and carpeta_adjuntos:
            try:
                from pathlib import Path
                import logging
                logger = logging.getLogger(__name__)
                adjuntos_path = Path(carpeta_adjuntos)
                if adjuntos_path.exists():
                    archivos = list(adjuntos_path.glob("*.*"))
                    total_adjuntos = len(archivos)
                    logger.info(f"Contados {total_adjuntos} adjuntos en {adjuntos_path}")
                else:
                    logger.warning(f"Ruta de adjuntos no existe: {adjuntos_path}")
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error al contar adjuntos: {e}")

        # Actualizar manifest
        try:
            manifest_path = carpeta_expediente / "manifest.json"
            if manifest_path.exists():
                manifest_actual = json.loads(manifest_path.read_text(encoding="utf-8"))

                # Asegurar estructura de procesamiento existe
                if "metadata" not in manifest_actual:
                    manifest_actual["metadata"] = {}
                if "procesamiento" not in manifest_actual["metadata"]:
                    manifest_actual["metadata"]["procesamiento"] = {
                        "creado_en": datetime.now().isoformat(timespec="seconds"),
                        "total_extracciones": 0,
                    }

                # Actualizar contadores
                proc = manifest_actual["metadata"]["procesamiento"]
                proc["ultima_extraccion"] = datetime.now().isoformat(timespec="seconds")
                proc["total_extracciones"] = proc.get("total_extracciones", 0) + 1
                proc["total_actuaciones"] = total_actuaciones
                proc["total_adjuntos_descargados"] = total_adjuntos
                proc["estado_sincronizacion"] = "actualizado"

                # Guardar manifest actualizado usando escritura atómica
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Actualizando manifest: {total_adjuntos} adjuntos, {total_actuaciones} actuaciones")
                gestor._persistir_json_atomico(manifest_path, manifest_actual)
                manifest = manifest_actual
                logger.info(f"Manifest actualizado exitosamente para {numero_expediente}")
        except Exception as e:
            # No fallar si no se puede actualizar manifest
            import logging
            import traceback
            logger = logging.getLogger(__name__)
            logger.error(
                f"No se pudo actualizar manifest para {numero_expediente}: {e}\n"
                f"Traceback: {traceback.format_exc()}"
            )

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
