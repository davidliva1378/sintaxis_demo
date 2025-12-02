import { useState, useEffect, useMemo, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useVirtualizer } from '@tanstack/react-virtual'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu'
import {
  Calendar,
  Clock,
  AlertTriangle,
  Search,
  Filter,
  RefreshCw,
  ExternalLink,
  ChevronRight,
  XCircle,
  AlertOctagon,
  Timer,
  CalendarClock,
  ChevronDown,
  Loader2,
  MoreVertical,
  Trash2,
  CheckCircle,
  Ban
} from 'lucide-react'
import { format, formatDistanceToNow } from 'date-fns'
import { es } from 'date-fns/locale'
import { toast } from 'sonner'
import { vencimientosApi, FILTROS_TEMPORALES, type FiltroTemporalKey, type VencimientoGlobal, type EstadisticasVencimientos } from '@/api/vencimientosApi'
import type { NivelUrgencia } from '@/types/vencimiento'
import { COLORES_URGENCIA, LABELS_URGENCIA, formatDiasRestantes } from '@/types/vencimiento'

// Constantes para paginacion
const ITEMS_PER_PAGE = 50
const CARD_HEIGHT = 140 // Altura estimada de cada tarjeta

/**
 * Normaliza número de expediente al formato usado en la BD de expedientes.
 * Convierte "FRE 004409/2021" a "FRE_004409_2021"
 */
function normalizarExpedienteNumero(numero: string): string {
  return numero
    .replace(/\s+/g, '_')  // Espacios a guiones bajos
    .replace(/\//g, '_')   // Barras a guiones bajos
}

export default function VencimientosPage() {
  const navigate = useNavigate()
  const [vencimientos, setVencimientos] = useState<VencimientoGlobal[]>([])
  const [stats, setStats] = useState<EstadisticasVencimientos | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isLoadingMore, setIsLoadingMore] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hasMore, setHasMore] = useState(true)
  const [offset, setOffset] = useState(0)
  const [total, setTotal] = useState(0)

  // Filtros
  const [filtroTemporal, setFiltroTemporal] = useState<FiltroTemporalKey>('PROXIMOS_7_DIAS')
  const [ocultarVencidos, setOcultarVencidos] = useState(false)
  const [busqueda, setBusqueda] = useState('')
  const [nivelUrgencia, setNivelUrgencia] = useState<NivelUrgencia | 'todos'>('todos')

  // Ref para scroll container
  const parentRef = useRef<HTMLDivElement>(null)

  // Cargar datos iniciales (resetea paginacion)
  const cargarDatos = async () => {
    setIsLoading(true)
    setError(null)
    setOffset(0)
    setHasMore(true)
    try {
      const filtro = FILTROS_TEMPORALES[filtroTemporal]
      const [vencResponse, statsResponse] = await Promise.all([
        vencimientosApi.getVencimientos({
          dias_desde: filtro.dias_desde,
          dias_hasta: filtro.dias_hasta,
          ocultarVencidos,
          nivel_urgencia: nivelUrgencia,
          expediente: busqueda || undefined,
          limite: ITEMS_PER_PAGE,
          offset: 0
        }),
        vencimientosApi.getEstadisticas()
      ])
      setVencimientos(vencResponse.vencimientos)
      setTotal(vencResponse.total || vencResponse.vencimientos.length)
      setHasMore(vencResponse.vencimientos.length >= ITEMS_PER_PAGE)
      setStats(statsResponse)
    } catch (err) {
      console.error('Error cargando vencimientos:', err)
      setError('Error al cargar vencimientos')
      toast.error('Error al cargar vencimientos')
    } finally {
      setIsLoading(false)
    }
  }

  // Cargar mas (infinite scroll)
  const cargarMas = useCallback(async () => {
    if (isLoadingMore || !hasMore) return

    setIsLoadingMore(true)
    try {
      const filtro = FILTROS_TEMPORALES[filtroTemporal]
      const newOffset = offset + ITEMS_PER_PAGE

      const vencResponse = await vencimientosApi.getVencimientos({
        dias_desde: filtro.dias_desde,
        dias_hasta: filtro.dias_hasta,
        ocultarVencidos,
        nivel_urgencia: nivelUrgencia,
        expediente: busqueda || undefined,
        limite: ITEMS_PER_PAGE,
        offset: newOffset
      })

      setVencimientos(prev => [...prev, ...vencResponse.vencimientos])
      setOffset(newOffset)
      setHasMore(vencResponse.vencimientos.length >= ITEMS_PER_PAGE)
    } catch (err) {
      console.error('Error cargando mas vencimientos:', err)
      toast.error('Error al cargar mas vencimientos')
    } finally {
      setIsLoadingMore(false)
    }
  }, [isLoadingMore, hasMore, offset, filtroTemporal, ocultarVencidos, nivelUrgencia, busqueda])

  useEffect(() => {
    cargarDatos()
  }, [filtroTemporal, ocultarVencidos, nivelUrgencia])

  // Debounce para busqueda
  useEffect(() => {
    const timer = setTimeout(() => {
      if (busqueda !== '') cargarDatos()
    }, 300)
    return () => clearTimeout(timer)
  }, [busqueda])

  // Filtro de búsqueda local
  const vencimientosFiltrados = useMemo(() => {
    if (!busqueda.trim()) return vencimientos
    const q = busqueda.toLowerCase()
    return vencimientos.filter(v =>
      v.expediente_numero.toLowerCase().includes(q) ||
      v.tipo?.toLowerCase().includes(q) ||
      v.descripcion?.toLowerCase().includes(q) ||
      v.actuacion_detalle?.toLowerCase().includes(q)
    )
  }, [vencimientos, busqueda])

  // Agrupar por nivel de urgencia
  const vencimientosAgrupados = useMemo(() => {
    const grupos: Record<string, VencimientoGlobal[]> = {
      vencido: [],
      critico: [],
      urgente: [],
      proximo: [],
      normal: []
    }
    vencimientosFiltrados.forEach(v => {
      const nivel = v.nivel_urgencia || 'normal'
      if (grupos[nivel]) {
        grupos[nivel].push(v)
      }
    })
    return grupos
  }, [vencimientosFiltrados])

  const formatFecha = (fecha: string) => {
    try {
      return format(new Date(fecha), "dd/MM/yyyy", { locale: es })
    } catch {
      return fecha
    }
  }

  const getIconoUrgencia = (nivel: NivelUrgencia) => {
    switch (nivel) {
      case 'vencido': return <XCircle className="h-4 w-4" />
      case 'critico': return <AlertOctagon className="h-4 w-4" />
      case 'urgente': return <AlertTriangle className="h-4 w-4" />
      case 'proximo': return <Timer className="h-4 w-4" />
      default: return <CalendarClock className="h-4 w-4" />
    }
  }

  const getBgColorUrgencia = (nivel: NivelUrgencia): string => {
    const colors: Record<NivelUrgencia, string> = {
      vencido: 'bg-black',
      critico: 'bg-red-600',
      urgente: 'bg-orange-500',
      proximo: 'bg-yellow-400',
      normal: 'bg-green-500'
    }
    return colors[nivel] || 'bg-gray-400'
  }

  const getTextColorUrgencia = (nivel: NivelUrgencia): string => {
    const colors: Record<NivelUrgencia, string> = {
      vencido: 'text-black dark:text-gray-300',
      critico: 'text-red-600',
      urgente: 'text-orange-500',
      proximo: 'text-yellow-600',
      normal: 'text-green-500'
    }
    return colors[nivel] || 'text-gray-600'
  }

  // Stats Cards
  const StatsCards = () => (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
      <Card className={stats?.vencidos ? 'border-black bg-black/5' : ''}>
        <CardContent className="p-4">
          <div className="flex items-center gap-2">
            <XCircle className="h-5 w-5 text-black" />
            <div>
              <p className="text-2xl font-bold">{stats?.vencidos || 0}</p>
              <p className="text-xs text-muted-foreground">Vencidos</p>
            </div>
          </div>
        </CardContent>
      </Card>
      <Card className={stats?.criticos ? 'border-red-600 bg-red-50' : ''}>
        <CardContent className="p-4">
          <div className="flex items-center gap-2">
            <AlertOctagon className="h-5 w-5 text-red-600" />
            <div>
              <p className="text-2xl font-bold">{stats?.criticos || 0}</p>
              <p className="text-xs text-muted-foreground">Criticos</p>
            </div>
          </div>
        </CardContent>
      </Card>
      <Card className={stats?.urgentes ? 'border-orange-500 bg-orange-50' : ''}>
        <CardContent className="p-4">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-orange-500" />
            <div>
              <p className="text-2xl font-bold">{stats?.urgentes || 0}</p>
              <p className="text-xs text-muted-foreground">Urgentes</p>
            </div>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-2">
            <Timer className="h-5 w-5 text-yellow-600" />
            <div>
              <p className="text-2xl font-bold">{stats?.proximos || 0}</p>
              <p className="text-xs text-muted-foreground">Proximos</p>
            </div>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-2">
            <Calendar className="h-5 w-5 text-green-500" />
            <div>
              <p className="text-2xl font-bold">{stats?.total || 0}</p>
              <p className="text-xs text-muted-foreground">Total</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  // Handlers para acciones de vencimientos
  const handleEliminarVencimiento = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirm('¿Está seguro de eliminar este vencimiento?')) return
    try {
      await vencimientosApi.eliminarVencimiento(id)
      toast.success('Vencimiento eliminado')
      // Remover de la lista local
      setVencimientos(prev => prev.filter(v => v.id !== id))
    } catch (err) {
      console.error('Error eliminando vencimiento:', err)
      toast.error('Error al eliminar vencimiento')
    }
  }

  const handleAtenderVencimiento = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await vencimientosApi.atenderVencimiento(id)
      toast.success('Vencimiento marcado como atendido')
      // Remover de la lista local (ya no está pendiente)
      setVencimientos(prev => prev.filter(v => v.id !== id))
    } catch (err) {
      console.error('Error atendiendo vencimiento:', err)
      toast.error('Error al marcar como atendido')
    }
  }

  const handleCancelarVencimiento = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await vencimientosApi.cancelarVencimiento(id)
      toast.success('Vencimiento cancelado')
      // Remover de la lista local
      setVencimientos(prev => prev.filter(v => v.id !== id))
    } catch (err) {
      console.error('Error cancelando vencimiento:', err)
      toast.error('Error al cancelar vencimiento')
    }
  }

  // Vencimiento Card - Mejorada con caratula y acciones
  const VencimientoCard = ({ vencimiento }: { vencimiento: VencimientoGlobal }) => (
    <Card
      className="cursor-pointer hover:shadow-md transition-shadow overflow-hidden group"
      onClick={() => navigate(`/expedientes/${encodeURIComponent(normalizarExpedienteNumero(vencimiento.expediente_numero))}`)}
    >
      <div className={`h-1.5 ${getBgColorUrgencia(vencimiento.nivel_urgencia)}`} />
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            {/* Header: Badge urgencia + tipo */}
            <div className="flex items-center gap-2 mb-2">
              <Badge className={`${COLORES_URGENCIA[vencimiento.nivel_urgencia]} text-xs`}>
                {getIconoUrgencia(vencimiento.nivel_urgencia)}
                <span className="ml-1">{LABELS_URGENCIA[vencimiento.nivel_urgencia]}</span>
              </Badge>
              <Badge variant="outline" className="text-xs">
                {vencimiento.tipo?.replace(/_/g, ' ')}
              </Badge>
            </div>

            {/* Numero de expediente */}
            <p className="font-semibold text-primary hover:underline text-sm">
              {vencimiento.expediente_numero}
            </p>

            {/* Caratula - destacada */}
            {(vencimiento as any).caratula && (
              <p className="text-sm font-medium text-foreground mt-1 line-clamp-2">
                {(vencimiento as any).caratula}
              </p>
            )}

            {/* Descripcion del vencimiento */}
            <p className="text-xs text-muted-foreground mt-1 line-clamp-1">
              {vencimiento.descripcion || 'Sin descripcion'}
            </p>

            {/* Footer: Fecha + Dependencia */}
            <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
              <div className="flex items-center gap-1">
                <Calendar className="h-3 w-3" />
                <span>Vence: {formatFecha(vencimiento.fecha_vencimiento)}</span>
              </div>
              {(vencimiento as any).dependencia && (
                <span className="truncate max-w-[150px]" title={(vencimiento as any).dependencia}>
                  {(vencimiento as any).dependencia.split(' - ')[0]}
                </span>
              )}
            </div>
          </div>

          {/* Columna derecha: Menu + Dias restantes */}
          <div className="flex flex-col items-end gap-1">
            {/* Menú de acciones - visible en hover o siempre */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 w-7 p-0 opacity-60 hover:opacity-100 group-hover:opacity-100"
                >
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem
                  onClick={(e) => handleAtenderVencimiento(vencimiento.id, e as any)}
                  className="text-green-600"
                >
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Marcar atendido
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={(e) => handleCancelarVencimiento(vencimiento.id, e as any)}
                  className="text-orange-600"
                >
                  <Ban className="h-4 w-4 mr-2" />
                  Cancelar
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={(e) => handleEliminarVencimiento(vencimiento.id, e as any)}
                  className="text-red-600"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Eliminar
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            {/* Dias restantes */}
            <div className="text-right">
              <div className={`text-2xl font-bold ${getTextColorUrgencia(vencimiento.nivel_urgencia)}`}>
                {vencimiento.dias_restantes < 0
                  ? Math.abs(vencimiento.dias_restantes)
                  : vencimiento.dias_restantes}
              </div>
              <p className="text-xs text-muted-foreground">
                {vencimiento.dias_restantes < 0 ? 'dias vencido' : 'dias'}
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )

  // Grupo de vencimientos
  const GrupoVencimientos = ({ nivel, vencimientos }: { nivel: string, vencimientos: VencimientoGlobal[] }) => {
    if (vencimientos.length === 0) return null

    const labelNivel = LABELS_URGENCIA[nivel as NivelUrgencia] || nivel
    const colorNivel = getTextColorUrgencia(nivel as NivelUrgencia)

    return (
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-3">
          {getIconoUrgencia(nivel as NivelUrgencia)}
          <h3 className={`font-semibold ${colorNivel}`}>
            {labelNivel} ({vencimientos.length})
          </h3>
        </div>
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {vencimientos.map((v, i) => (
            <VencimientoCard key={`${v.expediente_numero}-${v.id}-${i}`} vencimiento={v} />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Clock className="h-6 w-6" />
            Vencimientos
          </h1>
          <p className="text-muted-foreground">
            Control de plazos y vencimientos de todos los expedientes
          </p>
        </div>
        <Button variant="outline" onClick={cargarDatos} disabled={isLoading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          Actualizar
        </Button>
      </div>

      {/* Stats */}
      {!isLoading && stats && <StatsCards />}

      {/* Filtros */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-4">
            {/* Filtro temporal */}
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <Select
                value={filtroTemporal}
                onValueChange={(v) => setFiltroTemporal(v as FiltroTemporalKey)}
              >
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="Rango temporal" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(FILTROS_TEMPORALES).map(([key, value]) => (
                    <SelectItem key={key} value={key}>
                      {value.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Filtro por urgencia */}
            <Select
              value={nivelUrgencia}
              onValueChange={(v) => setNivelUrgencia(v as NivelUrgencia | 'todos')}
            >
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="Urgencia" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="todos">Todas</SelectItem>
                <SelectItem value="vencido">Vencidos</SelectItem>
                <SelectItem value="critico">Criticos</SelectItem>
                <SelectItem value="urgente">Urgentes</SelectItem>
                <SelectItem value="proximo">Proximos</SelectItem>
                <SelectItem value="normal">Normales</SelectItem>
              </SelectContent>
            </Select>

            {/* Toggle ocultar vencidos */}
            <div className="flex items-center gap-2">
              <Switch
                id="ocultar-vencidos"
                checked={ocultarVencidos}
                onCheckedChange={setOcultarVencidos}
              />
              <Label htmlFor="ocultar-vencidos" className="text-sm">
                Ocultar vencidos
              </Label>
            </div>

            {/* Busqueda */}
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Buscar expediente..."
                  value={busqueda}
                  onChange={(e) => setBusqueda(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Loading */}
      {isLoading && (
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <Card key={i}>
              <CardContent className="p-4">
                <Skeleton className="h-24 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Error */}
      {error && (
        <Card className="border-red-500 bg-red-50">
          <CardContent className="p-6 text-center">
            <AlertTriangle className="h-8 w-8 text-red-500 mx-auto mb-2" />
            <p className="text-red-700">{error}</p>
            <Button variant="outline" className="mt-4" onClick={cargarDatos}>
              Reintentar
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Sin resultados */}
      {!isLoading && !error && vencimientosFiltrados.length === 0 && (
        <Card>
          <CardContent className="p-12 text-center">
            <Calendar className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Sin vencimientos
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              No se encontraron vencimientos con los filtros seleccionados
            </p>
          </CardContent>
        </Card>
      )}

      {/* Lista de vencimientos agrupados */}
      {!isLoading && !error && vencimientosFiltrados.length > 0 && (
        <div>
          {/* Info de paginacion */}
          <div className="flex items-center justify-between mb-4 text-sm text-muted-foreground">
            <span>
              Mostrando {vencimientosFiltrados.length} de {total > 0 ? total : vencimientosFiltrados.length} vencimientos
            </span>
            {hasMore && (
              <span className="text-xs">
                Scroll o click en "Cargar mas" para ver mas resultados
              </span>
            )}
          </div>

          {/* Mostrar por grupos en orden de urgencia */}
          <GrupoVencimientos nivel="vencido" vencimientos={vencimientosAgrupados.vencido} />
          <GrupoVencimientos nivel="critico" vencimientos={vencimientosAgrupados.critico} />
          <GrupoVencimientos nivel="urgente" vencimientos={vencimientosAgrupados.urgente} />
          <GrupoVencimientos nivel="proximo" vencimientos={vencimientosAgrupados.proximo} />
          <GrupoVencimientos nivel="normal" vencimientos={vencimientosAgrupados.normal} />

          {/* Cargar mas */}
          {hasMore && (
            <div className="flex justify-center mt-6 mb-4">
              <Button
                variant="outline"
                onClick={cargarMas}
                disabled={isLoadingMore}
                className="gap-2"
              >
                {isLoadingMore ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Cargando...
                  </>
                ) : (
                  <>
                    <ChevronDown className="h-4 w-4" />
                    Cargar mas vencimientos
                  </>
                )}
              </Button>
            </div>
          )}

          {/* Mensaje fin de lista */}
          {!hasMore && vencimientosFiltrados.length > ITEMS_PER_PAGE && (
            <div className="text-center text-sm text-muted-foreground py-4 border-t mt-4">
              Has visto todos los {vencimientosFiltrados.length} vencimientos
            </div>
          )}
        </div>
      )}
    </div>
  )
}
