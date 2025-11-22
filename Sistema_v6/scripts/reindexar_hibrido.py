"""
Script para re-indexar actuaciones con búsqueda híbrida.

Limpia los índices existentes y re-indexa todas las actuaciones
con los nuevos parámetros (chunks 1000, overlap 150) en:
- ChromaDB (búsqueda semántica)
- BM25 Whoosh (búsqueda por keywords)
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


def reindexar_hibrido(limpiar_indices: bool = True):
    """
    Re-indexa todas las actuaciones en ChromaDB y BM25.

    Args:
        limpiar_indices: Si True, limpia los índices antes de re-indexar
    """

    print("=" * 60)
    print("Re-indexación Híbrida (ChromaDB + BM25)")
    print("=" * 60)

    # === Inicializar servicios ===
    print("\n1. Inicializando servicios...")

    try:
        from infrastructure.vector_store.chroma_client import ChromaClient
        from infrastructure.vector_store.bm25_indexer import BM25Indexer
        from application.services.ia.embeddings_service import EmbeddingsService
        from application.services.ia.rag_service import RAGService

        chroma = ChromaClient(
            persist_directory="./data/vector_store",
            collection_name="actuaciones"
        )

        bm25 = BM25Indexer(
            index_dir="./data/bm25_index",
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
        import traceback
        traceback.print_exc()
        return

    # === Limpiar índices existentes ===
    if limpiar_indices:
        print("\n2. Limpiando índices existentes...")
        try:
            # Limpiar ChromaDB
            chroma.delete_collection("actuaciones")
            print("   ChromaDB limpiado")

            # Limpiar BM25
            bm25.clear()
            print("   BM25 limpiado")

        except Exception as e:
            print(f"   Advertencia limpiando índices: {e}")

    # === Obtener TODAS las actuaciones con texto ===
    print("\n3. Obteniendo actuaciones...")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT id, tipo, detalle, texto_extraido, expediente_numero, expediente_id, fecha
        FROM actuaciones
        WHERE tiene_texto_extraido = 1
          AND LENGTH(texto_extraido) > 100
        ORDER BY id
    """
    cursor.execute(query)
    actuaciones = cursor.fetchall()

    total = len(actuaciones)
    print(f"   Encontradas {total} actuaciones para indexar")

    if not actuaciones:
        print("   No hay actuaciones con texto")
        cursor.close()
        conn.close()
        return

    # === Indexar en batches ===
    print("\n4. Indexando actuaciones (ChromaDB + BM25)...")
    print("   Parámetros: chunk_size=1000, overlap=150")

    indexadas = 0
    errores = 0
    batch_size = 10

    inicio = datetime.now()

    for i, act in enumerate(actuaciones):
        try:
            # RAGService.indexar_actuacion ahora indexa en ambos
            # Formatear fecha
            fecha = act.get('fecha')
            fecha_str = fecha.strftime('%Y-%m-%d') if fecha else ''

            rag.indexar_actuacion(
                id_actuacion=str(act['id']),
                texto=act['texto_extraido'],
                metadata={
                    "expediente_id": str(act.get('expediente_id', '') or ''),
                    "expediente_numero": act.get('expediente_numero', ''),
                    "tipo": act.get('tipo', ''),
                    "detalle": act.get('detalle', '') or '',
                    "fecha": fecha_str
                }
            )

            # Marcar como indexada en BD
            cursor.execute(
                "UPDATE actuaciones SET indexado_rag = 1 WHERE id = %s",
                (act['id'],)
            )

            indexadas += 1

            # Commit y progreso cada batch
            if (i + 1) % batch_size == 0:
                conn.commit()
                elapsed = (datetime.now() - inicio).total_seconds()
                rate = indexadas / elapsed if elapsed > 0 else 0
                eta = (total - indexadas) / rate if rate > 0 else 0
                print(f"   Progreso: {i + 1}/{total} | {rate:.1f} act/s | ETA: {eta/60:.1f} min")

        except Exception as e:
            errores += 1
            print(f"   ERROR en actuación {act['id']}: {str(e)[:80]}")

    # Commit final
    conn.commit()
    cursor.close()
    conn.close()

    duracion = (datetime.now() - inicio).total_seconds()

    # === Estadísticas finales ===
    print("\n5. Estadísticas finales...")

    try:
        chroma_stats = chroma.get_stats()
        for col_name, col_stats in chroma_stats['collections'].items():
            print(f"   ChromaDB '{col_name}': {col_stats['count']} chunks")
    except Exception as e:
        print(f"   Error stats ChromaDB: {e}")

    try:
        bm25_stats = bm25.get_stats()
        print(f"   BM25: {bm25_stats['doc_count']} documentos")
    except Exception as e:
        print(f"   Error stats BM25: {e}")

    print("\n" + "=" * 60)
    print(f"RESULTADO: {indexadas}/{total} indexadas, {errores} errores")
    print(f"Tiempo: {duracion/60:.1f} minutos")
    print("=" * 60)

    # === Prueba de búsqueda híbrida ===
    print("\n6. Prueba de búsqueda híbrida...")

    try:
        queries = [
            "sentencia definitiva",
            "recurso de apelación",
            "García demanda",
            "medida cautelar embargo"
        ]

        for query in queries:
            # Búsqueda híbrida
            resultados = rag.buscar_hibrido(query=query, n_results=2)
            if resultados:
                print(f"\n   Query: '{query}'")
                for r in resultados:
                    score = r.get('hybrid_score', r.get('score', 0))
                    doc = r.get('document', '')[:60]
                    print(f"   - Score: {score:.4f} | {doc}...")
            else:
                print(f"   Query: '{query}' - Sin resultados")

    except Exception as e:
        print(f"   Error en búsqueda: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Re-indexar actuaciones para búsqueda híbrida")
    parser.add_argument("--no-limpiar", action="store_true",
                       help="No limpiar índices existentes (agregar a lo existente)")

    args = parser.parse_args()

    reindexar_hibrido(limpiar_indices=not args.no_limpiar)
