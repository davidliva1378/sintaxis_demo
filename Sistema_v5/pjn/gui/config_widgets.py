"""Widgets personalizados para el configurador del sistema.

Este módulo proporciona componentes reutilizables para la interfaz
gráfica de configuración.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog
from datetime import datetime
from typing import Callable, Any


class DirectorySelector(ttk.Frame):
    """Widget para seleccionar un directorio.

    Combina un Entry con un botón para explorar directorios.
    """

    def __init__(self, parent, initial_value: str = "", **kwargs):
        """Inicializa el selector de directorio.

        Args:
            parent: Widget padre
            initial_value: Valor inicial del directorio
            **kwargs: Argumentos adicionales para ttk.Frame
        """
        super().__init__(parent, **kwargs)

        # Variable de control
        self.directory_var = tk.StringVar(value=initial_value)

        # Entry para mostrar/editar ruta
        self.entry = ttk.Entry(self, textvariable=self.directory_var, width=40)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        # Botón para explorar
        self.browse_button = ttk.Button(
            self,
            text="📂",
            width=3,
            command=self._browse
        )
        self.browse_button.pack(side=tk.RIGHT)

    def _browse(self):
        """Abre el diálogo para seleccionar directorio."""
        current = self.directory_var.get()
        directory = filedialog.askdirectory(
            initialdir=current if current else ".",
            title="Seleccionar Directorio"
        )

        if directory:
            self.directory_var.set(directory)

    def get(self) -> str:
        """Obtiene el valor actual del directorio.

        Returns:
            str: Ruta del directorio
        """
        return self.directory_var.get()

    def set(self, value: str) -> None:
        """Establece el valor del directorio.

        Args:
            value: Nueva ruta del directorio
        """
        self.directory_var.set(value)


class DatePicker(ttk.Frame):
    """Widget para seleccionar una fecha.

    Proporciona campos separados para día, mes y año con validación.
    """

    def __init__(self, parent, initial_value: str | None = None, **kwargs):
        """Inicializa el selector de fecha.

        Args:
            parent: Widget padre
            initial_value: Fecha inicial en formato YYYY-MM-DD o DD/MM/YYYY
            **kwargs: Argumentos adicionales para ttk.Frame
        """
        super().__init__(parent, **kwargs)

        # Variables de control
        self.day_var = tk.StringVar()
        self.month_var = tk.StringVar()
        self.year_var = tk.StringVar()

        # Parsear valor inicial
        if initial_value:
            self._parse_date(initial_value)

        # Frame para componentes
        ttk.Label(self, text="Día:").pack(side=tk.LEFT, padx=(0, 2))
        self.day_spin = ttk.Spinbox(
            self,
            from_=1,
            to=31,
            width=3,
            textvariable=self.day_var
        )
        self.day_spin.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(self, text="Mes:").pack(side=tk.LEFT, padx=(0, 2))
        self.month_spin = ttk.Spinbox(
            self,
            from_=1,
            to=12,
            width=3,
            textvariable=self.month_var
        )
        self.month_spin.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(self, text="Año:").pack(side=tk.LEFT, padx=(0, 2))
        self.year_spin = ttk.Spinbox(
            self,
            from_=2020,
            to=2100,
            width=5,
            textvariable=self.year_var
        )
        self.year_spin.pack(side=tk.LEFT)

    def _parse_date(self, date_str: str) -> None:
        """Parsea string de fecha y establece los valores.

        Args:
            date_str: Fecha en formato YYYY-MM-DD o DD/MM/YYYY
        """
        try:
            if "-" in date_str:
                # Formato ISO
                year, month, day = date_str.split("-")
            else:
                # Formato argentino
                day, month, year = date_str.split("/")

            self.day_var.set(day.lstrip("0") or "1")
            self.month_var.set(month.lstrip("0") or "1")
            self.year_var.set(year)
        except:
            pass

    def get(self, format: str = "iso") -> str | None:
        """Obtiene la fecha en el formato especificado.

        Args:
            format: "iso" para YYYY-MM-DD, "arg" para DD/MM/YYYY

        Returns:
            str | None: Fecha formateada o None si incompleta
        """
        day = self.day_var.get()
        month = self.month_var.get()
        year = self.year_var.get()

        if not (day and month and year):
            return None

        try:
            day_int = int(day)
            month_int = int(month)
            year_int = int(year)

            if format == "iso":
                return f"{year_int:04d}-{month_int:02d}-{day_int:02d}"
            else:
                return f"{day_int:02d}/{month_int:02d}/{year_int:04d}"
        except:
            return None

    def set(self, value: str | None) -> None:
        """Establece la fecha.

        Args:
            value: Fecha en formato YYYY-MM-DD o DD/MM/YYYY
        """
        if value:
            self._parse_date(value)
        else:
            self.day_var.set("")
            self.month_var.set("")
            self.year_var.set("")


class TimePicker(ttk.Frame):
    """Widget para seleccionar una hora en formato HH:MM."""

    def __init__(self, parent, initial_value: str = "08:00", **kwargs):
        """Inicializa el selector de hora.

        Args:
            parent: Widget padre
            initial_value: Hora inicial en formato HH:MM
            **kwargs: Argumentos adicionales para ttk.Frame
        """
        super().__init__(parent, **kwargs)

        # Variables de control
        self.hour_var = tk.StringVar()
        self.minute_var = tk.StringVar()

        # Parsear valor inicial
        if initial_value:
            try:
                hour, minute = initial_value.split(":")
                self.hour_var.set(hour)
                self.minute_var.set(minute)
            except:
                self.hour_var.set("08")
                self.minute_var.set("00")

        # Componentes
        self.hour_spin = ttk.Spinbox(
            self,
            from_=0,
            to=23,
            width=3,
            textvariable=self.hour_var,
            format="%02.0f"
        )
        self.hour_spin.pack(side=tk.LEFT)

        ttk.Label(self, text=":").pack(side=tk.LEFT, padx=2)

        self.minute_spin = ttk.Spinbox(
            self,
            from_=0,
            to=59,
            width=3,
            textvariable=self.minute_var,
            format="%02.0f"
        )
        self.minute_spin.pack(side=tk.LEFT)

    def get(self) -> str:
        """Obtiene la hora en formato HH:MM.

        Returns:
            str: Hora formateada
        """
        hour = self.hour_var.get() or "0"
        minute = self.minute_var.get() or "0"

        try:
            hour_int = int(hour)
            minute_int = int(minute)
            return f"{hour_int:02d}:{minute_int:02d}"
        except:
            return "00:00"

    def set(self, value: str) -> None:
        """Establece la hora.

        Args:
            value: Hora en formato HH:MM
        """
        try:
            hour, minute = value.split(":")
            self.hour_var.set(hour)
            self.minute_var.set(minute)
        except:
            pass


class IntervalInput(ttk.Frame):
    """Widget para ingresar intervalos con unidades."""

    def __init__(
        self,
        parent,
        initial_value: int = 15,
        unit: str = "minutos",
        min_value: int = 1,
        max_value: int = 1440,
        **kwargs
    ):
        """Inicializa el input de intervalo.

        Args:
            parent: Widget padre
            initial_value: Valor inicial
            unit: Unidad (minutos, segundos, horas)
            min_value: Valor mínimo
            max_value: Valor máximo
            **kwargs: Argumentos adicionales para ttk.Frame
        """
        super().__init__(parent, **kwargs)

        self.min_value = min_value
        self.max_value = max_value

        # Variable de control
        self.value_var = tk.IntVar(value=initial_value)

        # Spinbox
        self.spinbox = ttk.Spinbox(
            self,
            from_=min_value,
            to=max_value,
            width=10,
            textvariable=self.value_var
        )
        self.spinbox.pack(side=tk.LEFT, padx=(0, 5))

        # Label de unidad
        ttk.Label(self, text=unit).pack(side=tk.LEFT)

    def get(self) -> int:
        """Obtiene el valor del intervalo.

        Returns:
            int: Valor del intervalo
        """
        try:
            value = int(self.value_var.get())
            return max(self.min_value, min(value, self.max_value))
        except:
            return self.min_value

    def set(self, value: int) -> None:
        """Establece el valor del intervalo.

        Args:
            value: Nuevo valor
        """
        self.value_var.set(max(self.min_value, min(value, self.max_value)))


class DaysSelector(ttk.Frame):
    """Widget para seleccionar días de la semana."""

    DIAS_SEMANA = [
        "lunes", "martes", "miércoles", "jueves",
        "viernes", "sábado", "domingo"
    ]

    def __init__(self, parent, initial_days: list[str] | None = None, **kwargs):
        """Inicializa el selector de días.

        Args:
            parent: Widget padre
            initial_days: Lista de días inicialmente seleccionados
            **kwargs: Argumentos adicionales para ttk.Frame
        """
        super().__init__(parent, **kwargs)

        initial_days = initial_days or []

        # Normalizar días iniciales (sin tildes)
        initial_normalized = [
            d.lower().replace("á", "a").replace("é", "e").replace("í", "i")
            for d in initial_days
        ]

        # Variables de control para cada día
        self.day_vars = {}

        for dia in self.DIAS_SEMANA:
            # Normalizar para comparación
            dia_norm = dia.replace("á", "a").replace("é", "e").replace("í", "i")

            # Crear variable
            var = tk.BooleanVar(value=dia_norm in initial_normalized)
            self.day_vars[dia] = var

            # Crear checkbox
            cb = ttk.Checkbutton(
                self,
                text=dia.capitalize(),
                variable=var
            )
            cb.pack(side=tk.LEFT, padx=5)

    def get(self) -> list[str]:
        """Obtiene la lista de días seleccionados.

        Returns:
            list[str]: Lista de días seleccionados (en minúsculas)
        """
        return [
            dia for dia, var in self.day_vars.items()
            if var.get()
        ]

    def set(self, days: list[str]) -> None:
        """Establece los días seleccionados.

        Args:
            days: Lista de días a seleccionar
        """
        # Normalizar días
        days_normalized = [
            d.lower().replace("á", "a").replace("é", "e").replace("í", "i")
            for d in days
        ]

        for dia, var in self.day_vars.items():
            dia_norm = dia.replace("á", "a").replace("é", "e").replace("í", "i")
            var.set(dia_norm in days_normalized)


class ValidatedEntry(ttk.Entry):
    """Entry con validación visual.

    Cambia el color del borde según si el valor es válido o no.
    """

    def __init__(
        self,
        parent,
        validator: Callable[[str], bool] | None = None,
        **kwargs
    ):
        """Inicializa el entry validado.

        Args:
            parent: Widget padre
            validator: Función que retorna True si el valor es válido
            **kwargs: Argumentos adicionales para ttk.Entry
        """
        super().__init__(parent, **kwargs)

        self.validator = validator

        # Bindear evento de cambio de contenido
        self.bind("<KeyRelease>", self._on_change)
        self.bind("<FocusOut>", self._on_change)

    def _on_change(self, event=None) -> None:
        """Maneja cambio de contenido y valida."""
        if self.validator:
            value = self.get()
            is_valid = self.validator(value)

            if is_valid:
                self.config(foreground="black")
            else:
                self.config(foreground="red")

    def set_validator(self, validator: Callable[[str], bool]) -> None:
        """Establece o cambia el validador.

        Args:
            validator: Nueva función validadora
        """
        self.validator = validator
        self._on_change()


__all__ = [
    "DirectorySelector",
    "DatePicker",
    "TimePicker",
    "IntervalInput",
    "DaysSelector",
    "ValidatedEntry",
]
