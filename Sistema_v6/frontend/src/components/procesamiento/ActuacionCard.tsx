import { FileText, AlertCircle, Clock, Tag } from 'lucide-react'
import { ActuacionPorUtilidad, UtilidadJuridica, formatDiasRestantes } from '@/types/procesamiento'
import { format, parseISO } from 'date-fns'
import { es } from 'date-fns/locale'

interface ActuacionCardProps {
  actuacion: ActuacionPorUtilidad
  onClick?: () => void
}

export default function ActuacionCard({ actuacion, onClick }: ActuacionCardProps) {
  const colorClasses = getUtilidadColorClasses(actuacion.utilidad)
  const showVencimiento = actuacion.tiene_vencimiento && actuacion.fecha_vencimiento

  return (
    <div
      className={`
        border rounded-lg p-4 transition-all
        ${onClick ? 'cursor-pointer hover:shadow-lg' : 'hover:shadow-md'}
        ${colorClasses.bg} ${colorClasses.border}
      `}
      onClick={onClick}
    >
      {/* Header con utilidad y score */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <FileText className={`h-4 w-4 ${colorClasses.icon}`} />
          <span className={`text-xs font-semibold px-2 py-1 rounded ${colorClasses.badge}`}>
            {getUtilidadLabel(actuacion.utilidad)}
          </span>
        </div>
        <div className="flex items-center gap-1">
          <Tag className="h-3 w-3 text-gray-400" />
          <span className="text-xs font-mono text-gray-500">
            {actuacion.score}
          </span>
        </div>
      </div>

      {/* Expediente */}
      <div className="mb-2">
        <p className="text-xs text-gray-500 dark:text-gray-400">Expediente</p>
        <p className={`text-sm font-semibold ${colorClasses.text}`}>
          {actuacion.expediente_numero}
        </p>
      </div>

      {/* Tipo de actuación */}
      <div className="mb-2">
        <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {actuacion.tipo}
        </p>
      </div>

      {/* Detalle (truncado) */}
      <div className="mb-3">
        <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-3">
          {actuacion.detalle}
        </p>
      </div>

      {/* Vencimiento (si existe) */}
      {showVencimiento && actuacion.fecha_vencimiento && (
        <div className={`
          flex items-center gap-2 p-2 rounded mt-3
          ${actuacion.dias_restantes !== undefined && actuacion.dias_restantes <= 3
            ? 'bg-red-100 dark:bg-red-900/30'
            : 'bg-gray-100 dark:bg-gray-700'}
        `}>
          <Clock className={`h-3 w-3 ${
            actuacion.dias_restantes !== undefined && actuacion.dias_restantes <= 3
              ? 'text-red-600'
              : 'text-gray-500'
          }`} />
          <div className="flex-1">
            <p className="text-xs text-gray-600 dark:text-gray-300">
              Vence: {format(parseISO(actuacion.fecha_vencimiento), "d 'de' MMMM", { locale: es })}
            </p>
          </div>
          {actuacion.dias_restantes !== undefined && (
            <span className={`
              text-xs font-semibold
              ${actuacion.dias_restantes <= 3 ? 'text-red-700' : 'text-gray-700'}
            `}>
              {formatDiasRestantes(actuacion.dias_restantes)}
            </span>
          )}
        </div>
      )}

      {/* Indicador de urgencia */}
      {actuacion.dias_restantes !== undefined && actuacion.dias_restantes <= 3 && (
        <div className="flex items-center gap-1 mt-2 text-red-600">
          <AlertCircle className="h-3 w-3" />
          <span className="text-xs font-semibold">Requiere atención urgente</span>
        </div>
      )}
    </div>
  )
}

function getUtilidadColorClasses(utilidad: UtilidadJuridica) {
  switch (utilidad) {
    case UtilidadJuridica.ALTA:
      return {
        bg: 'bg-red-50 dark:bg-red-900/20',
        border: 'border-red-200 dark:border-red-800',
        text: 'text-red-900 dark:text-red-200',
        icon: 'text-red-600 dark:text-red-400',
        badge: 'bg-red-600 text-white'
      }
    case UtilidadJuridica.MEDIA:
      return {
        bg: 'bg-yellow-50 dark:bg-yellow-900/20',
        border: 'border-yellow-200 dark:border-yellow-800',
        text: 'text-yellow-900 dark:text-yellow-200',
        icon: 'text-yellow-600 dark:text-yellow-400',
        badge: 'bg-yellow-500 text-white'
      }
    case UtilidadJuridica.BAJA:
      return {
        bg: 'bg-blue-50 dark:bg-blue-900/20',
        border: 'border-blue-200 dark:border-blue-800',
        text: 'text-blue-900 dark:text-blue-200',
        icon: 'text-blue-600 dark:text-blue-400',
        badge: 'bg-blue-500 text-white'
      }
    default: // NULA
      return {
        bg: 'bg-gray-50 dark:bg-gray-800',
        border: 'border-gray-200 dark:border-gray-700',
        text: 'text-gray-900 dark:text-gray-200',
        icon: 'text-gray-600 dark:text-gray-400',
        badge: 'bg-gray-400 text-white'
      }
  }
}

function getUtilidadLabel(utilidad: UtilidadJuridica): string {
  switch (utilidad) {
    case UtilidadJuridica.ALTA:
      return 'ALTA'
    case UtilidadJuridica.MEDIA:
      return 'MEDIA'
    case UtilidadJuridica.BAJA:
      return 'BAJA'
    default:
      return 'NULA'
  }
}
