import { useState, useEffect, useRef } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { toast } from 'sonner'
import { useExtraccionStore } from '@/stores/extraccionStore'
import type { ExpedienteResumen, ConfigExtraccion, ExpedienteFiltros } from '@/types/expediente'

// Sub-componentes
import { ExtraccionConfiguracion } from './extraccion/ExtraccionConfiguracion'
import { ExtraccionProgreso } from './extraccion/ExtraccionProgreso'
import { ExtraccionReporte } from './extraccion/ExtraccionReporte'
import { ExtraccionFiltros } from './extraccion/ExtraccionFiltros'
import { ExtraccionListado } from './extraccion/ExtraccionListado'

interface ExtraccionMasivaDialogProps {
  onClose: () => void
  onSuccess?: () => void
  minActuaciones?: number
  usarMinActuaciones?: boolean
}

export default function ExtraccionMasivaDialog({ onClose }: ExtraccionMasivaDialogProps) {
  // Usar selectores específicos de Zustand para asegurar re-renders
  const {
    estado,
    sessionId,
    progreso,
    paginas_procesadas,
    archivos_descargados,
    comparacion,
    motivo_finalizacion,
    intentos_realizados,
    intentos_maximos,
    historial_intentos,
    total_esperado,
    // Campos de feedback de procesamiento detallado
    expediente_procesando,
    actuacion_actual,
    actuaciones_total,
    fase_procesamiento,
    mensaje_procesamiento,
    iniciarExtraccionMasivaAvanzada,
    pausarExtraccion,
    reanudarExtraccion,
    cancelarExtraccion,
    procesarExpedientesSeleccionados,
    cargarListadoBase,
    setEstado,
    resetExtraccionMasiva,
    descargarReporte
  } = useExtraccionStore()

  // Resetear estado al montar el componente para evitar estados residuales
  useEffect(() => {
    resetExtraccionMasiva()
    // Cleanup al desmontar también es buena práctica
    return () => {
      resetExtraccionMasiva()
    }
  }, [])

  // Mapear estado para compatibilidad
  const extraccionMasiva = {
    estado,
    sessionId,
    progreso,
    paginas_procesadas,
    archivos_descargados,
    comparacion,
    motivo_finalizacion,
    intentos_realizados,
    intentos_maximos,
    historial_intentos,
    total_esperado,
    // Campos de feedback de procesamiento detallado
    expediente_procesando,
    actuacion_actual,
    actuaciones_total,
    fase_procesamiento,
    mensaje_procesamiento
  }

  // Estados
  const [expedientesExtraidos, setExpedientesExtraidos] = useState<ExpedienteResumen[]>([])
  const [expedientesFiltrados, setExpedientesFiltrados] = useState<ExpedienteResumen[]>([])
  const [expedientesSeleccionados, setExpedientesSeleccionados] = useState<Set<string>>(new Set())
  const [mostrarReporte, setMostrarReporte] = useState(false)
  const [tipoExtraccion, setTipoExtraccion] = useState<'masiva' | 'seleccionados'>('masiva')
  const [maximizado, setMaximizado] = useState(false)
  const [mostrarOpcionesAvanzadas, setMostrarOpcionesAvanzadas] = useState(false)

  // Ref para evitar mostrar reporte múltiples veces para la misma sesión
  const reporteMostradoRef = useRef<string | null>(null)

  // Configuración
  const [config, setConfig] = useState<ConfigExtraccion>({
    headless: true,
    umbral_errores: 10,
    timeout_pagina: 30000,
    max_reintentos: 3,
    procesar_con_pdf: true,
    incluir_historicas: true,
    min_utilidad: 'MEDIA',
    directorio_base: './Sistema_v6/data/expedientes',
    detener_en_duplicado: true,
    omitir_duplicados: true,
    exportar_formatos: ['json']
  })

  // Estado para el checkbox de PDF (sincronizado con config)
  const [procesarConPDF, setProcesarConPDF] = useState(true)

  // Sincronizar procesarConPDF con config
  useEffect(() => {
    setConfig(prev => ({ ...prev, procesar_con_pdf: procesarConPDF }))
  }, [procesarConPDF])

  // Filtros
  const [filtros, setFiltros] = useState<ExpedienteFiltros>({
    numero: '',
    caratula: '',
    dependencia: [],
    situacion: []
  })

  // Paginación
  const [paginaActual, setPaginaActual] = useState(1)
  const ITEMS_POR_PAGINA = 10

  // Opciones para filtros (calculadas dinámicamente)
  const [opcionesDependencia, setOpcionesDependencia] = useState<{ valor: string, count: number }[]>([])
  const [opcionesSituacion, setOpcionesSituacion] = useState<{ valor: string, count: number }[]>([])

  // Efecto para calcular opciones de filtros cuando cambian los expedientes extraídos
  useEffect(() => {
    if (expedientesExtraidos.length > 0) {
      const deps = new Map<string, number>()
      const sits = new Map<string, number>()

      expedientesExtraidos.forEach(exp => {
        if (exp.dependencia) {
          deps.set(exp.dependencia, (deps.get(exp.dependencia) || 0) + 1)
        }
        if (exp.situacion) {
          sits.set(exp.situacion, (sits.get(exp.situacion) || 0) + 1)
        }
      })

      setOpcionesDependencia(
        Array.from(deps.entries())
          .map(([valor, count]) => ({ valor, count }))
          .sort((a, b) => b.count - a.count)
      )

      setOpcionesSituacion(
        Array.from(sits.entries())
          .map(([valor, count]) => ({ valor, count }))
          .sort((a, b) => b.count - a.count)
      )
    }
  }, [expedientesExtraidos])

  // Efecto para aplicar filtros
  useEffect(() => {
    let resultado = expedientesExtraidos

    if (filtros.numero) {
      const termino = filtros.numero.toLowerCase()
      resultado = resultado.filter(exp =>
        exp.numero.toLowerCase().includes(termino) ||
        (exp.caratula && exp.caratula.toLowerCase().includes(termino))
      )
    }

    if (filtros.dependencia && filtros.dependencia.length > 0) {
      resultado = resultado.filter(exp =>
        filtros.dependencia?.includes(exp.dependencia)
      )
    }

    if (filtros.situacion && filtros.situacion.length > 0) {
      resultado = resultado.filter(exp =>
        filtros.situacion?.includes(exp.situacion)
      )
    }

    setExpedientesFiltrados(resultado)
    setPaginaActual(1)
  }, [filtros, expedientesExtraidos])

  // Efecto para manejar el estado completado y mostrar reporte
  useEffect(() => {
    if (extraccionMasiva.estado === 'completado' && extraccionMasiva.sessionId) {
      // Evitar procesar la misma sesión múltiples veces
      if (reporteMostradoRef.current === extraccionMasiva.sessionId) {
        return
      }

      // Marcar esta sesión como procesada
      reporteMostradoRef.current = extraccionMasiva.sessionId

      // Obtener resumen final
      const obtenerResumenFinal = async () => {
        try {
          // Si es extracción masiva, cargar el listado generado
          if (tipoExtraccion === 'masiva') {
            // Esperar un momento para asegurar que el backend haya guardado todo
            await new Promise(resolve => setTimeout(resolve, 1000))

            // Cargar listado base (que ahora debería ser el recién generado)
            const data = await cargarListadoBase()
            if (data && data.expedientes) {
              setExpedientesExtraidos(data.expedientes)
              setExpedientesFiltrados(data.expedientes)
              // Seleccionar todos por defecto para facilitar el siguiente paso
              setExpedientesSeleccionados(new Set(data.expedientes.map((e: ExpedienteResumen) => e.numero)))
            }
          }

          setMostrarReporte(true)
          setMostrarReporte(true)
          // setCountdown(5) - Eliminado para persistencia

        } catch (error) {
          console.error('Error obteniendo resumen final:', error)
          toast.error('Error al cargar los resultados finales')
        }
      }

      obtenerResumenFinal()
    }
  }, [extraccionMasiva.estado, extraccionMasiva.sessionId, tipoExtraccion])

  // Handlers
  const handleCargarBase = async () => {
    try {
      const data = await cargarListadoBase()
      if (data && data.expedientes) {
        const expedientesData = data.expedientes || []
        setExpedientesExtraidos(expedientesData)
        setExpedientesFiltrados(expedientesData)

        // Seleccionar todos por defecto
        const seleccionados = new Set<string>(expedientesData.map((exp: ExpedienteResumen) => exp.numero))
        setExpedientesSeleccionados(seleccionados)

        // Mostrar reporte y marcar sesión como vista
        setMostrarReporte(true)
        // setCountdown(5) - Eliminado
        setEstado('completado')
        setTipoExtraccion('masiva') // Asumimos que cargar base es como haber hecho una masiva

        toast.success(`Cargados ${expedientesData.length} expedientes de la base`)
      }
    } catch (error) {
      console.error('Error cargando base:', error)
      toast.error('Error al cargar la base de expedientes')
    }
  }

  const handleIniciarExtraccion = async () => {
    try {
      setTipoExtraccion('masiva')
      setExpedientesExtraidos([])
      setExpedientesFiltrados([])
      setExpedientesSeleccionados(new Set())
      setMostrarReporte(false)
      reporteMostradoRef.current = null // Resetear ref para nueva sesión

      await iniciarExtraccionMasivaAvanzada(config)
    } catch (error) {
      console.error('Error al iniciar extracción:', error)
      // El error ya se maneja en el store y muestra toast
    }
  }

  const handlePausar = async () => {
    try {
      await pausarExtraccion()
      toast.info('Pausando extracción...')
    } catch (error) {
      console.error('Error al pausar:', error)
    }
  }

  const handleReanudar = async () => {
    try {
      await reanudarExtraccion()
      toast.info('Reanudando extracción...')
    } catch (error) {
      console.error('Error al reanudar:', error)
    }
  }

  const handleCancelar = async () => {
    try {
      await cancelarExtraccion()
      toast.info('Cancelando extracción...')
      onClose()
    } catch (error) {
      console.error('Error al cancelar:', error)
    }
  }

  const handleToggleExpediente = (numero: string) => {
    const newSelected = new Set(expedientesSeleccionados)
    if (newSelected.has(numero)) {
      newSelected.delete(numero)
    } else {
      newSelected.add(numero)
    }
    setExpedientesSeleccionados(newSelected)
  }

  const handleSeleccionarTodos = (checked: boolean) => {
    if (checked) {
      const newSelected = new Set<string>()
      expedientesFiltrados.forEach(exp => {
        if (!exp.ya_agregado) {
          newSelected.add(exp.numero)
        }
      })
      setExpedientesSeleccionados(newSelected)
    } else {
      setExpedientesSeleccionados(new Set())
    }
  }

  const handleLimpiarFiltros = () => {
    setFiltros({
      numero: '',
      caratula: '',
      dependencia: [],
      situacion: []
    })
  }

  const handleConfirmar = async () => {
    if (expedientesSeleccionados.size === 0) {
      toast.error('Debe seleccionar al menos un expediente')
      return
    }

    try {
      setTipoExtraccion('seleccionados')
      const numeros = Array.from(expedientesSeleccionados)

      const configProcesamiento: Partial<ConfigExtraccion> = {
        procesar_con_pdf: procesarConPDF,
        headless: config.headless
      }

      await procesarExpedientesSeleccionados(numeros, configProcesamiento)

      // Resetear estados de UI
      setMostrarReporte(false)
      reporteMostradoRef.current = null

    } catch (error) {
      console.error('Error al procesar seleccionados:', error)
      toast.error('Error al iniciar el procesamiento')
    }
  }

  const formatearFecha = (fecha: string) => {
    if (!fecha) return '-'
    try {
      // Agregar hora del mediodía para evitar problemas de timezone
      // (JavaScript interpreta fechas ISO como UTC, causando que en Argentina UTC-3 se muestre el día anterior)
      const fechaConHora = fecha.includes('T') ? fecha : `${fecha}T12:00:00`
      return new Date(fechaConHora).toLocaleDateString('es-AR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      })
    } catch (e) {
      return fecha
    }
  }

  const handleClose = () => {
    if (extraccionMasiva.estado === 'error' || extraccionMasiva.estado === 'completado' || extraccionMasiva.estado === 'cancelado') {
      resetExtraccionMasiva()
    }
    onClose()
  }

  return (
    <Dialog open={true} onOpenChange={handleClose}>
      <DialogContent className={`max-w-6xl ${maximizado ? 'h-[95vh]' : 'max-h-[90vh]'} flex flex-col p-0 gap-0 transition-all duration-300`}>
        <DialogHeader className="p-6 pb-4 border-b">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <DialogTitle>Extracción Masiva de Expedientes</DialogTitle>
              {/* Badge de estado */}
              {extraccionMasiva.estado !== 'inactivo' && (
                <span className={`text-xs px-2 py-1 rounded-full border ${extraccionMasiva.estado === 'extrayendo' ? 'bg-blue-100 text-blue-800 border-blue-200' :
                  extraccionMasiva.estado === 'completado' ? 'bg-green-100 text-green-800 border-green-200' :
                    extraccionMasiva.estado === 'error' ? 'bg-red-100 text-red-800 border-red-200' :
                      'bg-gray-100 text-gray-800 border-gray-200'
                  }`}>
                  {extraccionMasiva.estado.toUpperCase()}
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setMaximizado(!maximizado)}
                className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded"
                title={maximizado ? "Restaurar" : "Maximizar"}
              >
                {maximizado ? '🗗' : '🗖'}
              </button>
            </div>
          </div>
          <DialogDescription>
            Configure y ejecute la extracción masiva de expedientes del Poder Judicial.
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto p-6">
          {/* Tab de Configuración */}
          {extraccionMasiva.estado === 'inactivo' && (
            <ExtraccionConfiguracion
              config={config}
              setConfig={setConfig}
              procesarConPDF={procesarConPDF}
              setProcesarConPDF={setProcesarConPDF}
              mostrarOpcionesAvanzadas={mostrarOpcionesAvanzadas}
              setMostrarOpcionesAvanzadas={setMostrarOpcionesAvanzadas}
              onCargarBase={handleCargarBase}
              onIniciar={handleIniciarExtraccion}
            />
          )}

          {/* Tab de Progreso (Iniciando/Extrayendo/Pausado) */}
          {(extraccionMasiva.estado === 'iniciando' || extraccionMasiva.estado === 'extrayendo' || extraccionMasiva.estado === 'pausado') && (
            <ExtraccionProgreso
              estado={extraccionMasiva.estado}
              progreso={extraccionMasiva.progreso}
              tipoExtraccion={tipoExtraccion}
              procesarConPDF={procesarConPDF}
              totalEsperado={extraccionMasiva.total_esperado}
              expedienteProcesando={extraccionMasiva.expediente_procesando}
              actuacionActual={extraccionMasiva.actuacion_actual}
              actuacionesTotal={extraccionMasiva.actuaciones_total}
              faseProcesamiento={extraccionMasiva.fase_procesamiento}
              mensajeProcesamiento={extraccionMasiva.mensaje_procesamiento}
              onPausar={handlePausar}
              onReanudar={handleReanudar}
              onCancelar={handleCancelar}
            />
          )}

          {/* Estado de Error */}
          {extraccionMasiva.estado === 'error' && (
            <div className="flex flex-col items-center justify-center h-full p-8 text-center space-y-4">
              <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center">
                <span className="text-3xl">⚠️</span>
              </div>
              <h3 className="text-xl font-semibold text-red-800">Ha ocurrido un error</h3>
              <p className="text-gray-600 max-w-md">
                {extraccionMasiva.progreso.mensaje || 'Error desconocido durante la extracción'}
              </p>
              <Button
                onClick={() => resetExtraccionMasiva()}
                variant="outline"
                className="mt-4"
              >
                Volver a intentar
              </Button>
            </div>
          )}

          {/* Estado Cancelado */}
          {extraccionMasiva.estado === 'cancelado' && (
            <div className="flex flex-col items-center justify-center h-full p-8 text-center space-y-4">
              <div className="w-16 h-16 rounded-full bg-yellow-100 flex items-center justify-center">
                <span className="text-3xl">🛑</span>
              </div>
              <h3 className="text-xl font-semibold text-yellow-800">Extracción Cancelada</h3>
              <p className="text-gray-600 max-w-md">
                La operación fue cancelada por el usuario.
              </p>
              <Button
                onClick={() => resetExtraccionMasiva()}
                variant="outline"
                className="mt-4"
              >
                Iniciar nueva extracción
              </Button>
            </div>
          )}

          {/* Tab de Reporte */}
          {mostrarReporte && extraccionMasiva.estado === 'completado' && (
            <ExtraccionReporte
              estado={extraccionMasiva.estado}
              tipoExtraccion={tipoExtraccion}
              procesarConPDF={procesarConPDF}
              expedientesExtraidos={expedientesExtraidos}
              progreso={extraccionMasiva.progreso}
              totalEsperado={extraccionMasiva.total_esperado}
              paginasProcesadas={extraccionMasiva.paginas_procesadas}
              archivosDescargados={extraccionMasiva.archivos_descargados}
              comparacion={extraccionMasiva.comparacion}
              motivoFinalizacion={extraccionMasiva.motivo_finalizacion}
              onVolverAFiltrado={() => setMostrarReporte(false)}
              onCerrar={handleClose}
              onContinuar={() => setMostrarReporte(false)}
              onDescargar={descargarReporte}
            />
          )}

          {/* Tab de Filtrado y Listado */}
          {(extraccionMasiva.estado === 'completado' && expedientesExtraidos.length > 0 && !mostrarReporte) && (
            <div className="grid grid-cols-12 gap-6 h-full">
              {/* Panel de Filtros */}
              <ExtraccionFiltros
                filtros={filtros}
                setFiltros={setFiltros}
                opcionesDependencia={opcionesDependencia}
                opcionesSituacion={opcionesSituacion}
                onLimpiar={handleLimpiarFiltros}
                maximizado={maximizado}
              />

              {/* Listado de Expedientes */}
              <ExtraccionListado
                expedientesFiltrados={expedientesFiltrados}
                expedientesSeleccionados={expedientesSeleccionados}
                paginaActual={paginaActual}
                setPaginaActual={setPaginaActual}
                itemsPorPagina={ITEMS_POR_PAGINA}
                onToggleExpediente={handleToggleExpediente}
                onSeleccionarTodos={handleSeleccionarTodos}
                formatearFecha={formatearFecha}
              />
            </div>
          )}
        </div>

        {/* Footer con acciones finales (solo en modo filtrado) */}
        {(extraccionMasiva.estado === 'completado' && !mostrarReporte) && (
          <div className="p-4 border-t bg-gray-50 dark:bg-gray-900/50 flex justify-between items-center">
            <div className="text-sm text-gray-600 dark:text-gray-400">
              {expedientesSeleccionados.size} expedientes seleccionados
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700"
              >
                Cancelar
              </button>
              <button
                onClick={handleConfirmar}
                disabled={expedientesSeleccionados.size === 0}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Procesar Seleccionados
              </button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
