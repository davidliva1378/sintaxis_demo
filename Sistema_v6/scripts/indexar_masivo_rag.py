"""
Script para indexación masiva RAG de actuaciones.
Indexa todas las actuaciones con texto que no están indexadas.
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


def indexar_masivo():
    """Indexa todas las actuaciones pendientes en ChromaDB."""

    print("=" * 60)
    print("Indexación Masiva RAG")
    print("=" * 60)

    # === Inicializar servicios ===
    print("\n1. Inicializando servicios...")

    try:
        from infrastructure.vector_store.chroma_client import ChromaClient
        from application.services.ia.embeddings_service import EmbeddingsService
        from application.services.ia.rag_service import RAGService

        chroma = ChromaClient(
            persist_directory="./data/vector_store",
            collection_name="actuaciones"
        )

        embeddings = EmbeddingsService(device="cpu")

        rag = RAGService(
            embeddings_service=embeddings,
            chroma_client=chroma
        )

        print("   Servicios inicializados OK")

    except Exception as e:
        print(f"   ERROR inicializando servicios: {e}")
        return

    # === Obtener actuaciones pendientes ===
    print("\n2. Obteniendo actuaciones pendientes...")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT id, tipo, detalle, texto_extraido, expediente_numero, expediente_id
        FROM actuaciones
        WHERE tiene_texto_extraido = 1
          AND indexado_rag = 0
          AND LENGTH(texto_extraido) > 100
        ORDER BY id
    """
    cursor.execute(query)
    actuaciones = cursor.fetchall()

    total = len(actuaciones)
    print(f"   Encontradas {total} actuaciones para indexar")

    if not actuaciones:
        print("   No hay actuaciones pendientes")
        cursor.close()
        conn.close()
        return

    # === Indexar en batches ===
    print("\n3. Indexando actuaciones...")

    indexadas = 0
    errores = 0
    batch_size = 10

    for i, act in enumerate(actuaciones):
        try:
            rag.indexar_actuacion(
                id_actuacion=str(act['id']),
                texto=act['texto_extraido'],
                metadata={
                    "expediente_id": str(act.get('expediente_id', '') or ''),
                    "expediente_numero": act.get('expediente_numero', ''),
                    "tipo": act.get('tipo', ''),
                    "detalle": (act.get('detalle', '') or '')[:100]
                }
            )

            # Marcar como indexada en BD
            cursor.execute(
                "UPDATE actuaciones SET indexado_rag = 1 WHERE id = %s",
                (act['id'],)
            )

            indexadas += 1

            # Commit cada batch
            if (i + 1) % batch_size == 0:
                conn.commit()
                print(f"   Progreso: {i + 1}/{total} ({indexadas} OK, {errores} errores)")

        except Exception as e:
            errores += 1
            print(f"   ERROR en actuación {act['id']}: {str(e)[:50]}")

    # Commit final
    conn.commit()
    cursor.close()
    conn.close()

    # === Estadísticas finales ===
    print("\n4. Estadísticas finales...")

    try:
        stats = chroma.get_stats()
        for col_name, col_stats in stats['collections'].items():
            print(f"   Colección '{col_name}': {col_stats['count']} documentos")
    except Exception as e:
        print(f"   Error obteniendo stats: {e}")

    print("\n" + "=" * 60)
    print(f"RESULTADO: {indexadas}/{total} indexadas, {errores} errores")
    print("=" * 60)

    # === Prueba de búsqueda ===
    print("\n5. Prueba de búsqueda semántica...")

    try:
        queries = [
            "sentencia definitiva",
            "recurso de apelación",
            "notificación cédula",
            "medida cautelar embargo"
        ]

        for query in queries:
            resultados = rag.buscar(query=query, n_results=2)
            if resultados:
                print(f"\n   Query: '{query}'")
                for r in resultados:
                    print(f"   - Score: {r['score']:.3f} | {r['document'][:60]}...")
            else:
                print(f"   Query: '{query}' - Sin resultados")

    except Exception as e:
        print(f"   Error en búsqueda: {e}")


if __name__ == "__main__":
    indexar_masivo()
