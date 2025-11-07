import { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  ArrowLeft,
  FileText,
  Building2,
  Calendar,
  Clock,
  Loader2,
  AlertCircle,
} from 'lucide-react'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'
import { useExpedientesStore } from '@/stores/expedientesStore'
import ActuacionesList from '@/components/expedientes/ActuacionesList'

export default function ExpedienteDetallePage() {
  const { numero } = useParams<{ numero: string }>()
  const navigate = useNavigate()

  const {
    expedienteActual,
    isLoading,
    obtenerExpediente,
    limpiarExpedienteActual,
  } = useExpedientesStore()

  useEffect(() => {
    if (numero) {
      obtenerExpediente(numero)
    }

    return () => {
      limpiarExpedienteActual()
    }
  }, [numero])

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
              No se pudo cargar la información del expediente
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
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            {expedienteActual.numero}
          </h1>
          <p className="mt-1 text-gray-600 dark:text-gray-400">
            Detalle del expediente
          </p>
        </div>
      </div>

      {/* Información Principal */}
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
                    Última Actuación
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
                    Extraído el
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

      {/* Actuaciones */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          Actuaciones ({expedienteActual.actuaciones.length})
        </h2>
        <ActuacionesList actuaciones={expedienteActual.actuaciones} />
      </div>
    </div>
  )
}
