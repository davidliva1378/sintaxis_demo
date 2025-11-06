/**
 * Store Zustand para gestión de Monitoreo
 */

import { create } from 'zustand'
import { toast } from 'sonner'
import type {
  ConfiguracionMonitoreo,
  ExpedienteMonitoreado,
  CambioDetectado,
  EstadisticasMonitoreo,
  SolicitudMonitorear,
  ActualizarMonitoreo,
  FrecuenciaMonitoreo,
} from '@/types/monitoreo'
// import apiClient from '@/lib/api'

interface MonitoreoState {
  // Estado
  configuracion: ConfiguracionMonitoreo | null
  expedientes: ExpedienteMonitoreado[]
  cambios: CambioDetectado[]
  estadisticas: EstadisticasMonitoreo | null
  isLoading: boolean

  // Acciones - Configuración
  obtenerConfiguracion: () => Promise<void>
  actualizarConfiguracion: (data: ActualizarMonitoreo) => Promise<void>
  toggleMonitoreo: (activo: boolean) => Promise<void>

  // Acciones - Expedientes Monitoreados
  listarExpedientes: () => Promise<void>
  agregarExpediente: (data: SolicitudMonitorear) => Promise<void>
  removerExpediente: (id: number) => Promise<void>
  toggleExpediente: (id: number, activo: boolean) => Promise<void>
  verificarExpediente: (id: number) => Promise<void>

  // Acciones - Cambios
  listarCambios: (expedienteId?: number) => Promise<void>
  marcarComoLeido: (id: number) => Promise<void>
  marcarTodosLeidos: () => Promise<void>

  // Acciones - Estadísticas
  obtenerEstadisticas: () => Promise<void>

  // Utilidades
  limpiar: () => void
}

export const useMonitoreoStore = create<MonitoreoState>((set, get) => ({
  // Estado inicial
  configuracion: null,
  expedientes: [],
  cambios: [],
  estadisticas: null,
  isLoading: false,

  // Obtener configuración del monitoreo
  obtenerConfiguracion: async () => {
    try {
      // TODO: Reemplazar con llamada real a la API
      // const response = await apiClient.get<ConfiguracionMonitoreo>('/api/v1/monitoreo/configuracion')
      // set({ configuracion: response.data })

      // Mock data por ahora
      await new Promise(resolve => setTimeout(resolve, 500))

      const mockConfig: ConfiguracionMonitoreo = {
        id: 1,
        usuario_id: 1,
        activo: true,
        frecuencia: '1hora',
        notificar_email: true,
        notificar_sistema: true,
        hora_inicio: '09:00',
        hora_fin: '18:00',
        dias_semana: [1, 2, 3, 4, 5], // Lunes a Viernes
        created_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
        updated_at: new Date().toISOString(),
      }

      set({ configuracion: mockConfig })
    } catch (error: any) {
      console.error('Error al obtener configuración:', error)
      toast.error('Error al cargar la configuración')
    }
  },

  // Actualizar configuración
  actualizarConfiguracion: async (data: ActualizarMonitoreo) => {
    try {
      // TODO: Reemplazar con llamada real a la API
      // const response = await apiClient.put<ConfiguracionMonitoreo>('/api/v1/monitoreo/configuracion', data)
      // set({ configuracion: response.data })

      // Mock data por ahora
      await new Promise(resolve => setTimeout(resolve, 500))

      set(state => ({
        configuracion: state.configuracion
          ? { ...state.configuracion, ...data, updated_at: new Date().toISOString() }
          : null,
      }))

      toast.success('Configuración actualizada correctamente')
    } catch (error: any) {
      console.error('Error al actualizar configuración:', error)
      toast.error('Error al actualizar la configuración')
    }
  },

  // Toggle monitoreo activo/pausado
  toggleMonitoreo: async (activo: boolean) => {
    try {
      // TODO: Reemplazar con llamada real a la API
      // await apiClient.patch('/api/v1/monitoreo/toggle', { activo })

      // Mock data por ahora
      await new Promise(resolve => setTimeout(resolve, 400))

      set(state => ({
        configuracion: state.configuracion
          ? { ...state.configuracion, activo, updated_at: new Date().toISOString() }
          : null,
      }))

      toast.success(activo ? 'Monitoreo activado' : 'Monitoreo pausado')
    } catch (error: any) {
      console.error('Error al cambiar estado del monitoreo:', error)
      toast.error('Error al cambiar el estado')
    }
  },

  // Listar expedientes monitoreados
  listarExpedientes: async () => {
    set({ isLoading: true })

    try {
      // TODO: Reemplazar con llamada real a la API
      // const response = await apiClient.get<ExpedienteMonitoreado[]>('/api/v1/monitoreo/expedientes')
      // set({ expedientes: response.data })

      // Mock data por ahora
      await new Promise(resolve => setTimeout(resolve, 700))

      const mockExpedientes: ExpedienteMonitoreado[] = [
        {
          id: 1,
          usuario_id: 1,
          expediente_numero: 'EXP-2024-123-CS',
          expediente_caratula: 'PÉREZ JUAN C/ GARCÍA MARÍA S/ DAÑOS Y PERJUICIOS',
          expediente_dependencia: 'Juzgado Civil 45 - Secretaría Única',
          activo: true,
          ultima_verificacion: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          ultima_actuacion_fecha: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
          total_cambios_detectados: 5,
          created_at: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString(),
          updated_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        },
        {
          id: 2,
          usuario_id: 1,
          expediente_numero: 'EXP-2024-456-CF',
          expediente_caratula: 'RODRÍGUEZ ANA C/ GÓMEZ PEDRO S/ DIVORCIO',
          expediente_dependencia: 'Juzgado de Familia 12 - Secretaría 2',
          activo: true,
          ultima_verificacion: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
          ultima_actuacion_fecha: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
          total_cambios_detectados: 12,
          created_at: new Date(Date.now() - 20 * 24 * 60 * 60 * 1000).toISOString(),
          updated_at: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
        },
        {
          id: 3,
          usuario_id: 1,
          expediente_numero: 'EXP-2024-789-CC',
          expediente_caratula: 'LÓPEZ CARLOS S/ QUIEBRA',
          expediente_dependencia: 'Juzgado Comercial 8 - Secretaría 1',
          activo: false,
          ultima_verificacion: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(),
          ultima_actuacion_fecha: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
          total_cambios_detectados: 3,
          created_at: new Date(Date.now() - 25 * 24 * 60 * 60 * 1000).toISOString(),
          updated_at: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(),
        },
      ]

      set({ expedientes: mockExpedientes })
    } catch (error: any) {
      console.error('Error al listar expedientes:', error)
      toast.error('Error al cargar expedientes monitoreados')
      set({ expedientes: [] })
    } finally {
      set({ isLoading: false })
    }
  },

  // Agregar expediente al monitoreo
  agregarExpediente: async (data: SolicitudMonitorear) => {
    try {
      // TODO: Reemplazar con llamada real a la API
      // const response = await apiClient.post<ExpedienteMonitoreado>('/api/v1/monitoreo/expedientes', data)
      // set(state => ({ expedientes: [...state.expedientes, response.data] }))

      // Mock data por ahora
      await new Promise(resolve => setTimeout(resolve, 500))

      const nuevoExpediente: ExpedienteMonitoreado = {
        id: Date.now(),
        usuario_id: 1,
        expediente_numero: data.expediente_numero,
        expediente_caratula: data.expediente_caratula || '',
        expediente_dependencia: data.expediente_dependencia,
        activo: true,
        total_cambios_detectados: 0,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }

      set(state => ({
        expedientes: [...state.expedientes, nuevoExpediente],
      }))

      toast.success('Expediente agregado al monitoreo', {
        description: `${data.expediente_numero} será verificado automáticamente`,
      })
    } catch (error: any) {
      console.error('Error al agregar expediente:', error)
      toast.error('Error al agregar expediente al monitoreo')
    }
  },

  // Remover expediente del monitoreo
  removerExpediente: async (id: number) => {
    try {
      // TODO: Reemplazar con llamada real a la API
      // await apiClient.delete(`/api/v1/monitoreo/expedientes/${id}`)

      // Mock data por ahora
      await new Promise(resolve => setTimeout(resolve, 400))

      set(state => ({
        expedientes: state.expedientes.filter(e => e.id !== id),
      }))

      toast.success('Expediente removido del monitoreo')
    } catch (error: any) {
      console.error('Error al remover expediente:', error)
      toast.error('Error al remover expediente')
    }
  },

  // Toggle expediente activo/pausado
  toggleExpediente: async (id: number, activo: boolean) => {
    try {
      // TODO: Reemplazar con llamada real a la API
      // await apiClient.patch(`/api/v1/monitoreo/expedientes/${id}/toggle`, { activo })

      // Mock data por ahora
      await new Promise(resolve => setTimeout(resolve, 300))

      set(state => ({
        expedientes: state.expedientes.map(e =>
          e.id === id ? { ...e, activo, updated_at: new Date().toISOString() } : e
        ),
      }))

      toast.success(activo ? 'Monitoreo activado' : 'Monitoreo pausado')
    } catch (error: any) {
      console.error('Error al cambiar estado del expediente:', error)
      toast.error('Error al cambiar el estado')
    }
  },

  // Verificar expediente manualmente
  verificarExpediente: async (id: number) => {
    try {
      // TODO: Reemplazar con llamada real a la API
      // await apiClient.post(`/api/v1/monitoreo/expedientes/${id}/verificar`)

      // Mock data por ahora
      await new Promise(resolve => setTimeout(resolve, 1500))

      set(state => ({
        expedientes: state.expedientes.map(e =>
          e.id === id
            ? { ...e, ultima_verificacion: new Date().toISOString() }
            : e
        ),
      }))

      toast.success('Verificación completada', {
        description: 'No se detectaron cambios nuevos',
      })
    } catch (error: any) {
      console.error('Error al verificar expediente:', error)
      toast.error('Error al verificar expediente')
    }
  },

  // Listar cambios detectados
  listarCambios: async (expedienteId?: number) => {
    set({ isLoading: true })

    try {
      // TODO: Reemplazar con llamada real a la API
      // const url = expedienteId
      //   ? `/api/v1/monitoreo/cambios?expediente_id=${expedienteId}`
      //   : '/api/v1/monitoreo/cambios'
      // const response = await apiClient.get<CambioDetectado[]>(url)
      // set({ cambios: response.data })

      // Mock data por ahora
      await new Promise(resolve => setTimeout(resolve, 600))

      const mockCambios: CambioDetectado[] = [
        {
          id: 1,
          expediente_monitoreado_id: 1,
          expediente_numero: 'EXP-2024-123-CS',
          expediente_caratula: 'PÉREZ JUAN C/ GARCÍA MARÍA S/ DAÑOS Y PERJUICIOS',
          tipo_cambio: 'nueva_actuacion',
          descripcion: 'Nueva actuación: PRESENTACION',
          detalles: {
            oficina: 'Secretaría Única',
            fecha: '12/01/2025',
            tipo: 'PRESENTACION',
          },
          notificado: true,
          leido: false,
          fecha_deteccion: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        },
        {
          id: 2,
          expediente_monitoreado_id: 2,
          expediente_numero: 'EXP-2024-456-CF',
          expediente_caratula: 'RODRÍGUEZ ANA C/ GÓMEZ PEDRO S/ DIVORCIO',
          tipo_cambio: 'nuevo_archivo',
          descripcion: 'Nuevo archivo adjunto: Informe pericial',
          detalles: {
            nombre_archivo: 'informe_pericial.pdf',
            tipo_archivo: 'Informe',
          },
          notificado: true,
          leido: false,
          fecha_deteccion: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
          created_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
        },
        {
          id: 3,
          expediente_monitoreado_id: 2,
          expediente_numero: 'EXP-2024-456-CF',
          expediente_caratula: 'RODRÍGUEZ ANA C/ GÓMEZ PEDRO S/ DIVORCIO',
          tipo_cambio: 'cambio_estado',
          descripcion: 'Cambio de situación: SENTENCIA',
          detalles: {
            estado_anterior: 'EN TRAMITE',
            estado_nuevo: 'SENTENCIA',
          },
          notificado: true,
          leido: true,
          fecha_deteccion: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
          created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
        },
      ]

      const cambiosFiltrados = expedienteId
        ? mockCambios.filter(c => c.expediente_monitoreado_id === expedienteId)
        : mockCambios

      set({ cambios: cambiosFiltrados })
    } catch (error: any) {
      console.error('Error al listar cambios:', error)
      toast.error('Error al cargar cambios detectados')
      set({ cambios: [] })
    } finally {
      set({ isLoading: false })
    }
  },

  // Marcar cambio como leído
  marcarComoLeido: async (id: number) => {
    try {
      // TODO: Reemplazar con llamada real a la API
      // await apiClient.patch(`/api/v1/monitoreo/cambios/${id}/leer`)

      // Mock data por ahora
      await new Promise(resolve => setTimeout(resolve, 200))

      set(state => ({
        cambios: state.cambios.map(c =>
          c.id === id ? { ...c, leido: true } : c
        ),
      }))
    } catch (error: any) {
      console.error('Error al marcar como leído:', error)
    }
  },

  // Marcar todos como leídos
  marcarTodosLeidos: async () => {
    try {
      // TODO: Reemplazar con llamada real a la API
      // await apiClient.patch('/api/v1/monitoreo/cambios/leer-todos')

      // Mock data por ahora
      await new Promise(resolve => setTimeout(resolve, 300))

      set(state => ({
        cambios: state.cambios.map(c => ({ ...c, leido: true })),
      }))

      toast.success('Todos los cambios marcados como leídos')
    } catch (error: any) {
      console.error('Error al marcar todos como leídos:', error)
      toast.error('Error al marcar como leídos')
    }
  },

  // Obtener estadísticas
  obtenerEstadisticas: async () => {
    try {
      // TODO: Reemplazar con llamada real a la API
      // const response = await apiClient.get<EstadisticasMonitoreo>('/api/v1/monitoreo/estadisticas')
      // set({ estadisticas: response.data })

      // Mock data por ahora
      await new Promise(resolve => setTimeout(resolve, 400))

      const mockEstadisticas: EstadisticasMonitoreo = {
        total_expedientes: get().expedientes.length,
        expedientes_activos: get().expedientes.filter(e => e.activo).length,
        expedientes_pausados: get().expedientes.filter(e => !e.activo).length,
        cambios_hoy: 2,
        cambios_semana: 8,
        cambios_mes: 25,
        cambios_sin_leer: get().cambios.filter(c => !c.leido).length,
        ultima_ejecucion: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
        proxima_ejecucion: new Date(Date.now() + 1 * 60 * 60 * 1000).toISOString(),
      }

      set({ estadisticas: mockEstadisticas })
    } catch (error: any) {
      console.error('Error al obtener estadísticas:', error)
    }
  },

  // Limpiar estado
  limpiar: () => {
    set({
      configuracion: null,
      expedientes: [],
      cambios: [],
      estadisticas: null,
      isLoading: false,
    })
  },
}))
