/**
 * Tipos de datos para expedientes y extracción masiva.
 */

export interface ExpedienteListado {
  numero: string;
  caratula: string;
  dependencia: string;
  situacion: string;
  fecha_inicio: string;
  ultima_actuacion: string;
}

export interface ConfigExtraccion {
  headless?: boolean;
  umbral_errores?: number;
  timeout_pagina?: number;
  max_reintentos?: number;
}

export interface Comparacion {
  total_nuevo: number;
  total_base: number;
  nuevos: number;
  eliminados: number;
  comunes: number;
  listado_base_path: string;
  expedientes_nuevos: string[];
  expedientes_eliminados: string[];
}

export interface ListadoResponse {
  session_id: string;
  estado: string;
  total: number;
  listado_path: string;
  comparacion?: Comparacion;
  mensaje: string;
}

export interface ResumenExtraccion {
  total: number;
  exitosos: number;
  errores: number;
  omitidos: number;
  tiempo_total: number;
  tasa_exito: number;
  errores_detalles: Array<{
    numero: string;
    error: string;
  }>;
}

export interface SesionExtraccion {
  session_id: string;
  estado: string;
  fase: string;
  tiempo_inicio: string;
  tiempo_fin?: string;
  config: Record<string, unknown>;
  progreso_actual: number;
  progreso_total: number;
  mensaje: string;
  listado_path?: string;
  comparacion?: Comparacion;
}

/**
 * Filtros disponibles para expedientes
 */
export interface FiltrosExpedientes {
  // Filtros de texto
  numero?: string;
  caratula?: string;

  // Filtros de selección
  dependencia?: string[];
  situacion?: string[];

  // Filtros de fecha
  fecha_inicio_desde?: string;
  fecha_inicio_hasta?: string;
  ultima_actuacion_desde?: string;
  ultima_actuacion_hasta?: string;
}

/**
 * Estado de selección de expedientes
 */
export interface SeleccionExpedientes {
  seleccionados: Set<string>;
  total: number;
  expedientes: ExpedienteListado[];
}
