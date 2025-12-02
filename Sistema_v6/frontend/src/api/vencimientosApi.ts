/**
 * API client para vencimientos globales
 */

import { apiClient } from './client'
import type {
  VencimientoUrgente,
  FiltrosVencimientos,
  EstadisticasVencimientosSimple
} from '@/types/vencimiento'
import { FILTROS_TEMPORALES } from '@/types/vencimiento'

// Re-exportar tipos para compatibilidad
export type { VencimientoUrgente, FiltrosVencimientos }
export { FILTROS_TEMPORALES }
export type FiltroTemporalKey = keyof typeof FILTROS_TEMPORALES

// Alias para compatibilidad
export type VencimientoGlobal = VencimientoUrgente
export type EstadisticasVencimientos = EstadisticasVencimientosSimple

export interface VencimientosResponse {
  vencimientos: VencimientoUrgente[]
  total: number
  filtros_aplicados?: {
    dias_desde: number
    dias_hasta: number
    ocultarVencidos: boolean
  }
}

// === API ===

export const vencimientosApi = {
  /**
   * Obtiene vencimientos globales con filtros (filtrado en backend)
   */
  async getVencimientos(filtros: FiltrosVencimientos = {}): Promise<VencimientosResponse> {
    // Construir parámetros para el endpoint /api/v1/vencimientos
    const params: Record<string, string | number | boolean> = {
      limite: filtros.limite ?? 100,
      offset: filtros.offset ?? 0,
    }

    // Filtros de expediente
    if (filtros.expediente || filtros.expediente_numero) {
      params.expediente = filtros.expediente || filtros.expediente_numero || ''
    }

    // Filtros de fechas
    if (filtros.dias_desde !== undefined && filtros.dias_hasta !== undefined) {
      // Calcular fechas desde/hasta basado en días relativos
      const hoy = new Date()
      const desde = new Date(hoy)
      desde.setDate(hoy.getDate() + filtros.dias_desde)
      const hasta = new Date(hoy)
      hasta.setDate(hoy.getDate() + filtros.dias_hasta)

      params.desde = desde.toISOString().split('T')[0]
      params.hasta = hasta.toISOString().split('T')[0]
    } else if (filtros.fecha_desde) {
      params.desde = filtros.fecha_desde
    }
    if (filtros.fecha_hasta) {
      params.hasta = filtros.fecha_hasta
    }

    // Filtro de estado
    if (filtros.estado) {
      params.estado = filtros.estado
    }

    // Filtro de tipo
    if (filtros.tipo) {
      params.tipo = filtros.tipo
    }

    // Filtro de urgencia
    if (filtros.nivel_urgencia && filtros.nivel_urgencia !== 'todos') {
      params.urgencia = filtros.nivel_urgencia
    }

    // Solo pendientes si se ocultan vencidos
    if (filtros.ocultarVencidos) {
      params.solo_pendientes = true
    }

    const response = await apiClient.get<{ vencimientos: VencimientoGlobal[], total: number }>(
      '/api/v1/vencimientos',
      { params }
    )

    return {
      vencimientos: response.data.vencimientos || [],
      total: response.data.total,
      filtros_aplicados: {
        dias_desde: filtros.dias_desde ?? -7,
        dias_hasta: filtros.dias_hasta ?? 7,
        ocultarVencidos: filtros.ocultarVencidos ?? false
      }
    }
  },

  /**
   * Obtiene estadísticas de vencimientos desde el backend
   */
  async getEstadisticas(): Promise<EstadisticasVencimientos> {
    try {
      // Intentar usar el endpoint de estadísticas si existe
      const response = await apiClient.get<{
        total: number
        pendientes: number
        vencidos: number
        atendidos: number
        cancelados: number
        criticos_hoy: number
        urgentes_3_dias: number
        proximos_7_dias: number
        por_tipo: Record<string, number>
      }>('/api/v1/vencimientos/estadisticas')

      // Mapear a formato simple
      return {
        total: response.data.total,
        vencidos: response.data.vencidos,
        criticos: response.data.criticos_hoy,
        urgentes: response.data.urgentes_3_dias,
        proximos: response.data.proximos_7_dias,
        normales: response.data.total - response.data.vencidos - response.data.criticos_hoy -
                  response.data.urgentes_3_dias - response.data.proximos_7_dias
      }
    } catch {
      // Fallback: calcular desde vencimientos
      const response = await this.getVencimientos({ dias_desde: -30, dias_hasta: 30, limite: 500 })

      const stats: EstadisticasVencimientos = {
        total: response.total,
        vencidos: 0,
        criticos: 0,
        urgentes: 0,
        proximos: 0,
        normales: 0
      }

      for (const v of response.vencimientos) {
        switch (v.nivel_urgencia) {
          case 'vencido': stats.vencidos++; break
          case 'critico': stats.criticos++; break
          case 'urgente': stats.urgentes++; break
          case 'proximo': stats.proximos++; break
          default: stats.normales++
        }
      }

      return stats
    }
  },

  /**
   * Obtiene vencimientos para un expediente específico
   */
  async getVencimientosExpediente(expedienteNumero: string): Promise<VencimientoGlobal[]> {
    try {
      // Usar endpoint específico si existe
      const response = await apiClient.get<{ vencimientos: VencimientoGlobal[] }>(
        `/api/v1/vencimientos/expediente/${encodeURIComponent(expedienteNumero)}`
      )
      return response.data.vencimientos || []
    } catch {
      // Fallback: usar filtro general
      const response = await this.getVencimientos({
        expediente: expedienteNumero,
        dias_desde: -30,
        dias_hasta: 60,
        limite: 100
      })
      return response.vencimientos
    }
  },

  /**
   * Elimina un vencimiento
   */
  async eliminarVencimiento(id: number): Promise<void> {
    await apiClient.delete(`/api/v1/vencimientos/${id}`)
  },

  /**
   * Marca un vencimiento como atendido
   */
  async atenderVencimiento(id: number, notas?: string): Promise<void> {
    await apiClient.post(`/api/v1/vencimientos/${id}/atender`, null, {
      params: notas ? { notas } : undefined
    })
  },

  /**
   * Cancela un vencimiento
   */
  async cancelarVencimiento(id: number, notas?: string): Promise<void> {
    await apiClient.post(`/api/v1/vencimientos/${id}/cancelar`, null, {
      params: notas ? { notas } : undefined
    })
  }
}

export default vencimientosApi
