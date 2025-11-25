"""
Script de prueba para QdrantService

Verifica:
1. Conexión a Qdrant
2. Creación de colección
3. Health check
"""

import sys
import logging
from pathlib import Path

# Agregar path para imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from infrastructure.rag.services.qdrant_service import QdrantService

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_qdrant_connection():
    """Probar conexión y operaciones básicas con Qdrant"""

    logger.info("=" * 60)
    logger.info("Iniciando pruebas de QdrantService")
    logger.info("=" * 60)

    try:
        # 1. Crear servicio
        logger.info("\n1. Creando QdrantService...")
        qdrant = QdrantService()

        # 2. Conectar
        logger.info("\n2. Conectando a Qdrant...")
        qdrant.connect()
        logger.info("✅ Conexión exitosa")

        # 3. Health check
        logger.info("\n3. Verificando health check...")
        is_healthy = qdrant.health_check()
        if is_healthy:
            logger.info("✅ Qdrant está saludable")
        else:
            logger.error("❌ Qdrant no responde correctamente")
            return False

        # 4. Verificar si colección existe
        logger.info("\n4. Verificando colección...")
        exists = qdrant.collection_exists()
        if exists:
            logger.info(f"✅ Colección '{qdrant.collection_name}' ya existe")
            count = qdrant.count_points()
            logger.info(f"   Contiene {count} puntos")
        else:
            logger.info(f"⚠️  Colección '{qdrant.collection_name}' no existe")

        # 5. Crear colección (no recrear si existe)
        logger.info("\n5. Creando colección (si no existe)...")
        qdrant.create_collection(recreate=False)
        logger.info("✅ Colección lista para usar")

        # 6. Contar puntos
        logger.info("\n6. Contando puntos en colección...")
        count = qdrant.count_points()
        logger.info(f"✅ La colección tiene {count} puntos")

        # 7. Desconectar
        logger.info("\n7. Desconectando...")
        qdrant.disconnect()
        logger.info("✅ Desconexión exitosa")

        logger.info("\n" + "=" * 60)
        logger.info("✅ TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"\n❌ Error en las pruebas: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_qdrant_connection()
    sys.exit(0 if success else 1)
