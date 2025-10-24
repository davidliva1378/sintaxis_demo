from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from Sistema_v4.actuaciones.actuaciones_v4 import construir_nombre_archivo_normalizado


def test_tipo_doc_extension_docx():
    nombre, tipo_archivo = construir_nombre_archivo_normalizado(
        "2024-01-01",
        "RESOLUCION",
        "abc123",
        "https://example.com/descarga?tipoDoc=docx",
    )

    assert nombre.endswith(".docx")
    assert tipo_archivo == "docx"


def test_tipo_doc_semantico_fallback_pdf():
    nombre, tipo_archivo = construir_nombre_archivo_normalizado(
        "2024-01-01",
        "RESOLUCION",
        "abc123",
        "https://example.com/descarga?tipoDoc=DEO",
    )

    assert nombre.endswith(".pdf")
    assert tipo_archivo == "pdf"


def test_extension_de_url_prevalece_sobre_tipo_doc_semantico():
    nombre, tipo_archivo = construir_nombre_archivo_normalizado(
        "2024-01-01",
        "RESOLUCION",
        "abc123",
        "https://example.com/documento.docx?tipoDoc=DEO",
    )

    assert nombre.endswith(".docx")
    assert tipo_archivo == "docx"


def test_prioriza_extension_descarga_sobre_tipo_doc_semantico():
    nombre, tipo_archivo = construir_nombre_archivo_normalizado(
        "2024-01-01",
        "RESOLUCION",
        "abc123",
        "https://example.com/descarga?tipoDoc=DEO",
        nombre_descarga="firmado.P7M",
    )

    assert nombre.endswith(".p7m")
    assert tipo_archivo == "p7m"
