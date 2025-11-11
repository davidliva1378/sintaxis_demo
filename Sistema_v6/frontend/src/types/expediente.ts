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

// Alias para compatibilidad con el store
export type ExpedienteResumen = ExpedienteListado;

export interface Actuacion {
  indice: number;
  oficina: string;
  oficina_completa: string;
  fecha: string;
  tipo: string;
  detalle: string;
  foja: string;
  archivo: string | null;
  nombre_archivo: string | null;
  tiene_archivo: boolean;
  tipo_archivo: string | null;
  hash: string | null;
  extraida_en: string | null;
  es_historica: boolean;
  descargado: boolean;
}

export interface ExpedienteDetalle extends ExpedienteListado {
  actuaciones: Actuacion[];
  total_actuaciones: number;
  fecha_extraccion: string;
}

export interface SolicitudExtraccion {
  numero: string;
  anio: string;
  dependencia?: string;
}

export interface PaginacionResult<T> {
  items: T[];
  total: number;
  pagina: number;
  por_pagina: number;
  total_paginas: number;
}

/**
 * Configuración para la extracción masiva de expedientes.
 * Todos los campos son opcionales y tienen valores por defecto en el backend.
 */
export interface ConfigExtraccion {
  /** Ejecutar navegador sin interfaz gráfica (más rápido). Default: true */
  headless?: boolean;

  /** Número de errores consecutivos antes de detener la extracción. Default: 10 */
  umbral_errores?: number;

  /** Timeout en milisegundos para cargar cada página. Default: 30000 */
  timeout_pagina?: number;

  /** Número máximo de reintentos por página fallida. Default: 3 */
  max_reintentos?: number;

  /** Formatos de exportación deseados. Default: ['json'] */
  exportar_formatos?: string[];

  /** Fecha de corte (YYYY-MM-DD). Solo extraer expedientes desde esta fecha */
  fecha_corte?: string;
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

// Alias para compatibilidad con el store
export type ExpedienteFiltros = FiltrosExpedientes;

/**
 * Estado de selección de expedientes
 */
export interface SeleccionExpedientes {
  seleccionados: Set<string>;
  total: number;
  expedientes: ExpedienteListado[];
}
