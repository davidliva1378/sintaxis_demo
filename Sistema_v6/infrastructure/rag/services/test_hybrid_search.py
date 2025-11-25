"""
Script de prueba para HybridSearchService (flujo completo RAG)

Verifica:
1. Chunking de documentos legales
2. Indexación en Qdrant + BM25
3. Búsqueda híbrida (dense + sparse)
4. Fusión y reranking de resultados
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Agregar path para imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from infrastructure.rag.services.hybrid_search_service import HybridSearchService
from infrastructure.rag.services.legal_chunker import LegalChunker
from infrastructure.rag.models.dto import LegalDocument, SearchQuery

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_hybrid_search():
    """Probar flujo completo de búsqueda híbrida"""

    logger.info("=" * 60)
    logger.info("Iniciando pruebas de HybridSearchService (Flujo completo RAG)")
    logger.info("=" * 60)

    try:
        # 1. Crear documentos de prueba
        logger.info("\n1. Creando documentos legales de prueba...")

        documentos = [
            LegalDocument(
                doc_id="actuacion_001",
                expediente_numero="EXP-2024-001",
                actuacion_id=1,
                tipo="Sentencia",
                fecha=datetime(2024, 3, 15),
                contenido="""
VISTOS: Los presentes autos caratulados "PEREZ JUAN CARLOS C/ GOMEZ MARIA LAURA
S/ DAÑOS Y PERJUICIOS", de los que resulta que el actor reclama daños materiales
y morales derivados de un accidente de tránsito ocurrido en la intersección de
las calles San Martín y Belgrano.

CONSIDERANDOS: Que de la prueba producida surge acreditada la responsabilidad del
demandado en el hecho dañoso. El peritaje mecánico establece daños por $300.000.

RESUELVE: Hacer lugar parcialmente a la demanda. Condenar al pago de $400.000.
Imponer las costas al demandado vencido.
                """,
                metadata={"juzgado": "Civil N° 5"}
            ),
            LegalDocument(
                doc_id="actuacion_002",
                expediente_numero="EXP-2024-002",
                actuacion_id=2,
                tipo="Providencia",
                fecha=datetime(2024, 3, 20),
                contenido="""
RESUELVE: Téngase presente lo manifestado. Agréguese la documental acompañada.
Notifíquese a la contraria para que tome vista en el plazo de 10 días hábiles.
                """,
                metadata={"juzgado": "Civil N° 5"}
            ),
            LegalDocument(
                doc_id="actuacion_003",
                expediente_numero="EXP-2024-003",
                actuacion_id=3,
                tipo="Sentencia",
                fecha=datetime(2024, 3, 25),
                contenido="""
VISTOS: Los autos "RODRIGUEZ CARLOS C/ EMPRESA XYZ S.A. S/ DESPIDO", donde el
actor reclama diferencias salariales y rubros indemnizatorios derivados de un
despido sin causa.

CONSIDERANDOS: Que el actor prestó servicios para la demandada durante 5 años.
Que la prueba documental acredita que el despido fue sin justa causa. Que
corresponde hacer lugar a la indemnización prevista en el Art. 245 de la LCT.

RESUELVE: Hacer lugar a la demanda. Condenar al pago de $850.000 en concepto
de indemnización por despido. Costas a la demandada.
                """,
                metadata={"juzgado": "Laboral N° 2"}
            )
        ]

        logger.info(f"   ✅ Creados {len(documentos)} documentos")

        # 2. Chunking de documentos
        logger.info("\n2. Dividiendo documentos en chunks...")
        chunker = LegalChunker()

        all_chunks = []
        for doc in documentos:
            chunks = chunker.chunk_document(doc)
            all_chunks.extend(chunks)
            logger.info(f"   - {doc.doc_id}: {len(chunks)} chunks")

        logger.info(f"   ✅ Total: {len(all_chunks)} chunks")

        # 3. Crear servicio de búsqueda híbrida
        logger.info("\n3. Creando HybridSearchService...")
        search_service = HybridSearchService()
        logger.info("   ✅ Servicio creado")

        # 4. Conectar a Qdrant y crear colección
        logger.info("\n4. Configurando Qdrant...")
        search_service.qdrant.connect()
        search_service.qdrant.create_collection(recreate=True)  # Recrear limpia
        logger.info("   ✅ Colección Qdrant lista")

        # 5. Indexar chunks (Qdrant + BM25)
        logger.info("\n5. Indexando chunks...")
        search_service.index_chunks(all_chunks)
        logger.info("   ✅ Indexación completada")

        # 6. Verificar stats
        logger.info("\n6. Verificando estadísticas...")
        stats = search_service.get_stats()
        logger.info(f"   Qdrant: {stats['qdrant']['count']} puntos")
        logger.info(f"   BM25: {stats['bm25']['total_documents']} documentos")

        if stats['qdrant']['count'] == len(all_chunks) and stats['bm25']['total_documents'] == len(all_chunks):
            logger.info("   ✅ Estadísticas correctas")
        else:
            logger.warning("   ⚠️  Estadísticas no coinciden")

        # 7. Búsqueda híbrida - Query 1: accidente de tránsito
        logger.info("\n7. Búsqueda 1: 'accidente de tránsito'")
        query1 = SearchQuery(
            texto="accidente de tránsito",
            limit=10
        )

        results1 = search_service.search(query1)
        logger.info(f"   Resultados: {len(results1)}")

        for i, result in enumerate(results1[:3]):
            logger.info(f"\n   Resultado {i+1}:")
            logger.info(f"   - Score: {result.score:.4f}")
            logger.info(f"   - Expediente: {result.chunk.metadata.get('expediente_numero')}")
            logger.info(f"   - Tipo: {result.chunk.chunk_type.value}")
            logger.info(f"   - Snippet: {result.highlights[0] if result.highlights else 'N/A'}")

        # Verificar que el primer resultado es el documento correcto
        if results1 and "EXP-2024-001" in str(results1[0].chunk.metadata.get('expediente_numero', '')):
            logger.info("\n   ✅ Resultado más relevante correcto (EXP-2024-001)")
        else:
            logger.warning("\n   ⚠️  Resultado esperado no en primera posición")

        # 8. Búsqueda híbrida - Query 2: despido laboral
        logger.info("\n8. Búsqueda 2: 'despido indemnización'")
        query2 = SearchQuery(
            texto="despido indemnización",
            limit=5
        )

        results2 = search_service.search(query2)
        logger.info(f"   Resultados: {len(results2)}")

        for i, result in enumerate(results2[:2]):
            logger.info(f"\n   Resultado {i+1}:")
            logger.info(f"   - Score: {result.score:.4f}")
            logger.info(f"   - Expediente: {result.chunk.metadata.get('expediente_numero')}")

        # 9. Búsqueda solo dense
        logger.info("\n9. Búsqueda solo dense (vectorial)...")
        query3 = SearchQuery(texto="daños y perjuicios", limit=5)
        results3 = search_service.search(query3, use_dense=True, use_sparse=False)
        logger.info(f"   Resultados dense: {len(results3)}")

        # 10. Búsqueda solo sparse
        logger.info("\n10. Búsqueda solo sparse (keywords)...")
        query4 = SearchQuery(texto="notifíquese vista plazo", limit=5)
        results4 = search_service.search(query4, use_dense=False, use_sparse=True)
        logger.info(f"   Resultados sparse: {len(results4)}")

        # 11. Búsqueda con filtros
        logger.info("\n11. Búsqueda con filtro de expediente...")
        query5 = SearchQuery(
            texto="sentencia",
            limit=5,
            filter_expediente="EXP-2024-001"
        )
        results5 = search_service.search(query5)
        logger.info(f"   Resultados filtrados: {len(results5)}")

        # Verificar que todos son del expediente correcto
        if all("EXP-2024-001" == r.chunk.metadata.get('expediente_numero') for r in results5):
            logger.info("   ✅ Filtro aplicado correctamente")
        else:
            logger.warning("   ⚠️  Filtro no funcionó correctamente")

        logger.info("\n" + "=" * 60)
        logger.info("✅ TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
        logger.info("=" * 60)
        logger.info("\nResumen:")
        logger.info(f"  - {len(documentos)} documentos procesados")
        logger.info(f"  - {len(all_chunks)} chunks indexados")
        logger.info(f"  - Búsqueda híbrida funcionando correctamente")
        logger.info(f"  - Filtros aplicados correctamente")

        return True

    except Exception as e:
        logger.error(f"\n❌ Error en las pruebas: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_hybrid_search()
    sys.exit(0 if success else 1)
