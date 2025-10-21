"""Formulario temporal para gestionar historiales y selecciones del monitor PJN.

Este módulo ofrece una ventana sencilla basada en :mod:`tkinter` que carga los
listados de entradas y expedientes mediante los adaptadores existentes
(:func:`Sistema_v5.pjn.services.gui_monitor_adapter.cargar_historiales_monitor`
y :func:`Sistema_v5.pjn.services.gui_monitor_adapter.cargar_selecciones_monitor`).

Uso rápido
==========

Ejecutar el formulario directamente (usando la configuración por defecto)
::

    python -m Sistema_v5.ui.gui_monitor_form

O bien indicar una ruta de configuración explícita::

    python -m Sistema_v5.ui.gui_monitor_form --config config/monitor.json

También se incluye un punto de entrada temporal en :mod:`scripts.monitor_gui`
para facilitar la apertura desde la raíz del proyecto.

Ejemplo utilizando el script::

    python scripts/monitor_gui.py

Dependencias
============

* Python 3.11+
* ``tkinter`` (biblioteca estándar; en algunas distribuciones Linux puede
  requerir instalar ``python3-tk``)

La ventana y este script están pensados como una herramienta de desarrollo
provisional mientras se diseña la interfaz definitiva del monitor.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import tkinter as tk
from tkinter import messagebox

from Sistema_v5.pjn.models import Entrada, ExpedienteResumen
from Sistema_v5.pjn.services.gui_monitor_adapter import (
    cargar_historiales_monitor,
    cargar_selecciones_monitor,
    guardar_historiales_monitor,
    guardar_selecciones_monitor,
)


@dataclass(frozen=True, slots=True)
class _EntradaItem:
    """Elemento presentado en la lista de entradas."""

    id: str
    entrada: Entrada

    def render(self) -> str:
        estado = "✓" if self.entrada.leida else "✗"
        evento = f" · {self.entrada.evento}" if self.entrada.evento else ""
        return (
            f"[{estado}] {self.entrada.numero or '—'} — {self.entrada.caratula}"
            f" ({self.entrada.fecha}){evento}"
        )


@dataclass(frozen=True, slots=True)
class _ExpedienteItem:
    """Elemento presentado en la lista de expedientes."""

    id: str
    expediente: ExpedienteResumen

    def render(self) -> str:
        situacion = f" · {self.expediente.situacion}" if self.expediente.situacion else ""
        return (
            f"{self.expediente.numero or '—'} — {self.expediente.caratula}"
            f"{situacion}"
        )


class MonitorForm(tk.Tk):
    """Ventana principal para gestionar historiales y selecciones."""

    def __init__(self, config_path: Path | str) -> None:
        super().__init__()
        self.title("Monitor PJN – Historiales")
        self.minsize(980, 540)
        self.config_path = Path(config_path)

        self.entradas: list[Entrada]
        self.expedientes: list[ExpedienteResumen]
        self._entradas_items: list[_EntradaItem]
        self._expedientes_items: list[_ExpedienteItem]
        self._historial_dirty = False

        self._entradas_selected: set[str]
        self._expedientes_selected: set[str]

        self._entradas_listbox: tk.Listbox
        self._expedientes_listbox: tk.Listbox

        self._load_data()
        self._build_layout()

    # ------------------------------------------------------------------
    # Datos y estado
    # ------------------------------------------------------------------
    def _load_data(self) -> None:
        self.entradas, self.expedientes = cargar_historiales_monitor(self.config_path)
        entradas_ids, expedientes_ids = cargar_selecciones_monitor(self.config_path)

        entradas_selected = {str(_id) for _id in entradas_ids}
        expedientes_selected = {str(_id) for _id in expedientes_ids}

        self._entradas_items = [
            _EntradaItem(id=_infer_item_id(entrada.numero, idx, prefix="entrada"), entrada=entrada)
            for idx, entrada in enumerate(self.entradas)
        ]
        self._expedientes_items = [
            _ExpedienteItem(
                id=_infer_item_id(expediente.numero, idx, prefix="expediente"),
                expediente=expediente,
            )
            for idx, expediente in enumerate(self.expedientes)
        ]

        self._entradas_selected = entradas_selected
        self._expedientes_selected = expedientes_selected

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------
    def _build_layout(self) -> None:
        container = tk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(1, weight=1)

        entradas_label = tk.Label(container, text="Entradas del monitor", font=("TkDefaultFont", 11, "bold"))
        entradas_label.grid(row=0, column=0, sticky="w")

        expedientes_label = tk.Label(container, text="Expedientes conocidos", font=("TkDefaultFont", 11, "bold"))
        expedientes_label.grid(row=0, column=1, sticky="w")

        entradas_frame = tk.Frame(container)
        entradas_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 6))
        expedientes_frame = tk.Frame(container)
        expedientes_frame.grid(row=1, column=1, sticky="nsew", padx=(6, 0))

        self._entradas_listbox = self._create_listbox(entradas_frame)
        self._expedientes_listbox = self._create_listbox(expedientes_frame)

        self._populate_listbox(self._entradas_listbox, self._entradas_items, self._entradas_selected)
        self._populate_listbox(
            self._expedientes_listbox, self._expedientes_items, self._expedientes_selected
        )

        acciones_frame = tk.Frame(container)
        acciones_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        acciones_frame.columnconfigure(0, weight=1)
        acciones_frame.columnconfigure(1, weight=0)
        acciones_frame.columnconfigure(2, weight=0)
        acciones_frame.columnconfigure(3, weight=0)

        marcar_leidas_btn = tk.Button(
            acciones_frame,
            text="Marcar entradas seleccionadas como leídas",
            command=self._mark_selected_as_read,
        )
        marcar_leidas_btn.grid(row=0, column=0, sticky="w")

        marcar_no_leidas_btn = tk.Button(
            acciones_frame,
            text="Marcar entradas como no leídas",
            command=self._mark_selected_as_unread,
        )
        marcar_no_leidas_btn.grid(row=0, column=1, padx=(12, 0), sticky="w")

        guardar_btn = tk.Button(acciones_frame, text="Guardar selecciones", command=self._save_changes)
        guardar_btn.grid(row=0, column=2, padx=(12, 0))

        cerrar_btn = tk.Button(acciones_frame, text="Cerrar", command=self.destroy)
        cerrar_btn.grid(row=0, column=3, padx=(12, 0))

    def _create_listbox(self, parent: tk.Misc) -> tk.Listbox:
        frame = tk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True)

        listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE, activestyle="dotbox")
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.config(yscrollcommand=scrollbar.set)

        return listbox

    def _populate_listbox(
        self,
        listbox: tk.Listbox,
        items: list[_EntradaItem] | list[_ExpedienteItem],
        selected_ids: set[str],
    ) -> None:
        listbox.delete(0, tk.END)
        for index, item in enumerate(items):
            listbox.insert(tk.END, item.render())
            if item.id in selected_ids:
                listbox.selection_set(index)

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------
    def _mark_selected_as_read(self) -> None:
        indices = self._entradas_listbox.curselection()
        if not indices:
            messagebox.showinfo("Monitor PJN", "Seleccione al menos una entrada para actualizar su estado.")
            return
        for index in indices:
            entrada = self._entradas_items[index].entrada
            if not entrada.leida:
                entrada.leida = True  # type: ignore[misc]
                self._historial_dirty = True
        self._entradas_selected = set(self._gather_selections(self._entradas_listbox, self._entradas_items))
        self._populate_listbox(self._entradas_listbox, self._entradas_items, self._entradas_selected)

    def _mark_selected_as_unread(self) -> None:
        indices = self._entradas_listbox.curselection()
        if not indices:
            messagebox.showinfo("Monitor PJN", "Seleccione al menos una entrada para actualizar su estado.")
            return
        for index in indices:
            entrada = self._entradas_items[index].entrada
            if entrada.leida:
                entrada.leida = False  # type: ignore[misc]
                self._historial_dirty = True
        self._entradas_selected = set(self._gather_selections(self._entradas_listbox, self._entradas_items))
        self._populate_listbox(self._entradas_listbox, self._entradas_items, self._entradas_selected)

    def _gather_selections(
        self, listbox: tk.Listbox, items: list[_EntradaItem] | list[_ExpedienteItem]
    ) -> list[str]:
        return [items[index].id for index in listbox.curselection()]

    def _save_changes(self) -> None:
        entradas_ids = self._gather_selections(self._entradas_listbox, self._entradas_items)
        expedientes_ids = self._gather_selections(self._expedientes_listbox, self._expedientes_items)

        try:
            guardar_selecciones_monitor(
                self.config_path,
                entradas_ids=entradas_ids,
                expedientes_ids=expedientes_ids,
            )
            self._entradas_selected = set(entradas_ids)
            self._expedientes_selected = set(expedientes_ids)
            if self._historial_dirty:
                guardar_historiales_monitor(
                    self.config_path,
                    entradas=self.entradas,
                    expedientes=self.expedientes,
                )
                self._historial_dirty = False
            messagebox.showinfo("Monitor PJN", "Cambios guardados correctamente.")
        except Exception as exc:  # pragma: no cover - comunicación con UI
            messagebox.showerror("Monitor PJN", f"No fue posible guardar los cambios.\n{exc}")


# ----------------------------------------------------------------------
# Utilidades públicas
# ----------------------------------------------------------------------

def _infer_item_id(value: str | None, index: int, prefix: str) -> str:
    value = (value or "").strip()
    return value if value else f"{prefix}-{index}"


def launch_monitor_form(config_path: Path | str = Path("config/monitor.json")) -> None:
    """Inicia el formulario gráfico con la configuración indicada."""

    app = MonitorForm(config_path)
    app.mainloop()


def _build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Formulario de apoyo para el monitor PJN")
    parser.add_argument(
        "--config",
        default="config/monitor.json",
        type=Path,
        help="Ruta al archivo de configuración del monitor (monitor.json).",
    )
    return parser


def main() -> None:
    """Punto de entrada CLI usado cuando se ejecuta el módulo directamente."""

    parser = _build_argument_parser()
    args = parser.parse_args()
    launch_monitor_form(args.config)


if __name__ == "__main__":  # pragma: no cover - ejecución directa
    main()
