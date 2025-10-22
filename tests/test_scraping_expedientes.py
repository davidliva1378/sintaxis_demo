import asyncio
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from Sistema_v5.pjn.scraping.base import descomponer_numero_expediente
from Sistema_v5.pjn.scraping import expedientes as scraping_expedientes


def test_descomponer_numero_expediente_variantes():
    casos = {
        "FPA 21002641/2010": (None, "21002641", "2010"),
        "3-21002641-23": ("3", "21002641", "2023"),
        "21002641/2010/I": (None, "21002641", "2010"),
        "FPA1945/2024/1": (None, "1945", "2024"),
        "FPA 1945/2024/1": (None, "1945", "2024"),
        "Expte: 12345/024": (None, "12345", "2024"),
    }

    for valor, esperado in casos.items():
        assert descomponer_numero_expediente(valor) == esperado


class DummyRow:
    async def query_selector_all(self, selector):
        return []


class DummyTable:
    async def query_selector_all(self, selector):
        assert selector == "tbody tr"
        return [DummyRow()]


class DummyPage:
    async def query_selector(self, selector):
        assert selector == "table.table-striped"
        return DummyTable()


class DummyColumnWithText:
    def __init__(self, texto):
        self._texto = texto

    async def inner_text(self):
        return self._texto


class DummyRowCaratula:
    def __init__(self, caratula):
        self.caratula = caratula
        self._columnas = [
            DummyColumnWithText("columna 1"),
            DummyColumnWithText("columna 2"),
            DummyColumnWithText(caratula),
        ]

    async def query_selector_all(self, selector):
        assert selector == scraping_expedientes.SEL_EXPEDIENTES.COLUMNAS_FILA
        return self._columnas


class DummyTableCaratula:
    def __init__(self, filas):
        self._filas = filas

    async def query_selector_all(self, selector):
        assert selector == "tbody tr"
        return self._filas


class DummyPageCaratula:
    def __init__(self, filas):
        self._tabla = DummyTableCaratula(filas)

    async def query_selector(self, selector):
        assert selector == "table.table-striped"
        return self._tabla


@pytest.mark.parametrize(
    "entrada",
    [
        "FPA 21002641/10/I",
        "FPA 21002641/10/1",
    ],
)
def test_buscar_expedientes_normaliza_numero(monkeypatch, caplog, entrada):
    llamado: dict[str, tuple[str, str, int]] = {}

    async def fake_buscar(page, numero, anio, timeout=8000):
        llamado["args"] = (numero, anio, timeout)
        return True, "OK"

    monkeypatch.setattr(
        scraping_expedientes,
        "buscar_expediente_por_numero",
        fake_buscar,
    )

    caplog.set_level("ERROR")

    filas = asyncio.run(
        scraping_expedientes.buscar_expedientes(DummyPage(), numero=entrada)
    )

    assert llamado["args"] == ("21002641", "2010", 8000)
    assert not caplog.records
    assert filas and isinstance(filas[0], DummyRow)


def test_buscar_expedientes_numero_invalido_registra_error(monkeypatch, caplog):
    async def fail(*args, **kwargs):  # pragma: no cover - no debería llamarse
        raise AssertionError("La búsqueda por número no debería ejecutarse")

    monkeypatch.setattr(
        scraping_expedientes,
        "buscar_expediente_por_numero",
        fail,
    )

    caplog.set_level("ERROR")

    filas = asyncio.run(
        scraping_expedientes.buscar_expedientes(
            DummyPage(), numero="FPA"
        )
    )

    assert filas == []
    assert any("No se pudo interpretar el número de expediente" in r.message for r in caplog.records)


def test_buscar_expedientes_filtra_caratula_normalizada(monkeypatch, caplog):
    filas = [
        DummyRowCaratula("Juicio Alvarez  S.A. s/ Daños"),
        DummyRowCaratula("Expediente Diferente"),
    ]

    async def fake_buscar(page, numero, anio, timeout=8_000):
        return True, "OK"

    monkeypatch.setattr(
        scraping_expedientes,
        "buscar_expediente_por_numero",
        fake_buscar,
    )
    monkeypatch.setattr(
        scraping_expedientes._config.scraping,
        "caratula_coincidencia_parcial",
        True,
    )

    caplog.set_level("DEBUG", logger=scraping_expedientes.logger.name)

    pagina = DummyPageCaratula(filas)
    resultado = asyncio.run(
        scraping_expedientes.buscar_expedientes(
            pagina,
            numero="12345",
            anio="2023",
            caratula="JUICIO ÁLVAREZ  S.A.",
        )
    )

    assert resultado == [filas[0]]
    assert any(
        "Fila descartada tras normalizar carátula" in registro.message
        for registro in caplog.records
    )
