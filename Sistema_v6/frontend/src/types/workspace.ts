/**
 * Tipos TypeScript para el módulo de Workspaces
 */

/**
 * Workspace - Espacio de trabajo para organizar expedientes
 */
export interface Workspace {
  id: number
  nombre: string
  descripcion?: string
  color?: string // Color hex para identificación visual
  icon?: string // Icono opcional (lucide icon name)
  usuario_id: number
  expedientes_count: number // Cantidad de expedientes asociados
  created_at: string
  updated_at: string
}

/**
 * WorkspaceCrear - Datos para crear un workspace
 */
export interface WorkspaceCrear {
  nombre: string
  descripcion?: string
  color?: string
  icon?: string
}

/**
 * WorkspaceActualizar - Datos para actualizar un workspace
 */
export interface WorkspaceActualizar {
  nombre?: string
  descripcion?: string
  color?: string
  icon?: string
}

/**
 * WorkspaceExpediente - Relación entre workspace y expediente
 */
export interface WorkspaceExpediente {
  id: number
  workspace_id: number
  expediente_numero: string
  created_at: string
}

/**
 * WorkspaceConExpedientes - Workspace con lista de expedientes
 */
export interface WorkspaceConExpedientes extends Workspace {
  expedientes: Array<{
    numero: string
    caratula: string
    dependencia?: string
    situacion?: string
  }>
}

/**
 * Colores predefinidos para workspaces
 */
export const WORKSPACE_COLORS = [
  { value: '#ef4444', label: 'Rojo' },
  { value: '#f97316', label: 'Naranja' },
  { value: '#f59e0b', label: 'Ámbar' },
  { value: '#eab308', label: 'Amarillo' },
  { value: '#84cc16', label: 'Lima' },
  { value: '#22c55e', label: 'Verde' },
  { value: '#10b981', label: 'Esmeralda' },
  { value: '#14b8a6', label: 'Turquesa' },
  { value: '#06b6d4', label: 'Cian' },
  { value: '#0ea5e9', label: 'Azul cielo' },
  { value: '#3b82f6', label: 'Azul' },
  { value: '#6366f1', label: 'Índigo' },
  { value: '#8b5cf6', label: 'Violeta' },
  { value: '#a855f7', label: 'Púrpura' },
  { value: '#d946ef', label: 'Fucsia' },
  { value: '#ec4899', label: 'Rosa' },
  { value: '#64748b', label: 'Pizarra' },
] as const

/**
 * Iconos predefinidos para workspaces (lucide-react)
 */
export const WORKSPACE_ICONS = [
  'folder',
  'folder-open',
  'briefcase',
  'archive',
  'bookmark',
  'star',
  'heart',
  'flag',
  'target',
  'award',
  'layers',
  'package',
  'inbox',
  'file-text',
  'clipboard',
] as const

export type WorkspaceIconType = typeof WORKSPACE_ICONS[number]
