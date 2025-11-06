// Tipos para el módulo de Expedientes
// Basados en las entidades del dominio del backend

export interface ExpedienteResumen {
  numero: string
  dependencia: string
  caratula: string
  situacion: string | null
  ultima_actuacion: string | null
}

export interface ExpedienteIdentificacion {
  numero: string
  anio: string
}

export interface Actuacion {
  indice: number
  oficina: string
  oficina_completa: string | null
  fecha: string | null
  tipo: string | null
  detalle: string | null
  foja: string | null
  archivo: string | null
  nombre_archivo: string | null
  tiene_archivo: boolean
  tipo_archivo: string | null
  hash: string | null
  extraida_en: string | null
  es_historica: boolean
  descargado: boolean
}

export interface ExpedienteDetalle extends ExpedienteResumen {
  actuaciones: Actuacion[]
  total_actuaciones: number
  fecha_extraccion: string | null
}

// Tipos para filtros y búsqueda
export interface ExpedienteFiltros {
  numero?: string
  caratula?: string
  dependencia?: string
  situacion?: string
  fecha_desde?: string
  fecha_hasta?: string
  tiene_actuaciones_recientes?: boolean
}

// Tipos para paginación
export interface PaginacionParams {
  pagina: number
  por_pagina: number
}

export interface PaginacionResult<T> {
  items: T[]
  total: number
  pagina: number
  por_pagina: number
  total_paginas: number
}

// Tipo para solicitud de extracción
export interface SolicitudExtraccion {
  numero: string
  anio: string
  dependencia?: string
  tipo?: 'completo' | 'resumen'
}

// Tipos para estadísticas
export interface EstadisticasExpedientes {
  total: number
  activos: number
  con_actuaciones_recientes: number
  por_dependencia: Record<string, number>
  por_situacion: Record<string, number>
}
