"""Formulario de filtrado y exportación del historial de expedientes."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox
from typing import Iterable, Sequence

from Sistema_v5.pjn.models.expediente import ExpedienteResumen

from ..storage import cargar_historial_simulado, guardar_historial_simulado


class HistorialForm(tk.Toplevel):
    """Ventana modal para filtrar y exportar historiales."""

    _ORDENES = {
        "Original": None,
        "Número": lambda exp: exp.numero.casefold(),
        "Dependencia": lambda exp: exp.dependencia.casefold(),
        "Carátula": lambda exp: exp.caratula.casefold(),
        "Situación": lambda exp: (exp.situacion or "").casefold(),
    }

    def __init__(
        self,
        master: tk.Misc | None,
        expedientes: Sequence[ExpedienteResumen],
        directorio_destino: Path | str,
    ) -> None:
        super().__init__(master=master)
        self.title("Historial de expedientes extraídos")
        self.geometry("720x520")
        self.minsize(640, 400)
        self.transient(master)

        self._destino = Path(directorio_destino)
        self._expedientes = list(expedientes)
        self._seleccion_previa = {
            exp.numero for exp in cargar_historial_simulado(self._destino)
        }
        self._expedientes_filtrados: list[ExpedienteResumen] = []
        self.result: list[ExpedienteResumen] | None = None

        self._numero_var = tk.StringVar()
        self._caratula_var = tk.StringVar()
        self._dependencia_var = tk.StringVar()
        self._situacion_var = tk.StringVar(value="Todas")
        self._orden_var = tk.StringVar(value="Original")

        self._build_ui()
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._actualizar_listado()

    # ------------------------------------------------------------------ UI --
    def _build_ui(self) -> None:
        container = ttk.Frame(self, padding=15)
        container.pack(fill=tk.BOTH, expand=True)

        filtros_frame = ttk.LabelFrame(container, text="Filtros", padding=10)
        filtros_frame.pack(fill=tk.X)

        ttk.Label(filtros_frame, text="Número").grid(row=0, column=0, sticky="w")
        numero_entry = ttk.Entry(filtros_frame, textvariable=self._numero_var, width=24)
        numero_entry.grid(row=0, column=1, padx=5, pady=2, sticky="we")
        numero_entry.bind("<KeyRelease>", self._on_filter_change)

        ttk.Label(filtros_frame, text="Carátula").grid(row=0, column=2, sticky="w")
        caratula_entry = ttk.Entry(filtros_frame, textvariable=self._caratula_var, width=24)
        caratula_entry.grid(row=0, column=3, padx=5, pady=2, sticky="we")
        caratula_entry.bind("<KeyRelease>", self._on_filter_change)

        ttk.Label(filtros_frame, text="Dependencia").grid(row=1, column=0, sticky="w")
        dependencia_entry = ttk.Entry(
            filtros_frame, textvariable=self._dependencia_var, width=24
        )
        dependencia_entry.grid(row=1, column=1, padx=5, pady=2, sticky="we")
        dependencia_entry.bind("<KeyRelease>", self._on_filter_change)

        ttk.Label(filtros_frame, text="Situación").grid(row=1, column=2, sticky="w")
        situacion_combo = ttk.Combobox(
            filtros_frame,
            textvariable=self._situacion_var,
            values=self._build_situaciones_options(),
            state="readonly",
        )
        situacion_combo.grid(row=1, column=3, padx=5, pady=2, sticky="we")
        situacion_combo.bind("<<ComboboxSelected>>", self._on_filter_change)

        ttk.Label(filtros_frame, text="Ordenar por").grid(
            row=2, column=0, sticky="w", pady=(8, 0)
        )
        orden_combo = ttk.Combobox(
            filtros_frame,
            textvariable=self._orden_var,
            values=list(self._ORDENES.keys()),
            state="readonly",
        )
        orden_combo.grid(row=2, column=1, padx=5, pady=(8, 0), sticky="we")
        orden_combo.bind("<<ComboboxSelected>>", self._on_filter_change)

        filtros_frame.columnconfigure(1, weight=1)
        filtros_frame.columnconfigure(3, weight=1)

        lista_frame = ttk.Frame(container)
        lista_frame.pack(fill=tk.BOTH, expand=True, pady=(15, 10))

        scrollbar = ttk.Scrollbar(lista_frame, orient=tk.VERTICAL)
        self._listbox = tk.Listbox(
            lista_frame,
            selectmode=tk.EXTENDED,
            yscrollcommand=scrollbar.set,
            activestyle="none",
        )
        self._listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self._listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        acciones_frame = ttk.Frame(container)
        acciones_frame.pack(fill=tk.X)

        ttk.Button(
            acciones_frame,
            text="Seleccionar todo",
            command=self._seleccionar_todo,
        ).pack(side=tk.LEFT)

        ttk.Button(
            acciones_frame,
            text="Guardar selección",
            command=self._guardar_seleccion,
        ).pack(side=tk.RIGHT)

        ttk.Button(
            acciones_frame,
            text="Exportar todo",
            command=self._exportar_todo,
        ).pack(side=tk.RIGHT, padx=(0, 10))

        ttk.Button(
            acciones_frame,
            text="Cerrar",
            command=self._on_close,
        ).pack(side=tk.RIGHT, padx=(0, 10))

    # ----------------------------------------------------------- lifecycle --
    def _build_situaciones_options(self) -> list[str]:
        situaciones = sorted({
            exp.situacion or ""
            for exp in self._expedientes
            if (exp.situacion or "").strip()
        })
        opciones = ["Todas"]
        opciones.extend(situaciones)
        return opciones

    def _actualizar_listado(self) -> None:
        self._expedientes_filtrados = self._filtrar_expedientes()
        self._listbox.delete(0, tk.END)
        for exp in self._expedientes_filtrados:
            display = self._format_expediente(exp)
            self._listbox.insert(tk.END, display)

        self._listbox.selection_clear(0, tk.END)
        for idx, exp in enumerate(self._expedientes_filtrados):
            if exp.numero in self._seleccion_previa:
                self._listbox.selection_set(idx)

    # -------------------------------------------------------------- utils --
    def _filtrar_expedientes(self) -> list[ExpedienteResumen]:
        numero = self._numero_var.get().strip().casefold()
        caratula = self._caratula_var.get().strip().casefold()
        dependencia = self._dependencia_var.get().strip().casefold()
        situacion = self._situacion_var.get().strip()
        orden = self._orden_var.get()

        filtrados: list[ExpedienteResumen] = []
        for exp in self._expedientes:
            if numero and numero not in exp.numero.casefold():
                continue
            if caratula and caratula not in exp.caratula.casefold():
                continue
            if dependencia and dependencia not in exp.dependencia.casefold():
                continue
            if situacion != "Todas":
                exp_situacion = (exp.situacion or "").strip()
                if situacion != exp_situacion:
                    continue
            filtrados.append(exp)

        key = self._ORDENES.get(orden)
        if key is None:
            return filtrados

        return sorted(filtrados, key=key)

    @staticmethod
    def _format_expediente(exp: ExpedienteResumen) -> str:
        situacion = exp.situacion or "Sin información"
        return (
            f"{exp.numero}  |  {exp.dependencia}  |  {exp.caratula}  |  {situacion}"
        )

    def _obtener_seleccion(self) -> list[ExpedienteResumen]:
        indices = self._listbox.curselection()
        return [self._expedientes_filtrados[i] for i in indices]

    # ------------------------------------------------------------- events --
    def _on_filter_change(self, _event: object) -> None:
        self._actualizar_listado()

    def _seleccionar_todo(self) -> None:
        if not self._expedientes_filtrados:
            return
        self._listbox.selection_set(0, tk.END)

    def _guardar_seleccion(self) -> None:
        seleccion = self._obtener_seleccion()
        guardar_historial_simulado(seleccion, self._destino)
        self._seleccion_previa = {exp.numero for exp in seleccion}
        self.result = seleccion
        messagebox.showinfo(
            "Historial guardado",
            f"Se guardaron {len(seleccion)} expedientes seleccionados.",
            parent=self,
        )

    def _exportar_todo(self) -> None:
        guardar_historial_simulado(self._expedientes, self._destino)
        self._seleccion_previa = {exp.numero for exp in self._expedientes}
        self.result = list(self._expedientes)
        self._actualizar_listado()
        messagebox.showinfo(
            "Historial exportado",
            f"Se exportaron {len(self._expedientes)} expedientes.",
            parent=self,
        )

    def _on_close(self) -> None:
        self.grab_release()
        self.destroy()


def mostrar_formulario_historial(
    expedientes: Iterable[ExpedienteResumen],
    directorio_destino: Path | str,
) -> list[ExpedienteResumen]:
    """Abre el formulario modal de historiales y devuelve la selección."""

    root = tk.Tk()
    root.withdraw()
    form = HistorialForm(root, list(expedientes), directorio_destino)
    root.wait_window(form)
    root.destroy()
    return form.result or []


__all__ = ["HistorialForm", "mostrar_formulario_historial"]
