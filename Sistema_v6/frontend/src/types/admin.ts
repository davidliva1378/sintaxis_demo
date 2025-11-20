/**
 * Tipos para administración del sistema.
 */

export enum NivelReseteo {
  LISTADOS = 'listados',
  PDFS = 'pdfs',
  EXPEDIENTES = 'expedientes',
  COMPLETO = 'completo',
  NUCLEAR = 'nuclear'
}

export interface EstadisticasSistema {
  espacio_total_mb: number
  expedientes_procesados: number
  pdfs_descargados: number
  sesiones_activas: number
  desglose: {
    extraccion_masiva_mb: number
    expedientes_mb: number
    cache_mb: number
    logs_mb: number
  }
  ultimo_backup: string | null
}

export interface ResultadoReseteo {
  nivel: string
  archivos_eliminados: number
  espacio_liberado_mb: number
  backup_path: string | null
  dry_run: boolean
  timestamp: string
  detalles: string[]
}

export interface BackupInfo {
  id: string
  nivel: string | null
  timestamp: string
  archivos: number
  size_mb: number
}

export interface ResetRequest {
  nivel: string
  confirmacion: string
  crear_backup?: boolean
  dry_run?: boolean
  incluir_procesamiento_mysql?: boolean
}

// Tipos para sincronización MySQL

export interface EstadoSincronizacion {
  total_json: number
  total_mysql: number
  sincronizados: number
  pendientes: number
  porcentaje_sincronizado: number
  ultima_sincronizacion: string | null
}

export interface DiferenciaSincronizacion {
  numero_normalizado: string
  estado: 'solo_json' | 'solo_mysql' | 'desincronizado'
  id_json: number | null
  id_mysql: number | null
}

export interface ComparacionSincronizacion {
  total_diferencias: number
  solo_en_json: number
  solo_en_mysql: number
  diferencias: DiferenciaSincronizacion[]
}

export interface ResultadoSincronizacion {
  procesados: number
  creados: number
  actualizados: number
  errores: number
  timestamp: string
}

export interface ExpedienteMySQL {
  id: number
  numero_normalizado: string
  numero_original: string
  dependencia: string | null
  caratula: string | null
  situacion: string | null
  estado_monitoreo: string
  prioridad: string
  fecha_creacion: string
  fecha_ultima_extraccion: string | null
  total_actuaciones: number
  total_pdfs_descargados: number
}
