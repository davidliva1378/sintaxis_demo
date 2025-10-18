"""Módulo GUI para configuración del sistema PJN.

Este módulo proporciona interfaces gráficas para configurar el sistema,
incluyendo formularios, widgets y utilidades.
"""

from .config_widgets import (
    DirectorySelector,
    DatePicker,
    TimePicker,
    IntervalInput,
    DaysSelector,
    ValidatedEntry,
)

try:
    from .config_form import ConfigForm
    __all__ = [
        "ConfigForm",
        "DirectorySelector",
        "DatePicker",
        "TimePicker",
        "IntervalInput",
        "DaysSelector",
        "ValidatedEntry",
    ]
except ImportError:
    # tkinter no disponible
    __all__ = [
        "DirectorySelector",
        "DatePicker",
        "TimePicker",
        "IntervalInput",
        "DaysSelector",
        "ValidatedEntry",
    ]
