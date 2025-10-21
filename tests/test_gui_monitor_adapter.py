"""Pruebas para el adaptador de historiales del monitor."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from Sistema_v5.pjn.models import Entrada, ExpedienteResumen
from Sistema_v5.pjn.services.gui_monitor_adapter import (
    cargar_historiales_monitor,
    guardar_historiales_monitor,
    cargar_selecciones_monitor,
    guardar_selecciones_monitor,
)


@pytest.fixture
def monitor_config(tmp_path: Path) -> Path:
    """Crea un archivo de configuración que apunta al directorio temporal."""
    data_dir = tmp_path / "datos_monitor"
    config_path = tmp_path / "monitor.json"
    config_path.write_text(
        json.dumps({"directorio_datos": str(data_dir)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return config_path


@pytest.fixture
def entrada_fixture() -> dict:
    fixture_path = Path("tests/fixtures/pjn/entrada.json")
    return json.loads(fixture_path.read_text(encoding="utf-8"))


@pytest.fixture
def expediente_fixture() -> dict:
    fixture_path = Path("tests/fixtures/pjn/expediente_resumen.json")
    return json.loads(fixture_path.read_text(encoding="utf-8"))


def test_cargar_historiales_monitor(
    tmp_path: Path,
    monitor_config: Path,
    entrada_fixture: dict,
    expediente_fixture: dict,
) -> None:
    """Debe devolver instancias de ``Entrada`` y ``ExpedienteResumen`` listas para la GUI."""
    data_dir = tmp_path / "datos_monitor"
    data_dir.mkdir(parents=True, exist_ok=True)

    (data_dir / "historial_entradas.json").write_text(
        json.dumps([entrada_fixture], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (data_dir / "historial_expedientes.json").write_text(
        json.dumps([expediente_fixture], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    entradas, expedientes = cargar_historiales_monitor(monitor_config)

    assert entradas == [Entrada.from_dict(entrada_fixture)]
    assert expedientes == [ExpedienteResumen.from_dict(expediente_fixture)]


def test_guardar_historiales_monitor(
    tmp_path: Path,
    monitor_config: Path,
    entrada_fixture: dict,
    expediente_fixture: dict,
) -> None:
    """Debe persistir los historiales usando la ruta configurada."""
    entrada = Entrada.from_dict(entrada_fixture)
    expediente = ExpedienteResumen.from_dict(expediente_fixture)

    guardar_historiales_monitor(monitor_config, [entrada], [expediente])

    data_dir = tmp_path / "datos_monitor"
    entradas_path = data_dir / "historial_entradas.json"
    expedientes_path = data_dir / "historial_expedientes.json"

    assert json.loads(entradas_path.read_text(encoding="utf-8")) == [entrada.to_dict()]
    assert json.loads(expedientes_path.read_text(encoding="utf-8")) == [expediente.to_dict()]


def test_cargar_selecciones_monitor(tmp_path: Path, monitor_config: Path) -> None:
    """Debe recuperar las selecciones almacenadas para la interfaz."""

    data_dir = tmp_path / "datos_monitor"
    data_dir.mkdir(parents=True, exist_ok=True)
    selecciones = {
        "entradas_ids": ["ENT-1", 42],
        "expedientes_ids": ["EXP-7"],
    }
    (data_dir / "selecciones_monitor.json").write_text(
        json.dumps(selecciones, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    entradas_ids, expedientes_ids = cargar_selecciones_monitor(monitor_config)

    assert entradas_ids == ["ENT-1", "42"]
    assert expedientes_ids == ["EXP-7"]


def test_guardar_selecciones_monitor(tmp_path: Path, monitor_config: Path) -> None:
    """Debe persistir las selecciones realizadas en la GUI."""

    guardar_selecciones_monitor(
        monitor_config,
        entradas_ids=["ENT-9", 1234],
        expedientes_ids=["EXP-55"],
    )

    data_dir = tmp_path / "datos_monitor"
    selecciones_path = data_dir / "selecciones_monitor.json"

    data = json.loads(selecciones_path.read_text(encoding="utf-8"))
    assert data == {
        "entradas_ids": ["ENT-9", "1234"],
        "expedientes_ids": ["EXP-55"],
    }
