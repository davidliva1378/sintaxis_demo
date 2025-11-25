"""
LegalChunker - Servicio para dividir documentos legales en chunks semánticos

Maneja:
- Detección de secciones legales (VISTOS, CONSIDERANDOS, RESUELVE)
- Chunking semántico con overlap
- Preservación de contexto legal
- Generación de IDs únicos para chunks
"""

import logging
import re
import uuid
from typing import List, Dict, Tuple, Optional
from datetime import datetime

from infrastructure.rag.config import get_rag_settings
from infrastructure.rag.models.dto import (
    LegalDocument,
    DocumentChunk,
    ChunkType,
)

logger = logging.getLogger(__name__)


class LegalChunker:
    """Servicio para dividir documentos legales en chunks semánticos"""

    def __init__(self):
        self.settings = get_rag_settings()

        # Patrones para detectar secciones legales
        self.section_patterns = {
            ChunkType.VISTOS: [
                r'\bVISTOS?\b',
                r'\bVISTO Y CONSIDERANDO\b',
                r'\bY\s+VISTOS?\b',
            ],
            ChunkType.CONSIDERANDOS: [
                r'\bCONSIDERANDOS?\b',
                r'\bY\s+CONSIDERANDO\b',
                r'\bCONSIDERANDO QUE\b',
            ],
            ChunkType.RESUELVE: [
                r'\bRESUELVE\b',
                r'\bSE\s+RESUELVE\b',
                r'\bRESOLUCIÓN\b',
                r'\bFALLA\b',
                r'\bDISPONE\b',
            ],
        }

        # Compilar patrones
        self.compiled_patterns = {
            chunk_type: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
            for chunk_type, patterns in self.section_patterns.items()
        }

    def chunk_document(self, document: LegalDocument) -> List[DocumentChunk]:
        """
        Dividir documento en chunks semánticos

        Args:
            document: Documento legal a procesar

        Returns:
            Lista de chunks con metadata
        """
        try:
            logger.info(f"Procesando documento: {document.doc_id}")

            # 1. Detectar secciones del documento
            sections = self._detect_sections(document.contenido)

            if not sections:
                logger.warning(f"No se detectaron secciones en {document.doc_id}, usando chunk completo")
                return self._create_full_document_chunk(document)

            # 2. Crear chunks por sección
            chunks = []
            for section_type, section_text, section_start, section_end in sections:
                section_chunks = self._chunk_section(
                    section_text=section_text,
                    section_type=section_type,
                    document=document,
                    start_position=section_start,
                )
                chunks.extend(section_chunks)

            # 3. Asignar índices
            for idx, chunk in enumerate(chunks):
                chunk.chunk_index = idx

            logger.info(f"✅ Documento dividido en {len(chunks)} chunks")
            return chunks

        except Exception as e:
            logger.error(f"Error al procesar documento {document.doc_id}: {e}")
            raise

    def _detect_sections(self, text: str) -> List[Tuple[ChunkType, str, int, int]]:
        """
        Detectar secciones legales en el texto

        Returns:
            Lista de tuplas (tipo, texto, posición_inicio, posición_fin)
        """
        sections = []

        # Buscar todas las ocurrencias de patrones
        matches = []
        for chunk_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                for match in pattern.finditer(text):
                    matches.append((match.start(), chunk_type, match.group()))

        # Ordenar por posición
        matches.sort(key=lambda x: x[0])

        if not matches:
            return []

        # Crear secciones basadas en los matches
        for i, (start_pos, chunk_type, match_text) in enumerate(matches):
            # Determinar fin de la sección (inicio de la siguiente o fin del texto)
            if i < len(matches) - 1:
                end_pos = matches[i + 1][0]
            else:
                end_pos = len(text)

            section_text = text[start_pos:end_pos].strip()

            # Solo agregar si tiene contenido significativo
            if len(section_text) > 50:  # Mínimo 50 caracteres
                sections.append((chunk_type, section_text, start_pos, end_pos))

        logger.debug(f"Detectadas {len(sections)} secciones")
        return sections

    def _chunk_section(
        self,
        section_text: str,
        section_type: ChunkType,
        document: LegalDocument,
        start_position: int,
    ) -> List[DocumentChunk]:
        """
        Dividir una sección en chunks con overlap

        Args:
            section_text: Texto de la sección
            section_type: Tipo de sección legal
            document: Documento padre
            start_position: Posición inicial en el documento

        Returns:
            Lista de chunks de la sección
        """
        chunks = []
        chunk_size = self.settings.chunk_size
        chunk_overlap = self.settings.chunk_overlap

        # Si la sección es más pequeña que el chunk_size, un solo chunk
        if len(section_text) <= chunk_size:
            chunk = self._create_chunk(
                texto=section_text,
                chunk_type=section_type,
                document=document,
                chunk_index=0,
            )
            return [chunk]

        # Dividir por párrafos primero (mejor semántica)
        paragraphs = self._split_into_paragraphs(section_text)

        current_chunk = ""
        current_chunk_start = 0

        for para in paragraphs:
            # Si agregar este párrafo excede el tamaño, crear chunk
            if len(current_chunk) + len(para) > chunk_size and current_chunk:
                # Crear chunk
                chunk = self._create_chunk(
                    texto=current_chunk.strip(),
                    chunk_type=section_type,
                    document=document,
                    chunk_index=len(chunks),
                )
                chunks.append(chunk)

                # Preparar siguiente chunk con overlap
                # Usar las últimas palabras como overlap
                overlap_text = self._get_overlap_text(current_chunk, chunk_overlap)
                current_chunk = overlap_text + " " + para
            else:
                # Agregar párrafo al chunk actual
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para

            # Si el chunk actual es demasiado largo (ej: un párrafo gigante)
            # dividirlo por caracteres
            while len(current_chunk) > chunk_size * 1.5:  # 1.5x para dar margen
                # Cortar en chunk_size
                split_point = chunk_size
                # Buscar espacio más cercano para no cortar palabras
                while split_point > 0 and current_chunk[split_point] != ' ':
                    split_point -= 1

                if split_point == 0:  # No hay espacios, cortar en chunk_size
                    split_point = chunk_size

                # Crear chunk
                chunk_text = current_chunk[:split_point].strip()
                chunk = self._create_chunk(
                    texto=chunk_text,
                    chunk_type=section_type,
                    document=document,
                    chunk_index=len(chunks),
                )
                chunks.append(chunk)

                # Preparar siguiente con overlap
                overlap_text = self._get_overlap_text(chunk_text, chunk_overlap)
                current_chunk = overlap_text + current_chunk[split_point:]

        # Agregar último chunk si tiene contenido
        if current_chunk.strip():
            chunk = self._create_chunk(
                texto=current_chunk.strip(),
                chunk_type=section_type,
                document=document,
                chunk_index=len(chunks),
            )
            chunks.append(chunk)

        return chunks

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Dividir texto en párrafos"""
        # Separar por doble salto de línea o puntos seguidos
        paragraphs = re.split(r'\n\s*\n|(?<=[.!?])\s{2,}', text)
        # Limpiar y filtrar vacíos
        return [p.strip() for p in paragraphs if p.strip()]

    def _get_overlap_text(self, text: str, overlap_size: int) -> str:
        """Obtener últimos N caracteres para overlap"""
        if len(text) <= overlap_size:
            return text

        # Intentar cortar en un espacio para no partir palabras
        overlap_text = text[-overlap_size:]
        first_space = overlap_text.find(' ')
        if first_space > 0:
            return overlap_text[first_space:].strip()
        return overlap_text.strip()

    def _create_chunk(
        self,
        texto: str,
        chunk_type: ChunkType,
        document: LegalDocument,
        chunk_index: int,
    ) -> DocumentChunk:
        """Crear un DocumentChunk con metadata"""

        chunk_id = f"{document.doc_id}_chunk_{uuid.uuid4().hex[:8]}"

        # Metadata del chunk
        metadata = {
            "expediente_numero": document.expediente_numero,
            "actuacion_id": document.actuacion_id,
            "tipo_actuacion": document.tipo,
            "fecha_actuacion": document.fecha.isoformat() if isinstance(document.fecha, datetime) else document.fecha,
            **document.metadata,  # Heredar metadata del documento
        }

        chunk = DocumentChunk(
            chunk_id=chunk_id,
            doc_id=document.doc_id,
            chunk_index=chunk_index,
            chunk_type=chunk_type,
            texto=texto,
            metadata=metadata,
        )

        return chunk

    def _create_full_document_chunk(self, document: LegalDocument) -> List[DocumentChunk]:
        """
        Crear chunks del documento completo cuando no se detectan secciones

        Args:
            document: Documento a procesar

        Returns:
            Lista con un chunk del documento completo
        """
        chunks = self._chunk_section(
            section_text=document.contenido,
            section_type=ChunkType.FULL,
            document=document,
            start_position=0,
        )

        return chunks

    def get_chunk_stats(self, chunks: List[DocumentChunk]) -> Dict[str, any]:
        """
        Obtener estadísticas de los chunks

        Args:
            chunks: Lista de chunks

        Returns:
            Diccionario con estadísticas
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "avg_length": 0,
                "min_length": 0,
                "max_length": 0,
                "by_type": {},
            }

        lengths = [len(chunk.texto) for chunk in chunks]
        by_type = {}

        for chunk in chunks:
            chunk_type = chunk.chunk_type.value
            if chunk_type not in by_type:
                by_type[chunk_type] = 0
            by_type[chunk_type] += 1

        return {
            "total_chunks": len(chunks),
            "avg_length": sum(lengths) // len(lengths),
            "min_length": min(lengths),
            "max_length": max(lengths),
            "by_type": by_type,
        }
