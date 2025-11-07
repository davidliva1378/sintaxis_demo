/**
 * MonitoreoCard - Card para mostrar expediente monitoreado
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { formatDistanceToNow } from 'date-fns'
import { es } from 'date-fns/locale'
import {
  FileText,
  Building2,
  Clock,
  Activity,
  Eye,
  Play,
  Pause,
  Trash2,
  RefreshCw,
  MoreVertical,
} from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import type { ExpedienteMonitoreado } from '@/types/monitoreo'

interface MonitoreoCardProps {
  expediente: ExpedienteMonitoreado
  onToggle: (id: number, activo: boolean) => void
  onRemove: (id: number) => void
  onVerify: (id: number) => void
  onViewChanges: (id: number) => void
}

export default function MonitoreoCard({
  expediente,
  onToggle,
  onRemove,
  onVerify,
  onViewChanges,
}: MonitoreoCardProps) {
  const [showMenu, setShowMenu] = useState(false)
  const [isVerifying, setIsVerifying] = useState(false)
  const navigate = useNavigate()

  const formatFecha = (fecha: string | null | undefined) => {
    if (!fecha) return 'Nunca'
    try {
      return formatDistanceToNow(new Date(fecha), { addSuffix: true, locale: es })
    } catch {
      return fecha
    }
  }

  const handleVerify = async () => {
    setIsVerifying(true)
    await onVerify(expediente.id)
    setIsVerifying(false)
  }

  const handleToggle = () => {
    setShowMenu(false)
    onToggle(expediente.id, !expediente.activo)
  }

  const handleRemove = () => {
    setShowMenu(false)
    if (
      confirm(
        `¿Estás seguro de remover "${expediente.expediente_numero}" del monitoreo?\n\nEsto detendrá las verificaciones automáticas.`
      )
    ) {
      onRemove(expediente.id)
    }
  }

  const handleViewExpediente = () => {
    navigate(`/expedientes/${expediente.expediente_numero}`)
  }

  return (
    <Card
      className={`p-6 transition-all duration-200 group relative ${
        expediente.activo
          ? 'border-l-4 border-l-green-500 hover:shadow-lg'
          : 'border-l-4 border-l-gray-300 dark:border-l-gray-600 opacity-75'
      }`}
    >
      {/* Badge de estado */}
      <div className="absolute top-4 right-4 flex items-center gap-2">
        <Badge
          variant={expediente.activo ? 'default' : 'outline'}
          className={
            expediente.activo
              ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
              : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
          }
        >
          {expediente.activo ? (
            <>
              <Activity className="h-3 w-3 mr-1" />
              Activo
            </>
          ) : (
            <>
              <Pause className="h-3 w-3 mr-1" />
              Pausado
            </>
          )}
        </Badge>

        {/* Menú dropdown */}
        <div className="relative">
          <Button
            variant="ghost"
            size="sm"
            className="opacity-0 group-hover:opacity-100 transition-opacity"
            onClick={e => {
              e.stopPropagation()
              setShowMenu(!showMenu)
            }}
          >
            <MoreVertical className="h-4 w-4" />
          </Button>

          {showMenu && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={e => {
                  e.stopPropagation()
                  setShowMenu(false)
                }}
              />
              <div className="absolute right-0 top-8 z-20 w-48 bg-white dark:bg-gray-800 rounded-md shadow-lg border border-gray-200 dark:border-gray-700 py-1">
                <button
                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
                  onClick={handleToggle}
                >
                  {expediente.activo ? (
                    <>
                      <Pause className="h-4 w-4" />
                      Pausar monitoreo
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4" />
                      Activar monitoreo
                    </>
                  )}
                </button>
                <button
                  className="w-full px-4 py-2 text-left text-sm hover:bg-red-50 dark:hover:bg-red-900/20 text-red-600 dark:text-red-400 flex items-center gap-2"
                  onClick={handleRemove}
                >
                  <Trash2 className="h-4 w-4" />
                  Remover
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Información del expediente */}
      <div className="pr-32 mb-4">
        <div className="flex items-center gap-2 mb-2">
          <FileText className="h-5 w-5 text-blue-600 dark:text-blue-400" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {expediente.expediente_numero}
          </h3>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
          {expediente.expediente_caratula}
        </p>
      </div>

      {/* Dependencia */}
      {expediente.expediente_dependencia && (
        <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 mb-3">
          <Building2 className="h-4 w-4" />
          <span className="truncate">{expediente.expediente_dependencia}</span>
        </div>
      )}

      {/* Estadísticas */}
      <div className="grid grid-cols-2 gap-4 mb-4 py-3 border-y border-gray-200 dark:border-gray-700">
        <div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">
            Última verificación
          </div>
          <div className="text-sm font-medium text-gray-900 dark:text-white">
            {formatFecha(expediente.ultima_verificacion)}
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">
            Cambios detectados
          </div>
          <div className="text-sm font-medium text-gray-900 dark:text-white">
            {expediente.total_cambios_detectados}
          </div>
        </div>
      </div>

      {/* Última actuación */}
      {expediente.ultima_actuacion_fecha && (
        <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 mb-4">
          <Clock className="h-4 w-4" />
          <span>
            Última actuación: {formatFecha(expediente.ultima_actuacion_fecha)}
          </span>
        </div>
      )}

      {/* Acciones */}
      <div className="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={handleViewExpediente}
          className="flex-1"
        >
          <Eye className="h-4 w-4 mr-2" />
          Ver expediente
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onViewChanges(expediente.id)}
          disabled={expediente.total_cambios_detectados === 0}
        >
          {expediente.total_cambios_detectados > 0 && (
            <Badge className="mr-2 bg-blue-600">{expediente.total_cambios_detectados}</Badge>
          )}
          Cambios
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={handleVerify}
          disabled={!expediente.activo || isVerifying}
          title={expediente.activo ? 'Verificar ahora' : 'El monitoreo está pausado'}
        >
          <RefreshCw className={`h-4 w-4 ${isVerifying ? 'animate-spin' : ''}`} />
        </Button>
      </div>
    </Card>
  )
}
