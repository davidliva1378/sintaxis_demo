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
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="flex-1">
                    {actuacion.tipo && (
                      <Badge variant="outline" className="mb-2">
                        {actuacion.tipo}
                      </Badge>
                    )}
                    <h4 className="font-semibold text-gray-900 dark:text-white">
                      {actuacion.oficina}
                    </h4>
                    {actuacion.oficina_completa && actuacion.oficina_completa !== actuacion.oficina && (
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {actuacion.oficina_completa}
                      </p>
                    )}
                  </div>

                  {actuacion.tiene_archivo && (
                    <div className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
                      <File className="h-4 w-4" />
                      {actuacion.tipo_archivo?.toUpperCase() || 'PDF'}
                    </div>
                  )}
                </div>

                {/* Fecha y Foja */}
                <div className="flex flex-wrap gap-4 text-sm text-gray-600 dark:text-gray-400 mb-2">
                  {actuacion.fecha && (
                    <div className="flex items-center gap-1">
                      <Calendar className="h-4 w-4" />
                      {formatFecha(actuacion.fecha)}
                    </div>
                  )}
                  {actuacion.foja && (
                    <div className="flex items-center gap-1">
                      <FileText className="h-4 w-4" />
                      Foja: {actuacion.foja}
                    </div>
                  )}
                </div>

                {/* Detalle */}
                {actuacion.detalle && (
                  <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
                    {actuacion.detalle}
                  </p>
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
