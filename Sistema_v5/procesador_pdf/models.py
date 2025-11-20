"""
Modelos de datos para el procesador de PDFs de actuaciones judiciales.

Representa los resultados de clasificación, detección de duplicados,
extracción de vencimientos y análisis de contenido.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import Optional, List, Dict, Any


class UtilidadJuridica(Enum):
    """Nivel de utilidad jurídica de una actuación."""
    NULA = "nula"
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"


class TipoDuplicado(Enum):
    """Tipo de duplicado detectado."""
    EXACTO = "exacto"          # Hash idéntico
    SEMANTICO = "semantico"    # Contenido similar
    PARCIAL = "parcial"        # Similitud parcial


class TipoVencimiento(Enum):
    """Tipo de vencimiento detectado."""
    CEDULA_ELECTRONICA = "cedula_electronica"
    CEDULA_FISICA = "cedula_fisica"
    TRASLADO = "traslado"
    ALEGATO = "alegato"
    PRESENTACION = "presentacion"
    OTRO = "otro"


@dataclass
class ClasificacionActuacion:
    """
    Resultado de la clasificación de utilidad jurídica de una actuación.

    Attributes:
        utilidad: Nivel de utilidad (nula, baja, media, alta)
        score: Puntuación 0-100
        motivo: Explicación de la clasificación
        requiere_pdf: Si necesita abrir el PDF para confirmar
        es_duplicado_probable: Si parece ser un duplicado
        tiene_plazo_probable: Si probablemente contiene un plazo
        keywords_detectados: Palabras clave que influyeron en la clasificación
        timestamp: Momento de la clasificación
    """
    utilidad: UtilidadJuridica
    score: int  # 0-100
    motivo: str
    requiere_pdf: bool = False
    es_duplicado_probable: bool = False
    tiene_plazo_probable: bool = False
    keywords_detectados: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización."""
        return {
            "utilidad": self.utilidad.value,
            "score": self.score,
            "motivo": self.motivo,
            "requiere_pdf": self.requiere_pdf,
            "es_duplicado_probable": self.es_duplicado_probable,
            "tiene_plazo_probable": self.tiene_plazo_probable,
            "keywords_detectados": self.keywords_detectados,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class DuplicadoDetectado:
    """
    Información sobre un duplicado detectado.

    Attributes:
        actuacion_id_original: ID de la actuación original (a conservar)
        actuacion_id_duplicada: ID de la actuación duplicada
        tipo: Tipo de duplicado (exacto, semántico, parcial)
        similitud: Porcentaje de similitud (0.0-1.0)
        hash_normalizado: Hash del contenido normalizado
        motivo: Explicación de por qué se considera duplicado
        timestamp: Momento de detección
    """
    actuacion_id_original: int
    actuacion_id_duplicada: int
    tipo: TipoDuplicado
    similitud: float  # 0.0-1.0
    hash_normalizado: Optional[str] = None
    motivo: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización."""
        return {
            "actuacion_id_original": self.actuacion_id_original,
            "actuacion_id_duplicada": self.actuacion_id_duplicada,
            "tipo": self.tipo.value,
            "similitud": self.similitud,
            "hash_normalizado": self.hash_normalizado,
            "motivo": self.motivo,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class Vencimiento:
    """
    Información sobre un vencimiento o plazo detectado.

    Attributes:
        tipo: Tipo de vencimiento
        fecha_notificacion: Fecha de notificación/inicio del plazo
        plazo_dias: Cantidad de días del plazo
        fecha_vencimiento: Fecha de vencimiento calculada
        dias_habiles: Si el plazo es en días hábiles
        descripcion: Descripción del vencimiento
        actuacion_id: ID de la actuación origen
        texto_fuente: Fragmento de texto donde se detectó
        confianza: Nivel de confianza en la detección (0.0-1.0)
        timestamp: Momento de detección
    """
    tipo: TipoVencimiento
    fecha_notificacion: date
    plazo_dias: int
    fecha_vencimiento: date
    dias_habiles: bool = True
    descripcion: str = ""
    actuacion_id: Optional[int] = None
    texto_fuente: str = ""
    confianza: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización."""
        return {
            "tipo": self.tipo.value,
            "fecha_notificacion": self.fecha_notificacion.isoformat(),
            "plazo_dias": self.plazo_dias,
            "fecha_vencimiento": self.fecha_vencimiento.isoformat(),
            "dias_habiles": self.dias_habiles,
            "descripcion": self.descripcion,
            "actuacion_id": self.actuacion_id,
            "texto_fuente": self.texto_fuente,
            "confianza": self.confianza,
            "timestamp": self.timestamp.isoformat()
        }

    @property
    def dias_restantes(self) -> int:
        """Calcula días restantes hasta el vencimiento."""
        delta = self.fecha_vencimiento - date.today()
        return delta.days

    @property
    def esta_vencido(self) -> bool:
        """Verifica si el plazo está vencido."""
        return date.today() > self.fecha_vencimiento

    @property
    def es_urgente(self) -> bool:
        """Verifica si el vencimiento es urgente (menos de 3 días)."""
        return 0 <= self.dias_restantes <= 3


@dataclass
class TextoExtraido:
    """
    Texto extraído y normalizado de un PDF.

    Attributes:
        texto_completo: Texto completo extraído
        texto_normalizado: Texto limpio y normalizado
        num_paginas: Cantidad de páginas
        metodo_extraccion: Método usado (embebido, ocr)
        tiene_texto_embebido: Si el PDF tiene texto embebido
        longitud_caracteres: Cantidad de caracteres
        longitud_palabras: Cantidad de palabras estimadas
        hash_contenido: Hash del contenido para deduplicación
        timestamp: Momento de extracción
    """
    texto_completo: str
    texto_normalizado: str
    num_paginas: int
    metodo_extraccion: str  # 'embebido', 'ocr', 'mixto'
    tiene_texto_embebido: bool
    longitud_caracteres: int
    longitud_palabras: int
    hash_contenido: str
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def esta_vacio(self) -> bool:
        """Verifica si el texto extraído está vacío."""
        return len(self.texto_normalizado.strip()) < 10

    @property
    def es_muy_corto(self) -> bool:
        """Verifica si el texto es muy corto (probablemente sin valor)."""
        return self.longitud_palabras < 20

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización."""
        return {
            "num_paginas": self.num_paginas,
            "metodo_extraccion": self.metodo_extraccion,
            "tiene_texto_embebido": self.tiene_texto_embebido,
            "longitud_caracteres": self.longitud_caracteres,
            "longitud_palabras": self.longitud_palabras,
            "hash_contenido": self.hash_contenido,
            "esta_vacio": self.esta_vacio,
            "es_muy_corto": self.es_muy_corto,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class ResultadoProcesamiento:
    """
    Resultado completo del procesamiento de una actuación.

    Combina clasificación, duplicados, vencimientos y texto extraído.
    """
    actuacion_id: int
    clasificacion: ClasificacionActuacion
    texto: Optional[TextoExtraido] = None
    duplicados: List[DuplicadoDetectado] = field(default_factory=list)
    vencimientos: List[Vencimiento] = field(default_factory=list)
    errores: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def tiene_errores(self) -> bool:
        """Verifica si hubo errores en el procesamiento."""
        return len(self.errores) > 0

    @property
    def es_duplicado(self) -> bool:
        """Verifica si se detectaron duplicados."""
        return len(self.duplicados) > 0

    @property
    def tiene_vencimientos(self) -> bool:
        """Verifica si se detectaron vencimientos."""
        return len(self.vencimientos) > 0

    @property
    def requiere_atencion(self) -> bool:
        """Verifica si requiere atención (alta utilidad o vencimientos)."""
        return (self.clasificacion.utilidad in [UtilidadJuridica.ALTA, UtilidadJuridica.MEDIA]
                or self.tiene_vencimientos)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización."""
        return {
            "actuacion_id": self.actuacion_id,
            "clasificacion": self.clasificacion.to_dict(),
            "texto": self.texto.to_dict() if self.texto else None,
            "duplicados": [d.to_dict() for d in self.duplicados],
            "vencimientos": [v.to_dict() for v in self.vencimientos],
            "errores": self.errores,
            "tiene_errores": self.tiene_errores,
            "es_duplicado": self.es_duplicado,
            "tiene_vencimientos": self.tiene_vencimientos,
            "requiere_atencion": self.requiere_atencion,
            "timestamp": self.timestamp.isoformat()
        }
