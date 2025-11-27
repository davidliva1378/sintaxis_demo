import { create } from 'zustand'
import { toast } from 'sonner'
import apiClient from '@/lib/api'
import type {
  ExpedienteResumen,
  ExpedienteDetalle,
  ExpedienteFiltros,
  SolicitudExtraccion,
  PaginacionResult,
  ConfigExtraccion,
  ComparacionDetallada,
  Actuacion,
} from '@/types/expediente'

interface ProgresoExtraccion {
  actual: number
  total: number
  porcentaje: number
  fase: string
  mensaje: string
  errores: number
  tiempoTranscurrido: number
  tiempoEstimado: number | null
  velocidad: number | null
}

interface ResumenExtraccion {
  sessionId: string
  estado: string
  total: number
  exitosos: number
  errores: number
  omitidos: number
  duracionSegundos: number
  velocidadPromedio: number
  archivosGenerados: string[]
}

interface ExtraccionMasivaState {
  sessionId: string | null
  estado: 'inactivo' | 'iniciando' | 'extrayendo' | 'pausado' | 'filtrado' | 'completado' | 'error' | 'cancelado' | 'error_agotado'
  progreso: ProgresoExtraccion
  websocket: WebSocket | null
  pollInterval: any | null
  paginas_procesadas: number
  archivos_descargados: number
  comparacion: ComparacionDetallada | null
  motivo_finalizacion: string | null
  // Campos de reintentos
  intentos_realizados: number
  intentos_maximos: number
  historial_intentos: Array<{
    intento: number
    timestamp: string
    motivo: string
    total_expedientes: number
    metadata?: any
    error?: string
  }>
  // Total esperado reportado por PJN
  total_esperado: number | null
}

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
  extraccionMasiva: ExtraccionMasivaState

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

  // Acciones de extracción masiva avanzada
  iniciarExtraccionMasivaAvanzada: (config: ConfigExtraccion) => Promise<string>
  conectarWebSocket: (sessionId: string) => void
  desconectarWebSocket: () => void
  pausarExtraccion: () => Promise<void>
  reanudarExtraccion: () => Promise<void>
  cancelarExtraccion: () => Promise<void>
  obtenerProgreso: () => Promise<void>
  obtenerResumen: () => Promise<ResumenExtraccion>
  descargarReporte: (formato: 'json' | 'excel' | 'csv' | 'html') => Promise<void>
  procesarExpedientesSeleccionados: (numeros: string[], config?: Partial<ConfigExtraccion>) => Promise<string>
  resetExtraccionMasiva: () => void
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
  extraccionMasiva: {
    sessionId: null,
    estado: 'inactivo',
    progreso: {
      actual: 0,
      total: 0,
      porcentaje: 0,
      fase: '',
      mensaje: '',
      errores: 0,
      tiempoTranscurrido: 0,
      tiempoEstimado: null,
      velocidad: null,
    },
    websocket: null,
    pollInterval: null,
    paginas_procesadas: 0,
    archivos_descargados: 0,
    comparacion: null,
    motivo_finalizacion: null,
    // Campos de reintentos
    intentos_realizados: 0,
    intentos_maximos: 3,
    historial_intentos: [],
    // Total esperado reportado por PJN
    total_esperado: null,
  },

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

  // Iniciar extracción masiva avanzada con WebSocket
  iniciarExtraccionMasivaAvanzada: async (config: ConfigExtraccion): Promise<string> => {
    try {
      toast.info('Iniciando extracción masiva avanzada...', {
        description: 'Configurando sesión de extracción',
      })

      // Construir payload según formato esperado por el backend
      const payload = {
        fecha_corte: config.fecha_corte || undefined,
        config: {
          headless: config.headless ?? true,
          umbral_errores: config.umbral_errores ?? 10,
          timeout_pagina: config.timeout_pagina,
          max_reintentos: config.max_reintentos,
          procesar_con_pdf: config.procesar_con_pdf ?? false,
          incluir_historicas: config.incluir_historicas ?? true,
          min_utilidad: config.min_utilidad ?? 'MEDIA',
          directorio_base: config.directorio_base ?? './Sistema_v6/data/expedientes',
          detener_en_duplicado: config.detener_en_duplicado ?? true,
          omitir_duplicados: config.omitir_duplicados ?? true,
          max_paginas: config.max_paginas,
          tiempo_maximo_segundos: config.tiempo_maximo_segundos,
        }
      }

      // Iniciar extracción en el backend
      const response = await apiClient.post('/api/v1/extraccion-masiva/listado', payload)
      const sessionId = response.data.session_id

      // Iniciar polling para obtener progreso
      const pollInterval = setInterval(() => {
        get().obtenerProgreso()
      }, 1000) // Cada 1 segundo para updates más fluidos

      // Actualizar estado con sesión y polling
      set({
        extraccionMasiva: {
          ...get().extraccionMasiva,
          sessionId,
          estado: 'extrayendo',
          pollInterval,
        },
      })

      // Conectar WebSocket automáticamente
      // TODO: WebSocket no disponible aún, usar polling
      // get().conectarWebSocket(sessionId)

      toast.success('Extracción iniciada', {
        description: `Sesión: ${sessionId}`,
      })

      return sessionId
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Error al iniciar extracción masiva'
      toast.error('Error al iniciar extracción', {
        description: errorMsg,
      })
      throw error
    }
  },

  // Conectar WebSocket para recibir actualizaciones en tiempo real
  conectarWebSocket: (sessionId: string) => {
    const state = get()

    // Cerrar conexión existente si hay
    if (state.extraccionMasiva.websocket) {
      state.extraccionMasiva.websocket.close()
    }

    // Construir URL del WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/api/v1/extraccion-masiva/sesion/${sessionId}/ws`

    // Crear conexión WebSocket
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log(`WebSocket conectado para sesión ${sessionId}`)

      // Enviar ping cada 25 segundos para mantener conexión
      const pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping')
        } else {
          clearInterval(pingInterval)
        }
      }, 25000)
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)

      // Actualizar progreso en el estado
      set({
        extraccionMasiva: {
          ...get().extraccionMasiva,
          estado: data.estado,
          progreso: {
            actual: data.progreso_actual,
            total: data.progreso_total,
            porcentaje: data.porcentaje,
            fase: data.fase,
            mensaje: data.mensaje,
            errores: data.errores,
            tiempoTranscurrido: data.tiempo_transcurrido || 0,
            tiempoEstimado: data.tiempo_estimado || null,
            velocidad: data.velocidad || null,
          },
        },
      })

      // Si la extracción terminó, cerrar WebSocket
      if (['completado', 'error', 'cancelado'].includes(data.estado)) {
        ws.close()

        if (data.estado === 'completado') {
          toast.success('Extracción completada', {
            description: data.mensaje,
          })
          // Actualizar lista de expedientes
          get().listarExpedientes()
        } else if (data.estado === 'error') {
          toast.error('Error en extracción', {
            description: data.mensaje,
          })
        } else if (data.estado === 'cancelado') {
          toast.warning('Extracción cancelada', {
            description: data.mensaje,
          })
        }
      }
    }

    ws.onerror = (error) => {
      console.error('Error en WebSocket:', error)
      toast.error('Error de conexión', {
        description: 'No se pudo conectar con el servidor',
      })
    }

    ws.onclose = () => {
      console.log(`WebSocket cerrado para sesión ${sessionId}`)
      set({
        extraccionMasiva: {
          ...get().extraccionMasiva,
          websocket: null,
        },
      })
    }

    // Guardar WebSocket en el estado
    set({
      extraccionMasiva: {
        ...get().extraccionMasiva,
        websocket: ws,
      },
    })
  },

  // Desconectar WebSocket
  desconectarWebSocket: () => {
    const ws = get().extraccionMasiva.websocket
    if (ws) {
      ws.close()
      set({
        extraccionMasiva: {
          ...get().extraccionMasiva,
          websocket: null,
        },
      })
    }
  },

  // Pausar extracción (TODO: implementar endpoint en backend)
  pausarExtraccion: async () => {
    const sessionId = get().extraccionMasiva.sessionId
    if (!sessionId) {
      toast.error('No hay sesión activa')
      return
    }

    // TODO: Endpoint no implementado aún
    toast.warning('Funcionalidad pausar no disponible aún')
    return
  },

  // Reanudar extracción (TODO: implementar endpoint en backend)
  reanudarExtraccion: async () => {
    const sessionId = get().extraccionMasiva.sessionId
    if (!sessionId) {
      toast.error('No hay sesión activa')
      return
    }

    // TODO: Endpoint no implementado aún
    toast.warning('Funcionalidad reanudar no disponible aún')
    return
  },

  // Cancelar extracción (TODO: implementar endpoint en backend)
  cancelarExtraccion: async () => {
    const sessionId = get().extraccionMasiva.sessionId
    if (!sessionId) {
      toast.error('No hay sesión activa')
      return
    }

    // TODO: Endpoint no implementado aún
    toast.warning('Funcionalidad cancelar no disponible aún')
    return
  },

  // Obtener progreso actual (polling como alternativa a WebSocket)
  obtenerProgreso: async () => {
    const state = get()
    const sessionId = state.extraccionMasiva.sessionId
    if (!sessionId) {
      console.log('[POLLING] No hay sessionId, saltando polling')
      return
    }

    try {
      // Usar endpoint de sesión para obtener progreso
      const response = await apiClient.get(`/api/v1/extraccion-masiva/sesion/${sessionId}`)
      const data = response.data

      const nuevoEstado = data.estado || 'extrayendo'
      console.log(`[POLLING] Session: ${sessionId}, Estado: ${nuevoEstado}, Progreso: ${data.progreso_actual}/${data.progreso_total}`)

      // Calcular tiempo transcurrido desde tiempo_inicio
      let tiempoTranscurrido = 0
      if (data.tiempo_inicio) {
        const inicio = new Date(data.tiempo_inicio)
        const fin = data.tiempo_fin ? new Date(data.tiempo_fin) : new Date()
        tiempoTranscurrido = Math.floor((fin.getTime() - inicio.getTime()) / 1000) // en segundos
      }

      // Extraer paginas_procesadas, archivos_descargados, comparacion y motivo_finalizacion del backend
      const paginasProcesadas = data.paginas_procesadas || 0
      const archivosDescargados = data.archivos_descargados || 0
      const comparacion = (data.comparacion as ComparacionDetallada | null) || null
      const motivoFinalizacion = data.motivo_finalizacion || null
      // Extraer campos de reintentos
      const intentosRealizados = data.intentos_realizados || 0
      const intentosMaximos = data.intentos_maximos || 3
      const historialIntentos = data.historial_intentos || []
      // Extraer total esperado del metadata (si existe)
      const totalEsperado = data.metadata?.total_esperado || null

      // Si la extracción terminó (completado, error o error_agotado), detener el polling
      if ((nuevoEstado === 'completado' || nuevoEstado === 'error' || nuevoEstado === 'error_agotado') && state.extraccionMasiva.pollInterval) {
        console.log(`[POLLING] Detectado estado final: ${nuevoEstado}. Deteniendo polling...`)
        clearInterval(state.extraccionMasiva.pollInterval)

        // Mostrar notificación de completado con duración extendida
        if (nuevoEstado === 'completado') {
          const exitosos = data.progreso_actual || 0
          const total = data.progreso_total || 0

          // Validar completitud si hay total_esperado
          let descripcion = `${exitosos}/${total} expedientes procesados exitosamente`
          if (totalEsperado && totalEsperado > 0) {
            const porcentaje = ((exitosos / totalEsperado) * 100).toFixed(1)
            const completitud = exitosos >= totalEsperado ? '✅ Extracción completa' : `⚠️ Extracción parcial (${porcentaje}%)`
            descripcion = `${completitud}: ${exitosos}/${totalEsperado} expedientes`
          }

          toast.success('Procesamiento completado', {
            description: descripcion,
            duration: 10000, // 10 segundos para que el usuario pueda leer
          })
        } else if (nuevoEstado === 'error') {
          toast.error('Error en procesamiento', {
            description: data.mensaje || 'Ocurrió un error durante el procesamiento',
            duration: 10000,
          })
        } else if (nuevoEstado === 'error_agotado') {
          toast.error('Reintentos agotados', {
            description: `Se agotaron los ${intentosRealizados} intentos. ${motivoFinalizacion || 'Error desconocido'}`,
            duration: 15000, // 15 segundos para que el usuario pueda leer y decidir
          })
        }
      }

      set({
        extraccionMasiva: {
          ...state.extraccionMasiva,
          estado: nuevoEstado,
          pollInterval: (nuevoEstado === 'completado' || nuevoEstado === 'error' || nuevoEstado === 'error_agotado') ? null : state.extraccionMasiva.pollInterval,
          paginas_procesadas: paginasProcesadas,
          archivos_descargados: archivosDescargados,
          comparacion: comparacion,
          motivo_finalizacion: motivoFinalizacion,
          intentos_realizados: intentosRealizados,
          intentos_maximos: intentosMaximos,
          historial_intentos: historialIntentos,
          total_esperado: totalEsperado,
          progreso: {
            actual: data.progreso_actual || 0,
            total: data.progreso_total || 0,
            porcentaje: data.progreso_actual && data.progreso_total
              ? (data.progreso_actual / data.progreso_total) * 100
              : 0,
            fase: data.fase || '',
            mensaje: data.mensaje || '',
            errores: 0,
            tiempoTranscurrido,
            tiempoEstimado: null,
            velocidad: null,
          },
        },
      })
    } catch (error: any) {
      console.error('[POLLING] Error al obtener progreso:', error)
      // Si hay error en el polling, detener el polling
      if (state.extraccionMasiva.pollInterval) {
        console.log('[POLLING] Deteniendo polling debido a error')
        clearInterval(state.extraccionMasiva.pollInterval)
        set({
          extraccionMasiva: {
            ...state.extraccionMasiva,
            pollInterval: null,
          },
        })
      }
    }
  },

  // Obtener resumen de la extracción
  obtenerResumen: async (): Promise<ResumenExtraccion> => {
    const sessionId = get().extraccionMasiva.sessionId
    if (!sessionId) {
      throw new Error('No hay sesión activa')
    }

    try {
      // Usar endpoint de sesión
      const response = await apiClient.get(`/api/v1/extraccion-masiva/sesion/${sessionId}`)
      const data = response.data

      // Mapear al formato esperado
      return {
        sessionId,
        estado: data.estado,
        total: data.progreso_total || 0,
        exitosos: data.progreso_actual || 0,
        errores: 0,
        omitidos: 0,
        duracionSegundos: 0,
        velocidadPromedio: 0,
        archivosGenerados: [],
      }
    } catch (error: any) {
      toast.error('Error al obtener resumen', {
        description: error.response?.data?.detail || 'Error desconocido',
      })
      throw error
    }
  },

  // Descargar reporte en formato específico (TODO: implementar endpoint en backend)
  descargarReporte: async (formato: 'json' | 'excel' | 'csv' | 'html') => {
    const sessionId = get().extraccionMasiva.sessionId
    if (!sessionId) {
      toast.error('No hay sesión activa')
      return
    }

    // TODO: Endpoint no implementado aún
    toast.warning(`Descarga de reportes no disponible aún (formato: ${formato})`)
    return
  },

  // Procesar expedientes seleccionados
  procesarExpedientesSeleccionados: async (numeros: string[], config?: Partial<ConfigExtraccion>): Promise<string> => {
    try {
      toast.info('Procesando expedientes seleccionados...', {
        description: `${numeros.length} expedientes`,
      })

      // Preparar payload con config si se proporciona
      const payload: any = {
        numeros_expedientes: numeros,
      }

      // Agregar config si se proporciona
      if (config) {
        payload.config = {
          headless: config.headless ?? true,
          umbral_errores: config.umbral_errores ?? 10,
          timeout_pagina: config.timeout_pagina,
          max_reintentos: config.max_reintentos,
          procesar_con_pdf: config.procesar_con_pdf ?? false,
          incluir_historicas: config.incluir_historicas ?? true,
          min_utilidad: config.min_utilidad ?? "MEDIA",
          directorio_base: config.directorio_base,
          detener_en_duplicado: config.detener_en_duplicado ?? true,
          omitir_duplicados: config.omitir_duplicados ?? true,
          max_paginas: config.max_paginas,
          tiempo_maximo_segundos: config.tiempo_maximo_segundos,
        }
      }

      // Cambiar estado a 'iniciando' ANTES de la llamada al backend
      // Esto permite que React renderice la vista de progreso inmediatamente
      set({
        extraccionMasiva: {
          ...get().extraccionMasiva,
          estado: 'iniciando',
          progreso: {
            actual: 0,
            total: numeros.length,
            porcentaje: 0,
            fase: 'Preparando procesamiento',
            mensaje: 'Iniciando procesamiento de expedientes seleccionados...',
            errores: 0,
            tiempoTranscurrido: 0,
            tiempoEstimado: null,
            velocidad: null,
          },
        },
      })

      // Llamar al backend para procesar los expedientes seleccionados
      const response = await apiClient.post('/api/v1/extraccion-masiva/procesar-seleccionados', payload)

      const sessionId = response.data.session_id
      const resumen = response.data.resumen

      // Actualizar estado con la sesión de procesamiento (resetear progreso)
      set({
        extraccionMasiva: {
          ...get().extraccionMasiva,
          sessionId,
          estado: 'extrayendo',
          progreso: {
            actual: 0,
            total: numeros.length,
            porcentaje: 0,
            fase: 'Procesando expedientes seleccionados',
            mensaje: 'Iniciando procesamiento...',
            errores: 0,
            tiempoTranscurrido: 0,
            tiempoEstimado: null,
            velocidad: null,
          },
        },
      })

      toast.success('Procesamiento iniciado', {
        description: `Sesión: ${sessionId}`,
      })

      // Conectar WebSocket para recibir actualizaciones de progreso
      // TODO: WebSocket no disponible aún, usar polling
      // get().conectarWebSocket(sessionId)

      // Iniciar polling para obtener progreso
      const pollInterval = setInterval(() => {
        get().obtenerProgreso()
      }, 1000) // Cada 1 segundo para updates más fluidos

      // Actualizar pollInterval en el estado
      set({
        extraccionMasiva: {
          ...get().extraccionMasiva,
          pollInterval,
        },
      })

      return sessionId
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Error al procesar expedientes seleccionados'
      toast.error('Error al procesar expedientes', {
        description: errorMsg,
      })
      throw error
    }
  },

  // Resetear estado de extracción masiva
  resetExtraccionMasiva: () => {
    const state = get()

    // Detener polling si está activo
    if (state.extraccionMasiva.pollInterval) {
      clearInterval(state.extraccionMasiva.pollInterval)
    }

    // Desconectar WebSocket si está conectado
    if (state.extraccionMasiva.websocket) {
      state.extraccionMasiva.websocket.close()
    }

    // Resetear estado a valores iniciales
    set({
      extraccionMasiva: {
        sessionId: null,
        estado: 'inactivo',
        progreso: {
          actual: 0,
          total: 0,
          porcentaje: 0,
          fase: '',
          mensaje: '',
          errores: 0,
          tiempoTranscurrido: 0,
          tiempoEstimado: null,
          velocidad: null,
        },
        websocket: null,
        pollInterval: null,
        paginas_procesadas: 0,
        archivos_descargados: 0,
        comparacion: null,
        motivo_finalizacion: null,
        intentos_realizados: 0,
        intentos_maximos: 3,
        historial_intentos: [],
        total_esperado: null,
      },
    })
  },
}))
