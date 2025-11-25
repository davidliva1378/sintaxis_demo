"""
Script de prueba para EmbeddingService

Verifica:
1. Carga del modelo
2. Generación de embeddings individuales
3. Generación de embeddings en batch
4. Cache
5. Similitud coseno
"""

import sys
import logging
from pathlib import Path

# Agregar path para imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from infrastructure.rag.services.embedding_service import EmbeddingService

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_embedding_service():
    """Probar EmbeddingService"""

    logger.info("=" * 60)
    logger.info("Iniciando pruebas de EmbeddingService")
    logger.info("=" * 60)

    try:
        # 1. Crear servicio
        logger.info("\n1. Creando EmbeddingService...")
        embedding_service = EmbeddingService()

        # 2. Cargar modelo
        logger.info("\n2. Cargando modelo sentence-transformers...")
        embedding_service.load_model()

        # Obtener dimensión
        dimension = embedding_service.get_dimension()
        logger.info(f"✅ Modelo cargado con dimensión: {dimension}")

        # 3. Generar embedding individual
        logger.info("\n3. Generando embedding para texto individual...")
        texto1 = "El demandado deberá comparecer en el plazo de 10 días hábiles."
        embedding1 = embedding_service.encode_text(texto1)
        logger.info(f"✅ Embedding generado: {len(embedding1)} dimensiones")
        logger.info(f"   Primeros 5 valores: {embedding1[:5]}")

        # 4. Probar cache
        logger.info("\n4. Probando cache...")
        logger.info("   Generando mismo texto nuevamente (debería usar cache)...")
        embedding1_cache = embedding_service.encode_text(texto1)

        # Verificar que son iguales
        if embedding1 == embedding1_cache:
            logger.info("✅ Cache funciona correctamente (embeddings idénticos)")
        else:
            logger.error("❌ Cache falló (embeddings diferentes)")
            return False

        # Stats del cache
        stats = embedding_service.get_cache_stats()
        logger.info(f"   Cache stats: {stats}")

        # 5. Generar embeddings en batch
        logger.info("\n5. Generando embeddings en batch...")
        textos = [
            "El actor solicita la medida cautelar de no innovar.",
            "La sentencia definitiva fue apelada por ambas partes.",
            "Se decreta el embargo preventivo por la suma reclamada.",
            "El expediente queda en estado de Vista al Fiscal.",
            "Se notifica al demandado por cédula en su domicilio real.",
        ]

        embeddings_batch = embedding_service.encode_batch(
            textos,
            show_progress=True
        )

        logger.info(f"✅ Batch generado: {len(embeddings_batch)} embeddings")
        for i, emb in enumerate(embeddings_batch):
            logger.info(f"   Texto {i+1}: {len(emb)} dimensiones")

        # 6. Calcular similitud
        logger.info("\n6. Calculando similitudes...")

        # Similitud entre textos similares (1 y 3 hablan de medidas cautelares)
        sim_similar = embedding_service.compute_similarity(
            embeddings_batch[0],  # medida cautelar
            embeddings_batch[2],  # embargo preventivo
        )
        logger.info(f"   Similitud textos similares (cautelares): {sim_similar:.4f}")

        # Similitud entre textos diferentes
        sim_different = embedding_service.compute_similarity(
            embeddings_batch[0],  # medida cautelar
            embeddings_batch[4],  # notificación
        )
        logger.info(f"   Similitud textos diferentes: {sim_different:.4f}")

        if sim_similar > sim_different:
            logger.info("✅ Similitudes coherentes (similar > diferente)")
        else:
            logger.warning("⚠️  Similitudes inesperadas")

        # 7. Test con texto legal más largo
        logger.info("\n7. Probando con texto legal más largo...")
        texto_largo = """
        VISTOS: Los presentes autos caratulados "PEREZ JUAN CARLOS C/ GOMEZ MARIA LAURA
        S/ DAÑOS Y PERJUICIOS", de los que resulta que el actor reclama la suma de
        pesos quinientos mil ($500.000) en concepto de daños materiales y morales
        derivados del accidente de tránsito ocurrido el día 15 de marzo de 2023.

        CONSIDERANDO: Que de la prueba producida surge acreditada la responsabilidad
        del demandado en el hecho dañoso. Que corresponde hacer lugar parcialmente
        a la demanda en virtud de las constancias de autos.

        RESUELVE: 1) Hacer lugar parcialmente a la demanda. 2) Condenar al demandado
        a abonar la suma de pesos trescientos mil ($300.000) en concepto de daños y
        perjuicios. 3) Imponer las costas al demandado vencido.
        """

        embedding_largo = embedding_service.encode_text(texto_largo.strip())
        logger.info(f"✅ Texto largo vectorizado: {len(embedding_largo)} dimensiones")

        # 8. Verificar cache stats finales
        logger.info("\n8. Estadísticas finales del cache...")
        final_stats = embedding_service.get_cache_stats()
        logger.info(f"   Total entradas: {final_stats['total_entries']}")
        logger.info(f"   Tamaño en bytes: {final_stats['cache_size_bytes']}")

        logger.info("\n" + "=" * 60)
        logger.info("✅ TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"\n❌ Error en las pruebas: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_embedding_service()
    sys.exit(0 if success else 1)
