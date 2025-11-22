/**
 * API client para servicios de IA
 */

import { apiClient } from './client'

// === Tipos ===

export interface ClasificarRequest {
  texto: string
  contexto?: string
  usar_llm?: boolean
}

export interface ClasificarResponse {
  tipo: string
  confianza: number
  justificacion: string
  metodo?: string
}

export interface NERRequest {
  texto: string
  labels?: string[]
}

export interface Entidad {
  text: string
  label: string
  score: number
  start: number
  end: number
}

export interface BuscarRequest {
  query: string
  n_results?: number
  expediente_id?: string
  expediente_numero?: string
}

export interface BuscarHibridoRequest {
  query: string
  n_results?: number
  expediente_id?: string
  expediente_numero?: string
  use_bm25?: boolean
  use_semantic?: boolean
}

export interface ResultadoBusqueda {
  id: string
  document: string
  metadata: Record<string, unknown>
  score: number
  hybrid_score?: number
}

export interface PreguntarRequest {
  pregunta: string
  n_contextos?: number
  expediente_id?: string
}

export interface PreguntarResponse {
  respuesta: string
  confianza: number
  fuentes: Array<{
    id: string
    fragmento: string
    score: number
  }>
}

export interface MensajeChat {
  rol: 'usuario' | 'asistente'
  contenido: string
}

export interface ChatRequest {
  mensaje: string
  expediente_numero?: string
  historial?: MensajeChat[]
  n_contextos?: number
}

export interface ChatResponse {
  respuesta: string
  fuentes: Array<{
    id: string
    fragmento: string
    score: number
    expediente: string
  }>
}

export interface GenerarRequest {
  prompt: string
  system?: string
  temperature?: number
  max_tokens?: number
}

export interface TipoActuacion {
  tipo: string
  descripcion: string
}

export interface IAStatus {
  clasificador: string
  ner: string
  rag: string
  llm: string
}

// === Clasificación ===

export async function clasificarActuacion(request: ClasificarRequest): Promise<ClasificarResponse> {
  const response = await apiClient.post<ClasificarResponse>('/api/v1/ia/clasificar', request)
  return response.data
}

export async function getTiposActuacion(): Promise<TipoActuacion[]> {
  const response = await apiClient.get<{ tipos: TipoActuacion[] }>('/api/v1/ia/tipos-actuacion')
  return response.data.tipos
}

// === NER ===

export async function extraerEntidades(request: NERRequest): Promise<Entidad[]> {
  const response = await apiClient.post<{ entidades: Entidad[] }>('/api/v1/ia/ner/extraer', request)
  return response.data.entidades
}

export async function extraerEntidadesJuridicas(texto: string): Promise<Record<string, string[]>> {
  const response = await apiClient.post<{ entidades: Record<string, string[]> }>('/api/v1/ia/ner/juridico', { texto })
  return response.data.entidades
}

export async function extraerPartes(texto: string): Promise<{
  actora: string[]
  demandada: string[]
  otros: string[]
}> {
  const response = await apiClient.post('/api/v1/ia/ner/partes', { texto })
  return response.data
}

// === RAG ===

export async function buscarSemantico(request: BuscarRequest): Promise<ResultadoBusqueda[]> {
  const response = await apiClient.post<{ resultados: ResultadoBusqueda[] }>('/api/v1/ia/rag/buscar', request)
  return response.data.resultados
}

/**
 * Búsqueda híbrida que combina BM25 (keywords) + Semántica (embeddings)
 * usando Reciprocal Rank Fusion (RRF) para mejores resultados.
 */
export async function buscarHibrido(request: BuscarHibridoRequest): Promise<ResultadoBusqueda[]> {
  const response = await apiClient.post<{ resultados: ResultadoBusqueda[] }>('/api/v1/ia/rag/buscar-hibrido', request)
  return response.data.resultados
}

export async function preguntar(request: PreguntarRequest): Promise<PreguntarResponse> {
  const response = await apiClient.post<PreguntarResponse>('/api/v1/ia/rag/preguntar', request)
  return response.data
}

export async function chatIA(request: ChatRequest): Promise<ChatResponse> {
  const response = await apiClient.post<ChatResponse>('/api/v1/ia/chat', request)
  return response.data
}

/**
 * Chat con streaming (SSE) - recibe tokens en tiempo real
 */
export async function chatIAStream(
  request: ChatRequest,
  onToken: (token: string) => void,
  onFuentes: (fuentes: ChatResponse['fuentes']) => void,
  onDone: () => void,
  onError: (error: string) => void
): Promise<void> {
  const token = localStorage.getItem('auth_token')
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  const response = await fetch(`${API_BASE_URL}/api/v1/ia/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    },
    body: JSON.stringify(request)
  })

  if (!response.ok) {
    throw new Error(`Error: ${response.status}`)
  }

  const reader = response.body?.getReader()
  if (!reader) {
    throw new Error('No se pudo obtener el reader del stream')
  }

  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()

      if (done) break

      buffer += decoder.decode(value, { stream: true })

      // Procesar líneas completas
      const lines = buffer.split('\n')
      buffer = lines.pop() || '' // Guardar línea incompleta

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))

            if (data.type === 'token') {
              onToken(data.data)
            } else if (data.type === 'fuentes') {
              onFuentes(data.data)
            } else if (data.type === 'done') {
              onDone()
            } else if (data.type === 'error') {
              onError(data.data)
            }
          } catch {
            // Ignorar líneas que no son JSON válido
          }
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}

export async function indexarActuacion(id: string, texto: string, metadata?: Record<string, unknown>): Promise<void> {
  await apiClient.post('/api/v1/ia/rag/indexar', { id, texto, metadata })
}

export async function getRAGStats(): Promise<{
  collection: string
  total_documents: number
}> {
  const response = await apiClient.get('/api/v1/ia/rag/stats')
  return response.data
}

export async function resumirExpediente(expedienteId: string, maxLength?: number): Promise<string> {
  const params = maxLength ? `?max_length=${maxLength}` : ''
  const response = await apiClient.get<{ resumen: string }>(`/ia/rag/resumir/${expedienteId}${params}`)
  return response.data.resumen
}

// === LLM ===

export async function generarTexto(request: GenerarRequest): Promise<string> {
  const response = await apiClient.post<{ texto: string }>('/api/v1/ia/llm/generar', request)
  return response.data.texto
}

export async function resumirTexto(texto: string, maxLength?: number): Promise<string> {
  const response = await apiClient.post<{ resumen: string }>('/api/v1/ia/llm/resumir', {
    texto,
    max_length: maxLength || 200
  })
  return response.data.resumen
}

// === Estado ===

export async function getIAStatus(): Promise<IAStatus> {
  const response = await apiClient.get<IAStatus>('/api/v1/ia/status')
  return response.data
}

export async function getModelos(): Promise<{ models: string[], current: string }> {
  const response = await apiClient.get<{ models: string[], current: string }>('/api/v1/ia/models')
  return response.data
}

export async function setModelo(model: string): Promise<{ success: boolean, message: string }> {
  const response = await apiClient.post<{ success: boolean, message: string }>('/api/v1/ia/models/set', { model })
  return response.data
}

export async function getModeloActual(): Promise<{ model: string, info: Record<string, unknown> }> {
  const response = await apiClient.get<{ model: string, info: Record<string, unknown> }>('/api/v1/ia/models/current')
  return response.data
}
