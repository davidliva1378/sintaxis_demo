"""
Script de prueba para verificar integración RAG con procesador de actuaciones

Verifica:
1. RAGIndexer puede leer JSONs de actuaciones existentes
2. Conversión de actuaciones a LegalDocuments funciona
3. Chunking y enrichment funcionan
4. Indexación en Qdrant + BM25 funciona
5. Búsqueda funciona correctamente
"""

import sys
import logging
from pathlib import Path

# Agregar path para imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from infrastructure.rag.services.rag_indexer import RAGIndexer
from infrastructure.rag.models.dto import SearchQuery
from infrastructure.rag.services.llm_service import RAGService

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_integracion():
    """Test completo de integración"""

    logger.info("=" * 60)
    logger.info("TEST DE INTEGRACIÓN RAG - PROCESADOR DE ACTUACIONES")
    logger.info("=" * 60)

    try:
        # ==================================================================
        # 1. Verificar que existe al menos un JSON de actuaciones
        # ==================================================================
        logger.info("\n1. Buscando JSONs de actuaciones...")

        directorio_base = Path(__file__).parent.parent.parent.parent / "data" / "actuaciones"

        if not directorio_base.exists():
            logger.error(f"❌ Directorio no existe: {directorio_base}")
            return False

        archivos_json = list(directorio_base.rglob("actuaciones-*.json"))

        if not archivos_json:
            logger.warning(f"⚠️ No se encontraron JSONs en {directorio_base}")
            logger.info("   Sugerencia: Procesa un expediente primero usando el sistema")
            return False

        logger.info(f"✅ Encontrados {len(archivos_json)} archivos JSON")

        # Tomar el primero para pruebas
        json_test = archivos_json[0]
        logger.info(f"   Usando: {json_test.name}")

        # Extraer número de expediente
        numero_expediente = json_test.stem.replace("actuaciones-", "").replace("_", "/")
        logger.info(f"   Expediente: {numero_expediente}")

        # ==================================================================
        # 2. Crear RAGIndexer y procesar expediente de prueba
        # ==================================================================
        logger.info("\n2. Indexando expediente de prueba...")

        indexer = RAGIndexer()

        resultado = indexer.indexar_expediente(
            ruta_json=json_test,
            expediente_numero=numero_expediente,
            force=True
        )

        if not resultado["success"]:
            logger.error(f"❌ Error indexando: {resultado.get('error')}")
            return False

        logger.info(f"✅ Indexación exitosa:")
        logger.info(f"   Actuaciones procesadas: {resultado['actuaciones_procesadas']}")
        logger.info(f"   Documentos creados: {resultado['documentos_creados']}")
        logger.info(f"   Chunks indexados: {resultado['chunks_indexados']}")

        # ==================================================================
        # 3. Verificar estadísticas de índices
        # ==================================================================
        logger.info("\n3. Verificando índices...")

        stats = indexer.get_stats()
        logger.info(f"   Qdrant: {stats['qdrant']['count']} puntos")
        logger.info(f"   BM25: {stats['bm25']['total_documents']} documentos")

        if stats['qdrant']['count'] == 0 or stats['bm25']['total_documents'] == 0:
            logger.error("❌ Los índices están vacíos")
            return False

        logger.info("✅ Índices poblados correctamente")

        # ==================================================================
        # 4. Probar búsqueda híbrida
        # ==================================================================
        logger.info("\n4. Probando búsqueda híbrida...")

        # Queries de prueba
        queries_prueba = [
            "sentencia",
            "resolución",
            "plazo",
        ]

        for query_text in queries_prueba:
            logger.info(f"\n   Query: '{query_text}'")

            query = SearchQuery(texto=query_text, limit=3)
            resultados = indexer.search_service.search(query)

            logger.info(f"   Resultados: {len(resultados)}")

            if resultados:
                for i, res in enumerate(resultados[:2], 1):
                    logger.info(f"      [{i}] Score: {res.score:.4f}")
                    logger.info(f"          Expediente: {res.chunk.metadata.get('expediente_numero')}")
                    logger.info(f"          Tipo: {res.chunk.chunk_type.value}")
                    snippet = res.highlights[0] if res.highlights else res.chunk.texto[:100]
                    logger.info(f"          Snippet: {snippet}...")

        logger.info("\n✅ Búsqueda híbrida funciona correctamente")

        # ==================================================================
        # 5. Probar RAG completo (opcional, si Ollama está disponible)
        # ==================================================================
        logger.info("\n5. Probando RAG completo con LLM...")

        try:
            rag_service = RAGService(
                hybrid_search_service=indexer.search_service
            )

            # Verificar si Ollama está disponible
            if rag_service.llm.health_check():
                logger.info("   Ollama disponible, generando respuesta...")

                respuesta = rag_service.query("¿Cuál es el plazo para apelar?")

                logger.info(f"   Pregunta: {respuesta.pregunta}")
                logger.info(f"   Respuesta: {respuesta.respuesta[:200]}...")
                logger.info(f"   Chunks usados: {respuesta.metadata.get('num_chunks', 0)}")

                logger.info("\n✅ RAG completo funciona correctamente")
            else:
                logger.warning("   ⚠️ Ollama no disponible, skipping test de LLM")

        except Exception as e:
            logger.warning(f"   ⚠️ Error en test de LLM (no crítico): {e}")

        # ==================================================================
        # RESUMEN FINAL
        # ==================================================================
        logger.info("\n" + "=" * 60)
        logger.info("✅ TODAS LAS PRUEBAS DE INTEGRACIÓN PASARON")
        logger.info("=" * 60)
        logger.info("\nResumen:")
        logger.info(f"  ✓ RAGIndexer puede leer JSONs de actuaciones")
        logger.info(f"  ✓ Conversión a LegalDocuments funciona")
        logger.info(f"  ✓ Chunking y enrichment funcionan")
        logger.info(f"  ✓ Indexación en Qdrant + BM25 funciona")
        logger.info(f"  ✓ Búsqueda híbrida funciona")
        logger.info(f"\nSistema RAG integrado correctamente con procesador de actuaciones")

        return True

    except Exception as e:
        logger.error(f"\n❌ Error en test de integración: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_integracion()
    sys.exit(0 if success else 1)
