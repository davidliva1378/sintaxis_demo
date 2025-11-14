"""
Modelos de datos para el sistema de extracción masiva.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
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
class CambioSituacion:
    """Cambio en la situación de un expediente."""
    numero: str
    caratula: str
    situacion_anterior: str
    situacion_nueva: str

    def to_dict(self) -> Dict:
        return {
            "numero": self.numero,
            "caratula": self.caratula,
            "situacion_anterior": self.situacion_anterior,
            "situacion_nueva": self.situacion_nueva
        }


@dataclass
class CambioUltimaActuacion:
    """Cambio en la última actuación de un expediente."""
    numero: str
    caratula: str
    ultima_actuacion_anterior: str
    ultima_actuacion_nueva: str

    def to_dict(self) -> Dict:
        return {
            "numero": self.numero,
            "caratula": self.caratula,
            "ultima_actuacion_anterior": self.ultima_actuacion_anterior,
            "ultima_actuacion_nueva": self.ultima_actuacion_nueva
        }


@dataclass
class CambioDependencia:
    """Cambio en la dependencia de un expediente."""
    numero: str
    caratula: str
    dependencia_anterior: str
    dependencia_nueva: str

    def to_dict(self) -> Dict:
        return {
            "numero": self.numero,
            "caratula": self.caratula,
            "dependencia_anterior": self.dependencia_anterior,
            "dependencia_nueva": self.dependencia_nueva
        }


@dataclass
class ComparacionDetallada:
    """Comparación detallada entre listados."""
    nuevos: List[ExpedienteListado]
    eliminados: List[ExpedienteListado]
    cambios_situacion: List[CambioSituacion]
    cambios_ultima_actuacion: List[CambioUltimaActuacion]
    cambios_dependencia: List[CambioDependencia]
    total_cambios: int

    def to_dict(self) -> Dict:
        return {
            "nuevos": [e.to_dict() for e in self.nuevos],
            "eliminados": [e.to_dict() for e in self.eliminados],
            "cambios_situacion": [c.to_dict() for c in self.cambios_situacion],
            "cambios_ultima_actuacion": [c.to_dict() for c in self.cambios_ultima_actuacion],
            "cambios_dependencia": [c.to_dict() for c in self.cambios_dependencia],
            "total_cambios": self.total_cambios,
            "total_nuevos": len(self.nuevos),
            "total_eliminados": len(self.eliminados),
            "total_modificados": (
                len(self.cambios_situacion) +
                len(self.cambios_ultima_actuacion) +
                len(self.cambios_dependencia)
            )
        }


@dataclass
class ConfigExtraccionMasiva:
    """Configuración para la extracción masiva."""
    headless: bool = True
    umbral_errores: int = 10
    timeout_pagina: int = 30000
    max_reintentos: int = 3
    procesar_con_pdf: bool = False
    incluir_historicas: bool = True
    min_utilidad: str = "MEDIA"
    directorio_base: str = "./Sistema_v6/data/expedientes"
    # Opciones avanzadas de extracción
    detener_en_duplicado: bool = True
    omitir_duplicados: bool = True
    max_paginas: int | None = None
    tiempo_maximo_segundos: int | None = None

    def __post_init__(self):
        """Valida los campos opcionales después de la inicialización."""
        if self.max_paginas is not None and self.max_paginas <= 0:
            raise ValueError(f"max_paginas debe ser un valor positivo o None, recibido: {self.max_paginas}")
        if self.tiempo_maximo_segundos is not None and self.tiempo_maximo_segundos <= 0:
            raise ValueError(f"tiempo_maximo_segundos debe ser un valor positivo o None, recibido: {self.tiempo_maximo_segundos}")

    def to_dict(self) -> Dict:
        return {
            "headless": self.headless,
            "umbral_errores": self.umbral_errores,
            "timeout_pagina": self.timeout_pagina,
            "max_reintentos": self.max_reintentos,
            "procesar_con_pdf": self.procesar_con_pdf,
            "incluir_historicas": self.incluir_historicas,
            "min_utilidad": self.min_utilidad,
            "directorio_base": self.directorio_base,
            "detener_en_duplicado": self.detener_en_duplicado,
            "omitir_duplicados": self.omitir_duplicados,
            "max_paginas": self.max_paginas,
            "tiempo_maximo_segundos": self.tiempo_maximo_segundos
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
    archivos_descargados: int = 0

    def to_dict(self) -> Dict:
        return {
            "total": self.total,
            "exitosos": self.exitosos,
            "errores": self.errores,
            "omitidos": self.omitidos,
            "tiempo_total": self.tiempo_total,
            "tasa_exito": round((self.exitosos / self.total * 100) if self.total > 0 else 0, 2),
            "errores_detalles": self.errores_detalles,
            "archivos_descargados": self.archivos_descargados
        }


@dataclass
class SesionExtraccion:
    """Sesión de extracción masiva."""
    session_id: str
    estado: str  # iniciando, extrayendo, completado, error, error_agotado
    fase: str  # listado, procesamiento
    tiempo_inicio: str
    tiempo_fin: Optional[str] = None
    config: Dict = field(default_factory=dict)
    progreso_actual: int = 0
    progreso_total: int = 0
    mensaje: str = ""
    listado_path: Optional[str] = None
    comparacion: Optional[Dict] = None
    paginas_procesadas: int = 0  # Total de páginas procesadas en la extracción masiva inicial
    archivos_descargados: int = 0  # Total de archivos descargados durante procesamiento
    motivo_finalizacion: Optional[str] = None  # Motivo por el cual terminó la extracción
    # Campos de reintentos
    intentos_realizados: int = 0  # Número de intentos realizados
    intentos_maximos: int = 3  # Máximo de reintentos permitidos
    historial_intentos: List[Dict[str, Any]] = field(default_factory=list)  # Historial de cada intento
    # Metadata de extracción (incluye total_esperado, paginas_esperadas, etc.)
    metadata: Dict[str, Any] = field(default_factory=dict)

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
            "paginas_procesadas": self.paginas_procesadas,
            "archivos_descargados": self.archivos_descargados,
            "motivo_finalizacion": self.motivo_finalizacion,
            "intentos_realizados": self.intentos_realizados,
            "intentos_maximos": self.intentos_maximos,
            "historial_intentos": self.historial_intentos,
            "metadata": self.metadata
        }
