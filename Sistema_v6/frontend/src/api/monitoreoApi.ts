/**
 * API Client para Monitoreo de Expedientes
 *
 * Conecta con los endpoints de monitoreo del backend:
 * - GET /api/v1/monitoreo/estado - Estado del scheduler
 * - POST /api/v1/monitoreo/start - Iniciar scheduler
 * - POST /api/v1/monitoreo/stop - Detener scheduler
 * - POST /api/v1/monitoreo/verificar - Verificación manual
 * - GET/PUT /api/v1/monitoreo/configuracion - Configuración
 * - GET/POST/PUT/DELETE /api/v1/monitoreo/expedientes - Expedientes
 * - GET /api/v1/monitoreo/cambios - Cambios detectados
 * - GET /api/v1/monitoreo/estadisticas - Estadísticas
 */

import type {
  ConfiguracionMonitoreo,
  ExpedienteMonitoreado,
  CambioDetectado,
  EstadisticasMonitoreo,
  SolicitudMonitorear,
  ActualizarMonitoreo,
} from '../types/monitoreo'

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

// ============================================================================
// NUEVAS FUNCIONES DE API CRUD
// ============================================================================

// --- CONFIGURACION ---

/**
 * Obtiene la configuración de monitoreo del usuario
 */
export async function obtenerConfiguracion(): Promise<ConfiguracionMonitoreo> {
  const response = await fetch(`${API_BASE_URL}/api/v1/monitoreo/configuracion`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

/**
 * Actualiza la configuración de monitoreo
 */
export async function actualizarConfiguracion(config: ActualizarMonitoreo): Promise<ConfiguracionMonitoreo> {
  const response = await fetch(`${API_BASE_URL}/api/v1/monitoreo/configuracion`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

// --- EXPEDIENTES MONITOREADOS ---

export interface ListaExpedientesResponse {
  expedientes: ExpedienteMonitoreado[]
  total: number
  pagina: number
  por_pagina: number
  total_paginas: number
}

/**
 * Lista los expedientes monitoreados
 */
export async function listarExpedientes(
  soloActivos = false,
  pagina = 1,
  porPagina = 50
): Promise<ListaExpedientesResponse> {
  const params = new URLSearchParams({
    solo_activos: String(soloActivos),
    pagina: String(pagina),
    por_pagina: String(porPagina),
  })

  const response = await fetch(`${API_BASE_URL}/api/v1/monitoreo/expedientes?${params}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

/**
 * Agrega un expediente al monitoreo
 */
export async function agregarExpediente(solicitud: SolicitudMonitorear): Promise<ExpedienteMonitoreado> {
  const response = await fetch(`${API_BASE_URL}/api/v1/monitoreo/expedientes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(solicitud),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

/**
 * Obtiene un expediente monitoreado específico
 */
export async function obtenerExpediente(expedienteNumero: string): Promise<ExpedienteMonitoreado> {
  const response = await fetch(`${API_BASE_URL}/api/v1/monitoreo/expedientes/${encodeURIComponent(expedienteNumero)}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

/**
 * Actualiza un expediente monitoreado
 */
export async function actualizarExpediente(
  expedienteNumero: string,
  datos: { activo?: boolean; prioridad?: string; notas?: string }
): Promise<ExpedienteMonitoreado> {
  const response = await fetch(`${API_BASE_URL}/api/v1/monitoreo/expedientes/${encodeURIComponent(expedienteNumero)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(datos),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

/**
 * Elimina un expediente del monitoreo
 */
export async function eliminarExpediente(expedienteNumero: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/monitoreo/expedientes/${encodeURIComponent(expedienteNumero)}`, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
}

/**
 * Pausa el monitoreo de un expediente
 */
export async function pausarExpediente(expedienteNumero: string): Promise<ExpedienteMonitoreado> {
  const response = await fetch(`${API_BASE_URL}/api/v1/monitoreo/expedientes/${encodeURIComponent(expedienteNumero)}/pausar`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

/**
 * Reanuda el monitoreo de un expediente
 */
export async function reanudarExpediente(expedienteNumero: string): Promise<ExpedienteMonitoreado> {
  const response = await fetch(`${API_BASE_URL}/api/v1/monitoreo/expedientes/${encodeURIComponent(expedienteNumero)}/reanudar`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

// --- CAMBIOS DETECTADOS ---

export interface ListaCambiosResponse {
  cambios: CambioDetectado[]
  total_no_leidos: number
  pagina: number
  por_pagina: number
}

/**
 * Lista los cambios detectados
 */
export async function listarCambios(
  soloNoLeidos = false,
  tipoCambio?: string,
  expedienteNumero?: string,
  pagina = 1,
  porPagina = 50
): Promise<ListaCambiosResponse> {
  const params = new URLSearchParams({
    solo_no_leidos: String(soloNoLeidos),
    pagina: String(pagina),
    por_pagina: String(porPagina),
  })

  if (tipoCambio) params.set('tipo_cambio', tipoCambio)
  if (expedienteNumero) params.set('expediente_numero', expedienteNumero)

  const response = await fetch(`${API_BASE_URL}/api/v1/monitoreo/cambios?${params}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

/**
 * Marca un cambio como leído
 */
export async function marcarLeido(cambioId: number): Promise<{ success: boolean; cantidad_marcados: number }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/monitoreo/cambios/${cambioId}/marcar-leido`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

/**
 * Marca todos los cambios como leídos
 */
export async function marcarTodosLeidos(): Promise<{ success: boolean; cantidad_marcados: number }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/monitoreo/cambios/marcar-todos-leidos`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

// --- ESTADISTICAS ---

/**
 * Obtiene estadísticas del monitoreo
 */
export async function obtenerEstadisticas(): Promise<EstadisticasMonitoreo> {
  const response = await fetch(`${API_BASE_URL}/api/v1/monitoreo/estadisticas`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

// --- SINCRONIZACION ---

export interface SincronizarResponse {
  success: boolean
  mensaje: string
  total_sistema: number
  nuevos_monitoreados: number
  ya_monitoreados: number
  errores?: string[]
}

/**
 * Sincroniza todos los expedientes del sistema principal con el monitoreo
 */
export async function sincronizarExpedientes(): Promise<SincronizarResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/monitoreo/sincronizar`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}
