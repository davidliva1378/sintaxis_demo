"""
Cliente de ChromaDB para almacenamiento de embeddings.

Proporciona búsqueda semántica para el sistema RAG.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class ChromaClient:
    """
    Cliente para ChromaDB (base de datos vectorial).

    Permite almacenar y buscar embeddings para búsqueda semántica.
    """

    def __init__(
        self,
        persist_directory: str = "./data/vector_store",
        collection_name: str = "actuaciones"
    ):
        """
        Inicializa el cliente de ChromaDB.

        Args:
            persist_directory: Directorio para persistir datos
            collection_name: Nombre de la colección por defecto
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self._client = None
        self._collection = None

    def _lazy_load_client(self):
        """Carga el cliente solo cuando se necesita."""
        if self._client is None:
            try:
                import chromadb
                from chromadb.config import Settings

                # Crear directorio si no existe
                Path(self.persist_directory).mkdir(parents=True, exist_ok=True)

                # Cliente persistente
                self._client = chromadb.PersistentClient(
                    path=self.persist_directory,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )

                logger.info(f"ChromaDB inicializado en: {self.persist_directory}")

            except ImportError:
                raise ImportError(
                    "chromadb no está instalado. "
                    "Instalar con: pip install chromadb"
                )

        return self._client

    def get_collection(self, name: Optional[str] = None):
        """
        Obtiene o crea una colección.

        Args:
            name: Nombre de la colección (usa default si no se especifica)

        Returns:
            Colección de ChromaDB
        """
        client = self._lazy_load_client()
        collection_name = name or self.collection_name

        collection = client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        if name is None:
            self._collection = collection

        return collection

    def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        collection_name: Optional[str] = None
    ):
        """
        Agrega documentos a la colección.

        Args:
            ids: IDs únicos para cada documento
            embeddings: Lista de embeddings
            documents: Textos originales
            metadatas: Metadata para cada documento
            collection_name: Colección (usa default si no se especifica)
        """
        collection = self.get_collection(collection_name)

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

        logger.debug(f"Agregados {len(ids)} documentos a {collection.name}")

    def query(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        collection_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Busca documentos similares.

        Args:
            query_embedding: Embedding de la consulta
            n_results: Número de resultados
            where: Filtros de metadata
            collection_name: Colección a buscar

        Returns:
            Dict con ids, documents, metadatas, distances
        """
        collection = self.get_collection(collection_name)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )

        return {
            "ids": results["ids"][0] if results["ids"] else [],
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else []
        }

    def search(
        self,
        query_text: str,
        embeddings_service,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        collection_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Búsqueda semántica con texto.

        Args:
            query_text: Texto de búsqueda
            embeddings_service: Servicio para generar embeddings
            n_results: Número de resultados
            where: Filtros de metadata
            collection_name: Colección a buscar

        Returns:
            Lista de resultados con documento, metadata y score
        """
        # Generar embedding de la consulta
        query_embedding = embeddings_service.encode_query(query_text)

        # Buscar
        results = self.query(
            query_embedding=query_embedding,
            n_results=n_results,
            where=where,
            collection_name=collection_name
        )

        # Formatear resultados
        formatted = []
        for i in range(len(results["ids"])):
            formatted.append({
                "id": results["ids"][i],
                "document": results["documents"][i],
                "metadata": results["metadatas"][i] if results["metadatas"] else {},
                "score": 1 - results["distances"][i] if results["distances"] else 0
            })

        return formatted

    def delete(
        self,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
        collection_name: Optional[str] = None
    ):
        """
        Elimina documentos de la colección.

        Args:
            ids: IDs a eliminar
            where: Filtro para eliminar
            collection_name: Colección
        """
        collection = self.get_collection(collection_name)

        if ids:
            collection.delete(ids=ids)
        elif where:
            collection.delete(where=where)

        logger.debug(f"Eliminados documentos de {collection.name}")

    def update(
        self,
        ids: List[str],
        embeddings: Optional[List[List[float]]] = None,
        documents: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None,
        collection_name: Optional[str] = None
    ):
        """
        Actualiza documentos existentes.

        Args:
            ids: IDs a actualizar
            embeddings: Nuevos embeddings
            documents: Nuevos textos
            metadatas: Nueva metadata
            collection_name: Colección
        """
        collection = self.get_collection(collection_name)

        collection.update(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

    def count(self, collection_name: Optional[str] = None) -> int:
        """
        Cuenta documentos en la colección.

        Args:
            collection_name: Colección

        Returns:
            Número de documentos
        """
        collection = self.get_collection(collection_name)
        return collection.count()

    def list_collections(self) -> List[str]:
        """
        Lista todas las colecciones.

        Returns:
            Nombres de colecciones
        """
        client = self._lazy_load_client()
        collections = client.list_collections()
        return [c.name for c in collections]

    def delete_collection(self, name: str):
        """
        Elimina una colección completa.

        Args:
            name: Nombre de la colección
        """
        client = self._lazy_load_client()
        client.delete_collection(name)
        logger.info(f"Colección {name} eliminada")

    def reset(self):
        """
        Elimina todos los datos (PELIGROSO).
        """
        client = self._lazy_load_client()
        client.reset()
        logger.warning("ChromaDB reseteado - todos los datos eliminados")

    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del store.

        Returns:
            Dict con estadísticas
        """
        client = self._lazy_load_client()
        collections = client.list_collections()

        stats = {
            "persist_directory": self.persist_directory,
            "collections": {}
        }

        for col in collections:
            stats["collections"][col.name] = {
                "count": col.count()
            }

        return stats
