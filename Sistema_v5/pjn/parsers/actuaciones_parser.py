"""Parsers especializados para actuaciones del portal PJN."""
from __future__ import annotations

from datetime import date, datetime
from typing import Iterable, Mapping, Sequence

# Mapping ya está importado arriba para type hints

from playwright.async_api import ElementHandle, Page

from ..models import Actuacion, ActuacionesArchivo
from ..scraping.actuaciones_utils import (
    generar_hash_archivo,
    limpiar_texto,
    normalizar_fecha,
)
from ..scraping.base import normalizar_numero_expediente
from ..selectores import SEL_ACTUACIONES


EXTENSIONES_CONOCIDAS = {
    "7z": ".7z",
    "avi": ".avi",
    "bak": ".bak",
    "bmp": ".bmp",
    "cer": ".cer",
    "csv": ".csv",
    "der": ".der",
    "doc": ".doc",
    "docm": ".docm",
    "docx": ".docx",
    "eml": ".eml",
    "epub": ".epub",
    "gif": ".gif",
    "gz": ".gz",
    "heic": ".heic",
    "heif": ".heif",
    "htm": ".htm",
    "html": ".html",
    "ics": ".ics",
    "jpeg": ".jpeg",
    "jpg": ".jpg",
    "json": ".json",
    "log": ".log",
    "m4a": ".m4a",
    "mkv": ".mkv",
    "mov": ".mov",
    "mp3": ".mp3",
    "mp4": ".mp4",
    "msg": ".msg",
    "odt": ".odt",
    "ogg": ".ogg",
    "pdf": ".pdf",
    "pdfa": ".pdf",
    "pfx": ".pfx",
    "p12": ".p12",
    "p7m": ".p7m",
    "p7s": ".p7s",
    "png": ".png",
    "ppt": ".ppt",
    "pptx": ".pptx",
    "pps": ".pps",
    "ppsx": ".ppsx",
    "rar": ".rar",
    "rtf": ".rtf",
    "svg": ".svg",
    "tar": ".tar",
    "tif": ".tif",
    "tiff": ".tiff",
    "txt": ".txt",
    "wav": ".wav",
    "webm": ".webm",
    "xls": ".xls",
    "xlsx": ".xlsx",
    "xml": ".xml",
    "xps": ".xps",
}


EXTENSIONES_GENERICAS = {".seam", ".jsp", ".do", ".php", ".aspx", ".ashx"}


def obtener_extension_valida(valor: str | None) -> str | None:
    if not valor:
        return None
    base = limpiar_texto(valor).lstrip(".").lower()
    if not base:
        return None
    if base in EXTENSIONES_CONOCIDAS:
        return EXTENSIONES_CONOCIDAS[base]
    if base.startswith("."):
        base = base[1:]
        if base in EXTENSIONES_CONOCIDAS:
            return EXTENSIONES_CONOCIDAS[base]
    return f".{base}" if base else None


def construir_nombre_archivo_normalizado(
    fecha: str | None,
    tipo: str | None,
    hash_val: str | None,
    archivo_url: str | None,
    nombre_descarga: str | None = None,
) -> tuple[str | None, str | None]:
    """Calcula el nombre de archivo y su extensión."""

    extension = None
    if nombre_descarga:
        extension = obtener_extension_valida(nombre_descarga.split(".")[-1])
    if not extension and archivo_url:
        fragmento = archivo_url.split("?")[0]
        extension = obtener_extension_valida(fragmento.split(".")[-1])

    # Sanitizar la fecha para evitar crear subdirectorios
    # Remover cualquier prefijo "Fecha:" y reemplazar barras por guiones
    fecha_limpia = fecha or ""
    if fecha_limpia:
        # Remover prefijo "Fecha:"
        fecha_limpia = fecha_limpia.replace("Fecha:", "").replace("Fecha: ", "").strip()
        # Reemplazar barras por guiones para evitar crear carpetas
        fecha_limpia = fecha_limpia.replace("/", "-")

    nombre_base = "_".join(
        filtro
        for filtro in (
            fecha_limpia,
            (tipo or "").replace(" ", "_").lower(),
            hash_val or "",
        )
        if filtro
    )
    nombre_base = nombre_base or "actuacion"

    tipo_archivo = extension[1:] if extension and len(extension) > 1 else None
    nombre_final = f"{nombre_base}{extension}" if extension else nombre_base

    return nombre_final, tipo_archivo


async def parse_actuacion_row(
    page_expediente: Page,
    fila: ElementHandle,
    indice: int,
    timestamp_extraccion: str,
    *,
    es_historica: bool = False,
) -> Actuacion | None:
    """Interpreta una fila HTML y devuelve una :class:`Actuacion`."""

    celdas = await fila.query_selector_all("td")
    if len(celdas) < 6:
        return None

    oficina = limpiar_texto(await celdas[1].inner_text())
    oficina_completa = await celdas[1].get_attribute("title") or oficina
    fecha_cruda = limpiar_texto(await celdas[2].inner_text())
    fecha = normalizar_fecha(fecha_cruda)
    tipo = limpiar_texto(await celdas[3].inner_text()).replace(" ", "_").upper()
    detalle = limpiar_texto(await celdas[4].inner_text())
    foja = limpiar_texto(await celdas[5].inner_text())

    archivo_url = None
    nombre_archivo = None
    tipo_archivo = None
    hash_val = generar_hash_archivo(fecha, tipo, detalle)

    icono = await fila.query_selector(SEL_ACTUACIONES.ICONO_DESCARGA)
    tiene_archivo = bool(icono)

    if icono:
        link = await page_expediente.evaluate_handle("(el) => el.closest('a')", icono)
        if link:
            archivo_url = await link.get_attribute("href")
            if archivo_url:
                nombre_descarga = await link.get_attribute("download")
                nombre_archivo, tipo_archivo = construir_nombre_archivo_normalizado(
                    fecha,
                    tipo,
                    hash_val,
                    archivo_url,
                    nombre_descarga,
                )

    return Actuacion(
        indice=indice,
        oficina=oficina,
        oficina_completa=oficina_completa,
        fecha=fecha,
        tipo=tipo,
        detalle=detalle,
        foja=foja,
        archivo=archivo_url or None,
        nombre_archivo=nombre_archivo,
        tiene_archivo=tiene_archivo,
        tipo_archivo=tipo_archivo,
        hash=hash_val,
        extraida_en=timestamp_extraccion,
        es_historica=es_historica,
        descargado=False,
    )


def _calcular_metricas_descargas(
    actuaciones: Iterable[Actuacion | Mapping[str, object]],
) -> tuple[int, int, int]:
    """Calcula métricas de descarga para una lista de actuaciones.

    Args:
        actuaciones: Iterable de objetos Actuacion o dicts con datos de actuaciones

    Returns:
        tuple[total_con_archivo, total_descargados, pendientes]

    Note:
        Función consolidada desde actuaciones.py para evitar duplicación.
        Acepta tanto objetos Actuacion como dicts para compatibilidad.
    """
    total_con_archivo = 0
    total_descargados = 0

    for act in actuaciones:
        # Convertir dict a Actuacion si es necesario
        if isinstance(act, Actuacion):
            actuacion = act
        elif isinstance(act, Mapping):
            actuacion = Actuacion.from_dict(act)
        else:
            continue

        if actuacion.tiene_archivo:
            total_con_archivo += 1
            if actuacion.descargado:
                total_descargados += 1

    pendientes = max(total_con_archivo - total_descargados, 0)
    return total_con_archivo, total_descargados, pendientes


def construir_encabezado_actuaciones(
    expediente_datos: Mapping[str, object],
    actuaciones_actuales: Sequence[Actuacion],
    actuaciones_historicas: Sequence[Actuacion],
    *,
    incluye_historicas: bool,
    timestamp_generacion: str,
) -> dict[str, object]:
    """Compone el encabezado enriquecido para el archivo de actuaciones."""

    campos_base: dict[str, object | None] = {
        "numero": expediente_datos.get("numero"),
        "caratula": expediente_datos.get("caratula"),
        "dependencia": expediente_datos.get("dependencia"),
        "jurisdiccion": expediente_datos.get("jurisdiccion"),
        "situacion": expediente_datos.get("situacion"),
    }

    for clave, valor in list(campos_base.items()):
        if isinstance(valor, (date, datetime)):
            campos_base[clave] = valor.strftime("%Y-%m-%d")

    total_actuales = len(actuaciones_actuales)
    total_historicas = len(actuaciones_historicas)
    todas = list(actuaciones_actuales) + list(actuaciones_historicas)
    total_con_archivo, total_descargados, descargas_pendientes = _calcular_metricas_descargas(
        todas
    )

    ultimo_hash_actual = actuaciones_actuales[0].hash if actuaciones_actuales else None
    ultima_fecha_actual = actuaciones_actuales[0].fecha if actuaciones_actuales else None

    campos_base.update(
        {
            "Cantidad de Actuaciones Obtenidas": total_actuales + total_historicas,
            "Cantidad de Archivos Descargados": total_descargados,
            "version_formato": "1.1",
            "fecha_extraccion": timestamp_generacion,
            "incluye_historicas": incluye_historicas,
            "total_actuales": total_actuales,
            "total_historicas": total_historicas,
            "total_actuaciones": total_actuales + total_historicas,
            "total_archivos_con_enlace": total_con_archivo,
            "descargas_pendientes": descargas_pendientes,
            "ultimo_hash_actual": ultimo_hash_actual,
            "ultima_fecha_actual": ultima_fecha_actual,
        }
    )

    return campos_base


def construir_actuaciones_archivo(
    expediente_datos: Mapping[str, object],
    actuaciones_actuales: Sequence[Actuacion],
    actuaciones_historicas: Sequence[Actuacion],
    *,
    incluye_historicas: bool,
    timestamp_generacion: str,
) -> ActuacionesArchivo:
    encabezado = construir_encabezado_actuaciones(
        expediente_datos,
        actuaciones_actuales,
        actuaciones_historicas,
        incluye_historicas=incluye_historicas,
        timestamp_generacion=timestamp_generacion,
    )
    return ActuacionesArchivo(
        encabezado=encabezado,
        actuaciones=tuple(actuaciones_actuales) + tuple(actuaciones_historicas),
    )


def normalizar_nombre_expediente(expediente_datos: Mapping[str, object]) -> str:
    return normalizar_numero_expediente(
        expediente_datos.get("numero"), valor_por_defecto="desconocido"
    )


__all__ = [
    "Actuacion",
    "ActuacionesArchivo",
    "construir_actuaciones_archivo",
    "construir_encabezado_actuaciones",
    "construir_nombre_archivo_normalizado",
    "normalizar_nombre_expediente",
    "obtener_extension_valida",
    "parse_actuacion_row",
]
