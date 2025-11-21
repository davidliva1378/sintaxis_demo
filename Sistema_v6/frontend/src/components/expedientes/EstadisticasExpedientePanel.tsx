import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  BarChart3,
  Clock,
  AlertTriangle,
  TrendingDown,
  FileText,
  Copy
} from 'lucide-react'
import type { EstadisticasExpediente } from '@/types/procesamiento'
import { formatearTiempoProcesamiento } from '@/api/procesamientoApi'

interface EstadisticasExpedientePanelProps {
  estadisticas: EstadisticasExpediente | null
  isLoading?: boolean
}

export default function EstadisticasExpedientePanel({
  estadisticas,
  isLoading = false
}: EstadisticasExpedientePanelProps) {
  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {[...Array(6)].map((_, i) => (
          <Card key={i}>
            <CardHeader className="pb-2">
              <Skeleton className="h-4 w-24" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16" />
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (!estadisticas) {
    return null
  }

  const total = estadisticas.total_actuaciones || 1
  const porcentajeAlta = (estadisticas.actuaciones_alta / total) * 100
  const porcentajeMedia = (estadisticas.actuaciones_media / total) * 100
  const porcentajeBaja = (estadisticas.actuaciones_baja / total) * 100
  const porcentajeNula = (estadisticas.actuaciones_nula / total) * 100

  return (
    <div className="space-y-6">
      {/* Resumen General */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Actuaciones
            </CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{estadisticas.total_actuaciones}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Reduccion Estimada
            </CardTitle>
            <TrendingDown className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {estadisticas.reduccion_estimada_pct.toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">
              de actuaciones de baja/nula utilidad
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Vencimientos
            </CardTitle>
            <AlertTriangle className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{estadisticas.vencimientos_detectados}</div>
            {estadisticas.vencimientos_urgentes > 0 && (
              <Badge variant="destructive" className="mt-1">
                {estadisticas.vencimientos_urgentes} urgentes
              </Badge>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Duplicados
            </CardTitle>
            <Copy className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{estadisticas.duplicados_detectados}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Tiempo de Procesamiento
            </CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatearTiempoProcesamiento(estadisticas.tiempo_procesamiento_seg)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Relevantes
            </CardTitle>
            <BarChart3 className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {estadisticas.actuaciones_alta + estadisticas.actuaciones_media}
            </div>
            <p className="text-xs text-muted-foreground">
              Alta + Media utilidad
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Desglose por Utilidad */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Clasificacion por Utilidad</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <div className="h-3 w-3 rounded-full bg-red-500" />
                <span>Alta Utilidad</span>
              </div>
              <span className="font-medium">
                {estadisticas.actuaciones_alta} ({porcentajeAlta.toFixed(1)}%)
              </span>
            </div>
            <Progress value={porcentajeAlta} className="h-2 bg-red-100" />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <div className="h-3 w-3 rounded-full bg-yellow-500" />
                <span>Media Utilidad</span>
              </div>
              <span className="font-medium">
                {estadisticas.actuaciones_media} ({porcentajeMedia.toFixed(1)}%)
              </span>
            </div>
            <Progress value={porcentajeMedia} className="h-2 bg-yellow-100" />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <div className="h-3 w-3 rounded-full bg-blue-500" />
                <span>Baja Utilidad</span>
              </div>
              <span className="font-medium">
                {estadisticas.actuaciones_baja} ({porcentajeBaja.toFixed(1)}%)
              </span>
            </div>
            <Progress value={porcentajeBaja} className="h-2 bg-blue-100" />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <div className="h-3 w-3 rounded-full bg-gray-400" />
                <span>Sin Utilidad</span>
              </div>
              <span className="font-medium">
                {estadisticas.actuaciones_nula} ({porcentajeNula.toFixed(1)}%)
              </span>
            </div>
            <Progress value={porcentajeNula} className="h-2 bg-gray-200" />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
