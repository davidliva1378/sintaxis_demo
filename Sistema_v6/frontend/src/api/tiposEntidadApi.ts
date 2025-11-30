/**
 * API client para endpoints de Tipos de Entidad
 */

const API_BASE_URL = import.meta.env.VITE_API_URL

// ============================================================================
// Types
// ============================================================================

export interface TipoEntidad {
  id: number
  nombre: string
  descripcion: string | null
  color: string
  es_predefinido: boolean
  activo: boolean
}

export interface TiposEntidadListResponse {
  total: number
  tipos: TipoEntidad[]
}

export interface CrearTipoEntidadRequest {
  nombre: string
  descripcion?: string
  color?: string
}

export interface ActualizarTipoEntidadRequest {
  descripcion?: string
  color?: string
  activo?: boolean
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Obtiene todos los tipos de entidad
 */
export async function obtenerTiposEntidadCompletos(
  soloActivos: boolean = true,
  incluirPredefinidos: boolean = true
): Promise<TiposEntidadListResponse> {
  const params = new URLSearchParams()
  params.append('solo_activos', String(soloActivos))
  params.append('incluir_predefinidos', String(incluirPredefinidos))

  const response = await fetch(
    `${API_BASE_URL}/api/v1/tipos-entidad?${params.toString()}`
  )

  if (!response.ok) {
    throw new Error(`Error ${response.status}: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Obtiene un tipo de entidad por ID
 */
export async function obtenerTipoEntidad(tipoId: number): Promise<TipoEntidad> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/tipos-entidad/${tipoId}`
  )

  if (!response.ok) {
    throw new Error(`Error ${response.status}: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Crea un nuevo tipo de entidad
 */
export async function crearTipoEntidad(
  tipo: CrearTipoEntidadRequest
): Promise<TipoEntidad> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/tipos-entidad`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(tipo),
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || `Error ${response.status}`)
  }

  return response.json()
}

/**
 * Actualiza un tipo de entidad
 */
export async function actualizarTipoEntidad(
  tipoId: number,
  datos: ActualizarTipoEntidadRequest
): Promise<TipoEntidad> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/tipos-entidad/${tipoId}`,
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
 * Elimina un tipo de entidad
 */
export async function eliminarTipoEntidad(
  tipoId: number
): Promise<{ message: string }> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/tipos-entidad/${tipoId}`,
    {
      method: 'DELETE',
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || `Error ${response.status}`)
  }

  return response.json()
}

/**
 * Activa/desactiva un tipo de entidad
 */
export async function toggleTipoEntidad(
  tipoId: number
): Promise<{ message: string; activo: boolean }> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/tipos-entidad/${tipoId}/toggle`,
    {
      method: 'POST',
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || `Error ${response.status}`)
  }

  return response.json()
}
