import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { CheckCircle2, XCircle, AlertCircle, Loader2, Play } from 'lucide-react'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'

interface ProcesamientoStatusBadgeProps {
  isProcesado: boolean
  fechaProcesamiento?: string
  isOutdated?: boolean
  isProcessing?: boolean
  onProcesar?: () => void
  compact?: boolean
}

export default function ProcesamientoStatusBadge({
  isProcesado,
  fechaProcesamiento,
  isOutdated = false,
  isProcessing = false,
  onProcesar,
  compact = false
}: ProcesamientoStatusBadgeProps) {
  if (isProcessing) {
    return (
      <Badge variant="secondary" className="flex items-center gap-1">
        <Loader2 className="h-3 w-3 animate-spin" />
        {!compact && 'Procesando...'}
      </Badge>
    )
  }

  if (!isProcesado) {
    return (
      <div className="flex items-center gap-2">
        <Badge variant="outline" className="flex items-center gap-1 text-gray-500">
          <XCircle className="h-3 w-3" />
          {!compact && 'Sin procesar'}
        </Badge>
        {onProcesar && (
          <Button size="sm" variant="outline" onClick={onProcesar} className="h-6 text-xs">
            <Play className="h-3 w-3 mr-1" />
            Procesar
          </Button>
        )}
      </div>
    )
  }

  if (isOutdated) {
    return (
      <div className="flex items-center gap-2">
        <Badge variant="secondary" className="flex items-center gap-1 bg-yellow-100 text-yellow-700">
          <AlertCircle className="h-3 w-3" />
          {!compact && 'Desactualizado'}
        </Badge>
        {onProcesar && (
          <Button size="sm" variant="outline" onClick={onProcesar} className="h-6 text-xs">
            <Play className="h-3 w-3 mr-1" />
            Reprocesar
          </Button>
        )}
      </div>
    )
  }

  const formatFecha = (fecha: string) => {
    try {
      return format(new Date(fecha), "dd/MM/yy HH:mm", { locale: es })
    } catch {
      return fecha
    }
  }

  return (
    <div className="flex items-center gap-2">
      <Badge variant="secondary" className="flex items-center gap-1 bg-green-100 text-green-700">
        <CheckCircle2 className="h-3 w-3" />
        {compact ? 'Procesado' : `Procesado ${fechaProcesamiento ? formatFecha(fechaProcesamiento) : ''}`}
      </Badge>
      {onProcesar && (
        <Button size="sm" variant="ghost" onClick={onProcesar} className="h-6 text-xs">
          <Play className="h-3 w-3 mr-1" />
          Reprocesar
        </Button>
      )}
    </div>
  )
}
