/**
 * Tipos unificados para el sistema de vencimientos.
 *
 * Este archivo centraliza todos los tipos relacionados con vencimientos
 * para evitar duplicación y garantizar consistencia.
 */

// ============================================================================
// Enums
// ============================================================================

export type TipoVencimiento =
  | 'cedula_electronica'
  | 'cedula_fisica'
  | 'traslado'
  | 'alegato'
  | 'presentacion'
  | 'otro'

export type EstadoVencimiento = 'pendiente' | 'atendido' | 'vencido' | 'cancelado'

export type NivelUrgencia = 'vencido' | 'critico' | 'urgente' | 'proximo' | 'normal'

// ============================================================================
// Modelos Base
// ============================================================================

/**
 * Vencimiento básico detectado en una actuación.
 * Usado durante el procesamiento/detección.
 */
export interface VencimientoDetectado {
  tipo: TipoVencimiento
  fecha_notificacion: string  // ISO date
  plazo_dias: number
  fecha_vencimiento: string   // ISO date
  dias_habiles: boolean
  descripcion?: string
  confianza: number           // 0.0 - 1.0
}

/**
 * Vencimiento completo con ID y metadata del backend.
 * Modelo principal para gestión de vencimientos.
 */
export interface Vencimiento {
  id: number
  expediente_numero: string
  actuacion_id: number | null
  tipo: TipoVencimiento
  descripcion: string
  fecha_notificacion: string
  plazo_dias: number
  fecha_vencimiento: string
  estado: EstadoVencimiento
  confianza: number
  texto_fuente: string | null
  creado_en: string
  actualizado_en: string
  // Campos calculados
  dias_restantes: number
  nivel_urgencia: NivelUrgencia
}

/**
 * Vencimiento con datos de actuación para mostrar en UI.
 * Extiende Vencimiento con campos adicionales para visualización.
 */
export interface VencimientoUrgente {
  id: number
  actuacion_id: number
  expediente_numero: string
  tipo: string
  fecha_vencimiento: string   // ISO date
  dias_restantes: number
  nivel_urgencia: NivelUrgencia
  descripcion?: string
  actuacion_tipo: string
  actuacion_detalle: string
  fecha_notificacion?: string
}

// ============================================================================
// Filtros y Opciones
// ============================================================================

export interface FiltrosVencimientos {
  estado?: EstadoVencimiento
  tipo?: TipoVencimiento
  nivel_urgencia?: NivelUrgencia | 'todos'
  expediente_numero?: string
  expediente?: string         // Alias para compatibilidad
  dias_desde?: number         // Desde hace X días (para incluir vencidos)
  dias_hasta?: number         // Hasta X días adelante
  fecha_desde?: string
  fecha_hasta?: string
  ocultarVencidos?: boolean
  limite?: number
  offset?: number             // Offset para paginación
}

// ============================================================================
// Estadísticas
// ============================================================================

export interface EstadisticasVencimientos {
  total: number
  pendientes: number
  vencidos: number
  atendidos: number
  cancelados: number
  criticos_hoy: number
  urgentes_3_dias: number
  proximos_7_dias: number
  por_tipo: Record<string, number>
}

export interface EstadisticasVencimientosSimple {
  total: number
  vencidos: number
  criticos: number
  urgentes: number
  proximos: number
  normales: number
}

// ============================================================================
// Paginación
// ============================================================================

export interface PaginacionVencimientos {
  pagina: number
  por_pagina: number
  total: number
  total_paginas: number
}

export interface VencimientosResponse {
  vencimientos: VencimientoUrgente[]
  total: number
  pagina: number
  por_pagina: number
  total_paginas: number
}

// ============================================================================
// Filtros Predefinidos
// ============================================================================

export const FILTROS_TEMPORALES = {
  HOY: { label: 'Vence hoy', dias_desde: 0, dias_hasta: 0 },
  PROXIMOS_3_DIAS: { label: 'Próximos 3 días', dias_desde: 0, dias_hasta: 3 },
  PROXIMOS_7_DIAS: { label: 'Próximos 7 días', dias_desde: 0, dias_hasta: 7 },
  PROXIMOS_15_DIAS: { label: 'Próximos 15 días', dias_desde: 0, dias_hasta: 15 },
  PROXIMOS_30_DIAS: { label: 'Próximos 30 días', dias_desde: 0, dias_hasta: 30 },
  ULTIMOS_7_DIAS: { label: 'Últimos 7 días (vencidos)', dias_desde: -7, dias_hasta: 0 },
  TODOS: { label: 'Todos', dias_desde: -30, dias_hasta: 30 },
} as const

export type FiltroTemporalKey = keyof typeof FILTROS_TEMPORALES

// ============================================================================
// Colores y Labels
// ============================================================================

export const COLORES_URGENCIA: Record<NivelUrgencia, string> = {
  vencido: 'bg-black text-white',
  critico: 'bg-red-600 text-white',
  urgente: 'bg-orange-500 text-white',
  proximo: 'bg-yellow-400 text-gray-900',
  normal: 'bg-green-500 text-white'
}

export const COLORES_URGENCIA_BORDER: Record<NivelUrgencia, string> = {
  vencido: 'border-black',
  critico: 'border-red-600',
  urgente: 'border-orange-500',
  proximo: 'border-yellow-400',
  normal: 'border-green-500'
}

export const COLORES_URGENCIA_BG: Record<NivelUrgencia, string> = {
  vencido: 'bg-black/5 dark:bg-black/30',
  critico: 'bg-red-50 dark:bg-red-900/20',
  urgente: 'bg-orange-50 dark:bg-orange-900/20',
  proximo: 'bg-yellow-50 dark:bg-yellow-900/20',
  normal: 'bg-green-50 dark:bg-green-900/20'
}

export const COLORES_URGENCIA_TEXT: Record<NivelUrgencia, string> = {
  vencido: 'text-black dark:text-white',
  critico: 'text-red-600 dark:text-red-400',
  urgente: 'text-orange-600 dark:text-orange-400',
  proximo: 'text-yellow-600 dark:text-yellow-400',
  normal: 'text-green-600 dark:text-green-400'
}

export const LABELS_URGENCIA: Record<NivelUrgencia, string> = {
  vencido: 'VENCIDO',
  critico: 'Crítico (hoy/mañana)',
  urgente: 'Urgente (2-3 días)',
  proximo: 'Próximo (4-7 días)',
  normal: 'Normal'
}

export const LABELS_URGENCIA_CORTO: Record<NivelUrgencia, string> = {
  vencido: 'VENCIDO',
  critico: 'CRÍTICO',
  urgente: 'URGENTE',
  proximo: 'PRÓXIMO',
  normal: 'NORMAL'
}

export const LABELS_TIPO_VENCIMIENTO: Record<TipoVencimiento, string> = {
  cedula_electronica: 'Cédula Electrónica',
  cedula_fisica: 'Cédula Física',
  traslado: 'Traslado',
  alegato: 'Alegato',
  presentacion: 'Presentación',
  otro: 'Otro'
}

// ============================================================================
// Utilidades
// ============================================================================

/**
 * Formatea los días restantes para mostrar en UI.
 */
export function formatDiasRestantes(dias: number): string {
  if (dias < 0) return `Vencido (${Math.abs(dias)} días)`
  if (dias === 0) return 'Hoy'
  if (dias === 1) return 'Mañana'
  return `${dias} días`
}

/**
 * Calcula el nivel de urgencia según los días restantes.
 */
export function calcularNivelUrgencia(diasRestantes: number): NivelUrgencia {
  if (diasRestantes < 0) return 'vencido'
  if (diasRestantes <= 1) return 'critico'
  if (diasRestantes <= 3) return 'urgente'
  if (diasRestantes <= 7) return 'proximo'
  return 'normal'
}

/**
 * Calcula días restantes desde fecha de vencimiento.
 */
export function calcularDiasRestantes(fechaVencimiento: string): number {
  const hoy = new Date()
  hoy.setHours(0, 0, 0, 0)
  const venc = new Date(fechaVencimiento)
  venc.setHours(0, 0, 0, 0)
  return Math.ceil((venc.getTime() - hoy.getTime()) / (1000 * 60 * 60 * 24))
}

/**
 * Enriquece un vencimiento con campos calculados.
 */
export function enriquecerVencimiento<T extends { fecha_vencimiento: string }>(
  vencimiento: T
): T & { dias_restantes: number; nivel_urgencia: NivelUrgencia } {
  const dias_restantes = calcularDiasRestantes(vencimiento.fecha_vencimiento)
  return {
    ...vencimiento,
    dias_restantes,
    nivel_urgencia: calcularNivelUrgencia(dias_restantes)
  }
}

/**
 * Obtiene el color de badge según el nivel de urgencia.
 */
export function getColorUrgencia(nivel: NivelUrgencia): string {
  return COLORES_URGENCIA[nivel] || COLORES_URGENCIA.normal
}

/**
 * Ordena vencimientos por urgencia (más urgentes primero).
 */
export function ordenarPorUrgencia<T extends { dias_restantes: number }>(
  vencimientos: T[]
): T[] {
  return [...vencimientos].sort((a, b) => a.dias_restantes - b.dias_restantes)
}
