"""
Script para reindexar expedientes existentes en el sistema RAG

Uso:
    python reindexar_expedientes.py [--directorio DIR] [--limite N] [--limpiar]

Argumentos:
    --directorio: Directorio base de expedientes (default: desde config)
    --limite: Límite de expedientes a procesar (default: todos)
    --limpiar: Limpiar índices antes de reindexar
"""

import sys
import logging
import argparse
from pathlib import Path

# Agregar path para imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from infrastructure.rag.services.rag_indexer import RAGIndexer
from infrastructure.rag.config import get_rag_settings

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main del script de reindexación"""

    parser = argparse.ArgumentParser(
        description="Reindexar expedientes en el sistema RAG"
    )
    parser.add_argument(
        '--directorio',
        type=str,
        help='Directorio base de expedientes',
        default=None
    )
    parser.add_argument(
        '--limite',
        type=int,
        help='Límite de expedientes a procesar',
        default=None
    )
    parser.add_argument(
        '--limpiar',
        action='store_true',
        help='Limpiar índices antes de reindexar'
    )

    args = parser.parse_args()

    try:
        logger.info("=" * 60)
        logger.info("REINDEXACIÓN DE EXPEDIENTES EN RAG")
        logger.info("=" * 60)

        # Obtener directorio base
        if args.directorio:
            directorio_base = Path(args.directorio)
        else:
            # Usar directorio por defecto desde config
            settings = get_rag_settings()
            # Asumir estructura: Sistema_v6/data/actuaciones
            directorio_base = Path(__file__).parent.parent.parent.parent / "data" / "actuaciones"

        logger.info(f"\nDirectorio base: {directorio_base}")

        if not directorio_base.exists():
            logger.error(f"❌ El directorio no existe: {directorio_base}")
            return 1

        # Crear indexer
        indexer = RAGIndexer()

        # Limpiar índices si se solicitó
        if args.limpiar:
            logger.info("\n🗑️ Limpiando índices existentes...")
            try:
                indexer.search_service.qdrant.clear_collection()
                indexer.search_service.bm25.clear_index()
                logger.info("✅ Índices limpiados")
            except Exception as e:
                logger.error(f"❌ Error limpiando índices: {e}")
                return 1

        # Mostrar estadísticas iniciales
        logger.info("\n📊 Estadísticas iniciales:")
        stats_inicial = indexer.get_stats()
        logger.info(f"   Qdrant: {stats_inicial['qdrant']['count']} puntos")
        logger.info(f"   BM25: {stats_inicial['bm25']['total_documents']} documentos")

        # Reindexar
        logger.info(f"\n🔄 Iniciando reindexación...")
        if args.limite:
            logger.info(f"   Límite: {args.limite} expedientes")

        resultado = indexer.reindexar_todos_expedientes(
            directorio_base=directorio_base,
            limite=args.limite
        )

        if not resultado["success"]:
            logger.error(f"\n❌ Error en reindexación: {resultado.get('error')}")
            return 1

        # Mostrar estadísticas finales
        logger.info("\n📊 Estadísticas finales:")
        stats_final = indexer.get_stats()
        logger.info(f"   Qdrant: {stats_final['qdrant']['count']} puntos")
        logger.info(f"   BM25: {stats_final['bm25']['total_documents']} documentos")

        logger.info("\n✅ REINDEXACIÓN COMPLETADA EXITOSAMENTE")
        return 0

    except KeyboardInterrupt:
        logger.warning("\n⚠️ Reindexación interrumpida por el usuario")
        return 130
    except Exception as e:
        logger.error(f"\n❌ Error crítico: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
