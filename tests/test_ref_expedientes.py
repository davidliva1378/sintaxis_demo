from pathlib import Path
import sys
import asyncio

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from Sistema_v3.operaciones.expedientes import ref_expedientes


def test_buscar_expedientes_con_numero_y_anio(monkeypatch):
    llamado = {}

    async def fake_buscar_expediente(page, numero, anio, timeout=8000):
        llamado["args"] = (numero, anio, timeout)
        return True, "OK"

    monkeypatch.setattr(
        ref_expedientes, "buscar_expediente_por_numero", fake_buscar_expediente
    )

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

    filas = asyncio.run(
        ref_expedientes.buscar_expedientes(DummyPage(), numero=" 123 ", anio="2023  ")
    )

    assert llamado["args"] == ("123", "2023", 8000)
    assert len(filas) == 1
    assert isinstance(filas[0], DummyRow)


def test_buscar_expedientes_sin_numero(capsys):
    filas = asyncio.run(ref_expedientes.buscar_expedientes(object(), anio="2023"))
    assert filas == []

    salida = capsys.readouterr().out
    assert "Para buscar por año" in salida


def test_buscar_expedientes_solo_caratula(monkeypatch):
    async def fake_buscar_por_caratula(page, caratula):
        assert caratula == "Carátula de prueba"
        return ["fila"]

    async def fail(*args, **kwargs):
        raise AssertionError("No debería llamarse la búsqueda por número")

    monkeypatch.setattr(
        ref_expedientes, "buscar_expedientes_por_caratula", fake_buscar_por_caratula
    )
    monkeypatch.setattr(ref_expedientes, "buscar_expediente_por_numero", fail)

    filas = asyncio.run(
        ref_expedientes.buscar_expedientes(object(), caratula="Carátula de prueba")
    )

    assert filas == ["fila"]
