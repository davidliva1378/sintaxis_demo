/**
 * Tipos para el sistema RAG
 */

export interface SearchResult {
  expediente_numero: string
  chunk_type: string
  score: number
  rank: number
  texto: string
  highlights: string[]
  metadata: Record<string, any>
}

export interface RAGResponse {
  pregunta: string
  respuesta: string
  resultados: SearchResult[]
  metadata: Record<string, any>
}

export interface RAGStats {
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

export interface RAGHealth {
  qdrant: boolean
  ollama: boolean
  bm25: boolean
  overall: boolean
}

export interface RAGModels {
  models: string[]
  current: string
}

export interface RAGConfig {
  model: string
  temperature: number
  dense_weight: number
  sparse_weight: number
  search_limit: number
  rerank_top_k: number
}

export interface RAGQueryConfig {
  model?: string
  temperature?: number
  dense_weight?: number
  sparse_weight?: number
}
