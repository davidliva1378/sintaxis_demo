/**
 * Panel de Analisis IA para un expediente
 * Muestra clasificacion IA e indexacion RAG de actuaciones
 */

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import {
  obtenerAnalisisIA,
  AnalisisIAExpedienteResponse,
  ActuacionConAnalisisIA
} from '@/api/expedientesApi'
import {
  Brain,
  Database,
  CheckCircle2,
  XCircle,
  AlertCircle,
  ChevronDown,
  ChevronRight
} from 'lucide-react'

interface AnalisisIAPanelProps {
  numeroExpediente: string
}

export function AnalisisIAPanel({ numeroExpediente }: AnalisisIAPanelProps) {
  const [data, setData] = useState<AnalisisIAExpedienteResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedActuacion, setExpandedActuacion] = useState<number | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        setError(null)
        const result = await obtenerAnalisisIA(numeroExpediente)
        setData(result)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error desconocido')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [numeroExpediente])

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (error) {
    return (
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle className="text-destructive flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            Error al cargar analisis IA
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">{error}</p>
        </CardContent>
      </Card>
    )
  }

  if (!data) {
    return null
  }

  const toggleActuacion = (indice: number) => {
    setExpandedActuacion(expandedActuacion === indice ? null : indice)
  }

  const getConfianzaColor = (confianza: number | null) => {
    if (confianza === null) return 'bg-gray-100 text-gray-800'
    if (confianza >= 0.8) return 'bg-green-100 text-green-800'
    if (confianza >= 0.6) return 'bg-yellow-100 text-yellow-800'
    return 'bg-red-100 text-red-800'
  }

  return (
    <div className="space-y-6">
      {/* Resumen estadistico */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Brain className="h-4 w-4 text-purple-500" />
              Clasificacion IA
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Actuaciones clasificadas</span>
                <span className="font-medium">
                  {data.actuaciones_con_ia} / {data.total_actuaciones}
                </span>
              </div>
              <Progress value={data.porcentaje_clasificado} className="h-2" />
              <p className="text-xs text-muted-foreground">
                {data.porcentaje_clasificado}% completado
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Database className="h-4 w-4 text-blue-500" />
              Indexacion RAG
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Actuaciones indexadas</span>
                <span className="font-medium">
                  {data.actuaciones_indexadas} / {data.total_actuaciones}
                </span>
              </div>
              <Progress value={data.porcentaje_indexado} className="h-2" />
              <p className="text-xs text-muted-foreground">
                {data.porcentaje_indexado}% completado
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Lista de actuaciones con analisis */}
      <Card>
        <CardHeader>
          <CardTitle>Detalle por Actuacion</CardTitle>
          <CardDescription>
            Clasificacion y estado de indexacion de cada actuacion
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {data.actuaciones.map((act) => (
              <ActuacionIAItem
                key={act.id}
                actuacion={act}
                isExpanded={expandedActuacion === act.indice}
                onToggle={() => toggleActuacion(act.indice)}
                getConfianzaColor={getConfianzaColor}
              />
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

interface ActuacionIAItemProps {
  actuacion: ActuacionConAnalisisIA
  isExpanded: boolean
  onToggle: () => void
  getConfianzaColor: (confianza: number | null) => string
}

function ActuacionIAItem({
  actuacion,
  isExpanded,
  onToggle,
  getConfianzaColor
}: ActuacionIAItemProps) {
  return (
    <div className="border rounded-lg">
      <button
        onClick={onToggle}
        className="w-full p-3 flex items-center justify-between hover:bg-muted/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          {isExpanded ? (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronRight className="h-4 w-4 text-muted-foreground" />
          )}
          <span className="font-medium text-sm">#{actuacion.indice}</span>
          <span className="text-sm text-muted-foreground truncate max-w-[200px]">
            {actuacion.tipo}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {/* Badge de clasificacion */}
          {actuacion.tipo_ia ? (
            <Badge variant="secondary" className={getConfianzaColor(actuacion.confianza_ia)}>
              {actuacion.tipo_ia}
            </Badge>
          ) : (
            <Badge variant="outline" className="text-muted-foreground">
              Sin clasificar
            </Badge>
          )}

          {/* Indicador de indexacion */}
          {actuacion.indexado_rag ? (
            <CheckCircle2 className="h-4 w-4 text-green-500" />
          ) : (
            <XCircle className="h-4 w-4 text-gray-300" />
          )}
        </div>
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 pt-2 border-t bg-muted/30">
          <div className="grid gap-3 text-sm">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-muted-foreground text-xs mb-1">Tipo original</p>
                <p className="font-medium">{actuacion.tipo}</p>
              </div>
              <div>
                <p className="text-muted-foreground text-xs mb-1">Fecha</p>
                <p className="font-medium">{actuacion.fecha || '-'}</p>
              </div>
            </div>

            {actuacion.detalle && (
              <div>
                <p className="text-muted-foreground text-xs mb-1">Detalle</p>
                <p className="text-sm">{actuacion.detalle}</p>
              </div>
            )}

            <div className="border-t pt-3 mt-2">
              <p className="text-muted-foreground text-xs mb-2 font-medium">Analisis IA</p>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-muted-foreground text-xs mb-1">Clasificacion IA</p>
                  <p className="font-medium">{actuacion.tipo_ia || '-'}</p>
                </div>
                <div>
                  <p className="text-muted-foreground text-xs mb-1">Confianza</p>
                  <p className="font-medium">
                    {actuacion.confianza_ia !== null
                      ? `${(actuacion.confianza_ia * 100).toFixed(0)}%`
                      : '-'}
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground text-xs mb-1">Metodo</p>
                  <p className="font-medium">{actuacion.metodo_ia || '-'}</p>
                </div>
                <div>
                  <p className="text-muted-foreground text-xs mb-1">Indexado RAG</p>
                  <p className="font-medium">
                    {actuacion.indexado_rag ? 'Si' : 'No'}
                  </p>
                </div>
              </div>

              {actuacion.justificacion_ia && (
                <div className="mt-3">
                  <p className="text-muted-foreground text-xs mb-1">Justificacion</p>
                  <p className="text-sm bg-muted p-2 rounded">
                    {actuacion.justificacion_ia}
                  </p>
                </div>
              )}

              {actuacion.fecha_clasificacion_ia && (
                <div className="mt-2">
                  <p className="text-muted-foreground text-xs">
                    Clasificado: {actuacion.fecha_clasificacion_ia}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default AnalisisIAPanel
