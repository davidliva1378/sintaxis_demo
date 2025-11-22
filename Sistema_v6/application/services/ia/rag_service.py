"""
Servicio RAG (Retrieval Augmented Generation) para actuaciones.

Permite indexar actuaciones y realizar búsquedas semánticas
para encontrar información relevante en el expediente.
"""

import logging
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from .hybrid_search import HybridSearchService

logger = logging.getLogger(__name__)


class RAGService:
    """
    Servicio para búsqueda semántica y generación aumentada.

    Combina ChromaDB para búsqueda vectorial con LLM para
    generar respuestas contextualizadas.
    """

    def __init__(
        self,
        embeddings_service=None,
        chroma_client=None,
        llm_service=None,
        collection_name: str = "actuaciones"
    ):
        """
        Inicializa el servicio RAG.

        Args:
            embeddings_service: Servicio de embeddings
            chroma_client: Cliente de ChromaDB
            llm_service: Servicio LLM
            collection_name: Nombre de la colección
        """
        self._embeddings = embeddings_service
        self._chroma = chroma_client
        self._llm = llm_service
        self._hybrid_search = None
        self.collection_name = collection_name

        # Cache para consultas frecuentes (TTL: 1 hora)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = timedelta(hours=1)

    def _get_embeddings(self):
        """Obtiene servicio de embeddings (lazy loading)."""
        if self._embeddings is None:
            from .embeddings_service import EmbeddingsService
            self._embeddings = EmbeddingsService()
        return self._embeddings

    def _get_chroma(self):
        """Obtiene cliente ChromaDB (lazy loading)."""
        if self._chroma is None:
            from infrastructure.vector_store import ChromaClient
            self._chroma = ChromaClient()
        return self._chroma

    def _get_llm(self):
        """Obtiene servicio LLM (lazy loading)."""
        if self._llm is None:
            from .llm_service import LLMService
            self._llm = LLMService()
        return self._llm

    def _get_hybrid_search(self):
        """Obtiene servicio de búsqueda híbrida (lazy loading)."""
        if self._hybrid_search is None:
            self._hybrid_search = HybridSearchService(
                chroma_client=self._get_chroma(),
                embeddings_service=self._get_embeddings()
            )
        return self._hybrid_search

    def _cache_key(self, query: str, n_results: int, expediente_id: str = None, expediente_numero: str = None) -> str:
        """Genera clave de cache para una consulta."""
        key_data = f"{query}|{n_results}|{expediente_id or ''}|{expediente_numero or ''}"
        return hashlib.md5(key_data.encode('utf-8')).hexdigest()

    def _cache_get(self, key: str) -> Optional[List[Dict[str, Any]]]:
        """Obtiene resultado del cache si existe y no expiró."""
        if key in self._cache:
            cached = self._cache[key]
            if datetime.now() - cached['timestamp'] < self._cache_ttl:
                logger.debug(f"Cache hit: {key[:8]}...")
                return cached['results']
            else:
                # Expirado, eliminar
                del self._cache[key]
        return None

    def _cache_set(self, key: str, results: List[Dict[str, Any]]):
        """Guarda resultado en cache."""
        self._cache[key] = {
            'results': results,
            'timestamp': datetime.now()
        }
        # Limpiar cache si es muy grande (max 100 entradas)
        if len(self._cache) > 100:
            self._cache_cleanup()

    def _cache_cleanup(self):
        """Elimina entradas expiradas del cache."""
        now = datetime.now()
        expired = [
            key for key, value in self._cache.items()
            if now - value['timestamp'] >= self._cache_ttl
        ]
        for key in expired:
            del self._cache[key]

    def limpiar_cache(self):
        """Limpia todo el cache de consultas."""
        self._cache.clear()
        logger.info("Cache de consultas limpiado")

    def indexar_actuacion(
        self,
        id_actuacion: str,
        texto: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Indexa una actuación individual.

        Args:
            id_actuacion: ID único de la actuación
            texto: Contenido textual
            metadata: Metadatos adicionales
        """
        if not texto or len(texto.strip()) < 10:
            logger.warning(f"Texto muy corto para indexar: {id_actuacion}")
            return

        embeddings_service = self._get_embeddings()
        chroma = self._get_chroma()

        # Generar chunks si el texto es largo
        # Usando chunks más grandes (1000 chars) con mayor overlap (150 chars)
        # para mejor contexto en documentos legales argentinos
        chunks = embeddings_service.chunk_text(texto, chunk_size=1000, overlap=150)

        ids = []
        embeddings = []
        documents = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            chunk_id = f"{id_actuacion}_chunk_{i}"
            embedding = embeddings_service.encode(chunk)

            ids.append(chunk_id)
            embeddings.append(embedding)
            documents.append(chunk)

            chunk_metadata = {
                "actuacion_id": id_actuacion,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "indexed_at": datetime.now().isoformat()
            }

            if metadata:
                chunk_metadata.update(metadata)

            metadatas.append(chunk_metadata)

        # Agregar a ChromaDB
        chroma.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            collection_name=self.collection_name
        )

        # Indexar en BM25 para búsqueda híbrida
        try:
            hybrid = self._get_hybrid_search()
            for i, chunk in enumerate(chunks):
                chunk_id = f"{id_actuacion}_chunk_{i}"
                hybrid.index_document(
                    doc_id=chunk_id,
                    content=chunk,
                    actuacion_id=id_actuacion,
                    expediente_id=metadata.get("expediente_id", "") if metadata else "",
                    expediente_numero=metadata.get("expediente_numero", "") if metadata else "",
                    tipo=metadata.get("tipo", "") if metadata else "",
                    detalle=metadata.get("detalle", "") if metadata else ""
                )
        except Exception as e:
            logger.warning(f"Error indexando en BM25: {e}")

        logger.info(
            f"Indexada actuación {id_actuacion}: "
            f"{len(chunks)} chunks (ChromaDB + BM25)"
        )

    def indexar_batch(
        self,
        actuaciones: List[Dict[str, Any]],
        batch_size: int = 100
    ):
        """
        Indexa múltiples actuaciones.

        Args:
            actuaciones: Lista de actuaciones con id, texto y metadata
            batch_size: Tamaño del batch
        """
        total = len(actuaciones)
        indexadas = 0

        for actuacion in actuaciones:
            try:
                self.indexar_actuacion(
                    id_actuacion=str(actuacion.get("id", "")),
                    texto=actuacion.get("texto", ""),
                    metadata=actuacion.get("metadata", {})
                )
                indexadas += 1

                if indexadas % batch_size == 0:
                    logger.info(f"Progreso: {indexadas}/{total}")

            except Exception as e:
                logger.error(
                    f"Error indexando actuación {actuacion.get('id')}: {e}"
                )

        logger.info(f"Indexación completada: {indexadas}/{total}")

    def buscar(
        self,
        query: str,
        n_results: int = 5,
        filtros: Optional[Dict[str, Any]] = None,
        expediente_id: Optional[str] = None,
        expediente_numero: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca actuaciones relevantes.

        Args:
            query: Texto de búsqueda
            n_results: Número de resultados
            filtros: Filtros adicionales de metadata
            expediente_id: Filtrar por ID de expediente
            expediente_numero: Filtrar por número de expediente (ej: "FPA-004134-2020")

        Returns:
            Lista de resultados con documento, metadata y score
        """
        # Verificar cache (solo si no hay filtros adicionales)
        if not filtros:
            cache_key = self._cache_key(query, n_results, expediente_id, expediente_numero)
            cached_results = self._cache_get(cache_key)
            if cached_results is not None:
                return cached_results

        embeddings_service = self._get_embeddings()
        chroma = self._get_chroma()

        # Construir filtros
        where = {}
        if expediente_id:
            where["expediente_id"] = expediente_id
        if expediente_numero:
            where["expediente_numero"] = expediente_numero
        if filtros:
            where.update(filtros)

        # Buscar
        resultados = chroma.search(
            query_text=query,
            embeddings_service=embeddings_service,
            n_results=n_results,
            where=where if where else None,
            collection_name=self.collection_name
        )

        # Guardar en cache (solo si no hay filtros adicionales)
        if not filtros:
            self._cache_set(cache_key, resultados)

        return resultados

    def buscar_hibrido(
        self,
        query: str,
        n_results: int = 5,
        expediente_id: Optional[str] = None,
        expediente_numero: Optional[str] = None,
        use_bm25: bool = True,
        use_semantic: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Busca actuaciones usando búsqueda híbrida (BM25 + Semántica).

        Combina resultados de búsqueda por palabras clave y semántica
        usando Reciprocal Rank Fusion (RRF) para mejores resultados.

        Args:
            query: Texto de búsqueda
            n_results: Número de resultados
            expediente_id: Filtrar por ID de expediente
            expediente_numero: Filtrar por número de expediente
            use_bm25: Usar búsqueda BM25 (keywords)
            use_semantic: Usar búsqueda semántica (embeddings)

        Returns:
            Lista de resultados con documento, metadata y score híbrido
        """
        # Verificar cache
        cache_key = self._cache_key(f"hybrid:{query}", n_results, expediente_id, expediente_numero)
        cached_results = self._cache_get(cache_key)
        if cached_results is not None:
            return cached_results

        try:
            hybrid = self._get_hybrid_search()
            resultados = hybrid.search(
                query=query,
                n_results=n_results,
                expediente_id=expediente_id,
                expediente_numero=expediente_numero,
                use_bm25=use_bm25,
                use_semantic=use_semantic
            )

            # Guardar en cache
            self._cache_set(cache_key, resultados)

            logger.info(
                f"Búsqueda híbrida: '{query[:50]}...' -> {len(resultados)} resultados"
            )
            return resultados

        except Exception as e:
            logger.error(f"Error en búsqueda híbrida: {e}")
            # Fallback a búsqueda semántica simple
            return self.buscar(
                query=query,
                n_results=n_results,
                expediente_id=expediente_id,
                expediente_numero=expediente_numero
            )

    def responder(
        self,
        pregunta: str,
        n_contextos: int = 5,
        expediente_id: Optional[str] = None,
        expediente_numero: Optional[str] = None,
        incluir_fuentes: bool = True
    ) -> Dict[str, Any]:
        """
        Responde una pregunta usando RAG.

        Args:
            pregunta: Pregunta del usuario
            n_contextos: Número de contextos a recuperar
            expediente_id: Filtrar por ID de expediente
            expediente_numero: Filtrar por número de expediente
            incluir_fuentes: Si incluir las fuentes usadas

        Returns:
            Dict con respuesta y fuentes
        """
        llm = self._get_llm()

        # Buscar contextos relevantes
        contextos = self.buscar(
            query=pregunta,
            n_results=n_contextos,
            expediente_id=expediente_id,
            expediente_numero=expediente_numero
        )

        if not contextos:
            return {
                "respuesta": "No encontré información relevante para responder esta pregunta.",
                "fuentes": [],
                "confianza": 0.0
            }

        # Construir contexto para el LLM
        contexto_texto = "\n\n---\n\n".join([
            f"[Fragmento {i+1}]\n{c['document']}"
            for i, c in enumerate(contextos)
        ])

        system_prompt = """Eres un asistente legal experto en analizar expedientes judiciales argentinos.
Tu tarea es responder preguntas basándote ÚNICAMENTE en la información proporcionada.
Si la información no es suficiente para responder, indícalo claramente.
Sé preciso y conciso en tus respuestas."""

        user_prompt = f"""Basándote en los siguientes fragmentos del expediente, responde la pregunta.

CONTEXTO:
{contexto_texto}

PREGUNTA: {pregunta}

RESPUESTA:"""

        try:
            respuesta = llm.generate(
                user_prompt,
                system=system_prompt,
                temperature=0.3,
                max_tokens=500
            )

            resultado = {
                "respuesta": respuesta.strip(),
                "confianza": sum(c["score"] for c in contextos) / len(contextos)
            }

            if incluir_fuentes:
                resultado["fuentes"] = [
                    {
                        "id": c["metadata"].get("actuacion_id"),
                        "fragmento": c["document"][:200] + "..." if len(c["document"]) > 200 else c["document"],
                        "score": c["score"]
                    }
                    for c in contextos
                ]

            return resultado

        except Exception as e:
            logger.error(f"Error generando respuesta: {e}")
            return {
                "respuesta": f"Error al generar respuesta: {str(e)}",
                "fuentes": [],
                "confianza": 0.0
            }

    def resumir_expediente(
        self,
        expediente_id: Optional[str] = None,
        expediente_numero: Optional[str] = None,
        max_length: int = 500
    ) -> str:
        """
        Genera un resumen del expediente.

        Args:
            expediente_id: ID del expediente
            expediente_numero: Número del expediente (ej: "FPA-004134-2020")
            max_length: Longitud máxima del resumen

        Returns:
            Resumen del expediente
        """
        # Buscar todas las actuaciones del expediente
        contextos = self.buscar(
            query="resumen del caso partes demanda resolución",
            n_results=10,
            expediente_id=expediente_id,
            expediente_numero=expediente_numero
        )

        if not contextos:
            return "No hay información suficiente para generar un resumen."

        llm = self._get_llm()

        contexto_texto = "\n\n".join([c["document"] for c in contextos])

        return llm.summarize(contexto_texto, max_length=max_length)

    def eliminar_actuacion(self, id_actuacion: str):
        """
        Elimina una actuación del índice.

        Args:
            id_actuacion: ID de la actuación
        """
        chroma = self._get_chroma()

        # Eliminar todos los chunks de la actuación
        chroma.delete(
            where={"actuacion_id": id_actuacion},
            collection_name=self.collection_name
        )

        logger.info(f"Eliminada actuación del índice: {id_actuacion}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del índice.

        Returns:
            Dict con estadísticas
        """
        chroma = self._get_chroma()

        return {
            "collection": self.collection_name,
            "total_documents": chroma.count(self.collection_name),
            "chroma_stats": chroma.get_stats()
        }

    def limpiar_indice(self):
        """
        Elimina todos los documentos del índice.
        """
        chroma = self._get_chroma()
        chroma.delete_collection(self.collection_name)
        logger.warning(f"Índice {self.collection_name} eliminado")
