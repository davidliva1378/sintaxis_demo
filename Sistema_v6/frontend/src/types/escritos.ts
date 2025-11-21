/**
 * Tipos para el modulo Escritos
 */

export type EstadoEscrito = 'borrador' | 'revision' | 'presentado' | 'confirmado'

export interface Plantilla {
  id: number
  user_id: number
  nombre: string
  descripcion: string | null
  contenido: string
  variables: string[]
  categoria: string
  es_publica: boolean
  created_at: string
  updated_at: string
}

export interface PlantillaCreate {
  nombre: string
  descripcion?: string | null
  contenido: string
  variables?: string[]
  categoria?: string
  es_publica?: boolean
}

export interface PlantillaUpdate {
  nombre?: string
  descripcion?: string | null
  contenido?: string
  variables?: string[]
  categoria?: string
  es_publica?: boolean
}

export interface Escrito {
  id: number
  user_id: number
  expediente_numero: string | null
  plantilla_id: number | null
  titulo: string
  contenido: string
  estado: EstadoEscrito
  fecha_presentacion: string | null
  numero_escrito: string | null
  notas: string | null
  created_at: string
  updated_at: string
}

export interface EscritoCreate {
  expediente_numero?: string | null
  plantilla_id?: number | null
  titulo: string
  contenido: string
  notas?: string | null
}

export interface EscritoUpdate {
  expediente_numero?: string | null
  titulo?: string
  contenido?: string
  estado?: EstadoEscrito
  fecha_presentacion?: string | null
  numero_escrito?: string | null
  notas?: string | null
}

export interface EstadisticasEscritos {
  total_escritos: number
  borradores: number
  en_revision: number
  presentados: number
  confirmados: number
  expedientes_con_escritos: number
}

export interface VersionEscrito {
  id: number
  escrito_id?: number
  version: number
  contenido?: string
  comentario: string | null
  created_at: string
}

export interface FiltrosEscritos {
  expediente?: string
  estado?: EstadoEscrito
  limit?: number
  offset?: number
}
