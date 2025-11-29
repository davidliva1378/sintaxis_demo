/**
 * API Client para Procesamiento de Actuaciones.
 *
 * Conecta con los endpoints del procesador_pdf:
 * - POST /api/v1/procesamiento/actuacion - Procesar actuación individual
 * - POST /api/v1/procesamiento/expediente - Procesar expediente completo
 * - GET /api/v1/procesamiento/vencimientos/urgentes - Vencimientos urgentes
 * - GET /api/v1/procesamiento/expediente/{numero}/estadisticas - Estadísticas
 * - GET /api/v1/procesamiento/actuaciones/utilidad/{nivel} - Filtrar por utilidad
 * - GET /api/v1/procesamiento/estadisticas/globales - Estadísticas globales
 */

import {
  ActuacionInput,
  ResultadoProcesamiento,
  ResultadoExpediente,
  VencimientoUrgente,
  EstadisticasExpediente,
  EstadisticasGlobales,
  ActuacionPorUtilidad,
  ProcesarActuacionRequest,
  ProcesarExpedienteRequest,
  UtilidadJuridica,
} from '@/types/procesamiento'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Helper para obtener headers con autenticación
function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('access_token')
  return {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
  }
}

// ============================================================================
// Funciones de API
// ============================================================================

/**
 * Procesa una actuación individual con clasificación y análisis de vencimientos.
 */
export async function procesarActuacion(
  request: ProcesarActuacionRequest
): Promise<ResultadoProcesamiento> {
  const response = await fetch(`${API_BASE_URL}/api/v1/procesamiento/actuacion`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

/**
 * Procesa todas las actuaciones de un expediente.
 *
 * Ejecuta clasificación, detección de duplicados y análisis de vencimientos
 * en batch para todas las actuaciones del expediente.
 */
export async function procesarExpediente(
  request: ProcesarExpedienteRequest
): Promise<ResultadoExpediente> {
  const response = await fetch(`${API_BASE_URL}/api/v1/procesamiento/expediente`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

export interface ProcesarExpedientePayload {
  numero_expediente: string
  actuaciones: ActuacionInput[]
  rutas_pdf?: Record<number, string>
  guardar_en_bd?: boolean
  usar_ocr?: boolean
}

/**
 * Procesa un expediente con feedback en tiempo real (Streaming).
 *
 * @param payload Datos del expediente
 * @param onProgress Callback para eventos de progreso
 */
export const procesarExpedienteStream = async (
  payload: ProcesarExpedientePayload,
  onProgress: (event: any) => void, // Assuming StreamEvent is 'any' for now, or needs to be imported/defined
  signal?: AbortSignal
): Promise<ResultadoExpediente> => {
  const token = localStorage.getItem('access_token')

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/procesamiento/expediente/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
      },
      body: JSON.stringify({
        ...payload,
        usar_ocr: payload.usar_ocr ?? true // Default true
      }),
      signal
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    if (!response.body) throw new Error('No response body')

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let finalResult: ResultadoExpediente | null = null

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.trim()) continue
          try {
            const event = JSON.parse(line)

            if (event.event === 'error') {
              throw new Error(event.message || 'Error en el servidor')
            }

            onProgress(event)

            if (event.event === 'complete' && event.result) {
              finalResult = event.result
            }
          } catch (e) {
            if (e instanceof Error && e.message !== 'Error parsing stream event:') {
              throw e
            }
            console.warn('Error parsing stream event:', e)
          }
        }
      }
    } finally {
      reader.releaseLock()
    }

    if (!finalResult) throw new Error('Stream finished without result')
    return finalResult
  } catch (error) {
    console.error('Error en stream:', error)
    throw error
  }
}

/**
 * Obtiene todos los vencimientos urgentes del sistema.
 *
 * @param diasAdelante - Días hacia adelante a considerar (default: 7)
 */
export async function obtenerVencimientosUrgentes(
  diasAdelante: number = 7
): Promise<VencimientoUrgente[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/procesamiento/vencimientos/urgentes?dias_adelante=${diasAdelante}`,
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
 * Obtiene las estadísticas de procesamiento de un expediente específico.
 */
export async function obtenerEstadisticasExpediente(
  numeroExpediente: string
): Promise<EstadisticasExpediente> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/procesamiento/expediente/${encodeURIComponent(numeroExpediente)}/estadisticas`,
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
 * Obtiene los vencimientos de un expediente específico.
 */
export async function obtenerVencimientosExpediente(
  numeroExpediente: string
): Promise<VencimientoUrgente[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/procesamiento/expediente/${encodeURIComponent(numeroExpediente)}/vencimientos`,
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
 * Obtiene las actuaciones clasificadas de un expediente específico.
 */
export async function obtenerActuacionesClasificadasExpediente(
  numeroExpediente: string
): Promise<ActuacionPorUtilidad[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/procesamiento/expediente/${encodeURIComponent(numeroExpediente)}/actuaciones-clasificadas`,
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
 * Obtiene actuaciones filtradas por nivel de utilidad.
 *
 * @param nivel - Nivel de utilidad (alta, media, baja, nula)
 * @param limite - Máximo de resultados (default: 100)
 */
export async function obtenerActuacionesPorUtilidad(
  nivel: UtilidadJuridica,
  limite: number = 100
): Promise<ActuacionPorUtilidad[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/procesamiento/actuaciones/utilidad/${nivel}?limite=${limite}`,
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
 * Obtiene estadísticas globales del sistema de procesamiento.
 */
export async function obtenerEstadisticasGlobales(): Promise<EstadisticasGlobales> {
  const response = await fetch(`${API_BASE_URL}/api/v1/procesamiento/estadisticas/globales`, {
    method: 'GET',
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

// ============================================================================
// Funciones Helper
// ============================================================================

/**
 * Procesa múltiples expedientes en batch.
 *
 * Procesa cada expediente de forma secuencial y retorna resultados.
 */
export async function procesarExpedientesBatch(
  expedientes: Array<{
    numero_expediente: string
    actuaciones: ActuacionInput[]
    rutas_pdf?: Record<number, string>
  }>,
  onProgreso?: (actual: number, total: number, expediente: string) => void
): Promise<ResultadoExpediente[]> {
  const resultados: ResultadoExpediente[] = []

  for (let i = 0; i < expedientes.length; i++) {
    const exp = expedientes[i]

    if (onProgreso) {
      onProgreso(i + 1, expedientes.length, exp.numero_expediente)
    }

    try {
      const resultado = await procesarExpediente({
        numero_expediente: exp.numero_expediente,
        actuaciones: exp.actuaciones,
        rutas_pdf: exp.rutas_pdf,
        guardar_en_bd: true,
      })

      resultados.push(resultado)
    } catch (error) {
      console.error(`Error procesando expediente ${exp.numero_expediente}:`, error)
      // Continuar con el siguiente expediente
    }
  }

  return resultados
}

/**
 * Obtiene el dashboard data con todas las métricas necesarias.
 *
 * Hace múltiples llamadas en paralelo y combina los resultados.
 */
export async function obtenerDashboardData(): Promise<{
  estadisticas: EstadisticasGlobales
  vencimientos_urgentes: VencimientoUrgente[]
  actuaciones_alta: ActuacionPorUtilidad[]
}> {
  const [estadisticas, vencimientos, actuaciones_alta] = await Promise.all([
    obtenerEstadisticasGlobales(),
    obtenerVencimientosUrgentes(7),
    obtenerActuacionesPorUtilidad(UtilidadJuridica.ALTA, 50),
  ])

  return {
    estadisticas,
    vencimientos_urgentes: vencimientos,
    actuaciones_alta,
  }
}

/**
 * Obtiene actuaciones de todas las utilidades para comparación.
 */
export async function obtenerActuacionesPorTodasUtilidades(
  limite: number = 20
): Promise<Record<UtilidadJuridica, ActuacionPorUtilidad[]>> {
  const [alta, media, baja, nula] = await Promise.all([
    obtenerActuacionesPorUtilidad(UtilidadJuridica.ALTA, limite),
    obtenerActuacionesPorUtilidad(UtilidadJuridica.MEDIA, limite),
    obtenerActuacionesPorUtilidad(UtilidadJuridica.BAJA, limite),
    obtenerActuacionesPorUtilidad(UtilidadJuridica.NULA, limite),
  ])

  return {
    [UtilidadJuridica.ALTA]: alta,
    [UtilidadJuridica.MEDIA]: media,
    [UtilidadJuridica.BAJA]: baja,
    [UtilidadJuridica.NULA]: nula,
  }
}

// ============================================================================
// Utilidades de formato y parseo
// ============================================================================

/**
 * Calcula el tiempo estimado de procesamiento para un expediente.
 *
 * @param cantidadActuaciones - Cantidad de actuaciones del expediente
 * @returns Tiempo estimado en segundos
 */
export function calcularTiempoEstimado(cantidadActuaciones: number): number {
  // Estimación basada en benchmarks del procesador_pdf:
  // - Clasificación: ~1000 acts/seg
  // - Extracción PDF: ~2-5 PDFs/seg
  // Promedio conservador: 100 acts/seg
  return Math.ceil(cantidadActuaciones / 100)
}

/**
 * Formatea el tiempo de procesamiento para mostrar en UI.
 */
export function formatearTiempoProcesamiento(segundos: number): string {
  if (segundos < 1) return '< 1s'
  if (segundos < 60) return `${segundos.toFixed(1)}s`

  const minutos = Math.floor(segundos / 60)
  const segs = Math.floor(segundos % 60)

  if (minutos < 60) {
    return segs > 0 ? `${minutos}m ${segs}s` : `${minutos}m`
  }

  const horas = Math.floor(minutos / 60)
  const mins = minutos % 60
  return mins > 0 ? `${horas}h ${mins}m` : `${horas}h`
}

/**
 * Determina si una actuación requiere atención inmediata.
 */
export function requiereAtencionInmediata(actuacion: ActuacionPorUtilidad): boolean {
  // Criterios:
  // 1. Utilidad ALTA
  // 2. Tiene vencimiento próximo (≤ 3 días)
  if (actuacion.utilidad !== UtilidadJuridica.ALTA) {
    return false
  }

  if (actuacion.tiene_vencimiento && actuacion.dias_restantes !== undefined) {
    return actuacion.dias_restantes <= 3
  }

  return true // Toda actuación de utilidad ALTA requiere atención
}

/**
 * Agrupa vencimientos por nivel de urgencia.
 */
export function agruparVencimientosPorUrgencia(
  vencimientos: VencimientoUrgente[]
): Record<string, VencimientoUrgente[]> {
  return vencimientos.reduce((acc, venc) => {
    const nivel = venc.nivel_urgencia
    if (!acc[nivel]) {
      acc[nivel] = []
    }
    acc[nivel].push(venc)
    return acc
  }, {} as Record<string, VencimientoUrgente[]>)
}

/**
 * Calcula métricas de rendimiento del procesamiento.
 */
export function calcularMetricasRendimiento(estadisticas: EstadisticasExpediente): {
  velocidad_acts_por_seg: number
  actuaciones_relevantes: number
  porcentaje_alta: number
  porcentaje_reduccion: number
} {
  const total = estadisticas.total_actuaciones
  const tiempo = estadisticas.tiempo_procesamiento_seg || 1

  return {
    velocidad_acts_por_seg: total / tiempo,
    actuaciones_relevantes: estadisticas.actuaciones_alta + estadisticas.actuaciones_media,
    porcentaje_alta: total > 0 ? (estadisticas.actuaciones_alta / total) * 100 : 0,
    porcentaje_reduccion: estadisticas.reduccion_estimada_pct,
  }
}

/**
 * Genera un resumen textual del procesamiento.
 */
export function generarResumenProcesamiento(resultado: ResultadoExpediente): string {
  const stats = resultado.estadisticas
  const relevantes = stats.actuaciones_alta + stats.actuaciones_media
  const porcentaje = ((relevantes / stats.total_actuaciones) * 100).toFixed(1)

  const lineas = [
    `Procesadas ${stats.total_actuaciones} actuaciones en ${formatearTiempoProcesamiento(stats.tiempo_procesamiento_seg)}`,
    `${relevantes} actuaciones relevantes (${porcentaje}%)`,
  ]

  if (stats.vencimientos_urgentes > 0) {
    lineas.push(`⚠️  ${stats.vencimientos_urgentes} vencimientos urgentes detectados`)
  }

  if (stats.duplicados_detectados > 0) {
    lineas.push(`🔍 ${stats.duplicados_detectados} duplicados encontrados`)
  }

  return lineas.join('\n')
}
