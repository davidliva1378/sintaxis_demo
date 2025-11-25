"""
DTOs (Data Transfer Objects) para el sistema RAG

Define las estructuras de datos utilizadas para:
- Documentos
- Chunks
- Metadata
- Resultados de búsqueda
- Queries
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum


class ChunkType(str, Enum):
    """Tipo de chunk según la sección del documento legal"""
    VISTOS = "vistos"
    CONSIDERANDOS = "considerandos"
    RESUELVE = "resuelve"
    FULL = "full"
    OTHER = "other"


@dataclass
class LegalDocument:
    """Documento legal completo (Actuación)"""
    doc_id: str  # ID único del documento (ej: actuacion_12345)
    expediente_numero: str
    actuacion_id: int
    tipo: str
    fecha: datetime
    contenido: str  # Texto completo
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            "doc_id": self.doc_id,
            "expediente_numero": self.expediente_numero,
            "actuacion_id": self.actuacion_id,
            "tipo": self.tipo,
            "fecha": self.fecha.isoformat() if isinstance(self.fecha, datetime) else self.fecha,
            "contenido": self.contenido,
            "metadata": self.metadata
        }


@dataclass
class DocumentChunk:
    """Chunk de documento con contexto"""
    chunk_id: str  # ID único del chunk
    doc_id: str    # ID del documento padre
    chunk_index: int  # Posición en el documento
    chunk_type: ChunkType  # Tipo de sección legal
    texto: str  # Contenido del chunk
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Embeddings (se llenan después)
    dense_vector: Optional[List[float]] = None
    sparse_vector: Optional[Dict[str, float]] = None  # BM25

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para Qdrant"""
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "chunk_index": self.chunk_index,
            "chunk_type": self.chunk_type.value,
            "texto": self.texto,
            "metadata": self.metadata
        }


@dataclass
class EnrichedMetadata:
    """Metadata enriquecida con NER y patrones legales"""
    # Entidades Named Entity Recognition
    personas: List[str] = field(default_factory=list)
    organizaciones: List[str] = field(default_factory=list)
    lugares: List[str] = field(default_factory=list)

    # Entidades legales específicas
    actores: List[str] = field(default_factory=list)
    demandados: List[str] = field(default_factory=list)
    jueces: List[str] = field(default_factory=list)

    # Referencias legales
    normativa_citada: List[str] = field(default_factory=list)  # Ej: "Art. 123 CPCyC"
    jurisprudencia: List[str] = field(default_factory=list)

    # Montos y plazos
    montos: List[Dict[str, Any]] = field(default_factory=list)  # {"valor": 1000, "moneda": "ARS"}
    fechas: List[datetime] = field(default_factory=list)
    plazos: List[str] = field(default_factory=list)  # Ej: "10 días hábiles"

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            "personas": self.personas,
            "organizaciones": self.organizaciones,
            "lugares": self.lugares,
            "actores": self.actores,
            "demandados": self.demandados,
            "jueces": self.jueces,
            "normativa_citada": self.normativa_citada,
            "jurisprudencia": self.jurisprudencia,
            "montos": self.montos,
            "fechas": [f.isoformat() if isinstance(f, datetime) else f for f in self.fechas],
            "plazos": self.plazos
        }


@dataclass
class SearchQuery:
    """Query de búsqueda"""
    texto: str
    limit: int = 10
    filter_expediente: Optional[str] = None
    filter_tipo: Optional[str] = None
    filter_fecha_desde: Optional[datetime] = None
    filter_fecha_hasta: Optional[datetime] = None


@dataclass
class SearchResult:
    """Resultado de búsqueda con score"""
    chunk: DocumentChunk
    score: float  # Relevancia (0-1)
    rank: int  # Posición en resultados
    highlights: List[str] = field(default_factory=list)  # Snippets relevantes

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            "chunk": self.chunk.to_dict(),
            "score": self.score,
            "rank": self.rank,
            "highlights": self.highlights
        }


@dataclass
class RAGResponse:
    """Respuesta del sistema RAG completo"""
    pregunta: str
    respuesta: str  # Generada por LLM
    resultados: List[SearchResult]  # Chunks utilizados
    metadata: Dict[str, Any] = field(default_factory=dict)  # Info adicional

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            "pregunta": self.pregunta,
            "respuesta": self.respuesta,
            "resultados": [r.to_dict() for r in self.resultados],
            "metadata": self.metadata
        }
