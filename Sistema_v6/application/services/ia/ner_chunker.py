"""
NER Chunker Service - Chunking Inteligente para Textos Largos (TAREA 2.4)

Funcionalidades:
- Divide textos largos en chunks para NER
- Mantiene contexto entre chunks (overlap)
- Fusiona entidades de chunks adyacentes
- Maneja entidades que cruzan límites de chunks
- Optimizado para documentos legales argentinos
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ChunkResult:
    """Resultado de un chunk procesado"""
    chunk_id: int
    start_pos: int
    end_pos: int
    text: str
    entities: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class MergedEntity:
    """Entidad fusionada de múltiples chunks"""
    text: str
    label: str
    score: float
    start: int
    end: int
    chunk_ids: List[int] = field(default_factory=list)
    merged: bool = False


class NERChunker:
    """
    Servicio para procesar textos largos con NER mediante chunking.

    Divide textos en chunks manejables, procesa cada uno con NER,
    y luego fusiona los resultados eliminando duplicados y manejando
    entidades que cruzan límites de chunks.
    """

    # Límites recomendados para GLiNER
    DEFAULT_CHUNK_SIZE = 1500  # caracteres
    DEFAULT_OVERLAP = 200  # caracteres de overlap

    # Patrones para encontrar buenos puntos de corte
    SENTENCE_ENDINGS = r'[.!?]\s+'
    PARAGRAPH_ENDINGS = r'\n\s*\n'
    LEGAL_MARKERS = r'(?:VISTOS|RESULTA|CONSIDERANDO|RESUELVE|FALLO|POR ELLO|SE RESUELVE):'

    def __init__(
        self,
        ner_service=None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_OVERLAP
    ):
        """
        Args:
            ner_service: Servicio NER a usar
            chunk_size: Tamaño máximo de cada chunk
            overlap: Caracteres de overlap entre chunks
        """
        self._ner_service = ner_service
        self.chunk_size = chunk_size
        self.overlap = overlap

        logger.info(f"NERChunker inicializado: chunk_size={chunk_size}, overlap={overlap}")

    @property
    def ner_service(self):
        """Lazy loading del servicio NER"""
        if self._ner_service is None:
            try:
                from application.services.ia.ner_service import NERService
                self._ner_service = NERService()
            except Exception as e:
                logger.error(f"No se pudo cargar NERService: {e}")
                raise
        return self._ner_service

    def process_long_text(
        self,
        text: str,
        labels: Optional[List[str]] = None,
        threshold: float = 0.5,
        use_enhanced: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Procesa un texto largo con NER mediante chunking.

        Args:
            text: Texto a procesar (puede ser muy largo)
            labels: Etiquetas de entidades a buscar
            threshold: Umbral de confianza
            use_enhanced: Si usar extract_enhanced con LLM fallback

        Returns:
            Lista de entidades fusionadas y deduplicadas
        """
        # Si el texto es corto, procesar directamente
        if len(text) <= self.chunk_size:
            if use_enhanced:
                return self.ner_service.extract_enhanced(text, labels, threshold)
            else:
                return self.ner_service.extract(text, labels, threshold)

        logger.info(f"Procesando texto largo: {len(text)} caracteres en chunks")

        # 1. Dividir en chunks
        chunks = self._create_chunks(text)
        logger.info(f"Creados {len(chunks)} chunks")

        # 2. Procesar cada chunk
        chunk_results = []
        for i, chunk in enumerate(chunks):
            entities = self._process_chunk(
                chunk,
                labels=labels,
                threshold=threshold,
                use_enhanced=use_enhanced
            )

            chunk_result = ChunkResult(
                chunk_id=i,
                start_pos=chunk["start"],
                end_pos=chunk["end"],
                text=chunk["text"],
                entities=entities
            )
            chunk_results.append(chunk_result)

        # 3. Fusionar resultados
        merged = self._merge_chunk_results(chunk_results)

        logger.info(f"Extraídas {len(merged)} entidades de texto largo")
        return merged

    def _create_chunks(self, text: str) -> List[Dict[str, Any]]:
        """
        Divide el texto en chunks con overlap.

        Intenta cortar en puntos naturales (fin de oración, párrafo, etc.)
        """
        chunks = []
        pos = 0
        text_len = len(text)

        while pos < text_len:
            # Calcular fin del chunk
            end = min(pos + self.chunk_size, text_len)

            if end < text_len:
                # Buscar mejor punto de corte
                end = self._find_cut_point(text, pos, end)

            chunk_text = text[pos:end]

            chunks.append({
                "start": pos,
                "end": end,
                "text": chunk_text
            })

            # Siguiente chunk con overlap
            if end < text_len:
                pos = end - self.overlap
            else:
                break

        return chunks

    def _find_cut_point(self, text: str, start: int, end: int) -> int:
        """
        Encuentra el mejor punto para cortar el texto.

        Prioridad:
        1. Marcadores legales (VISTOS:, CONSIDERANDO:, etc.)
        2. Fin de párrafo
        3. Fin de oración
        4. Espacio en blanco
        """
        search_start = max(start, end - 300)  # Buscar en los últimos 300 chars
        search_text = text[search_start:end]

        # 1. Buscar marcadores legales
        for match in re.finditer(self.LEGAL_MARKERS, search_text):
            cut_pos = search_start + match.start()
            if cut_pos > start + self.chunk_size // 2:  # No cortar muy cerca del inicio
                return cut_pos

        # 2. Buscar fin de párrafo
        for match in re.finditer(self.PARAGRAPH_ENDINGS, search_text):
            cut_pos = search_start + match.end()
            if cut_pos > start + self.chunk_size // 2:
                return cut_pos

        # 3. Buscar fin de oración
        for match in re.finditer(self.SENTENCE_ENDINGS, search_text):
            cut_pos = search_start + match.end()
            if cut_pos > start + self.chunk_size // 2:
                return cut_pos

        # 4. Buscar espacio
        last_space = search_text.rfind(' ')
        if last_space > 0:
            return search_start + last_space + 1

        # Default: cortar en el límite
        return end

    def _process_chunk(
        self,
        chunk: Dict[str, Any],
        labels: Optional[List[str]],
        threshold: float,
        use_enhanced: bool
    ) -> List[Dict[str, Any]]:
        """Procesa un chunk individual con NER"""
        try:
            if use_enhanced:
                entities = self.ner_service.extract_enhanced(
                    chunk["text"],
                    labels,
                    threshold
                )
            else:
                entities = self.ner_service.extract(
                    chunk["text"],
                    labels,
                    threshold
                )

            # Ajustar posiciones al texto original
            for entity in entities:
                entity["start"] = chunk["start"] + entity.get("start", 0)
                entity["end"] = chunk["start"] + entity.get("end", len(entity["text"]))

            return entities

        except Exception as e:
            logger.warning(f"Error procesando chunk: {e}")
            return []

    def _merge_chunk_results(
        self,
        chunk_results: List[ChunkResult]
    ) -> List[Dict[str, Any]]:
        """
        Fusiona resultados de múltiples chunks.

        - Elimina duplicados exactos
        - Fusiona entidades que aparecen en múltiples chunks
        - Maneja entidades parciales en zonas de overlap
        """
        if not chunk_results:
            return []

        # Recolectar todas las entidades
        all_entities: List[MergedEntity] = []

        for chunk in chunk_results:
            for entity in chunk.entities:
                merged_entity = MergedEntity(
                    text=entity["text"],
                    label=entity["label"],
                    score=entity.get("score", 1.0),
                    start=entity.get("start", 0),
                    end=entity.get("end", 0),
                    chunk_ids=[chunk.chunk_id],
                    merged=False
                )
                all_entities.append(merged_entity)

        # Ordenar por posición
        all_entities.sort(key=lambda x: x.start)

        # Fusionar duplicados y overlaps
        merged = self._deduplicate_entities(all_entities)

        # Convertir a formato dict
        return [
            {
                "text": e.text,
                "label": e.label,
                "score": e.score,
                "start": e.start,
                "end": e.end,
                "chunk_ids": e.chunk_ids,
                "merged": e.merged
            }
            for e in merged
        ]

    def _deduplicate_entities(
        self,
        entities: List[MergedEntity]
    ) -> List[MergedEntity]:
        """
        Elimina duplicados y fusiona entidades overlapping.

        Criterios de fusión:
        - Mismo texto exacto y mismo label
        - Posiciones overlapping con texto similar
        """
        if not entities:
            return []

        result = []
        used = set()

        for i, entity in enumerate(entities):
            if i in used:
                continue

            # Buscar duplicados/similares
            merged = entity
            merged_indices = [i]

            for j in range(i + 1, len(entities)):
                if j in used:
                    continue

                other = entities[j]

                # Mismo texto y label
                if self._is_same_entity(merged, other):
                    merged = self._merge_two_entities(merged, other)
                    merged_indices.append(j)
                    merged.merged = True

                # Posiciones muy cercanas con texto similar
                elif self._is_overlapping(merged, other):
                    # Tomar el de mayor score
                    if other.score > merged.score:
                        merged = other
                        merged.merged = True
                    merged_indices.append(j)

            # Marcar usados
            for idx in merged_indices:
                used.add(idx)

            result.append(merged)

        return result

    def _is_same_entity(self, e1: MergedEntity, e2: MergedEntity) -> bool:
        """Verifica si dos entidades son la misma"""
        # Mismo texto exacto (ignorando mayúsculas) y mismo label
        return (
            e1.text.lower().strip() == e2.text.lower().strip() and
            e1.label == e2.label
        )

    def _is_overlapping(self, e1: MergedEntity, e2: MergedEntity) -> bool:
        """Verifica si dos entidades tienen posiciones overlapping"""
        # Mismo label
        if e1.label != e2.label:
            return False

        # Posiciones overlapping
        overlap = min(e1.end, e2.end) - max(e1.start, e2.start)
        min_len = min(len(e1.text), len(e2.text))

        # Si hay más del 50% de overlap
        return overlap > min_len * 0.5

    def _merge_two_entities(
        self,
        e1: MergedEntity,
        e2: MergedEntity
    ) -> MergedEntity:
        """Fusiona dos entidades en una"""
        return MergedEntity(
            text=e1.text if e1.score >= e2.score else e2.text,
            label=e1.label,
            score=max(e1.score, e2.score),
            start=min(e1.start, e2.start),
            end=max(e1.end, e2.end),
            chunk_ids=list(set(e1.chunk_ids + e2.chunk_ids)),
            merged=True
        )

    def estimate_chunks(self, text_length: int) -> int:
        """
        Estima cuántos chunks se necesitarán.

        Args:
            text_length: Longitud del texto

        Returns:
            Número estimado de chunks
        """
        if text_length <= self.chunk_size:
            return 1

        effective_chunk = self.chunk_size - self.overlap
        return (text_length - self.chunk_size) // effective_chunk + 2

    def get_stats(self, text: str) -> Dict[str, Any]:
        """
        Obtiene estadísticas del texto para chunking.

        Args:
            text: Texto a analizar

        Returns:
            Dict con estadísticas
        """
        chunks = self._create_chunks(text)

        return {
            "text_length": len(text),
            "num_chunks": len(chunks),
            "chunk_size": self.chunk_size,
            "overlap": self.overlap,
            "avg_chunk_length": sum(len(c["text"]) for c in chunks) / len(chunks) if chunks else 0,
            "estimated_processing_time": f"{len(chunks) * 0.5:.1f}s"  # ~0.5s por chunk
        }
