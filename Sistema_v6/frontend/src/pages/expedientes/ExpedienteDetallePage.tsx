import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  ArrowLeft,
  FileText,
  Building2,
  Calendar,
  Clock,
  Loader2,
  AlertCircle,
  BarChart3,
  ListTodo,
  StickyNote,
} from 'lucide-react'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'
import { toast } from 'sonner'
import { useExpedientesStore } from '@/stores/expedientesStore'
import ActuacionesList from '@/components/expedientes/ActuacionesList'
import EstadisticasExpedientePanel from '@/components/expedientes/EstadisticasExpedientePanel'
import ActuacionesClasificadasList from '@/components/expedientes/ActuacionesClasificadasList'
import VencimientosExpedientePanel from '@/components/expedientes/VencimientosExpedientePanel'
import ProcesamientoStatusBadge from '@/components/expedientes/ProcesamientoStatusBadge'
import MiAnalisisList from '@/components/expedientes/MiAnalisisList'
import {
  obtenerEstadisticasExpediente,
  procesarExpediente,
  obtenerActuacionesClasificadasExpediente,
  obtenerVencimientosExpediente
} from '@/api/procesamientoApi'
import type {
  EstadisticasExpediente,
  VencimientoUrgente,
  ActuacionPorUtilidad,
  ActuacionInput
} from '@/types/procesamiento'

export default function ExpedienteDetallePage() {
  const { numero } = useParams<{ numero: string }>()
  const navigate = useNavigate()

  const {
    expedienteActual,
    isLoading,
    obtenerExpediente,
    limpiarExpedienteActual,
  } = useExpedientesStore()

  // Estado de procesamiento
  const [estadisticas, setEstadisticas] = useState<EstadisticasExpediente | null>(null)
  const [vencimientos, setVencimientos] = useState<VencimientoUrgente[]>([])
  const [actuacionesClasificadas, setActuacionesClasificadas] = useState<ActuacionPorUtilidad[]>([])
  const [isLoadingProcesamiento, setIsLoadingProcesamiento] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [isProcesado, setIsProcesado] = useState(false)

  useEffect(() => {
    if (numero) {
      obtenerExpediente(numero)
    }

    return () => {
      limpiarExpedienteActual()
    }
  }, [numero])

  // Cargar datos de procesamiento cuando se tenga el expediente
  useEffect(() => {
    if (expedienteActual?.numero) {
      cargarDatosProcesamiento(expedienteActual.numero)
    }
  }, [expedienteActual?.numero])

  const cargarDatosProcesamiento = async (numeroExp: string) => {
    setIsLoadingProcesamiento(true)
    try {
      // Cargar estadísticas, actuaciones clasificadas y vencimientos en paralelo
      const [stats, actuaciones, venc] = await Promise.all([
        obtenerEstadisticasExpediente(numeroExp),
        obtenerActuacionesClasificadasExpediente(numeroExp),
        obtenerVencimientosExpediente(numeroExp)
      ])

      setEstadisticas(stats)
      setActuacionesClasificadas(actuaciones)
      setVencimientos(venc)
      setIsProcesado(true)
    } catch (error) {
      // No hay datos de procesamiento - expediente no procesado
      setIsProcesado(false)
      setEstadisticas(null)
      setActuacionesClasificadas([])
      setVencimientos([])
    } finally {
      setIsLoadingProcesamiento(false)
    }
  }

  const handleProcesar = async () => {
    if (!expedienteActual) return

    setIsProcessing(true)
    try {
      // Convertir actuaciones al formato requerido
      const actuacionesInput: ActuacionInput[] = expedienteActual.actuaciones.map((act, index) => ({
        id: act.indice || index + 1,
        tipo: act.tipo || '',
        detalle: act.detalle || '',
        tiene_archivo: (act.archivos?.length || 0) > 0 || act.tiene_archivo,
        expediente_numero: expedienteActual.numero
      }))

      // Construir diccionario de rutas de PDFs
      const rutas_pdf: Record<number, string> = {}
      expedienteActual.actuaciones.forEach((act, index) => {
        const id = act.indice || index + 1
        if (act.ruta_pdf) {
          rutas_pdf[id] = act.ruta_pdf
        }
      })

      const resultado = await procesarExpediente({
        numero_expediente: expedienteActual.numero,
        actuaciones: actuacionesInput,
        rutas_pdf: Object.keys(rutas_pdf).length > 0 ? rutas_pdf : undefined,
        guardar_en_bd: true
      })

      setEstadisticas(resultado.estadisticas)
      setVencimientos(resultado.vencimientos_urgentes)
      setIsProcesado(true)

      toast.success('Expediente procesado', {
        description: `${resultado.estadisticas.total_actuaciones} actuaciones clasificadas`
      })

      // Recargar datos completos
      await cargarDatosProcesamiento(expedienteActual.numero)
    } catch (error) {
      toast.error('Error al procesar', {
        description: error instanceof Error ? error.message : 'Error desconocido'
      })
    } finally {
      setIsProcessing(false)
    }
  }

  const formatFechaExtraccion = (fecha: string | null) => {
    if (!fecha) return 'Desconocida'

    try {
      const parsedDate = new Date(fecha)
      return format(parsedDate, "dd 'de' MMMM 'de' yyyy 'a las' HH:mm", { locale: es })
    } catch {
      return fecha
    }
  }

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-12 space-y-4">
        <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
        <p className="text-gray-600 dark:text-gray-400">Cargando expediente...</p>
      </div>
    )
  }

  if (!expedienteActual) {
    return (
      <div className="space-y-6">
        <Button variant="outline" onClick={() => navigate('/expedientes')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Volver
        </Button>

        <Card>
          <CardContent className="py-12 text-center">
            <AlertCircle className="h-12 w-12 text-orange-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Expediente no encontrado
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              No se pudo cargar la informacion del expediente
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="outline" onClick={() => navigate('/expedientes')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Volver
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              {expedienteActual.numero}
            </h1>
            <ProcesamientoStatusBadge
              isProcesado={isProcesado}
              isProcessing={isProcessing}
              onProcesar={handleProcesar}
              compact
            />
          </div>
          <p className="mt-1 text-gray-600 dark:text-gray-400">
            Detalle del expediente
          </p>
        </div>
      </div>

      {/* Informacion Principal */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="text-2xl">{expedienteActual.numero}</CardTitle>
              <CardDescription className="mt-2 text-base">
                {expedienteActual.caratula}
              </CardDescription>
            </div>
            {expedienteActual.situacion && (
              <Badge className="text-sm">
                {expedienteActual.situacion}
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="flex items-start gap-3">
              <Building2 className="h-5 w-5 text-gray-400 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Dependencia
                </p>
                <p className="text-base text-gray-900 dark:text-white">
                  {expedienteActual.dependencia}
                </p>
              </div>
            </div>

            {expedienteActual.ultima_actuacion && (
              <div className="flex items-start gap-3">
                <Calendar className="h-5 w-5 text-gray-400 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                    Ultima Actuacion
                  </p>
                  <p className="text-base text-gray-900 dark:text-white">
                    {expedienteActual.ultima_actuacion}
                  </p>
                </div>
              </div>
            )}

            <div className="flex items-start gap-3">
              <FileText className="h-5 w-5 text-gray-400 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Total de Actuaciones
                </p>
                <p className="text-base text-gray-900 dark:text-white">
                  {expedienteActual.total_actuaciones}
                </p>
              </div>
            </div>

            {expedienteActual.fecha_extraccion && (
              <div className="flex items-start gap-3">
                <Clock className="h-5 w-5 text-gray-400 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                    Extraido el
                  </p>
                  <p className="text-base text-gray-900 dark:text-white">
                    {formatFechaExtraccion(expedienteActual.fecha_extraccion)}
                  </p>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs defaultValue="actuaciones" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="actuaciones" className="flex items-center gap-2">
            <ListTodo className="h-4 w-4" />
            Actuaciones ({expedienteActual.actuaciones.length})
          </TabsTrigger>
          <TabsTrigger value="mi-analisis" className="flex items-center gap-2">
            <StickyNote className="h-4 w-4" />
            Mi Analisis
          </TabsTrigger>
          <TabsTrigger value="procesamiento" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Procesamiento
            {isProcesado && estadisticas && (
              <Badge variant="secondary" className="ml-1 h-5 text-xs">
                {estadisticas.vencimientos_urgentes}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="vencimientos" className="flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            Vencimientos
            {vencimientos.length > 0 && (
              <Badge variant="destructive" className="ml-1 h-5 text-xs">
                {vencimientos.length}
              </Badge>
            )}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="actuaciones" className="mt-6">
          <ActuacionesList
            actuaciones={expedienteActual.actuaciones}
            expedienteNumero={expedienteActual.numero}
          />
        </TabsContent>

        <TabsContent value="mi-analisis" className="mt-6">
          <MiAnalisisList
            actuaciones={expedienteActual.actuaciones}
            expedienteNumero={expedienteActual.numero}
          />
        </TabsContent>

        <TabsContent value="procesamiento" className="mt-6 space-y-6">
          {!isProcesado ? (
            <Card>
              <CardContent className="py-12 text-center">
                <BarChart3 className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  Expediente no procesado
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  Procesa el expediente para ver la clasificacion de actuaciones, vencimientos y estadisticas
                </p>
                <Button onClick={handleProcesar} disabled={isProcessing}>
                  {isProcessing ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Procesando...
                    </>
                  ) : (
                    <>
                      <BarChart3 className="h-4 w-4 mr-2" />
                      Procesar Expediente
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          ) : (
            <>
              <EstadisticasExpedientePanel
                estadisticas={estadisticas}
                isLoading={isLoadingProcesamiento}
              />

              <div className="mt-6">
                <h3 className="text-lg font-semibold mb-4">Actuaciones Clasificadas</h3>
                <ActuacionesClasificadasList
                  actuaciones={actuacionesClasificadas}
                  isLoading={isLoadingProcesamiento}
                />
              </div>
            </>
          )}
        </TabsContent>

        <TabsContent value="vencimientos" className="mt-6">
          <VencimientosExpedientePanel
            vencimientos={vencimientos}
            isLoading={isLoadingProcesamiento}
          />
        </TabsContent>
      </Tabs>
    </div>
  )
}
