/**
 * Tipos para el modulo Agenda
 */

export type TipoEvento = 'vencimiento' | 'audiencia' | 'tarea' | 'recordatorio' | 'otro'
export type Prioridad = 'baja' | 'media' | 'alta' | 'urgente'
export type EstadoEvento = 'pendiente' | 'en_progreso' | 'completado' | 'cancelado'

export interface Evento {
  id: number
  titulo: string
  descripcion: string | null
  fecha_inicio: string
  fecha_fin: string | null
  todo_el_dia: boolean
  tipo: TipoEvento
  prioridad: Prioridad
  estado: EstadoEvento
  expediente_numero: string | null
  actuacion_indice: number | null
  color: string | null
  recordatorio_minutos: number | null
  notas: string | null
  created_at: string
  updated_at: string
  urgencia: string | null
  dias_restantes: number | null
}

export interface EventoCreate {
  titulo: string
  descripcion?: string | null
  fecha_inicio: string
  fecha_fin?: string | null
  todo_el_dia?: boolean
  tipo?: TipoEvento
  prioridad?: Prioridad
  expediente_numero?: string | null
  actuacion_indice?: number | null
  color?: string | null
  recordatorio_minutos?: number | null
  notas?: string | null
}

export interface EventoUpdate {
  titulo?: string
  descripcion?: string | null
  fecha_inicio?: string
  fecha_fin?: string | null
  todo_el_dia?: boolean
  tipo?: TipoEvento
  prioridad?: Prioridad
  estado?: EstadoEvento
  expediente_numero?: string | null
  actuacion_indice?: number | null
  color?: string | null
  recordatorio_minutos?: number | null
  notas?: string | null
}

export interface ResumenAgenda {
  total_pendientes: number
  total_hoy: number
  total_semana: number
  total_vencidos: number
  proximos_eventos: Evento[]
}

export interface FiltrosAgenda {
  fecha_desde?: string
  fecha_hasta?: string
  tipo?: TipoEvento
  estado?: EstadoEvento
  expediente?: string
}
