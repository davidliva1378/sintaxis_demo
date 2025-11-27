/**
 * API Client para Dashboard Hub.
 *
 * Conecta con los endpoints del dashboard:
 * - GET /api/v1/dashboard/stats - KPIs consolidados
 * - GET /api/v1/dashboard/health - Estado del sistema
 * - GET /api/v1/dashboard/movimientos - Últimos movimientos
 * - GET /api/v1/dashboard/vencimientos-urgentes - Vencimientos urgentes
 */

// ============================================================================
// Tipos
// ============================================================================

export interface DashboardStats {
  total_expedientes: number
  expedientes_semana: number
  vencimientos_urgentes: number
  vencimientos_vencidos: number
  expedientes_monitoreados: number
  porcentaje_procesado_ia: number
  total_actuaciones: number
  documentos_indexados_rag: number
}

export interface ServiceHealthStatus {
  name: string
  status: 'ok' | 'error' | 'warning' | 'unknown'
  message?: string
  response_time_ms?: number
}

export interface SystemHealth {
  overall_status: 'healthy' | 'degraded' | 'critical'
  services: ServiceHealthStatus[]
  timestamp: string
}

export interface MovimientoReciente {
  id: number
  tipo: 'extraccion' | 'monitoreo' | 'procesamiento' | 'alerta'
  descripcion: string
  expediente_numero?: string
  fecha: string
  icono: string
}

export interface UltimosMovimientos {
  movimientos: MovimientoReciente[]
  total: number
}

export interface VencimientoUrgenteDashboard {
  id: number
  expediente_numero: string
  tipo: string
  descripcion: string
  fecha_vencimiento: string
  dias_restantes: number
  nivel_urgencia: 'vencido' | 'critico' | 'urgente' | 'proximo'
}

export interface VencimientosUrgentes {
  vencimientos: VencimientoUrgenteDashboard[]
  total: number
}

// ============================================================================
// Config
// ============================================================================

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Helper para obtener headers con autenticacion
function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('access_token')
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
}

// ============================================================================
// Funciones de API
// ============================================================================

/**
 * Obtiene las estadisticas/KPIs consolidados del dashboard.
 */
export async function getDashboardStats(): Promise<DashboardStats> {
  const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/stats`, {
    method: 'GET',
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

/**
 * Obtiene el estado de salud completo del sistema.
 */
export async function getSystemHealth(): Promise<SystemHealth> {
  const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/health`, {
    method: 'GET',
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

/**
 * Obtiene los ultimos movimientos/actividad del sistema.
 *
 * @param limite - Maximo de movimientos a retornar (default: 10)
 */
export async function getUltimosMovimientos(limite: number = 10): Promise<UltimosMovimientos> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/dashboard/movimientos?limite=${limite}`,
    {
      method: 'GET',
      headers: getAuthHeaders(),
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

/**
 * Obtiene los vencimientos mas urgentes para el dashboard.
 *
 * @param limite - Maximo de vencimientos a retornar (default: 5)
 */
export async function getVencimientosUrgentes(limite: number = 5): Promise<VencimientosUrgentes> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/dashboard/vencimientos-urgentes?limite=${limite}`,
    {
      method: 'GET',
      headers: getAuthHeaders(),
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

// ============================================================================
// Funciones Helper - Carga de datos combinados
// ============================================================================

/**
 * Carga todos los datos del dashboard en paralelo.
 *
 * Ideal para la carga inicial del dashboard.
 */
export async function loadDashboardData(): Promise<{
  stats: DashboardStats
  health: SystemHealth
  movimientos: UltimosMovimientos
  vencimientos: VencimientosUrgentes
}> {
  const [stats, health, movimientos, vencimientos] = await Promise.all([
    getDashboardStats(),
    getSystemHealth(),
    getUltimosMovimientos(10),
    getVencimientosUrgentes(5),
  ])

  return {
    stats,
    health,
    movimientos,
    vencimientos,
  }
}

// ============================================================================
// Utilidades de formato
// ============================================================================

/**
 * Obtiene el color CSS segun el nivel de urgencia.
 */
export function getUrgenciaColor(nivel: VencimientoUrgenteDashboard['nivel_urgencia']): string {
  const colores: Record<typeof nivel, string> = {
    vencido: 'text-red-600 bg-red-50',
    critico: 'text-orange-600 bg-orange-50',
    urgente: 'text-yellow-600 bg-yellow-50',
    proximo: 'text-blue-600 bg-blue-50',
  }
  return colores[nivel] || 'text-gray-600 bg-gray-50'
}

/**
 * Obtiene el color CSS segun el estado del servicio.
 */
export function getServiceStatusColor(status: ServiceHealthStatus['status']): string {
  const colores: Record<typeof status, string> = {
    ok: 'text-green-600 bg-green-50',
    warning: 'text-yellow-600 bg-yellow-50',
    error: 'text-red-600 bg-red-50',
    unknown: 'text-gray-600 bg-gray-50',
  }
  return colores[status] || 'text-gray-600 bg-gray-50'
}

/**
 * Obtiene el icono segun el tipo de movimiento.
 */
export function getMovimientoIcon(tipo: MovimientoReciente['tipo']): string {
  const iconos: Record<typeof tipo, string> = {
    extraccion: 'download',
    monitoreo: 'refresh-cw',
    procesamiento: 'cpu',
    alerta: 'alert-triangle',
  }
  return iconos[tipo] || 'bell'
}

/**
 * Formatea la fecha de forma relativa (hace X minutos, etc).
 */
export function formatRelativeTime(fechaStr: string): string {
  const fecha = new Date(fechaStr)
  const ahora = new Date()
  const diffMs = ahora.getTime() - fecha.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return 'Ahora'
  if (diffMins < 60) return `Hace ${diffMins}m`
  if (diffHours < 24) return `Hace ${diffHours}h`
  if (diffDays < 7) return `Hace ${diffDays}d`

  return fecha.toLocaleDateString('es-AR', {
    day: '2-digit',
    month: 'short',
  })
}

/**
 * Formatea porcentaje con precision.
 */
export function formatPorcentaje(valor: number, decimales: number = 1): string {
  return `${valor.toFixed(decimales)}%`
}

/**
 * Determina el estado general del dashboard basado en las metricas.
 */
export function getDashboardAlertLevel(
  stats: DashboardStats,
  health: SystemHealth
): 'ok' | 'warning' | 'critical' {
  // Critico si hay servicios caidos o muchos vencimientos vencidos
  if (health.overall_status === 'critical' || stats.vencimientos_vencidos > 5) {
    return 'critical'
  }

  // Warning si sistema degradado o hay vencimientos urgentes
  if (
    health.overall_status === 'degraded' ||
    stats.vencimientos_urgentes > 3 ||
    stats.vencimientos_vencidos > 0
  ) {
    return 'warning'
  }

  return 'ok'
}
