/**
 * API client para endpoints de Agenda
 */

import type {
  Evento,
  EventoCreate,
  EventoUpdate,
  ResumenAgenda,
  FiltrosAgenda
} from '@/types/agenda'

const API_BASE_URL = import.meta.env.VITE_API_URL

function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('access_token')
  return {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
  }
}

/**
 * Lista eventos con filtros opcionales
 */
export async function listarEventos(filtros?: FiltrosAgenda): Promise<Evento[]> {
  const params = new URLSearchParams()

  if (filtros?.fecha_desde) params.append('fecha_desde', filtros.fecha_desde)
  if (filtros?.fecha_hasta) params.append('fecha_hasta', filtros.fecha_hasta)
  if (filtros?.tipo) params.append('tipo', filtros.tipo)
  if (filtros?.estado) params.append('estado', filtros.estado)
  if (filtros?.expediente) params.append('expediente', filtros.expediente)

  const url = `${API_BASE_URL}/api/v1/agenda/eventos${params.toString() ? '?' + params.toString() : ''}`

  const response = await fetch(url, {
    method: 'GET',
    headers: getAuthHeaders()
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error al listar eventos' }))
    throw new Error(error.detail || `Error ${response.status}`)
  }

  return response.json()
}

/**
 * Obtiene un evento por ID
 */
export async function obtenerEvento(eventoId: number): Promise<Evento> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/agenda/eventos/${eventoId}`,
    {
      method: 'GET',
      headers: getAuthHeaders()
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error al obtener evento' }))
    throw new Error(error.detail || `Error ${response.status}`)
  }

  return response.json()
}

/**
 * Crea un nuevo evento
 */
export async function crearEvento(data: EventoCreate): Promise<Evento> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/agenda/eventos`,
    {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data)
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error al crear evento' }))
    throw new Error(error.detail || `Error ${response.status}`)
  }

  return response.json()
}

/**
 * Actualiza un evento existente
 */
export async function actualizarEvento(eventoId: number, data: EventoUpdate): Promise<Evento> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/agenda/eventos/${eventoId}`,
    {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(data)
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error al actualizar evento' }))
    throw new Error(error.detail || `Error ${response.status}`)
  }

  return response.json()
}

/**
 * Elimina un evento
 */
export async function eliminarEvento(eventoId: number): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/agenda/eventos/${eventoId}`,
    {
      method: 'DELETE',
      headers: getAuthHeaders()
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error al eliminar evento' }))
    throw new Error(error.detail || `Error ${response.status}`)
  }
}

/**
 * Obtiene resumen de agenda
 */
export async function obtenerResumen(): Promise<ResumenAgenda> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/agenda/resumen`,
    {
      method: 'GET',
      headers: getAuthHeaders()
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error al obtener resumen' }))
    throw new Error(error.detail || `Error ${response.status}`)
  }

  return response.json()
}

/**
 * Marca un evento como completado
 */
export async function completarEvento(eventoId: number): Promise<Evento> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/agenda/eventos/${eventoId}/completar`,
    {
      method: 'POST',
      headers: getAuthHeaders()
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error al completar evento' }))
    throw new Error(error.detail || `Error ${response.status}`)
  }

  return response.json()
}
