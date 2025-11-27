import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
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
  CalendarClock
} from 'lucide-react'
import { format, formatDistanceToNow } from 'date-fns'
import { es } from 'date-fns/locale'
import { toast } from 'sonner'
import { vencimientosApi, FILTROS_TEMPORALES, type FiltroTemporalKey, type VencimientoGlobal, type EstadisticasVencimientos } from '@/api/vencimientosApi'
import { NivelUrgencia, COLORES_URGENCIA, LABELS_URGENCIA, formatDiasRestantes } from '@/types/procesamiento'

export default function VencimientosPage() {
  const navigate = useNavigate()
  const [vencimientos, setVencimientos] = useState<VencimientoGlobal[]>([])
  const [stats, setStats] = useState<EstadisticasVencimientos | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filtros
  const [filtroTemporal, setFiltroTemporal] = useState<FiltroTemporalKey>('PROXIMOS_7_DIAS')
  const [ocultarVencidos, setOcultarVencidos] = useState(false)
  const [busqueda, setBusqueda] = useState('')
  const [nivelUrgencia, setNivelUrgencia] = useState<NivelUrgencia | 'todos'>('todos')

  // Cargar datos
  const cargarDatos = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const filtro = FILTROS_TEMPORALES[filtroTemporal]
      const [vencResponse, statsResponse] = await Promise.all([
        vencimientosApi.getVencimientos({
          dias_desde: filtro.dias_desde,
          dias_hasta: filtro.dias_hasta,
          ocultarVencidos,
          nivel_urgencia: nivelUrgencia,
          expediente: busqueda || undefined,
          limite: 200
        }),
        vencimientosApi.getEstadisticas()
      ])
      setVencimientos(vencResponse.vencimientos)
      setStats(statsResponse)
    } catch (err) {
      console.error('Error cargando vencimientos:', err)
      setError('Error al cargar vencimientos')
      toast.error('Error al cargar vencimientos')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    cargarDatos()
  }, [filtroTemporal, ocultarVencidos, nivelUrgencia])

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

  // Vencimiento Card
  const VencimientoCard = ({ vencimiento }: { vencimiento: VencimientoGlobal }) => (
    <Card
      className="cursor-pointer hover:shadow-md transition-shadow overflow-hidden"
      onClick={() => navigate(`/expedientes/${encodeURIComponent(vencimiento.expediente_numero)}`)}
    >
      <div className={`h-1 ${getBgColorUrgencia(vencimiento.nivel_urgencia)}`} />
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <Badge className={COLORES_URGENCIA[vencimiento.nivel_urgencia]}>
                {getIconoUrgencia(vencimiento.nivel_urgencia)}
                <span className="ml-1">{LABELS_URGENCIA[vencimiento.nivel_urgencia]}</span>
              </Badge>
              <span className="text-sm font-medium text-muted-foreground truncate">
                {vencimiento.tipo}
              </span>
            </div>

            <p className="font-semibold text-primary hover:underline mb-1">
              {vencimiento.expediente_numero}
            </p>

            <p className="text-sm text-muted-foreground line-clamp-2">
              {vencimiento.actuacion_detalle || vencimiento.descripcion || 'Sin descripcion'}
            </p>

            <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
              <div className="flex items-center gap-1">
                <Calendar className="h-3 w-3" />
                {formatFecha(vencimiento.fecha_vencimiento)}
              </div>
            </div>
          </div>

          <div className="text-right flex-shrink-0">
            <div className={`text-2xl font-bold ${getTextColorUrgencia(vencimiento.nivel_urgencia)}`}>
              {formatDiasRestantes(vencimiento.dias_restantes)}
            </div>
            <p className="text-xs text-muted-foreground">restantes</p>
            <ChevronRight className="h-4 w-4 mt-2 text-muted-foreground ml-auto" />
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
          {/* Mostrar por grupos en orden de urgencia */}
          <GrupoVencimientos nivel="vencido" vencimientos={vencimientosAgrupados.vencido} />
          <GrupoVencimientos nivel="critico" vencimientos={vencimientosAgrupados.critico} />
          <GrupoVencimientos nivel="urgente" vencimientos={vencimientosAgrupados.urgente} />
          <GrupoVencimientos nivel="proximo" vencimientos={vencimientosAgrupados.proximo} />
          <GrupoVencimientos nivel="normal" vencimientos={vencimientosAgrupados.normal} />
        </div>
      )}
    </div>
  )
}
