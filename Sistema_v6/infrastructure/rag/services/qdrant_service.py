"""
QdrantService - Servicio para interactuar con Qdrant Vector Database

Maneja:
- Conexión a Qdrant
- Creación y gestión de colecciones
- CRUD de chunks vectorizados
- Búsqueda por similitud (dense vectors)
- Búsqueda híbrida (dense + sparse)
"""

import logging
from typing import List, Optional, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    MatchText,
    Range,
    ScoredPoint,
    SearchRequest,
    NamedVector,
)

from infrastructure.rag.config import get_rag_settings
from infrastructure.rag.models.dto import DocumentChunk, SearchQuery

logger = logging.getLogger(__name__)


class QdrantService:
    """Servicio para operaciones con Qdrant"""

    def __init__(self):
        self.settings = get_rag_settings()
        self.client: Optional[QdrantClient] = None
        self.collection_name = self.settings.qdrant_collection

    def connect(self) -> None:
        """Conectar a Qdrant"""
        try:
            self.client = QdrantClient(
                host=self.settings.qdrant_host,
                port=self.settings.qdrant_port,
                timeout=self.settings.qdrant_timeout,
            )
            logger.info(f"Conectado a Qdrant en {self.settings.qdrant_host}:{self.settings.qdrant_port}")
        except Exception as e:
            logger.error(f"Error al conectar con Qdrant: {e}")
            raise

    def disconnect(self) -> None:
        """Cerrar conexión"""
        if self.client:
            self.client.close()
            logger.info("Desconectado de Qdrant")

    def health_check(self) -> bool:
        """Verificar que Qdrant esté disponible"""
        try:
            if not self.client:
                self.connect()
            # Intentar listar colecciones como health check
            self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Health check falló: {e}")
            return False

    def create_collection(self, recreate: bool = False) -> None:
        """
        Crear colección para actuaciones

        Args:
            recreate: Si True, elimina colección existente y la recrea
        """
        try:
            if not self.client:
                self.connect()

            # Verificar si existe
            collections = self.client.get_collections().collections
            exists = any(col.name == self.collection_name for col in collections)

            if exists:
                if recreate:
                    logger.warning(f"Eliminando colección existente: {self.collection_name}")
                    self.client.delete_collection(self.collection_name)
                else:
                    logger.info(f"Colección {self.collection_name} ya existe")
                    return

            # Crear colección con vectores densos
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.settings.embedding_dimension,
                    distance=Distance.COSINE,  # Cosine similarity para embeddings
                ),
            )
            logger.info(f"Colección {self.collection_name} creada exitosamente")

        except Exception as e:
            logger.error(f"Error al crear colección: {e}")
            raise

    def collection_exists(self) -> bool:
        """Verificar si la colección existe"""
        try:
            if not self.client:
                self.connect()
            collections = self.client.get_collections().collections
            return any(col.name == self.collection_name for col in collections)
        except Exception as e:
            logger.error(f"Error al verificar colección: {e}")
            return False

    def ensure_collection_exists(self) -> None:
        """
        Asegurar que la colección existe, crearla si no existe

        Este método es seguro para llamar múltiples veces
        """
        try:
            if not self.client:
                self.connect()

            if not self.collection_exists():
                logger.info(f"Creando colección {self.collection_name}...")
                self.create_collection(recreate=False)
                logger.info(f"✅ Colección {self.collection_name} creada")
            else:
                logger.debug(f"Colección {self.collection_name} ya existe")
        except Exception as e:
            logger.error(f"Error al asegurar colección: {e}")
            raise

    def count_points(self) -> int:
        """Contar puntos en la colección"""
        try:
            if not self.client:
                self.connect()
            result = self.client.count(collection_name=self.collection_name)
            return result.count
        except Exception as e:
            logger.error(f"Error al contar puntos: {e}")
            return 0

    def upsert_chunks(self, chunks: List[DocumentChunk]) -> None:
        """
        Insertar o actualizar chunks en Qdrant

        Args:
            chunks: Lista de chunks con embeddings ya calculados
        """
        try:
            if not self.client:
                self.connect()

            # Asegurar que la colección existe antes de insertar
            self.ensure_collection_exists()

            if not chunks:
                logger.warning("No hay chunks para insertar")
                return

            # Verificar que los chunks tengan embeddings
            for chunk in chunks:
                if chunk.dense_vector is None:
                    raise ValueError(f"Chunk {chunk.chunk_id} no tiene dense_vector")

            # Convertir chunks a PointStruct
            points = []
            for idx, chunk in enumerate(chunks):
                # Usar hash del chunk_id como ID numérico para Qdrant
                import hashlib
                chunk_id_hash = int(hashlib.md5(chunk.chunk_id.encode()).hexdigest()[:16], 16)

                point = PointStruct(
                    id=chunk_id_hash,  # ID numérico
                    vector=chunk.dense_vector,
                    payload={
                        "chunk_id": chunk.chunk_id,  # Guardar ID original en payload
                        "doc_id": chunk.doc_id,
                        "chunk_index": chunk.chunk_index,
                        "chunk_type": chunk.chunk_type.value,
                        "texto": chunk.texto,
                        **chunk.metadata,
                    },
                )
                points.append(point)

            # Upsert en batch
            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
            )
            logger.info(f"Insertados {len(chunks)} chunks en {self.collection_name}")

        except Exception as e:
            logger.error(f"Error al insertar chunks: {e}")
            raise

    def search_similar(
        self,
        query_vector: List[float],
        limit: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[ScoredPoint]:
        """
        Búsqueda por similitud vectorial

        Args:
            query_vector: Vector de la query
            limit: Número de resultados
            filter_dict: Filtros opcionales (ej: {"doc_id": "actuacion_123"})

        Returns:
            Lista de ScoredPoint con resultados
        """
        try:
            if not self.client:
                self.connect()

            # Construir filtros si existen
            search_filter = None
            if filter_dict:
                conditions = []
                for key, value in filter_dict.items():
                    # Para expediente_numero usar MatchText (búsqueda parcial/contains)
                    # porque los expedientes tienen prefijos como "FPO " que el usuario no incluye
                    if key == "expediente_numero":
                        conditions.append(
                            FieldCondition(
                                key=key,
                                match=MatchText(text=value),
                            )
                        )
                    else:
                        conditions.append(
                            FieldCondition(
                                key=key,
                                match=MatchValue(value=value),
                            )
                        )
                search_filter = Filter(must=conditions)

            # Buscar usando query_points (API nueva de qdrant-client >= 1.7)
            response = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=limit,
                query_filter=search_filter,
                with_payload=True,
            )

            # query_points retorna QueryResponse con .points
            results = response.points if response else []

            logger.info(f"Búsqueda retornó {len(results)} resultados")
            return results

        except Exception as e:
            logger.error(f"Error en búsqueda: {e}")
            raise

    def get_chunk_by_id(self, chunk_id: str) -> Optional[DocumentChunk]:
        """
        Obtener un chunk por su ID

        Args:
            chunk_id: ID del chunk (string)

        Returns:
            DocumentChunk o None si no existe
        """
        try:
            if not self.client:
                self.connect()

            # Buscar por chunk_id en el payload usando scroll
            # (más eficiente que retrieve con hash)
            from qdrant_client.models import Filter, FieldCondition, MatchValue

            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="chunk_id",
                            match=MatchValue(value=chunk_id)
                        )
                    ]
                ),
                limit=1,
            )

            if not results[0]:  # results es (points, next_page_offset)
                return None

            point = results[0][0]
            # Reconstruir DocumentChunk desde payload
            from infrastructure.rag.models.dto import ChunkType

            chunk = DocumentChunk(
                chunk_id=point.payload.get("chunk_id"),
                doc_id=point.payload.get("doc_id"),
                chunk_index=point.payload.get("chunk_index"),
                chunk_type=ChunkType(point.payload.get("chunk_type")),
                texto=point.payload.get("texto"),
                metadata={k: v for k, v in point.payload.items() if k not in [
                    "chunk_id", "doc_id", "chunk_index", "chunk_type", "texto"
                ]},
                dense_vector=point.vector if hasattr(point, 'vector') else None,
            )
            return chunk

        except Exception as e:
            logger.error(f"Error al obtener chunk {chunk_id}: {e}")
            return None

    def delete_by_doc_id(self, doc_id: str) -> int:
        """
        Eliminar todos los chunks de un documento

        Args:
            doc_id: ID del documento

        Returns:
            Número de chunks eliminados
        """
        try:
            if not self.client:
                self.connect()

            # Primero contar cuántos hay
            count_before = self.count_points()

            # Eliminar por filtro
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="doc_id",
                            match=MatchValue(value=doc_id),
                        )
                    ]
                ),
            )

            count_after = self.count_points()
            deleted = count_before - count_after

            logger.info(f"Eliminados {deleted} chunks del documento {doc_id}")
            return deleted

        except Exception as e:
            logger.error(f"Error al eliminar chunks del documento {doc_id}: {e}")
            raise

    def clear_collection(self) -> None:
        """Eliminar todos los puntos de la colección"""
        try:
            if not self.client:
                self.connect()

            # Eliminar colección y recrear
            if self.collection_exists():
                self.client.delete_collection(self.collection_name)
                logger.info(f"Colección {self.collection_name} eliminada")

            self.create_collection()
            logger.info(f"Colección {self.collection_name} recreada vacía")

        except Exception as e:
            logger.error(f"Error al limpiar colección: {e}")
            raise

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
