"""Módulo para extraer texto de archivos PDF.

Este módulo ahora actúa como wrapper sobre Sistema_v5.procesador_pdf.ExtractorTexto,
eliminando código duplicado y agregando funcionalidades mejoradas:
- Extracción con múltiples métodos (PyPDF2, pdfplumber)
- Soporte para OCR opcional (pytesseract)
- Normalización de texto
- Hash MD5 para deduplicación
- Metadata enriquecida

Refactorizado: 2025-11-03 (Tarea 3 - Eliminación de código duplicado)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

# Intentar importar procesador_pdf (integración principal)
try:
    from Sistema_v5.procesador_pdf import ExtractorTexto
    PROCESADOR_DISPONIBLE = True
except ImportError:
    PROCESADOR_DISPONIBLE = False
    logging.warning(
        "procesador_pdf no disponible. Cayendo a implementación legacy con pdfplumber."
    )

# Fallback a pdfplumber si procesador_pdf no está disponible
if not PROCESADOR_DISPONIBLE:
    try:
        import pdfplumber
    except ImportError:
        pdfplumber = None


logger = logging.getLogger(__name__)


def extract_text_from_pdf(
    pdf_path: str | Path,
    max_pages: int | None = None,
    include_metadata: bool = False,
    use_ocr: bool = False,
) -> dict[str, Any]:
    """Extrae texto de un archivo PDF.

    Esta función ahora usa Sistema_v5.procesador_pdf.ExtractorTexto para
    proporcionar extracción mejorada con soporte para OCR y normalización.

    Args:
        pdf_path: Ruta al archivo PDF.
        max_pages: Número máximo de páginas a extraer (None = todas).
        include_metadata: Si incluir metadata del PDF en el resultado.
        use_ocr: Si usar OCR para PDFs escaneados (requiere tesseract).

    Returns:
        Diccionario con:
        - text: Texto completo extraído y normalizado
        - pages: Lista de diccionarios con texto por página
        - num_pages: Número total de páginas
        - metadata: Metadata del PDF (si include_metadata=True)
        - hash: Hash MD5 del texto (para deduplicación)
        - extraction_method: Método usado (pdfplumber, pypdf2, ocr)
        - error: Mensaje de error si falló la extracción

    Raises:
        FileNotFoundError: Si el archivo no existe.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"Archivo PDF no encontrado: {pdf_path}")

    # Usar procesador_pdf si está disponible (RECOMENDADO)
    if PROCESADOR_DISPONIBLE:
        return _extract_with_procesador_pdf(
            pdf_path, max_pages, include_metadata, use_ocr
        )

    # Fallback a implementación legacy
    return _extract_with_pdfplumber_legacy(
        pdf_path, max_pages, include_metadata
    )


def _extract_with_procesador_pdf(
    pdf_path: Path,
    max_pages: int | None,
    include_metadata: bool,
    use_ocr: bool,
) -> dict[str, Any]:
    """Extrae texto usando procesador_pdf.ExtractorTexto (método preferido)."""

    try:
        extractor = ExtractorTexto(usar_ocr=use_ocr)
        resultado = extractor.extraer(str(pdf_path))

        # Convertir a formato esperado por MCP Server
        result: dict[str, Any] = {
            "text": resultado.texto_completo,
            "pages": [],
            "num_pages": resultado.num_paginas,
            "hash": resultado.hash_md5,
            "extraction_method": resultado.metodo_extraccion,
            "error": None,
        }

        # Construir información por página si es necesario
        if max_pages:
            # Limitar texto a las primeras N páginas (aproximado)
            lines = resultado.texto_completo.split('\n')
            estimated_lines_per_page = len(lines) // resultado.num_paginas if resultado.num_paginas > 0 else len(lines)

            for i in range(min(max_pages, resultado.num_paginas)):
                start_line = i * estimated_lines_per_page
                end_line = (i + 1) * estimated_lines_per_page
                page_text = '\n'.join(lines[start_line:end_line])

                result["pages"].append({
                    "page_number": i + 1,
                    "text": page_text,
                    "char_count": len(page_text),
                })
        else:
            # Todas las páginas (información agregada)
            avg_chars = len(resultado.texto_completo) // resultado.num_paginas if resultado.num_paginas > 0 else 0
            for i in range(resultado.num_paginas):
                result["pages"].append({
                    "page_number": i + 1,
                    "char_count": avg_chars,  # Estimado
                })

        # Metadata del PDF
        if include_metadata and resultado.metadata:
            result["metadata"] = resultado.metadata

        logger.info(
            f"PDF extraído con procesador_pdf: {resultado.num_paginas} páginas, "
            f"método={resultado.metodo_extraccion}"
        )

        return result

    except Exception as e:
        logger.error(f"Error al extraer PDF con procesador_pdf: {e}")
        return {
            "text": "",
            "pages": [],
            "num_pages": 0,
            "error": str(e),
        }


def _extract_with_pdfplumber_legacy(
    pdf_path: Path,
    max_pages: int | None,
    include_metadata: bool,
) -> dict[str, Any]:
    """Fallback a extracción legacy con pdfplumber.

    Esta función se mantiene para backward compatibility cuando procesador_pdf
    no está disponible.
    """
    if pdfplumber is None:
        return {
            "text": "",
            "pages": [],
            "num_pages": 0,
            "error": "pdfplumber no está instalado. Instala con: pip install pdfplumber",
        }

    result: dict[str, Any] = {
        "text": "",
        "pages": [],
        "num_pages": 0,
        "extraction_method": "pdfplumber_legacy",
        "error": None,
    }

    try:
        with pdfplumber.open(pdf_path) as pdf:
            result["num_pages"] = len(pdf.pages)

            if include_metadata:
                result["metadata"] = pdf.metadata

            pages_to_extract = (
                pdf.pages[:max_pages] if max_pages else pdf.pages
            )

            all_text = []
            for i, page in enumerate(pages_to_extract, start=1):
                try:
                    page_text = page.extract_text() or ""
                    all_text.append(page_text)

                    result["pages"].append({
                        "page_number": i,
                        "text": page_text,
                        "char_count": len(page_text),
                    })
                except Exception as e:
                    result["pages"].append({
                        "page_number": i,
                        "text": "",
                        "error": str(e),
                    })

            result["text"] = "\n\n".join(all_text)

    except Exception as e:
        result["error"] = str(e)

    return result


def extract_text_summary(
    pdf_path: str | Path,
    max_chars: int = 1000,
) -> str:
    """Extrae un resumen del texto del PDF (primeras N caracteres).

    Args:
        pdf_path: Ruta al archivo PDF.
        max_chars: Número máximo de caracteres a extraer.

    Returns:
        Texto extraído (truncado si es mayor a max_chars).
    """
    try:
        result = extract_text_from_pdf(pdf_path, max_pages=5)

        if result["error"]:
            return f"Error al extraer PDF: {result['error']}"

        text = result["text"]
        if len(text) > max_chars:
            return text[:max_chars] + "... (truncado)"

        return text

    except Exception as e:
        return f"Error: {e}"


def get_pdf_info(pdf_path: str | Path) -> dict[str, Any]:
    """Obtiene información básica de un PDF sin extraer todo el texto.

    Args:
        pdf_path: Ruta al archivo PDF.

    Returns:
        Diccionario con información básica del PDF:
        - num_pages: Número de páginas
        - metadata: Metadata del PDF
        - file_size: Tamaño del archivo en bytes
        - error: Mensaje de error si falló
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        return {"error": f"Archivo no encontrado: {pdf_path}"}

    info: dict[str, Any] = {
        "num_pages": 0,
        "metadata": {},
        "file_size": 0,
        "error": None,
    }

    try:
        info["file_size"] = pdf_path.stat().st_size

        # Usar procesador_pdf si está disponible
        if PROCESADOR_DISPONIBLE:
            # Extraer solo metadata, sin texto completo
            result = extract_text_from_pdf(pdf_path, max_pages=1, include_metadata=True)
            info["num_pages"] = result["num_pages"]
            info["metadata"] = result.get("metadata", {})
            if result["error"]:
                info["error"] = result["error"]

        # Fallback a pdfplumber
        elif pdfplumber is not None:
            with pdfplumber.open(pdf_path) as pdf:
                info["num_pages"] = len(pdf.pages)
                info["metadata"] = pdf.metadata or {}
        else:
            info["error"] = "No hay extractor de PDF disponible"

    except Exception as e:
        info["error"] = str(e)

    return info


# Función auxiliar para clasificar texto de PDF (NUEVO)
def classify_pdf_content(
    pdf_path: str | Path,
    tipo_actuacion: str = "",
    detalle_actuacion: str = "",
) -> dict[str, Any] | None:
    """Clasifica el contenido de un PDF usando procesador_pdf.

    Esta es una nueva funcionalidad que aprovecha la integración con
    procesador_pdf para proporcionar clasificación automática.

    Args:
        pdf_path: Ruta al archivo PDF.
        tipo_actuacion: Tipo de la actuación (opcional).
        detalle_actuacion: Detalle de la actuación (opcional).

    Returns:
        Diccionario con clasificación o None si procesador_pdf no está disponible:
        - utilidad: ALTA, MEDIA, BAJA, NULA
        - score: Confianza de la clasificación (0-100)
        - motivo: Explicación de la clasificación
        - keywords: Palabras clave detectadas

    Ejemplo:
        >>> clasificacion = classify_pdf_content("cedula.pdf", tipo="CEDULA_ELECTRONICA")
        >>> print(clasificacion["utilidad"])  # "ALTA"
    """
    if not PROCESADOR_DISPONIBLE:
        logger.warning("procesador_pdf no disponible para clasificación")
        return None

    try:
        from Sistema_v5.procesador_pdf import ClasificadorActuaciones

        # Extraer texto del PDF
        result = extract_text_from_pdf(pdf_path, max_pages=10)
        if result["error"]:
            return {"error": result["error"]}

        # Usar el detalle de la actuación o el texto extraído
        texto_para_clasificar = detalle_actuacion or result["text"][:1000]

        # Clasificar
        clasificador = ClasificadorActuaciones()
        clasificacion = clasificador.clasificar(
            tipo=tipo_actuacion,
            detalle=texto_para_clasificar,
            tiene_archivo=True
        )

        return {
            "utilidad": clasificacion.utilidad.value,
            "score": clasificacion.score,
            "motivo": clasificacion.motivo,
            "keywords": clasificacion.keywords_detectados,
            "tiene_plazo": clasificacion.tiene_plazo_probable,
        }

    except Exception as e:
        logger.error(f"Error al clasificar PDF: {e}")
        return {"error": str(e)}


# Función auxiliar para analizar vencimientos en PDF (NUEVO)
def analyze_deadlines_in_pdf(
    pdf_path: str | Path,
) -> list[dict[str, Any]] | None:
    """Analiza vencimientos y plazos procesales en un PDF.

    Esta es una nueva funcionalidad que detecta automáticamente vencimientos
    en el contenido del PDF.

    Args:
        pdf_path: Ruta al archivo PDF.

    Returns:
        Lista de vencimientos detectados o None si procesador_pdf no está disponible.
        Cada vencimiento contiene:
        - tipo: Tipo de vencimiento (CEDULA_ELECTRONICA, TRASLADO, etc.)
        - fecha_notificacion: Fecha de notificación
        - fecha_vencimiento: Fecha de vencimiento calculada
        - dias_restantes: Días hasta el vencimiento
        - es_urgente: Si el vencimiento es urgente (< 7 días)
        - descripcion: Descripción del plazo

    Ejemplo:
        >>> vencimientos = analyze_deadlines_in_pdf("cedula.pdf")
        >>> for venc in vencimientos:
        ...     print(f"Vence en {venc['dias_restantes']} días")
    """
    if not PROCESADOR_DISPONIBLE:
        logger.warning("procesador_pdf no disponible para análisis de vencimientos")
        return None

    try:
        from Sistema_v5.procesador_pdf import AnalizadorVencimientos

        # Extraer texto del PDF
        result = extract_text_from_pdf(pdf_path)
        if result["error"]:
            logger.error(f"Error al extraer PDF: {result['error']}")
            return []

        # Analizar vencimientos
        analizador = AnalizadorVencimientos()
        vencimientos = analizador.analizar_actuacion({
            "tipo": "",
            "detalle": result["text"],
            "tiene_archivo": True
        })

        # Convertir a formato dict
        resultado = []
        for venc in vencimientos:
            resultado.append({
                "tipo": venc.tipo.value,
                "fecha_notificacion": venc.fecha_notificacion.isoformat() if venc.fecha_notificacion else None,
                "fecha_vencimiento": venc.fecha_vencimiento.isoformat() if venc.fecha_vencimiento else None,
                "dias_restantes": venc.dias_restantes,
                "es_urgente": venc.es_urgente,
                "descripcion": venc.descripcion,
            })

        return resultado

    except Exception as e:
        logger.error(f"Error al analizar vencimientos: {e}")
        return []


__all__ = [
    "extract_text_from_pdf",
    "extract_text_summary",
    "get_pdf_info",
    "classify_pdf_content",
    "analyze_deadlines_in_pdf",
    "PROCESADOR_DISPONIBLE",
]
