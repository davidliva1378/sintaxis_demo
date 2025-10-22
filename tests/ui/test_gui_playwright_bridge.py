import asyncio
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from Sistema_v5.pjn.models import ExpedienteResumen
from Sistema_v5.ui import gui_playwright_bridge
from Sistema_v5.ui.gui_playwright_bridge import (
    ExpedienteNotFoundError,
    GUIPlaywrightBridge,
)
from extractor_inicial.services import procesamiento as procesamiento_module


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_build_payload_prioriza_caratula(monkeypatch, caplog):
    bridge = GUIPlaywrightBridge()
    bridge._lock = asyncio.Lock()
    sentinel_page = object()

    async def fake_get_page(self):
        return sentinel_page

    async def fake_ensure_consultas(self):
        return None

    monkeypatch.setattr(GUIPlaywrightBridge, "_get_page", fake_get_page, raising=True)
    monkeypatch.setattr(
        GUIPlaywrightBridge,
        "_ensure_consultas_page",
        fake_ensure_consultas,
        raising=True,
    )

    async def fake_buscar(page, numero=None, anio=None, caratula=None):
        assert caratula == "Carátula Única"
        return [object(), object()]

    async def fake_mostrar(
        page,
        filas,
        *,
        estrategia_seleccion=None,
        descripcion_estrategia=None,
    ):
        assert estrategia_seleccion is not None
        assert descripcion_estrategia == "coincidencia exacta por carátula"
        opciones = [
            {"caratula": "Otro expediente"},
            {"caratula": "Carátula Única"},
        ]
        indice = estrategia_seleccion(opciones)
        assert indice == 1
        return {"numero": "12345/2020", "caratula": "Carátula Única"}

    monkeypatch.setattr(gui_playwright_bridge, "buscar_expedientes", fake_buscar)
    monkeypatch.setattr(
        gui_playwright_bridge,
        "mostrar_y_elegir_expediente",
        fake_mostrar,
    )

    expediente = ExpedienteResumen(
        numero="12345/2020",
        dependencia="Juzgado",
        caratula="Carátula Única",
        situacion=None,
        ultima_actuacion=None,
    )

    caplog.set_level("WARNING", logger=gui_playwright_bridge.logger.name)

    datos = await bridge._build_payload(expediente)

    assert datos["numero"] == "12345/2020"
    assert any("múltiples filas" in record.message for record in caplog.records)


class _DummyBridge:
    def __init__(self, *_, **__):
        self._behaviors: dict[str, object] = {}
        self.started = False
        self.closed = False

    def configure(self, behaviors: dict[str, object]) -> None:
        self._behaviors = behaviors

    def start(self) -> None:
        self.started = True

    def close(self) -> None:
        self.closed = True

    def get_expediente_payload(self, expediente: ExpedienteResumen):
        resultado = self._behaviors[expediente.numero]
        if isinstance(resultado, Exception):
            raise resultado
        return resultado

    def run_coroutine(self, coro):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


def test_procesar_expedientes_reporta_no_encontrados(monkeypatch):
    dummy_bridge = _DummyBridge()

    def bridge_factory(*args, **kwargs):
        dummy_bridge.configure(
            {
                "1/2020": {"numero": "1/2020", "caratula": "Uno"},
                "2/2020": ExpedienteNotFoundError(
                    "El expediente 2/2020 no fue encontrado en el portal."
                ),
            }
        )
        return dummy_bridge

    async def fake_procesar_actuaciones(datos, *, descargar_adjuntos):
        return (
            "carpeta/1-2020.json",
            {
                "descargas_ejecutadas": False,
                "carpeta_expediente": "expedientes/1",
                "carpeta_json": "json/1",
                "carpeta_actuaciones": "actuaciones/1",
                "carpeta_adjuntos": "adjuntos/1",
            },
        )

    monkeypatch.setattr(
        procesamiento_module,
        "procesar_actuaciones_expediente",
        fake_procesar_actuaciones,
    )
    monkeypatch.setattr(
        procesamiento_module,
        "GUIPlaywrightBridge",
        bridge_factory,
    )

    seleccion = [
        ExpedienteResumen("1/2020", "Juzgado", "Uno"),
        ExpedienteResumen("2/2020", "Juzgado", "Dos"),
    ]

    resumen = procesamiento_module.procesar_expedientes_iniciales(
        seleccion,
        headless=True,
        descargar_adjuntos=False,
    )

    assert resumen["no_encontrados"] == [seleccion[1].to_dict()]
    assert resumen["con_error"] == 1
    assert resumen["exitosos"] == 1
    assert dummy_bridge.closed is True
