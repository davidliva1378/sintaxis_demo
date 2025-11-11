import { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { Progress } from '@/components/ui/progress'
import { X, Download, Loader2, Filter, CheckSquare, Square, Pause, Play, XCircle, FileDown } from 'lucide-react'
import { useExpedientesStore } from '@/stores/expedientesStore'
import type { ExpedienteResumen, ConfigExtraccion } from '@/types/expediente'
import { FiltradoExpedientesDialog } from '../FiltradoExpedientesDialog'
import { DateInputArgentino } from '@/components/ui/date-input-argentino'

interface ExtraccionMasivaDialogProps {
  onClose: () => void
  onSuccess?: (expedientes: ExpedienteResumen[]) => void
}

interface Filtros {
  texto: string
  fuero: string
  situacion: string[]
  filtrarPorFecha: boolean
  fechaDesde: string
  fechaHasta: string
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

  // Estados
  const [expedientesExtraidos, setExpedientesExtraidos] = useState<ExpedienteResumen[]>([])
  const [expedientesFiltrados, setExpedientesFiltrados] = useState<ExpedienteResumen[]>([])
  const [expedientesSeleccionados, setExpedientesSeleccionados] = useState<Set<string>>(new Set())
  const [procesarConPDF, setProcesarConPDF] = useState(false)
  const [logMensajes, setLogMensajes] = useState<string[]>([])
  const [mostrarOpcionesAvanzadas, setMostrarOpcionesAvanzadas] = useState(false)
  const [mostrarFiltrosExtraccion, setMostrarFiltrosExtraccion] = useState(false)
  const [mostrarReporte, setMostrarReporte] = useState(false)
  const [countdown, setCountdown] = useState(5)

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
    fuero: 'todos',
    situacion: ['en_tramite'],
    filtrarPorFecha: false,
    fechaDesde: '',
    fechaHasta: '',
    minActuaciones: 5,
    usarMinActuaciones: false
  })

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
      if (
        extraccionMasiva.estado === 'completado' &&
        extraccionMasiva.sessionId &&
        reporteMostradoRef.current !== extraccionMasiva.sessionId
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
      }
    }

    cargarExpedientes()
  }, [extraccionMasiva.estado, extraccionMasiva.sessionId])

  // Countdown automático para transición a filtros
  useEffect(() => {
    if (mostrarReporte && countdown > 0) {
      const timer = setTimeout(() => {
        setCountdown(countdown - 1)
      }, 1000)
      return () => clearTimeout(timer)
    } else if (mostrarReporte && countdown === 0) {
      // Transición automática a filtros
      setMostrarReporte(false)
    }
  }, [mostrarReporte, countdown])

  // Cleanup: desconectar WebSocket y detener polling al cerrar
  useEffect(() => {
    return () => {
      if (extraccionMasiva.websocket) {
        desconectarWebSocket()
      }
      // Detener polling si está activo
      if (extraccionMasiva.pollInterval) {
        clearInterval(extraccionMasiva.pollInterval)
      }
    }
  }, [])

  const aplicarFiltros = () => {
    let filtered = [...expedientesExtraidos]

    // Filtro por texto
    if (filtros.texto) {
      const textoLower = filtros.texto.toLowerCase()
      filtered = filtered.filter(exp =>
        exp.numero.toLowerCase().includes(textoLower) ||
        exp.caratula.toLowerCase().includes(textoLower)
      )
    }

    // Filtro por fuero
    if (filtros.fuero !== 'todos') {
      filtered = filtered.filter(exp => exp.dependencia?.toLowerCase().includes(filtros.fuero.toLowerCase()))
    }

    // Filtro por situación
    if (filtros.situacion.length > 0) {
      filtered = filtered.filter(exp => {
        const situacionExp = exp.situacion?.toLowerCase() || ''
        return filtros.situacion.some(sit => situacionExp.includes(sit.replace('_', ' ')))
      })
    }

    // TODO: Implementar filtros adicionales cuando el backend los soporte
    // - Filtro por fecha
    // - Filtro por número mínimo de actuaciones

    setExpedientesFiltrados(filtered)

    // Seleccionar todos por defecto
    const nuevosSeleccionados = new Set(filtered.map(exp => exp.numero))
    setExpedientesSeleccionados(nuevosSeleccionados)
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
      fuero: 'todos',
      situacion: ['en_tramite'],
      filtrarPorFecha: false,
      fechaDesde: '',
      fechaHasta: '',
      minActuaciones: 5,
      usarMinActuaciones: false
    })
  }

  const handleConfirmar = async () => {
    const expedientesConfirmados = expedientesFiltrados.filter(exp =>
      expedientesSeleccionados.has(exp.numero)
    )

    if (expedientesConfirmados.length === 0) {
      return
    }

    try {
      // Enviar expedientes seleccionados para procesamiento
      const numeros = expedientesConfirmados.map(exp => exp.numero)
      const sessionId = await procesarExpedientesSeleccionados(numeros)

      // El estado cambia automáticamente a 'extrayendo' en el store
      // El progreso se mostrará en tiempo real

      // Llamar onSuccess si se proporcionó
      if (onSuccess) {
        onSuccess(expedientesConfirmados)
      }
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

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget && !isExtractingMasivo) {
          onClose()
        }
      }}
    >
      <Card className="w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Download className="h-5 w-5 text-blue-600" />
              <CardTitle>Extracción Masiva de Expedientes</CardTitle>
            </div>
            <button
              onClick={onClose}
              disabled={isExtractingMasivo}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 disabled:opacity-50"
            >
              <X className="h-5 w-5" />
            </button>
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
          {extraccionMasiva.estado === 'extrayendo' && (
            <div className="space-y-6">
              {/* Barra de progreso */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-lg">Extracción en Progreso</h3>
                  <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                    <span className="font-mono">{extraccionMasiva.progreso.actual}/{extraccionMasiva.progreso.total}</span>
                    <span>•</span>
                    <span>{extraccionMasiva.progreso.porcentaje.toFixed(1)}%</span>
                  </div>
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
                    ¡Extracción Completada!
                  </h2>
                  <p className="text-gray-600 dark:text-gray-400 mt-1">
                    Los expedientes han sido extraídos exitosamente
                  </p>
                </div>
              </div>

              {/* Estadísticas */}
              <div className="grid grid-cols-3 gap-4">
                {/* Total Extraído */}
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                  <div className="text-sm text-blue-600 dark:text-blue-400 font-medium mb-1">
                    Total Extraído
                  </div>
                  <div className="text-3xl font-bold text-blue-900 dark:text-blue-100">
                    {expedientesExtraidos.length}
                  </div>
                  <div className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                    expedientes
                  </div>
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

                {/* Páginas Procesadas */}
                <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
                  <div className="text-sm text-amber-600 dark:text-amber-400 font-medium mb-1">
                    Páginas Procesadas
                  </div>
                  <div className="text-3xl font-bold text-amber-900 dark:text-amber-100">
                    {(extraccionMasiva as any).paginas_procesadas || '0'}
                  </div>
                  <div className="text-xs text-amber-600 dark:text-amber-400 mt-1">
                    páginas
                  </div>
                </div>
              </div>

              {/* Comparación con extracción anterior */}
              {extraccionMasiva.sessionId && (
                <div className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-3 flex items-center gap-2">
                    <span>📊</span> Comparación con Extracción Anterior
                  </h3>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600 dark:text-gray-400">Nuevos:</span>
                      <span className="ml-2 font-semibold text-green-600 dark:text-green-400">
                        +0
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-600 dark:text-gray-400">Eliminados:</span>
                      <span className="ml-2 font-semibold text-red-600 dark:text-red-400">
                        -0
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-600 dark:text-gray-400">Sin cambios:</span>
                      <span className="ml-2 font-semibold text-gray-600 dark:text-gray-400">
                        {expedientesExtraidos.length}
                      </span>
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-2">
                    * Comparación disponible cuando exista una extracción previa
                  </p>
                </div>
              )}

              {/* Countdown y botón */}
              <div className="flex flex-col items-center gap-4 pt-4">
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
              </div>
            </div>
          )}

          {/* Tab de Filtrado */}
          {(extraccionMasiva.estado === 'completado' && expedientesExtraidos.length > 0 && !mostrarReporte) && (
            <div className="grid grid-cols-12 gap-6 h-full">
              {/* Panel de Filtros */}
              <div className="col-span-3 space-y-4">
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

                {/* Fuero */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Fuero</label>
                  <Select
                    value={filtros.fuero}
                    onValueChange={(value) => setFiltros({ ...filtros, fuero: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="todos">Todos</SelectItem>
                      <SelectItem value="federal">Federal</SelectItem>
                      <SelectItem value="civil">Civil</SelectItem>
                      <SelectItem value="penal">Penal</SelectItem>
                      <SelectItem value="laboral">Laboral</SelectItem>
                      <SelectItem value="contencioso">Contencioso Administrativo</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Situación */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Situación Procesal</label>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="en-tramite"
                        checked={filtros.situacion.includes('en_tramite')}
                        onCheckedChange={() => handleToggleSituacion('en_tramite')}
                      />
                      <label htmlFor="en-tramite" className="text-sm">En trámite</label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="archivado"
                        checked={filtros.situacion.includes('archivado')}
                        onCheckedChange={() => handleToggleSituacion('archivado')}
                      />
                      <label htmlFor="archivado" className="text-sm">Archivado</label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="finalizado"
                        checked={filtros.situacion.includes('finalizado')}
                        onCheckedChange={() => handleToggleSituacion('finalizado')}
                      />
                      <label htmlFor="finalizado" className="text-sm">Finalizado</label>
                    </div>
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
                      Todos
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
                <div className="border rounded-lg overflow-auto max-h-96">
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
                      </tr>
                    </thead>
                    <tbody>
                      {expedientesFiltrados.map((expediente) => (
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
                        </tr>
                      ))}
                    </tbody>
                  </table>
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
    </div>
  )
}
