import { create } from 'zustand'
import { toast } from 'sonner'
import apiClient from '@/lib/api'
import type {
  ExpedienteResumen,
  ExpedienteDetalle,
  ExpedienteFiltros,
  SolicitudExtraccion,
  PaginacionResult,
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
  isExtractingMasivo: boolean

  // Acciones
  listarExpedientes: (filtros?: ExpedienteFiltros, pagina?: number) => Promise<void>
  obtenerExpediente: (numero: string) => Promise<void>
  extraerExpediente: (solicitud: SolicitudExtraccion) => Promise<void>
  extraerExpedientesMasivamente: (
    usuario?: string,
    contrasena?: string,
    procesarConPDF?: boolean,
    onProgress?: (mensaje: string) => void
  ) => Promise<ExpedienteResumen[]>
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
  isExtractingMasivo: false,

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

      // Nota: Este endpoint será implementado en el backend en futuras fases
      // Por ahora, devolver datos de ejemplo
      const mockData: PaginacionResult<ExpedienteResumen> = {
        items: [
          {
            numero: 'JUZ-FAM-2024-0123',
            dependencia: 'JUZGADO DE FAMILIA N°1',
            caratula: 'PEREZ, JUAN C/ GOMEZ, MARIA S/ DIVORCIO',
            situacion: 'EN TRAMITE',
            ultima_actuacion: '2025-01-15',
          },
          {
            numero: 'JUZ-CIV-2024-0456',
            dependencia: 'JUZGADO CIVIL N°2',
            caratula: 'RODRIGUEZ, CARLOS C/ MARTINEZ, ANA S/ DAÑOS Y PERJUICIOS',
            situacion: 'SENTENCIA',
            ultima_actuacion: '2025-01-10',
          },
          {
            numero: 'JUZ-LAB-2024-0789',
            dependencia: 'JUZGADO LABORAL N°3',
            caratula: 'LOPEZ, MARIA C/ EMPRESA XYZ S.A. S/ DESPIDO',
            situacion: 'EN TRAMITE',
            ultima_actuacion: '2025-01-05',
          },
        ],
        total: 3,
        pagina: currentPagina,
        por_pagina: get().paginacion.por_pagina,
        total_paginas: 1,
      }

      set({
        expedientes: mockData.items,
        paginacion: {
          pagina: mockData.pagina,
          por_pagina: mockData.por_pagina,
          total: mockData.total,
          total_paginas: mockData.total_paginas,
        },
        filtros: currentFiltros,
      })

      // Implementación real (comentada para futuras fases):
      // const response = await apiClient.get<PaginacionResult<ExpedienteResumen>>(
      //   '/api/v1/expedientes',
      //   { params }
      // )
      // set({
      //   expedientes: response.data.items,
      //   paginacion: {
      //     pagina: response.data.pagina,
      //     por_pagina: response.data.por_pagina,
      //     total: response.data.total,
      //     total_paginas: response.data.total_paginas,
      //   },
      //   filtros: currentFiltros,
      // })
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
      // Datos de ejemplo (será reemplazado con llamada real al backend)
      const mockExpediente: ExpedienteDetalle = {
        numero: numero,
        dependencia: 'JUZGADO DE FAMILIA N°1',
        caratula: 'PEREZ, JUAN C/ GOMEZ, MARIA S/ DIVORCIO',
        situacion: 'EN TRAMITE',
        ultima_actuacion: '2025-01-15',
        actuaciones: [
          {
            indice: 1,
            oficina: 'JUZGADO FAM N°1',
            oficina_completa: 'JUZGADO DE FAMILIA N°1',
            fecha: '2024-01-10',
            tipo: 'SENTENCIA',
            detalle: 'Se dicta sentencia favorable',
            foja: '125',
            archivo: null,
            nombre_archivo: null,
            tiene_archivo: false,
            tipo_archivo: null,
            hash: null,
            extraida_en: null,
            es_historica: false,
            descargado: false,
          },
          {
            indice: 2,
            oficina: 'JUZGADO FAM N°1',
            oficina_completa: 'JUZGADO DE FAMILIA N°1',
            fecha: '2024-01-15',
            tipo: 'RESOLUCION',
            detalle: 'Se notifica a las partes',
            foja: '126',
            archivo: '/archivos/123.pdf',
            nombre_archivo: 'resolucion_123.pdf',
            tiene_archivo: true,
            tipo_archivo: 'pdf',
            hash: 'abc123',
            extraida_en: '2024-01-16T10:00:00',
            es_historica: false,
            descargado: false,
          },
        ],
        total_actuaciones: 2,
        fecha_extraccion: '2025-01-16T10:00:00',
      }

      set({ expedienteActual: mockExpediente })

      // Implementación real (comentada para futuras fases):
      // const response = await apiClient.get<ExpedienteDetalle>(
      //   `/api/v1/expedientes/${numero}`
      // )
      // set({ expedienteActual: response.data })
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

      // Implementación real (comentada para futuras fases):
      // const response = await apiClient.post<ExpedienteDetalle>(
      //   '/api/v1/expedientes/extraer',
      //   solicitud
      // )
      // set({ expedienteActual: response.data })

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

  // Extracción masiva de expedientes del PJN
  extraerExpedientesMasivamente: async (
    usuario?: string,
    contrasena?: string,
    procesarConPDF: boolean = false,
    onProgress?: (mensaje: string) => void
  ): Promise<ExpedienteResumen[]> => {
    set({ isExtractingMasivo: true })
    try {
      onProgress?.('🔄 Iniciando extracción masiva de expedientes del PJN...')

      // Llamada al backend
      const response = await apiClient.post('/api/v1/expedientes/extraer', {
        usuario,
        contrasena,
        headless: true,
        // Nota: procesarConPDF se implementará en una futura fase
      })

      onProgress?.(`✅ Extracción completada: ${response.data.total} expedientes`)

      // Obtener la lista completa de expedientes del backend
      onProgress?.('📊 Obteniendo lista actualizada...')
      const listResponse = await apiClient.get('/api/v1/expedientes')

      if (listResponse.data.success) {
        const expedientes = listResponse.data.expedientes
        onProgress?.(`✅ Lista actualizada: ${expedientes.length} expedientes disponibles`)

        // Actualizar el store con los expedientes
        set({ expedientes })

        toast.success('Extracción masiva completada', {
          description: `${expedientes.length} expedientes extraídos exitosamente`,
        })

        return expedientes
      } else {
        throw new Error(listResponse.data.error || 'Error al obtener lista de expedientes')
      }
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || error.response?.data?.error || 'Error al extraer expedientes'
      onProgress?.(`❌ Error: ${errorMsg}`)

      toast.error('Error en extracción masiva', {
        description: errorMsg,
      })

      throw error
    } finally {
      set({ isExtractingMasivo: false })
    }
  },
}))
