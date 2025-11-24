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
import * as monitoreoApi from '@/api/monitoreoApi'

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
      const response = await monitoreoApi.obtenerConfiguracion()

      // Mapear respuesta a ConfiguracionMonitoreo
      const config: ConfiguracionMonitoreo = {
        id: response.id,
        usuario_id: response.usuario_id,
        activo: response.activo,
        frecuencia: response.frecuencia as FrecuenciaMonitoreo,
        notificar_email: response.notificar_email,
        notificar_sistema: response.notificar_sistema,
        hora_inicio: response.hora_inicio || undefined,
        hora_fin: response.hora_fin || undefined,
        dias_semana: response.dias_semana || undefined,
        created_at: response.created_at,
        updated_at: response.updated_at,
      }

      set({ configuracion: config })
    } catch (error: any) {
      console.error('Error al obtener configuración:', error)
      toast.error('Error al cargar la configuración del monitoreo')
    }
  },

  // Actualizar configuración
  actualizarConfiguracion: async (data: ActualizarMonitoreo) => {
    try {
      const response = await monitoreoApi.actualizarConfiguracion(data)

      // Mapear respuesta a ConfiguracionMonitoreo
      const config: ConfiguracionMonitoreo = {
        id: response.id,
        usuario_id: response.usuario_id,
        activo: response.activo,
        frecuencia: response.frecuencia as FrecuenciaMonitoreo,
        notificar_email: response.notificar_email,
        notificar_sistema: response.notificar_sistema,
        hora_inicio: response.hora_inicio || undefined,
        hora_fin: response.hora_fin || undefined,
        dias_semana: response.dias_semana || undefined,
        created_at: response.created_at,
        updated_at: response.updated_at,
      }

      set({ configuracion: config })
      toast.success('Configuración actualizada correctamente')
    } catch (error: any) {
      console.error('Error al actualizar configuración:', error)
      toast.error('Error al actualizar la configuración')
    }
  },

  // Toggle monitoreo activo/pausado
  toggleMonitoreo: async (activo: boolean) => {
    try {
      // Llamada real a la API del scheduler
      if (activo) {
        const response = await monitoreoApi.iniciarScheduler()
        if (!response.success) {
          toast.error(response.mensaje)
          return
        }
        toast.success('Monitoreo activado', {
          description: response.intervalo_minutos
            ? `Verificando cada ${response.intervalo_minutos} minutos`
            : undefined,
        })
      } else {
        const response = await monitoreoApi.detenerScheduler()
        if (!response.success) {
          toast.error(response.mensaje)
          return
        }
        toast.success('Monitoreo pausado')
      }

      // Actualizar configuración local
      set(state => ({
        configuracion: state.configuracion
          ? { ...state.configuracion, activo, updated_at: new Date().toISOString() }
          : null,
      }))

      // Refrescar estado para obtener datos actualizados
      await get().obtenerConfiguracion()
    } catch (error: any) {
      console.error('Error al cambiar estado del monitoreo:', error)
      toast.error(`Error al ${activo ? 'iniciar' : 'detener'} el monitoreo: ${error.message}`)
    }
  },

  // Listar expedientes monitoreados
  listarExpedientes: async () => {
    set({ isLoading: true })

    try {
      const response = await monitoreoApi.listarExpedientes()

      // Mapear respuesta al tipo del frontend
      const expedientes: ExpedienteMonitoreado[] = response.expedientes.map(exp => ({
        id: exp.id,
        usuario_id: exp.usuario_id,
        expediente_numero: exp.expediente_numero,
        expediente_caratula: exp.expediente_caratula || '',
        expediente_dependencia: exp.expediente_dependencia || undefined,
        activo: exp.activo,
        ultima_verificacion: exp.ultima_verificacion || undefined,
        ultima_actuacion_fecha: exp.ultima_actuacion_fecha || undefined,
        ultima_actuacion_id: exp.ultima_actuacion_id || undefined,
        total_cambios_detectados: exp.total_cambios_detectados,
        notas: exp.notas || undefined,
        prioridad: exp.prioridad,
        created_at: exp.created_at,
        updated_at: exp.updated_at,
      }))

      set({ expedientes })
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
      const response = await monitoreoApi.agregarExpediente(data)

      // Mapear respuesta al tipo del frontend
      const nuevoExpediente: ExpedienteMonitoreado = {
        id: response.id,
        usuario_id: response.usuario_id,
        expediente_numero: response.expediente_numero,
        expediente_caratula: response.expediente_caratula || '',
        expediente_dependencia: response.expediente_dependencia || undefined,
        activo: response.activo,
        ultima_verificacion: response.ultima_verificacion || undefined,
        ultima_actuacion_fecha: response.ultima_actuacion_fecha || undefined,
        total_cambios_detectados: response.total_cambios_detectados,
        notas: response.notas || undefined,
        prioridad: response.prioridad,
        created_at: response.created_at,
        updated_at: response.updated_at,
      }

      set(state => ({
        expedientes: [...state.expedientes, nuevoExpediente],
      }))

      toast.success('Expediente agregado al monitoreo', {
        description: `${data.expediente_numero} será verificado automáticamente`,
      })
    } catch (error: any) {
      console.error('Error al agregar expediente:', error)
      toast.error(error.message || 'Error al agregar expediente al monitoreo')
    }
  },

  // Remover expediente del monitoreo
  removerExpediente: async (id: number) => {
    try {
      // Buscar el expediente por ID para obtener el número
      const expediente = get().expedientes.find(e => e.id === id)
      if (!expediente) {
        toast.error('Expediente no encontrado')
        return
      }

      await monitoreoApi.eliminarExpediente(expediente.expediente_numero)

      set(state => ({
        expedientes: state.expedientes.filter(e => e.id !== id),
      }))

      toast.success('Expediente removido del monitoreo')
    } catch (error: any) {
      console.error('Error al remover expediente:', error)
      toast.error(error.message || 'Error al remover expediente')
    }
  },

  // Toggle expediente activo/pausado
  toggleExpediente: async (id: number, activo: boolean) => {
    try {
      // Buscar el expediente por ID para obtener el número
      const expediente = get().expedientes.find(e => e.id === id)
      if (!expediente) {
        toast.error('Expediente no encontrado')
        return
      }

      // Usar pausar/reanudar según el estado deseado
      const response = activo
        ? await monitoreoApi.reanudarExpediente(expediente.expediente_numero)
        : await monitoreoApi.pausarExpediente(expediente.expediente_numero)

      set(state => ({
        expedientes: state.expedientes.map(e =>
          e.id === id ? { ...e, activo: response.activo, updated_at: response.updated_at } : e
        ),
      }))

      toast.success(activo ? 'Monitoreo activado' : 'Monitoreo pausado')
    } catch (error: any) {
      console.error('Error al cambiar estado del expediente:', error)
      toast.error(error.message || 'Error al cambiar el estado')
    }
  },

  // Verificar expediente manualmente
  verificarExpediente: async (id: number) => {
    set({ isLoading: true })
    try {
      // Toast de inicio
      toast.info('Verificando expediente...', {
        id: 'verifying',
        description: 'Conectando con PJN...'
      })

      // Llamada real a la API
      const response = await monitoreoApi.verificarManual()

      if (response.success) {
        const cambiosDetectados = response.cambios_detectados || 0

        // Actualizar última verificación
        set(state => ({
          expedientes: state.expedientes.map(e =>
            e.id === id
              ? { ...e, ultima_verificacion: new Date().toISOString() }
              : e
          ),
        }))

        // Toast de éxito con detalles
        toast.success('Verificación completada', {
          description: cambiosDetectados > 0
            ? `${cambiosDetectados} cambio${cambiosDetectados > 1 ? 's' : ''} detectado${cambiosDetectados > 1 ? 's' : ''}`
            : 'No se detectaron cambios nuevos',
        })
      } else {
        toast.error('Error en verificación', {
          description: response.error || 'Error desconocido'
        })
      }
    } catch (error: any) {
      console.error('Error al verificar expediente:', error)
      toast.error('Error al verificar expediente', {
        description: error.message || 'Error de conexión'
      })
    } finally {
      set({ isLoading: false })
      toast.dismiss('verifying')
    }
  },

  // Listar cambios detectados
  listarCambios: async (expedienteId?: number) => {
    set({ isLoading: true })

    try {
      // Si hay expedienteId, buscar el número del expediente
      let expedienteNumero: string | undefined
      if (expedienteId) {
        const expediente = get().expedientes.find(e => e.id === expedienteId)
        expedienteNumero = expediente?.expediente_numero
      }

      const response = await monitoreoApi.listarCambios(
        false, // solo_no_leidos
        undefined, // tipo_cambio
        expedienteNumero
      )

      // Mapear respuesta al tipo del frontend
      const cambios: CambioDetectado[] = response.cambios.map(cambio => ({
        id: cambio.id,
        expediente_monitoreado_id: cambio.expediente_monitoreado_id,
        expediente_numero: cambio.expediente_numero,
        expediente_caratula: cambio.expediente_caratula || undefined,
        tipo_cambio: cambio.tipo_cambio,
        descripcion: cambio.descripcion,
        detalles: cambio.detalles || undefined,
        notificado: cambio.notificado,
        leido: cambio.leido,
        fecha_deteccion: cambio.fecha_deteccion,
        created_at: cambio.created_at,
      }))

      set({ cambios })
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
      await monitoreoApi.marcarLeido(id)

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
      const response = await monitoreoApi.marcarTodosLeidos()

      set(state => ({
        cambios: state.cambios.map(c => ({ ...c, leido: true })),
      }))

      toast.success(`${response.cantidad_marcados} cambios marcados como leídos`)
    } catch (error: any) {
      console.error('Error al marcar todos como leídos:', error)
      toast.error('Error al marcar como leídos')
    }
  },

  // Obtener estadísticas
  obtenerEstadisticas: async () => {
    try {
      const response = await monitoreoApi.obtenerEstadisticas()

      const estadisticas: EstadisticasMonitoreo = {
        total_expedientes: response.total_expedientes,
        expedientes_activos: response.expedientes_activos,
        expedientes_pausados: response.expedientes_pausados,
        cambios_hoy: response.cambios_hoy,
        cambios_semana: response.cambios_semana,
        cambios_mes: response.cambios_mes,
        cambios_sin_leer: response.cambios_sin_leer,
        ultima_ejecucion: response.ultima_ejecucion || null,
        proxima_ejecucion: response.proxima_ejecucion || null,
      }

      set({ estadisticas })
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
