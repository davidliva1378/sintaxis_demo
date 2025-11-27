/**
 * API client para sistema RAG (Retrieval-Augmented Generation)
 */

import { apiClient } from './client'

// === Tipos ===

export interface RAGQueryRequest {
  pregunta: string
  limite?: number
  filter_expediente?: string
  filter_tipo?: string
  // Parámetros de configuración opcionales
  model?: string
  temperature?: number
  dense_weight?: number
  sparse_weight?: number
}

export interface SearchOnlyRequest {
  texto: string
  limite?: number
  use_dense?: boolean
  use_sparse?: boolean
  filter_expediente?: string
  filter_tipo?: string
  // Parámetros de configuración opcionales
  dense_weight?: number
  sparse_weight?: number
}

export interface IndexarExpedienteRequest {
  expediente_numero: string
  ruta_json?: string
  force?: boolean
}

export interface ReindexarRequest {
  directorio_base?: string
  limite?: number
  limpiar?: boolean
}

export interface SearchResultResponse {
  expediente_numero: string
  chunk_type: string
  score: number
  rank: number
  texto: string
  highlights: string[]
  metadata: Record<string, any>
}

export interface RAGQueryResponse {
  pregunta: string
  respuesta: string
  resultados: SearchResultResponse[]
  metadata: Record<string, any>
}

export interface SearchOnlyResponse {
  resultados: SearchResultResponse[]
  total: number
}

export interface IndexacionResponse {
  success: boolean
  expediente: string
  actuaciones_procesadas?: number
  documentos_creados?: number
  chunks_indexados?: number
  error?: string
  timestamp?: string
}

export interface StatsResponse {
  qdrant: {
    collection: string
    count: number
  }
  bm25: {
    total_documents: number
    index_exists: boolean
    index_path: string
  }
  weights: {
    dense: number
    sparse: number
  }
}

export interface HealthCheckResponse {
  qdrant: boolean
  ollama: boolean
  bm25: boolean
  overall: boolean
}

export interface ModelsResponse {
  models: string[]
  current: string
}

export interface ConfigResponse {
  model: string
  temperature: number
  dense_weight: number
  sparse_weight: number
  search_limit: number
  rerank_top_k: number
}

// === API ===

/**
 * API para sistema RAG
 */
export const ragApi = {
  /**
   * Query RAG completo: búsqueda híbrida + generación de respuesta con LLM
   */
  async query(request: RAGQueryRequest): Promise<RAGQueryResponse> {
    const response = await apiClient.post<RAGQueryResponse>(
      '/api/v1/rag/query',
      request
    )
    return response.data
  },

  /**
   * Búsqueda híbrida sin generación de respuesta LLM
   */
  async search(request: SearchOnlyRequest): Promise<SearchOnlyResponse> {
    const response = await apiClient.post<SearchOnlyResponse>(
      '/api/v1/rag/search',
      request
    )
    return response.data
  },

  /**
   * Indexar un expediente específico manualmente
   */
  async indexar(request: IndexarExpedienteRequest): Promise<IndexacionResponse> {
    const response = await apiClient.post<IndexacionResponse>(
      '/api/v1/rag/indexar',
      request
    )
    return response.data
  },

  /**
   * Reindexar todos los expedientes (operación en background)
   */
  async reindexar(request: ReindexarRequest): Promise<{
    status: string
    mensaje: string
    directorio: string
    limite?: number
    limpiar: boolean
  }> {
    const response = await apiClient.post(
      '/api/v1/rag/reindexar',
      request
    )
    return response.data
  },

  /**
   * Obtener estadísticas de los índices
   */
  async getStats(): Promise<StatsResponse> {
    const response = await apiClient.get<StatsResponse>('/api/v1/rag/stats')
    return response.data
  },

  /**
   * Health check de servicios RAG
   */
  async healthCheck(): Promise<HealthCheckResponse> {
    const response = await apiClient.get<HealthCheckResponse>('/api/v1/rag/health')
    return response.data
  },

  /**
   * Listar modelos LLM disponibles en Ollama
   */
  async getModels(): Promise<ModelsResponse> {
    const response = await apiClient.get<ModelsResponse>('/api/v1/rag/models')
    return response.data
  },

  /**
   * Obtener configuración actual del sistema RAG
   */
  async getConfig(): Promise<ConfigResponse> {
    const response = await apiClient.get<ConfigResponse>('/api/v1/rag/config')
    return response.data
  },
}

/**
 * Genera un resumen ejecutivo del expediente usando RAG + LLM
 * @param expedienteNumero - Numero del expediente
 * @returns Promise con el resumen generado
 */
export async function generarResumenExpediente(expedienteNumero: string): Promise<string> {
  const pregunta = `Genera un resumen ejecutivo conciso del expediente ${expedienteNumero}.
Incluye: objeto del caso, partes involucradas, estado procesal actual, y aspectos clave a tener en cuenta.
El resumen debe ser claro, directo y en terminologia juridica apropiada.`

  const response = await ragApi.query({
    pregunta,
    limite: 10,
    filter_expediente: expedienteNumero,
    temperature: 0.3,  // Baja temperatura para mayor precision
  })

  return response.respuesta
}

export default ragApi
