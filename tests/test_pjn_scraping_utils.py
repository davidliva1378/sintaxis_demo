from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from Sistema_v5.pjn.models import Actuacion
from Sistema_v5.pjn.scraping.actuaciones import actualizar_metricas_descargas_en_json
from Sistema_v5.pjn.scraping.base import (
    generar_hash_identificador,
    limpiar_texto,
    normalizar_fecha,
    normalizar_numero_expediente,
    normalizar_texto,
)
from Sistema_v5.pjn.scraping.entradas import (
    _base_key,
    _event_key,
    _parse_fecha_limite,
    _parse_fechas_exactas,
    _to_iso,
)


def test_limpiar_texto_elimina_saltos_y_trim():
    assert limpiar_texto("  Hola\nMundo  ") == "Hola Mundo"
    assert limpiar_texto(None) == ""


def test_normalizar_texto_minusculas_sin_acentos():
    assert normalizar_texto("  ÁÉÍÓÚ Ñ  ") == "aeiou n"


def test_normalizar_fecha_admite_varios_formatos():
    assert normalizar_fecha("03/01/2024") == "2024-01-03"
    assert normalizar_fecha(date(2024, 1, 3)) == "2024-01-03"
    assert normalizar_fecha(datetime(2024, 1, 3, 15, 30)) == "2024-01-03"


def test_normalizar_fecha_retorna_original_si_no_identifica_formato():
    assert normalizar_fecha("03.01.2024") == "03.01.2024"


def test_generar_hash_identificador_deterministico():
    base = generar_hash_identificador("expediente", "123")
    assert base == generar_hash_identificador("expediente", "123")
    assert base != generar_hash_identificador("expediente", "124")


def test_normalizar_numero_expediente_reemplaza_caracteres_no_seguros():
    assert normalizar_numero_expediente("1234/2023 - A") == "1234_2023_-_A"
    assert normalizar_numero_expediente(None) == "expediente"


def test_actualizar_metricas_descargas_en_json_recalcula_encabezado():
    actuales = [
        Actuacion(
            indice=1,
            oficina="Juzgado",
            fecha="2024-01-02",
            tipo="DEO",
            detalle="Notificación",
            tiene_archivo=True,
            archivo="https://ejemplo/uno.pdf",
            nombre_archivo="uno.pdf",
            tipo_archivo=".pdf",
            hash="hash1",
            extraida_en="2024-02-01T00:00:00Z",
            descargado=True,
        ).to_dict(),
        Actuacion(
            indice=2,
            oficina="Secretaría",
            fecha="2024-01-03",
            tipo="RESOLUCIÓN",
            detalle="Providencia",
            tiene_archivo=True,
            archivo="https://ejemplo/dos.pdf",
            nombre_archivo="dos.pdf",
            tipo_archivo=".pdf",
            hash="hash2",
            extraida_en="2024-02-01T00:00:00Z",
            descargado=False,
        ).to_dict(),
    ]

    payload = {
        "Expediente": {
            "Cantidad de Archivos Descargados": 0,
            "total_archivos_con_enlace": 0,
            "descargas_pendientes": 0,
        },
        "Actuaciones": actuales,
    }

    actualizar_metricas_descargas_en_json(payload)

    encabezado = payload["Expediente"]
    assert encabezado["Cantidad de Archivos Descargados"] == 1
    assert encabezado["total_archivos_con_enlace"] == 2
    assert encabezado["descargas_pendientes"] == 1


def test_to_iso_convierte_formato_dd_mm_yyyy():
    assert _to_iso("05/01/2024") == "2024-01-05"
    assert _to_iso("2024-01-05") == "2024-01-05"
    assert _to_iso("2024.01.05") is None


def test_parse_fechas_exactas_filtra_invalidas():
    fechas = _parse_fechas_exactas(["05/01/2024", "2024-01-06", "2024.01.07"])
    assert fechas == {"2024-01-05", "2024-01-06"}


def test_parse_fecha_limite_retorna_date_o_none():
    assert _parse_fecha_limite("05/01/2024").isoformat() == "2024-01-05"
    assert _parse_fecha_limite("2024.01.05") is None


def test_claves_historial_entradas_usan_normalizacion():
    entrada = {
        "numero": " 1234/2023 ",
        "fecha": "2024-01-05",
        "caratula": " Juicio ",
        "evento": "Aviso",
    }
    base_key = _base_key(entrada)
    event_key = _event_key(entrada)

    assert base_key == ("1234/2023", "2024-01-05", "juicio")
    assert event_key == ("1234/2023", "2024-01-05", "juicio", "Aviso")
