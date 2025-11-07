"""Respuestas de extracción masiva de expedientes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class IniciarExtraccionMasivaResponse:
    """Respuesta al iniciar extracción masiva.

    Attributes:
        session_id: ID único de la sesión creada
        mensaje: Mensaje descriptivo
        estado: Estado inicial de la extracción
    """

    session_id: str
    mensaje: str
    estado: str


@dataclass
class ProgresoExtraccionResponse:
    """Respuesta con progreso de extracción.

    Attributes:
        session_id: ID de la sesión
        estado: Estado actual (iniciando, en_progreso, pausado, completado, error)
        fase: Fase actual (configuracion, listado, procesamiento, exportacion)
        progreso_actual: Número de elementos procesados
        progreso_total: Total de elementos a procesar
        porcentaje: Porcentaje de completitud (0-100)
        mensaje: Mensaje descriptivo del progreso
        errores: Número de errores encontrados
        tiempo_transcurrido: Tiempo transcurrido en segundos
        tiempo_estimado: Tiempo estimado restante en segundos
        velocidad: Velocidad de procesamiento (elementos/segundo)
    """

    session_id: str
    estado: str
    fase: str
    progreso_actual: int
    progreso_total: int
    porcentaje: float
    mensaje: str
    errores: int
    tiempo_transcurrido: float
    tiempo_estimado: Optional[float]
    velocidad: Optional[float]


@dataclass
class ResumenExtraccionResponse:
    """Respuesta con resumen de extracción completada.

    Attributes:
        session_id: ID de la sesión
        estado: Estado final
        total: Total de expedientes procesados
        exitosos: Expedientes procesados exitosamente
        errores: Expedientes con error
        omitidos: Expedientes omitidos
        duracion_segundos: Duración total en segundos
        velocidad_promedio: Velocidad promedio de procesamiento
        archivos_generados: Lista de archivos generados
    """

    session_id: str
    estado: str
    total: int
    exitosos: int
    errores: int
    omitidos: int
    duracion_segundos: float
    velocidad_promedio: float
    archivos_generados: List[str]
