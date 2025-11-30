/**
 * API client para endpoints de Analisis de Usuario
 * Maneja notas, tags y destacados personales por actuacion
 */

const API_BASE_URL = import.meta.env.VITE_API_URL

// ============================================================================
// Types
// ============================================================================

export interface NotaActuacion {
  id: number
  expediente_numero: string
  actuacion_indice: number
  nota: string | null
  tags: string[]
  destacado: boolean
  oculto: boolean
  color: string | null
  created_at: string
  updated_at: string
}

export interface NotasExpediente {
  expediente_numero: string
  total_notas: number
  total_destacados: number
  notas: NotaActuacion[]
}

export interface NotaActuacionCreate {
  actuacion_indice: number
  nota?: string | null
  tags?: string[]
  destacado?: boolean
  oculto?: boolean
  color?: string | null
}

export interface NotaActuacionUpdate {
  nota?: string | null
  tags?: string[]
  destacado?: boolean
  oculto?: boolean
  color?: string | null
}

export interface DestacadoGlobal {
  id: number
  expediente_numero: string
  actuacion_indice: number
  nota: string | null
  tags: string[]
  color: string | null
  created_at: string
  updated_at: string
}

export interface DestacadosGlobalResponse {
  total_destacados: number
  expedientes: Record<string, DestacadoGlobal[]>
}

// ============================================================================
// Helpers
// ============================================================================

function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('access_token')
  return {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
  }
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Obtiene todas las notas del usuario para un expediente
 */
export async function obtenerNotasExpediente(
  numeroExpediente: string
): Promise<NotasExpediente> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/analisis/expediente/${encodeURIComponent(numeroExpediente)}/notas`,
    {
      method: 'GET',
      headers: getAuthHeaders()
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error al obtener notas' }))
    throw new Error(error.detail || `Error ${response.status}`)
  }

  return response.json()
}

/**
 * Crea o actualiza una nota para una actuacion
 */
export async function crearNotaActuacion(
  numeroExpediente: string,
  data: NotaActuacionCreate
): Promise<NotaActuacion> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/analisis/expediente/${encodeURIComponent(numeroExpediente)}/notas`,
    {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data)
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error al crear nota' }))
    throw new Error(error.detail || `Error ${response.status}`)
  }

  return response.json()
}

/**
 * Actualiza una nota existente
 */
export async function actualizarNotaActuacion(
  numeroExpediente: string,
  indice: number,
  data: NotaActuacionUpdate
): Promise<NotaActuacion> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/analisis/expediente/${encodeURIComponent(numeroExpediente)}/notas/${indice}`,
    {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(data)
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error al actualizar nota' }))
    throw new Error(error.detail || `Error ${response.status}`)
  }

  return response.json()
}

/**
 * Elimina una nota de actuacion
 */
export async function eliminarNotaActuacion(
  numeroExpediente: string,
  indice: number
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/analisis/expediente/${encodeURIComponent(numeroExpediente)}/notas/${indice}`,
    {
      method: 'DELETE',
      headers: getAuthHeaders()
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error al eliminar nota' }))
    throw new Error(error.detail || `Error ${response.status}`)
  }
}

/**
 * Alterna el estado destacado de una actuacion
 */
export async function toggleDestacado(
  numeroExpediente: string,
  indice: number
): Promise<{ actuacion_indice: number; destacado: boolean }> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/analisis/expediente/${encodeURIComponent(numeroExpediente)}/notas/${indice}/toggle-destacado`,
    {
      method: 'POST',
      headers: getAuthHeaders()
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error al cambiar destacado' }))
    throw new Error(error.detail || `Error ${response.status}`)
  }

  return response.json()
}

/**
 * Obtiene todos los destacados del usuario agrupados por expediente
 */
export async function obtenerDestacadosGlobal(): Promise<DestacadosGlobalResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/analisis/destacados`,
    {
      method: 'GET',
      headers: getAuthHeaders()
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error al obtener destacados' }))
    throw new Error(error.detail || `Error ${response.status}`)
  }

  return response.json()
}

/**
 * Exporta las notas de un expediente
 */
export async function exportarNotas(
  numeroExpediente: string,
  formato: 'json' | 'csv' = 'json'
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/analisis/expediente/${encodeURIComponent(numeroExpediente)}/exportar?formato=${formato}`,
    {
      method: 'GET',
      headers: getAuthHeaders()
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error al exportar notas' }))
    throw new Error(error.detail || `Error ${response.status}`)
  }

  // Descargar archivo
  const blob = await response.blob()
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `notas_${numeroExpediente}.${formato}`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  window.URL.revokeObjectURL(url)
}
