"""Pruebas ligeras para el formulario del monitor PJN."""
from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from Sistema_v5.pjn.monitor.storage_selecciones import SeleccionesStorageManager
from Sistema_v5.ui import gui_monitor_form
from Sistema_v5.ui.gui_monitor_form import MonitorForm


class _FakeListbox:
    def __init__(self, selected: tuple[int, ...] = ()) -> None:
        self._selected = selected
        self.items: list[str] = []
        self.selection_calls: list[int] = []

    def delete(self, _start: int, _end: object) -> None:
        self.items.clear()

    def insert(self, _index: int, value: str) -> None:
        self.items.append(value)

    def selection_set(self, index: int) -> None:
        self.selection_calls.append(index)

    def curselection(self) -> tuple[int, ...]:
        return self._selected

    def set_selection(self, selection: tuple[int, ...]) -> None:
        self._selected = selection


@pytest.fixture(autouse=True)
def _silence_messagebox(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("showinfo", "showwarning", "showerror"):
        monkeypatch.setattr(getattr(gui_monitor_form, "messagebox"), name, lambda *args, **kwargs: None)


@pytest.fixture
def monitor_environment(tmp_path: Path) -> tuple[Path, Path]:
    data_dir = tmp_path / "datos_monitor"
    data_dir.mkdir(parents=True, exist_ok=True)
    config_path = tmp_path / "monitor.json"
    config_path.write_text(
        json.dumps({"directorio_datos": str(data_dir)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return config_path, data_dir


@pytest.fixture
def entrada_fixture() -> dict:
    fixture_path = Path("tests/fixtures/pjn/entrada.json")
    return json.loads(fixture_path.read_text(encoding="utf-8"))


@pytest.fixture
def expediente_fixture() -> dict:
    fixture_path = Path("tests/fixtures/pjn/expediente_resumen.json")
    return json.loads(fixture_path.read_text(encoding="utf-8"))


def _write_historiales(data_dir: Path, entrada: dict, expediente: dict) -> None:
    (data_dir / "historial_entradas.json").write_text(
        json.dumps([entrada], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (data_dir / "historial_expedientes.json").write_text(
        json.dumps([expediente], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def test_monitor_form_loads_previous_selections(
    monitor_environment: tuple[Path, Path],
    entrada_fixture: dict,
    expediente_fixture: dict,
) -> None:
    config_path, data_dir = monitor_environment
    _write_historiales(data_dir, entrada_fixture, expediente_fixture)

    storage = SeleccionesStorageManager(data_dir)
    storage.guardar_selecciones(
        entradas_ids=[entrada_fixture["numero"]],
        expedientes_ids=[expediente_fixture["numero"]],
    )

    form = MonitorForm.__new__(MonitorForm)
    form.config_path = config_path
    form._selecciones_loader = gui_monitor_form.cargar_selecciones_monitor
    form._selecciones_saver = gui_monitor_form.guardar_selecciones_monitor
    form._historial_dirty = False

    MonitorForm._load_data(form)

    assert form._entradas_selected == {entrada_fixture["numero"]}
    assert form._expedientes_selected == {expediente_fixture["numero"]}

    entradas_listbox = _FakeListbox()
    form._populate_listbox(entradas_listbox, form._entradas_items, form._entradas_selected)
    assert entradas_listbox.selection_calls == [0]

    expedientes_listbox = _FakeListbox()
    form._populate_listbox(expedientes_listbox, form._expedientes_items, form._expedientes_selected)
    assert expedientes_listbox.selection_calls == [0]


def test_monitor_form_persists_current_selections(
    monitor_environment: tuple[Path, Path],
    entrada_fixture: dict,
    expediente_fixture: dict,
) -> None:
    config_path, data_dir = monitor_environment
    _write_historiales(data_dir, entrada_fixture, expediente_fixture)

    form = MonitorForm.__new__(MonitorForm)
    form.config_path = config_path
    form._selecciones_loader = gui_monitor_form.cargar_selecciones_monitor
    form._selecciones_saver = gui_monitor_form.guardar_selecciones_monitor
    form._historial_dirty = False

    MonitorForm._load_data(form)

    entradas_listbox = _FakeListbox(selected=(0,))
    expedientes_listbox = _FakeListbox(selected=(0,))
    form._entradas_listbox = entradas_listbox
    form._expedientes_listbox = expedientes_listbox

    assert form._persist_selecciones(show_success=False) is True
    assert form._entradas_selected == {entrada_fixture["numero"]}
    assert form._expedientes_selected == {expediente_fixture["numero"]}

    storage = SeleccionesStorageManager(data_dir)
    entradas_ids, expedientes_ids = storage.cargar_selecciones()

    assert entradas_ids == [entrada_fixture["numero"]]
    assert expedientes_ids == [expediente_fixture["numero"]]
