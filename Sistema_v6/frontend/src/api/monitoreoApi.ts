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

import apiClient from './client'
import type {
  ConfiguracionMonitoreo,
  ExpedienteMonitoreado,
  CambioDetectado,
  EstadisticasMonitoreo,
  SolicitudMonitorear,
  ActualizarMonitoreo,
} from '../types/monitoreo'

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
  const response = await apiClient.get<EstadoMonitoreoResponse>('/api/v1/monitoreo/estado')
  return response.data
}

/**
 * Inicia el scheduler de monitoreo continuo
 */
export async function iniciarScheduler(): Promise<StartSchedulerResponse> {
  const response = await apiClient.post<StartSchedulerResponse>('/api/v1/monitoreo/start')
  return response.data
}

/**
 * Detiene el scheduler de monitoreo continuo
 */
export async function detenerScheduler(): Promise<StopSchedulerResponse> {
  const response = await apiClient.post<StopSchedulerResponse>('/api/v1/monitoreo/stop')
  return response.data
}

/**
 * Ejecuta una verificación manual inmediata (sin afectar el scheduler)
 */
export async function verificarManual(): Promise<VerificacionManualResponse> {
  const response = await apiClient.post<VerificacionManualResponse>('/api/v1/monitoreo/verificar')
  return response.data
}

// ============================================================================
// Helper: Mapeo de tipos del backend al frontend
// ============================================================================

/**
 * Mapea el tipo de cambio del backend al tipo esperado por el frontend
 * NOTA: Ahora frontend y backend usan los mismos tipos
 */
export function mapearTipoCambio(tipoBackend: string): string {
  // Frontend y backend ahora usan los mismos tipos
  return tipoBackend
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
  const response = await apiClient.get<ConfiguracionMonitoreo>('/api/v1/monitoreo/configuracion')
  return response.data
}

/**
 * Actualiza la configuración de monitoreo
 */
export async function actualizarConfiguracion(config: ActualizarMonitoreo): Promise<ConfiguracionMonitoreo> {
  const response = await apiClient.put<ConfiguracionMonitoreo>('/api/v1/monitoreo/configuracion', config)
  return response.data
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
  prioridad?: string,
  busqueda?: string,
  pagina = 1,
  porPagina = 50
): Promise<ListaExpedientesResponse> {
  const response = await apiClient.get<ListaExpedientesResponse>('/api/v1/monitoreo/expedientes', {
    params: {
      solo_activos: soloActivos,
      prioridad,
      busqueda,
      pagina,
      por_pagina: porPagina,
    }
  })
  return response.data
}

/**
 * Exporta los expedientes monitoreados a CSV
 */
export async function exportarReporte(
  soloActivos = false,
  prioridad?: string,
  busqueda?: string,
  formato = 'csv'
): Promise<void> {
  const response = await apiClient.get('/api/v1/monitoreo/exportar', {
    params: {
      solo_activos: soloActivos,
      prioridad,
      busqueda,
      formato
    },
    responseType: 'blob'
  })

  // Crear link de descarga
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `monitoreo_expedientes_${new Date().toISOString().slice(0, 10)}.csv`)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

/**
 * Agrega un expediente al monitoreo
 */
export async function agregarExpediente(solicitud: SolicitudMonitorear): Promise<ExpedienteMonitoreado> {
  const response = await apiClient.post<ExpedienteMonitoreado>('/api/v1/monitoreo/expedientes', solicitud)
  return response.data
}

/**
 * Obtiene un expediente monitoreado específico
 */
export async function obtenerExpediente(expedienteNumero: string): Promise<ExpedienteMonitoreado> {
  const response = await apiClient.get<ExpedienteMonitoreado>(`/api/v1/monitoreo/expedientes/${encodeURIComponent(expedienteNumero)}`)
  return response.data
}

/**
 * Actualiza un expediente monitoreado
 */
export async function actualizarExpediente(
  expedienteNumero: string,
  datos: { activo?: boolean; prioridad?: string; notas?: string }
): Promise<ExpedienteMonitoreado> {
  const response = await apiClient.put<ExpedienteMonitoreado>(
    `/api/v1/monitoreo/expedientes/${encodeURIComponent(expedienteNumero)}`,
    datos
  )
  return response.data
}

/**
 * Elimina un expediente del monitoreo
 */
export async function eliminarExpediente(expedienteNumero: string): Promise<void> {
  await apiClient.delete(`/api/v1/monitoreo/expedientes/${encodeURIComponent(expedienteNumero)}`)
}

/**
 * Pausa el monitoreo de un expediente
 */
export async function pausarExpediente(expedienteNumero: string): Promise<ExpedienteMonitoreado> {
  const response = await apiClient.post<ExpedienteMonitoreado>(
    `/api/v1/monitoreo/expedientes/${encodeURIComponent(expedienteNumero)}/pausar`
  )
  return response.data
}

/**
 * Reanuda el monitoreo de un expediente
 */
export async function reanudarExpediente(expedienteNumero: string): Promise<ExpedienteMonitoreado> {
  const response = await apiClient.post<ExpedienteMonitoreado>(
    `/api/v1/monitoreo/expedientes/${encodeURIComponent(expedienteNumero)}/reanudar`
  )
  return response.data
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
  const params: Record<string, string | number | boolean> = {
    solo_no_leidos: soloNoLeidos,
    pagina,
    por_pagina: porPagina,
  }

  if (tipoCambio) params.tipo_cambio = tipoCambio
  if (expedienteNumero) params.expediente_numero = expedienteNumero

  const response = await apiClient.get<ListaCambiosResponse>('/api/v1/monitoreo/cambios', { params })
  return response.data
}

/**
 * Marca un cambio como leído
 */
export async function marcarLeido(cambioId: number): Promise<{ success: boolean; cantidad_marcados: number }> {
  const response = await apiClient.post<{ success: boolean; cantidad_marcados: number }>(
    `/api/v1/monitoreo/cambios/${cambioId}/marcar-leido`
  )
  return response.data
}

/**
 * Marca todos los cambios como leídos
 */
export async function marcarTodosLeidos(): Promise<{ success: boolean; cantidad_marcados: number }> {
  const response = await apiClient.post<{ success: boolean; cantidad_marcados: number }>(
    '/api/v1/monitoreo/cambios/marcar-todos-leidos'
  )
  return response.data
}

// --- ESTADISTICAS ---

/**
 * Obtiene estadísticas del monitoreo
 */
export async function obtenerEstadisticas(): Promise<EstadisticasMonitoreo> {
  const response = await apiClient.get<EstadisticasMonitoreo>('/api/v1/monitoreo/estadisticas')
  return response.data
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
  const response = await apiClient.post<SincronizarResponse>('/api/v1/monitoreo/sincronizar')
  return response.data
}

// --- NUEVAS FUNCIONES PARA GESTIÓN DE CAMBIOS ---

/**
 * Elimina un cambio específico
 */
export async function eliminarCambio(cambioId: number): Promise<{ success: boolean }> {
  const response = await apiClient.delete<{ success: boolean }>(`/api/v1/monitoreo/cambios/${cambioId}`)
  return response.data
}

/**
 * Elimina todos los cambios marcados como leídos
 */
export async function eliminarCambiosLeidos(): Promise<{ success: boolean; cantidad_eliminados: number }> {
  const response = await apiClient.delete<{ success: boolean; cantidad_eliminados: number }>(
    '/api/v1/monitoreo/cambios/leidos'
  )
  return response.data
}

/**
 * Exporta el historial de cambios
 */
export async function exportarCambios(
  soloNoLeidos = false,
  tipoCambio?: string,
  formato: 'csv' | 'json' = 'csv'
): Promise<void> {
  const response = await apiClient.get('/api/v1/monitoreo/cambios/exportar', {
    params: {
      solo_no_leidos: soloNoLeidos,
      tipo_cambio: tipoCambio,
      formato
    },
    responseType: 'blob'
  })

  // Crear link de descarga
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  const extension = formato === 'json' ? 'json' : 'csv'
  link.setAttribute('download', `historial_cambios_${new Date().toISOString().slice(0, 10)}.${extension}`)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}
