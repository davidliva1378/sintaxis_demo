"""Parser especializado para actuaciones del portal PJN.

Este módulo contiene funciones para interpretar las filas HTML de actuaciones
judiciales y convertirlas en objetos del dominio, incluyendo manejo de archivos
adjuntos, extensiones, y construcción de encabezados.

Migrado de: Sistema_v5/pjn/parsers/actuaciones_parser.py
"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime
from typing import Iterable, Mapping, Sequence

from playwright.async_api import ElementHandle, Page

from core.domain.entities import Actuacion, ActuacionesArchivo
from core.domain.utils.dates import normalizar_fecha
from core.domain.utils.hashing import generar_hash_identificador
from core.domain.utils.text import limpiar_texto, normalizar_numero_expediente

from ..selectores import SEL_ACTUACIONES

logger = logging.getLogger(__name__)


# === Extensiones de archivo ===


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


# === Utilidades de texto para actuaciones ===


_PREFIXES = re.compile(
    r"^(?:Oficina:|Fecha:|Tipo[_ ]actuacion:|Detalle:|Foja:)[_\s]*",
    re.IGNORECASE,
)


def limpiar_texto_actuacion(texto: str | None) -> str:
    """Limpia texto de celdas de actuaciones removiendo etiquetas iniciales.

    Args:
        texto: Texto a limpiar

    Returns:
        Texto limpio sin prefijos como "Oficina:", "Fecha:", etc.
    """
    base = limpiar_texto(texto)
    if not base:
        return ""
    return _PREFIXES.sub("", base, count=1)


def normalizar_fecha_actuacion(texto: str | None) -> str:
    """Normaliza fechas de actuaciones al formato ISO.

    Args:
        texto: Fecha en cualquier formato

    Returns:
        Fecha en formato YYYY-MM-DD o string vacío si no se pudo parsear
    """
    # Primero limpiar el prefijo "Fecha:" si existe
    texto_limpio = limpiar_texto_actuacion(texto)
    if not texto_limpio:
        return ""

    # Luego normalizar al formato ISO
    normalizada = normalizar_fecha(texto_limpio)
    if normalizada is None:
        return ""
    return normalizada


def generar_hash_archivo(
    fecha: str | None, tipo: str | None, detalle: str | None, longitud: int = 6
) -> str:
    """Genera un hash corto para identificar actuaciones con archivo adjunto.

    Args:
        fecha: Fecha de la actuación
        tipo: Tipo de actuación
        detalle: Detalle de la actuación
        longitud: Longitud del hash (default: 6)

    Returns:
        Hash hexadecimal de longitud especificada
    """
    return generar_hash_identificador(fecha, tipo, detalle, longitud=longitud)


# === Funciones de extensión de archivos ===


def obtener_extension_valida(valor: str | None) -> str | None:
    """Obtiene la extensión de archivo válida a partir de un string.

    Args:
        valor: String que contiene la extensión (puede incluir el punto o no)

    Returns:
        Extensión normalizada con punto (ej: ".pdf") o None si no es válida

    Example:
        >>> obtener_extension_valida("pdf")
        '.pdf'
        >>> obtener_extension_valida(".docx")
        '.docx'
        >>> obtener_extension_valida("PDF")
        '.pdf'
    """
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
    """Construye un nombre de archivo normalizado y seguro.

    Args:
        fecha: Fecha de la actuación
        tipo: Tipo de actuación
        hash_val: Hash identificador
        archivo_url: URL del archivo para inferir extensión
        nombre_descarga: Nombre de descarga sugerido por el servidor

    Returns:
        Tupla (nombre_final, tipo_archivo):
            - nombre_final: Nombre completo con extensión
            - tipo_archivo: Tipo de archivo sin punto (ej: "pdf")

    Example:
        >>> nombre, tipo = construir_nombre_archivo_normalizado(
        ...     "2024-01-15", "PROVIDENCIA", "abc123",
        ...     "https://portal.pjn.gov.ar/doc.pdf", None
        ... )
        >>> print(nombre)
        '2024-01-15_providencia_abc123.pdf'
        >>> print(tipo)
        'pdf'
    """
    extension = None

    # Intentar obtener extensión del nombre de descarga
    if nombre_descarga:
        extension = obtener_extension_valida(nombre_descarga.split(".")[-1])

    # Si no, intentar desde URL
    if not extension and archivo_url:
        fragmento = archivo_url.split("?")[0]
        extension = obtener_extension_valida(fragmento.split(".")[-1])

    # Sanitizar la fecha para evitar crear subdirectorios
    fecha_limpia = fecha or ""
    if fecha_limpia:
        # Remover prefijo "Fecha:" si existe
        fecha_limpia = fecha_limpia.replace("Fecha:", "").replace("Fecha: ", "").strip()
        # Reemplazar barras por guiones para evitar crear carpetas
        fecha_limpia = fecha_limpia.replace("/", "-")

    # Construir nombre base
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

    # Determinar tipo de archivo
    tipo_archivo = extension[1:] if extension and len(extension) > 1 else None

    # Nombre final
    nombre_final = f"{nombre_base}{extension}" if extension else nombre_base

    return nombre_final, tipo_archivo


# === Parser principal de actuaciones ===


async def parse_actuacion_row(
    page_expediente: Page,
    fila: ElementHandle,
    indice: int,
    timestamp_extraccion: str,
    *,
    es_historica: bool = False,
) -> Actuacion | None:
    """Interpreta una fila HTML de actuación y devuelve un objeto Actuacion.

    Args:
        page_expediente: Página de Playwright del expediente
        fila: Handle de la fila HTML (<tr>)
        indice: Índice de la actuación en la lista
        timestamp_extraccion: Timestamp de cuando se extrajo
        es_historica: Si es una actuación histórica (default: False)

    Returns:
        Actuacion si se pudo parsear correctamente, None si no

    Example:
        >>> # En contexto async
        >>> fila = await page.query_selector("tr")
        >>> actuacion = await parse_actuacion_row(
        ...     page, fila, 1, "2024-01-15T10:00:00", es_historica=False
        ... )
    """
    # Obtener celdas de la fila
    celdas = await fila.query_selector_all("td")
    if len(celdas) < 6:
        logger.warning(f"Fila con menos de 6 celdas (indice={indice}), saltando")
        return None

    # Extraer datos de las celdas
    oficina = limpiar_texto_actuacion(await celdas[1].inner_text())
    oficina_completa = await celdas[1].get_attribute("title") or oficina
    fecha_cruda = limpiar_texto_actuacion(await celdas[2].inner_text())
    fecha = normalizar_fecha_actuacion(fecha_cruda)
    tipo = limpiar_texto_actuacion(await celdas[3].inner_text()).replace(" ", "_").upper()
    detalle = limpiar_texto_actuacion(await celdas[4].inner_text())
    foja = limpiar_texto_actuacion(await celdas[5].inner_text())

    # Inicializar variables de archivo
    archivo_url = None
    nombre_archivo = None
    tipo_archivo = None
    hash_val = generar_hash_archivo(fecha, tipo, detalle)

    # Buscar icono de descarga
    icono = await fila.query_selector(SEL_ACTUACIONES.ICONO_DESCARGA)
    tiene_archivo = bool(icono)

    if icono:
        # Si tiene archivo, obtener URL y nombre
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
        firmante=None,  # Campo adicional en v6
    )


# === Funciones de construcción de archivos ===


def _calcular_metricas_descargas(
    actuaciones: Iterable[Actuacion | Mapping[str, object]],
) -> tuple[int, int, int]:
    """Calcula métricas de descarga para una lista de actuaciones.

    Args:
        actuaciones: Iterable de objetos Actuacion o dicts con datos

    Returns:
        Tupla (total_con_archivo, total_descargados, pendientes)

    Example:
        >>> actuaciones = [
        ...     Actuacion(..., tiene_archivo=True, descargado=True),
        ...     Actuacion(..., tiene_archivo=True, descargado=False),
        ... ]
        >>> con_archivo, descargados, pendientes = _calcular_metricas_descargas(actuaciones)
        >>> print(f"{descargados}/{con_archivo} descargados, {pendientes} pendientes")
        '1/2 descargados, 1 pendientes'
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
    """Compone el encabezado enriquecido para el archivo de actuaciones.

    Args:
        expediente_datos: Datos del expediente (numero, caratula, etc.)
        actuaciones_actuales: Actuaciones actuales
        actuaciones_historicas: Actuaciones históricas
        incluye_historicas: Si se incluyeron históricas
        timestamp_generacion: Timestamp de generación

    Returns:
        Diccionario con el encabezado completo
    """
    campos_base: dict[str, object | None] = {
        "numero": expediente_datos.get("numero"),
        "caratula": expediente_datos.get("caratula"),
        "dependencia": expediente_datos.get("dependencia"),
        "jurisdiccion": expediente_datos.get("jurisdiccion"),
        "situacion": expediente_datos.get("situacion"),
    }

    # Normalizar fechas a string
    for clave, valor in list(campos_base.items()):
        if isinstance(valor, (date, datetime)):
            campos_base[clave] = valor.strftime("%Y-%m-%d")

    # Calcular métricas
    total_actuales = len(actuaciones_actuales)
    total_historicas = len(actuaciones_historicas)
    todas = list(actuaciones_actuales) + list(actuaciones_historicas)
    total_con_archivo, total_descargados, descargas_pendientes = _calcular_metricas_descargas(
        todas
    )

    # Obtener última actuación actual
    ultimo_hash_actual = actuaciones_actuales[0].hash if actuaciones_actuales else None
    ultima_fecha_actual = actuaciones_actuales[0].fecha if actuaciones_actuales else None

    # Agregar metadatos
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
    """Construye un objeto ActuacionesArchivo completo.

    Args:
        expediente_datos: Datos del expediente
        actuaciones_actuales: Actuaciones actuales
        actuaciones_historicas: Actuaciones históricas
        incluye_historicas: Si se incluyeron históricas
        timestamp_generacion: Timestamp de generación

    Returns:
        ActuacionesArchivo con encabezado y actuaciones

    Example:
        >>> archivo = construir_actuaciones_archivo(
        ...     {"numero": "CNM 0001/2024", "caratula": "CASO X"},
        ...     actuaciones_actuales,
        ...     [],
        ...     incluye_historicas=False,
        ...     timestamp_generacion="2024-01-15T10:00:00"
        ... )
    """
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
    """Normaliza el nombre del expediente para uso en paths.

    Args:
        expediente_datos: Diccionario con datos del expediente

    Returns:
        Nombre normalizado seguro para filesystem
    """
    return normalizar_numero_expediente(
        expediente_datos.get("numero"), valor_por_defecto="desconocido"
    )


__all__ = [
    "parse_actuacion_row",
    "construir_actuaciones_archivo",
    "construir_encabezado_actuaciones",
    "construir_nombre_archivo_normalizado",
    "normalizar_nombre_expediente",
    "obtener_extension_valida",
    "generar_hash_archivo",
    "limpiar_texto_actuacion",
    "normalizar_fecha_actuacion",
]
