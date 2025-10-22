"""Pruebas para el servicio de procesamiento de actuaciones."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from Sistema_v5.pjn.scraping import normalizar_numero_expediente
from Sistema_v5.pjn.services import actuaciones


class DummyGestor:
    """Gestor simplificado que crea el árbol esperado bajo un tmp_path."""

    def __init__(self, base: Path) -> None:
        self.raiz = base

    def crear_para_expediente(self, numero: str) -> tuple[Path, dict]:
        destino = self.raiz / normalizar_numero_expediente(numero)
        (destino / "actuaciones" / "adjuntos").mkdir(parents=True, exist_ok=True)
        (destino / "json").mkdir(parents=True, exist_ok=True)
        return destino, {"directories": []}


def test_procesar_actuaciones_generates_json_and_downloads(monkeypatch, tmp_path):
    dummy_gestor = DummyGestor(tmp_path / "expedientes")
    dummy_gestor.raiz.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(
        actuaciones,
        "GestorDirectoriosExpedientes",
        SimpleNamespace(desde_config=lambda *args, **kwargs: dummy_gestor),
    )

    async def fake_extraer(page_expediente, expediente_datos, incluir_historicas, directorio_base):
        numero = normalizar_numero_expediente(expediente_datos["numero"])
        carpeta = Path(directorio_base) / numero
        carpeta.mkdir(parents=True, exist_ok=True)
        archivo = carpeta / f"actuaciones-{numero}.json"
        archivo.write_text(json.dumps({"Actuaciones": []}), encoding="utf-8")
        return ([{"id": 1}], [{"id": 2}], None)

    descargar_mock = AsyncMock()

    monkeypatch.setattr(actuaciones, "extraer_actuaciones_completas", fake_extraer)
    monkeypatch.setattr(actuaciones, "descargar_archivos_de_json", descargar_mock)

    datos = {"numero": "123/2023", "page": object()}

    json_path, resumen = asyncio.run(
        actuaciones.procesar_actuaciones_expediente(
            datos,
            descargar_adjuntos=True,
        )
    )

    assert json_path is not None
    assert json_path.exists()
    assert resumen["actuaciones_actuales"] == 1
    assert resumen["actuaciones_historicas"] == 1
    assert resumen["descargas_ejecutadas"] is True
    assert resumen["error"] is None
    expected_adjuntos = resumen["carpeta_adjuntos"]
    assert expected_adjuntos is not None
    descargar_mock.assert_awaited_once_with(
        datos["page"],
        str(json_path.parent),
        expected_adjuntos,
    )
    assert resumen["carpeta_json"] == str(json_path.parent)
    assert resumen["carpeta_actuaciones"].endswith("actuaciones")
    assert resumen["carpeta_adjuntos"].endswith("actuaciones/adjuntos")

    # Idempotencia: una segunda ejecución debe reutilizar la estructura sin errores
    descargar_mock.reset_mock()
    json_path_second, resumen_second = asyncio.run(
        actuaciones.procesar_actuaciones_expediente(
            datos,
            descargar_adjuntos=True,
        )
    )

    assert json_path_second == json_path
    assert resumen_second["actuaciones_actuales"] == 1
    assert resumen_second["actuaciones_historicas"] == 1
    expected_adjuntos_second = resumen_second["carpeta_adjuntos"]
    assert expected_adjuntos_second == expected_adjuntos
    descargar_mock.assert_awaited_once_with(
        datos["page"],
        str(json_path.parent),
        expected_adjuntos_second,
    )


def test_procesar_actuaciones_no_descarga_si_hay_error(monkeypatch, tmp_path):
    dummy_gestor = DummyGestor(tmp_path / "expedientes")
    dummy_gestor.raiz.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(
        actuaciones,
        "GestorDirectoriosExpedientes",
        SimpleNamespace(desde_config=lambda *args, **kwargs: dummy_gestor),
    )

    async def fake_extraer(*_args, **_kwargs):
        return [], [], "error controlado"

    descargar_mock = AsyncMock()

    monkeypatch.setattr(actuaciones, "extraer_actuaciones_completas", fake_extraer)
    monkeypatch.setattr(actuaciones, "descargar_archivos_de_json", descargar_mock)

    json_path, resumen = asyncio.run(
        actuaciones.procesar_actuaciones_expediente(
            {"numero": "555/2020", "page": object()},
            descargar_adjuntos=True,
        )
    )

    assert json_path is None
    assert resumen["error"] == "error controlado"
    assert resumen["descargas_ejecutadas"] is False
    descargar_mock.assert_not_awaited()


def test_procesar_actuaciones_valida_parametros():
    with pytest.raises(TypeError):
        asyncio.run(
            actuaciones.procesar_actuaciones_expediente("no es dict")  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError):
        asyncio.run(actuaciones.procesar_actuaciones_expediente({}))
