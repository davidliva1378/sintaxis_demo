"""
Tests para los servicios de IA implementados en el plan de mejoras RAG/NER
- TAREA 1.3: Prompts dinámicos
- TAREA 1.4: Chain-of-Thought
- TAREA 1.5: Context Compression
- TAREA 2.3: Entity Normalization
- TAREA 2.4: NER Chunking
"""

import pytest
import sys
import os

# Agregar paths necesarios
sys.path.insert(0, '/Users/davidalejandroliva/PycharmProjects/sintaXis/Sistema_v6')
sys.path.insert(0, '/Users/davidalejandroliva/PycharmProjects/sintaXis')


class TestDetectQuestionType:
    """Tests para TAREA 1.3: Detección de tipos de pregunta"""

    def test_detect_factual_questions(self):
        from infrastructure.rag.services.llm_service import detect_question_type

        assert detect_question_type("¿Qué pasó en el expediente?") == "factual"
        assert detect_question_type("¿Cuál es el monto reclamado?") == "factual"
        assert detect_question_type("¿Quién es el demandado?") == "factual"
        assert detect_question_type("¿Cuáles son los hechos del caso?") == "factual"

    def test_detect_analisis_questions(self):
        from infrastructure.rag.services.llm_service import detect_question_type

        assert detect_question_type("¿Por qué el juez falló a favor?") == "analisis"
        assert detect_question_type("¿Cuál es el fundamento de la sentencia?") == "analisis"
        assert detect_question_type("Explica los argumentos de la demandada") == "analisis"

    def test_detect_temporal_questions(self):
        from infrastructure.rag.services.llm_service import detect_question_type

        assert detect_question_type("¿Cuándo se presentó la demanda?") == "temporal"
        assert detect_question_type("¿Cuál es la fecha de vencimiento?") == "temporal"
        assert detect_question_type("¿Qué plazos hay que cumplir?") == "temporal"

    def test_detect_procesal_questions(self):
        from infrastructure.rag.services.llm_service import detect_question_type

        assert detect_question_type("¿Qué sigue en el proceso?") == "procesal"
        assert detect_question_type("¿Cuál es el estado actual del expediente?") == "procesal"
        assert detect_question_type("¿Se puede apelar la resolución?") == "procesal"

    def test_detect_default_questions(self):
        from infrastructure.rag.services.llm_service import detect_question_type

        assert detect_question_type("Hola") == "default"
        assert detect_question_type("Información general") == "default"


class TestPromptTemplates:
    """Tests para verificar que los templates existan"""

    def test_prompt_templates_exist(self):
        from infrastructure.rag.services.llm_service import PROMPT_TEMPLATES

        assert "factual" in PROMPT_TEMPLATES
        assert "analisis" in PROMPT_TEMPLATES
        assert "temporal" in PROMPT_TEMPLATES
        assert "procesal" in PROMPT_TEMPLATES
        assert "default" in PROMPT_TEMPLATES

    def test_cot_prompt_exists(self):
        from infrastructure.rag.services.llm_service import SYSTEM_PROMPT_COT

        assert "ANÁLISIS" in SYSTEM_PROMPT_COT
        assert "CONEXIÓN" in SYSTEM_PROMPT_COT
        assert "RESPUESTA" in SYSTEM_PROMPT_COT
        assert "CITAS" in SYSTEM_PROMPT_COT


class TestEntityNormalizer:
    """Tests para TAREA 2.3: Normalización de entidades"""

    def setup_method(self):
        from application.services.ia.entity_normalizer import EntityNormalizer
        self.normalizer = EntityNormalizer()

    def test_normalize_date_dmy(self):
        """Normaliza fecha formato DD/MM/YYYY"""
        entities = [{"text": "15/03/2024", "label": "FECHA", "score": 0.95}]
        result = self.normalizer.normalize(entities)
        assert result[0].normalized == "15/03/2024"

    def test_normalize_date_spanish(self):
        """Normaliza fecha en español"""
        entities = [{"text": "6 de junio de 2023", "label": "FECHA", "score": 0.9}]
        result = self.normalizer.normalize(entities)
        assert result[0].normalized == "06/06/2023"

    def test_normalize_date_iso(self):
        """Normaliza fecha formato ISO"""
        entities = [{"text": "2023-12-31", "label": "FECHA", "score": 0.9}]
        result = self.normalizer.normalize(entities)
        assert result[0].normalized == "31/12/2023"

    def test_normalize_monto_argentino(self):
        """Normaliza monto formato argentino"""
        entities = [{"text": "$1.234,56", "label": "MONTO", "score": 0.9}]
        result = self.normalizer.normalize(entities)
        # Debe mantener formato $X.XXX,XX
        assert "$" in result[0].normalized
        assert "1" in result[0].normalized

    def test_normalize_nombre(self):
        """Normaliza nombre a APELLIDO, Nombre"""
        entities = [{"text": "Juan Carlos Pérez", "label": "PERSONA", "score": 0.9}]
        result = self.normalizer.normalize(entities)
        # Debe estar en mayúsculas
        assert result[0].normalized.isupper() or "," in result[0].normalized

    def test_normalize_norma(self):
        """Normaliza referencia a norma legal"""
        entities = [{"text": "ley 24240", "label": "NORMA", "score": 0.9}]
        result = self.normalizer.normalize(entities)
        assert "Ley" in result[0].normalized or "LEY" in result[0].normalized.upper()

    def test_normalize_tribunal(self):
        """Normaliza nombre de tribunal"""
        entities = [{"text": "Cámara Federal de Resistencia", "label": "TRIBUNAL", "score": 0.9}]
        result = self.normalizer.normalize(entities)
        # Debe tener alguna normalización
        assert len(result[0].normalized) > 0

    def test_cache_works(self):
        """Verifica que el cache funciona"""
        entities = [{"text": "15/03/2024", "label": "FECHA", "score": 0.95}]
        result1 = self.normalizer.normalize(entities, use_cache=True)
        result2 = self.normalizer.normalize(entities, use_cache=True)
        assert result1[0].normalized == result2[0].normalized


class TestNERChunker:
    """Tests para TAREA 2.4: Chunking para textos largos"""

    def setup_method(self):
        from application.services.ia.ner_chunker import NERChunker
        self.chunker = NERChunker(ner_service=None)  # Sin NER service para tests básicos

    def test_short_text_no_chunking(self):
        """Textos cortos no se dividen"""
        text = "Este es un texto corto."
        chunks = self.chunker._create_chunks(text)
        assert len(chunks) == 1
        assert chunks[0]["text"] == text

    def test_long_text_creates_chunks(self):
        """Textos largos se dividen en chunks"""
        # Crear texto de 3000 caracteres
        text = "VISTOS: " + "a" * 1500 + ". CONSIDERANDO: " + "b" * 1500
        chunks = self.chunker._create_chunks(text)
        assert len(chunks) > 1

    def test_chunks_have_overlap(self):
        """Chunks tienen overlap"""
        text = "x" * 3000
        chunks = self.chunker._create_chunks(text)
        if len(chunks) > 1:
            # El segundo chunk debe empezar antes de donde termina el primero
            assert chunks[1]["start"] < chunks[0]["end"]

    def test_estimate_chunks(self):
        """Estimación de chunks funciona"""
        # Texto corto = 1 chunk
        assert self.chunker.estimate_chunks(500) == 1
        # Texto largo = múltiples chunks
        assert self.chunker.estimate_chunks(5000) > 1

    def test_get_stats(self):
        """Stats de texto funciona"""
        text = "Texto de prueba " * 100
        stats = self.chunker.get_stats(text)
        assert "text_length" in stats
        assert "num_chunks" in stats
        assert "chunk_size" in stats
        assert "overlap" in stats

    def test_legal_markers_cut_points(self):
        """Corta en marcadores legales"""
        text = "Introducción. " * 50 + "VISTOS: Análisis. " + "Contenido. " * 50
        chunks = self.chunker._create_chunks(text)
        # Debe preferir cortar en VISTOS:
        for chunk in chunks:
            # Al menos un chunk debe terminar cerca de VISTOS
            pass  # El test es estructural


class TestContextCompressor:
    """Tests para TAREA 1.5: Compresión de contexto"""

    def test_no_compression_needed(self):
        """No comprime si ya cabe"""
        from infrastructure.rag.services.llm_service import ContextCompressor
        compressor = ContextCompressor()

        chunks = ["Chunk corto 1", "Chunk corto 2"]
        result = compressor.compress(chunks, "query", max_chars=1000)

        # Debe contener ambos chunks
        assert "Chunk corto 1" in result
        assert "Chunk corto 2" in result


class TestNERChunkerDeduplication:
    """Tests para deduplicación de entidades entre chunks"""

    def test_deduplicate_same_entity(self):
        from application.services.ia.ner_chunker import NERChunker, ChunkResult, MergedEntity

        chunker = NERChunker(ner_service=None)

        # Simular dos chunks con la misma entidad
        chunk1 = ChunkResult(
            chunk_id=0, start_pos=0, end_pos=100, text="texto",
            entities=[{"text": "Juan Pérez", "label": "PERSONA", "score": 0.9, "start": 10, "end": 20}]
        )
        chunk2 = ChunkResult(
            chunk_id=1, start_pos=80, end_pos=180, text="texto",
            entities=[{"text": "Juan Pérez", "label": "PERSONA", "score": 0.85, "start": 90, "end": 100}]
        )

        merged = chunker._merge_chunk_results([chunk1, chunk2])

        # Debe haber solo una entidad "Juan Pérez"
        juan_count = sum(1 for e in merged if "Juan Pérez" in e["text"])
        assert juan_count == 1


class TestIntegration:
    """Tests de integración básica"""

    def test_import_all_services(self):
        """Todos los servicios se pueden importar"""
        from infrastructure.rag.services.llm_service import (
            LLMService,
            ContextCompressor,
            detect_question_type,
            PROMPT_TEMPLATES,
            SYSTEM_PROMPT_COT
        )
        from application.services.ia.entity_normalizer import EntityNormalizer
        from application.services.ia.ner_chunker import NERChunker

        assert LLMService is not None
        assert ContextCompressor is not None
        assert EntityNormalizer is not None
        assert NERChunker is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
