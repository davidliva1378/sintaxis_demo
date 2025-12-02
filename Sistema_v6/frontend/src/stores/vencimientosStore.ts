/**
 * Store centralizado para gestión de vencimientos.
 *
 * Maneja el estado de vencimientos a nivel global, permitiendo:
 * - Consulta y filtrado de vencimientos
 * - Acciones sobre vencimientos (atender, cancelar)
 * - Estadísticas globales
 * - Sincronización con backend
 */

import { create } from 'zustand'
import { toast } from 'sonner'
import apiClient from '@/lib/api'
import type {
  Vencimiento,
  EstadisticasVencimientos,
  FiltrosVencimientos,
  NivelUrgencia
} from '@/types/vencimiento'
import { enriquecerVencimiento } from '@/types/vencimiento'

// Re-exportar tipos para compatibilidad
export type { Vencimiento, EstadisticasVencimientos, FiltrosVencimientos, NivelUrgencia }

// ============================================================================
// Estado del Store
// ============================================================================

interface VencimientosState {
  // Estado
  vencimientos: Vencimiento[]
  estadisticas: EstadisticasVencimientos | null
  filtros: FiltrosVencimientos
  paginacion: {
    pagina: number
    por_pagina: number
    total: number
    total_paginas: number
  }
  isLoading: boolean
  isUpdating: boolean
  llmStatus: {
    disponible: boolean
    modelo: string | null
    error: string | null
  } | null

  // Acciones de consulta
  listarVencimientos: (filtros?: FiltrosVencimientos, pagina?: number) => Promise<void>
  obtenerEstadisticas: () => Promise<void>
  obtenerVencimientosExpediente: (numero: string) => Promise<Vencimiento[]>

  // Acciones de modificación
  atenderVencimiento: (id: number) => Promise<void>
  cancelarVencimiento: (id: number, motivo?: string) => Promise<void>
  eliminarVencimiento: (id: number) => Promise<void>

  // Acciones de utilidad
  setFiltros: (filtros: FiltrosVencimientos) => void
  limpiarFiltros: () => void
  setPagina: (pagina: number) => Promise<void>
  verificarLLMStatus: () => Promise<void>
  refrescar: () => Promise<void>
}

// ============================================================================
// Store
// ============================================================================

export const useVencimientosStore = create<VencimientosState>((set, get) => ({
  // Estado inicial
  vencimientos: [],
  estadisticas: null,
  filtros: {},
  paginacion: {
    pagina: 1,
    por_pagina: 20,
    total: 0,
    total_paginas: 0,
  },
  isLoading: false,
  isUpdating: false,
  llmStatus: null,

  // Listar vencimientos con filtros
  listarVencimientos: async (filtros?: FiltrosVencimientos, pagina?: number) => {
    set({ isLoading: true })
    try {
      const currentFiltros = filtros !== undefined ? filtros : get().filtros
      const currentPagina = pagina !== undefined ? pagina : get().paginacion.pagina

      const params: Record<string, any> = {
        pagina: currentPagina,
        por_pagina: get().paginacion.por_pagina,
        ...currentFiltros,
      }

      const response = await apiClient.get<{
        vencimientos: any[]
        total: number
        pagina: number
        por_pagina: number
        total_paginas: number
      }>('/api/v1/vencimientos', { params })

      const vencimientosEnriquecidos = response.data.vencimientos.map(enriquecerVencimiento)

      set({
        vencimientos: vencimientosEnriquecidos,
        paginacion: {
          pagina: response.data.pagina,
          por_pagina: response.data.por_pagina,
          total: response.data.total,
          total_paginas: response.data.total_paginas,
        },
        filtros: currentFiltros,
      })
    } catch (error: any) {
      toast.error('Error al cargar vencimientos', {
        description: error.response?.data?.detail || 'No se pudieron cargar los vencimientos',
      })
      throw error
    } finally {
      set({ isLoading: false })
    }
  },

  // Obtener estadísticas
  obtenerEstadisticas: async () => {
    try {
      const response = await apiClient.get<EstadisticasVencimientos>(
        '/api/v1/vencimientos/estadisticas'
      )
      set({ estadisticas: response.data })
    } catch (error: any) {
      console.error('Error obteniendo estadísticas:', error)
    }
  },

  // Obtener vencimientos de un expediente
  obtenerVencimientosExpediente: async (numero: string) => {
    try {
      const response = await apiClient.get<{ vencimientos: any[] }>(
        `/api/v1/vencimientos/expediente/${numero}`
      )
      return response.data.vencimientos.map(enriquecerVencimiento)
    } catch (error: any) {
      console.error('Error obteniendo vencimientos del expediente:', error)
      return []
    }
  },

  // Atender vencimiento
  atenderVencimiento: async (id: number) => {
    set({ isUpdating: true })
    try {
      await apiClient.post(`/api/v1/vencimientos/${id}/atender`)

      toast.success('Vencimiento marcado como atendido')

      // Actualizar lista y estadísticas
      await Promise.all([get().listarVencimientos(), get().obtenerEstadisticas()])
    } catch (error: any) {
      toast.error('Error al atender vencimiento', {
        description: error.response?.data?.detail || 'No se pudo actualizar el vencimiento',
      })
      throw error
    } finally {
      set({ isUpdating: false })
    }
  },

  // Cancelar vencimiento
  cancelarVencimiento: async (id: number, motivo?: string) => {
    set({ isUpdating: true })
    try {
      await apiClient.post(`/api/v1/vencimientos/${id}/cancelar`, null, {
        params: motivo ? { motivo } : undefined,
      })

      toast.success('Vencimiento cancelado')

      // Actualizar lista y estadísticas
      await Promise.all([get().listarVencimientos(), get().obtenerEstadisticas()])
    } catch (error: any) {
      toast.error('Error al cancelar vencimiento', {
        description: error.response?.data?.detail || 'No se pudo cancelar el vencimiento',
      })
      throw error
    } finally {
      set({ isUpdating: false })
    }
  },

  // Eliminar vencimiento
  eliminarVencimiento: async (id: number) => {
    set({ isUpdating: true })
    try {
      await apiClient.delete(`/api/v1/vencimientos/${id}`)

      toast.success('Vencimiento eliminado')

      // Actualizar lista y estadísticas
      await Promise.all([get().listarVencimientos(), get().obtenerEstadisticas()])
    } catch (error: any) {
      toast.error('Error al eliminar vencimiento', {
        description: error.response?.data?.detail || 'No se pudo eliminar el vencimiento',
      })
      throw error
    } finally {
      set({ isUpdating: false })
    }
  },

  // Establecer filtros
  setFiltros: (filtros: FiltrosVencimientos) => {
    set({ filtros })
  },

  // Limpiar filtros
  limpiarFiltros: () => {
    set({ filtros: {} })
  },

  // Cambiar página
  setPagina: async (pagina: number) => {
    await get().listarVencimientos(get().filtros, pagina)
  },

  // Verificar estado del LLM
  verificarLLMStatus: async () => {
    try {
      const response = await apiClient.get<{
        disponible: boolean
        modelo_activo: string | null
        error: string | null
      }>('/api/v1/logs/llm/status')

      set({
        llmStatus: {
          disponible: response.data.disponible,
          modelo: response.data.modelo_activo,
          error: response.data.error,
        },
      })
    } catch (error) {
      set({
        llmStatus: {
          disponible: false,
          modelo: null,
          error: 'No se pudo verificar el estado del LLM',
        },
      })
    }
  },

  // Refrescar datos
  refrescar: async () => {
    await Promise.all([get().listarVencimientos(), get().obtenerEstadisticas()])
  },
}))
