from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from Sistema_v5.pjn.models import Actuacion
from Sistema_v5.pjn.parsers.actuaciones_parser import (
    construir_encabezado_actuaciones,
    construir_nombre_archivo_normalizado,
    normalizar_nombre_expediente,
)
from Sistema_v5.pjn.parsers.entradas_parser import (
    deduplicar_historial,
    normalizar_fecha as normalizar_fecha_entrada,
    parse_entrada,
)
from Sistema_v5.pjn.parsers.expedientes_parser import (
    normalizar_fecha_actuacion,
    parse_expediente_resumen,
)


def test_parse_entrada_normaliza_fecha_y_trim_campos():
    entrada = parse_entrada(
        " 1234/2023 ",
        " Carátula Principal ",
        "03/01/2024",
        evento=" Aviso de traslado ",
        tipo_evento=" DEO ",
        leida=True,
        extraida_en="2024-03-01T10:00:00Z",
    )

    assert entrada.numero == "1234/2023"
    assert entrada.caratula == "Carátula Principal"
    assert entrada.fecha == "2024-01-03"
    assert entrada.evento == " Aviso de traslado "
    assert entrada.tipo_evento == " DEO "
    assert entrada.leida is True
    assert entrada.extraida_en == "2024-03-01T10:00:00Z"


def test_normalizar_fecha_entrada_devuelve_original_si_formato_desconocido():
    assert normalizar_fecha_entrada("2024.01.05") == "2024.01.05"


def test_deduplicar_historial_identifica_claves_unicas():
    original = [
        parse_entrada("001", "Uno", "2024-01-01", evento="A", tipo_evento="X"),
        parse_entrada("001", "Uno", "2024-01-01", evento="A", tipo_evento="X"),
        parse_entrada("002", "Dos", "2024-01-02", evento="B", tipo_evento="Y"),
    ]

    claves = deduplicar_historial(original)
    assert claves == {
        ("001", "2024-01-01", "Uno", "A"),
        ("002", "2024-01-02", "Dos", "B"),
    }


def test_parse_expediente_resumen_normaliza_fecha_y_descarta_incompletos():
    resumen = parse_expediente_resumen(
        [
            " 12345/2023 ",
            " Juzgado Civil 1 ",
            " Pérez c/ García ",
            " En trámite ",
            "05/01/2024",
        ]
    )
    assert resumen is not None
    assert resumen.numero == "12345/2023"
    assert resumen.dependencia == "Juzgado Civil 1"
    assert resumen.caratula == "Pérez c/ García"
    assert resumen.situacion == "En trámite"
    assert resumen.ultima_actuacion == "2024-01-05"

    incompleto = parse_expediente_resumen(["", "", "", "", ""])
    assert incompleto is None


def test_normalizar_fecha_actuacion_deja_valor_si_no_puede_convertir():
    assert normalizar_fecha_actuacion("2024.01.05") == "2024.01.05"


def test_construir_nombre_archivo_prioriza_nombre_descarga():
    nombre, extension = construir_nombre_archivo_normalizado(
        "2024-02-01",
        "DEO",
        "hash123",
        "https://pjn.gob.ar/documento.seam?id=1",
        nombre_descarga="Actuacion.PDF",
    )

    assert nombre == "2024-02-01-deo-hash123.pdf"
    assert extension == ".pdf"


def test_construir_nombre_archivo_usa_extension_de_url_si_no_hay_descarga():
    nombre, extension = construir_nombre_archivo_normalizado(
        "2024-02-01",
        "DEO",
        "hash123",
        "https://pjn.gob.ar/documento.jsp?id=1",
    )

    assert nombre.endswith(".jsp")
    assert extension == ".jsp"


def test_construir_encabezado_actuaciones_calcula_metricas():
    actuales = [
        Actuacion(
            indice=1,
            oficina="Juzgado",
            oficina_completa="Juzgado Civil",
            fecha="2024-01-02",
            tipo="DEO",
            detalle="Notificación",
            foja=None,
            archivo="https://pjn.gob.ar/archivo.pdf",
            nombre_archivo="2024-01-02-deo-hash1.pdf",
            tiene_archivo=True,
            tipo_archivo=".pdf",
            hash="hash1",
            extraida_en="2024-02-01T00:00:00Z",
            es_historica=False,
            descargado=True,
        )
    ]
    historicas = [
        Actuacion(
            indice=2,
            oficina="Secretaría",
            oficina_completa="Secretaría Civil",
            fecha="2023-12-20",
            tipo="RESOLUCION",
            detalle="Providencia",
            foja="12",
            archivo="https://pjn.gob.ar/archivo_anterior.pdf",
            nombre_archivo="2023-12-20-resolucion-hash2.pdf",
            tiene_archivo=True,
            tipo_archivo=".pdf",
            hash="hash2",
            extraida_en="2024-01-15T00:00:00Z",
            es_historica=True,
            descargado=False,
        )
    ]
    expediente_datos = {
        "numero": " 12345/2023 - A ",
        "caratula": "Pérez c/ García",
        "dependencia": "Juzgado Civil 1",
        "jurisdiccion": "Capital Federal",
        "situacion": date(2024, 2, 10),
    }

    encabezado = construir_encabezado_actuaciones(
        expediente_datos,
        actuales,
        historicas,
        incluye_historicas=True,
        timestamp_generacion="2024-03-01T00:00:00Z",
    )

    assert encabezado["Cantidad de Actuaciones Obtenidas"] == 2
    assert encabezado["Cantidad de Archivos Descargados"] == 1
    assert encabezado["descargas_pendientes"] == 1
    assert encabezado["total_actuales"] == 1
    assert encabezado["total_historicas"] == 1
    assert encabezado["ultimo_hash_actual"] == "hash1"
    assert encabezado["ultima_fecha_actual"] == "2024-01-02"
    assert encabezado["situacion"] == "2024-02-10"


def test_normalizar_nombre_expediente_generar_slug_seguro():
    resultado = normalizar_nombre_expediente({"numero": " 12345/2023 - A "})
    assert resultado == "12345_2023_-_A"
