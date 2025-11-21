import { useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ChevronDown, ChevronUp, FileText, AlertTriangle, Calendar } from 'lucide-react'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'
import type { ActuacionPorUtilidad, UtilidadJuridica } from '@/types/procesamiento'
import {
  COLORES_UTILIDAD,
  LABELS_UTILIDAD,
  COLORES_URGENCIA,
  formatDiasRestantes,
  getNivelUrgencia
} from '@/types/procesamiento'

interface ActuacionesClasificadasListProps {
  actuaciones: ActuacionPorUtilidad[]
  isLoading?: boolean
}

export default function ActuacionesClasificadasList({
  actuaciones,
  isLoading = false
}: ActuacionesClasificadasListProps) {
  const [filtroUtilidad, setFiltroUtilidad] = useState<UtilidadJuridica | 'todas'>('todas')
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set())

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <Card key={i}>
            <CardContent className="py-4">
              <Skeleton className="h-16 w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (actuaciones.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Sin actuaciones clasificadas
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Procesa el expediente para ver la clasificacion de actuaciones
          </p>
        </CardContent>
      </Card>
    )
  }

  // Filtrar actuaciones
  const actuacionesFiltradas = filtroUtilidad === 'todas'
    ? actuaciones
    : actuaciones.filter(a => a.utilidad === filtroUtilidad)

  // Ordenar por utilidad (alta primero) y score
  const actuacionesOrdenadas = [...actuacionesFiltradas].sort((a, b) => {
    const ordenUtilidad: Record<UtilidadJuridica, number> = {
      alta: 4,
      media: 3,
      baja: 2,
      nula: 1
    }
    const diff = ordenUtilidad[b.utilidad] - ordenUtilidad[a.utilidad]
    if (diff !== 0) return diff
    return b.score - a.score
  })

  const toggleExpand = (id: number) => {
    setExpandedIds(prev => {
      const newSet = new Set(prev)
      if (newSet.has(id)) {
        newSet.delete(id)
      } else {
        newSet.add(id)
      }
      return newSet
    })
  }

  // Contadores por utilidad
  const contadores = {
    todas: actuaciones.length,
    alta: actuaciones.filter(a => a.utilidad === 'alta').length,
    media: actuaciones.filter(a => a.utilidad === 'media').length,
    baja: actuaciones.filter(a => a.utilidad === 'baja').length,
    nula: actuaciones.filter(a => a.utilidad === 'nula').length,
  }

  return (
    <div className="space-y-4">
      {/* Filtros */}
      <div className="flex items-center justify-between">
        <Select
          value={filtroUtilidad}
          onValueChange={(value) => setFiltroUtilidad(value as UtilidadJuridica | 'todas')}
        >
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="Filtrar por utilidad" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="todas">Todas ({contadores.todas})</SelectItem>
            <SelectItem value="alta">Alta ({contadores.alta})</SelectItem>
            <SelectItem value="media">Media ({contadores.media})</SelectItem>
            <SelectItem value="baja">Baja ({contadores.baja})</SelectItem>
            <SelectItem value="nula">Nula ({contadores.nula})</SelectItem>
          </SelectContent>
        </Select>

        <span className="text-sm text-muted-foreground">
          {actuacionesFiltradas.length} actuaciones
        </span>
      </div>

      {/* Lista de actuaciones */}
      <div className="space-y-3">
        {actuacionesOrdenadas.map((actuacion) => {
          const isExpanded = expandedIds.has(actuacion.id)
          const nivelUrgencia = actuacion.dias_restantes !== undefined
            ? getNivelUrgencia(actuacion.dias_restantes)
            : undefined

          return (
            <Card key={actuacion.id} className="overflow-hidden">
              <div className={`h-1 ${COLORES_UTILIDAD[actuacion.utilidad]}`} />
              <CardContent className="py-4">
                <div className="space-y-3">
                  {/* Header */}
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge className={COLORES_UTILIDAD[actuacion.utilidad]}>
                          {LABELS_UTILIDAD[actuacion.utilidad]}
                        </Badge>
                        <span className="text-sm font-medium">{actuacion.tipo}</span>
                        {actuacion.tiene_vencimiento && nivelUrgencia && (
                          <Badge className={COLORES_URGENCIA[nivelUrgencia]} variant="outline">
                            <AlertTriangle className="h-3 w-3 mr-1" />
                            {formatDiasRestantes(actuacion.dias_restantes!)}
                          </Badge>
                        )}
                      </div>

                      <p className={`text-sm text-gray-600 dark:text-gray-400 ${isExpanded ? '' : 'line-clamp-2'}`}>
                        {actuacion.detalle}
                      </p>
                    </div>

                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => toggleExpand(actuacion.id)}
                      className="shrink-0"
                    >
                      {isExpanded ? (
                        <ChevronUp className="h-4 w-4" />
                      ) : (
                        <ChevronDown className="h-4 w-4" />
                      )}
                    </Button>
                  </div>

                  {/* Expanded content */}
                  {isExpanded && (
                    <div className="pt-3 border-t space-y-2">
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span>ID: {actuacion.id}</span>
                        <span>Score: {actuacion.score.toFixed(0)}</span>
                        {actuacion.fecha_vencimiento && (
                          <span className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            Vence: {format(new Date(actuacion.fecha_vencimiento), "dd/MM/yyyy", { locale: es })}
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
