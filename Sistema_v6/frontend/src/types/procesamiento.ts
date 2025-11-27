/**
 * Tipos para procesamiento de actuaciones y expedientes.
 *
 * Sistema de clasificación automática por utilidad jurídica,
 * detección de vencimientos y duplicados.
 */

// ============================================================================
// Enums
// ============================================================================

export enum UtilidadJuridica {
  NULA = 'nula',
  BAJA = 'baja',
  MEDIA = 'media',
  ALTA = 'alta'
}

export enum TipoVencimiento {
  CEDULA_ELECTRONICA = 'cedula_electronica',
  CEDULA_FISICA = 'cedula_fisica',
  TRASLADO = 'traslado',
  ALEGATO = 'alegato',
  CONTESTACION = 'contestacion',
  OTROS = 'otros'
}

export enum NivelUrgencia {
  VENCIDO = 'vencido',
  CRITICO = 'critico',      // 0-1 días
  URGENTE = 'urgente',      // 2-3 días
  PROXIMO = 'proximo',      // 4-7 días
  NORMAL = 'normal'         // >7 días
}

export enum EstadoVencimiento {
  PENDIENTE = 'pendiente',
  ATENDIDO = 'atendido',
  VENCIDO = 'vencido'
}

// ============================================================================
// Modelos de Actuación
// ============================================================================

export interface ActuacionInput {
  id: number
  tipo: string
  detalle: string
  tiene_archivo?: boolean
  expediente_numero?: string
}

export interface ClasificacionActuacion {
  utilidad: UtilidadJuridica
  score: number
  motivo: string
  requiere_pdf: boolean
  tiene_plazo_probable: boolean
  keywords_detectados: string[]
}

export interface Vencimiento {
  tipo: TipoVencimiento
  fecha_notificacion: string  // ISO date
  plazo_dias: number
  fecha_vencimiento: string   // ISO date
  dias_habiles: boolean
  descripcion?: string
  confianza: number           // 0.0 - 1.0
}

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
}

export interface ResultadoProcesamiento {
  actuacion_id: number
  clasificacion: ClasificacionActuacion
  vencimientos: Vencimiento[]
  duplicados_detectados: number
  tiene_errores: boolean
  errores: string[]
}

// ============================================================================
// Modelos de Expediente
// ============================================================================

export interface EstadisticasExpediente {
  total_actuaciones: number
  actuaciones_alta: number
  actuaciones_media: number
  actuaciones_baja: number
  actuaciones_nula: number
  reduccion_estimada_pct: number
  vencimientos_detectados: number
  vencimientos_urgentes: number
  duplicados_detectados: number
  tiempo_procesamiento_seg: number
}

// ============================================================================
// Entidades Normalizadas (NER)
// ============================================================================

export interface EntidadNormalizada {
  original: string
  normalized: string
  label: string
  score: number
  normalization_type?: string  // fecha, monto, nombre, norma, tribunal, llm
}

export interface ResultadoExpediente {
  expediente_numero: string
  estadisticas: EstadisticasExpediente
  vencimientos_urgentes: VencimientoUrgente[]
  con_errores: number
  entidades_por_actuacion?: Record<number, EntidadNormalizada[]>
}

// ============================================================================
// Modelos de Consulta
// ============================================================================

export interface ActuacionPorUtilidad {
  id: number
  expediente_numero: string
  tipo: string
  detalle: string
  utilidad: UtilidadJuridica
  score: number
  tiene_vencimiento: boolean
  fecha_vencimiento?: string
  dias_restantes?: number
}

export interface EstadisticasGlobales {
  total_expedientes_procesados: number
  total_actuaciones_procesadas: number
  total_vencimientos_detectados: number
  total_vencimientos_urgentes: number
  total_duplicados_detectados: number
  reduccion_promedio_pct: number
  ultima_actualizacion?: string
}

// ============================================================================
// Request Types
// ============================================================================

export interface ProcesarActuacionRequest {
  actuacion: ActuacionInput
  ruta_pdf?: string
  guardar_en_bd?: boolean
}

export interface ProcesarExpedienteRequest {
  numero_expediente: string
  actuaciones: ActuacionInput[]
  rutas_pdf?: Record<number, string>  // { actuacion_id: ruta }
  guardar_en_bd?: boolean
}

// ============================================================================
// Filtros y Opciones
// ============================================================================

export interface FiltrosActuaciones {
  utilidad?: UtilidadJuridica
  tiene_vencimiento?: boolean
  urgente?: boolean
  limite?: number
}

export interface FiltrosVencimientos {
  dias_adelante?: number
  nivel_urgencia?: NivelUrgencia
  estado?: EstadoVencimiento
  expediente_numero?: string
}

// ============================================================================
// UI Helper Types
// ============================================================================

export interface CardActuacionData {
  id: number
  tipo: string
  detalle: string
  utilidad: UtilidadJuridica
  score: number
  tiene_vencimiento: boolean
  fecha_vencimiento?: string
  nivel_urgencia?: NivelUrgencia
  keywords?: string[]
}

export interface DashboardData {
  estadisticas_globales: EstadisticasGlobales
  vencimientos_urgentes: VencimientoUrgente[]
  actuaciones_alta_utilidad: ActuacionPorUtilidad[]
  chart_data: {
    utilidad: { label: string; value: number; color: string }[]
    vencimientos_por_dia: { fecha: string; cantidad: number }[]
  }
}

export interface ProcesamientoState {
  en_proceso: boolean
  expediente_actual?: string
  progreso: number        // 0-100
  actuaciones_procesadas: number
  actuaciones_totales: number
  errores: string[]
}

// ============================================================================
// Colores y Estilos por Utilidad
// ============================================================================

export const COLORES_UTILIDAD: Record<UtilidadJuridica, string> = {
  [UtilidadJuridica.ALTA]: 'bg-red-500',
  [UtilidadJuridica.MEDIA]: 'bg-yellow-500',
  [UtilidadJuridica.BAJA]: 'bg-blue-500',
  [UtilidadJuridica.NULA]: 'bg-gray-400'
}

export const COLORES_UTILIDAD_TEXT: Record<UtilidadJuridica, string> = {
  [UtilidadJuridica.ALTA]: 'text-red-700',
  [UtilidadJuridica.MEDIA]: 'text-yellow-700',
  [UtilidadJuridica.BAJA]: 'text-blue-700',
  [UtilidadJuridica.NULA]: 'text-gray-600'
}

export const COLORES_URGENCIA: Record<NivelUrgencia, string> = {
  [NivelUrgencia.VENCIDO]: 'bg-black text-white',
  [NivelUrgencia.CRITICO]: 'bg-red-600 text-white',
  [NivelUrgencia.URGENTE]: 'bg-orange-500 text-white',
  [NivelUrgencia.PROXIMO]: 'bg-yellow-400',
  [NivelUrgencia.NORMAL]: 'bg-green-500'
}

export const LABELS_UTILIDAD: Record<UtilidadJuridica, string> = {
  [UtilidadJuridica.ALTA]: 'Alta Utilidad',
  [UtilidadJuridica.MEDIA]: 'Media Utilidad',
  [UtilidadJuridica.BAJA]: 'Baja Utilidad',
  [UtilidadJuridica.NULA]: 'Sin Utilidad'
}

export const LABELS_URGENCIA: Record<NivelUrgencia, string> = {
  [NivelUrgencia.VENCIDO]: 'VENCIDO',
  [NivelUrgencia.CRITICO]: 'Crítico (hoy/mañana)',
  [NivelUrgencia.URGENTE]: 'Urgente (2-3 días)',
  [NivelUrgencia.PROXIMO]: 'Próximo (4-7 días)',
  [NivelUrgencia.NORMAL]: 'Normal'
}

// Colores para tipos de entidad NER
export const COLORES_ENTIDAD: Record<string, string> = {
  'FECHA': 'bg-blue-100 text-blue-800',
  'MONTO': 'bg-green-100 text-green-800',
  'PERSONA': 'bg-purple-100 text-purple-800',
  'JUEZ': 'bg-indigo-100 text-indigo-800',
  'ABOGADO': 'bg-violet-100 text-violet-800',
  'ACTOR': 'bg-orange-100 text-orange-800',
  'DEMANDADO': 'bg-red-100 text-red-800',
  'NORMA': 'bg-amber-100 text-amber-800',
  'LEY': 'bg-yellow-100 text-yellow-800',
  'ARTICULO': 'bg-lime-100 text-lime-800',
  'TRIBUNAL': 'bg-cyan-100 text-cyan-800',
  'EXPEDIENTE': 'bg-teal-100 text-teal-800',
  'default': 'bg-gray-100 text-gray-800'
}

export function getColorEntidad(label: string): string {
  return COLORES_ENTIDAD[label.toUpperCase()] || COLORES_ENTIDAD['default']
}

// ============================================================================
// Utilidades de formato
// ============================================================================

/**
 * Obtiene el color de badge según la utilidad
 */
export function getColorUtilidad(utilidad: UtilidadJuridica): string {
  return COLORES_UTILIDAD[utilidad]
}

/**
 * Obtiene el color de badge según el nivel de urgencia
 */
export function getColorUrgencia(nivel: NivelUrgencia): string {
  return COLORES_URGENCIA[nivel]
}

/**
 * Formatea el porcentaje de reducción
 */
export function formatReduccion(pct: number): string {
  return `${pct.toFixed(1)}%`
}

/**
 * Formatea los días restantes para vencimiento
 */
export function formatDiasRestantes(dias: number): string {
  if (dias < 0) return `Vencido (${Math.abs(dias)} días)`
  if (dias === 0) return 'Hoy'
  if (dias === 1) return 'Mañana'
  return `${dias} días`
}

/**
 * Determina el nivel de urgencia según días restantes
 */
export function getNivelUrgencia(dias: number): NivelUrgencia {
  if (dias < 0) return NivelUrgencia.VENCIDO
  if (dias <= 1) return NivelUrgencia.CRITICO
  if (dias <= 3) return NivelUrgencia.URGENTE
  if (dias <= 7) return NivelUrgencia.PROXIMO
  return NivelUrgencia.NORMAL
}
