"""Backwards compatibility wrapper for GUI configuration widgets.

El módulo ``Sistema_v5.pjn.gui`` se mantiene por compatibilidad con
versiones previas, pero las implementaciones viven ahora en
``Sistema_v5.configuracion.gui``.
"""

from __future__ import annotations

from warnings import warn

from Sistema_v5.configuracion.gui.config_widgets import (
    DirectorySelector,
    DatePicker,
    TimePicker,
    IntervalInput,
    DaysSelector,
    ValidatedEntry,
)

try:
    from Sistema_v5.configuracion.gui.config_form import ConfigForm
except ImportError:  # pragma: no cover - tkinter puede no estar disponible
    ConfigForm = None  # type: ignore[assignment]
else:
    warn(
        "Sistema_v5.pjn.gui está deprecado; usa Sistema_v5.configuracion.gui",
        DeprecationWarning,
        stacklevel=2,
    )

__all__ = [
    "ConfigForm",
    "DirectorySelector",
    "DatePicker",
    "TimePicker",
    "IntervalInput",
    "DaysSelector",
    "ValidatedEntry",
]
