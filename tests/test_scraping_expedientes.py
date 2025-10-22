import asyncio
import sys
from pathlib import Path


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


def test_buscar_expedientes_normaliza_numero(monkeypatch, caplog):
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
        scraping_expedientes.buscar_expedientes(
            DummyPage(), numero="FPA 21002641/10/I"
        )
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
