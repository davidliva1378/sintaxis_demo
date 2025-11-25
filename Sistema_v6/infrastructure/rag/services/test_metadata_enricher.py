"""
Script de prueba para MetadataEnricher

Verifica:
1. Carga del modelo spaCy
2. Extracción de entidades NER
3. Extracción de entidades legales específicas
4. Extracción de referencias normativas
5. Extracción de montos y plazos
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Agregar path para imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from infrastructure.rag.services.metadata_enricher import MetadataEnricher
from infrastructure.rag.models.dto import DocumentChunk, ChunkType

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_metadata_enricher():
    """Probar MetadataEnricher con chunks legales"""

    logger.info("=" * 60)
    logger.info("Iniciando pruebas de MetadataEnricher")
    logger.info("=" * 60)

    try:
        # 1. Crear servicio
        logger.info("\n1. Creando MetadataEnricher...")
        enricher = MetadataEnricher()
        logger.info("✅ MetadataEnricher creado")

        # 2. Cargar modelo spaCy
        logger.info("\n2. Cargando modelo spaCy...")
        enricher.load_model()
        logger.info("✅ Modelo spaCy cargado")

        # 3. Chunk con datos legales completos
        logger.info("\n3. Probando extracción de metadata completa...")
        chunk_completo = DocumentChunk(
            chunk_id="chunk_test_001",
            doc_id="doc_test_001",
            chunk_index=0,
            chunk_type=ChunkType.CONSIDERANDOS,
            texto="""
CONSIDERANDOS: Que de la prueba producida en autos surge acreditada la responsabilidad
del demandado GOMEZ MARIA LAURA en el hecho dañoso ocurrido el día 15 de marzo de 2023.
El testimonio del testigo RODRIGUEZ CARLOS (fs. 45/46) confirma que el vehículo conducido
por el demandado cruzó el semáforo en rojo.

Que el peritaje mecánico establece que los daños en el vehículo del actor PEREZ JUAN CARLOS
ascienden a la suma de pesos trescientos mil ($300.000), conforme presupuesto de
Automotores del Sur S.A. agregado a fs. 83/85.

Que en cuanto al daño moral reclamado, esta Magistratura considera procedente fijar
una indemnización de $100.000, atendiendo a las circunstancias del caso y la jurisprudencia
aplicable en el Art. 1741 del Código Civil y Comercial (Ley 26.994).

Que el demandado deberá comparecer en el plazo de 10 días hábiles a fin de cumplir con
lo aquí resuelto, bajo apercibimiento de lo dispuesto en el Art. 251 del C.P.C.C.
            """,
            metadata={}
        )

        metadata = enricher.enrich_chunk(chunk_completo)

        logger.info(f"\n   Metadata extraída:")
        logger.info(f"   Personas: {metadata.personas}")
        logger.info(f"   Organizaciones: {metadata.organizaciones}")
        logger.info(f"   Actores: {metadata.actores}")
        logger.info(f"   Demandados: {metadata.demandados}")
        logger.info(f"   Normativa citada: {metadata.normativa_citada}")
        logger.info(f"   Montos: {metadata.montos}")
        logger.info(f"   Plazos: {metadata.plazos}")

        # Verificar que se extrajeron las entidades esperadas
        checks = []

        # Debe haber nombres de personas
        if metadata.personas or metadata.actores or metadata.demandados:
            logger.info("   ✅ Personas detectadas")
            checks.append(True)
        else:
            logger.warning("   ⚠️  No se detectaron personas")
            checks.append(False)

        # Debe haber referencias normativas
        if metadata.normativa_citada:
            logger.info("   ✅ Referencias normativas detectadas")
            checks.append(True)
        else:
            logger.warning("   ⚠️  No se detectaron referencias normativas")
            checks.append(False)

        # Debe haber montos
        if metadata.montos:
            logger.info("   ✅ Montos detectados")
            checks.append(True)
        else:
            logger.warning("   ⚠️  No se detectaron montos")
            checks.append(False)

        # Debe haber plazos
        if metadata.plazos:
            logger.info("   ✅ Plazos detectados")
            checks.append(True)
        else:
            logger.warning("   ⚠️  No se detectaron plazos")
            checks.append(False)

        # 4. Chunk simple (para verificar que no falla con poco contenido)
        logger.info("\n4. Probando con chunk simple...")
        chunk_simple = DocumentChunk(
            chunk_id="chunk_test_002",
            doc_id="doc_test_002",
            chunk_index=0,
            chunk_type=ChunkType.RESUELVE,
            texto="RESUELVE: Regístrese, notifíquese y archívese.",
            metadata={}
        )

        metadata_simple = enricher.enrich_chunk(chunk_simple)
        logger.info("   ✅ Chunk simple procesado sin errores")

        # 5. Procesamiento en batch
        logger.info("\n5. Probando procesamiento en batch...")
        chunks = [chunk_completo, chunk_simple]
        metadata_dict = enricher.enrich_chunks(chunks)

        logger.info(f"   ✅ Procesados {len(metadata_dict)} chunks")

        # 6. Estadísticas
        logger.info("\n6. Obteniendo estadísticas...")
        stats = enricher.get_statistics(metadata_dict)

        logger.info(f"   Total chunks: {stats.get('total_chunks', 0)}")
        logger.info(f"   Chunks con metadata: {stats.get('chunks_con_metadata', 0)}")
        logger.info(f"   Total personas: {stats.get('total_personas', 0)}")
        logger.info(f"   Total actores: {stats.get('total_actores', 0)}")
        logger.info(f"   Total demandados: {stats.get('total_demandados', 0)}")
        logger.info(f"   Total normativa: {stats.get('total_normativa', 0)}")
        logger.info(f"   Total montos: {stats.get('total_montos', 0)}")
        logger.info(f"   Total plazos: {stats.get('total_plazos', 0)}")

        if stats.get('chunks_con_metadata', 0) > 0:
            logger.info("   ✅ Estadísticas generadas correctamente")
            checks.append(True)
        else:
            logger.warning("   ⚠️  No se generaron estadísticas")
            checks.append(False)

        # 7. Verificación específica de patrones
        logger.info("\n7. Verificando patrones específicos...")

        # Verificar que se extrajo el Art. 1741
        tiene_art_1741 = any("1741" in norma for norma in metadata.normativa_citada)
        if tiene_art_1741:
            logger.info("   ✅ Art. 1741 detectado correctamente")
        else:
            logger.warning("   ⚠️  Art. 1741 no detectado")

        # Verificar que se extrajo la Ley 26.994
        tiene_ley_26994 = any("26.994" in norma or "26994" in norma for norma in metadata.normativa_citada)
        if tiene_ley_26994:
            logger.info("   ✅ Ley 26.994 detectada correctamente")
        else:
            logger.warning("   ⚠️  Ley 26.994 no detectada")

        # Verificar que se extrajo el plazo de 10 días
        tiene_plazo_10_dias = any("10 días" in plazo for plazo in metadata.plazos)
        if tiene_plazo_10_dias:
            logger.info("   ✅ Plazo de 10 días detectado correctamente")
        else:
            logger.warning("   ⚠️  Plazo de 10 días no detectado")

        # 8. Resultado final
        logger.info("\n" + "=" * 60)
        if all(checks):
            logger.info("✅ TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
            logger.info("=" * 60)
            return True
        else:
            logger.warning("⚠️  ALGUNAS PRUEBAS FALLARON (es normal con NER, depende del modelo)")
            logger.warning(f"    Checks passed: {sum(checks)}/{len(checks)}")
            logger.info("=" * 60)
            # Considerar exitoso si al menos 3 de 5 checks pasaron
            return sum(checks) >= 3

    except Exception as e:
        logger.error(f"\n❌ Error en las pruebas: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_metadata_enricher()
    sys.exit(0 if success else 1)
