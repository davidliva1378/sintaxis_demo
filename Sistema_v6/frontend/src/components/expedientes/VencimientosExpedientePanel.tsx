import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu'
import { AlertTriangle, Calendar, Clock, Check, X, MoreVertical, Loader2, Trash2 } from 'lucide-react'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'
import type { VencimientoUrgente, NivelUrgencia } from '@/types/procesamiento'
import { COLORES_URGENCIA, LABELS_URGENCIA, formatDiasRestantes } from '@/types/procesamiento'
import { useVencimientosStore } from '@/stores/vencimientosStore'
import { toast } from 'sonner'

interface VencimientosExpedientePanelProps {
  vencimientos: VencimientoUrgente[]
  isLoading?: boolean
  onVencimientoActualizado?: () => void
}

export default function VencimientosExpedientePanel({
  vencimientos,
  isLoading = false,
  onVencimientoActualizado
}: VencimientosExpedientePanelProps) {
  const [procesandoId, setProcesandoId] = useState<number | null>(null)
  const { atenderVencimiento, cancelarVencimiento, eliminarVencimiento } = useVencimientosStore()

  const handleAtender = async (id: number) => {
    setProcesandoId(id)
    try {
      await atenderVencimiento(id)
      onVencimientoActualizado?.()
    } catch (error) {
      // El store ya muestra el toast de error
    } finally {
      setProcesandoId(null)
    }
  }

  const handleCancelar = async (id: number) => {
    setProcesandoId(id)
    try {
      await cancelarVencimiento(id)
      onVencimientoActualizado?.()
    } catch (error) {
      // El store ya muestra el toast de error
    } finally {
      setProcesandoId(null)
    }
  }

  const handleEliminar = async (id: number) => {
    if (!confirm('¿Está seguro de eliminar este vencimiento? Esta acción no se puede deshacer.')) return
    setProcesandoId(id)
    try {
      await eliminarVencimiento(id)
      onVencimientoActualizado?.()
    } catch (error) {
      // El store ya muestra el toast de error
    } finally {
      setProcesandoId(null)
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[...Array(3)].map((_, i) => (
          <Card key={i}>
            <CardContent className="py-4">
              <Skeleton className="h-16 w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (vencimientos.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <Calendar className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Sin vencimientos
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            No se detectaron plazos o vencimientos en las actuaciones de este expediente
          </p>
        </CardContent>
      </Card>
    )
  }

  // Ordenar por dias restantes (mas urgentes primero)
  const vencimientosOrdenados = [...vencimientos].sort((a, b) => a.dias_restantes - b.dias_restantes)

  const formatFecha = (fecha: string) => {
    try {
      return format(new Date(fecha), "dd 'de' MMMM 'de' yyyy", { locale: es })
    } catch {
      return fecha
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">
          {vencimientos.length} {vencimientos.length === 1 ? 'Vencimiento' : 'Vencimientos'} Detectados
        </h3>
        {vencimientos.some(v => v.dias_restantes <= 3) && (
          <Badge variant="destructive" className="flex items-center gap-1">
            <AlertTriangle className="h-3 w-3" />
            Urgentes
          </Badge>
        )}
      </div>

      <div className="space-y-3">
        {vencimientosOrdenados.map((vencimiento) => (
          <Card key={vencimiento.id} className="overflow-hidden">
            <div className={`h-1 ${getBgColorUrgencia(vencimiento.nivel_urgencia)}`} />
            <CardContent className="py-4">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-2">
                    <Badge className={getColorUrgencia(vencimiento.nivel_urgencia)}>
                      {LABELS_URGENCIA[vencimiento.nivel_urgencia]}
                    </Badge>
                    <span className="text-sm text-muted-foreground">
                      {vencimiento.tipo}
                    </span>
                  </div>

                  <p className="text-sm font-medium line-clamp-2">
                    {vencimiento.actuacion_detalle || vencimiento.descripcion}
                  </p>

                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      {formatFecha(vencimiento.fecha_vencimiento)}
                    </div>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="text-right">
                    <div className={`text-2xl font-bold ${getTextColorUrgencia(vencimiento.nivel_urgencia)}`}>
                      {formatDiasRestantes(vencimiento.dias_restantes)}
                    </div>
                    <p className="text-xs text-muted-foreground">restantes</p>
                  </div>

                  {/* Menu de acciones */}
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8"
                        disabled={procesandoId === vencimiento.id}
                      >
                        {procesandoId === vencimiento.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <MoreVertical className="h-4 w-4" />
                        )}
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem
                        onClick={() => handleAtender(vencimiento.id)}
                        className="text-green-600"
                      >
                        <Check className="h-4 w-4 mr-2" />
                        Marcar como atendido
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => handleCancelar(vencimiento.id)}
                        className="text-orange-600"
                      >
                        <X className="h-4 w-4 mr-2" />
                        Cancelar vencimiento
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        onClick={() => handleEliminar(vencimiento.id)}
                        className="text-red-600"
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Eliminar
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}

function getBgColorUrgencia(nivel: NivelUrgencia): string {
  const colors: Record<NivelUrgencia, string> = {
    vencido: 'bg-black',
    critico: 'bg-red-600',
    urgente: 'bg-orange-500',
    proximo: 'bg-yellow-400',
    normal: 'bg-green-500'
  }
  return colors[nivel] || 'bg-gray-400'
}

function getColorUrgencia(nivel: NivelUrgencia): string {
  return COLORES_URGENCIA[nivel] || 'bg-gray-400'
}

function getTextColorUrgencia(nivel: NivelUrgencia): string {
  const colors: Record<NivelUrgencia, string> = {
    vencido: 'text-black',
    critico: 'text-red-600',
    urgente: 'text-orange-500',
    proximo: 'text-yellow-600',
    normal: 'text-green-500'
  }
  return colors[nivel] || 'text-gray-600'
}
