"""Formulario ligero para confirmar directorios del extractor inicial."""

from __future__ import annotations

import copy
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Optional

from ...configuracion.core.system_config import SystemConfig
from ...configuracion.monitor.exceptions import ValidationError
from ...configuracion.monitor.validators import validar_directorio


class DirectoriosForm(tk.Toplevel):
    """Ventana modal para ajustar directorios críticos."""

    def __init__(
        self,
        master: tk.Misc | None,
        config: SystemConfig,
        config_path: Path,
    ) -> None:
        super().__init__(master=master)
        self.title("Directorios del extractor inicial")
        self.resizable(False, False)
        self.transient(master)

        self._config_path = Path(config_path)
        self._config_copy = copy.deepcopy(config)
        self.result: Optional[SystemConfig] = None

        self._directorio_extraccion = tk.StringVar(
            value=self._config_copy.directorio_extraccion_inicial
        )
        self._directorio_expedientes = tk.StringVar(
            value=self._config_copy.directorio_expedientes_base
        )
        self._guardar_cambios = tk.BooleanVar(value=True)

        self._build_ui()
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self._center_window()

    # ------------------------------------------------------------------ UI --
    def _build_ui(self) -> None:
        container = ttk.Frame(self, padding=20)
        container.grid(row=0, column=0, sticky="nsew")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)

        ttk.Label(
            container,
            text=(
                "Confirma los directorios donde se guardarán las extracciones "
                "iniciales y la base de expedientes."
            ),
            wraplength=380,
            justify=tk.LEFT,
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 15))

        first_entry = self._build_directory_row(
            container,
            row=1,
            label="Extracción inicial",
            variable=self._directorio_extraccion,
        )
        self._build_directory_row(
            container,
            row=2,
            label="Expedientes base",
            variable=self._directorio_expedientes,
        )

        if first_entry is not None:
            self.after(10, first_entry.focus_set)

        ttk.Checkbutton(
            container,
            variable=self._guardar_cambios,
            text=f"Guardar cambios en {self._config_path}",
        ).grid(row=3, column=0, columnspan=3, sticky="w", pady=(15, 0))

        button_frame = ttk.Frame(container)
        button_frame.grid(row=4, column=0, columnspan=3, sticky="e", pady=(20, 0))

        ttk.Button(
            button_frame,
            text="Cancelar",
            command=self._on_cancel,
        ).pack(side=tk.RIGHT, padx=(10, 0))

        ttk.Button(
            button_frame,
            text="Confirmar",
            command=self._on_confirm,
        ).pack(side=tk.RIGHT)

    def _build_directory_row(
        self,
        parent: ttk.Frame,
        *,
        row: int,
        label: str,
        variable: tk.StringVar,
    ) -> ttk.Entry | None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=5)

        entry = ttk.Entry(parent, textvariable=variable, width=45)
        entry.grid(row=row, column=1, sticky="we", padx=(10, 10))
        entry.bind("<Return>", lambda _event: self._on_confirm())

        ttk.Button(
            parent,
            text="Seleccionar…",
            command=lambda var=variable: self._browse_directory(var),
        ).grid(row=row, column=2, sticky="we")

        return entry

    # ------------------------------------------------------------- actions --
    def _browse_directory(self, variable: tk.StringVar) -> None:
        initial = variable.get().strip() or str(self._config_path.parent)
        selected = filedialog.askdirectory(
            parent=self,
            initialdir=initial,
            title="Seleccionar directorio",
            mustexist=False,
        )
        if selected:
            variable.set(selected)

    def _on_confirm(self) -> None:
        try:
            dir_extraccion = validar_directorio(
                self._directorio_extraccion.get(),
                "directorio_extraccion_inicial",
                create=True,
            )
            dir_expedientes = validar_directorio(
                self._directorio_expedientes.get(),
                "directorio_expedientes_base",
                create=True,
            )
        except ValidationError as exc:
            messagebox.showerror("Error de validación", str(exc), parent=self)
            return
        except OSError as exc:
            messagebox.showerror(
                "Error de acceso",
                f"No se pudo preparar el directorio seleccionado:\n{exc}",
                parent=self,
            )
            return

        self._directorio_extraccion.set(dir_extraccion)
        self._directorio_expedientes.set(dir_expedientes)

        self._config_copy.directorio_extraccion_inicial = dir_extraccion
        self._config_copy.directorio_expedientes_base = dir_expedientes

        if self._guardar_cambios.get():
            try:
                self._config_copy.to_file(self._config_path)
            except OSError as exc:
                messagebox.showerror(
                    "Error al guardar",
                    f"No se pudo guardar la configuración:\n{exc}",
                    parent=self,
                )
                return

        self.result = self._config_copy
        self.destroy()

    def _on_cancel(self) -> None:
        self.result = None
        self.destroy()

    def _center_window(self) -> None:
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")


def mostrar_formulario_directorios(config_path: Path) -> SystemConfig:
    """Abre el formulario y devuelve la configuración resultante."""

    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo de configuración: {config_path}"
        )
    config = SystemConfig.from_file(config_path)

    root = tk.Tk()
    root.withdraw()
    form = DirectoriosForm(root, config=config, config_path=config_path)
    root.wait_window(form)
    root.destroy()

    return form.result or config
