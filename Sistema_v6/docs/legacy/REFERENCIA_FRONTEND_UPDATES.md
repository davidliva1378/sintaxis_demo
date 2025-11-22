# REFERENCIA PARA ACTUALIZACIONES DEL FRONTEND

## PASO 8: Actualizar expedientesStore.ts

**Archivo**: `Sistema_v6/frontend/src/stores/expedientesStore.ts`

### Agregar al interface ExpedientesState:

```typescript
interface ExpedientesState {
  // ... estados existentes ...

  // 🆕 Estados de extracción masiva avanzada
  extraccionMasiva: {
    sessionId: string | null
    estado: 'idle' | 'running' | 'paused' | 'completed' | 'error' | 'cancelled'
    progreso: {
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
    websocket: WebSocket | null
  }

  // 🆕 Acciones de extracción masiva avanzada
  iniciarExtraccionMasivaAvanzada: (config: ConfigExtraccionMasiva) => Promise<string>
  conectarWebSocket: (sessionId: string) => void
  desconectarWebSocket: () => void
  pausarExtraccion: () => Promise<void>
  reanudarExtraccion: () => Promise<void>
  cancelarExtraccion: () => Promise<void>
  obtenerProgreso: () => Promise<void>
  obtenerResumen: () => Promise<ResumenExtraccion>
  descargarReporte: (formato: 'json' | 'excel' | 'csv' | 'html') => Promise<void>
}

interface ConfigExtraccionMasiva {
  usuario?: string
  contrasena?: string
  fechaDesde?: string
  fechaHasta?: string
  estados?: string[]
  dependencias?: string[]
  umbralErrores?: number
  headless?: boolean
  exportarFormatos?: string[]
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
```

### Agregar al estado inicial:

```typescript
export const useExpedientesStore = create<ExpedientesState>((set, get) => ({
  // ... estados existentes ...

  // 🆕 Estado inicial de extracción masiva
  extraccionMasiva: {
    sessionId: null,
    estado: 'idle',
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
  },

  // ... acciones existentes ...
}))
```

### Agregar las nuevas acciones:

```typescript
  // 🆕 Iniciar extracción masiva avanzada
  iniciarExtraccionMasivaAvanzada: async (config: ConfigExtraccionMasiva): Promise<string> => {
    try {
      toast.info('Iniciando extracción masiva...', {
        description: 'Configurando proceso de extracción',
      })

      const response = await apiClient.post('/api/v1/expedientes/extraer/masivo', {
        usuario: config.usuario,
        contrasena: config.contrasena,
        fecha_desde: config.fechaDesde,
        fecha_hasta: config.fechaHasta,
        estados: config.estados,
        dependencias: config.dependencias,
        umbral_errores: config.umbralErrores || 10,
        headless: config.headless !== false,
        exportar_formatos: config.exportarFormatos || ['json'],
      })

      const sessionId = response.data.session_id

      // Actualizar estado
      set({
        extraccionMasiva: {
          ...get().extraccionMasiva,
          sessionId,
          estado: 'running',
        },
      })

      // Conectar WebSocket automáticamente
      get().conectarWebSocket(sessionId)

      toast.success('Extracción masiva iniciada', {
        description: `ID de sesión: ${sessionId}`,
      })

      return sessionId
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Error al iniciar extracción masiva'
      toast.error('Error en extracción masiva', {
        description: errorMsg,
      })
      throw error
    }
  },

  // 🆕 Conectar WebSocket para progreso en tiempo real
  conectarWebSocket: (sessionId: string) => {
    // Desconectar WebSocket anterior si existe
    const wsActual = get().extraccionMasiva.websocket
    if (wsActual) {
      wsActual.close()
    }

    // Crear nueva conexión WebSocket
    const wsUrl = `ws://localhost:8000/api/v1/expedientes/extraer/${sessionId}/ws`
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log('WebSocket conectado')
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
      try {
        const data = JSON.parse(event.data)

        // Actualizar progreso en el store
        set({
          extraccionMasiva: {
            ...get().extraccionMasiva,
            estado: data.estado === 'en_progreso' ? 'running' : data.estado,
            progreso: {
              actual: data.progreso_actual || 0,
              total: data.progreso_total || 0,
              porcentaje: data.porcentaje || 0,
              fase: data.fase || '',
              mensaje: data.mensaje || '',
              errores: data.errores || 0,
              tiempoTranscurrido: data.tiempo_transcurrido || 0,
              tiempoEstimado: data.tiempo_estimado || null,
              velocidad: data.velocidad || null,
            },
          },
        })

        // Si la extracción terminó, cerrar WebSocket
        if (['completado', 'cancelado', 'error'].includes(data.estado)) {
          ws.close()

          if (data.estado === 'completado') {
            toast.success('Extracción completada', {
              description: data.mensaje,
            })
          } else if (data.estado === 'error') {
            toast.error('Error en extracción', {
              description: data.mensaje,
            })
          }
        }
      } catch (error) {
        console.error('Error al procesar mensaje WebSocket:', error)
      }
    }

    ws.onerror = (error) => {
      console.error('Error en WebSocket:', error)
      toast.error('Error de conexión', {
        description: 'Se perdió la conexión con el servidor',
      })
    }

    ws.onclose = () => {
      console.log('WebSocket desconectado')
      set({
        extraccionMasiva: {
          ...get().extraccionMasiva,
          websocket: null,
        },
      })
    }

    // Guardar WebSocket en el store
    set({
      extraccionMasiva: {
        ...get().extraccionMasiva,
        websocket: ws,
      },
    })
  },

  // 🆕 Desconectar WebSocket
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

  // 🆕 Pausar extracción
  pausarExtraccion: async () => {
    const sessionId = get().extraccionMasiva.sessionId
    if (!sessionId) {
      toast.error('No hay extracción activa')
      return
    }

    try {
      await apiClient.post(`/api/v1/expedientes/extraer/${sessionId}/pausar`)

      set({
        extraccionMasiva: {
          ...get().extraccionMasiva,
          estado: 'paused',
        },
      })

      toast.success('Extracción pausada')
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Error al pausar extracción'
      toast.error('Error', { description: errorMsg })
      throw error
    }
  },

  // 🆕 Reanudar extracción
  reanudarExtraccion: async () => {
    const sessionId = get().extraccionMasiva.sessionId
    if (!sessionId) {
      toast.error('No hay extracción activa')
      return
    }

    try {
      await apiClient.post(`/api/v1/expedientes/extraer/${sessionId}/reanudar`)

      set({
        extraccionMasiva: {
          ...get().extraccionMasiva,
          estado: 'running',
        },
      })

      toast.success('Extracción reanudada')
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Error al reanudar extracción'
      toast.error('Error', { description: errorMsg })
      throw error
    }
  },

  // 🆕 Cancelar extracción
  cancelarExtraccion: async () => {
    const sessionId = get().extraccionMasiva.sessionId
    if (!sessionId) {
      toast.error('No hay extracción activa')
      return
    }

    try {
      await apiClient.post(`/api/v1/expedientes/extraer/${sessionId}/cancelar`)

      set({
        extraccionMasiva: {
          ...get().extraccionMasiva,
          estado: 'cancelled',
        },
      })

      // Desconectar WebSocket
      get().desconectarWebSocket()

      toast.success('Extracción cancelada')
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Error al cancelar extracción'
      toast.error('Error', { description: errorMsg })
      throw error
    }
  },

  // 🆕 Obtener progreso actual
  obtenerProgreso: async () => {
    const sessionId = get().extraccionMasiva.sessionId
    if (!sessionId) return

    try {
      const response = await apiClient.get(`/api/v1/expedientes/extraer/${sessionId}/progreso`)
      const data = response.data

      set({
        extraccionMasiva: {
          ...get().extraccionMasiva,
          estado: data.estado === 'en_progreso' ? 'running' : data.estado,
          progreso: {
            actual: data.progreso_actual,
            total: data.progreso_total,
            porcentaje: data.porcentaje,
            fase: data.fase,
            mensaje: data.mensaje,
            errores: data.errores,
            tiempoTranscurrido: data.tiempo_transcurrido,
            tiempoEstimado: data.tiempo_estimado,
            velocidad: data.velocidad,
          },
        },
      })
    } catch (error: any) {
      console.error('Error al obtener progreso:', error)
    }
  },

  // 🆕 Obtener resumen final
  obtenerResumen: async (): Promise<ResumenExtraccion> => {
    const sessionId = get().extraccionMasiva.sessionId
    if (!sessionId) {
      throw new Error('No hay extracción activa')
    }

    try {
      const response = await apiClient.get(`/api/v1/expedientes/extraer/${sessionId}/resumen`)
      return response.data
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Error al obtener resumen'
      toast.error('Error', { description: errorMsg })
      throw error
    }
  },

  // 🆕 Descargar reporte
  descargarReporte: async (formato: 'json' | 'excel' | 'csv' | 'html') => {
    const sessionId = get().extraccionMasiva.sessionId
    if (!sessionId) {
      toast.error('No hay extracción activa')
      return
    }

    try {
      const response = await apiClient.get(
        `/api/v1/expedientes/extraer/${sessionId}/descargar/${formato}`,
        { responseType: 'blob' }
      )

      // Crear enlace de descarga
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `extraccion_${sessionId}.${formato}`)
      document.body.appendChild(link)
      link.click()
      link.remove()

      toast.success('Reporte descargado', {
        description: `Formato: ${formato.toUpperCase()}`,
      })
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Error al descargar reporte'
      toast.error('Error', { description: errorMsg })
      throw error
    }
  },
```

---

## PASO 9: Actualizar ExtraccionMasivaDialog.tsx

**Archivo**: `Sistema_v6/frontend/src/components/expedientes/ExtraccionMasivaDialog.tsx`

### Cambios principales:

1. **Agregar controles de pausar/reanudar/cancelar**
2. **Mostrar progreso en tiempo real con WebSocket**
3. **Agregar opciones de descarga**
4. **Mejorar visualización de estadísticas**

### Código de referencia (fragmento del componente mejorado):

```typescript
import { useEffect } from 'react'
import { useExpedientesStore } from '@/stores/expedientesStore'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { Play, Pause, X, Download } from 'lucide-react'

export function ExtraccionMasivaDialog() {
  const {
    extraccionMasiva,
    iniciarExtraccionMasivaAvanzada,
    pausarExtraccion,
    reanudarExtraccion,
    cancelarExtraccion,
    descargarReporte,
    desconectarWebSocket,
  } = useExpedientesStore()

  // Limpiar WebSocket al desmontar
  useEffect(() => {
    return () => {
      desconectarWebSocket()
    }
  }, [])

  const handleIniciar = async () => {
    await iniciarExtraccionMasivaAvanzada({
      headless: true,
      exportarFormatos: ['json', 'excel'],
    })
  }

  const handlePausar = async () => {
    await pausarExtraccion()
  }

  const handleReanudar = async () => {
    await reanudarExtraccion()
  }

  const handleCancelar = async () => {
    if (confirm('¿Estás seguro de cancelar la extracción?')) {
      await cancelarExtraccion()
    }
  }

  const handleDescargar = async (formato: 'json' | 'excel' | 'csv') => {
    await descargarReporte(formato)
  }

  // Formatear tiempo
  const formatearTiempo = (segundos: number) => {
    const horas = Math.floor(segundos / 3600)
    const minutos = Math.floor((segundos % 3600) / 60)
    const segs = Math.floor(segundos % 60)
    return `${horas}h ${minutos}m ${segs}s`
  }

  return (
    <div className="space-y-4">
      {/* Cabecera con estado */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Extracción Masiva</h2>
        <Badge variant={extraccionMasiva.estado === 'running' ? 'default' : 'secondary'}>
          {extraccionMasiva.estado.toUpperCase()}
        </Badge>
      </div>

      {/* Progreso */}
      {extraccionMasiva.sessionId && (
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>{extraccionMasiva.progreso.fase}</span>
            <span>{extraccionMasiva.progreso.porcentaje.toFixed(1)}%</span>
          </div>

          <Progress value={extraccionMasiva.progreso.porcentaje} />

          <div className="text-sm text-muted-foreground">
            {extraccionMasiva.progreso.mensaje}
          </div>

          {/* Estadísticas */}
          <div className="grid grid-cols-3 gap-4 mt-4">
            <div className="text-center">
              <div className="text-2xl font-bold">
                {extraccionMasiva.progreso.actual}/{extraccionMasiva.progreso.total}
              </div>
              <div className="text-xs text-muted-foreground">Progreso</div>
            </div>

            <div className="text-center">
              <div className="text-2xl font-bold text-red-500">
                {extraccionMasiva.progreso.errores}
              </div>
              <div className="text-xs text-muted-foreground">Errores</div>
            </div>

            <div className="text-center">
              <div className="text-2xl font-bold">
                {extraccionMasiva.progreso.velocidad?.toFixed(2) || '0.00'}/s
              </div>
              <div className="text-xs text-muted-foreground">Velocidad</div>
            </div>
          </div>

          {/* Tiempos */}
          <div className="grid grid-cols-2 gap-4 mt-2">
            <div className="text-sm">
              <span className="text-muted-foreground">Transcurrido: </span>
              <span className="font-medium">
                {formatearTiempo(extraccionMasiva.progreso.tiempoTranscurrido)}
              </span>
            </div>

            {extraccionMasiva.progreso.tiempoEstimado && (
              <div className="text-sm">
                <span className="text-muted-foreground">Estimado: </span>
                <span className="font-medium">
                  {formatearTiempo(extraccionMasiva.progreso.tiempoEstimado)}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Controles */}
      <div className="flex gap-2">
        {extraccionMasiva.estado === 'idle' && (
          <Button onClick={handleIniciar} className="flex-1">
            <Play className="mr-2 h-4 w-4" />
            Iniciar Extracción
          </Button>
        )}

        {extraccionMasiva.estado === 'running' && (
          <>
            <Button onClick={handlePausar} variant="outline" className="flex-1">
              <Pause className="mr-2 h-4 w-4" />
              Pausar
            </Button>
            <Button onClick={handleCancelar} variant="destructive">
              <X className="mr-2 h-4 w-4" />
              Cancelar
            </Button>
          </>
        )}

        {extraccionMasiva.estado === 'paused' && (
          <>
            <Button onClick={handleReanudar} className="flex-1">
              <Play className="mr-2 h-4 w-4" />
              Reanudar
            </Button>
            <Button onClick={handleCancelar} variant="destructive">
              <X className="mr-2 h-4 w-4" />
              Cancelar
            </Button>
          </>
        )}

        {extraccionMasiva.estado === 'completed' && (
          <div className="flex gap-2 flex-1">
            <Button onClick={() => handleDescargar('json')} variant="outline" className="flex-1">
              <Download className="mr-2 h-4 w-4" />
              JSON
            </Button>
            <Button onClick={() => handleDescargar('excel')} variant="outline" className="flex-1">
              <Download className="mr-2 h-4 w-4" />
              Excel
            </Button>
            <Button onClick={() => handleDescargar('csv')} variant="outline" className="flex-1">
              <Download className="mr-2 h-4 w-4" />
              CSV
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
```

---

## Notas Importantes

1. **WebSocket URL**: Ajustar según el entorno (desarrollo/producción)
2. **Autenticación**: Agregar tokens JWT si es necesario
3. **Error Handling**: Mejorar manejo de errores según necesidades
4. **Tipos TypeScript**: Definir interfaces completas en archivos separados
5. **Testing**: Agregar tests unitarios para las nuevas funcionalidades

---

## Dependencias adicionales necesarias

Si no están instaladas, agregar:

```bash
npm install lucide-react  # Para iconos
```

---

## Variables de entorno

Agregar al `.env` del frontend:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

Y usar en el código:

```typescript
const wsUrl = `${import.meta.env.VITE_WS_URL}/api/v1/expedientes/extraer/${sessionId}/ws`
```
