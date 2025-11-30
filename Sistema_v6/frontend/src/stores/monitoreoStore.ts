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
import type { EstadoMonitoreoResponse } from '@/api/monitoreoApi'

interface MonitoreoState {
  // Estado
  configuracion: ConfiguracionMonitoreo | null
  expedientes: ExpedienteMonitoreado[]
  cambios: CambioDetectado[]
  estadisticas: EstadisticasMonitoreo | null
  estadoScheduler: EstadoMonitoreoResponse | null
  isLoading: boolean
  socket: WebSocket | null
  filtros: {
    soloActivos: boolean
    prioridad: string | undefined
    busqueda: string | undefined
  }
  paginacion: {
    pagina: number
    porPagina: number
    total: number
    totalPaginas: number
  }

  // Acciones - Configuración
  obtenerConfiguracion: () => Promise<void>
  actualizarConfiguracion: (data: ActualizarMonitoreo) => Promise<void>
  toggleMonitoreo: (activo: boolean) => Promise<void>

  // Acciones - Expedientes Monitoreados
  listarExpedientes: () => Promise<void>
  cambiarPagina: (pagina: number) => Promise<void>
  setFiltros: (filtros: Partial<MonitoreoState['filtros']>) => void
  agregarExpediente: (data: SolicitudMonitorear) => Promise<void>
  sincronizarExpedientes: () => Promise<void>
  removerExpediente: (id: number) => Promise<void>
  toggleExpediente: (id: number, activo: boolean) => Promise<void>
  verificarExpediente: (id: number) => Promise<void>

  // Acciones - Cambios
  listarCambios: (expedienteId?: number) => Promise<void>
  marcarComoLeido: (id: number) => Promise<void>
  marcarTodosLeidos: () => Promise<void>

  // Acciones - Estadísticas
  obtenerEstadisticas: () => Promise<void>
  obtenerEstadoScheduler: () => Promise<void>
  exportarReporte: () => Promise<void>

  // Utilidades
  limpiar: () => void
  connectWebSocket: () => void
  disconnectWebSocket: () => void
}

export const useMonitoreoStore = create<MonitoreoState>((set, get) => ({
  // Estado inicial
  configuracion: null,
  expedientes: [],
  cambios: [],
  estadisticas: null,
  estadoScheduler: null,
  isLoading: false,
  socket: null,
  filtros: {
    soloActivos: false,
    prioridad: undefined,
    busqueda: undefined,
  },
  paginacion: {
    pagina: 1,
    porPagina: 50,
    total: 0,
    totalPaginas: 0,
  },

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
      const { filtros, paginacion } = get()
      const response = await monitoreoApi.listarExpedientes(
        filtros.soloActivos,
        filtros.prioridad,
        filtros.busqueda,
        paginacion.pagina,
        paginacion.porPagina
      )

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

      set({
        expedientes,
        paginacion: {
          ...get().paginacion,
          total: response.total,
          totalPaginas: response.total_paginas,
          pagina: response.pagina,
          porPagina: response.por_pagina
        }
      })
    } catch (error: any) {
      console.error('Error al listar expedientes:', error)
      toast.error('Error al cargar expedientes monitoreados')
      set({ expedientes: [] })
    } finally {
      set({ isLoading: false })
    }
  },

  // Actualizar filtros y recargar
  setFiltros: (nuevosFiltros: Partial<MonitoreoState['filtros']>) => {
    set(state => ({
      filtros: { ...state.filtros, ...nuevosFiltros }
    }))
    get().listarExpedientes()
  },

  // Cambiar página
  cambiarPagina: async (pagina: number) => {
    set(state => ({
      paginacion: { ...state.paginacion, pagina }
    }))
    await get().listarExpedientes()
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

  // Sincronizar expedientes del sistema
  sincronizarExpedientes: async () => {
    set({ isLoading: true })
    try {
      toast.info('Sincronizando expedientes...', { id: 'sync' })
      const response = await monitoreoApi.sincronizarExpedientes()

      if (response.success) {
        toast.success(response.mensaje, {
          description: `Nuevos: ${response.nuevos_monitoreados}, Ya monitoreados: ${response.ya_monitoreados}`
        })
        // Recargar lista
        await get().listarExpedientes()
        await get().obtenerEstadisticas()
      } else {
        toast.error('Error en sincronización', {
          description: response.mensaje
        })
      }
    } catch (error: any) {
      console.error('Error al sincronizar:', error)
      toast.error('Error al sincronizar expedientes')
    } finally {
      set({ isLoading: false })
      toast.dismiss('sync')
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
  verificarExpediente: async (_id: number) => {
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

        // Recargar expedientes desde el servidor para obtener la última verificación actualizada
        await get().listarExpedientes()

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
        expediente_caratula: cambio.expediente_caratula || '',
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
        ultima_ejecucion: response.ultima_ejecucion || undefined,
        proxima_ejecucion: response.proxima_ejecucion || undefined,
      }

      set({ estadisticas })
    } catch (error: any) {
      console.error('Error al obtener estadísticas:', error)
    }
  },

  // Obtener estado del scheduler (activo, ejecutando, etc.)
  obtenerEstadoScheduler: async () => {
    try {
      const response = await monitoreoApi.obtenerEstadoMonitoreo()
      set({ estadoScheduler: response })
    } catch (error: any) {
      console.error('Error al obtener estado del scheduler:', error)
    }
  },

  // Exportar reporte
  exportarReporte: async () => {
    try {
      const { filtros } = get()
      toast.info('Generando reporte...')
      await monitoreoApi.exportarReporte(
        filtros.soloActivos,
        filtros.prioridad,
        filtros.busqueda
      )
      toast.success('Reporte descargado')
    } catch (error: any) {
      console.error('Error al exportar:', error)
      toast.error('Error al generar el reporte')
    }
  },

  // Limpiar estado
  limpiar: () => {
    get().disconnectWebSocket()
    set({
      configuracion: null,
      expedientes: [],
      cambios: [],
      estadisticas: null,
      isLoading: false,
      socket: null,
      filtros: {
        soloActivos: false,
        prioridad: undefined,
        busqueda: undefined,
      },
      paginacion: {
        pagina: 1,
        porPagina: 50,
        total: 0,
        totalPaginas: 0,
      },
    })
  },

  // WebSocket
  connectWebSocket: () => {
    const { socket } = get()
    if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
      return
    }

    // Usar usuario_id=1 hardcoded por ahora, igual que en backend
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    // Ajustar puerto si es necesario (asumiendo backend en 8000)
    const wsUrl = `${protocol}//${window.location.hostname}:8000/api/v1/monitoreo/ws/1`

    console.log('Conectando WS Monitoreo:', wsUrl)
    const newSocket = new WebSocket(wsUrl)

    newSocket.onopen = () => {
      console.log('WS Monitoreo conectado')
    }

    newSocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        console.log('WS Mensaje:', data)

        if (data.type === 'scheduler_status') {
          get().obtenerEstadoScheduler()
        } else if (data.type === 'verificacion_inicio') {
          const current = get().estadoScheduler
          if (current) set({ estadoScheduler: { ...current, ejecutando: true } })
        } else if (data.type === 'verificacion_fin') {
          get().obtenerEstadoScheduler()
          get().obtenerEstadisticas()
          get().listarExpedientes()
          if (data.success && data.cambios > 0) {
            toast.info(`Verificación completada: ${data.cambios} cambios detectados`)
            get().listarCambios()
          }
        }
      } catch (e) {
        console.error('Error procesando mensaje WS:', e)
      }
    }

    newSocket.onclose = () => {
      console.log('WS Monitoreo desconectado')
      set({ socket: null })
      // Reintentar conexión en 5s si no se desconectó intencionalmente
      // (Implementación simple, se puede mejorar)
    }

    set({ socket: newSocket })
  },

  disconnectWebSocket: () => {
    const { socket } = get()
    if (socket) {
      socket.close()
      set({ socket: null })
    }
  }
}))
