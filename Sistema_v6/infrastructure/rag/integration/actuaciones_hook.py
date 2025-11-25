"""
Hook de integración para indexación automática de actuaciones

Se ejecuta después del procesamiento de actuaciones en el GestorBatch
para indexar automáticamente en el sistema RAG.
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

from infrastructure.rag.services.rag_indexer import RAGIndexer

logger = logging.getLogger(__name__)


class ActuacionesIndexHook:
    """Hook para indexación automática post-procesamiento"""

    def __init__(self, enabled: bool = True):
        """
        Args:
            enabled: Si False, el hook no hace nada (útil para testing)
        """
        self.enabled = enabled
        self.indexer: Optional[RAGIndexer] = None

    def _get_indexer(self) -> RAGIndexer:
        """Lazy initialization del indexer"""
        if self.indexer is None:
            self.indexer = RAGIndexer()
        return self.indexer

    def on_expediente_procesado(
        self,
        numero_expediente: str,
        resultado: Dict[str, Any]
    ) -> None:
        """
        Callback ejecutado después de procesar un expediente

        Args:
            numero_expediente: Número del expediente procesado
            resultado: Diccionario con resultado del procesamiento
        """
        if not self.enabled:
            return

        try:
            # Verificar que el procesamiento fue exitoso
            if not resultado.get("success"):
                logger.debug(f"⏭️ Skipping indexación de {numero_expediente} (procesamiento falló)")
                return

            # Obtener ruta del JSON
            ruta_json = resultado.get("data", {}).get("ruta_json")
            if not ruta_json:
                logger.warning(f"⚠️ No se encontró ruta_json para {numero_expediente}")
                return

            ruta_json = Path(ruta_json)
            if not ruta_json.exists():
                logger.warning(f"⚠️ JSON no existe: {ruta_json}")
                return

            # Indexar en RAG
            logger.info(f"🔄 Indexando {numero_expediente} en RAG...")
            indexer = self._get_indexer()
            resultado_index = indexer.indexar_expediente(
                ruta_json=ruta_json,
                expediente_numero=numero_expediente
            )

            if resultado_index["success"]:
                chunks = resultado_index.get("chunks_indexados", 0)
                logger.info(f"✅ {numero_expediente} indexado en RAG ({chunks} chunks)")
            else:
                error = resultado_index.get("error", "Error desconocido")
                logger.error(f"❌ Error indexando {numero_expediente}: {error}")

        except Exception as e:
            logger.error(f"❌ Error en hook de indexación para {numero_expediente}: {e}")
            # No propagamos la excepción para no interrumpir el flujo principal


# Instancia global del hook (puede ser configurada)
actuaciones_index_hook = ActuacionesIndexHook(enabled=True)


def configurar_hook(enabled: bool = True) -> None:
    """
    Configurar el hook de indexación

    Args:
        enabled: Habilitar/deshabilitar el hook
    """
    global actuaciones_index_hook
    actuaciones_index_hook.enabled = enabled
    logger.info(f"Hook de indexación RAG: {'habilitado' if enabled else 'deshabilitado'}")


def obtener_hook() -> ActuacionesIndexHook:
    """Obtener instancia del hook"""
    return actuaciones_index_hook
