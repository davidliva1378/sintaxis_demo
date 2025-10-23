"""Componentes de interfaz para el extractor inicial."""

from .directorios_form import mostrar_formulario_directorios
from .historial_form import HistorialForm, mostrar_formulario_historial
from .filtros_avanzados_form import FiltrosAvanzadosForm, mostrar_filtros_avanzados

__all__ = [
    "mostrar_formulario_directorios",
    "HistorialForm",
    "mostrar_formulario_historial",
    # Nuevos componentes v2.0
    "FiltrosAvanzadosForm",
    "mostrar_filtros_avanzados",
]
