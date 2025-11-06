/**
 * LogsList - Lista de cambios detectados en expedientes monitoreados
 */

import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { formatDistanceToNow, format } from 'date-fns'
import { es } from 'date-fns/locale'
import {
  FilePlus,
  RefreshCw,
  Paperclip,
  Edit,
  Info,
  Eye,
  FileText,
  CheckCircle2,
  Circle,
} from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useMonitoreoStore } from '@/stores/monitoreoStore'
import { TIPOS_CAMBIO, type TipoCambio } from '@/types/monitoreo'

// Mapeo de iconos para cada tipo de cambio
const ICON_MAP: Record<TipoCambio, React.ComponentType<{ className?: string }>> = {
  nueva_actuacion: FilePlus,
  cambio_estado: RefreshCw,
  nuevo_archivo: Paperclip,
  modificacion: Edit,
  otro: Info,
}

// Mapeo de colores para badges
const COLOR_MAP: Record<string, string> = {
  blue: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
  purple: 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400',
  green: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
  orange: 'bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-400',
  gray: 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400',
}

interface LogsListProps {
  expedienteId?: number
  showExpedienteInfo?: boolean
  limit?: number
}

export default function LogsList({
  expedienteId,
  showExpedienteInfo = true,
  limit,
}: LogsListProps) {
  const navigate = useNavigate()
  const { cambios, isLoading, listarCambios, marcarComoLeido, marcarTodosLeidos } =
    useMonitoreoStore()

  useEffect(() => {
    listarCambios(expedienteId)
  }, [listarCambios, expedienteId])

  const formatFecha = (fecha: string) => {
    try {
      const date = new Date(fecha)
      const relativa = formatDistanceToNow(date, { addSuffix: true, locale: es })
      const absoluta = format(date, "dd/MM/yyyy 'a las' HH:mm", { locale: es })
      return { relativa, absoluta }
    } catch {
      return { relativa: fecha, absoluta: fecha }
    }
  }

  const handleMarcarLeido = async (cambioId: number) => {
    await marcarComoLeido(cambioId)
  }

  const handleVerExpediente = (numero: string) => {
    navigate(`/expedientes/${numero}`)
  }

  const cambiosSinLeer = cambios.filter(c => !c.leido).length
  const cambiosMostrar = limit ? cambios.slice(0, limit) : cambios

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <RefreshCw className="h-6 w-6 animate-spin text-blue-600" />
        <span className="ml-3 text-gray-600 dark:text-gray-400">
          Cargando cambios...
        </span>
      </div>
    )
  }

  // Empty state
  if (cambios.length === 0) {
    return (
      <Card className="p-12">
        <div className="text-center">
          <FileText className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            No hay cambios detectados
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Cuando el sistema detecte cambios en los expedientes monitoreados, aparecerán aquí
          </p>
        </div>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header con contador */}
      {cambiosSinLeer > 0 && (
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Badge className="bg-blue-600">
              {cambiosSinLeer}
            </Badge>
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {cambiosSinLeer === 1 ? 'cambio sin leer' : 'cambios sin leer'}
            </span>
          </div>
          <Button variant="outline" size="sm" onClick={marcarTodosLeidos}>
            <CheckCircle2 className="h-4 w-4 mr-2" />
            Marcar todos como leídos
          </Button>
        </div>
      )}

      {/* Lista de cambios */}
      <div className="space-y-3">
        {cambiosMostrar.map((cambio, index) => {
          const IconComponent = ICON_MAP[cambio.tipo_cambio]
          const tipoInfo = TIPOS_CAMBIO[cambio.tipo_cambio]
          const { relativa, absoluta } = formatFecha(cambio.fecha_deteccion)

          return (
            <Card
              key={cambio.id}
              className={`p-4 transition-all ${
                !cambio.leido
                  ? 'border-l-4 border-l-blue-500 bg-blue-50/50 dark:bg-blue-900/10'
                  : 'border-l-4 border-l-transparent'
              }`}
            >
              <div className="flex items-start gap-4">
                {/* Indicador de leído/no leído */}
                <div className="pt-1">
                  {cambio.leido ? (
                    <CheckCircle2 className="h-5 w-5 text-gray-400" />
                  ) : (
                    <Circle className="h-5 w-5 text-blue-600 fill-blue-600" />
                  )}
                </div>

                {/* Icono del tipo de cambio */}
                <div
                  className="p-2 rounded-lg flex-shrink-0"
                  style={{ backgroundColor: `${tipoInfo.color}20` }}
                >
                  <IconComponent
                    className="h-5 w-5"
                    style={{ color: tipoInfo.color === 'gray' ? '#6b7280' : tipoInfo.color }}
                  />
                </div>

                {/* Contenido */}
                <div className="flex-1 min-w-0">
                  {/* Expediente info */}
                  {showExpedienteInfo && (
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-sm font-semibold text-gray-900 dark:text-white">
                        {cambio.expediente_numero}
                      </span>
                      <Badge className={COLOR_MAP[tipoInfo.color] || COLOR_MAP.gray}>
                        {tipoInfo.label}
                      </Badge>
                    </div>
                  )}

                  {!showExpedienteInfo && (
                    <Badge className={`${COLOR_MAP[tipoInfo.color] || COLOR_MAP.gray} mb-2`}>
                      {tipoInfo.label}
                    </Badge>
                  )}

                  {/* Descripción */}
                  <p className="text-sm text-gray-900 dark:text-white font-medium mb-1">
                    {cambio.descripcion}
                  </p>

                  {/* Carátula */}
                  {showExpedienteInfo && (
                    <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-1 mb-2">
                      {cambio.expediente_caratula}
                    </p>
                  )}

                  {/* Detalles adicionales */}
                  {cambio.detalles && Object.keys(cambio.detalles).length > 0 && (
                    <div className="mt-2 p-2 bg-gray-50 dark:bg-gray-800 rounded text-xs">
                      {Object.entries(cambio.detalles).map(([key, value]) => (
                        <div key={key} className="flex gap-2">
                          <span className="text-gray-500 dark:text-gray-400">
                            {key.replace(/_/g, ' ')}:
                          </span>
                          <span className="text-gray-900 dark:text-white font-medium">
                            {String(value)}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Footer */}
                  <div className="flex items-center justify-between mt-3">
                    <div className="text-xs text-gray-500 dark:text-gray-400" title={absoluta}>
                      {relativa}
                    </div>

                    <div className="flex gap-2">
                      {!cambio.leido && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleMarcarLeido(cambio.id)}
                          className="text-xs"
                        >
                          Marcar como leído
                        </Button>
                      )}
                      {showExpedienteInfo && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleVerExpediente(cambio.expediente_numero)}
                          className="text-xs"
                        >
                          <Eye className="h-3 w-3 mr-1" />
                          Ver expediente
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          )
        })}
      </div>

      {/* Mostrar más link */}
      {limit && cambios.length > limit && (
        <div className="text-center">
          <Button variant="outline" size="sm">
            Ver todos los cambios ({cambios.length})
          </Button>
        </div>
      )}
    </div>
  )
}
