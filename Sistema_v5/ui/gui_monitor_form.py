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

Si se prefiere omitir el archivo de configuración, es posible apuntar
directamente al directorio con los ``historial_*.json`` y ``selecciones.json``::

    python -m Sistema_v5.ui.gui_monitor_form --datos Sistema_v5/data/monitor

También se incluye un punto de entrada temporal en :mod:`scripts.monitor_gui`
para facilitar la apertura desde la raíz del proyecto.

Ejemplo utilizando el script::

    python scripts/monitor_gui.py

Si los historiales no aparecen automáticamente al iniciar la interfaz, utilice
el botón «Cargar historiales…» para seleccionar manualmente los archivos
``historial_entradas.json`` y ``historial_expedientes.json`` almacenados, por
ejemplo, en ``Sistema_v5/data/monitor``.

Dependencias
============

* Python 3.11+
* ``tkinter`` (biblioteca estándar; en algunas distribuciones Linux puede
  requerir instalar ``python3-tk``)

La ventana y este script están pensados como una herramienta de desarrollo
provisional mientras se diseña la interfaz definitiva del monitor.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Callable, Iterable, Literal

from Sistema_v5.configuracion.monitor.config import MonitorConfig
from Sistema_v5.configuracion.monitor.exceptions import StorageError
from Sistema_v5.pjn.models import Entrada, ExpedienteResumen
from Sistema_v5.pjn.services.gui_monitor_adapter import (
    cargar_historiales_desde_directorio,
    cargar_historiales_monitor,
    cargar_selecciones_desde_directorio,
    cargar_selecciones_monitor,
    guardar_historiales_en_directorio,
    guardar_historiales_monitor,
    guardar_selecciones_en_directorio,
    guardar_selecciones_monitor,
)
from Sistema_v5.pjn.services import ResultadoProcesamiento, procesar_actuaciones_expediente
from Sistema_v5.ui.gui_playwright_bridge import (
    GUIPlaywrightBridge,
    ExpedienteNavigationError,
    ExpedienteNotFoundError,
    PlaywrightBridgeError,
    PlaywrightSessionError,
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

    def __init__(
        self,
        config_path: Path | str,
        datos_dir: Path | str | None = None,
        expediente_payload_factory: Callable[[ExpedienteResumen], dict[str, object]] | None = None,
        playwright_bridge: GUIPlaywrightBridge | None = None,
        historiales_loader: Callable[[Path | str], tuple[list[Entrada], list[ExpedienteResumen]]] = cargar_historiales_monitor,
        historiales_saver: Callable[[Path | str, Iterable[Entrada] | None, Iterable[ExpedienteResumen] | None], None] = guardar_historiales_monitor,
        selecciones_loader: Callable[[Path | str], tuple[list[str], list[str]]] = cargar_selecciones_monitor,
        selecciones_saver: Callable[[Path | str, Iterable[object] | None, Iterable[object] | None], None] = guardar_selecciones_monitor,
    ) -> None:
        super().__init__()
        self.title("Monitor PJN – Historiales")
        self.minsize(980, 540)
        self.config_path = Path(config_path)
        self._datos_dir = Path(datos_dir) if datos_dir is not None else None
        self._storage_target: Path = self._datos_dir or self.config_path
        self._historiales_loader = historiales_loader
        self._historiales_saver = historiales_saver
        self._expediente_payload_factory: Callable[[ExpedienteResumen], dict[str, object]] | None = (
            expediente_payload_factory
        )
        self._playwright_bridge = playwright_bridge
        self._selecciones_loader = selecciones_loader
        self._selecciones_saver = selecciones_saver

        self.entradas: list[Entrada]
        self.expedientes: list[ExpedienteResumen]
        self._entradas_items: list[_EntradaItem]
        self._expedientes_items: list[_ExpedienteItem]
        self._historial_dirty = False

        self._entradas_selected: set[str]
        self._expedientes_selected: set[str]

        self._entradas_listbox: tk.Listbox
        self._expedientes_listbox: tk.Listbox
        self._procesar_btn: tk.Button
        self._abrir_carpeta_btn: tk.Button
        self._resultados_listbox: tk.Listbox
        self._descargar_adjuntos_var = tk.BooleanVar(value=False)

        self._processing_queue: queue.Queue[_ProcessingEvent] = queue.Queue()
        self._processing_thread: threading.Thread | None = None
        self._processing_active = False
        self._resultados_items: list[_ResultadoItem] = []

        self._entradas_manual_path: Path | None = None
        self._expedientes_manual_path: Path | None = None

        self._load_data()
        self._build_layout()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(200, self._poll_processing_queue)

    # ------------------------------------------------------------------
    # Datos y estado
    # ------------------------------------------------------------------
    def _load_data(self) -> None:
        try:
            entradas, expedientes = self._historiales_loader(self._storage_target)
        except StorageError as exc:  # pragma: no cover - comunicación con UI real
            messagebox.showerror(
                "Monitor PJN",
                "No fue posible cargar los historiales almacenados.\n"
                f"Detalle: {exc}",
            )
            entradas, expedientes = [], []
        except Exception as exc:  # pragma: no cover - comunicación con UI real
            messagebox.showerror(
                "Monitor PJN",
                "Ocurrió un error inesperado al cargar los historiales.\n"
                f"Detalle: {exc}",
            )
            entradas, expedientes = [], []

        self.entradas, self.expedientes = entradas, expedientes
        entradas_selected, expedientes_selected = self._load_selecciones()

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
        acciones_frame.columnconfigure(0, weight=0)
        acciones_frame.columnconfigure(1, weight=1)
        acciones_frame.columnconfigure(2, weight=0)
        acciones_frame.columnconfigure(3, weight=0)
        acciones_frame.columnconfigure(4, weight=0)
        acciones_frame.columnconfigure(5, weight=0)

        cargar_historiales_btn = tk.Button(
            acciones_frame,
            text="Cargar historiales…",
            command=self._prompt_manual_historial_load,
        )
        cargar_historiales_btn.grid(row=0, column=0, padx=(0, 12), sticky="w")

        marcar_leidas_btn = tk.Button(
            acciones_frame,
            text="Marcar entradas seleccionadas como leídas",
            command=self._mark_selected_as_read,
        )
        marcar_leidas_btn.grid(row=0, column=1, sticky="w")

        marcar_no_leidas_btn = tk.Button(
            acciones_frame,
            text="Marcar entradas como no leídas",
            command=self._mark_selected_as_unread,
        )
        marcar_no_leidas_btn.grid(row=0, column=2, padx=(12, 0), sticky="w")

        self._procesar_btn = tk.Button(
            acciones_frame,
            text="Procesar expediente(s)",
            command=self._process_selected_expedientes,
        )
        self._procesar_btn.grid(row=0, column=3, padx=(12, 0))

        guardar_btn = tk.Button(acciones_frame, text="Guardar selecciones", command=self._save_changes)
        guardar_btn.grid(row=0, column=4, padx=(12, 0))

        cerrar_btn = tk.Button(acciones_frame, text="Cerrar", command=self._on_close)
        cerrar_btn.grid(row=0, column=5, padx=(12, 0))

        opciones_frame = tk.Frame(container)
        opciones_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        opciones_frame.columnconfigure(0, weight=1)

        descargar_adjuntos_chk = tk.Checkbutton(
            opciones_frame,
            text="Descargar adjuntos",
            variable=self._descargar_adjuntos_var,
        )
        descargar_adjuntos_chk.grid(row=0, column=0, sticky="w")

        resultados_label = tk.Label(
            container,
            text="Resultados del procesamiento",
            font=("TkDefaultFont", 11, "bold"),
        )
        resultados_label.grid(row=4, column=0, columnspan=2, sticky="w", pady=(12, 0))

        resultados_frame = tk.Frame(container)
        resultados_frame.grid(row=5, column=0, columnspan=2, sticky="nsew")
        container.rowconfigure(5, weight=1)

        self._resultados_listbox = tk.Listbox(resultados_frame, activestyle="dotbox")
        self._resultados_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        resultados_scrollbar = tk.Scrollbar(
            resultados_frame, orient=tk.VERTICAL, command=self._resultados_listbox.yview
        )
        resultados_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._resultados_listbox.config(yscrollcommand=resultados_scrollbar.set)

        botones_resultados = tk.Frame(container)
        botones_resultados.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(6, 0))

        self._abrir_carpeta_btn = tk.Button(
            botones_resultados,
            text="Abrir carpeta del expediente",
            command=self._open_selected_result_folder,
            state=tk.DISABLED,
        )
        self._abrir_carpeta_btn.grid(row=0, column=0, sticky="w")

        self._resultados_listbox.bind("<<ListboxSelect>>", self._on_result_selection)

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

    def _prompt_manual_historial_load(self) -> None:  # pragma: no cover - interacción UI
        if (
            self._entradas_manual_path
            and self._expedientes_manual_path
            and self._entradas_manual_path.exists()
            and self._expedientes_manual_path.exists()
        ):
            if messagebox.askyesno(
                "Monitor PJN",
                "¿Desea recargar los historiales desde los últimos archivos seleccionados?",
            ):
                self._load_historiales_desde_archivos(
                    self._entradas_manual_path, self._expedientes_manual_path
                )
                return

        initial_dir: Path | None
        if self._entradas_manual_path and self._entradas_manual_path.exists():
            initial_dir = self._entradas_manual_path.parent
        elif self._expedientes_manual_path and self._expedientes_manual_path.exists():
            initial_dir = self._expedientes_manual_path.parent
        elif self._datos_dir is not None:
            initial_dir = self._datos_dir
        elif self._storage_target.is_dir():
            initial_dir = self._storage_target
        else:
            initial_dir = self.config_path.parent

        entradas_path_str = filedialog.askopenfilename(
            title="Seleccionar historial de entradas",
            filetypes=(("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")),
            initialdir=str(initial_dir) if initial_dir else None,
        )
        if not entradas_path_str:
            return

        entradas_path = Path(entradas_path_str)
        expedientes_initial_dir: Path | None
        if self._expedientes_manual_path and self._expedientes_manual_path.exists():
            expedientes_initial_dir = self._expedientes_manual_path.parent
        else:
            expedientes_initial_dir = entradas_path.parent

        expedientes_path_str = filedialog.askopenfilename(
            title="Seleccionar historial de expedientes",
            filetypes=(("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")),
            initialdir=str(expedientes_initial_dir) if expedientes_initial_dir else None,
        )
        if not expedientes_path_str:
            return

        self._load_historiales_desde_archivos(entradas_path, Path(expedientes_path_str))

    def _load_historiales_desde_archivos(
        self, entradas_path: Path | str, expedientes_path: Path | str
    ) -> bool:
        entradas_path = Path(entradas_path)
        expedientes_path = Path(expedientes_path)

        def _read_json(path: Path, etiqueta: str) -> list[object] | None:
            try:
                with path.open("r", encoding="utf-8") as file:
                    data = json.load(file)
            except FileNotFoundError:
                messagebox.showerror(
                    "Monitor PJN",
                    f"No se encontró el archivo {etiqueta}.\nUbicación: {path}",
                )
                return None
            except json.JSONDecodeError as exc:
                messagebox.showerror(
                    "Monitor PJN",
                    f"El archivo {etiqueta} no contiene un JSON válido.\nDetalle: {exc}",
                )
                return None
            except OSError as exc:  # pragma: no cover - comunicación con UI real
                messagebox.showerror(
                    "Monitor PJN",
                    f"No fue posible leer el archivo {etiqueta}.\nDetalle: {exc}",
                )
                return None

            if not isinstance(data, list):
                messagebox.showerror(
                    "Monitor PJN",
                    f"El archivo {etiqueta} debe contener una lista JSON de elementos.",
                )
                return None

            return data

        entradas_data = _read_json(entradas_path, "de entradas")
        if entradas_data is None:
            return False

        expedientes_data = _read_json(expedientes_path, "de expedientes")
        if expedientes_data is None:
            return False

        try:
            entradas = [Entrada.from_dict(item) for item in entradas_data]
        except Exception as exc:  # pragma: no cover - comunicación con UI real
            messagebox.showerror(
                "Monitor PJN",
                "No fue posible interpretar el historial de entradas proporcionado.\n"
                f"Detalle: {exc}",
            )
            return False

        try:
            expedientes = [ExpedienteResumen.from_dict(item) for item in expedientes_data]
        except Exception as exc:  # pragma: no cover - comunicación con UI real
            messagebox.showerror(
                "Monitor PJN",
                "No fue posible interpretar el historial de expedientes proporcionado.\n"
                f"Detalle: {exc}",
            )
            return False

        manual_dir: Path | None = None
        if entradas_path.parent == expedientes_path.parent:
            manual_dir = entradas_path.parent
        else:
            try:
                common_dir = Path(os.path.commonpath([entradas_path.parent, expedientes_path.parent]))
            except ValueError:
                common_dir = None
            else:
                manual_dir = common_dir if common_dir.is_dir() else None

        self.entradas = entradas
        self.expedientes = expedientes
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

        entradas_selected: set[str] = set()
        expedientes_selected: set[str] = set()
        if manual_dir is not None:
            try:
                selecciones = cargar_selecciones_desde_directorio(manual_dir)
            except FileNotFoundError:
                pass
            except OSError as exc:  # pragma: no cover - comunicación con UI real
                messagebox.showwarning(
                    "Monitor PJN",
                    "No fue posible leer las selecciones almacenadas.\n"
                    f"Detalle: {exc}",
                )
            except Exception as exc:  # pragma: no cover - comunicación con UI real
                messagebox.showerror(
                    "Monitor PJN",
                    "Ocurrió un error inesperado al cargar las selecciones.\n"
                    f"Detalle: {exc}",
                )
            else:
                if not isinstance(selecciones, tuple) or len(selecciones) != 2:
                    messagebox.showwarning(
                        "Monitor PJN",
                        "Las selecciones almacenadas tienen un formato inválido y se descartarán.",
                    )
                else:
                    entradas_ids, expedientes_ids = selecciones
                    entradas_selected = {str(_id) for _id in entradas_ids}
                    expedientes_selected = {str(_id) for _id in expedientes_ids}

        self._entradas_selected = entradas_selected
        self._expedientes_selected = expedientes_selected
        self._populate_listbox(self._entradas_listbox, self._entradas_items, self._entradas_selected)
        self._populate_listbox(
            self._expedientes_listbox, self._expedientes_items, self._expedientes_selected
        )

        self._historial_dirty = False
        self._entradas_manual_path = entradas_path
        self._expedientes_manual_path = expedientes_path
        messagebox.showinfo(
            "Monitor PJN",
            "Historiales cargados correctamente desde los archivos seleccionados.",
        )
        return True

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

    def _load_selecciones(self) -> tuple[set[str], set[str]]:
        try:
            entradas_ids, expedientes_ids = self._selecciones_loader(self._storage_target)
        except FileNotFoundError:
            return set(), set()
        except OSError as exc:  # pragma: no cover - comunicación con UI real
            messagebox.showwarning(
                "Monitor PJN",
                "No fue posible leer las selecciones almacenadas.\n"
                f"Detalle: {exc}",
            )
            return set(), set()
        except Exception as exc:  # pragma: no cover - comunicación con UI
            messagebox.showerror(
                "Monitor PJN",
                "Ocurrió un error inesperado al cargar las selecciones.\n"
                f"Detalle: {exc}",
            )
            return set(), set()

        return {str(_id) for _id in entradas_ids}, {str(_id) for _id in expedientes_ids}

    def _process_selected_expedientes(self) -> None:
        if self._processing_active:
            messagebox.showinfo(
                "Monitor PJN",
                "Ya hay un procesamiento en curso. Espere a que finalice.",
            )
            return

        indices = self._expedientes_listbox.curselection()
        if not indices:
            messagebox.showinfo(
                "Monitor PJN",
                "Seleccione al menos un expediente para iniciar el procesamiento.",
            )
            return

        seleccionados = [self._expedientes_items[index] for index in indices]
        descargar_adjuntos = self._descargar_adjuntos_var.get()

        self._processing_active = True
        self._procesar_btn.config(state=tk.DISABLED)
        self._append_resultado(
            _ResultadoItem(
                mensaje=f"Iniciando procesamiento de {len(seleccionados)} expediente(s)...",
                estado="info",
            )
        )

        self._processing_thread = threading.Thread(
            target=self._run_processing_worker,
            args=(seleccionados, descargar_adjuntos),
            daemon=True,
        )
        self._processing_thread.start()

    def _run_processing_worker(
        self, items: list[_ExpedienteItem], descargar_adjuntos: bool
    ) -> None:
        if self._playwright_bridge is not None:
            self._run_processing_with_bridge(items, descargar_adjuntos)
        else:
            asyncio.run(
                self._run_processing_async(items, descargar_adjuntos)
            )
        self._processing_queue.put(
            _ProcessingEvent(tipo="done", expediente=None, mensaje="Procesamiento finalizado."),
        )

    async def _run_processing_async(
        self, items: list[_ExpedienteItem], descargar_adjuntos: bool
    ) -> None:
        for item in items:
            self._processing_queue.put(
                _ProcessingEvent(
                    tipo="progress",
                    expediente=item,
                    mensaje=f"Procesando expediente {item.expediente.numero}...",
                )
            )
            try:
                datos_expediente = self._build_datos_expediente(item)
            except Exception as exc:  # pragma: no cover - comunicación con UI
                self._processing_queue.put(
                    _ProcessingEvent(
                        tipo="error",
                        expediente=item,
                        mensaje=str(exc),
                    )
                )
                continue

            try:
                json_path, resumen = await procesar_actuaciones_expediente(
                    datos_expediente,
                    descargar_adjuntos=descargar_adjuntos,
                )
            except Exception as exc:  # pragma: no cover - comunicación con UI
                self._processing_queue.put(
                    _ProcessingEvent(
                        tipo="error",
                        expediente=item,
                        mensaje=str(exc),
                    )
                )
            else:
                self._processing_queue.put(
                    _ProcessingEvent(
                        tipo="success",
                        expediente=item,
                        mensaje=f"Expediente {item.expediente.numero} procesado correctamente.",
                        resumen=resumen,
                        json_path=str(json_path) if json_path else None,
                    )
                )

    def _run_processing_with_bridge(
        self, items: list[_ExpedienteItem], descargar_adjuntos: bool
    ) -> None:
        assert self._playwright_bridge is not None
        bridge = self._playwright_bridge

        for item in items:
            self._processing_queue.put(
                _ProcessingEvent(
                    tipo="progress",
                    expediente=item,
                    mensaje=f"Procesando expediente {item.expediente.numero}...",
                )
            )
            try:
                datos_expediente = self._build_datos_expediente(item)
            except PlaywrightSessionError as exc:
                self._processing_queue.put(
                    _ProcessingEvent(
                        tipo="error",
                        expediente=item,
                        mensaje=str(exc),
                        alert="error",
                    )
                )
                break
            except ExpedienteNotFoundError as exc:
                self._processing_queue.put(
                    _ProcessingEvent(
                        tipo="error",
                        expediente=item,
                        mensaje=str(exc),
                        alert="warning",
                    )
                )
                continue
            except ExpedienteNavigationError as exc:
                self._processing_queue.put(
                    _ProcessingEvent(
                        tipo="error",
                        expediente=item,
                        mensaje=str(exc),
                        alert="error",
                    )
                )
                continue
            except PlaywrightBridgeError as exc:
                self._processing_queue.put(
                    _ProcessingEvent(
                        tipo="error",
                        expediente=item,
                        mensaje=str(exc),
                        alert="error",
                    )
                )
                continue
            except Exception as exc:  # pragma: no cover - comunicación con UI
                self._processing_queue.put(
                    _ProcessingEvent(
                        tipo="error",
                        expediente=item,
                        mensaje=str(exc),
                        alert="error",
                    )
                )
                continue

            try:
                json_path, resumen = bridge.run_coroutine(
                    procesar_actuaciones_expediente(
                        datos_expediente,
                        descargar_adjuntos=descargar_adjuntos,
                    )
                )
            except PlaywrightSessionError as exc:
                self._processing_queue.put(
                    _ProcessingEvent(
                        tipo="error",
                        expediente=item,
                        mensaje=str(exc),
                        alert="error",
                    )
                )
                break
            except PlaywrightBridgeError as exc:
                self._processing_queue.put(
                    _ProcessingEvent(
                        tipo="error",
                        expediente=item,
                        mensaje=str(exc),
                        alert="error",
                    )
                )
            except Exception as exc:  # pragma: no cover - comunicación con UI
                self._processing_queue.put(
                    _ProcessingEvent(
                        tipo="error",
                        expediente=item,
                        mensaje=str(exc),
                        alert="error",
                    )
                )
            else:
                self._processing_queue.put(
                    _ProcessingEvent(
                        tipo="success",
                        expediente=item,
                        mensaje=f"Expediente {item.expediente.numero} procesado correctamente.",
                        resumen=resumen,
                        json_path=str(json_path) if json_path else None,
                    )
                )

    def _build_datos_expediente(self, item: _ExpedienteItem) -> dict[str, object]:
        if self._expediente_payload_factory is None:
            raise RuntimeError(
                "No se configuró un proveedor de datos del expediente con la página activa."
            )
        datos = self._expediente_payload_factory(item.expediente)
        if not isinstance(datos, dict):
            raise TypeError(
                "El proveedor de expedientes debe devolver un diccionario con los datos necesarios."
            )
        if "page" not in datos:
            raise RuntimeError(
                "El proveedor de expedientes debe incluir la clave 'page' con la instancia de Playwright."
            )
        return datos

    def _poll_processing_queue(self) -> None:
        while True:
            try:
                event = self._processing_queue.get_nowait()
            except queue.Empty:
                break
            self._handle_processing_event(event)
        self.after(200, self._poll_processing_queue)

    def _handle_processing_event(self, event: "_ProcessingEvent") -> None:
        if event.tipo == "progress":
            self._append_resultado(_ResultadoItem(mensaje=event.mensaje, estado="info"))
        elif event.tipo == "success":
            resumen = event.resumen or {}
            mensaje_error = resumen.get("error")
            numero = (event.expediente.expediente.numero if event.expediente else "—")
            if mensaje_error:
                mensaje = f"✗ {numero} — Error: {mensaje_error}"
                event.mensaje = mensaje
                event.alert = event.alert or "error"
                self._append_resultado(
                    _ResultadoItem(
                        mensaje=mensaje,
                        estado="error",
                        json_path=event.json_path,
                    )
                )
            else:
                descargas = "Sí" if resumen.get("descargas_ejecutadas") else "No"
                mensaje = (
                    f"✓ {numero} — "
                    f"Act.: {resumen.get('actuaciones_actuales', 0)}/"
                    f"{resumen.get('actuaciones_historicas', 0)} — Descargas: {descargas}"
                )
                self._append_resultado(
                    _ResultadoItem(
                        mensaje=mensaje,
                        estado="success",
                        carpeta_expediente=resumen.get("carpeta_expediente"),
                        carpeta_actuaciones=resumen.get("carpeta_actuaciones"),
                        carpeta_json=resumen.get("carpeta_json"),
                        json_path=event.json_path,
                    )
                )
        elif event.tipo == "error":
            mensaje = f"✗ {event.expediente.expediente.numero} — Error: {event.mensaje}"
            self._append_resultado(_ResultadoItem(mensaje=mensaje, estado="error"))
        elif event.tipo == "done":
            self._append_resultado(_ResultadoItem(mensaje=event.mensaje, estado="info"))
            self._processing_active = False
            self._procesar_btn.config(state=tk.NORMAL)
            self._processing_thread = None

        if event.alert == "error":
            messagebox.showerror("Monitor PJN", event.mensaje)
        elif event.alert == "warning":
            messagebox.showwarning("Monitor PJN", event.mensaje)
        elif event.alert == "info":
            messagebox.showinfo("Monitor PJN", event.mensaje)

    def _append_resultado(self, item: "_ResultadoItem") -> None:
        self._resultados_items.append(item)
        self._resultados_listbox.insert(tk.END, item.mensaje)
        self._resultados_listbox.yview_moveto(1.0)
        if item.estado == "success" and item.carpeta_expediente:
            self._abrir_carpeta_btn.config(state=tk.NORMAL)
        else:
            self._abrir_carpeta_btn.config(state=tk.DISABLED)

    def _on_result_selection(self, _event: tk.Event[object]) -> None:  # pragma: no cover - UI
        index = self._get_selected_result_index()
        if index is None:
            self._abrir_carpeta_btn.config(state=tk.DISABLED)
            return
        item = self._resultados_items[index]
        if item.estado == "success" and item.carpeta_expediente:
            self._abrir_carpeta_btn.config(state=tk.NORMAL)
        else:
            self._abrir_carpeta_btn.config(state=tk.DISABLED)

    def _get_selected_result_index(self) -> int | None:
        selection = self._resultados_listbox.curselection()
        if not selection:
            return None
        return int(selection[0])

    def _open_selected_result_folder(self) -> None:
        index = self._get_selected_result_index()
        if index is None:
            messagebox.showinfo(
                "Monitor PJN", "Seleccione un resultado con carpeta disponible."
            )
            return

        item = self._resultados_items[index]
        if not item.carpeta_expediente:
            messagebox.showinfo(
                "Monitor PJN",
                "El resultado elegido no contiene información de carpeta disponible.",
            )
            return

        path = Path(item.carpeta_expediente)
        if not path.exists():
            messagebox.showerror(
                "Monitor PJN",
                f"La carpeta indicada no existe o no es accesible.\n{path}",
            )
            return

        try:
            _open_path_in_explorer(path)
        except Exception as exc:  # pragma: no cover - interacción con SO
            messagebox.showerror(
                "Monitor PJN",
                f"No se pudo abrir la carpeta del expediente.\n{exc}",
            )

    def _save_changes(self) -> None:
        if not self._persist_selecciones(show_success=False):
            return

        if self._historial_dirty and not self._persist_historiales():
            return

        messagebox.showinfo("Monitor PJN", "Cambios guardados correctamente.")

    def _persist_selecciones(self, *, show_success: bool) -> bool:
        entradas_ids = self._gather_selections(self._entradas_listbox, self._entradas_items)
        expedientes_ids = self._gather_selections(self._expedientes_listbox, self._expedientes_items)

        try:
            self._selecciones_saver(
                self._storage_target,
                entradas_ids=entradas_ids,
                expedientes_ids=expedientes_ids,
            )
        except OSError as exc:
            messagebox.showerror(
                "Monitor PJN",
                "No fue posible guardar las selecciones actuales.\n"
                "Verifique los permisos del directorio de datos.\n"
                f"Detalle: {exc}",
            )
            return False
        except Exception as exc:  # pragma: no cover - comunicación con UI
            messagebox.showerror(
                "Monitor PJN",
                "Ocurrió un error inesperado al guardar las selecciones.\n"
                f"Detalle: {exc}",
            )
            return False

        self._entradas_selected = set(entradas_ids)
        self._expedientes_selected = set(expedientes_ids)

        if show_success:  # pragma: no cover - comunicación con UI
            messagebox.showinfo("Monitor PJN", "Selecciones guardadas correctamente.")

        return True

    def _persist_historiales(self) -> bool:
        try:
            self._historiales_saver(
                self._storage_target,
                entradas=self.entradas,
                expedientes=self.expedientes,
            )
        except OSError as exc:
            messagebox.showerror(
                "Monitor PJN",
                "No fue posible guardar los historiales modificados.\n"
                "Verifique los permisos del directorio de datos.\n"
                f"Detalle: {exc}",
            )
            return False
        except Exception as exc:  # pragma: no cover - comunicación con UI
            messagebox.showerror(
                "Monitor PJN",
                "Ocurrió un error inesperado al guardar los historiales.\n"
                f"Detalle: {exc}",
            )
            return False

        self._historial_dirty = False
        return True

    def _on_close(self) -> None:
        if not self._persist_selecciones(show_success=False):
            return

        if self._historial_dirty and not self._persist_historiales():
            return

        self.destroy()


# ----------------------------------------------------------------------
# Utilidades públicas
# ----------------------------------------------------------------------

def _infer_item_id(value: str | None, index: int, prefix: str) -> str:
    value = (value or "").strip()
    return value if value else f"{prefix}-{index}"


def _open_path_in_explorer(path: Path) -> None:
    if sys.platform.startswith("win"):
        os.startfile(path)  # type: ignore[arg-type]
    elif sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
    else:
        subprocess.run(["xdg-open", str(path)], check=False)


@dataclass(slots=True)
class _ResultadoItem:
    mensaje: str
    estado: Literal["info", "success", "error"]
    carpeta_expediente: str | None = None
    carpeta_actuaciones: str | None = None
    carpeta_json: str | None = None
    json_path: str | None = None


@dataclass(slots=True)
class _ProcessingEvent:
    tipo: Literal["progress", "success", "error", "done"]
    expediente: _ExpedienteItem | None
    mensaje: str
    resumen: ResultadoProcesamiento | None = None
    json_path: str | None = None
    alert: Literal["info", "warning", "error"] | None = None


def launch_monitor_form(
    config_path: Path | str = Path("config/monitor.json"),
    *,
    datos_dir: Path | str | None = None,
    expediente_payload_factory: Callable[[ExpedienteResumen], dict[str, object]] | None = None,
) -> None:
    """Inicia el formulario gráfico con la configuración indicada."""

    bridge: GUIPlaywrightBridge | None = None
    bridge_error: Exception | None = None

    if expediente_payload_factory is None:
        try:
            monitor_config = MonitorConfig.from_file(config_path)
        except Exception as exc:  # pragma: no cover - carga defensiva
            monitor_config = MonitorConfig()
            bridge_error = exc

        bridge = GUIPlaywrightBridge(headless=monitor_config.headless)
        try:
            bridge.start()
        except PlaywrightSessionError as exc:
            bridge.close()
            bridge = None
            bridge_error = exc

            def _raise_session_error(_: ExpedienteResumen) -> dict[str, object]:
                raise PlaywrightSessionError(str(exc))

            expediente_payload_factory = _raise_session_error
        else:
            expediente_payload_factory = bridge.get_expediente_payload

    if datos_dir is not None:
        app = MonitorForm(
            config_path,
            datos_dir=datos_dir,
            expediente_payload_factory=expediente_payload_factory,
            playwright_bridge=bridge,
            historiales_loader=cargar_historiales_desde_directorio,
            historiales_saver=guardar_historiales_en_directorio,
            selecciones_loader=cargar_selecciones_desde_directorio,
            selecciones_saver=guardar_selecciones_en_directorio,
        )
    else:
        app = MonitorForm(
            config_path,
            expediente_payload_factory=expediente_payload_factory,
            playwright_bridge=bridge,
        )

    if bridge_error is not None:
        mensaje = (
            "No se pudo preparar la sesión de Playwright. "
            f"Detalle: {bridge_error}"
            if isinstance(bridge_error, PlaywrightSessionError)
            else f"No se pudo leer la configuración del monitor: {bridge_error}"
        )
        app.after(0, lambda: messagebox.showerror("Monitor PJN", mensaje))

    try:
        app.mainloop()
    finally:
        if bridge is not None:
            bridge.close()


def _build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Formulario de apoyo para el monitor PJN")
    parser.add_argument(
        "--config",
        default="config/monitor.json",
        type=Path,
        help=(
            "Ruta al archivo de configuración del monitor (monitor.json). "
            "Se ignora si se especifica --datos."
        ),
    )
    parser.add_argument(
        "--datos",
        type=Path,
        help=(
            "Directorio con los archivos historial_*.json y selecciones.json. "
            "Útil para apuntar a Sistema_v5/data/monitor u otra ubicación personalizada."
        ),
    )
    return parser


def main() -> None:
    """Punto de entrada CLI usado cuando se ejecuta el módulo directamente."""

    parser = _build_argument_parser()
    args = parser.parse_args()
    launch_monitor_form(args.config, datos_dir=args.datos)


if __name__ == "__main__":  # pragma: no cover - ejecución directa
    main()
