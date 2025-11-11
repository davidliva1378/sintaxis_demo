"""
Modelos de datos para el sistema de extracción masiva.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum


class EstadoExpediente(str, Enum):
    """Estados posibles de un expediente en el procesamiento."""
    PENDIENTE = "pendiente"
    PROCESANDO = "procesando"
    PROCESADO = "procesado"
    ERROR = "error"
    OMITIDO = "omitido"
    NO_ENCONTRADO = "no_encontrado"


class TipoExtraccion(str, Enum):
    """Tipos de extracción de monitoreo."""
    TOTAL = "TOTAL"
    PARCIAL = "PARCIAL"
    DIRIGIDA = "DIRIGIDA"


@dataclass
class ExpedienteListado:
    """Expediente extraído del listado (metadata básica)."""
    numero: str
    caratula: str
    dependencia: str
    situacion: str
    fecha_inicio: str
    ultima_actuacion: str

    def to_dict(self) -> Dict:
        """Convierte a diccionario."""
        return {
            "numero": self.numero,
            "caratula": self.caratula,
            "dependencia": self.dependencia,
            "situacion": self.situacion,
            "fecha_inicio": self.fecha_inicio,
            "ultima_actuacion": self.ultima_actuacion
        }


@dataclass
class ConfigExtraccionMasiva:
    """Configuración para la extracción masiva."""
    headless: bool = True
    umbral_errores: int = 10
    timeout_pagina: int = 30000
    max_reintentos: int = 3

    def to_dict(self) -> Dict:
        return {
            "headless": self.headless,
            "umbral_errores": self.umbral_errores,
            "timeout_pagina": self.timeout_pagina,
            "max_reintentos": self.max_reintentos
        }


@dataclass
class ResumenExtraccion:
    """Resumen de una extracción masiva."""
    total: int
    exitosos: int
    errores: int
    omitidos: int
    tiempo_total: float
    errores_detalles: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "total": self.total,
            "exitosos": self.exitosos,
            "errores": self.errores,
            "omitidos": self.omitidos,
            "tiempo_total": self.tiempo_total,
            "tasa_exito": round((self.exitosos / self.total * 100) if self.total > 0 else 0, 2),
            "errores_detalles": self.errores_detalles
        }


@dataclass
class SesionExtraccion:
    """Sesión de extracción masiva."""
    session_id: str
    estado: str  # iniciando, extrayendo, completado, error
    fase: str  # listado, procesamiento
    tiempo_inicio: str
    tiempo_fin: Optional[str] = None
    config: Dict = field(default_factory=dict)
    progreso_actual: int = 0
    progreso_total: int = 0
    mensaje: str = ""
    listado_path: Optional[str] = None
    comparacion: Optional[Dict] = None
    paginas_procesadas: int = 0  # Total de páginas procesadas en la extracción

    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "estado": self.estado,
            "fase": self.fase,
            "tiempo_inicio": self.tiempo_inicio,
            "tiempo_fin": self.tiempo_fin,
            "config": self.config,
            "progreso_actual": self.progreso_actual,
            "progreso_total": self.progreso_total,
            "mensaje": self.mensaje,
            "listado_path": self.listado_path,
            "comparacion": self.comparacion,
            "paginas_procesadas": self.paginas_procesadas
        }
