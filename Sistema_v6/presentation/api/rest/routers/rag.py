"""
Router API para sistema RAG

Endpoints:
- POST /api/v1/rag/query - Búsqueda y respuesta con LLM
- POST /api/v1/rag/search - Solo búsqueda (sin LLM)
- POST /api/v1/rag/indexar - Indexar expediente manualmente
- POST /api/v1/rag/reindexar - Reindexar todos los expedientes
- GET /api/v1/rag/stats - Estadísticas de los índices
- GET /api/v1/rag/health - Health check de servicios RAG
"""

import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from infrastructure.rag.services.rag_indexer import RAGIndexer
from infrastructure.rag.services.llm_service import RAGService
from infrastructure.rag.models.dto import SearchQuery

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/rag", tags=["RAG"])


# ==============================================================================
# Modelos de Request/Response
# ==============================================================================

class RAGQueryRequest(BaseModel):
    """Request para query RAG completo (búsqueda + LLM)"""
    pregunta: str = Field(..., description="Pregunta del usuario", min_length=3)
    limite: int = Field(5, description="Número de resultados a considerar", ge=1, le=20)
    filter_expediente: Optional[str] = Field(None, description="Filtrar por expediente")
    filter_tipo: Optional[str] = Field(None, description="Filtrar por tipo de actuación")
    # Parámetros de configuración opcionales
    model: Optional[str] = Field(None, description="Modelo LLM a usar (ej: gpt-oss:20b)")
    temperature: Optional[float] = Field(None, description="Temperature del LLM (0.0-1.0)", ge=0.0, le=1.0)
    dense_weight: Optional[float] = Field(None, description="Peso búsqueda vectorial (0.0-1.0)", ge=0.0, le=1.0)
    sparse_weight: Optional[float] = Field(None, description="Peso búsqueda BM25 (0.0-1.0)", ge=0.0, le=1.0)


class SearchOnlyRequest(BaseModel):
    """Request para búsqueda sin LLM"""
    texto: str = Field(..., description="Texto a buscar", min_length=1)
    limite: int = Field(10, description="Número de resultados", ge=1, le=50)
    use_dense: bool = Field(True, description="Usar búsqueda vectorial")
    use_sparse: bool = Field(True, description="Usar búsqueda BM25")
    filter_expediente: Optional[str] = Field(None, description="Filtrar por expediente")
    filter_tipo: Optional[str] = Field(None, description="Filtrar por tipo")
    # Parámetros de configuración opcionales
    dense_weight: Optional[float] = Field(None, description="Peso búsqueda vectorial (0.0-1.0)", ge=0.0, le=1.0)
    sparse_weight: Optional[float] = Field(None, description="Peso búsqueda BM25 (0.0-1.0)", ge=0.0, le=1.0)


class IndexarExpedienteRequest(BaseModel):
    """Request para indexar expediente manualmente"""
    expediente_numero: str = Field(..., description="Número del expediente")
    ruta_json: Optional[str] = Field(None, description="Ruta al JSON (opcional)")
    force: bool = Field(False, description="Forzar reindexación")


class ReindexarRequest(BaseModel):
    """Request para reindexación masiva"""
    directorio_base: Optional[str] = Field(None, description="Directorio base de expedientes")
    limite: Optional[int] = Field(None, description="Límite de expedientes a procesar")
    limpiar: bool = Field(False, description="Limpiar índices antes de reindexar")


class SearchResultResponse(BaseModel):
    """Response de un resultado de búsqueda"""
    expediente_numero: str
    chunk_type: str
    score: float
    rank: int
    texto: str
    highlights: List[str]
    metadata: Dict[str, Any]


class RAGQueryResponse(BaseModel):
    """Response de query RAG completo"""
    pregunta: str
    respuesta: str
    resultados: List[SearchResultResponse]
    metadata: Dict[str, Any]


class SearchOnlyResponse(BaseModel):
    """Response de búsqueda sin LLM"""
    resultados: List[SearchResultResponse]
    total: int


class IndexacionResponse(BaseModel):
    """Response de indexación"""
    success: bool
    expediente: str
    actuaciones_procesadas: Optional[int] = None
    documentos_creados: Optional[int] = None
    chunks_indexados: Optional[int] = None
    error: Optional[str] = None
    timestamp: Optional[str] = None


class StatsResponse(BaseModel):
    """Response de estadísticas"""
    qdrant: Dict[str, Any]
    bm25: Dict[str, Any]
    weights: Dict[str, Any]


class HealthCheckResponse(BaseModel):
    """Response de health check"""
    qdrant: bool
    ollama: bool
    bm25: bool
    overall: bool


class ModelsResponse(BaseModel):
    """Response de modelos disponibles"""
    models: List[str]
    current: str


class ConfigResponse(BaseModel):
    """Response de configuración actual"""
    model: str
    temperature: float
    dense_weight: float
    sparse_weight: float
    search_limit: int
    rerank_top_k: int


# ==============================================================================
# Dependencias
# ==============================================================================

def get_rag_indexer() -> RAGIndexer:
    """Dependency para obtener RAGIndexer"""
    return RAGIndexer()


def get_rag_service(indexer: RAGIndexer = Depends(get_rag_indexer)) -> RAGService:
    """Dependency para obtener RAGService"""
    return RAGService(hybrid_search_service=indexer.search_service)


# ==============================================================================
# Endpoints
# ==============================================================================

@router.post("/query", response_model=RAGQueryResponse)
async def query_rag(
    request: RAGQueryRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Query completo RAG: búsqueda híbrida + generación de respuesta con LLM

    Proceso:
    1. Búsqueda híbrida (dense + sparse) en índices
    2. Fusión y reranking de resultados
    3. Generación de respuesta contextual con LLM

    Returns:
        Respuesta generada por el LLM basada en chunks relevantes
    """
    try:
        logger.info(f"RAG Query: '{request.pregunta}'")

        # Ejecutar RAG completo con parámetros dinámicos
        rag_response = rag_service.query(
            question=request.pregunta,
            limit=request.limite,
            filter_expediente=request.filter_expediente,
            filter_tipo=request.filter_tipo,
            model=request.model,
            temperature=request.temperature,
            dense_weight=request.dense_weight,
            sparse_weight=request.sparse_weight
        )

        # Convertir resultados
        resultados_response = [
            SearchResultResponse(
                expediente_numero=res.chunk.metadata.get("expediente_numero", "N/A"),
                chunk_type=res.chunk.chunk_type.value,
                score=res.score,
                rank=res.rank,
                texto=res.chunk.texto,
                highlights=res.highlights,
                metadata=res.chunk.metadata
            )
            for res in rag_response.resultados
        ]

        return RAGQueryResponse(
            pregunta=rag_response.pregunta,
            respuesta=rag_response.respuesta,
            resultados=resultados_response,
            metadata=rag_response.metadata
        )

    except Exception as e:
        logger.error(f"Error en RAG query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error procesando query: {str(e)}")


@router.post("/search", response_model=SearchOnlyResponse)
async def search_only(
    request: SearchOnlyRequest,
    indexer: RAGIndexer = Depends(get_rag_indexer)
):
    """
    Búsqueda híbrida sin generación de respuesta LLM

    Útil para:
    - Explorar documentos relevantes
    - Debug de búsqueda
    - UI de búsqueda rápida

    Returns:
        Lista de chunks relevantes con scores
    """
    try:
        logger.info(f"Search only: '{request.texto}'")

        # Crear query
        query = SearchQuery(
            texto=request.texto,
            limit=request.limite,
            filter_expediente=request.filter_expediente,
            filter_tipo=request.filter_tipo
        )

        # Ejecutar búsqueda
        resultados = indexer.search_service.search(
            query,
            use_dense=request.use_dense,
            use_sparse=request.use_sparse
        )

        # Convertir resultados
        resultados_response = [
            SearchResultResponse(
                expediente_numero=res.chunk.metadata.get("expediente_numero", "N/A"),
                chunk_type=res.chunk.chunk_type.value,
                score=res.score,
                rank=res.rank,
                texto=res.chunk.texto,
                highlights=res.highlights,
                metadata=res.chunk.metadata
            )
            for res in resultados
        ]

        return SearchOnlyResponse(
            resultados=resultados_response,
            total=len(resultados_response)
        )

    except Exception as e:
        logger.error(f"Error en búsqueda: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error en búsqueda: {str(e)}")


@router.post("/indexar", response_model=IndexacionResponse)
async def indexar_expediente(
    request: IndexarExpedienteRequest,
    indexer: RAGIndexer = Depends(get_rag_indexer)
):
    """
    Indexar un expediente específico manualmente

    Útil para:
    - Reindexar expediente después de actualización
    - Forzar indexación de expediente que falló
    - Testing

    Returns:
        Resultado de la indexación
    """
    try:
        logger.info(f"Indexando expediente: {request.expediente_numero}")

        # Determinar ruta del JSON
        if request.ruta_json:
            ruta_json = Path(request.ruta_json)
        else:
            # Buscar JSON en directorio estándar
            directorio_base = Path(__file__).parent.parent.parent.parent.parent / "data" / "actuaciones"
            numero_normalizado = request.expediente_numero.replace("/", "_")
            ruta_json = directorio_base / numero_normalizado / "json" / f"actuaciones-{numero_normalizado}.json"

        if not ruta_json.exists():
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró JSON para expediente {request.expediente_numero}"
            )

        # Indexar
        resultado = indexer.indexar_expediente(
            ruta_json=ruta_json,
            expediente_numero=request.expediente_numero,
            force=request.force
        )

        return IndexacionResponse(**resultado)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error indexando expediente: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error indexando expediente: {str(e)}")


@router.post("/reindexar")
async def reindexar_todos(
    request: ReindexarRequest,
    background_tasks: BackgroundTasks,
    indexer: RAGIndexer = Depends(get_rag_indexer)
):
    """
    Reindexar todos los expedientes (operación en background)

    Esta operación puede tomar tiempo dependiendo del número de expedientes.
    Se ejecuta en background y retorna inmediatamente.

    Returns:
        Confirmación de inicio de reindexación
    """
    try:
        logger.info("Iniciando reindexación masiva...")

        # Determinar directorio base
        if request.directorio_base:
            directorio_base = Path(request.directorio_base)
        else:
            directorio_base = Path(__file__).parent.parent.parent.parent.parent / "data" / "actuaciones"

        # Limpiar índices si se solicitó
        if request.limpiar:
            logger.info("Limpiando índices...")
            indexer.search_service.qdrant.clear_collection()
            indexer.search_service.bm25.clear_index()

        # Ejecutar reindexación en background
        def reindexar_background():
            indexer.reindexar_todos_expedientes(
                directorio_base=directorio_base,
                limite=request.limite
            )

        background_tasks.add_task(reindexar_background)

        return {
            "status": "iniciado",
            "mensaje": "Reindexación iniciada en background",
            "directorio": str(directorio_base),
            "limite": request.limite,
            "limpiar": request.limpiar
        }

    except Exception as e:
        logger.error(f"Error iniciando reindexación: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error iniciando reindexación: {str(e)}")


@router.get("/stats", response_model=StatsResponse)
async def get_stats(indexer: RAGIndexer = Depends(get_rag_indexer)):
    """
    Obtener estadísticas de los índices

    Returns:
        Estadísticas de Qdrant, BM25 y configuración
    """
    try:
        stats = indexer.get_stats()
        return StatsResponse(**stats)

    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    indexer: RAGIndexer = Depends(get_rag_indexer),
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Health check de servicios RAG

    Verifica:
    - Qdrant está disponible
    - Ollama está disponible
    - Índice BM25 existe

    Returns:
        Estado de cada servicio
    """
    try:
        # Verificar Qdrant
        qdrant_ok = indexer.search_service.qdrant.health_check()

        # Verificar Ollama
        ollama_ok = rag_service.llm.health_check()

        # Verificar BM25
        bm25_ok = indexer.search_service.bm25.bm25 is not None

        overall = qdrant_ok and bm25_ok  # Ollama es opcional

        return HealthCheckResponse(
            qdrant=qdrant_ok,
            ollama=ollama_ok,
            bm25=bm25_ok,
            overall=overall
        )

    except Exception as e:
        logger.error(f"Error en health check: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error en health check: {str(e)}")


@router.get("/models", response_model=ModelsResponse)
async def list_models(rag_service: RAGService = Depends(get_rag_service)):
    """
    Listar modelos LLM disponibles en Ollama

    Returns:
        Lista de modelos disponibles y modelo actual configurado
    """
    try:
        models = rag_service.llm.list_models()
        current_model = rag_service.llm.model

        return ModelsResponse(
            models=models,
            current=current_model
        )

    except Exception as e:
        logger.error(f"Error listando modelos: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listando modelos: {str(e)}")


@router.get("/config", response_model=ConfigResponse)
async def get_config(
    indexer: RAGIndexer = Depends(get_rag_indexer),
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Obtener configuración actual del sistema RAG

    Returns:
        Configuración actual del sistema
    """
    try:
        from infrastructure.rag.config import get_rag_settings
        settings = get_rag_settings()

        return ConfigResponse(
            model=rag_service.llm.model,
            temperature=rag_service.llm.temperature,
            dense_weight=indexer.search_service.dense_weight,
            sparse_weight=indexer.search_service.sparse_weight,
            search_limit=settings.search_limit,
            rerank_top_k=settings.rerank_top_k
        )

    except Exception as e:
        logger.error(f"Error obteniendo configuración: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error obteniendo configuración: {str(e)}")
