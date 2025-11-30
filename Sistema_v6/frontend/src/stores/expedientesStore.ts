import { create } from 'zustand'
import { toast } from 'sonner'
import apiClient from '@/lib/api'
import type {
  ExpedienteResumen,
  ExpedienteDetalle,
  ExpedienteFiltros,
  SolicitudExtraccion,
  Actuacion,
} from '@/types/expediente'

interface ExpedientesState {
  // Estado
  expedientes: ExpedienteResumen[]
  expedienteActual: ExpedienteDetalle | null
  filtros: ExpedienteFiltros
  paginacion: {
    pagina: number
    por_pagina: number
    total: number
    total_paginas: number
  }
  isLoading: boolean
  isExtracting: boolean

  // Acciones
  listarExpedientes: (filtros?: ExpedienteFiltros, pagina?: number) => Promise<void>
  obtenerExpediente: (numero: string) => Promise<void>
  extraerExpediente: (solicitud: SolicitudExtraccion) => Promise<void>
  setFiltros: (filtros: ExpedienteFiltros) => void
  limpiarFiltros: () => void
  setPagina: (pagina: number) => void
  limpiarExpedienteActual: () => void
}

export const useExpedientesStore = create<ExpedientesState>((set, get) => ({
  // Estado inicial
  expedientes: [],
  expedienteActual: null,
  filtros: {},
  paginacion: {
    pagina: 1,
    por_pagina: 20,
    total: 0,
    total_paginas: 0,
  },
  isLoading: false,
  isExtracting: false,

  // Listar expedientes con filtros y paginación
  listarExpedientes: async (filtros?: ExpedienteFiltros, pagina?: number) => {
    set({ isLoading: true })
    try {
      const currentFiltros = filtros !== undefined ? filtros : get().filtros
      const currentPagina = pagina !== undefined ? pagina : get().paginacion.pagina

      const params: Record<string, any> = {
        pagina: currentPagina,
        por_pagina: get().paginacion.por_pagina,
        ...currentFiltros,
      }

      // Llamada real al backend
      const response = await apiClient.get<{
        success: boolean
        total: number
        expedientes: ExpedienteResumen[]
        pagina: number
        por_pagina: number
        total_paginas: number
        error?: string
      }>('/api/v1/expedientes', { params })

      if (!response.data.success) {
        throw new Error(response.data.error || 'Error al cargar expedientes')
      }

      set({
        expedientes: response.data.expedientes,
        paginacion: {
          pagina: response.data.pagina,
          por_pagina: response.data.por_pagina,
          total: response.data.total,
          total_paginas: response.data.total_paginas,
        },
        filtros: currentFiltros,
      })
    } catch (error: any) {
      toast.error('Error al cargar expedientes', {
        description: error.response?.data?.detail || 'No se pudieron cargar los expedientes',
      })
      throw error
    } finally {
      set({ isLoading: false })
    }
  },

  // Obtener detalle de un expediente
  obtenerExpediente: async (numero: string) => {
    set({ isLoading: true })
    try {
      // Obtener expediente y actuaciones en paralelo
      const [expedienteResponse, actuacionesResponse] = await Promise.all([
        apiClient.get<{
          numero: string
          dependencia: string
          caratula: string
          situacion: string | null
          ultima_actuacion: string | null
        }>(`/api/v1/expedientes/${numero}`),
        apiClient.get<Actuacion[]>(`/api/v1/expedientes/${numero}/actuaciones`).catch(() => ({ data: [] })),
      ])

      // Convertir respuesta a ExpedienteDetalle
      const expedienteDetalle: ExpedienteDetalle = {
        numero: expedienteResponse.data.numero,
        dependencia: expedienteResponse.data.dependencia,
        caratula: expedienteResponse.data.caratula,
        situacion: expedienteResponse.data.situacion || 'SIN DATOS',
        ultima_actuacion: expedienteResponse.data.ultima_actuacion || '',
        fecha_inicio: '', // No disponible en el backend actual
        actuaciones: actuacionesResponse.data || [],
        total_actuaciones: (actuacionesResponse.data || []).length,
        fecha_extraccion: new Date().toISOString(),
      }

      set({ expedienteActual: expedienteDetalle })
    } catch (error: any) {
      toast.error('Error al cargar expediente', {
        description: error.response?.data?.detail || 'No se pudo cargar el expediente',
      })
      throw error
    } finally {
      set({ isLoading: false })
    }
  },

  // Extraer expediente del PJN
  extraerExpediente: async (solicitud: SolicitudExtraccion) => {
    set({ isExtracting: true })
    try {
      toast.info('Extrayendo expediente...', {
        description: `Expediente ${solicitud.numero}/${solicitud.anio}`,
      })

      // Simular extracción (para demostración)
      await new Promise((resolve) => setTimeout(resolve, 2000))

      const mockExpediente: ExpedienteDetalle = {
        numero: `${solicitud.numero}-${solicitud.anio}`,
        dependencia: solicitud.dependencia || 'JUZGADO FEDERAL N°1',
        caratula: 'EXPEDIENTE EXTRAÍDO DEL PJN',
        situacion: 'EN TRAMITE',
        ultima_actuacion: new Date().toISOString().split('T')[0],
        actuaciones: [],
        total_actuaciones: 0,
        fecha_extraccion: new Date().toISOString(),
        fecha_inicio: '', // Mock value
      }

      set({ expedienteActual: mockExpediente })

      toast.success('Expediente extraído exitosamente', {
        description: `Expediente ${solicitud.numero}/${solicitud.anio}`,
      })

      // Actualizar lista de expedientes
      await get().listarExpedientes()
    } catch (error: any) {
      toast.error('Error al extraer expediente', {
        description: error.response?.data?.detail || 'No se pudo extraer el expediente del PJN',
      })
      throw error
    } finally {
      set({ isExtracting: false })
    }
  },

  // Establecer filtros
  setFiltros: (filtros: ExpedienteFiltros) => {
    set({ filtros })
  },

  // Limpiar filtros
  limpiarFiltros: () => {
    set({ filtros: {} })
  },

  // Cambiar página
  setPagina: async (pagina: number) => {
    await get().listarExpedientes(get().filtros, pagina)
  },

  // Limpiar expediente actual
  limpiarExpedienteActual: () => {
    set({ expedienteActual: null })
  },
}))
