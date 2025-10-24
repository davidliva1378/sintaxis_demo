"""Backwards compatibility wrapper for GUI configuration widgets.

El módulo ``Sistema_v5.pjn.gui`` se mantiene por compatibilidad con
versiones previas, pero las implementaciones viven ahora en
``Sistema_v5.configuracion.gui``.
"""

from __future__ import annotations

from warnings import warn

try:
    from ...configuracion.gui.config_widgets import (
        DirectorySelector,
        DatePicker,
        TimePicker,
        IntervalInput,
        DaysSelector,
        ValidatedEntry,
    )
except ImportError:
    from configuracion.gui.config_widgets import (
        DirectorySelector,
        DatePicker,
        TimePicker,
        IntervalInput,
        DaysSelector,
        ValidatedEntry,
    )

try:
    from ...configuracion.gui.config_form import ConfigForm
    _config_form_imported = True
except ImportError:
    try:
        from configuracion.gui.config_form import ConfigForm
        _config_form_imported = True
    except ImportError:  # pragma: no cover - tkinter puede no estar disponible
        ConfigForm = None  # type: ignore[assignment]
        _config_form_imported = False

if _config_form_imported:
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
