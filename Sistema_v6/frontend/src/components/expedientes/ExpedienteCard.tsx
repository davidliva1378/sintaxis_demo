import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { FileText, Calendar, Building2, Eye, FolderPlus, Bell } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { es } from 'date-fns/locale'
import type { ExpedienteResumen } from '@/types/expediente'

interface ExpedienteCardProps {
  expediente: ExpedienteResumen
  onView?: (numero: string) => void
  onAddToWorkspace?: (numero: string, caratula: string) => void
  onAddToMonitoreo?: (numero: string, caratula: string, dependencia?: string) => void
}

export default function ExpedienteCard({ expediente, onView, onAddToWorkspace, onAddToMonitoreo }: ExpedienteCardProps) {
  const getSituacionColor = (situacion: string | null) => {
    if (!situacion) return 'default'

    const situacionLower = situacion.toLowerCase()
    if (situacionLower.includes('tramite') || situacionLower.includes('activo')) {
      return 'default'
    }
    if (situacionLower.includes('sentencia') || situacionLower.includes('finalizado')) {
      return 'secondary'
    }
    if (situacionLower.includes('archivo')) {
      return 'outline'
    }
    return 'default'
  }

  const formatFecha = (fecha: string | null) => {
    if (!fecha) return 'Sin fecha'

    try {
      const parsedDate = new Date(fecha)
      return formatDistanceToNow(parsedDate, { addSuffix: true, locale: es })
    } catch {
      return fecha
    }
  }

  return (
    <Card className="hover:shadow-lg transition-shadow cursor-pointer group">
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <FileText className="h-5 w-5 text-blue-600 flex-shrink-0" />
            <CardTitle className="text-base truncate group-hover:text-blue-600 transition-colors">
              {expediente.numero}
            </CardTitle>
          </div>
          {expediente.situacion && (
            <Badge variant={getSituacionColor(expediente.situacion)} className="flex-shrink-0">
              {expediente.situacion}
            </Badge>
          )}
        </div>
        <CardDescription className="line-clamp-2 min-h-[40px]">
          {expediente.caratula}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
            <Building2 className="h-4 w-4 flex-shrink-0" />
            <span className="truncate">{expediente.dependencia}</span>
          </div>

          {expediente.ultima_actuacion && (
            <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
              <Calendar className="h-4 w-4 flex-shrink-0" />
              <span>Última actuación: {formatFecha(expediente.ultima_actuacion)}</span>
            </div>
          )}

          <div className="mt-3 flex gap-2">
            {onView && (
              <button
                onClick={() => onView(expediente.numero)}
                className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium text-blue-600 bg-blue-50 dark:bg-blue-900/20 rounded-md hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors"
              >
                <Eye className="h-4 w-4" />
                Ver detalle
              </button>
            )}
            {onAddToWorkspace && (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  onAddToWorkspace(expediente.numero, expediente.caratula)
                }}
                className="flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium text-green-600 bg-green-50 dark:bg-green-900/20 rounded-md hover:bg-green-100 dark:hover:bg-green-900/30 transition-colors"
                title="Agregar a Workspace"
              >
                <FolderPlus className="h-4 w-4" />
              </button>
            )}
            {onAddToMonitoreo && (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  onAddToMonitoreo(expediente.numero, expediente.caratula, expediente.dependencia)
                }}
                className="flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium text-orange-600 bg-orange-50 dark:bg-orange-900/20 rounded-md hover:bg-orange-100 dark:hover:bg-orange-900/30 transition-colors"
                title="Agregar al Monitoreo"
              >
                <Bell className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
