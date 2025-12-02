/**
 * VencimientosWidget - Widget de vencimientos urgentes para el Dashboard.
 *
 * Muestra los vencimientos mas urgentes con indicadores visuales de urgencia.
 */

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { AlertTriangle, Clock, Calendar, ExternalLink } from 'lucide-react'
import {
  getVencimientosUrgentes,
  VencimientosUrgentes,
  getUrgenciaColor,
} from '@/api/dashboardApi'
import type { NivelUrgencia } from '@/types/vencimiento'

interface VencimientosWidgetProps {
  className?: string
  limite?: number
  onError?: (error: Error) => void
}

const urgenciaLabels: Record<NivelUrgencia, string> = {
  vencido: 'Vencido',
  critico: 'Critico',
  urgente: 'Urgente',
  proximo: 'Proximo',
  normal: 'Normal',
}

const urgenciaIcons: Record<NivelUrgencia, React.ComponentType<{ className?: string }>> = {
  vencido: AlertTriangle,
  critico: AlertTriangle,
  urgente: Clock,
  proximo: Calendar,
  normal: Calendar,
}

export default function VencimientosWidget({
  className = '',
  limite = 5,
  onError,
}: VencimientosWidgetProps) {
  const [data, setData] = useState<VencimientosUrgentes | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchVencimientos() {
      try {
        setLoading(true)
        setError(null)
        const result = await getVencimientosUrgentes(limite)
        setData(result)
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Error al cargar vencimientos'
        setError(errorMsg)
        onError?.(err instanceof Error ? err : new Error(errorMsg))
      } finally {
        setLoading(false)
      }
    }

    fetchVencimientos()

    // Refrescar cada 5 minutos
    const interval = setInterval(fetchVencimientos, 300000)
    return () => clearInterval(interval)
  }, [limite, onError])

  const formatFecha = (fechaStr: string): string => {
    const fecha = new Date(fechaStr)
    return fecha.toLocaleDateString('es-AR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    })
  }

  const formatDiasRestantes = (dias: number): string => {
    if (dias < 0) return `Hace ${Math.abs(dias)} dias`
    if (dias === 0) return 'Hoy'
    if (dias === 1) return 'Manana'
    return `En ${dias} dias`
  }

  if (loading) {
    return (
      <Card className={className}>
        <CardHeader>
          <Skeleton className="h-5 w-40" />
          <Skeleton className="h-4 w-60" />
        </CardHeader>
        <CardContent className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-800">
              <Skeleton className="h-8 w-8 rounded" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-3 w-full" />
              </div>
              <Skeleton className="h-5 w-16" />
            </div>
          ))}
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className={`border-red-200 ${className}`}>
        <CardHeader>
          <CardTitle className="text-red-600">Error</CardTitle>
          <CardDescription>{error}</CardDescription>
        </CardHeader>
      </Card>
    )
  }

  const vencimientos = data?.vencimientos || []

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-orange-500" />
              Vencimientos Urgentes
            </CardTitle>
            <CardDescription>
              {vencimientos.length > 0
                ? `${vencimientos.length} vencimientos requieren atencion`
                : 'No hay vencimientos urgentes'}
            </CardDescription>
          </div>
          {vencimientos.length > 0 && (
            <Badge variant="secondary">{data?.total || 0} total</Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {vencimientos.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Calendar className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>Sin vencimientos urgentes</p>
          </div>
        ) : (
          <div className="space-y-3">
            {vencimientos.map((venc) => {
              const Icon = urgenciaIcons[venc.nivel_urgencia]
              const colorClasses = getUrgenciaColor(venc.nivel_urgencia)

              return (
                <div
                  key={venc.id}
                  className={`flex items-start gap-3 p-3 rounded-lg border ${
                    venc.nivel_urgencia === 'vencido'
                      ? 'border-red-200 bg-red-50 dark:bg-red-900/20'
                      : venc.nivel_urgencia === 'critico'
                      ? 'border-orange-200 bg-orange-50 dark:bg-orange-900/20'
                      : 'border-gray-200 bg-gray-50 dark:bg-gray-800'
                  }`}
                >
                  <div className={`rounded-lg p-2 ${colorClasses}`}>
                    <Icon className="h-4 w-4" />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm truncate">
                        {venc.expediente_numero}
                      </span>
                      <a
                        href={`/expedientes/${encodeURIComponent(venc.expediente_numero)}`}
                        className="text-blue-600 hover:text-blue-800"
                        title="Ver expediente"
                      >
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    </div>
                    <p className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">
                      {venc.tipo}: {venc.descripcion}
                    </p>
                    <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
                      <Calendar className="h-3 w-3" />
                      <span>{formatFecha(venc.fecha_vencimiento)}</span>
                      <span className="text-gray-400">|</span>
                      <span className={venc.dias_restantes < 0 ? 'text-red-600 font-medium' : ''}>
                        {formatDiasRestantes(venc.dias_restantes)}
                      </span>
                    </div>
                  </div>

                  <Badge className={colorClasses} variant="outline">
                    {urgenciaLabels[venc.nivel_urgencia]}
                  </Badge>
                </div>
              )
            })}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
