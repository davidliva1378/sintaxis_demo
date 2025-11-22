"""
Indexador BM25 para búsqueda por palabras clave.

Complementa la búsqueda semántica con búsqueda exacta de términos.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from whoosh import index
from whoosh.fields import Schema, TEXT, ID, STORED
from whoosh.qparser import QueryParser, OrGroup
from whoosh.analysis import StemmingAnalyzer, LanguageAnalyzer
from whoosh.scoring import BM25F

logger = logging.getLogger(__name__)


class BM25Indexer:
    """
    Indexador BM25 usando Whoosh.

    Permite búsqueda por palabras clave con scoring BM25.
    """

    def __init__(
        self,
        index_dir: str = "./data/bm25_index",
        collection_name: str = "actuaciones"
    ):
        """
        Inicializa el indexador BM25.

        Args:
            index_dir: Directorio para el índice
            collection_name: Nombre de la colección
        """
        self.index_dir = Path(index_dir)
        self.collection_name = collection_name
        self._ix = None

        # Esquema para documentos legales
        # Usando analizador español para stemming
        try:
            analyzer = LanguageAnalyzer("es")
        except Exception:
            # Fallback a stemming analyzer si no hay soporte español
            analyzer = StemmingAnalyzer()

        self.schema = Schema(
            id=ID(stored=True, unique=True),
            content=TEXT(stored=True, analyzer=analyzer),
            actuacion_id=ID(stored=True),
            expediente_id=ID(stored=True),
            expediente_numero=ID(stored=True),
            tipo=STORED(),
            detalle=STORED()
        )

    def _get_index(self):
        """Obtiene o crea el índice."""
        if self._ix is None:
            self.index_dir.mkdir(parents=True, exist_ok=True)

            index_path = self.index_dir / self.collection_name

            if index.exists_in(str(index_path)):
                self._ix = index.open_dir(str(index_path))
                logger.debug(f"Índice BM25 abierto: {index_path}")
            else:
                index_path.mkdir(parents=True, exist_ok=True)
                self._ix = index.create_in(str(index_path), self.schema)
                logger.info(f"Índice BM25 creado: {index_path}")

        return self._ix

    def add(
        self,
        doc_id: str,
        content: str,
        actuacion_id: str = "",
        expediente_id: str = "",
        expediente_numero: str = "",
        tipo: str = "",
        detalle: str = ""
    ):
        """
        Agrega un documento al índice.

        Args:
            doc_id: ID único del documento
            content: Contenido textual
            actuacion_id: ID de la actuación
            expediente_id: ID del expediente
            expediente_numero: Número del expediente
            tipo: Tipo de actuación
            detalle: Detalle de la actuación
        """
        ix = self._get_index()
        writer = ix.writer()

        writer.update_document(
            id=doc_id,
            content=content,
            actuacion_id=actuacion_id,
            expediente_id=expediente_id,
            expediente_numero=expediente_numero,
            tipo=tipo,
            detalle=detalle
        )

        writer.commit()
        logger.debug(f"Documento indexado en BM25: {doc_id}")

    def add_batch(self, documents: List[Dict[str, Any]]):
        """
        Agrega múltiples documentos al índice.

        Args:
            documents: Lista de documentos con id, content, y metadata
        """
        ix = self._get_index()
        writer = ix.writer()

        for doc in documents:
            writer.update_document(
                id=doc.get("id", ""),
                content=doc.get("content", ""),
                actuacion_id=doc.get("actuacion_id", ""),
                expediente_id=doc.get("expediente_id", ""),
                expediente_numero=doc.get("expediente_numero", ""),
                tipo=doc.get("tipo", ""),
                detalle=doc.get("detalle", "")
            )

        writer.commit()
        logger.info(f"Indexados {len(documents)} documentos en BM25")

    def search(
        self,
        query: str,
        n_results: int = 10,
        expediente_id: Optional[str] = None,
        expediente_numero: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca documentos por palabras clave.

        Args:
            query: Texto de búsqueda
            n_results: Número máximo de resultados
            expediente_id: Filtrar por expediente ID
            expediente_numero: Filtrar por número de expediente

        Returns:
            Lista de resultados con id, content, score y metadata
        """
        ix = self._get_index()

        results = []

        with ix.searcher(weighting=BM25F()) as searcher:
            # Parser con OR por defecto para mayor recall
            parser = QueryParser("content", ix.schema, group=OrGroup)

            # Construir query
            query_str = query

            # Agregar filtros si existen
            if expediente_id:
                query_str = f"({query}) AND expediente_id:{expediente_id}"
            elif expediente_numero:
                query_str = f"({query}) AND expediente_numero:{expediente_numero}"

            try:
                q = parser.parse(query_str)
                hits = searcher.search(q, limit=n_results)

                for hit in hits:
                    results.append({
                        "id": hit["id"],
                        "document": hit["content"],
                        "score": hit.score,
                        "metadata": {
                            "actuacion_id": hit.get("actuacion_id", ""),
                            "expediente_id": hit.get("expediente_id", ""),
                            "expediente_numero": hit.get("expediente_numero", ""),
                            "tipo": hit.get("tipo", ""),
                            "detalle": hit.get("detalle", "")
                        }
                    })

            except Exception as e:
                logger.error(f"Error en búsqueda BM25: {e}")

        return results

    def delete(self, doc_id: str):
        """
        Elimina un documento del índice.

        Args:
            doc_id: ID del documento a eliminar
        """
        ix = self._get_index()
        writer = ix.writer()
        writer.delete_by_term("id", doc_id)
        writer.commit()
        logger.debug(f"Documento eliminado de BM25: {doc_id}")

    def delete_by_expediente(self, expediente_numero: str):
        """
        Elimina todos los documentos de un expediente.

        Args:
            expediente_numero: Número del expediente
        """
        ix = self._get_index()
        writer = ix.writer()
        writer.delete_by_term("expediente_numero", expediente_numero)
        writer.commit()
        logger.info(f"Documentos eliminados de BM25 para: {expediente_numero}")

    def count(self) -> int:
        """
        Cuenta documentos en el índice.

        Returns:
            Número de documentos
        """
        ix = self._get_index()
        return ix.doc_count()

    def clear(self):
        """
        Elimina todos los documentos del índice.
        """
        ix = self._get_index()
        writer = ix.writer()
        writer.commit(mergetype=index.CLEAR)
        logger.warning(f"Índice BM25 {self.collection_name} limpiado")

    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del índice.

        Returns:
            Dict con estadísticas
        """
        ix = self._get_index()

        return {
            "index_dir": str(self.index_dir),
            "collection": self.collection_name,
            "doc_count": ix.doc_count(),
            "last_modified": ix.last_modified()
        }
