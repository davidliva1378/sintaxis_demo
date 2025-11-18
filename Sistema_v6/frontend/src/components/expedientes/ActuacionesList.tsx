import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { FileText, Download, Calendar, Building2, File } from 'lucide-react'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'
import type { Actuacion } from '@/types/expediente'

interface ActuacionesListProps {
  actuaciones: Actuacion[]
}

export default function ActuacionesList({ actuaciones }: ActuacionesListProps) {
  const formatFecha = (fecha: string | null) => {
    if (!fecha) return 'Sin fecha'

    try {
      const parsedDate = new Date(fecha)
      return format(parsedDate, "dd 'de' MMMM 'de' yyyy", { locale: es })
    } catch {
      return fecha
    }
  }

  if (actuaciones.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500 dark:text-gray-400">
            No hay actuaciones registradas
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {actuaciones.map((actuacion) => (
        <Card key={actuacion.indice}>
          <CardContent className="p-4">
            <div className="flex gap-4">
              {/* Índice */}
              <div className="flex-shrink-0">
                <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/20 flex items-center justify-center font-semibold text-blue-600">
                  {actuacion.indice}
                </div>
              </div>

              {/* Contenido */}
              <div className="flex-1 min-w-0 space-y-2">
                {/* Tipo */}
                {actuacion.tipo && (
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-500 dark:text-gray-400 min-w-[60px]">
                      Tipo:
                    </span>
                    <Badge variant="outline">
                      {actuacion.tipo}
                    </Badge>
                    {actuacion.tiene_archivo && (
                      <div className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400 ml-auto">
                        <File className="h-4 w-4" />
                        {actuacion.tipo_archivo?.toUpperCase() || 'PDF'}
                      </div>
                    )}
                  </div>
                )}

                {/* Oficina */}
                <div className="flex items-start gap-2">
                  <span className="text-sm font-medium text-gray-500 dark:text-gray-400 min-w-[60px]">
                    Oficina:
                  </span>
                  <div>
                    <p className="text-sm text-gray-900 dark:text-white font-medium">
                      {actuacion.oficina}
                    </p>
                    {actuacion.oficina_completa && actuacion.oficina_completa !== actuacion.oficina && (
                      <p className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">
                        ({actuacion.oficina_completa})
                      </p>
                    )}
                  </div>
                </div>

                {/* Fecha */}
                {actuacion.fecha && (
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-500 dark:text-gray-400 min-w-[60px]">
                      Fecha:
                    </span>
                    <div className="flex items-center gap-1 text-sm text-gray-700 dark:text-gray-300">
                      <Calendar className="h-4 w-4" />
                      {formatFecha(actuacion.fecha)}
                    </div>
                  </div>
                )}

                {/* Foja */}
                {actuacion.foja && (
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-500 dark:text-gray-400 min-w-[60px]">
                      Foja:
                    </span>
                    <div className="flex items-center gap-1 text-sm text-gray-700 dark:text-gray-300">
                      <FileText className="h-4 w-4" />
                      {actuacion.foja}
                    </div>
                  </div>
                )}

                {/* Detalle */}
                {actuacion.detalle && (
                  <div className="flex gap-2">
                    <span className="text-sm font-medium text-gray-500 dark:text-gray-400 min-w-[60px] flex-shrink-0">
                      Detalle:
                    </span>
                    <p className="text-sm text-gray-700 dark:text-gray-300 flex-1">
                      {actuacion.detalle}
                    </p>
                  </div>
                )}

                {/* Archivo adjunto */}
                {actuacion.tiene_archivo && actuacion.nombre_archivo && (
                  <div className="flex items-center gap-2 mt-2">
                    <button
                      className="flex items-center gap-1 px-3 py-1 text-sm text-blue-600 bg-blue-50 dark:bg-blue-900/20 rounded hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors"
                      onClick={() => {
                        // Implementar descarga en futuras fases
                        alert('Funcionalidad de descarga pendiente de implementación')
                      }}
                    >
                      <Download className="h-4 w-4" />
                      Descargar {actuacion.nombre_archivo}
                    </button>
                    {actuacion.descargado && (
                      <Badge variant="secondary" className="text-xs">
                        Descargado
                      </Badge>
                    )}
                  </div>
                )}

                {/* Marcadores */}
                <div className="flex gap-2 mt-2">
                  {actuacion.es_historica && (
                    <Badge variant="outline" className="text-xs">
                      Histórica
                    </Badge>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
