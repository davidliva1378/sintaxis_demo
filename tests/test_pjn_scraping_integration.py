from __future__ import annotations

import asyncio
import json
import sys
from types import SimpleNamespace
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import Sistema_v5.extractor_inicial.ciclo_prueba as ciclo_prueba
from Sistema_v5.pjn.models import Actuacion, ActuacionesArchivo, Entrada, ExpedienteResumen
from Sistema_v5.pjn.scraping import actuaciones, entradas, expedientes
from urls_pjn import URL_CONSULTAS


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "pjn"


def _load_fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_obtener_actuaciones_modelos_async_convierte_dicts(monkeypatch) -> None:
    payload = _load_fixture("actuacion.json")

    async def fake_colector(page, expediente_datos, carpeta_destino="Actuaciones"):
        return [payload], None, "/tmp/actuaciones"

    monkeypatch.setattr(
        actuaciones,
        "obtener_actuaciones_todas_paginas_async",
        fake_colector,
    )

    archivo, error, carpeta = asyncio.run(
        actuaciones.obtener_actuaciones_todas_paginas_modelos_async(
            page_expediente=None,
            expediente_datos={"numero": "12345/2023"},
            carpeta_destino="Actuaciones",
        )
    )

    assert error is None
    assert carpeta == "/tmp/actuaciones"
    assert isinstance(archivo, ActuacionesArchivo)
    assert archivo.actuaciones[0] == Actuacion.from_dict(payload)
    assert archivo.to_dict()["Actuaciones"][0]["Indice"] == payload["Indice"]


def test_extraer_expedientes_completos_modelos_envuelve_resumenes(monkeypatch) -> None:
    payload = _load_fixture("expediente_resumen.json")

    async def fake_extraer(page, *, mapper=None, **kwargs):
        resumen = ExpedienteResumen.from_dict(payload)
        resultado = mapper(resumen) if mapper is not None else resumen.to_dict()
        return [resultado], "completado", {"paginas_recorridas": 1}

    monkeypatch.setattr(expedientes, "extraer_expedientes_completos", fake_extraer)

    resultados, motivo, metadata = asyncio.run(
        expedientes.extraer_expedientes_completos_modelos(page=None)
    )

    assert motivo == "completado"
    assert metadata["paginas_recorridas"] == 1
    assert resultados == [ExpedienteResumen.from_dict(payload)]


def test_extraer_entradas_pjn_modelos_retorna_dataclasses(monkeypatch) -> None:
    payload = _load_fixture("entrada.json")

    async def fake_extraer(
        page,
        *,
        coleccion_modelos: list[Entrada],
        **kwargs,
    ) -> int:
        coleccion_modelos.append(Entrada.from_dict(payload))
        return 1

    monkeypatch.setattr(entradas, "extraer_entradas_pjn", fake_extraer)

    cantidad, modelos = asyncio.run(entradas.extraer_entradas_pjn_modelos(page=None))

    assert cantidad == 1
    assert modelos == [Entrada.from_dict(payload)]
    assert modelos[0].to_dict()["numero"] == payload["numero"]


class _DummyPage:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str | float]] = []

    async def goto(self, url: str) -> None:
        self.calls.append(("goto", url))

    async def wait_for_load_state(self, state: str) -> None:
        self.calls.append(("wait_for_load_state", state))


class _DummyAuthContext:
    def __init__(self, page: _DummyPage) -> None:
        self._page = page

    async def __aenter__(self) -> tuple[_DummyPage, None, None]:
        return self._page, None, None

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


def test_extraer_expedientes_iniciales_realiza_navegacion_previa(monkeypatch, tmp_path) -> None:
    page = _DummyPage()

    async def fake_sleep(delay: float) -> None:
        page.calls.append(("sleep", delay))

    def fake_obtener_pagina_autenticada(*, headless: bool):
        assert headless is True
        return _DummyAuthContext(page)

    async def fake_extraer(page, **kwargs):
        assert page.calls[0] == ("goto", URL_CONSULTAS)
        assert ("wait_for_load_state", "domcontentloaded") in page.calls
        return [], "ok", {}

    monkeypatch.setattr(ciclo_prueba.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(ciclo_prueba, "obtener_pagina_autenticada", fake_obtener_pagina_autenticada)
    monkeypatch.setattr(ciclo_prueba, "extraer_expedientes_completos_modelos", fake_extraer)

    system_config = SimpleNamespace(
        headless=True,
        directorio_extraccion_inicial=str(tmp_path),
        extraccion_expedientes_completa=True,
        expedientes_max_paginas=None,
        max_paginas_expedientes=None,
        expedientes_detener_duplicados=False,
        expedientes_orden=None,
        fecha_desde_expedientes=None,
        fecha_corte_expedientes=None,
        dias_atras_expedientes=None,
    )

    output_path = asyncio.run(
        ciclo_prueba._extraer_expedientes_iniciales(system_config, tmp_path)
    )

    assert output_path.exists()
    assert page.calls[0] == ("goto", URL_CONSULTAS)
    assert page.calls[1] == ("wait_for_load_state", "domcontentloaded")
