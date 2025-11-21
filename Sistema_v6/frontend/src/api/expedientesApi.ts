/**
 * API client para endpoints de Expedientes
 * Maneja texto extraido y otras funcionalidades de actuaciones
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

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
