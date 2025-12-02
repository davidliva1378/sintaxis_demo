import { create } from 'zustand'
import { toast } from 'sonner'
import apiClient from '@/lib/api'
import type {
    ConfigExtraccion,
    ComparacionDetallada,
} from '@/types/expediente'

export interface ProgresoExtraccion {
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

export interface ResumenExtraccion {
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

interface ExtraccionState {
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
    // Campos de feedback de procesamiento detallado
    expediente_procesando: string | null
    actuacion_actual: number
    actuaciones_total: number
    fase_procesamiento: string
    mensaje_procesamiento: string

    // Acciones
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
    cargarListadoBase: () => Promise<any>
    setEstado: (estado: ExtraccionState['estado']) => void
}

export const useExtraccionStore = create<ExtraccionState>((set, get) => ({
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
    // Campos de feedback de procesamiento detallado
    expediente_procesando: null,
    actuacion_actual: 0,
    actuaciones_total: 0,
    fase_procesamiento: '',
    mensaje_procesamiento: '',

    iniciarExtraccionMasivaAvanzada: async (config: ConfigExtraccion): Promise<string> => {
        try {
            toast.info('Iniciando extracción masiva avanzada...', {
                description: 'Configurando sesión de extracción',
            })

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

            const response = await apiClient.post('/api/v1/extraccion-masiva/listado', payload)
            const sessionId = response.data.session_id

            const pollInterval = setInterval(() => {
                get().obtenerProgreso()
            }, 1000)

            set({
                sessionId,
                estado: 'extrayendo',
                pollInterval,
            })

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

    conectarWebSocket: (sessionId: string) => {
        const state = get()

        if (state.websocket) {
            state.websocket.close()
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        const host = window.location.host
        const wsUrl = `${protocol}//${host}/api/v1/extraccion-masiva/sesion/${sessionId}/ws`

        const ws = new WebSocket(wsUrl)

        ws.onopen = () => {
            console.log(`WebSocket conectado para sesión ${sessionId}`)
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

            set({
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
            })

            if (['completado', 'error', 'cancelado'].includes(data.estado)) {
                ws.close()

                if (data.estado === 'completado') {
                    toast.success('Extracción completada', {
                        description: data.mensaje,
                    })
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
            set({ websocket: null })
        }

        set({ websocket: ws })
    },

    desconectarWebSocket: () => {
        const ws = get().websocket
        if (ws) {
            ws.close()
            set({ websocket: null })
        }
    },

    pausarExtraccion: async () => {
        const sessionId = get().sessionId
        if (!sessionId) {
            toast.error('No hay sesión activa')
            return
        }

        try {
            await apiClient.post(`/api/v1/extraccion-masiva/pausar/${sessionId}`)
            set({ estado: 'pausado' })
            toast.success('Extracción pausada')
        } catch (error: any) {
            toast.error('Error al pausar', {
                description: error.response?.data?.detail || 'Error desconocido'
            })
        }
    },

    reanudarExtraccion: async () => {
        const sessionId = get().sessionId
        if (!sessionId) {
            toast.error('No hay sesión activa')
            return
        }

        try {
            await apiClient.post(`/api/v1/extraccion-masiva/reanudar/${sessionId}`)
            set({ estado: 'extrayendo' })
            toast.success('Extracción reanudada')
        } catch (error: any) {
            toast.error('Error al reanudar', {
                description: error.response?.data?.detail || 'Error desconocido'
            })
        }
    },

    cancelarExtraccion: async () => {
        const sessionId = get().sessionId
        if (!sessionId) {
            toast.error('No hay sesión activa')
            return
        }

        try {
            // Feedback inmediato
            set({ estado: 'cancelado' }) // O un estado intermedio 'cancelando' si se prefiere
            toast.info('Cancelando extracción...')

            await apiClient.post(`/api/v1/extraccion-masiva/cancelar/${sessionId}`)

            toast.success('Extracción cancelada correctamente')
        } catch (error: any) {
            toast.error('Error al cancelar', {
                description: error.response?.data?.detail || 'Error desconocido'
            })
        }
    },

    obtenerProgreso: async () => {
        const state = get()
        const sessionId = state.sessionId
        if (!sessionId) {
            return
        }

        try {
            const response = await apiClient.get(`/api/v1/extraccion-masiva/sesion/${sessionId}`)
            const data = response.data

            const nuevoEstado = data.estado || 'extrayendo'

            let tiempoTranscurrido = 0
            if (data.tiempo_inicio) {
                const inicio = new Date(data.tiempo_inicio)
                const fin = data.tiempo_fin ? new Date(data.tiempo_fin) : new Date()
                tiempoTranscurrido = Math.floor((fin.getTime() - inicio.getTime()) / 1000)
            }

            if ((nuevoEstado === 'completado' || nuevoEstado === 'error' || nuevoEstado === 'error_agotado') && state.pollInterval) {
                clearInterval(state.pollInterval)

                if (nuevoEstado === 'completado') {
                    toast.success('Procesamiento completado', {
                        description: `${data.progreso_actual}/${data.progreso_total} expedientes procesados`,
                        duration: 10000,
                    })
                } else if (nuevoEstado === 'error') {
                    toast.error('Error en procesamiento', {
                        description: data.mensaje || 'Ocurrió un error',
                        duration: 10000,
                    })
                } else if (nuevoEstado === 'error_agotado') {
                    toast.error('Reintentos agotados', {
                        description: `Se agotaron los intentos. ${data.motivo_finalizacion || 'Error desconocido'}`,
                        duration: 15000,
                    })
                }
            }

            set({
                estado: nuevoEstado,
                pollInterval: (nuevoEstado === 'completado' || nuevoEstado === 'error' || nuevoEstado === 'error_agotado') ? null : state.pollInterval,
                paginas_procesadas: data.paginas_procesadas || 0,
                archivos_descargados: data.archivos_descargados || 0,
                comparacion: data.comparacion || null,
                motivo_finalizacion: data.motivo_finalizacion || null,
                intentos_realizados: data.intentos_realizados || 0,
                intentos_maximos: data.intentos_maximos || 3,
                historial_intentos: data.historial_intentos || [],
                total_esperado: data.metadata?.total_esperado || null,
                // Campos de feedback de procesamiento detallado
                expediente_procesando: data.expediente_procesando || null,
                actuacion_actual: data.actuacion_actual || 0,
                actuaciones_total: data.actuaciones_total || 0,
                fase_procesamiento: data.fase_procesamiento || '',
                mensaje_procesamiento: data.mensaje_procesamiento || '',
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
            })
        } catch (error) {
            console.error('[POLLING] Error al obtener progreso:', error)
            if (state.pollInterval) {
                clearInterval(state.pollInterval)
                set({ pollInterval: null })
            }
        }
    },

    obtenerResumen: async (): Promise<ResumenExtraccion> => {
        const sessionId = get().sessionId
        if (!sessionId) {
            throw new Error('No hay sesión activa')
        }

        try {
            const response = await apiClient.get(`/api/v1/extraccion-masiva/sesion/${sessionId}`)
            const data = response.data

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

    descargarReporte: async (formato: 'json' | 'excel' | 'csv' | 'html') => {
        const sessionId = get().sessionId
        if (!sessionId) {
            toast.error('No hay sesión activa')
            return
        }

        try {
            // Implementación real de descarga
            const response = await apiClient.get(`/api/v1/extraccion-masiva/descargar/${sessionId}/${formato}`, {
                responseType: 'blob'
            })

            // Crear link de descarga
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `reporte_${sessionId}.${formato}`);
            document.body.appendChild(link);
            link.click();
            link.remove();

        } catch (error: any) {
            toast.error(`Error al descargar reporte ${formato}`, {
                description: error.response?.data?.detail || 'Error desconocido'
            })
        }
    },

    procesarExpedientesSeleccionados: async (numeros: string[], config?: Partial<ConfigExtraccion>): Promise<string> => {
        try {
            toast.info('Procesando expedientes seleccionados...', {
                description: `${numeros.length} expedientes`,
            })

            const payload: any = {
                numeros_expedientes: numeros,
            }

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

            set({
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
            })

            const response = await apiClient.post('/api/v1/extraccion-masiva/procesar-seleccionados', payload)
            const sessionId = response.data.session_id

            set({
                sessionId,
                estado: 'extrayendo',
            })

            const pollInterval = setInterval(() => {
                get().obtenerProgreso()
            }, 1000)

            set({ pollInterval })

            return sessionId
        } catch (error: any) {
            toast.error('Error al procesar expedientes', {
                description: error.response?.data?.detail || 'Error desconocido',
            })
            throw error
        }
    },

    resetExtraccionMasiva: () => {
        const state = get()
        if (state.pollInterval) {
            clearInterval(state.pollInterval)
        }
        if (state.websocket) {
            state.websocket.close()
        }

        set({
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
            historial_intentos: [],
            total_esperado: null,
            // Reset campos de feedback de procesamiento
            expediente_procesando: null,
            actuacion_actual: 0,
            actuaciones_total: 0,
            fase_procesamiento: '',
            mensaje_procesamiento: '',
        })
    },

    cargarListadoBase: async () => {
        try {
            const response = await apiClient.get('/api/v1/extraccion-masiva/base')
            return response.data
        } catch (error: any) {
            console.error('Error cargando listado base:', error)
            // No mostrar toast de error si es 404 (simplemente no hay base)
            if (error.response?.status !== 404) {
                toast.error('Error al cargar listado base')
            }
            throw error
        }
    },

    setEstado: (estado) => set({ estado })
}))
