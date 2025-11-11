"""Modulo de scraping del PJN."""

from .base import (
    limpiar_texto,
    normalizar_texto,
    normalizar_fecha,
    generar_hash_identificador,
    normalizar_numero_expediente,
    descomponer_numero_expediente,
    obtener_pagina_autenticada,
)

__all__ = [
    "limpiar_texto",
    "normalizar_texto",
    "normalizar_fecha",
    "generar_hash_identificador",
    "normalizar_numero_expediente",
    "descomponer_numero_expediente",
    "obtener_pagina_autenticada",
]
