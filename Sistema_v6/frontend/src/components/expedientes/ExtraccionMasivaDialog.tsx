import { useState, useEffect, useRef, useMemo } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { Switch } from '@/components/ui/switch'
import { Progress } from '@/components/ui/progress'
import { X, Download, Loader2, Filter, CheckSquare, Square, Pause, Play, XCircle, FileDown, Maximize2, Minimize2 } from 'lucide-react'
import { useExpedientesStore } from '@/stores/expedientesStore'
import type { ExpedienteResumen, ConfigExtraccion } from '@/types/expediente'
import { FiltradoExpedientesDialog } from '../FiltradoExpedientesDialog'
import { DateInputArgentino } from '@/components/ui/date-input-argentino'
import { ComparacionDetalladaPanel } from './ComparacionDetalladaPanel'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'

interface ExtraccionMasivaDialogProps {
  onClose: () => void
  onSuccess?: (expedientes: ExpedienteResumen[]) => void
}

interface Filtros {
  texto: string
  dependencias: string[]  // Cambio de 'fuero' a array
  situacion: string[]
  ordenFecha: 'desc' | 'asc' | 'ninguno'
  fechaActuacionDesde: string  // YYYY-MM-DD
  fechaActuacionHasta: string  // YYYY-MM-DD
  usarFiltroFechaActuacion: boolean
  minActuaciones: number
  usarMinActuaciones: boolean
}

export default function ExtraccionMasivaDialog({ onClose, onSuccess }: ExtraccionMasivaDialogProps) {
  // Usar selectores específicos de Zustand para asegurar re-renders
  const extraccionMasiva = useExpedientesStore((state) => state.extraccionMasiva)
  const isExtractingMasivo = useExpedientesStore((state) => state.isExtractingMasivo)
  const iniciarExtraccionMasivaAvanzada = useExpedientesStore((state) => state.iniciarExtraccionMasivaAvanzada)
  const pausarExtraccion = useExpedientesStore((state) => state.pausarExtraccion)
  const reanudarExtraccion = useExpedientesStore((state) => state.reanudarExtraccion)
  const cancelarExtraccion = useExpedientesStore((state) => state.cancelarExtraccion)
  const desconectarWebSocket = useExpedientesStore((state) => state.desconectarWebSocket)
  const procesarExpedientesSeleccionados = useExpedientesStore((state) => state.procesarExpedientesSeleccionados)
  const resetExtraccionMasiva = useExpedientesStore((state) => state.resetExtraccionMasiva)

  // Estados
  const [expedientesExtraidos, setExpedientesExtraidos] = useState<ExpedienteResumen[]>([])
  const [expedientesFiltrados, setExpedientesFiltrados] = useState<ExpedienteResumen[]>([])
  const [expedientesSeleccionados, setExpedientesSeleccionados] = useState<Set<string>>(new Set())
  const [procesarConPDF, setProcesarConPDF] = useState(false)
  const [tipoExtraccion, setTipoExtraccion] = useState<'masiva' | 'seleccionados'>('masiva')
  const [logMensajes, setLogMensajes] = useState<string[]>([])
  const [mostrarOpcionesAvanzadas, setMostrarOpcionesAvanzadas] = useState(false)
  const [mostrarFiltrosExtraccion, setMostrarFiltrosExtraccion] = useState(false)
  const [mostrarReporte, setMostrarReporte] = useState(false)
  const [countdown, setCountdown] = useState(5)
  const [maximizado, setMaximizado] = useState(false)
  const [mostrarModalReintento, setMostrarModalReintento] = useState(false)

  // Ref para evitar mostrar reporte múltiples veces para la misma sesión
  const reporteMostradoRef = useRef<string | null>(null)

  // Configuración de extracción
  const [config, setConfig] = useState<ConfigExtraccion>({
    headless: true,
    umbral_errores: 10,
  })

  // Filtros
  const [filtros, setFiltros] = useState<Filtros>({
    texto: '',
    dependencias: [],
    situacion: [],
    ordenFecha: 'ninguno',
    fechaActuacionDesde: '',
    fechaActuacionHasta: '',
    usarFiltroFechaActuacion: false,
    minActuaciones: 5,
    usarMinActuaciones: false
  })

  // Estados de paginación
  const [paginaActual, setPaginaActual] = useState(1)
  const ITEMS_POR_PAGINA = 50

  // Resetear estado al montar el componente (limpiar estado previo)
  useEffect(() => {
    resetExtraccionMasiva()
  }, [])

  // Funciones auxiliares para fechas
  const parsearFecha = (fechaStr: string): Date | null => {
    if (!fechaStr || fechaStr === '') return null
    const [year, month, day] = fechaStr.split('-').map(Number)
    if (!year || !month || !day) return null
    return new Date(year, month - 1, day)
  }

  const formatearFecha = (fechaStr: string): string => {
    const fecha = parsearFecha(fechaStr)
    if (!fecha) return ''
    const dia = fecha.getDate().toString().padStart(2, '0')
    const mes = (fecha.getMonth() + 1).toString().padStart(2, '0')
    return `${dia}/${mes}/${fecha.getFullYear()}`
  }

  // Calcular opciones de Dependencia con conteo
  const opcionesDependencia = useMemo(() => {
    const counts = new Map<string, number>()
    expedientesExtraidos.forEach(exp => {
      const dep = exp.dependencia || 'Sin dependencia'
      counts.set(dep, (counts.get(dep) || 0) + 1)
    })
    return Array.from(counts.entries())
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([valor, count]) => ({ valor, count }))
  }, [expedientesExtraidos])

  // Calcular opciones de Situación con conteo
  const opcionesSituacion = useMemo(() => {
    const counts = new Map<string, number>()
    expedientesExtraidos.forEach(exp => {
      const sit = exp.situacion || 'Sin situación'
      counts.set(sit, (counts.get(sit) || 0) + 1)
    })
    return Array.from(counts.entries())
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([valor, count]) => ({ valor, count }))
  }, [expedientesExtraidos])

  // Aplicar filtros cuando cambien
  useEffect(() => {
    if (expedientesExtraidos.length > 0) {
      aplicarFiltros()
    }
  }, [filtros, expedientesExtraidos])

  // Monitorear progreso de extracción y mostrar reporte cuando termine
  useEffect(() => {
    const cargarExpedientes = async () => {
      // Solo cargar si completó y no se mostró reporte para esta sesión
      // NO intentar cargar para procesamiento de seleccionados (no genera listado)
      if (
        extraccionMasiva.estado === 'completado' &&
        extraccionMasiva.sessionId &&
        reporteMostradoRef.current !== extraccionMasiva.sessionId &&
        tipoExtraccion === 'masiva' // Solo para extracción masiva inicial
      ) {
        try {
          // Cargar expedientes del listado completado
          const response = await fetch(`http://localhost:8000/api/v1/extraccion-masiva/listado/${extraccionMasiva.sessionId}/expedientes`)
          const data = await response.json()

          const expedientesData = data.expedientes || []
          setExpedientesExtraidos(expedientesData)
          setExpedientesFiltrados(expedientesData)

          // Seleccionar todos por defecto
          const seleccionados = new Set(expedientesData.map((exp: ExpedienteResumen) => exp.numero))
          setExpedientesSeleccionados(seleccionados)

          // Mostrar reporte y marcar sesión como vista
          setMostrarReporte(true)
          setCountdown(5)
          reporteMostradoRef.current = extraccionMasiva.sessionId
        } catch (error) {
          console.error('Error al cargar expedientes:', error)
          agregarLog(`❌ Error al cargar expedientes: ${error}`)
        }
      } else if (
        extraccionMasiva.estado === 'completado' &&
        extraccionMasiva.sessionId &&
        reporteMostradoRef.current !== extraccionMasiva.sessionId &&
        tipoExtraccion === 'seleccionados' // Para procesamiento de seleccionados
      ) {
        // Solo mostrar reporte sin cargar expedientes (ya están cargados)
        // NO iniciar countdown automático - usuario debe decidir manualmente
        setMostrarReporte(true)
        setCountdown(0) // Desactivar countdown automático
        reporteMostradoRef.current = extraccionMasiva.sessionId
      }
    }

    cargarExpedientes()
  }, [extraccionMasiva.estado, extraccionMasiva.sessionId, tipoExtraccion])

  // Detectar estado error_agotado y mostrar modal
  useEffect(() => {
    if (extraccionMasiva.estado === 'error_agotado' && extraccionMasiva.sessionId) {
      setMostrarModalReintento(true)
    }
  }, [extraccionMasiva.estado, extraccionMasiva.sessionId])

  // Countdown automático para transición a filtros (solo para extracción masiva)
  useEffect(() => {
    // Solo aplicar countdown automático para extracción masiva inicial
    if (mostrarReporte && countdown > 0 && tipoExtraccion === 'masiva') {
      const timer = setTimeout(() => {
        setCountdown(countdown - 1)
      }, 1000)
      return () => clearTimeout(timer)
    } else if (mostrarReporte && countdown === 0 && tipoExtraccion === 'masiva') {
      // Transición automática a filtros solo para extracción masiva
      setMostrarReporte(false)
    }
  }, [mostrarReporte, countdown, tipoExtraccion])

  // Ocultar reporte cuando comience el procesamiento de seleccionados
  useEffect(() => {
    if (tipoExtraccion === 'seleccionados' && extraccionMasiva.estado === 'extrayendo' && mostrarReporte) {
      setMostrarReporte(false)
    }
  }, [tipoExtraccion, extraccionMasiva.estado, mostrarReporte])

  // Cleanup: resetear estado completo al desmontar
  useEffect(() => {
    return () => {
      resetExtraccionMasiva()
    }
  }, [resetExtraccionMasiva])

  const aplicarFiltros = () => {
    let filtered = [...expedientesExtraidos]

    // Función auxiliar para normalizar texto (quitar tildes, minúsculas)
    const normalizar = (texto: string) => {
      return texto
        .toLowerCase()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
    }

    // Filtro por texto
    if (filtros.texto) {
      const textoNormalizado = normalizar(filtros.texto)
      filtered = filtered.filter(exp =>
        normalizar(exp.numero).includes(textoNormalizado) ||
        normalizar(exp.caratula).includes(textoNormalizado)
      )
    }

    // Filtro por Dependencias (múltiple)
    if (filtros.dependencias.length > 0) {
      filtered = filtered.filter(exp =>
        filtros.dependencias.includes(exp.dependencia)
      )
    }

    // Filtro por Situación (múltiple)
    if (filtros.situacion.length > 0) {
      filtered = filtered.filter(exp =>
        filtros.situacion.includes(exp.situacion)
      )
    }

    // Filtro por Rango de Fechas
    if (filtros.usarFiltroFechaActuacion) {
      filtered = filtered.filter(exp => {
        const fecha = parsearFecha(exp.ultima_actuacion)
        if (!fecha) return false

        const desde = filtros.fechaActuacionDesde
          ? parsearFecha(filtros.fechaActuacionDesde)
          : null
        const hasta = filtros.fechaActuacionHasta
          ? parsearFecha(filtros.fechaActuacionHasta)
          : null

        if (desde && fecha < desde) return false
        if (hasta && fecha > hasta) return false

        return true
      })
    }

    // Ordenamiento por fecha
    if (filtros.ordenFecha !== 'ninguno') {
      filtered.sort((a, b) => {
        const fechaA = parsearFecha(a.ultima_actuacion)
        const fechaB = parsearFecha(b.ultima_actuacion)

        if (!fechaA && !fechaB) return 0
        if (!fechaA) return 1
        if (!fechaB) return -1

        const diff = fechaA.getTime() - fechaB.getTime()
        return filtros.ordenFecha === 'asc' ? diff : -diff
      })
    }

    setExpedientesFiltrados(filtered)

    // Seleccionar todos los filtrados por defecto
    const nuevosSeleccionados = new Set(filtered.map(exp => exp.numero))
    setExpedientesSeleccionados(nuevosSeleccionados)

    // Resetear a página 1 cuando cambian filtros
    setPaginaActual(1)
  }

  const handleIniciarExtraccion = async () => {
    setLogMensajes([])

    try {
      // Iniciar extracción masiva avanzada con la configuración del usuario
      await iniciarExtraccionMasivaAvanzada(config)

      // El estado cambia automáticamente a 'extrayendo' en el store
      // El progreso se mostrará en tiempo real

    } catch (error) {
      agregarLog(`❌ Error durante la extracción: ${error}`)
      // El error ya se muestra en el toast por el store
    }
  }

  const handlePausar = async () => {
    try {
      await pausarExtraccion()
    } catch (error) {
      console.error('Error al pausar:', error)
    }
  }

  const handleReanudar = async () => {
    try {
      await reanudarExtraccion()
    } catch (error) {
      console.error('Error al reanudar:', error)
    }
  }

  const handleCancelar = async () => {
    try {
      await cancelarExtraccion()
      // El estado se resetea automáticamente en el store
    } catch (error) {
      console.error('Error al cancelar:', error)
    }
  }

  const handleReintentar = async () => {
    setMostrarModalReintento(false)
    resetExtraccionMasiva()
    // El usuario deberá iniciar manualmente una nueva extracción
    agregarLog('🔄 Reintentos agotados. Puede iniciar una nueva extracción.')
  }

  const handleContinuarConParciales = () => {
    setMostrarModalReintento(false)
    // Intentar cargar los expedientes parciales obtenidos
    const cargarExpedientesParciales = async () => {
      try {
        if (extraccionMasiva.sessionId) {
          const response = await fetch(`http://localhost:8000/api/v1/extraccion-masiva/listado/${extraccionMasiva.sessionId}/expedientes`)
          const data = await response.json()
          if (data.expedientes && data.expedientes.length > 0) {
            setExpedientesExtraidos(data.expedientes)
            setMostrarReporte(false)
            agregarLog(`✅ ${data.expedientes.length} expedientes parciales cargados para filtrado`)
          } else {
            agregarLog('⚠️ No se obtuvieron expedientes en los intentos realizados')
          }
        }
      } catch (error) {
        console.error('Error al cargar expedientes parciales:', error)
        agregarLog('❌ Error al cargar expedientes parciales')
      }
    }
    cargarExpedientesParciales()
  }

  const handleDescargarReporte = async (formato: 'json' | 'excel' | 'csv' | 'html') => {
    try {
      await descargarReporte(formato)
    } catch (error) {
      console.error('Error al descargar reporte:', error)
    }
  }

  const agregarLog = (mensaje: string) => {
    setLogMensajes(prev => [...prev, `${new Date().toLocaleTimeString()}: ${mensaje}`])
  }

  const handleToggleExpediente = (numero: string) => {
    const nuevosSeleccionados = new Set(expedientesSeleccionados)
    if (nuevosSeleccionados.has(numero)) {
      nuevosSeleccionados.delete(numero)
    } else {
      nuevosSeleccionados.add(numero)
    }
    setExpedientesSeleccionados(nuevosSeleccionados)
  }

  const handleSeleccionarTodos = () => {
    const todos = new Set(expedientesFiltrados.map(exp => exp.numero))
    setExpedientesSeleccionados(todos)
  }

  const handleDeseleccionarTodos = () => {
    setExpedientesSeleccionados(new Set())
  }

  const handleInvertirSeleccion = () => {
    const nuevosSeleccionados = new Set<string>()
    expedientesFiltrados.forEach(exp => {
      if (!expedientesSeleccionados.has(exp.numero)) {
        nuevosSeleccionados.add(exp.numero)
      }
    })
    setExpedientesSeleccionados(nuevosSeleccionados)
  }

  const handleLimpiarFiltros = () => {
    setFiltros({
      texto: '',
      dependencias: [],
      situacion: [],
      ordenFecha: 'ninguno',
      fechaActuacionDesde: '',
      fechaActuacionHasta: '',
      usarFiltroFechaActuacion: false,
      minActuaciones: 5,
      usarMinActuaciones: false
    })
    setPaginaActual(1)
  }

  const handleConfirmar = async () => {
    const expedientesConfirmados = expedientesFiltrados.filter(exp =>
      expedientesSeleccionados.has(exp.numero)
    )

    if (expedientesConfirmados.length === 0) {
      return
    }

    try {
      // Cambiar tipo de extracción y ocultar reporte
      setTipoExtraccion('seleccionados')
      setMostrarReporte(false)

      // Enviar expedientes seleccionados para procesamiento con configuración
      const numeros = expedientesConfirmados.map(exp => exp.numero)

      // Preparar configuración incluyendo procesarConPDF y otras opciones
      const configProcesamiento: Partial<ConfigExtraccion> = {
        ...config,
        procesar_con_pdf: procesarConPDF,
      }

      // La función del store cambiará el estado a 'iniciando' inmediatamente
      // Esto permite que React renderice la vista de progreso antes de la llamada al backend
      const sessionId = await procesarExpedientesSeleccionados(numeros, configProcesamiento)

      // El estado cambia automáticamente a 'extrayendo' en el store después de la respuesta
      // El progreso se mostrará en tiempo real

      // No llamar onSuccess aquí - se puede llamar cuando el usuario cierre el diálogo
      // El callback onSuccess solo llama a listarExpedientes() que se ejecutará al cerrar
    } catch (error) {
      console.error('Error al procesar expedientes:', error)
      // El toast de error ya se muestra en el store
    }
  }

  const handleToggleSituacion = (situacion: string) => {
    const nuevasSituaciones = filtros.situacion.includes(situacion)
      ? filtros.situacion.filter(s => s !== situacion)
      : [...filtros.situacion, situacion]

    setFiltros({ ...filtros, situacion: nuevasSituaciones })
  }

  const handleVolverAFiltrado = () => {
    // Resetear selección
    setExpedientesSeleccionados(new Set())

    // Volver a mostrar filtrado
    setMostrarReporte(false)

    // Resetear tipo de extracción para próxima vez
    setTipoExtraccion('masiva')
  }

  const handleCerrarDialogo = () => {
    // Resetear estado de extracción masiva
    resetExtraccionMasiva()

    // Resetear estados locales
    setMostrarReporte(false)
    setTipoExtraccion('masiva')

    // Llamar onSuccess si hay expedientes procesados (para refrescar la lista en el padre)
    if (tipoExtraccion === 'seleccionados' && expedientesExtraidos.length > 0 && onSuccess) {
      onSuccess(expedientesExtraidos)
    }

    // Cerrar el diálogo
    onClose()
  }

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget && !isExtractingMasivo) {
          onClose()
        }
      }}
    >
      <Card className={`w-full overflow-hidden flex flex-col transition-all duration-200 ${
        maximizado
          ? 'max-w-[98vw] h-[95vh]'
          : 'max-w-6xl max-h-[90vh]'
      }`}>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Download className="h-5 w-5 text-blue-600" />
              <CardTitle>Extracción Masiva de Expedientes</CardTitle>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setMaximizado(!maximizado)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
                title={maximizado ? "Restaurar tamaño" : "Maximizar"}
              >
                {maximizado ? (
                  <Minimize2 className="h-5 w-5" />
                ) : (
                  <Maximize2 className="h-5 w-5" />
                )}
              </button>
              <button
                onClick={onClose}
                disabled={isExtractingMasivo}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 disabled:opacity-50"
                title="Cerrar"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          </div>
          <CardDescription>
            Extraer todos los expedientes del PJN y seleccionar cuáles monitorear
          </CardDescription>
        </CardHeader>

        <CardContent className="flex-1 overflow-auto">
          {/* Tab de Configuración */}
          {extraccionMasiva.estado === 'inactivo' && (
            <div className="space-y-6">
              {/* Opciones Básicas */}
              <div className="space-y-4">
                <h3 className="font-semibold text-lg">Opciones de Extracción</h3>

                {/* Headless */}
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="headless"
                    checked={config.headless}
                    onCheckedChange={(checked) => setConfig({...config, headless: checked as boolean})}
                  />
                  <label
                    htmlFor="headless"
                    className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                  >
                    Modo invisible (más rápido, ejecutar sin interfaz gráfica)
                  </label>
                </div>

                {/* Umbral de errores */}
                <div className="space-y-2">
                  <label htmlFor="umbral-errores" className="text-sm font-medium">
                    Umbral de errores consecutivos (1-100)
                  </label>
                  <Input
                    id="umbral-errores"
                    type="number"
                    min={1}
                    max={100}
                    value={config.umbral_errores}
                    onChange={(e) => setConfig({...config, umbral_errores: parseInt(e.target.value) || 10})}
                    className="w-32"
                  />
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Detener extracción tras N errores consecutivos
                  </p>
                </div>

                <div className="bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                  <p className="text-sm text-blue-900 dark:text-blue-100">
                    ℹ️ La extracción puede tardar varios minutos dependiendo de la cantidad de expedientes.
                    El proceso se ejecuta de forma incremental para mayor confiabilidad.
                  </p>
                </div>
              </div>

              {/* Opciones Avanzadas (Colapsable) */}
              <div className="space-y-4 border-t pt-4">
                <button
                  type="button"
                  onClick={() => setMostrarOpcionesAvanzadas(!mostrarOpcionesAvanzadas)}
                  className="flex items-center justify-between w-full text-left"
                >
                  <h3 className="font-semibold text-lg">Opciones Avanzadas</h3>
                  <span className="text-sm text-gray-500">
                    {mostrarOpcionesAvanzadas ? '▼' : '▶'}
                  </span>
                </button>

                {mostrarOpcionesAvanzadas && (
                  <div className="space-y-4 pl-4">
                    {/* Timeout de página */}
                    <div className="space-y-2">
                      <label htmlFor="timeout-pagina" className="text-sm font-medium">
                        Timeout de página (5000-60000 ms)
                      </label>
                      <Input
                        id="timeout-pagina"
                        type="number"
                        min={5000}
                        max={60000}
                        step={1000}
                        value={config.timeout_pagina || 30000}
                        onChange={(e) => setConfig({...config, timeout_pagina: parseInt(e.target.value) || 30000})}
                        className="w-40"
                      />
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        Tiempo máximo de espera para cargar cada página
                      </p>
                    </div>

                    {/* Máximo de reintentos */}
                    <div className="space-y-2">
                      <label htmlFor="max-reintentos" className="text-sm font-medium">
                        Máximo de reintentos (1-10)
                      </label>
                      <Input
                        id="max-reintentos"
                        type="number"
                        min={1}
                        max={10}
                        value={config.max_reintentos || 3}
                        onChange={(e) => setConfig({...config, max_reintentos: parseInt(e.target.value) || 3})}
                        className="w-32"
                      />
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        Número de reintentos por página fallida
                      </p>
                    </div>

                    {/* Formatos de exportación */}
                    <div className="space-y-2">
                      <label className="text-sm font-medium">
                        Formatos de exportación
                      </label>
                      <div className="space-y-2">
                        {['json', 'excel', 'csv', 'html'].map((formato) => (
                          <div key={formato} className="flex items-center space-x-2">
                            <Checkbox
                              id={`formato-${formato}`}
                              checked={config.exportar_formatos?.includes(formato) ?? (formato === 'json')}
                              onCheckedChange={(checked) => {
                                const formatos = config.exportar_formatos || ['json']
                                if (checked) {
                                  setConfig({...config, exportar_formatos: [...formatos, formato]})
                                } else {
                                  setConfig({...config, exportar_formatos: formatos.filter(f => f !== formato)})
                                }
                              }}
                            />
                            <label
                              htmlFor={`formato-${formato}`}
                              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                            >
                              {formato.toUpperCase()}
                            </label>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Separator */}
                    <div className="border-t my-4"></div>
                    <p className="text-sm font-semibold text-gray-700 dark:text-gray-300">Control de Paginación</p>

                    {/* Detener en duplicado */}
                    <div className="flex items-center justify-between space-x-4">
                      <div className="flex-1">
                        <label htmlFor="detener-duplicado" className="text-sm font-medium">
                          Detener al encontrar duplicados
                        </label>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          Detiene la extracción cuando encuentra expedientes duplicados entre páginas
                        </p>
                      </div>
                      <Switch
                        id="detener-duplicado"
                        checked={config.detener_en_duplicado ?? true}
                        onCheckedChange={(checked) => setConfig({...config, detener_en_duplicado: checked})}
                      />
                    </div>

                    {/* Omitir duplicados */}
                    <div className="flex items-center justify-between space-x-4">
                      <div className="flex-1">
                        <label htmlFor="omitir-duplicado" className="text-sm font-medium">
                          Omitir expedientes duplicados
                        </label>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          Filtra automáticamente los expedientes duplicados de la lista final
                        </p>
                      </div>
                      <Switch
                        id="omitir-duplicado"
                        checked={config.omitir_duplicados ?? true}
                        onCheckedChange={(checked) => setConfig({...config, omitir_duplicados: checked})}
                      />
                    </div>

                    {/* Límite de páginas */}
                    <div className="space-y-2">
                      <label htmlFor="max-paginas" className="text-sm font-medium">
                        Límite de páginas (opcional)
                      </label>
                      <Input
                        id="max-paginas"
                        type="number"
                        min={1}
                        max={500}
                        placeholder="Sin límite"
                        value={config.max_paginas || ''}
                        onChange={(e) => setConfig({...config, max_paginas: e.target.value ? parseInt(e.target.value) : undefined})}
                        className="w-40"
                      />
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        Número máximo de páginas a procesar (dejar vacío = sin límite)
                      </p>
                    </div>

                    {/* Tiempo máximo */}
                    <div className="space-y-2">
                      <label htmlFor="tiempo-maximo" className="text-sm font-medium">
                        Tiempo máximo (segundos, opcional)
                      </label>
                      <Input
                        id="tiempo-maximo"
                        type="number"
                        min={60}
                        max={7200}
                        placeholder="Sin límite"
                        value={config.tiempo_maximo_segundos || ''}
                        onChange={(e) => setConfig({...config, tiempo_maximo_segundos: e.target.value ? parseInt(e.target.value) : undefined})}
                        className="w-40"
                      />
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        Tiempo máximo antes de detener la extracción (dejar vacío = sin límite)
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* Filtros de Extracción (Colapsable) */}
              <div className="space-y-4 border-t pt-4">
                <button
                  type="button"
                  onClick={() => setMostrarFiltrosExtraccion(!mostrarFiltrosExtraccion)}
                  className="flex items-center justify-between w-full text-left"
                >
                  <h3 className="font-semibold text-lg">Filtros de Extracción</h3>
                  <span className="text-sm text-gray-500">
                    {mostrarFiltrosExtraccion ? '▼' : '▶'}
                  </span>
                </button>

                {mostrarFiltrosExtraccion && (
                  <div className="space-y-4 pl-4">
                  {/* Fecha de corte */}
                  <DateInputArgentino
                    label="Fecha de corte (opcional)"
                    value={config.fecha_corte}
                    onChange={(value) => setConfig({...config, fecha_corte: value})}
                    placeholder="dd/mm/aaaa"
                    className="w-48"
                  />
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Solo extraer expedientes desde esta fecha
                  </p>

                  {/* Procesar con PDF */}
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="procesar-pdf"
                      checked={procesarConPDF}
                      onCheckedChange={(checked) => setProcesarConPDF(checked as boolean)}
                    />
                    <label
                      htmlFor="procesar-pdf"
                      className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                    >
                      Procesar expedientes con procesador_pdf (clasificación y análisis de vencimientos)
                    </label>
                  </div>
                  </div>
                )}
              </div>

              {/* Botón Iniciar */}
              <div>
                <Button
                  onClick={handleIniciarExtraccion}
                  disabled={extraccionMasiva.estado === 'extrayendo'}
                  className="w-full"
                  size="lg"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Iniciar Extracción Masiva Avanzada
                </Button>
              </div>
            </div>
          )}

          {/* Tab de Iniciando */}
          {extraccionMasiva.estado === 'iniciando' && (
            <div className="flex flex-col items-center justify-center py-12 space-y-4">
              <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
              <div className="text-center space-y-2">
                <h3 className="font-semibold text-lg">Iniciando Extracción Masiva</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {extraccionMasiva.progreso.mensaje || 'Preparando navegador y autenticando...'}
                </p>
              </div>
            </div>
          )}

          {/* Tab de Error */}
          {extraccionMasiva.estado === 'error' && (
            <div className="space-y-6">
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
                <div className="flex items-start gap-3">
                  <XCircle className="h-6 w-6 text-red-600 flex-shrink-0 mt-0.5" />
                  <div className="flex-1 space-y-2">
                    <h3 className="font-semibold text-lg text-red-900 dark:text-red-100">
                      Error en la Extracción
                    </h3>
                    <p className="text-sm text-red-800 dark:text-red-200 font-mono whitespace-pre-wrap">
                      {extraccionMasiva.progreso.mensaje || 'Ocurrió un error durante la extracción'}
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex gap-2">
                <Button
                  onClick={handleIniciarExtraccion}
                  className="flex-1"
                  variant="outline"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Reintentar Extracción
                </Button>
                <Button
                  onClick={onClose}
                  className="flex-1"
                  variant="default"
                >
                  Cerrar
                </Button>
              </div>
            </div>
          )}

          {/* Tab de Extrayendo con progreso en tiempo real */}
          {(extraccionMasiva.estado === 'extrayendo' || extraccionMasiva.estado === 'iniciando') && (
            <div className="space-y-6">
              {/* Indicador de inicio cuando está iniciando */}
              {extraccionMasiva.estado === 'iniciando' && (
                <div className="flex flex-col items-center justify-center py-12 space-y-4">
                  <Loader2 className="h-16 w-16 animate-spin text-blue-600" />
                  <div className="text-center space-y-2">
                    <h3 className="font-semibold text-lg">Iniciando Procesamiento</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Preparando {tipoExtraccion === 'masiva' ? 'extracción masiva' : 'procesamiento de expedientes seleccionados'}...
                    </p>
                  </div>
                </div>
              )}

              {/* Barra de progreso (solo mostrar cuando ya está extrayendo) */}
              {extraccionMasiva.estado === 'extrayendo' && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
                      <h3 className="font-semibold text-lg">
                        {tipoExtraccion === 'masiva'
                          ? 'Extracción Masiva en Progreso'
                          : `Procesando ${extraccionMasiva.progreso.total} Expedientes Seleccionados`}
                      </h3>
                    </div>
                    {procesarConPDF && (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-300 border border-blue-300 dark:border-blue-700 rounded-full">
                        <FileDown className="h-3 w-3" />
                        Descargando PDFs
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                    {extraccionMasiva.progreso.total > 0 ? (
                      <>
                        <span className="font-mono">Página {extraccionMasiva.progreso.actual}/{extraccionMasiva.progreso.total}</span>
                        {extraccionMasiva.total_esperado && extraccionMasiva.total_esperado > 0 && (
                          <>
                            <span>•</span>
                            <span className="font-semibold text-blue-600">
                              ~{(extraccionMasiva.progreso.actual * 15).toLocaleString()}/{extraccionMasiva.total_esperado.toLocaleString()} expedientes
                            </span>
                          </>
                        )}
                        <span>•</span>
                        <span>{extraccionMasiva.progreso.porcentaje.toFixed(1)}%</span>
                      </>
                    ) : (
                      <span className="font-mono">Página {extraccionMasiva.progreso.actual} • Calculando total...</span>
                    )}
                  </div>

                  <Progress value={extraccionMasiva.progreso.porcentaje} className="h-3" />

                  {/* Información de progreso */}
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="space-y-1">
                      <div className="text-gray-600 dark:text-gray-400">Fase Actual</div>
                      <div className="font-semibold">{extraccionMasiva.progreso.fase || 'Iniciando...'}</div>
                    </div>
                    <div className="space-y-1">
                      <div className="text-gray-600 dark:text-gray-400">Estado</div>
                      <div className="font-semibold capitalize">{extraccionMasiva.estado}</div>
                    </div>
                    <div className="space-y-1">
                      <div className="text-gray-600 dark:text-gray-400">Errores</div>
                      <div className="font-semibold text-red-600">{extraccionMasiva.progreso.errores}</div>
                    </div>
                    <div className="space-y-1">
                      <div className="text-gray-600 dark:text-gray-400">Tiempo Transcurrido</div>
                      <div className="font-semibold font-mono">
                        {Math.floor(extraccionMasiva.progreso.tiempoTranscurrido / 60)}:{String(Math.floor(extraccionMasiva.progreso.tiempoTranscurrido % 60)).padStart(2, '0')}
                      </div>
                    </div>
                    {extraccionMasiva.progreso.velocidad && (
                      <div className="space-y-1">
                        <div className="text-gray-600 dark:text-gray-400">Velocidad</div>
                        <div className="font-semibold">{extraccionMasiva.progreso.velocidad.toFixed(2)} exp/s</div>
                      </div>
                    )}
                    {extraccionMasiva.progreso.tiempoEstimado && (
                      <div className="space-y-1">
                        <div className="text-gray-600 dark:text-gray-400">Tiempo Estimado</div>
                        <div className="font-semibold font-mono">
                          {Math.floor(extraccionMasiva.progreso.tiempoEstimado / 60)}:{String(Math.floor(extraccionMasiva.progreso.tiempoEstimado % 60)).padStart(2, '0')}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Mensaje actual */}
                  <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                    <p className="text-sm font-mono">{extraccionMasiva.progreso.mensaje || 'Esperando actualizaciones...'}</p>
                  </div>

                  {/* Controles de extracción */}
                  <div className="flex gap-2">
                    {extraccionMasiva.estado === 'extrayendo' && (
                      <Button
                        onClick={handlePausar}
                        variant="outline"
                        className="flex-1"
                      >
                        <Pause className="h-4 w-4 mr-2" />
                        Pausar
                      </Button>
                    )}
                    {extraccionMasiva.estado === 'pausado' && (
                      <Button
                        onClick={handleReanudar}
                        variant="outline"
                        className="flex-1"
                      >
                        <Play className="h-4 w-4 mr-2" />
                        Reanudar
                      </Button>
                    )}
                    <Button
                      onClick={handleCancelar}
                      variant="destructive"
                      className="flex-1"
                    >
                      <XCircle className="h-4 w-4 mr-2" />
                      Cancelar
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Tab de Reporte - Resumen de Extracción Completada */}
          {mostrarReporte && extraccionMasiva.estado === 'completado' && (
            <div className="space-y-6 py-8">
              {/* Header con ícono de éxito */}
              <div className="flex flex-col items-center gap-4">
                <div className="w-16 h-16 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
                  <Download className="h-8 w-8 text-green-600 dark:text-green-400" />
                </div>
                <div className="text-center">
                  <h2 className="text-2xl font-bold text-green-900 dark:text-green-100">
                    {tipoExtraccion === 'masiva'
                      ? '¡Extracción Masiva Completada!'
                      : '¡Procesamiento Completado!'}
                  </h2>
                  <p className="text-gray-600 dark:text-gray-400 mt-1">
                    {tipoExtraccion === 'masiva'
                      ? 'Los expedientes han sido extraídos exitosamente'
                      : 'Los expedientes seleccionados han sido procesados exitosamente'}
                  </p>
                </div>
              </div>

              {/* Motivo de Finalización */}
              {extraccionMasiva.motivo_finalizacion && (
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <div className="text-blue-600 dark:text-blue-400 text-lg">
                      ℹ️
                    </div>
                    <div className="flex-1">
                      <h4 className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-1">
                        Motivo de Finalización
                      </h4>
                      <p className="text-sm text-blue-700 dark:text-blue-300">
                        {extraccionMasiva.motivo_finalizacion}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Estadísticas */}
              <div className={`grid ${procesarConPDF ? 'grid-cols-4' : 'grid-cols-3'} gap-4`}>
                {/* Total Extraído con completitud */}
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                  <div className="text-sm text-blue-600 dark:text-blue-400 font-medium mb-1">
                    Total Extraído
                  </div>
                  <div className="text-3xl font-bold text-blue-900 dark:text-blue-100">
                    {expedientesExtraidos.length}
                  </div>
                  {extraccionMasiva.total_esperado && extraccionMasiva.total_esperado > 0 && (
                    <div className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                      de {extraccionMasiva.total_esperado.toLocaleString()} ({((expedientesExtraidos.length / extraccionMasiva.total_esperado) * 100).toFixed(1)}%)
                      {expedientesExtraidos.length >= extraccionMasiva.total_esperado ? ' ✅' : ' ⚠️'}
                    </div>
                  )}
                  {!extraccionMasiva.total_esperado && (
                    <div className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                      expedientes
                    </div>
                  )}
                </div>

                {/* Tiempo Total */}
                <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-4">
                  <div className="text-sm text-purple-600 dark:text-purple-400 font-medium mb-1">
                    Tiempo Total
                  </div>
                  <div className="text-3xl font-bold text-purple-900 dark:text-purple-100">
                    {(() => {
                      // Calcular duración si hay tiempo_inicio y tiempo_fin en la sesión
                      const inicio = extraccionMasiva.progreso.tiempoTranscurrido || 0
                      const minutos = Math.floor(inicio / 60)
                      const segundos = Math.floor(inicio % 60)
                      return minutos > 0 ? `${minutos}m` : `${segundos}s`
                    })()}
                  </div>
                  <div className="text-xs text-purple-600 dark:text-purple-400 mt-1">
                    duración
                  </div>
                </div>

                {/* Páginas Procesadas (solo para extracción masiva inicial, no para expedientes seleccionados) */}
                {tipoExtraccion === 'masiva' && (
                  <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
                    <div className="text-sm text-amber-600 dark:text-amber-400 font-medium mb-1">
                      Páginas Procesadas
                    </div>
                    <div className="text-3xl font-bold text-amber-900 dark:text-amber-100">
                      {extraccionMasiva.paginas_procesadas || 0}
                    </div>
                    <div className="text-xs text-amber-600 dark:text-amber-400 mt-1">
                      páginas
                    </div>
                  </div>
                )}

                {/* Archivos Descargados (solo si procesarConPDF) */}
                {procesarConPDF && (
                  <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                    <div className="text-sm text-green-600 dark:text-green-400 font-medium mb-1">
                      Archivos Descargados
                    </div>
                    <div className="text-3xl font-bold text-green-900 dark:text-green-100">
                      {extraccionMasiva.archivos_descargados || '0'}
                    </div>
                    <div className="text-xs text-green-600 dark:text-green-400 mt-1">
                      archivos
                    </div>
                  </div>
                )}
              </div>

              {/* Comparación con BASE */}
              {extraccionMasiva.comparacion && (
                <div className="border-t pt-4">
                  <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <span>📊</span> Comparación con BASE
                  </h3>
                  <ComparacionDetalladaPanel comparacion={extraccionMasiva.comparacion} />
                </div>
              )}

              {/* Botones contextuales según tipo de extracción */}
              <div className="flex flex-col items-center gap-4 pt-4">
                {tipoExtraccion === 'seleccionados' ? (
                  // Botones para extracción de seleccionados
                  <div className="flex gap-3 justify-center flex-wrap">
                    <Button
                      onClick={handleVolverAFiltrado}
                      variant="outline"
                      size="lg"
                    >
                      Procesar Más Expedientes
                    </Button>
                    <Button
                      onClick={handleCerrarDialogo}
                      size="lg"
                      className="min-w-[150px]"
                    >
                      Cerrar
                    </Button>
                  </div>
                ) : (
                  // Countdown automático para extracción masiva
                  <>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {countdown > 0 ? (
                        <>
                          Cargando filtros automáticamente en{' '}
                          <span className="font-bold text-blue-600 dark:text-blue-400 text-lg">
                            {countdown}
                          </span>{' '}
                          segundos...
                        </>
                      ) : (
                        'Cargando filtros...'
                      )}
                    </p>
                    <Button
                      onClick={() => setMostrarReporte(false)}
                      size="lg"
                      className="min-w-[200px]"
                    >
                      Continuar Ahora
                    </Button>
                  </>
                )}
              </div>
            </div>
          )}

          {/* Tab de Filtrado */}
          {(extraccionMasiva.estado === 'completado' && expedientesExtraidos.length > 0 && !mostrarReporte) && (
            <div className="grid grid-cols-12 gap-6 h-full">
              {/* Panel de Filtros */}
              <div className={`col-span-3 space-y-4 overflow-y-auto pr-2 ${
                maximizado ? 'max-h-[calc(95vh-12rem)]' : ''
              }`}>
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold flex items-center gap-2">
                    <Filter className="h-4 w-4" />
                    Filtros
                  </h3>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleLimpiarFiltros}
                  >
                    Limpiar
                  </Button>
                </div>

                {/* Búsqueda por texto */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Buscar</label>
                  <Input
                    placeholder="Número, carátula..."
                    value={filtros.texto}
                    onChange={(e) => setFiltros({ ...filtros, texto: e.target.value })}
                  />
                </div>

                {/* Dependencia (múltiple con checkboxes) */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium">Dependencia</label>
                    <div className="flex gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 text-xs"
                        onClick={() => setFiltros({
                          ...filtros,
                          dependencias: opcionesDependencia.map(o => o.valor)
                        })}
                      >
                        Todas
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 text-xs"
                        onClick={() => setFiltros({ ...filtros, dependencias: [] })}
                      >
                        Ninguna
                      </Button>
                    </div>
                  </div>
                  <div className="space-y-1 max-h-48 overflow-y-auto border rounded p-2">
                    {opcionesDependencia.map(({ valor, count }) => (
                      <div key={valor} className="flex items-center space-x-2">
                        <Checkbox
                          id={`dep-${valor}`}
                          checked={filtros.dependencias.includes(valor)}
                          onCheckedChange={(checked) => {
                            if (checked) {
                              setFiltros({
                                ...filtros,
                                dependencias: [...filtros.dependencias, valor]
                              })
                            } else {
                              setFiltros({
                                ...filtros,
                                dependencias: filtros.dependencias.filter(d => d !== valor)
                              })
                            }
                          }}
                        />
                        <label
                          htmlFor={`dep-${valor}`}
                          className="text-xs flex-1 cursor-pointer"
                        >
                          {valor} ({count})
                        </label>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Situación Procesal (dinámico con checkboxes) */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium">Situación Procesal</label>
                    <div className="flex gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 text-xs"
                        onClick={() => setFiltros({
                          ...filtros,
                          situacion: opcionesSituacion.map(o => o.valor)
                        })}
                      >
                        Todas
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 text-xs"
                        onClick={() => setFiltros({ ...filtros, situacion: [] })}
                      >
                        Ninguna
                      </Button>
                    </div>
                  </div>
                  <div className="space-y-1">
                    {opcionesSituacion.map(({ valor, count }) => (
                      <div key={valor} className="flex items-center space-x-2">
                        <Checkbox
                          id={`sit-${valor}`}
                          checked={filtros.situacion.includes(valor)}
                          onCheckedChange={(checked) => {
                            if (checked) {
                              setFiltros({
                                ...filtros,
                                situacion: [...filtros.situacion, valor]
                              })
                            } else {
                              setFiltros({
                                ...filtros,
                                situacion: filtros.situacion.filter(s => s !== valor)
                              })
                            }
                          }}
                        />
                        <label
                          htmlFor={`sit-${valor}`}
                          className="text-sm cursor-pointer"
                        >
                          {valor} ({count})
                        </label>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Separador */}
                <div className="border-t my-4" />

                {/* Ordenamiento por Fecha */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Ordenar por Última Actuación</label>
                  <Select
                    value={filtros.ordenFecha}
                    onValueChange={(value) => setFiltros({
                      ...filtros,
                      ordenFecha: value as 'desc' | 'asc' | 'ninguno'
                    })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ninguno">Sin ordenar</SelectItem>
                      <SelectItem value="desc">Más recientes primero</SelectItem>
                      <SelectItem value="asc">Más antiguos primero</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Filtro por Rango de Fechas */}
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="usar-filtro-fecha"
                      checked={filtros.usarFiltroFechaActuacion}
                      onCheckedChange={(checked) => setFiltros({
                        ...filtros,
                        usarFiltroFechaActuacion: checked as boolean
                      })}
                    />
                    <label
                      htmlFor="usar-filtro-fecha"
                      className="text-sm font-medium cursor-pointer"
                    >
                      Filtrar por rango de fechas
                    </label>
                  </div>

                  {filtros.usarFiltroFechaActuacion && (
                    <div className="space-y-3 pl-6">
                      <DateInputArgentino
                        label="Desde"
                        value={filtros.fechaActuacionDesde}
                        onChange={(value) => setFiltros({
                          ...filtros,
                          fechaActuacionDesde: value || ''
                        })}
                        placeholder="dd/mm/aaaa"
                      />
                      <DateInputArgentino
                        label="Hasta"
                        value={filtros.fechaActuacionHasta}
                        onChange={(value) => setFiltros({
                          ...filtros,
                          fechaActuacionHasta: value || ''
                        })}
                        placeholder="dd/mm/aaaa"
                      />
                    </div>
                  )}
                </div>

                {/* Opción de procesamiento con PDF */}
                <div className="space-y-2 border-t pt-4 mt-4">
                  <label className="text-sm font-medium">Opciones de Extracción</label>
                  <div className="flex items-start space-x-2 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                    <Checkbox
                      id="procesar-pdf"
                      checked={procesarConPDF}
                      onCheckedChange={(checked) => setProcesarConPDF(checked as boolean)}
                      className="mt-1"
                    />
                    <label htmlFor="procesar-pdf" className="flex-1 cursor-pointer">
                      <div className="font-medium text-sm">Descargar archivos adjuntos</div>
                      <p className="text-xs text-gray-600 dark:text-gray-400 mt-1 leading-relaxed">
                        Descarga todos los documentos (PDFs) asociados a las actuaciones.
                        Esto aumentará el tiempo de procesamiento pero obtendrás el expediente completo.
                      </p>
                    </label>
                  </div>
                </div>
              </div>

              {/* Tabla de Expedientes */}
              <div className="col-span-9 space-y-4">
                {/* Stats y Acciones */}
                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    <span className="font-semibold">{expedientesFiltrados.length}</span> expedientes |{' '}
                    <span className="font-semibold text-blue-600">{expedientesSeleccionados.size}</span> seleccionados
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleSeleccionarTodos}
                    >
                      <CheckSquare className="h-4 w-4 mr-1" />
                      Todos los filtrados ({expedientesFiltrados.length})
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        // Seleccionar solo los expedientes de la página actual
                        const indiceInicio = (paginaActual - 1) * ITEMS_POR_PAGINA
                        const indiceFin = Math.min(indiceInicio + ITEMS_POR_PAGINA, expedientesFiltrados.length)
                        const expedientesPaginados = expedientesFiltrados.slice(indiceInicio, indiceFin)

                        const nuevosSeleccionados = new Set(expedientesSeleccionados)
                        expedientesPaginados.forEach(exp => nuevosSeleccionados.add(exp.numero))
                        setExpedientesSeleccionados(nuevosSeleccionados)
                      }}
                    >
                      <CheckSquare className="h-4 w-4 mr-1" />
                      Página actual ({Math.min(ITEMS_POR_PAGINA, expedientesFiltrados.length - (paginaActual - 1) * ITEMS_POR_PAGINA)})
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleDeseleccionarTodos}
                    >
                      <Square className="h-4 w-4 mr-1" />
                      Ninguno
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleInvertirSeleccion}
                    >
                      Invertir
                    </Button>
                  </div>
                </div>

                {/* Lista de Expedientes */}
                <div className={`border rounded-lg overflow-auto ${
                  maximizado ? 'max-h-[calc(95vh-24rem)]' : 'max-h-[32rem]'
                }`}>
                  <table className="w-full">
                    <thead className="bg-gray-50 dark:bg-gray-900">
                      <tr>
                        <th className="w-12 p-3 text-left">
                          <Checkbox
                            checked={expedientesSeleccionados.size === expedientesFiltrados.length && expedientesFiltrados.length > 0}
                            onCheckedChange={handleSeleccionarTodos}
                          />
                        </th>
                        <th className="p-3 text-left text-sm font-medium">Número</th>
                        <th className="p-3 text-left text-sm font-medium">Carátula</th>
                        <th className="p-3 text-left text-sm font-medium">Dependencia</th>
                        <th className="p-3 text-left text-sm font-medium">Situación</th>
                        <th className="p-3 text-left text-sm font-medium">Última Actuación</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(() => {
                        // Calcular paginación
                        const totalPaginas = Math.ceil(expedientesFiltrados.length / ITEMS_POR_PAGINA)
                        const indiceInicio = (paginaActual - 1) * ITEMS_POR_PAGINA
                        const indiceFin = Math.min(indiceInicio + ITEMS_POR_PAGINA, expedientesFiltrados.length)
                        const expedientesPaginados = expedientesFiltrados.slice(indiceInicio, indiceFin)

                        return expedientesPaginados.map((expediente) => (
                        <tr
                          key={expediente.numero}
                          className="border-t hover:bg-gray-50 dark:hover:bg-gray-900/50 cursor-pointer"
                          onClick={() => handleToggleExpediente(expediente.numero)}
                        >
                          <td className="p-3">
                            <Checkbox
                              checked={expedientesSeleccionados.has(expediente.numero)}
                              onClick={(e) => e.stopPropagation()}
                              onCheckedChange={() => handleToggleExpediente(expediente.numero)}
                            />
                          </td>
                          <td className="p-3 text-sm font-mono">{expediente.numero}</td>
                          <td className="p-3 text-sm">{expediente.caratula}</td>
                          <td className="p-3 text-sm text-gray-600 dark:text-gray-400">{expediente.dependencia}</td>
                          <td className="p-3">
                            <span className={`text-xs px-2 py-1 rounded-full ${
                              expediente.situacion?.toLowerCase().includes('trámite')
                                ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100'
                                : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-100'
                            }`}>
                              {expediente.situacion}
                            </span>
                          </td>
                          <td className="p-3 text-sm text-gray-600 dark:text-gray-400">
                            {formatearFecha(expediente.ultima_actuacion)}
                          </td>
                        </tr>
                        ))
                      })()}
                    </tbody>
                  </table>

                  {/* Controles de Paginación */}
                  {expedientesFiltrados.length > ITEMS_POR_PAGINA && (() => {
                    const totalPaginas = Math.ceil(expedientesFiltrados.length / ITEMS_POR_PAGINA)
                    const indiceInicio = (paginaActual - 1) * ITEMS_POR_PAGINA
                    const indiceFin = Math.min(indiceInicio + ITEMS_POR_PAGINA, expedientesFiltrados.length)

                    return (
                      <div className="flex items-center justify-between px-4 py-3 border-t">
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          Mostrando {indiceInicio + 1}-{indiceFin} de {expedientesFiltrados.length} expedientes
                        </div>
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            disabled={paginaActual === 1}
                            onClick={() => setPaginaActual(1)}
                          >
                            Primera
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            disabled={paginaActual === 1}
                            onClick={() => setPaginaActual(paginaActual - 1)}
                          >
                            Anterior
                          </Button>
                          <span className="px-3 py-1 text-sm">
                            Página {paginaActual} de {totalPaginas}
                          </span>
                          <Button
                            variant="outline"
                            size="sm"
                            disabled={paginaActual >= totalPaginas}
                            onClick={() => setPaginaActual(paginaActual + 1)}
                          >
                            Siguiente
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            disabled={paginaActual >= totalPaginas}
                            onClick={() => setPaginaActual(totalPaginas)}
                          >
                            Última
                          </Button>
                        </div>
                      </div>
                    )
                  })()}
                </div>
              </div>
            </div>
          )}
        </CardContent>

        {/* Footer con botones */}
        <div className="border-t p-4 flex justify-between gap-2">
          <div className="flex gap-2">
            {(extraccionMasiva.estado === 'completado' && expedientesExtraidos.length > 0) && extraccionMasiva.sessionId && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleDescargarReporte('json')}
                >
                  <FileDown className="h-4 w-4 mr-2" />
                  JSON
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleDescargarReporte('excel')}
                >
                  <FileDown className="h-4 w-4 mr-2" />
                  Excel
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleDescargarReporte('csv')}
                >
                  <FileDown className="h-4 w-4 mr-2" />
                  CSV
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleDescargarReporte('html')}
                >
                  <FileDown className="h-4 w-4 mr-2" />
                  HTML
                </Button>
              </>
            )}
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={onClose}
              disabled={extraccionMasiva.estado === 'extrayendo'}
            >
              {(extraccionMasiva.estado === 'completado' && expedientesExtraidos.length > 0) ? 'Cerrar' : 'Cancelar'}
            </Button>
            {(extraccionMasiva.estado === 'completado' && expedientesExtraidos.length > 0) && (
              <Button
                onClick={handleConfirmar}
                disabled={expedientesSeleccionados.size === 0}
              >
                Confirmar y Guardar Selección ({expedientesSeleccionados.size})
              </Button>
            )}
          </div>
        </div>
      </Card>

      {/* Modal de Reintentos Agotados */}
      <Dialog open={mostrarModalReintento} onOpenChange={setMostrarModalReintento}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="text-red-600">Reintentos Agotados</DialogTitle>
            <DialogDescription>
              La extracción falló tras {extraccionMasiva.intentos_realizados} intentos.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="rounded-lg bg-red-50 p-4 border border-red-200">
              <p className="text-sm font-medium text-red-800 mb-2">
                Último motivo: {extraccionMasiva.motivo_finalizacion || 'Error desconocido'}
              </p>

              {extraccionMasiva.historial_intentos.length > 0 && (
                <div className="mt-3 space-y-1">
                  <p className="text-xs font-semibold text-red-700">Historial de intentos:</p>
                  {extraccionMasiva.historial_intentos.map((intento, idx) => (
                    <p key={idx} className="text-xs text-red-600">
                      • Intento {intento.intento}: {intento.motivo} ({intento.total_expedientes} expedientes)
                    </p>
                  ))}
                </div>
              )}
            </div>

            <p className="text-sm text-gray-600">
              ¿Qué desea hacer?
            </p>
          </div>

          <DialogFooter className="flex-col sm:flex-row gap-2">
            <Button
              variant="outline"
              onClick={handleReintentar}
              className="w-full sm:w-auto"
            >
              Reintentar Extracción
            </Button>
            <Button
              onClick={handleContinuarConParciales}
              className="w-full sm:w-auto bg-blue-600 hover:bg-blue-700"
            >
              Continuar con Parciales
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
