/**
 * API Client para funciones de administración del sistema.
 */

import { apiClient } from './client'
import {
  EstadisticasSistema,
  ResultadoReseteo,
  BackupInfo,
  ResetRequest,
  EstadoSincronizacion,
  ComparacionSincronizacion,
  ResultadoSincronizacion,
  ExpedienteMySQL,
} from '@/types/admin'

export const adminApi = {
  /**
   * Obtiene estadísticas del sistema.
   */
  async getEstadisticas(): Promise<EstadisticasSistema> {
    const response = await apiClient.get<EstadisticasSistema>('/api/v1/admin/stats')
    return response.data
  },

  /**
   * Ejecuta un reseteo del sistema.
   */
  async resetearSistema(request: ResetRequest): Promise<ResultadoReseteo> {
    const response = await apiClient.post<ResultadoReseteo>('/api/v1/admin/reset', request)
    return response.data
  },

  /**
   * Lista todos los backups disponibles.
   */
  async listarBackups(): Promise<BackupInfo[]> {
    const response = await apiClient.get<BackupInfo[]>('/api/v1/admin/backups')
    return response.data
  },

  /**
   * Restaura un backup específico.
   */
  async restaurarBackup(backupId: string): Promise<{ mensaje: string }> {
    const response = await apiClient.post<{ mensaje: string }>(`/api/v1/admin/restore/${backupId}`)
    return response.data
  },

  /**
   * Limpia el cache del sistema.
   */
  async limpiarCache(): Promise<{
    mensaje: string
    archivos_eliminados: number
    espacio_liberado_mb: number
  }> {
    const response = await apiClient.delete<{
      mensaje: string
      archivos_eliminados: number
      espacio_liberado_mb: number
    }>('/api/v1/admin/cache')
    return response.data
  },

  // === Funciones de Sincronización MySQL ===

  /**
   * Obtiene el estado de sincronización JSON vs MySQL.
   */
  async getEstadoSincronizacion(): Promise<EstadoSincronizacion> {
    const response = await apiClient.get<EstadoSincronizacion>('/api/v1/admin/sincronizacion/estado')
    return response.data
  },

  /**
   * Compara en detalle JSON vs MySQL.
   */
  async compararSincronizacion(limite?: number): Promise<ComparacionSincronizacion> {
    const params = limite ? { limite } : {}
    const response = await apiClient.get<ComparacionSincronizacion>('/api/v1/admin/sincronizacion/comparar', { params })
    return response.data
  },

  /**
   * Ejecuta sincronización masiva desde JSON a MySQL.
   */
  async ejecutarSincronizacion(): Promise<ResultadoSincronizacion> {
    const response = await apiClient.post<ResultadoSincronizacion>('/api/v1/admin/sincronizacion/ejecutar')
    return response.data
  },

  /**
   * Lista expedientes desde MySQL.
   */
  async getExpedientesMySQL(params?: {
    estado?: string
    limite?: number
    offset?: number
  }): Promise<ExpedienteMySQL[]> {
    const response = await apiClient.get<ExpedienteMySQL[]>('/api/v1/admin/expedientes-mysql', { params })
    return response.data
  },

  /**
   * Obtiene el conteo de expedientes en MySQL.
   */
  async contarExpedientesMySQL(estado?: string): Promise<{ count: number; estado: string | null }> {
    const params = estado ? { estado } : {}
    const response = await apiClient.get<{ count: number; estado: string | null }>('/api/v1/admin/expedientes-mysql/count', { params })
    return response.data
  },
}
