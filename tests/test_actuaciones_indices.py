import asyncio
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from Sistema_v4.actuaciones import actuaciones_v4 as extraccion_completa


def test_historicas_continuan_numeracion(monkeypatch, tmp_path):
    async def fake_obtener_actuaciones(_, __, carpeta_destino=""):
        return (
            [
                {"Indice": 1, "TieneArchivo": False},
                {"Indice": 2, "TieneArchivo": False},
            ],
            None,
            str(tmp_path),
        )

    llamado = {}

    async def fake_extraer_historicas(_, __, indice_inicial=1):
        llamado["indice_inicial"] = indice_inicial
        return (
            [
                {"Indice": indice_inicial, "TieneArchivo": False},
                {"Indice": indice_inicial + 1, "TieneArchivo": False},
            ],
            None,
        )

    monkeypatch.setattr(
        extraccion_completa,
        "obtener_actuaciones_todas_paginas_async",
        fake_obtener_actuaciones,
    )
    monkeypatch.setattr(
        extraccion_completa,
        "extraer_actuaciones_historicas",
        fake_extraer_historicas,
    )

    expediente = {
        "numero": "123/2020",
        "caratula": "",
        "dependencia": "",
        "jurisdiccion": "",
        "situacion": "",
    }

    async def ejecutar_prueba():
        actuales, historicas, error = await extraccion_completa.extraer_actuaciones_completas(
            page_expediente=None,
            expediente_datos=expediente,
            incluir_historicas=True,
            directorio_base=str(tmp_path),
        )

        assert error is None
        assert llamado["indice_inicial"] == len(actuales) + 1
        assert historicas[0]["Indice"] == len(actuales) + 1
        assert historicas[1]["Indice"] == len(actuales) + 2

    asyncio.run(ejecutar_prueba())

