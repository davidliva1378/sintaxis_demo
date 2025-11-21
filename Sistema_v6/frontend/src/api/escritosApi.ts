/**
 * API client para endpoints de Escritos
 */

import type {
  Escrito,
  EscritoCreate,
  EscritoUpdate,
  Plantilla,
  PlantillaCreate,
  PlantillaUpdate,
  EstadisticasEscritos,
  VersionEscrito,
  FiltrosEscritos
} from '@/types/escritos'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('access_token')
  return {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
  }
}

// === Plantillas ===

/**
 * Lista plantillas disponibles
 */
export async function listarPlantillas(categoria?: string, incluirPublicas: boolean = true): Promise<Plantilla[]> {
  const params = new URLSearchParams()
  if (categoria) params.append('categoria', categoria)
  params.append('incluir_publicas', String(incluirPublicas))

  const url = `${API_BASE_URL}/api/v1/escritos/plantillas?${params.toString()}`

  const response = await fetch(url, {
    method: 'GET',
    headers: getAuthHeaders()
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error al listar plantillas' }))
    throw new Error(error.detail || `Error ${response.status}`)
  }

  return response.json()
}

/**
 * Obtiene una plantilla por ID
 */
export async function obtenerPlantilla(plantillaId: number): Promise<Plantilla> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/escritos/plantillas/${plantillaId}`,
    {
      method: 'GET',
      headers: getAuthHeaders()
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error al obtener plantilla' }))
    throw new Error(error.detail || `Error ${response.status}`)
  }

  return response.json()
}

/**
 * Crea una nueva plantilla
 */
export async function crearPlantilla(data: PlantillaCreate): Promise<Plantilla> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/escritos/plantillas`,
    {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data)
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error al crear plantilla' }))
    throw new Error(error.detail || `Error ${response.status}`)
  }

  return response.json()
}

/**
 * Actualiza una plantilla
 */
export async function actualizarPlantilla(plantillaId: number, data: PlantillaUpdate): Promise<Plantilla> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/escritos/plantillas/${plantillaId}`,
    {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(data)
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error al actualizar plantilla' }))
    throw new Error(error.detail || `Error ${response.status}`)
  }

  return response.json()
}

/**
 * Elimina una plantilla
 */
export async function eliminarPlantilla(plantillaId: number): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/escritos/plantillas/${plantillaId}`,
    {
      method: 'DELETE',
      headers: getAuthHeaders()
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error al eliminar plantilla' }))
    throw new Error(error.detail || `Error ${response.status}`)
  }
}

// === Escritos ===

/**
 * Lista escritos con filtros opcionales
 */
export async function listarEscritos(filtros?: FiltrosEscritos): Promise<Escrito[]> {
  const params = new URLSearchParams()

  if (filtros?.expediente) params.append('expediente', filtros.expediente)
  if (filtros?.estado) params.append('estado', filtros.estado)
  if (filtros?.limit) params.append('limit', String(filtros.limit))
  if (filtros?.offset) params.append('offset', String(filtros.offset))

  const url = `${API_BASE_URL}/api/v1/escritos${params.toString() ? '?' + params.toString() : ''}`

  const response = await fetch(url, {
    method: 'GET',
    headers: getAuthHeaders()
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error al listar escritos' }))
    throw new Error(error.detail || `Error ${response.status}`)
  }

  return response.json()
}

/**
 * Obtiene estadisticas de escritos
 */
export async function obtenerEstadisticas(): Promise<EstadisticasEscritos> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/escritos/estadisticas`,
    {
      method: 'GET',
      headers: getAuthHeaders()
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error al obtener estadisticas' }))
    throw new Error(error.detail || `Error ${response.status}`)
  }

  return response.json()
}

/**
 * Obtiene un escrito por ID
 */
export async function obtenerEscrito(escritoId: number): Promise<Escrito> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/escritos/${escritoId}`,
    {
      method: 'GET',
      headers: getAuthHeaders()
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error al obtener escrito' }))
    throw new Error(error.detail || `Error ${response.status}`)
  }

  return response.json()
}

/**
 * Crea un nuevo escrito
 */
export async function crearEscrito(data: EscritoCreate): Promise<Escrito> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/escritos`,
    {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data)
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error al crear escrito' }))
    throw new Error(error.detail || `Error ${response.status}`)
  }

  return response.json()
}

/**
 * Actualiza un escrito
 */
export async function actualizarEscrito(escritoId: number, data: EscritoUpdate): Promise<Escrito> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/escritos/${escritoId}`,
    {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(data)
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error al actualizar escrito' }))
    throw new Error(error.detail || `Error ${response.status}`)
  }

  return response.json()
}

/**
 * Elimina un escrito
 */
export async function eliminarEscrito(escritoId: number): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/escritos/${escritoId}`,
    {
      method: 'DELETE',
      headers: getAuthHeaders()
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error al eliminar escrito' }))
    throw new Error(error.detail || `Error ${response.status}`)
  }
}

/**
 * Marca un escrito como presentado
 */
export async function marcarPresentado(escritoId: number, numeroEscrito?: string): Promise<Escrito> {
  const params = numeroEscrito ? `?numero_escrito=${encodeURIComponent(numeroEscrito)}` : ''

  const response = await fetch(
    `${API_BASE_URL}/api/v1/escritos/${escritoId}/presentar${params}`,
    {
      method: 'POST',
      headers: getAuthHeaders()
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error al marcar como presentado' }))
    throw new Error(error.detail || `Error ${response.status}`)
  }

  return response.json()
}

/**
 * Confirma la presentacion de un escrito
 */
export async function confirmarPresentacion(escritoId: number): Promise<Escrito> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/escritos/${escritoId}/confirmar`,
    {
      method: 'POST',
      headers: getAuthHeaders()
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error al confirmar presentacion' }))
    throw new Error(error.detail || `Error ${response.status}`)
  }

  return response.json()
}

/**
 * Lista versiones de un escrito
 */
export async function listarVersiones(escritoId: number): Promise<VersionEscrito[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/escritos/${escritoId}/versiones`,
    {
      method: 'GET',
      headers: getAuthHeaders()
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error al listar versiones' }))
    throw new Error(error.detail || `Error ${response.status}`)
  }

  return response.json()
}

/**
 * Obtiene una version especifica
 */
export async function obtenerVersion(escritoId: number, versionId: number): Promise<VersionEscrito> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/escritos/${escritoId}/versiones/${versionId}`,
    {
      method: 'GET',
      headers: getAuthHeaders()
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error al obtener version' }))
    throw new Error(error.detail || `Error ${response.status}`)
  }

  return response.json()
}
