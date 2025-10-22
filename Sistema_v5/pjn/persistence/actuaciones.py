"""Funciones de persistencia para actuaciones del PJN."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

PACKAGE_ROOT = Path(__file__).resolve().parents[3]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.append(str(PACKAGE_ROOT))

from Sistema_v5.configuracion.core.scraping_config import get_config
from Sistema_v5.pjn.models import Actuacion, ActuacionesArchivo
from Sistema_v5.pjn.parsers.actuaciones_parser import construir_actuaciones_archivo
from Sistema_v5.pjn.scraping.base import normalizar_numero_expediente
from Sistema_v5.pjn.utils.logging import get_logger

logger = get_logger(__name__)
_config = get_config()


def cargar_actuaciones_json(ruta_json: str | Path) -> dict[str, Any]:
    """Carga un archivo JSON de actuaciones desde disco.

    Args:
        ruta_json: Ruta al archivo JSON.

    Returns:
        dict: Estructura con "Expediente" y "Actuaciones".

    Raises:
        FileNotFoundError: Si el archivo no existe.
        json.JSONDecodeError: Si el archivo no es JSON válido.
    """
    with open(ruta_json, "r", encoding="utf-8") as f:
        return json.load(f)


def cargar_actuaciones_archivo(ruta_json: str | Path) -> ActuacionesArchivo:
    """Carga un archivo JSON y lo convierte a modelo ActuacionesArchivo.

    Args:
        ruta_json: Ruta al archivo JSON.

    Returns:
        ActuacionesArchivo: Modelo estructurado.

    Raises:
        FileNotFoundError: Si el archivo no existe.
        json.JSONDecodeError: Si el archivo no es JSON válido.
    """
    datos = cargar_actuaciones_json(ruta_json)

    encabezado = datos.get("Expediente", {})
    actuaciones_lista = datos.get("Actuaciones", [])

    actuaciones_modelos = [Actuacion.from_dict(act) for act in actuaciones_lista]

    # Separar actuales de históricas
    actuales = [act for act in actuaciones_modelos if not act.es_historica]
    historicas = [act for act in actuaciones_modelos if act.es_historica]

    # Crear archivo desde parsers
    archivo = construir_actuaciones_archivo(
        expediente_datos=encabezado,
        actuaciones_actuales=actuales,
        actuaciones_historicas=historicas,
        incluye_historicas=bool(historicas),
        timestamp_generacion=encabezado.get("timestamp_generacion", ""),
    )

    return archivo


def guardar_actuaciones_json(
    archivo: ActuacionesArchivo,
    directorio_base: str | Path | None = None,
    numero_expediente: str | None = None,
) -> str:
    """Guarda un ActuacionesArchivo como JSON en disco.

    Args:
        archivo: Modelo de actuaciones a guardar.
        directorio_base: Carpeta base (default desde config).
        numero_expediente: Número de expediente para nombrar el archivo.
            Si no se proporciona, se extrae del encabezado.

    Returns:
        str: Ruta absoluta al archivo guardado.

    Raises:
        ValueError: Si no se puede determinar el número de expediente.
    """
    if directorio_base is None:
        directorio_base = _config.archivos.directorio_base_actuaciones

    # Determinar número de expediente
    if numero_expediente is None:
        numero_expediente = archivo.encabezado.get("numero")
        if not numero_expediente:
            raise ValueError("No se pudo determinar el número de expediente")

    numero_normalizado = normalizar_numero_expediente(numero_expediente)
    carpeta_expediente = Path(directorio_base) / numero_normalizado
    carpeta_expediente.mkdir(parents=True, exist_ok=True)

    # Construir estructura JSON
    estructura_json = {
        "Expediente": archivo.encabezado,
        "Actuaciones": [act.to_dict() for act in archivo.actuaciones],
    }

    # Guardar archivo
    nombre_archivo = f"{_config.archivos.prefijo_archivo_actuaciones}{numero_normalizado}.json"
    ruta_completa = carpeta_expediente / nombre_archivo

    with open(ruta_completa, "w", encoding="utf-8") as f:
        json.dump(estructura_json, f, indent=2, ensure_ascii=False)

    logger.info("📄 JSON guardado: %s", ruta_completa)
    return str(ruta_completa.absolute())


def listar_archivos_actuaciones(
    directorio_base: str | Path | None = None,
    patron: str = "*.json",
) -> list[Path]:
    """Lista todos los archivos de actuaciones en el directorio base.

    Args:
        directorio_base: Carpeta base (default desde config).
        patron: Patrón glob para filtrar archivos.

    Returns:
        list[Path]: Lista de rutas a archivos encontrados.
    """
    if directorio_base is None:
        directorio_base = _config.archivos.directorio_base_actuaciones

    base_path = Path(directorio_base)
    if not base_path.exists():
        return []

    # Buscar recursivamente
    return list(base_path.rglob(patron))


def extraer_actuaciones_con_archivos(archivo: ActuacionesArchivo) -> list[Actuacion]:
    """Filtra actuaciones que tienen archivos para descargar.

    Args:
        archivo: Archivo de actuaciones.

    Returns:
        list[Actuacion]: Lista de actuaciones con archivo != None.
    """
    return [
        act
        for act in archivo.actuaciones
        if act.tiene_archivo and not act.descargado
    ]


def actualizar_descargados(
    ruta_json: str | Path,
    actuaciones_actualizadas: list[Actuacion],
) -> None:
    """Actualiza el estado de descarga de actuaciones en un JSON existente.

    Args:
        ruta_json: Ruta al archivo JSON.
        actuaciones_actualizadas: Lista de actuaciones con estado actualizado.

    Raises:
        FileNotFoundError: Si el archivo no existe.
    """
    # Cargar JSON existente
    datos = cargar_actuaciones_json(ruta_json)

    # Crear mapa por índice para actualización rápida
    mapa_actualizadas = {act.indice: act for act in actuaciones_actualizadas}

    # Actualizar actuaciones en el JSON
    actuaciones_json = datos.get("Actuaciones", [])
    for act_dict in actuaciones_json:
        indice = act_dict.get("Indice")
        if indice in mapa_actualizadas:
            act_actualizada = mapa_actualizadas[indice]
            act_dict["Descargado"] = act_actualizada.descargado
            act_dict["NombreArchivo"] = act_actualizada.nombre_archivo
            act_dict["TipoArchivo"] = act_actualizada.tipo_archivo

    # Guardar JSON actualizado
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)

    logger.info("📝 JSON actualizado: %s", ruta_json)
