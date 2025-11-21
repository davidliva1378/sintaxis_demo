import { Clock, AlertTriangle, FileText } from 'lucide-react'
import { VencimientoUrgente, NivelUrgencia, formatDiasRestantes, COLORES_URGENCIA } from '@/types/procesamiento'
import { format, parseISO } from 'date-fns'
import { es } from 'date-fns/locale'

interface VencimientosUrgentesListaProps {
  vencimientos: VencimientoUrgente[]
  limite?: number
}

export default function VencimientosUrgentesLista({
  vencimientos,
  limite
}: VencimientosUrgentesListaProps) {
  const vencimientosAMostrar = limite ? vencimientos.slice(0, limite) : vencimientos

  return (
    <div className="space-y-3">
      {vencimientosAMostrar.map((venc) => (
        <VencimientoCard key={venc.id} vencimiento={venc} />
      ))}

      {limite && vencimientos.length > limite && (
        <div className="text-center py-2">
          <button className="text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400">
            Ver {vencimientos.length - limite} vencimientos más →
          </button>
        </div>
      )}
    </div>
  )
}

function VencimientoCard({ vencimiento }: { vencimiento: VencimientoUrgente }) {
  const colorClasses = getColorClasses(vencimiento.nivel_urgencia)
  const fechaVenc = parseISO(vencimiento.fecha_vencimiento)

  return (
    <div className={`
      border rounded-lg p-4 transition-all hover:shadow-md
      ${colorClasses.bg} ${colorClasses.border}
    `}>
      <div className="flex items-start justify-between gap-4">
        {/* Contenido principal */}
        <div className="flex-1 space-y-2">
          {/* Expediente y tipo */}
          <div className="flex items-center gap-2">
            <FileText className={`h-4 w-4 ${colorClasses.icon}`} />
            <span className={`font-semibold ${colorClasses.text}`}>
              {vencimiento.expediente_numero}
            </span>
            <span className={`text-xs px-2 py-1 rounded ${colorClasses.badge}`}>
              {vencimiento.tipo.replace('_', ' ').toUpperCase()}
            </span>
          </div>

          {/* Detalle de la actuación */}
          <div>
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {vencimiento.actuacion_tipo}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-2">
              {vencimiento.actuacion_detalle}
            </p>
          </div>

          {/* Descripción del vencimiento */}
          {vencimiento.descripcion && (
            <p className="text-sm text-gray-600 dark:text-gray-300">
              {vencimiento.descripcion}
            </p>
          )}
        </div>

        {/* Fecha y urgencia */}
        <div className="text-right space-y-1">
          <div className={`flex items-center gap-1 justify-end ${colorClasses.text}`}>
            <Clock className="h-4 w-4" />
            <span className="text-sm font-semibold">
              {formatDiasRestantes(vencimiento.dias_restantes)}
            </span>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {format(fechaVenc, "d 'de' MMMM", { locale: es })}
          </p>
          <span className={`
            inline-block text-xs font-semibold px-2 py-1 rounded
            ${colorClasses.urgenciaBadge}
          `}>
            {getNivelUrgenciaLabel(vencimiento.nivel_urgencia)}
          </span>
        </div>
      </div>
    </div>
  )
}

function getColorClasses(nivel: NivelUrgencia) {
  switch (nivel) {
    case NivelUrgencia.VENCIDO:
      return {
        bg: 'bg-black/5 dark:bg-black/30',
        border: 'border-black dark:border-black',
        text: 'text-black dark:text-white',
        icon: 'text-black dark:text-white',
        badge: 'bg-black text-white',
        urgenciaBadge: 'bg-black text-white'
      }
    case NivelUrgencia.CRITICO:
      return {
        bg: 'bg-red-50 dark:bg-red-900/20',
        border: 'border-red-200 dark:border-red-800',
        text: 'text-red-900 dark:text-red-200',
        icon: 'text-red-600 dark:text-red-400',
        badge: 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-200',
        urgenciaBadge: 'bg-red-600 text-white'
      }
    case NivelUrgencia.URGENTE:
      return {
        bg: 'bg-orange-50 dark:bg-orange-900/20',
        border: 'border-orange-200 dark:border-orange-800',
        text: 'text-orange-900 dark:text-orange-200',
        icon: 'text-orange-600 dark:text-orange-400',
        badge: 'bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-200',
        urgenciaBadge: 'bg-orange-500 text-white'
      }
    case NivelUrgencia.PROXIMO:
      return {
        bg: 'bg-yellow-50 dark:bg-yellow-900/20',
        border: 'border-yellow-200 dark:border-yellow-800',
        text: 'text-yellow-900 dark:text-yellow-200',
        icon: 'text-yellow-600 dark:text-yellow-400',
        badge: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-200',
        urgenciaBadge: 'bg-yellow-400 text-gray-900'
      }
    default: // NORMAL
      return {
        bg: 'bg-green-50 dark:bg-green-900/20',
        border: 'border-green-200 dark:border-green-800',
        text: 'text-green-900 dark:text-green-200',
        icon: 'text-green-600 dark:text-green-400',
        badge: 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-200',
        urgenciaBadge: 'bg-green-500 text-white'
      }
  }
}

function getNivelUrgenciaLabel(nivel: NivelUrgencia): string {
  switch (nivel) {
    case NivelUrgencia.VENCIDO:
      return 'VENCIDO'
    case NivelUrgencia.CRITICO:
      return 'CRÍTICO'
    case NivelUrgencia.URGENTE:
      return 'URGENTE'
    case NivelUrgencia.PROXIMO:
      return 'PRÓXIMO'
    default:
      return 'NORMAL'
  }
}
