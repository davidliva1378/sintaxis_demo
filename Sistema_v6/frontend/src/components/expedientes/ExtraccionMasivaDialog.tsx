import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { Progress } from '@/components/ui/progress'
import { X, Download, Loader2, Filter, CheckSquare, Square, Pause, Play, XCircle, FileDown } from 'lucide-react'
import { useExpedientesStore } from '@/stores/expedientesStore'
import type { ExpedienteResumen } from '@/types/expediente'

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
  const {
    extraerExpedientesMasivamente,
    isExtractingMasivo,
    extraccionMasiva,
    iniciarExtraccionMasivaAvanzada,
    pausarExtraccion,
    reanudarExtraccion,
    cancelarExtraccion,
    obtenerResumen,
    descargarReporte,
    desconectarWebSocket,
    expedientes,
  } = useExpedientesStore()

  // Estados
  const [etapa, setEtapa] = useState<'config' | 'extrayendo' | 'filtrado'>('config')
  const [expedientesExtraidos, setExpedientesExtraidos] = useState<ExpedienteResumen[]>([])
  const [expedientesFiltrados, setExpedientesFiltrados] = useState<ExpedienteResumen[]>([])
  const [expedientesSeleccionados, setExpedientesSeleccionados] = useState<Set<string>>(new Set())
  const [procesarConPDF, setProcesarConPDF] = useState(false)
  const [logMensajes, setLogMensajes] = useState<string[]>([])
  const [mostrarOpcionesAvanzadas, setMostrarOpcionesAvanzadas] = useState(false)

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

  // Monitorear progreso de extracción y cambiar a filtrado cuando termine
  useEffect(() => {
    if (extraccionMasiva.estado === 'completed' && etapa === 'extrayendo') {
      // Obtener expedientes del store
      setExpedientesExtraidos(expedientes)
      setExpedientesFiltrados(expedientes)

      // Seleccionar todos por defecto
      const seleccionados = new Set(expedientes.map(exp => exp.numero))
      setExpedientesSeleccionados(seleccionados)

      // Avanzar a etapa de filtrado
      setEtapa('filtrado')
    }
  }, [extraccionMasiva.estado, etapa, expedientes])

  // Cleanup: desconectar WebSocket al cerrar
  useEffect(() => {
    return () => {
      if (extraccionMasiva.websocket) {
        desconectarWebSocket()
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
      // Configuración de extracción avanzada
      const config = {
        headless: true,
        umbralErrores: 10,
        exportarFormatos: ['json'],
      }

      // Iniciar extracción masiva avanzada con WebSocket
      await iniciarExtraccionMasivaAvanzada(config)

      // Cambiar a etapa de extrayendo (el progreso se mostrará en tiempo real)
      setEtapa('extrayendo')

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
      setEtapa('config')
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

  const handleConfirmar = () => {
    const expedientesConfirmados = expedientesFiltrados.filter(exp =>
      expedientesSeleccionados.has(exp.numero)
    )

    if (onSuccess) {
      onSuccess(expedientesConfirmados)
    }

    onClose()
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
          {etapa === 'config' && (
            <div className="space-y-6">
              {/* Opciones */}
              <div className="space-y-4">
                <h3 className="font-semibold text-lg">Opciones de Extracción</h3>

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

                <div className="bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                  <p className="text-sm text-blue-900 dark:text-blue-100">
                    ℹ️ La extracción puede tardar varios minutos dependiendo de la cantidad de expedientes.
                    El proceso se ejecuta de forma incremental para mayor confiabilidad.
                  </p>
                </div>
              </div>

              {/* Botón Iniciar */}
              <div>
                <Button
                  onClick={handleIniciarExtraccion}
                  disabled={extraccionMasiva.estado === 'running'}
                  className="w-full"
                  size="lg"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Iniciar Extracción Masiva Avanzada
                </Button>
              </div>
            </div>
          )}

          {/* Tab de Extrayendo con progreso en tiempo real */}
          {etapa === 'extrayendo' && (
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
                  {extraccionMasiva.estado === 'running' && (
                    <Button
                      onClick={handlePausar}
                      variant="outline"
                      className="flex-1"
                    >
                      <Pause className="h-4 w-4 mr-2" />
                      Pausar
                    </Button>
                  )}
                  {extraccionMasiva.estado === 'paused' && (
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

          {/* Tab de Filtrado */}
          {etapa === 'filtrado' && (
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
            {etapa === 'filtrado' && extraccionMasiva.sessionId && (
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
              disabled={extraccionMasiva.estado === 'running'}
            >
              {etapa === 'filtrado' ? 'Cerrar' : 'Cancelar'}
            </Button>
            {etapa === 'filtrado' && (
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
