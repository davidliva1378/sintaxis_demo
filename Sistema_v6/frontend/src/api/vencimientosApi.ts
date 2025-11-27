/**
 * API client para vencimientos globales
 */

import { apiClient } from './client'
import type { VencimientoUrgente, NivelUrgencia } from '@/types/procesamiento'

// === Tipos ===

export interface VencimientoGlobal extends VencimientoUrgente {
  fecha_notificacion?: string
}

export interface FiltrosVencimientos {
  dias_desde?: number         // Desde hace X días (para incluir vencidos)
  dias_hasta?: number         // Hasta X días adelante
  nivel_urgencia?: NivelUrgencia | 'todos'
  ocultarVencidos?: boolean   // No mostrar ya vencidos
  expediente?: string         // Filtrar por expediente
  limite?: number
}

export interface VencimientosResponse {
  vencimientos: VencimientoGlobal[]
  total: number
  filtros_aplicados?: {
    dias_desde: number
    dias_hasta: number
    ocultarVencidos: boolean
  }
}

export interface EstadisticasVencimientos {
  total: number
  vencidos: number
  criticos: number
  urgentes: number
  proximos: number
  normales: number
}

// === Filtros predefinidos ===

export const FILTROS_TEMPORALES = {
  HOY: { label: 'Vence hoy', dias_desde: 0, dias_hasta: 0 },
  PROXIMOS_3_DIAS: { label: 'Próximos 3 días', dias_desde: 0, dias_hasta: 3 },
  PROXIMOS_7_DIAS: { label: 'Próximos 7 días', dias_desde: 0, dias_hasta: 7 },
  PROXIMOS_15_DIAS: { label: 'Próximos 15 días', dias_desde: 0, dias_hasta: 15 },
  PROXIMOS_30_DIAS: { label: 'Próximos 30 días', dias_desde: 0, dias_hasta: 30 },
  ULTIMOS_7_DIAS: { label: 'Últimos 7 días (vencidos)', dias_desde: -7, dias_hasta: 0 },
  TODOS: { label: 'Todos', dias_desde: -30, dias_hasta: 30 },
} as const

export type FiltroTemporalKey = keyof typeof FILTROS_TEMPORALES

// === API ===

export const vencimientosApi = {
  /**
   * Obtiene vencimientos globales con filtros
   */
  async getVencimientos(filtros: FiltrosVencimientos = {}): Promise<VencimientosResponse> {
    const params = new URLSearchParams()

    // El endpoint existente usa dias_adelante, calculamos basado en filtros
    const diasAdelante = filtros.dias_hasta ?? 7
    params.append('limite', String(filtros.limite ?? 100))

    const response = await apiClient.get<{ vencimientos: VencimientoGlobal[], total: number }>(
      `/api/v1/dashboard/vencimientos-urgentes?${params.toString()}`
    )

    let vencimientos = response.data.vencimientos || []

    // Aplicar filtros del lado del cliente
    if (filtros.dias_desde !== undefined) {
      vencimientos = vencimientos.filter(v => v.dias_restantes >= filtros.dias_desde!)
    }
    if (filtros.dias_hasta !== undefined) {
      vencimientos = vencimientos.filter(v => v.dias_restantes <= filtros.dias_hasta!)
    }
    if (filtros.ocultarVencidos) {
      vencimientos = vencimientos.filter(v => v.dias_restantes >= 0)
    }
    if (filtros.nivel_urgencia && filtros.nivel_urgencia !== 'todos') {
      vencimientos = vencimientos.filter(v => v.nivel_urgencia === filtros.nivel_urgencia)
    }
    if (filtros.expediente) {
      const exp = filtros.expediente.toLowerCase()
      vencimientos = vencimientos.filter(v =>
        v.expediente_numero.toLowerCase().includes(exp)
      )
    }

    return {
      vencimientos,
      total: vencimientos.length,
      filtros_aplicados: {
        dias_desde: filtros.dias_desde ?? -7,
        dias_hasta: filtros.dias_hasta ?? 7,
        ocultarVencidos: filtros.ocultarVencidos ?? false
      }
    }
  },

  /**
   * Obtiene estadísticas de vencimientos
   */
  async getEstadisticas(): Promise<EstadisticasVencimientos> {
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
  },

  /**
   * Obtiene vencimientos para un expediente específico
   */
  async getVencimientosExpediente(expedienteNumero: string): Promise<VencimientoGlobal[]> {
    const response = await this.getVencimientos({
      expediente: expedienteNumero,
      dias_desde: -30,
      dias_hasta: 60,
      limite: 100
    })
    return response.vencimientos
  }
}

export default vencimientosApi
