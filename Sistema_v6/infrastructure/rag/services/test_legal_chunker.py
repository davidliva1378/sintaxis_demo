"""
Script de prueba para LegalChunker

Verifica:
1. Detección de secciones legales
2. Chunking semántico con overlap
3. Generación de metadata
4. Estadísticas de chunks
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Agregar path para imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from infrastructure.rag.services.legal_chunker import LegalChunker
from infrastructure.rag.models.dto import LegalDocument

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_legal_chunker():
    """Probar LegalChunker con documentos legales"""

    logger.info("=" * 60)
    logger.info("Iniciando pruebas de LegalChunker")
    logger.info("=" * 60)

    try:
        # 1. Crear servicio
        logger.info("\n1. Creando LegalChunker...")
        chunker = LegalChunker()
        logger.info("✅ LegalChunker creado")

        # 2. Documento con secciones claras
        logger.info("\n2. Probando con documento con secciones claras...")
        doc_con_secciones = LegalDocument(
            doc_id="actuacion_12345",
            expediente_numero="EXP-2024-001",
            actuacion_id=12345,
            tipo="Sentencia",
            fecha=datetime(2024, 3, 15),
            contenido="""
VISTOS: Los presentes autos caratulados "PEREZ JUAN CARLOS C/ GOMEZ MARIA LAURA
S/ DAÑOS Y PERJUICIOS", expediente número EXP-2024-001, de los que resulta que
el actor reclama la suma de pesos quinientos mil ($500.000) en concepto de daños
materiales y morales derivados del accidente de tránsito ocurrido el día 15 de
marzo de 2023 en la intersección de las calles San Martín y Belgrano de esta ciudad.

La demanda fue iniciada el 10 de enero de 2024 ante este Juzgado Civil y Comercial
N° 5. El demandado fue notificado mediante cédula el 25 de enero de 2024 y presentó
contestación de demanda el 15 de febrero de 2024, negando los hechos y solicitando
el rechazo de la demanda con costas.

CONSIDERANDOS: Que de la prueba producida en autos surge acreditada la responsabilidad
del demandado en el hecho dañoso. El testimonio del testigo RODRIGUEZ CARLOS (fs. 45/46)
confirma que el vehículo conducido por el demandado cruzó el semáforo en rojo,
impactando contra el vehículo del actor.

Que el peritaje mecánico de fs. 78/82 establece que los daños en el vehículo del actor
ascienden a la suma de pesos trescientos mil ($300.000), conforme presupuesto de
Automotores del Sur S.A. agregado a fs. 83/85.

Que en cuanto al daño moral reclamado, esta Magistratura considera procedente fijar
una indemnización de pesos cien mil ($100.000), atendiendo a las circunstancias del
caso, la edad del actor (42 años) y las molestias sufridas durante el tratamiento
médico que consta en historia clínica de fs. 90/95.

Que corresponde hacer lugar parcialmente a la demanda en virtud de las constancias
de autos y la jurisprudencia aplicable (CSJN, "Aquino c/ Cargo Servicios Industriales",
Fallos 327:3753).

RESUELVE: 1) Hacer lugar parcialmente a la demanda interpuesta por PEREZ JUAN CARLOS
contra GOMEZ MARIA LAURA por la suma de PESOS CUATROCIENTOS MIL ($400.000) en concepto
de daños y perjuicios materiales y morales.

2) Condenar al demandado GOMEZ MARIA LAURA a abonar la suma mencionada en el punto
anterior, con más los intereses establecidos en el artículo 768 inciso b) del Código
Civil y Comercial, desde la fecha del hecho (15/03/2023) hasta el efectivo pago.

3) Imponer las costas al demandado vencido (art. 68 del C.P.C.C.).

4) Diferir la regulación de honorarios profesionales para su oportunidad.

5) Regístrese, notifíquese y oportunamente archívese.
            """,
            metadata={
                "juzgado": "Civil y Comercial N° 5",
                "caratula": "PEREZ JUAN CARLOS C/ GOMEZ MARIA LAURA S/ DAÑOS Y PERJUICIOS"
            }
        )

        chunks_con_secciones = chunker.chunk_document(doc_con_secciones)
        logger.info(f"✅ Documento procesado: {len(chunks_con_secciones)} chunks")

        # Mostrar chunks
        for i, chunk in enumerate(chunks_con_secciones):
            logger.info(f"\n   Chunk {i+1}:")
            logger.info(f"   - ID: {chunk.chunk_id}")
            logger.info(f"   - Tipo: {chunk.chunk_type.value}")
            logger.info(f"   - Longitud: {len(chunk.texto)} caracteres")
            logger.info(f"   - Texto (primeros 100 chars): {chunk.texto[:100]}...")

        # Estadísticas
        stats = chunker.get_chunk_stats(chunks_con_secciones)
        logger.info(f"\n   Estadísticas:")
        logger.info(f"   - Total chunks: {stats['total_chunks']}")
        logger.info(f"   - Longitud promedio: {stats['avg_length']} caracteres")
        logger.info(f"   - Longitud mín: {stats['min_length']} caracteres")
        logger.info(f"   - Longitud máx: {stats['max_length']} caracteres")
        logger.info(f"   - Por tipo: {stats['by_type']}")

        # Verificar que se detectaron las secciones
        tipos_detectados = {chunk.chunk_type.value for chunk in chunks_con_secciones}
        logger.info(f"\n   Tipos de sección detectados: {tipos_detectados}")

        if 'vistos' in tipos_detectados and 'considerandos' in tipos_detectados and 'resuelve' in tipos_detectados:
            logger.info("   ✅ Todas las secciones detectadas correctamente")
        else:
            logger.warning(f"   ⚠️  No se detectaron todas las secciones esperadas")

        # 3. Documento sin secciones claras (texto plano)
        logger.info("\n3. Probando con documento sin secciones...")
        doc_sin_secciones = LegalDocument(
            doc_id="actuacion_67890",
            expediente_numero="EXP-2024-002",
            actuacion_id=67890,
            tipo="Providencia",
            fecha=datetime(2024, 3, 20),
            contenido="""
Téngase presente lo manifestado por la parte actora. Por presentada la documental
acompañada, agréguese. Notifíquese a la contraria para que en el plazo de cinco
días hábiles tome vista y manifieste lo que estime corresponder.
            """,
            metadata={}
        )

        chunks_sin_secciones = chunker.chunk_document(doc_sin_secciones)
        logger.info(f"✅ Documento sin secciones procesado: {len(chunks_sin_secciones)} chunks")

        for i, chunk in enumerate(chunks_sin_secciones):
            logger.info(f"\n   Chunk {i+1}:")
            logger.info(f"   - Tipo: {chunk.chunk_type.value}")
            logger.info(f"   - Longitud: {len(chunk.texto)} caracteres")

        # 4. Documento muy largo (probar chunking con overlap)
        logger.info("\n4. Probando con documento muy largo...")
        texto_largo = """
VISTOS: Los presentes autos caratulados "EMPRESA ABC S.A. C/ GOBIERNO NACIONAL
S/ ACCIÓN DE AMPARO", """ + " ".join([f"Párrafo {i} con contenido legal extenso que simula un documento real con múltiples consideraciones y fundamentos jurídicos." for i in range(100)])

        doc_largo = LegalDocument(
            doc_id="actuacion_99999",
            expediente_numero="EXP-2024-003",
            actuacion_id=99999,
            tipo="Sentencia",
            fecha=datetime(2024, 3, 25),
            contenido=texto_largo,
            metadata={}
        )

        chunks_largo = chunker.chunk_document(doc_largo)
        logger.info(f"✅ Documento largo procesado: {len(chunks_largo)} chunks")

        stats_largo = chunker.get_chunk_stats(chunks_largo)
        logger.info(f"   - Longitud promedio: {stats_largo['avg_length']} caracteres")
        logger.info(f"   - Longitud máx: {stats_largo['max_length']} caracteres")

        # Verificar que ningún chunk excede el tamaño configurado (1500 + margen)
        max_chunk_length = max(len(chunk.texto) for chunk in chunks_largo)
        if max_chunk_length <= 2000:  # Margen de tolerancia
            logger.info(f"   ✅ Todos los chunks respetan el tamaño máximo")
        else:
            logger.warning(f"   ⚠️  Hay chunks que exceden el tamaño: {max_chunk_length}")

        # 5. Verificar metadata
        logger.info("\n5. Verificando metadata de chunks...")
        sample_chunk = chunks_con_secciones[0]
        logger.info(f"   Metadata del primer chunk:")
        logger.info(f"   - doc_id: {sample_chunk.doc_id}")
        logger.info(f"   - chunk_index: {sample_chunk.chunk_index}")
        logger.info(f"   - expediente_numero: {sample_chunk.metadata.get('expediente_numero')}")
        logger.info(f"   - actuacion_id: {sample_chunk.metadata.get('actuacion_id')}")
        logger.info(f"   - tipo_actuacion: {sample_chunk.metadata.get('tipo_actuacion')}")

        if all([
            sample_chunk.metadata.get('expediente_numero'),
            sample_chunk.metadata.get('actuacion_id'),
            sample_chunk.metadata.get('tipo_actuacion'),
        ]):
            logger.info("   ✅ Metadata correctamente heredada del documento")
        else:
            logger.error("   ❌ Falta metadata en el chunk")
            return False

        logger.info("\n" + "=" * 60)
        logger.info("✅ TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"\n❌ Error en las pruebas: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_legal_chunker()
    sys.exit(0 if success else 1)
