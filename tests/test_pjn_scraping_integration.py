from __future__ import annotations

import json
import asyncio
from pathlib import Path
from typing import Any

from Sistema_v5.pjn.models import Actuacion, ActuacionesArchivo, Entrada, ExpedienteResumen
from Sistema_v5.pjn.scraping import actuaciones, entradas, expedientes


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
