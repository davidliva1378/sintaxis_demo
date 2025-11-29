import sys
import os
import logging
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.getcwd())

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ner_chunker():
    print("\n=== Testing NER Chunker ===")
    try:
        from application.services.ia.ner_chunker import NERChunker
        
        # Mock NER Service
        mock_ner = MagicMock()
        # Simulate extraction returning a list of dicts
        mock_ner.extract.return_value = [{"text": "Juan Perez", "label": "PERSONA", "start": 10, "end": 20}]
        mock_ner.extract_enhanced.return_value = [{"text": "Juan Perez", "label": "PERSONA", "start": 10, "end": 20}]
        
        chunker = NERChunker(ner_service=mock_ner, chunk_size=50, overlap=10)
        
        long_text = "Este es un texto muy largo para probar el chunking. " * 5
        print(f"Texto largo longitud: {len(long_text)}")
        
        results = chunker.process_long_text(long_text)
        print(f"Entidades encontradas: {len(results)}")
        print("✅ NER Chunker test passed (logic flow)")
    except Exception as e:
        print(f"❌ NER Chunker test failed: {e}")
        import traceback
        traceback.print_exc()

def test_rag_responder():
    print("\n=== Testing RAG Service Responder ===")
    try:
        from application.services.ia.rag_service import RAGService
        
        # Mock dependencies
        mock_hybrid = MagicMock()
        mock_llm = MagicMock()
        
        # Mock search results objects
        mock_chunk = MagicMock()
        mock_chunk.texto = "El demandado Juan Perez debe pagar 1000 pesos."
        mock_chunk.metadata = {"expediente": "123/2024"}
        mock_chunk.chunk_id = "chunk_1"
        
        mock_result = MagicMock()
        mock_result.chunk = mock_chunk
        mock_result.score = 0.9
        
        # Mock hybrid search return
        mock_hybrid.search.return_value = [mock_result]
        
        # Mock LLM response object
        mock_rag_response = MagicMock()
        mock_rag_response.respuesta = "Juan Perez debe pagar."
        mock_llm.generate_answer.return_value = mock_rag_response
        
        rag_service = RAGService(
            hybrid_search_service=mock_hybrid,
            llm_service=mock_llm
        )
        
        response = rag_service.responder("¿Quién debe pagar?")
        
        print(f"Respuesta RAG: {response.get('respuesta')}")
        if response.get('respuesta') == "Juan Perez debe pagar.":
            print("✅ RAG Responder test passed")
        else:
            print("❌ RAG Responder test failed: Unexpected response")
            
    except Exception as e:
        print(f"❌ RAG Responder test failed: {e}")
        import traceback
        traceback.print_exc()

def test_llm_summarize():
    print("\n=== Testing LLM Summarize ===")
    try:
        from infrastructure.rag.services.llm_service import LLMService
        
        llm = LLMService()
        # Mock _call_ollama to avoid real API call if not running/configured
        llm._call_ollama = MagicMock(return_value="Resumen simulado del expediente.")
        
        summary = llm.summarize("Texto largo del expediente...")
        print(f"Resumen: {summary}")
        
        if summary == "Resumen simulado del expediente.":
            print("✅ LLM Summarize test passed")
        else:
            print("❌ LLM Summarize test failed")
            
    except Exception as e:
        print(f"❌ LLM Summarize test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ner_chunker()
    test_llm_summarize()
    test_rag_responder()
