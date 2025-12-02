/**
 * Utilidades para manejo de errores type-safe
 */

import { AxiosError } from 'axios'

/**
 * Estructura de error de la API
 */
export interface ApiErrorResponse {
  detail: string
  status?: number
  code?: string
}

/**
 * Verifica si un error es un AxiosError
 */
export function isAxiosError(error: unknown): error is AxiosError<ApiErrorResponse> {
  return (
    typeof error === 'object' &&
    error !== null &&
    'isAxiosError' in error &&
    (error as AxiosError).isAxiosError === true
  )
}

/**
 * Extrae el mensaje de error de cualquier tipo de error
 * @param error - Error de cualquier tipo
 * @param defaultMessage - Mensaje por defecto si no se puede extraer
 * @returns Mensaje de error legible
 */
export function getErrorMessage(error: unknown, defaultMessage = 'Error desconocido'): string {
  // Error de Axios con respuesta del servidor
  if (isAxiosError(error)) {
    // Primero intentar obtener el mensaje del servidor
    const serverMessage = error.response?.data?.detail
    if (serverMessage && typeof serverMessage === 'string') {
      return serverMessage
    }

    // Si no hay respuesta del servidor, usar el mensaje de Axios
    if (error.message) {
      return error.message
    }
  }

  // Error estándar de JavaScript
  if (error instanceof Error) {
    return error.message
  }

  // String directamente
  if (typeof error === 'string') {
    return error
  }

  // Objeto con propiedad message
  if (
    typeof error === 'object' &&
    error !== null &&
    'message' in error &&
    typeof (error as { message: unknown }).message === 'string'
  ) {
    return (error as { message: string }).message
  }

  return defaultMessage
}

/**
 * Extrae el código de estado HTTP de un error
 */
export function getErrorStatus(error: unknown): number | undefined {
  if (isAxiosError(error)) {
    return error.response?.status
  }
  return undefined
}

/**
 * Verifica si es un error de red (sin conexión)
 */
export function isNetworkError(error: unknown): boolean {
  if (isAxiosError(error)) {
    return !error.response && error.code === 'ERR_NETWORK'
  }
  return false
}

/**
 * Verifica si es un error de timeout
 */
export function isTimeoutError(error: unknown): boolean {
  if (isAxiosError(error)) {
    return error.code === 'ECONNABORTED'
  }
  return false
}

/**
 * Verifica si es un error de autenticación (401)
 */
export function isAuthError(error: unknown): boolean {
  return getErrorStatus(error) === 401
}

/**
 * Verifica si es un error de permisos (403)
 */
export function isForbiddenError(error: unknown): boolean {
  return getErrorStatus(error) === 403
}

/**
 * Verifica si es un error de recurso no encontrado (404)
 */
export function isNotFoundError(error: unknown): boolean {
  return getErrorStatus(error) === 404
}
