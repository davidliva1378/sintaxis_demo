"""Módulo de persistencia para guardar y cargar datos del PJN.

Separa la lógica de I/O (lectura/escritura de archivos) de la lógica de negocio.
"""

from .actuaciones import (
    actualizar_descargados,
    cargar_actuaciones_archivo,
    cargar_actuaciones_json,
    extraer_actuaciones_con_archivos,
    guardar_actuaciones_json,
    listar_archivos_actuaciones,
)

__all__ = [
    "actualizar_descargados",
    "cargar_actuaciones_archivo",
    "cargar_actuaciones_json",
    "extraer_actuaciones_con_archivos",
    "guardar_actuaciones_json",
    "listar_archivos_actuaciones",
]
