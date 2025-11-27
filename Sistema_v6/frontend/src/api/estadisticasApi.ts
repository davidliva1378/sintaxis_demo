/**
 * API client para estadísticas globales del sistema
 */

import { apiClient } from './client'
import { ragApi } from './ragApi'
import { vencimientosApi } from './vencimientosApi'

// === Tipos ===

export interface EstadisticasGenerales {
  expedientes: {
    total: number
    monitoreados: number
    con_ia: number
    procesados_hoy: number
  }
  actuaciones: {
    total: number
    con_entidades: number
    indexadas_rag: number
  }
  entidades: {
    total: number
    por_tipo: Record<string, number>
  }
  vencimientos: {
    total: number
    vencidos: number
    criticos: number
    urgentes: number
    proximos: number
  }
  rag: {
    documentos_indexados: number
    coleccion: string
    bm25_documentos: number
  }
  sistema: {
    uptime?: string
    version: string
    ultima_sincronizacion?: string
  }
}

export interface TendenciaItem {
  fecha: string
  valor: number
}

export interface EstadisticasTendencias {
  actuaciones_por_dia: TendenciaItem[]
  expedientes_por_mes: TendenciaItem[]
  entidades_por_semana: TendenciaItem[]
}

export interface TopExpediente {
  numero: string
  caratula: string
  total_actuaciones: number
  total_entidades: number
  ultima_actuacion: string
}

// === API ===

export const estadisticasApi = {
  /**
   * Obtiene estadísticas generales del sistema
   * Combina datos de múltiples endpoints
   */
  async getEstadisticasGenerales(): Promise<EstadisticasGenerales> {
    // Ejecutar requests en paralelo
    const [
      dashboardRes,
      ragStatsRes,
      vencimientosRes,
    ] = await Promise.allSettled([
      apiClient.get<any>('/api/v1/dashboard/resumen'),
      ragApi.getStats().catch(() => null),
      vencimientosApi.getEstadisticas().catch(() => null),
    ])

    // Extraer datos del dashboard
    const dashboard = dashboardRes.status === 'fulfilled' ? dashboardRes.value.data : {}
    const ragStats = ragStatsRes.status === 'fulfilled' ? ragStatsRes.value : null
    const vencStats = vencimientosRes.status === 'fulfilled' ? vencimientosRes.value : null

    return {
      expedientes: {
        total: dashboard.total_expedientes || 0,
        monitoreados: dashboard.expedientes_monitoreados || 0,
        con_ia: dashboard.expedientes_con_ia || 0,
        procesados_hoy: dashboard.procesados_hoy || 0,
      },
      actuaciones: {
        total: dashboard.total_actuaciones || 0,
        con_entidades: dashboard.actuaciones_con_entidades || 0,
        indexadas_rag: ragStats?.bm25?.total_documents || 0,
      },
      entidades: {
        total: dashboard.total_entidades || 0,
        por_tipo: dashboard.entidades_por_tipo || {},
      },
      vencimientos: {
        total: vencStats?.total || 0,
        vencidos: vencStats?.vencidos || 0,
        criticos: vencStats?.criticos || 0,
        urgentes: vencStats?.urgentes || 0,
        proximos: vencStats?.proximos || 0,
      },
      rag: {
        documentos_indexados: ragStats?.qdrant?.count || 0,
        coleccion: ragStats?.qdrant?.collection || 'actuaciones',
        bm25_documentos: ragStats?.bm25?.total_documents || 0,
      },
      sistema: {
        version: 'v6.0.0',
        ultima_sincronizacion: dashboard.ultima_sincronizacion,
      }
    }
  },

  /**
   * Obtiene los expedientes más activos
   */
  async getTopExpedientes(limite: number = 10): Promise<TopExpediente[]> {
    try {
      const response = await apiClient.get<any>(`/api/v1/dashboard/top-expedientes?limite=${limite}`)
      return response.data.expedientes || []
    } catch {
      return []
    }
  },

  /**
   * Obtiene actividad reciente del sistema
   */
  async getActividadReciente(limite: number = 20): Promise<any[]> {
    try {
      const response = await apiClient.get<any>(`/api/v1/dashboard/actividad-reciente?limite=${limite}`)
      return response.data.actividad || []
    } catch {
      return []
    }
  },

  /**
   * Health check de todos los servicios
   */
  async getHealthStatus(): Promise<{
    backend: boolean
    database: boolean
    rag: boolean
    ollama: boolean
  }> {
    const [healthRes, ragHealthRes] = await Promise.allSettled([
      apiClient.get<any>('/api/v1/health'),
      ragApi.healthCheck().catch(() => null),
    ])

    const health = healthRes.status === 'fulfilled' ? healthRes.value.data : {}
    const ragHealth = ragHealthRes.status === 'fulfilled' ? ragHealthRes.value : null

    return {
      backend: health.status === 'ok' || health.status === 'healthy',
      database: health.database === true || health.mysql === true,
      rag: ragHealth?.qdrant === true,
      ollama: ragHealth?.ollama === true,
    }
  }
}

export default estadisticasApi
