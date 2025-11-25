"""
MetadataEnricher - Servicio para enriquecer chunks con metadata legal

Maneja:
- Named Entity Recognition (NER) con spaCy
- Extracción de entidades legales específicas
- Detección de referencias normativas
- Extracción de montos y fechas
- Detección de plazos legales
"""

import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal
import spacy
from spacy.language import Language

from infrastructure.rag.config import get_rag_settings
from infrastructure.rag.models.dto import (
    DocumentChunk,
    EnrichedMetadata,
)

logger = logging.getLogger(__name__)


class MetadataEnricher:
    """Servicio para enriquecer chunks con metadata legal usando NER y patrones"""

    def __init__(self):
        self.settings = get_rag_settings()
        self.nlp: Optional[Language] = None

        # Patrones para entidades legales específicas
        self.patterns = {
            # Referencias normativas (ej: "Art. 123 del CPCyC", "Ley 24.240")
            "normativa": [
                r'\b(?:Art\.|Artículo|Art)\s*\d+(?:\s*(?:inc\.|inciso)\s*[a-z])?(?:\s+(?:de|del|de la)\s+[\w\s]+)?',
                r'\bLey\s+N?°?\s*\d+[\./]?\d*',
                r'\bDecreto\s+N?°?\s*\d+[\./]?\d*',
                r'\bResolución\s+N?°?\s*\d+[\./]?\d*',
                r'\b(?:C\.?P\.?C\.?y?C\.?|Código\s+Procesal)',
                r'\b(?:C\.?C\.?y?C\.?N?\.?|Código\s+Civil(?:\s+y\s+Comercial)?)',
            ],
            # Montos (ej: "$500.000", "pesos quinientos mil")
            "montos": [
                r'\$\s*\d+(?:[.,]\d+)*',
                r'\bpesos\s+(?:[\w\s]+\s+)?(?:mil|millones?)',
                r'\b\d+(?:[.,]\d+)*\s*(?:pesos|ARS|USD|dólares)',
            ],
            # Plazos (ej: "10 días hábiles", "3 meses")
            "plazos": [
                r'\b\d+\s+(?:días?|meses?|años?)\s*(?:hábiles?|corridos?)?',
                r'\bplazo\s+de\s+\d+\s+(?:días?|meses?)',
            ],
            # Roles legales
            "roles": [
                r'\b(?:actor|demandante|actora)\b',
                r'\b(?:demandado|demandada)\b',
                r'\b(?:juez|jueza|magistrado|magistrada)\b',
                r'\b(?:fiscal|defensor|defensora)\b',
            ],
        }

        # Compilar patrones
        self.compiled_patterns = {
            key: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
            for key, patterns in self.patterns.items()
        }

    def load_model(self) -> None:
        """Cargar modelo spaCy"""
        try:
            logger.info(f"Cargando modelo spaCy: {self.settings.spacy_model}")
            self.nlp = spacy.load(self.settings.spacy_model)
            logger.info(f"✅ Modelo spaCy cargado exitosamente")
        except Exception as e:
            logger.error(f"Error al cargar modelo spaCy: {e}")
            raise

    def enrich_chunk(self, chunk: DocumentChunk) -> EnrichedMetadata:
        """
        Enriquecer un chunk con metadata extraída

        Args:
            chunk: Chunk a enriquecer

        Returns:
            Metadata enriquecida
        """
        try:
            if not self.nlp:
                self.load_model()

            # Procesar texto con spaCy
            doc = self.nlp(chunk.texto)

            # Inicializar metadata
            metadata = EnrichedMetadata()

            # 1. Extraer entidades NER estándar
            self._extract_ner_entities(doc, metadata)

            # 2. Extraer entidades legales específicas
            self._extract_legal_entities(chunk.texto, metadata)

            # 3. Extraer referencias normativas
            self._extract_normativa(chunk.texto, metadata)

            # 4. Extraer montos
            self._extract_montos(chunk.texto, metadata)

            # 5. Extraer plazos
            self._extract_plazos(chunk.texto, metadata)

            logger.debug(f"Chunk {chunk.chunk_id} enriquecido con {len(metadata.personas)} personas, "
                        f"{len(metadata.normativa_citada)} normas")

            return metadata

        except Exception as e:
            logger.error(f"Error al enriquecer chunk {chunk.chunk_id}: {e}")
            # Retornar metadata vacía en caso de error
            return EnrichedMetadata()

    def enrich_chunks(self, chunks: List[DocumentChunk]) -> Dict[str, EnrichedMetadata]:
        """
        Enriquecer múltiples chunks

        Args:
            chunks: Lista de chunks

        Returns:
            Diccionario {chunk_id: metadata}
        """
        try:
            if not self.nlp:
                self.load_model()

            logger.info(f"Enriqueciendo {len(chunks)} chunks...")

            metadata_dict = {}
            for chunk in chunks:
                metadata = self.enrich_chunk(chunk)
                metadata_dict[chunk.chunk_id] = metadata

            logger.info(f"✅ {len(chunks)} chunks enriquecidos")
            return metadata_dict

        except Exception as e:
            logger.error(f"Error al enriquecer chunks: {e}")
            return {}

    # === Métodos privados de extracción ===

    def _extract_ner_entities(self, doc, metadata: EnrichedMetadata) -> None:
        """Extraer entidades usando NER de spaCy"""
        for ent in doc.ents:
            text = ent.text.strip()
            if not text:
                continue

            # Personas
            if ent.label_ == "PER":
                if text not in metadata.personas:
                    metadata.personas.append(text)

            # Organizaciones
            elif ent.label_ == "ORG":
                if text not in metadata.organizaciones:
                    metadata.organizaciones.append(text)

            # Lugares
            elif ent.label_ == "LOC":
                if text not in metadata.lugares:
                    metadata.lugares.append(text)

    def _extract_legal_entities(self, text: str, metadata: EnrichedMetadata) -> None:
        """Extraer entidades legales específicas usando patrones"""
        for pattern in self.compiled_patterns["roles"]:
            for match in pattern.finditer(text):
                role_text = match.group().lower()

                # Buscar contexto (palabras alrededor)
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]

                # Intentar extraer nombre de la persona
                # Buscar nombres propios cerca del rol
                name_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b'
                names = re.findall(name_pattern, context)

                # Clasificar por rol
                if "actor" in role_text or "demandante" in role_text:
                    for name in names:
                        if name not in metadata.actores:
                            metadata.actores.append(name)

                elif "demandado" in role_text or "demandada" in role_text:
                    for name in names:
                        if name not in metadata.demandados:
                            metadata.demandados.append(name)

                elif "juez" in role_text or "magistrado" in role_text:
                    for name in names:
                        if name not in metadata.jueces:
                            metadata.jueces.append(name)

    def _extract_normativa(self, text: str, metadata: EnrichedMetadata) -> None:
        """Extraer referencias normativas"""
        for pattern in self.compiled_patterns["normativa"]:
            for match in pattern.finditer(text):
                norma = match.group().strip()
                if norma and norma not in metadata.normativa_citada:
                    metadata.normativa_citada.append(norma)

    def _extract_montos(self, text: str, metadata: EnrichedMetadata) -> None:
        """Extraer montos monetarios"""
        for pattern in self.compiled_patterns["montos"]:
            for match in pattern.finditer(text):
                monto_text = match.group().strip()

                # Intentar parsear el monto
                try:
                    # Extraer números
                    numbers = re.findall(r'\d+(?:[.,]\d+)*', monto_text)
                    if numbers:
                        # Limpiar separadores
                        value_str = numbers[0].replace('.', '').replace(',', '.')
                        value = float(value_str)

                        # Detectar moneda
                        moneda = "ARS"  # Default
                        if "USD" in monto_text or "dólar" in monto_text.lower():
                            moneda = "USD"

                        monto_dict = {
                            "valor": value,
                            "moneda": moneda,
                            "texto_original": monto_text
                        }

                        # Evitar duplicados
                        if monto_dict not in metadata.montos:
                            metadata.montos.append(monto_dict)

                except (ValueError, IndexError):
                    # Si no se puede parsear, al menos guardar el texto
                    metadata.montos.append({
                        "texto_original": monto_text
                    })

    def _extract_plazos(self, text: str, metadata: EnrichedMetadata) -> None:
        """Extraer plazos legales"""
        for pattern in self.compiled_patterns["plazos"]:
            for match in pattern.finditer(text):
                plazo = match.group().strip()
                if plazo and plazo not in metadata.plazos:
                    metadata.plazos.append(plazo)

    def get_statistics(self, metadata_dict: Dict[str, EnrichedMetadata]) -> Dict[str, Any]:
        """
        Obtener estadísticas de metadata enriquecida

        Args:
            metadata_dict: Diccionario de metadata por chunk

        Returns:
            Estadísticas agregadas
        """
        if not metadata_dict:
            return {}

        stats = {
            "total_chunks": len(metadata_dict),
            "total_personas": 0,
            "total_organizaciones": 0,
            "total_lugares": 0,
            "total_actores": 0,
            "total_demandados": 0,
            "total_jueces": 0,
            "total_normativa": 0,
            "total_montos": 0,
            "total_plazos": 0,
            "chunks_con_metadata": 0,
        }

        for metadata in metadata_dict.values():
            if (metadata.personas or metadata.organizaciones or
                metadata.normativa_citada or metadata.montos):
                stats["chunks_con_metadata"] += 1

            stats["total_personas"] += len(metadata.personas)
            stats["total_organizaciones"] += len(metadata.organizaciones)
            stats["total_lugares"] += len(metadata.lugares)
            stats["total_actores"] += len(metadata.actores)
            stats["total_demandados"] += len(metadata.demandados)
            stats["total_jueces"] += len(metadata.jueces)
            stats["total_normativa"] += len(metadata.normativa_citada)
            stats["total_montos"] += len(metadata.montos)
            stats["total_plazos"] += len(metadata.plazos)

        return stats
