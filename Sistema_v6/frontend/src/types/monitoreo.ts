/**
 * Tipos TypeScript para el módulo de Monitoreo
 */

/**
 * EstadoMonitoreo - Estado del sistema de monitoreo
 */
export type EstadoMonitoreo = 'activo' | 'pausado' | 'detenido' | 'error'

/**
 * TipoCambio - Tipo de cambio detectado en expediente
 */
export type TipoCambio =
  | 'nueva_actuacion'
  | 'cambio_estado'
  | 'nuevo_archivo'
  | 'modificacion'
  | 'otro'

/**
 * FrecuenciaMonitoreo - Frecuencia de verificación
 */
export type FrecuenciaMonitoreo =
  | '5min'
  | '15min'
  | '30min'
  | '1hora'
  | '3horas'
  | '6horas'
  | '12horas'
  | '24horas'

/**
 * ConfiguracionMonitoreo - Configuración global del sistema
 */
export interface ConfiguracionMonitoreo {
  id: number
  usuario_id: number
  activo: boolean
  frecuencia: FrecuenciaMonitoreo
  notificar_email: boolean
  notificar_sistema: boolean
  hora_inicio?: string // HH:mm formato 24h
  hora_fin?: string    // HH:mm formato 24h
  dias_semana?: number[] // 0-6 (domingo a sábado)
  created_at: string
  updated_at: string
}

/**
 * ExpedienteMonitoreado - Expediente bajo monitoreo
 */
export interface ExpedienteMonitoreado {
  id: number
  usuario_id: number
  expediente_numero: string
  expediente_caratula: string
  expediente_dependencia?: string
  activo: boolean
  ultima_verificacion?: string
  ultima_actuacion_fecha?: string
  ultima_actuacion_id?: number
  total_cambios_detectados: number
  created_at: string
  updated_at: string
}

/**
 * CambioDetectado - Cambio detectado en expediente
 */
export interface CambioDetectado {
  id: number
  expediente_monitoreado_id: number
  expediente_numero: string
  expediente_caratula: string
  tipo_cambio: TipoCambio
  descripcion: string
  detalles?: Record<string, any> // JSON con detalles del cambio
  notificado: boolean
  leido: boolean
  fecha_deteccion: string
  created_at: string
}

/**
 * EstadisticasMonitoreo - Estadísticas del sistema
 */
export interface EstadisticasMonitoreo {
  total_expedientes: number
  expedientes_activos: number
  expedientes_pausados: number
  cambios_hoy: number
  cambios_semana: number
  cambios_mes: number
  cambios_sin_leer: number
  ultima_ejecucion?: string
  proxima_ejecucion?: string
}

/**
 * SolicitudMonitorear - Request para agregar expediente al monitoreo
 */
export interface SolicitudMonitorear {
  expediente_numero: string
  expediente_caratula?: string
  expediente_dependencia?: string
}

/**
 * ActualizarMonitoreo - Request para actualizar estado de monitoreo
 */
export interface ActualizarMonitoreo {
  activo?: boolean
  frecuencia?: FrecuenciaMonitoreo
  notificar_email?: boolean
  notificar_sistema?: boolean
  hora_inicio?: string
  hora_fin?: string
  dias_semana?: number[]
}

/**
 * Frecuencias disponibles con etiquetas
 */
export const FRECUENCIAS_MONITOREO: Array<{
  value: FrecuenciaMonitoreo
  label: string
  descripcion: string
}> = [
  { value: '5min', label: 'Cada 5 minutos', descripcion: 'Verificación muy frecuente' },
  { value: '15min', label: 'Cada 15 minutos', descripcion: 'Verificación frecuente' },
  { value: '30min', label: 'Cada 30 minutos', descripcion: 'Verificación regular' },
  { value: '1hora', label: 'Cada hora', descripcion: 'Verificación estándar' },
  { value: '3horas', label: 'Cada 3 horas', descripcion: 'Verificación moderada' },
  { value: '6horas', label: 'Cada 6 horas', descripcion: 'Verificación espaciada' },
  { value: '12horas', label: 'Cada 12 horas', descripcion: '2 veces al día' },
  { value: '24horas', label: 'Cada 24 horas', descripcion: '1 vez al día' },
]

/**
 * Días de la semana
 */
export const DIAS_SEMANA = [
  { value: 0, label: 'Dom', fullLabel: 'Domingo' },
  { value: 1, label: 'Lun', fullLabel: 'Lunes' },
  { value: 2, label: 'Mar', fullLabel: 'Martes' },
  { value: 3, label: 'Mié', fullLabel: 'Miércoles' },
  { value: 4, label: 'Jue', fullLabel: 'Jueves' },
  { value: 5, label: 'Vie', fullLabel: 'Viernes' },
  { value: 6, label: 'Sáb', fullLabel: 'Sábado' },
]

/**
 * Tipos de cambio con etiquetas
 */
export const TIPOS_CAMBIO: Record<TipoCambio, { label: string; color: string; icon: string }> = {
  nueva_actuacion: {
    label: 'Nueva Actuación',
    color: 'blue',
    icon: 'file-plus',
  },
  cambio_estado: {
    label: 'Cambio de Estado',
    color: 'purple',
    icon: 'refresh-cw',
  },
  nuevo_archivo: {
    label: 'Nuevo Archivo',
    color: 'green',
    icon: 'paperclip',
  },
  modificacion: {
    label: 'Modificación',
    color: 'orange',
    icon: 'edit',
  },
  otro: {
    label: 'Otro',
    color: 'gray',
    icon: 'info',
  },
}
