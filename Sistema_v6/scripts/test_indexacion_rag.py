"""
Script de prueba para indexación RAG de actuaciones.
Prueba la Fase 2 del plan de IA.
"""

import os
import sys

# Setup paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(project_root))

import mysql.connector
from datetime import datetime

# Configuración BD
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': os.environ.get('MYSQL_PASSWORD', 'Sulaco01'),
    'database': 'sintaxis'
}


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def test_indexacion_rag():
    """Prueba la indexación RAG completa."""

    print("=" * 60)
    print("Test de Indexación RAG - Fase 2")
    print("=" * 60)

    # === Paso 1: Verificar ChromaDB ===
    print("\n1. Verificando ChromaDB...")
    try:
        from infrastructure.vector_store.chroma_client import ChromaClient

        chroma = ChromaClient(
            persist_directory="./data/vector_store",
            collection_name="actuaciones"
        )

        # Intentar obtener stats
        stats = chroma.get_stats()
        print(f"   ChromaDB OK - Directorio: {stats['persist_directory']}")
        print(f"   Colecciones: {list(stats['collections'].keys())}")

    except ImportError as e:
        print(f"   ERROR: {e}")
        print("   Instalar con: pip install chromadb")
        return
    except Exception as e:
        print(f"   ERROR inicializando ChromaDB: {e}")
        return

    # === Paso 2: Verificar EmbeddingsService ===
    print("\n2. Verificando EmbeddingsService...")
    try:
        from application.services.ia.embeddings_service import EmbeddingsService

        embeddings = EmbeddingsService(device="cpu")

        # Probar encoding
        test_text = "Esta es una prueba de embeddings para el sistema RAG."
        embedding = embeddings.encode(test_text)

        print(f"   EmbeddingsService OK")
        print(f"   Dimensiones embedding: {len(embedding)}")

    except ImportError as e:
        print(f"   ERROR: {e}")
        return
    except Exception as e:
        print(f"   ERROR en EmbeddingsService: {e}")
        return

    # === Paso 3: Probar RAGService indexación ===
    print("\n3. Probando RAGService indexación...")
    try:
        from application.services.ia.rag_service import RAGService

        rag = RAGService(
            embeddings_service=embeddings,
            chroma_client=chroma
        )

        # Obtener actuaciones para indexar
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT id, tipo, detalle, texto_extraido, expediente_numero
            FROM actuaciones
            WHERE tiene_texto_extraido = 1
              AND indexado_rag = 0
              AND LENGTH(texto_extraido) > 100
            LIMIT 5
        """
        cursor.execute(query)
        actuaciones = cursor.fetchall()

        print(f"   Encontradas {len(actuaciones)} actuaciones para indexar")

        if not actuaciones:
            print("   No hay actuaciones pendientes de indexar")
            cursor.close()
            conn.close()
            return

        # Indexar cada actuación
        indexadas = 0
        for act in actuaciones:
            try:
                print(f"\n   Indexando actuación {act['id']}...")

                rag.indexar_actuacion(
                    id_actuacion=str(act['id']),
                    texto=act['texto_extraido'],
                    metadata={
                        "expediente_id": str(act.get('expediente_id', '')),
                        "expediente_numero": act.get('expediente_numero', ''),
                        "tipo": act.get('tipo', ''),
                        "detalle": act.get('detalle', '')[:100]
                    }
                )

                # Marcar como indexada en BD
                cursor.execute(
                    "UPDATE actuaciones SET indexado_rag = 1 WHERE id = %s",
                    (act['id'],)
                )
                conn.commit()

                indexadas += 1
                print(f"   OK - Actuación {act['id']} indexada")

            except Exception as e:
                print(f"   ERROR indexando {act['id']}: {e}")

        cursor.close()
        conn.close()

        print(f"\n   Total indexadas: {indexadas}/{len(actuaciones)}")

    except Exception as e:
        print(f"   ERROR en RAGService: {e}")
        import traceback
        traceback.print_exc()
        return

    # === Paso 4: Verificar stats finales ===
    print("\n4. Estadísticas finales de ChromaDB...")
    try:
        stats = chroma.get_stats()
        for col_name, col_stats in stats['collections'].items():
            print(f"   Colección '{col_name}': {col_stats['count']} documentos")

    except Exception as e:
        print(f"   ERROR obteniendo stats: {e}")

    # === Paso 5: Probar búsqueda semántica ===
    print("\n5. Probando búsqueda semántica...")
    try:
        resultados = rag.buscar(
            query="apelación sentencia recurso",
            n_results=3
        )

        if resultados:
            print(f"   Encontrados {len(resultados)} resultados")
            for i, r in enumerate(resultados):
                print(f"\n   Resultado {i+1}:")
                print(f"   - Score: {r['score']:.3f}")
                print(f"   - ID: {r['id']}")
                print(f"   - Fragmento: {r['document'][:100]}...")
        else:
            print("   No se encontraron resultados")

    except Exception as e:
        print(f"   ERROR en búsqueda: {e}")

    print("\n" + "=" * 60)
    print("Test de RAG completado")
    print("=" * 60)


if __name__ == "__main__":
    test_indexacion_rag()
