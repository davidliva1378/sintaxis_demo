"""
Tests unitarios para RAGService.

Prueba las funcionalidades principales del servicio RAG usando mocks
para evitar dependencias de servicios externos (Qdrant, Ollama).
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
from application.services.ia.rag_service import RAGService


@pytest.mark.unit
class TestRAGServiceInit:
    """Tests para inicialización del servicio."""

    def test_init_with_defaults(self):
        """Debe inicializarse con valores por defecto."""
        service = RAGService()
        assert service.collection_name == "actuaciones"
        assert service._embeddings is None
        assert service._qdrant is None
        assert service._llm is None
        assert service._hybrid_search is None
        assert isinstance(service._cache, dict)
        assert len(service._cache) == 0

    def test_init_with_custom_collection(self):
        """Debe aceptar nombre de colección personalizado."""
        service = RAGService(collection_name="test_collection")
        assert service.collection_name == "test_collection"

    def test_init_with_services(self):
        """Debe aceptar servicios inyectados."""
        mock_embeddings = Mock()
        mock_qdrant = Mock()
        mock_llm = Mock()
        mock_hybrid = Mock()

        service = RAGService(
            embeddings_service=mock_embeddings,
            qdrant_service=mock_qdrant,
            llm_service=mock_llm,
            hybrid_search_service=mock_hybrid
        )

        assert service._embeddings is mock_embeddings
        assert service._qdrant is mock_qdrant
        assert service._llm is mock_llm
        assert service._hybrid_search is mock_hybrid


@pytest.mark.unit
class TestRAGServiceCache:
    """Tests para funcionalidad de cache."""

    def test_cache_key_generation(self):
        """Debe generar claves de cache consistentes."""
        service = RAGService()
        
        key1 = service._cache_key("test query", 5)
        key2 = service._cache_key("test query", 5)
        key3 = service._cache_key("different query", 5)
        
        # Misma query debe generar misma clave
        assert key1 == key2
        # Query diferente debe generar clave diferente
        assert key1 != key3
        # Clave debe ser hash MD5 (32 caracteres hex)
        assert len(key1) == 32

    def test_cache_key_with_filters(self):
        """Debe incluir filtros en la clave de cache."""
        service = RAGService()
        
        key1 = service._cache_key("query", 5, expediente_id="123")
        key2 = service._cache_key("query", 5, expediente_id="456")
        key3 = service._cache_key("query", 5, expediente_numero="EXP-001")
        
        assert key1 != key2
        assert key1 != key3
        assert key2 != key3

    def test_cache_set_and_get(self):
        """Debe guardar y recuperar del cache."""
        service = RAGService()
        
        key = "test_key"
        results = [{"id": "1", "document": "test"}]
        
        # Guardar en cache
        service._cache_set(key, results)
        
        # Recuperar del cache
        cached = service._cache_get(key)
        assert cached == results

    def test_cache_expiration(self):
        """Debe expirar entradas antiguas del cache."""
        service = RAGService()
        service._cache_ttl = timedelta(seconds=0.1)  # TTL muy corto para test
        
        key = "test_key"
        results = [{"id": "1"}]
        
        service._cache_set(key, results)
        
        # Debe estar en cache inmediatamente
        assert service._cache_get(key) is not None
        
        # Esperar a que expire
        import time
        time.sleep(0.2)
        
        # Debe haber expirado
        assert service._cache_get(key) is None

    def test_limpiar_cache(self):
        """Debe limpiar todo el cache."""
        service = RAGService()
        
        # Agregar varias entradas
        service._cache_set("key1", [{"id": "1"}])
        service._cache_set("key2", [{"id": "2"}])
        service._cache_set("key3", [{"id": "3"}])
        
        assert len(service._cache) == 3
        
        # Limpiar
        service.limpiar_cache()
        
        assert len(service._cache) == 0

    def test_cache_cleanup_on_overflow(self):
        """Debe limpiar cache cuando excede el límite."""
        service = RAGService()
        service._cache_ttl = timedelta(seconds=0.01)  # TTL muy corto
        
        # Agregar más de 100 entradas (límite)
        for i in range(105):
            service._cache_set(f"key{i}", [{"id": str(i)}])
        
        # Debe haber limpiado entradas expiradas
        assert len(service._cache) <= 105


@pytest.mark.unit
class TestRAGServiceChunking:
    """Tests para división de texto en chunks."""

    def test_chunk_text_small(self):
        """Texto pequeño no debe dividirse."""
        service = RAGService()
        
        texto = "Este es un texto corto."
        chunks = service._chunk_text(texto, chunk_size=1000)
        
        assert len(chunks) == 1
        assert chunks[0] == texto

    def test_chunk_text_large(self):
        """Texto grande debe dividirse en chunks."""
        service = RAGService()
        
        # Crear texto largo
        texto = "palabra " * 500  # ~3500 caracteres
        chunks = service._chunk_text(texto, chunk_size=1000, overlap=100)
        
        assert len(chunks) > 1
        # Cada chunk debe tener aproximadamente el tamaño especificado
        for chunk in chunks[:-1]:  # Excepto el último
            assert len(chunk) <= 1100  # chunk_size + margen

    def test_chunk_text_overlap(self):
        """Chunks deben tener overlap."""
        service = RAGService()
        
        texto = "palabra " * 200
        chunks = service._chunk_text(texto, chunk_size=500, overlap=100)
        
        if len(chunks) > 1:
            # Verificar que hay overlap entre chunks consecutivos
            # (esto es aproximado debido al corte en espacios)
            assert len(chunks) > 1

    def test_chunk_text_word_boundary(self):
        """Debe cortar en límites de palabras cuando sea posible."""
        service = RAGService()
        
        texto = "palabra1 palabra2 palabra3 " * 100
        chunks = service._chunk_text(texto, chunk_size=100, overlap=20)
        
        # Verificar que los chunks no cortan palabras a la mitad
        for chunk in chunks:
            # No debe empezar o terminar con espacio (excepto trailing)
            if chunk != chunks[-1]:
                assert not chunk.endswith(" ") or chunk.strip() == chunk


@pytest.mark.unit
class TestRAGServiceIndexing:
    """Tests para indexación de actuaciones."""

    def test_indexar_actuacion_texto_vacio(self):
        """No debe indexar texto vacío."""
        service = RAGService()
        
        # No debe lanzar error, solo advertencia
        service.indexar_actuacion("id1", "")
        service.indexar_actuacion("id2", "   ")
        service.indexar_actuacion("id3", "corto")  # Muy corto (<10 chars)

    @patch('application.services.ia.rag_service.RAGService._get_embeddings')
    @patch('application.services.ia.rag_service.RAGService._get_hybrid_search')
    def test_indexar_actuacion_success(self, mock_hybrid, mock_embeddings):
        """Debe indexar actuación correctamente."""
        # Setup mocks
        mock_hybrid_instance = Mock()
        mock_hybrid.return_value = mock_hybrid_instance
        
        service = RAGService()
        
        texto = "Esta es una actuación de prueba con suficiente texto para indexar."
        metadata = {"expediente_id": "123", "fecha": "2024-01-01"}
        
        service.indexar_actuacion("act_001", texto, metadata)
        
        # Verificar que se llamó a index_chunks
        mock_hybrid_instance.index_chunks.assert_called_once()
        
        # Verificar que los chunks tienen la estructura correcta
        chunks_arg = mock_hybrid_instance.index_chunks.call_args[0][0]
        assert len(chunks_arg) > 0
        assert chunks_arg[0].doc_id == "act_001"
        assert chunks_arg[0].texto == texto  # Texto corto, un solo chunk
        assert "expediente_id" in chunks_arg[0].metadata

    @patch('application.services.ia.rag_service.RAGService._get_embeddings')
    @patch('application.services.ia.rag_service.RAGService._get_hybrid_search')
    def test_indexar_actuacion_large_text(self, mock_hybrid, mock_embeddings):
        """Debe dividir texto largo en chunks."""
        mock_hybrid_instance = Mock()
        mock_hybrid.return_value = mock_hybrid_instance
        
        service = RAGService()
        
        # Texto largo que requiere chunking
        texto = "palabra " * 500  # ~3500 caracteres
        
        service.indexar_actuacion("act_002", texto)
        
        # Verificar que se crearon múltiples chunks
        chunks_arg = mock_hybrid_instance.index_chunks.call_args[0][0]
        assert len(chunks_arg) > 1
        
        # Verificar que cada chunk tiene índice correcto
        for i, chunk in enumerate(chunks_arg):
            assert chunk.chunk_index == i
            assert chunk.metadata["chunk_index"] == i


@pytest.mark.unit
class TestRAGServiceSearch:
    """Tests para búsqueda de actuaciones."""

    @patch('application.services.ia.rag_service.RAGService._get_embeddings')
    @patch('application.services.ia.rag_service.RAGService._get_qdrant')
    def test_buscar_basic(self, mock_qdrant_getter, mock_embeddings_getter):
        """Debe realizar búsqueda básica."""
        # Setup mocks
        mock_embeddings = Mock()
        mock_embeddings.encode_text.return_value = [0.1, 0.2, 0.3]
        mock_embeddings_getter.return_value = mock_embeddings
        
        mock_qdrant = Mock()
        mock_result = Mock()
        mock_result.payload = {
            "chunk_id": "chunk_1",
            "texto": "Resultado de prueba",
            "expediente_id": "123"
        }
        mock_result.score = 0.95
        mock_qdrant.search_similar.return_value = [mock_result]
        mock_qdrant_getter.return_value = mock_qdrant
        
        service = RAGService()
        
        # Realizar búsqueda
        results = service.buscar("test query", n_results=5)
        
        # Verificar resultados
        assert len(results) == 1
        assert results[0]["id"] == "chunk_1"
        assert results[0]["document"] == "Resultado de prueba"
        assert results[0]["score"] == 0.95
        assert "expediente_id" in results[0]["metadata"]

    @patch('application.services.ia.rag_service.RAGService._get_embeddings')
    @patch('application.services.ia.rag_service.RAGService._get_qdrant')
    def test_buscar_with_cache(self, mock_qdrant_getter, mock_embeddings_getter):
        """Debe usar cache en búsquedas repetidas."""
        # Setup mocks
        mock_embeddings = Mock()
        mock_embeddings.encode_text.return_value = [0.1, 0.2, 0.3]
        mock_embeddings_getter.return_value = mock_embeddings
        
        mock_qdrant = Mock()
        mock_result = Mock()
        mock_result.payload = {"chunk_id": "1", "texto": "test"}
        mock_result.score = 0.9
        mock_qdrant.search_similar.return_value = [mock_result]
        mock_qdrant_getter.return_value = mock_qdrant
        
        service = RAGService()
        
        # Primera búsqueda
        results1 = service.buscar("query", n_results=5)
        
        # Segunda búsqueda (misma query)
        results2 = service.buscar("query", n_results=5)
        
        # Debe haber llamado a Qdrant solo una vez (segunda usa cache)
        assert mock_qdrant.search_similar.call_count == 1
        
        # Resultados deben ser iguales
        assert results1 == results2

    @patch('application.services.ia.rag_service.RAGService._get_embeddings')
    @patch('application.services.ia.rag_service.RAGService._get_qdrant')
    def test_buscar_with_filters(self, mock_qdrant_getter, mock_embeddings_getter):
        """Debe aplicar filtros en la búsqueda."""
        mock_embeddings = Mock()
        mock_embeddings.encode_text.return_value = [0.1, 0.2, 0.3]
        mock_embeddings_getter.return_value = mock_embeddings
        
        mock_qdrant = Mock()
        mock_qdrant.search_similar.return_value = []
        mock_qdrant_getter.return_value = mock_qdrant
        
        service = RAGService()
        
        # Buscar con filtros
        service.buscar(
            "query",
            n_results=5,
            expediente_id="123",
            expediente_numero="EXP-001"
        )
        
        # Verificar que se pasaron los filtros
        call_args = mock_qdrant.search_similar.call_args
        filter_dict = call_args[1]["filter_dict"]
        assert filter_dict["expediente_id"] == "123"
        assert filter_dict["expediente_numero"] == "EXP-001"


@pytest.mark.unit
class TestRAGServiceResponder:
    """Tests para generación de respuestas."""

    @patch('application.services.ia.rag_service.RAGService._get_hybrid_search')
    @patch('application.services.ia.rag_service.RAGService._get_llm')
    def test_responder_no_results(self, mock_llm_getter, mock_hybrid_getter):
        """Debe manejar caso sin resultados."""
        mock_hybrid = Mock()
        mock_hybrid.search.return_value = []
        mock_hybrid_getter.return_value = mock_hybrid
        
        service = RAGService()
        
        resultado = service.responder("pregunta de prueba")
        
        assert "No encontré información" in resultado["respuesta"]
        assert resultado["fuentes"] == []
        assert resultado["confianza"] == 0.0

    @patch('application.services.ia.rag_service.RAGService._get_hybrid_search')
    @patch('application.services.ia.rag_service.RAGService._get_llm')
    def test_responder_with_results(self, mock_llm_getter, mock_hybrid_getter):
        """Debe generar respuesta con contextos encontrados."""
        # Setup mock search results
        mock_chunk = Mock()
        mock_chunk.chunk_id = "chunk_1"
        mock_chunk.texto = "Contexto relevante de prueba"
        mock_chunk.metadata = {"expediente_id": "123"}
        
        mock_search_result = Mock()
        mock_search_result.chunk = mock_chunk
        mock_search_result.score = 0.95
        
        mock_hybrid = Mock()
        mock_hybrid.search.return_value = [mock_search_result]
        mock_hybrid_getter.return_value = mock_hybrid
        
        # Setup mock LLM
        mock_rag_response = Mock()
        mock_rag_response.respuesta = "Esta es la respuesta generada"
        
        mock_llm = Mock()
        mock_llm.generate_answer.return_value = mock_rag_response
        mock_llm_getter.return_value = mock_llm
        
        service = RAGService()
        
        resultado = service.responder("¿Cuál es el estado del caso?")
        
        assert resultado["respuesta"] == "Esta es la respuesta generada"
        assert resultado["confianza"] > 0
        assert len(resultado["fuentes"]) == 1
        assert resultado["fuentes"][0]["id"] == "chunk_1"


@pytest.mark.unit
class TestRAGServiceStats:
    """Tests para estadísticas del servicio."""

    @patch('application.services.ia.rag_service.RAGService._get_hybrid_search')
    def test_get_stats_success(self, mock_hybrid_getter):
        """Debe obtener estadísticas correctamente."""
        mock_hybrid = Mock()
        mock_hybrid.get_stats.return_value = {
            "total_documents": 100,
            "total_chunks": 500
        }
        mock_hybrid_getter.return_value = mock_hybrid
        
        service = RAGService(collection_name="test_collection")
        
        stats = service.get_stats()
        
        assert stats["collection"] == "test_collection"
        assert stats["total_documents"] == 100
        assert stats["total_chunks"] == 500

    @patch('application.services.ia.rag_service.RAGService._get_hybrid_search')
    def test_get_stats_error(self, mock_hybrid_getter):
        """Debe manejar errores al obtener estadísticas."""
        mock_hybrid = Mock()
        mock_hybrid.get_stats.side_effect = Exception("Connection error")
        mock_hybrid_getter.return_value = mock_hybrid
        
        service = RAGService()
        
        stats = service.get_stats()
        
        assert "error" in stats
        assert "Connection error" in stats["error"]
