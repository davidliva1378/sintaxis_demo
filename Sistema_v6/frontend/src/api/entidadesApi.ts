/**
 * API client para endpoints de Entidades NER
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// ============================================================================
// Types
// ============================================================================

export interface Entidad {
  id: number
  expediente_numero: string
  actuacion_id: number | null
  entity_type: string
  entity_value: string
  score: number | null
  start_pos: number | null
  end_pos: number | null
  origen: 'ia' | 'manual'
  usuario_id: number | null
  notas: string | null
  fecha_creacion: string
  fecha_actualizacion: string
}

export interface EntidadesListResponse {
  expediente_numero: string
  total: number
  entidades: Entidad[]
}

export interface EstadisticasPorTipo {
  entity_type: string
  total: number
  por_ia: number
  manuales: number
  avg_score: number | null
}

export interface EstadisticasEntidadesResponse {
  expediente_numero: string
  total: number
  total_ia: number
  total_manual: number
  por_tipo: EstadisticasPorTipo[]
}

export interface TiposEntidadResponse {
  tipos: string[]
}

export interface CrearEntidadRequest {
  entity_type: string
  entity_value: string
  actuacion_id?: number
  notas?: string
}

export interface ActualizarEntidadRequest {
  entity_value?: string
  entity_type?: string
  notas?: string
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Obtiene las entidades de un expediente
 */
export async function obtenerEntidades(
  numeroExpediente: string,
  entityType?: string,
  origen?: string
): Promise<EntidadesListResponse> {
  const params = new URLSearchParams()
  if (entityType) params.append('entity_type', entityType)
  if (origen) params.append('origen', origen)

  const queryString = params.toString()
  const url = `${API_BASE_URL}/api/v1/expedientes/${encodeURIComponent(numeroExpediente)}/entidades${queryString ? `?${queryString}` : ''}`

  const response = await fetch(url)

  if (!response.ok) {
    throw new Error(`Error ${response.status}: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Obtiene estadisticas de entidades de un expediente
 */
export async function obtenerEstadisticasEntidades(
  numeroExpediente: string
): Promise<EstadisticasEntidadesResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/expedientes/${encodeURIComponent(numeroExpediente)}/entidades/estadisticas`
  )

  if (!response.ok) {
    throw new Error(`Error ${response.status}: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Obtiene los tipos de entidad disponibles
 */
export async function obtenerTiposEntidad(
  numeroExpediente: string
): Promise<TiposEntidadResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/expedientes/${encodeURIComponent(numeroExpediente)}/entidades/tipos`
  )

  if (!response.ok) {
    throw new Error(`Error ${response.status}: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Crea una nueva entidad
 */
export async function crearEntidad(
  numeroExpediente: string,
  entidad: CrearEntidadRequest
): Promise<{ id: number; message: string }> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/expedientes/${encodeURIComponent(numeroExpediente)}/entidades`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(entidad),
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || `Error ${response.status}`)
  }

  return response.json()
}

/**
 * Actualiza una entidad existente
 */
export async function actualizarEntidad(
  numeroExpediente: string,
  entidadId: number,
  datos: ActualizarEntidadRequest
): Promise<{ message: string }> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/expedientes/${encodeURIComponent(numeroExpediente)}/entidades/${entidadId}`,
    {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(datos),
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || `Error ${response.status}`)
  }

  return response.json()
}

/**
 * Elimina una entidad
 */
export async function eliminarEntidad(
  numeroExpediente: string,
  entidadId: number
): Promise<{ message: string }> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/expedientes/${encodeURIComponent(numeroExpediente)}/entidades/${entidadId}`,
    {
      method: 'DELETE',
    }
  )

  if (!response.ok) {
    throw new Error(`Error ${response.status}: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Elimina todas las entidades de un expediente
 */
export async function eliminarTodasEntidades(
  numeroExpediente: string,
  origen?: string
): Promise<{ message: string; count: number }> {
  const params = origen ? `?origen=${origen}` : ''

  const response = await fetch(
    `${API_BASE_URL}/api/v1/expedientes/${encodeURIComponent(numeroExpediente)}/entidades${params}`,
    {
      method: 'DELETE',
    }
  )

  if (!response.ok) {
    throw new Error(`Error ${response.status}: ${response.statusText}`)
  }

  return response.json()
}
