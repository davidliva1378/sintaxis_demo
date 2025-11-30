/**
 * API client para endpoints de Expedientes
 * Maneja texto extraido y otras funcionalidades de actuaciones
 */

const API_BASE_URL = import.meta.env.VITE_API_URL

// ============================================================================
// Types
// ============================================================================

export interface TextoExtraidoResponse {
  tiene_texto: boolean
  texto_completo: string | null
  texto_normalizado: string | null
  preview: string | null
  metadata: {
    metodo_extraccion?: string
    total_paginas?: number
    total_caracteres?: number
    total_palabras?: number
    tiene_texto_embebido?: boolean
    tiene_tablas?: boolean
    tiene_imagenes?: boolean
    requirio_ocr?: boolean
    confianza_ocr?: number
    fecha_extraccion?: string
    [key: string]: unknown
  } | null
  texto_por_pagina: Array<{
    pagina: number
    contenido: string
    tipo: string
    caracteres: number
  }> | null
}

export interface ActuacionConAnalisisIA {
  id: number
  indice: number
  tipo: string
  detalle: string | null
  fecha: string | null
  tiene_texto_extraido: boolean
  tipo_ia: string | null
  confianza_ia: number | null
  justificacion_ia: string | null
  metodo_ia: string | null
  fecha_clasificacion_ia: string | null
  indexado_rag: boolean
}

export interface AnalisisIAExpedienteResponse {
  expediente_numero: string
  total_actuaciones: number
  actuaciones_con_ia: number
  actuaciones_indexadas: number
  porcentaje_clasificado: number
  porcentaje_indexado: number
  actuaciones: ActuacionConAnalisisIA[]
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Obtiene el texto extraido de una actuacion especifica
 */
export async function obtenerTextoActuacion(
  numeroExpediente: string,
  indiceActuacion: number
): Promise<TextoExtraidoResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/expedientes/${encodeURIComponent(numeroExpediente)}/actuaciones/${indiceActuacion}/texto`
  )

  if (!response.ok) {
    if (response.status === 404) {
      return {
        tiene_texto: false,
        texto_completo: null,
        texto_normalizado: null,
        preview: null,
        metadata: null,
        texto_por_pagina: null
      }
    }
    throw new Error(`Error ${response.status}: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Obtiene el PDF de una actuacion para descarga
 */
export async function descargarPdfActuacion(
  numeroExpediente: string,
  indiceActuacion: number
): Promise<Blob> {
  const response = await fetch(
    `${API_BASE_URL}/expedientes/${encodeURIComponent(numeroExpediente)}/actuaciones/${indiceActuacion}/pdf`
  )

  if (!response.ok) {
    throw new Error(`Error ${response.status}: ${response.statusText}`)
  }

  return response.blob()
}

/**
 * Obtiene el analisis IA de todas las actuaciones de un expediente
 */
export async function obtenerAnalisisIA(
  numeroExpediente: string
): Promise<AnalisisIAExpedienteResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/expedientes/${encodeURIComponent(numeroExpediente)}/analisis-ia`
  )

  if (!response.ok) {
    throw new Error(`Error ${response.status}: ${response.statusText}`)
  }

  return response.json()
}

// ============================================================================
// Inteligencia Types (nuevo endpoint consolidado)
// ============================================================================

export interface EntidadNormalizadaDTO {
  original: string
  normalized: string
  label: string
  score: number
  normalization_type?: string
}

export interface ParteProcesalDTO {
  nombre: string
  rol: string  // ACTOR, DEMANDADO, JUEZ, ABOGADO, PERITO
  abogado?: string
}

export interface AnalisisActuacionDTO {
  id: number
  tipo: string
  tipo_ia?: string
  confianza_ia?: number
  fecha?: string
  entidades: EntidadNormalizadaDTO[]
  indexado_rag: boolean
}

export interface InteligenciaExpedienteResponse {
  expediente_numero: string
  resumen_ejecutivo?: string
  partes_procesales: Record<string, ParteProcesalDTO[]>
  entidades_normalizadas: Record<string, EntidadNormalizadaDTO[]>
  analisis_actuaciones: AnalisisActuacionDTO[]
  total_actuaciones: number
  total_entidades: number
  actuaciones_con_ia: number
  actuaciones_indexadas: number
}

/**
 * Obtiene toda la inteligencia consolidada de un expediente
 * (partes procesales, entidades normalizadas, analisis IA)
 * @param signal - AbortSignal opcional para cancelar la request (timeout)
 */
export async function obtenerInteligenciaExpediente(
  numeroExpediente: string,
  signal?: AbortSignal
): Promise<InteligenciaExpedienteResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/expedientes/${encodeURIComponent(numeroExpediente)}/inteligencia`,
    { signal }
  )

  if (!response.ok) {
    throw new Error(`Error ${response.status}: ${response.statusText}`)
  }

  return response.json()
}
