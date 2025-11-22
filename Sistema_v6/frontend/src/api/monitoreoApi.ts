/**
 * API Client para Monitoreo de Expedientes
 *
 * Conecta con los endpoints de monitoreo del backend:
 * - GET /api/v1/monitoreo/estado - Estado del scheduler
 * - POST /api/v1/monitoreo/start - Iniciar scheduler
 * - POST /api/v1/monitoreo/stop - Detener scheduler
 * - POST /api/v1/monitoreo/verificar - Verificación manual
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// ============================================================================
// Tipos de respuesta (según schemas de backend)
// ============================================================================

export interface EstadoMonitoreoResponse {
  activo: boolean
  ejecutando: boolean
  intervalo_actual_minutos: number | null
  es_horario_laboral: boolean
  proxima_ejecucion: string | null
  jobs_programados: number
}

export interface StartSchedulerResponse {
  success: boolean
  mensaje: string
  intervalo_minutos: number | null
}

export interface StopSchedulerResponse {
  success: boolean
  mensaje: string
}

export interface CambioDetectadoResponse {
  numero_expediente: string
  tipo_cambio: string
  descripcion: string
  fecha_deteccion: string
}

export interface VerificacionManualResponse {
  success: boolean
  total_expedientes: number
  cambios_detectados: number
  cambios: CambioDetectadoResponse[]
  error?: string
}

// ============================================================================
// Funciones de API
// ============================================================================

/**
 * Obtiene el estado actual del scheduler de monitoreo
 */
export async function obtenerEstadoMonitoreo(): Promise<EstadoMonitoreoResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/monitoreo/estado`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

/**
 * Inicia el scheduler de monitoreo continuo
 */
export async function iniciarScheduler(): Promise<StartSchedulerResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/monitoreo/start`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

/**
 * Detiene el scheduler de monitoreo continuo
 */
export async function detenerScheduler(): Promise<StopSchedulerResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/monitoreo/stop`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

/**
 * Ejecuta una verificación manual inmediata (sin afectar el scheduler)
 */
export async function verificarManual(): Promise<VerificacionManualResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/monitoreo/verificar`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

// ============================================================================
// Helper: Mapeo de tipos del backend al frontend
// ============================================================================

/**
 * Mapea el tipo de cambio del backend al tipo esperado por el frontend
 */
export function mapearTipoCambio(tipoBackend: string): string {
  const mapeo: Record<string, string> = {
    nueva_actuacion: 'nueva_actuacion',
    cambio_situacion: 'cambio_estado',
    cambio_dependencia: 'cambio_dependencia',
    cambio_caratula: 'cambio_caratula',
    multiples_cambios: 'multiples_cambios',
  }

  return mapeo[tipoBackend] || tipoBackend
}

/**
 * Formatea la próxima ejecución para mostrar en UI
 */
export function formatearProximaEjecucion(isoString: string | null): string {
  if (!isoString) return 'No programada'

  const fecha = new Date(isoString)
  const ahora = new Date()
  const diffMs = fecha.getTime() - ahora.getTime()
  const diffMinutos = Math.floor(diffMs / 60000)

  if (diffMinutos < 1) return 'Próximamente'
  if (diffMinutos < 60) return `En ${diffMinutos} minuto${diffMinutos > 1 ? 's' : ''}`

  const diffHoras = Math.floor(diffMinutos / 60)
  return `En ${diffHoras} hora${diffHoras > 1 ? 's' : ''}`
}

/**
 * Obtiene el texto descriptivo del intervalo
 */
export function obtenerDescripcionIntervalo(minutos: number | null): string {
  if (!minutos) return 'No configurado'

  if (minutos < 60) return `Cada ${minutos} minutos`

  const horas = Math.floor(minutos / 60)
  return `Cada ${horas} hora${horas > 1 ? 's' : ''}`
}
