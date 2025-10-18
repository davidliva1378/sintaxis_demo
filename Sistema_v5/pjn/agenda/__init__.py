"""Herramientas de agenda y gestión de plazos para Sistema_v5."""

from .agenda import (
    AgendaItem,
    AgendaQuery,
    AgendaRepository,
    AgendaService,
    calcular_fecha_plazo,
    contar_dias_corridos,
    contar_dias_habiles,
    crear_agenda_default,
    dias_habiles_entre,
    dias_corridos_entre,
    obtener_agenda_global,
    registrar_audiencia,
    registrar_nota,
    registrar_recordatorio,
    registrar_tarea,
    registrar_vencimiento,
)

Agenda = AgendaService

__all__ = [
    "AgendaItem",
    "AgendaQuery",
    "AgendaRepository",
    "AgendaService",
    "Agenda",
    "calcular_fecha_plazo",
    "contar_dias_corridos",
    "contar_dias_habiles",
    "crear_agenda_default",
    "dias_habiles_entre",
    "dias_corridos_entre",
    "obtener_agenda_global",
    "registrar_audiencia",
    "registrar_nota",
    "registrar_recordatorio",
    "registrar_tarea",
    "registrar_vencimiento",
]
