import { useState, useEffect } from 'react'
import {
  BarChart3,
  FileText,
  Users,
  Brain,
  Database,
  AlertTriangle,
  CheckCircle,
  XCircle,
  RefreshCw,
  TrendingUp,
  Clock,
  Activity
} from 'lucide-react'
import { estadisticasApi, type EstadisticasGenerales } from '@/api/estadisticasApi'
import { cn } from '@/lib/utils'

// Componente de tarjeta de estadística
function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  color = 'blue'
}: {
  title: string
  value: string | number
  subtitle?: string
  icon: React.ElementType
  trend?: { value: number; label: string }
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'purple' | 'indigo'
}) {
  const colorClasses = {
    blue: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
    green: 'bg-green-500/10 text-green-500 border-green-500/20',
    yellow: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
    red: 'bg-red-500/10 text-red-500 border-red-500/20',
    purple: 'bg-purple-500/10 text-purple-500 border-purple-500/20',
    indigo: 'bg-indigo-500/10 text-indigo-500 border-indigo-500/20',
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
      <div className="flex items-center justify-between">
        <div className={cn('rounded-lg p-3 border', colorClasses[color])}>
          <Icon className="h-6 w-6" />
        </div>
        {trend && (
          <div className={cn(
            'flex items-center gap-1 text-sm',
            trend.value >= 0 ? 'text-green-500' : 'text-red-500'
          )}>
            <TrendingUp className={cn('h-4 w-4', trend.value < 0 && 'rotate-180')} />
            <span>{Math.abs(trend.value)}%</span>
          </div>
        )}
      </div>
      <div className="mt-4">
        <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
          {typeof value === 'number' ? value.toLocaleString() : value}
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400">{title}</p>
        {subtitle && (
          <p className="mt-1 text-xs text-gray-400 dark:text-gray-500">{subtitle}</p>
        )}
      </div>
    </div>
  )
}

// Componente de estado de servicio
function ServiceStatus({
  name,
  status,
  description
}: {
  name: string
  status: boolean
  description: string
}) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
      <div className="flex items-center gap-3">
        {status ? (
          <CheckCircle className="h-5 w-5 text-green-500" />
        ) : (
          <XCircle className="h-5 w-5 text-red-500" />
        )}
        <div>
          <p className="font-medium text-gray-900 dark:text-white">{name}</p>
          <p className="text-sm text-gray-500 dark:text-gray-400">{description}</p>
        </div>
      </div>
      <span className={cn(
        'rounded-full px-2.5 py-0.5 text-xs font-medium',
        status
          ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
          : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
      )}>
        {status ? 'Online' : 'Offline'}
      </span>
    </div>
  )
}

// Componente de distribución de entidades
function EntidadesDistribucion({ porTipo }: { porTipo: Record<string, number> }) {
  const entries = Object.entries(porTipo).sort((a, b) => b[1] - a[1]).slice(0, 8)
  const total = entries.reduce((sum, [, count]) => sum + count, 0)

  const colors = [
    'bg-blue-500',
    'bg-green-500',
    'bg-yellow-500',
    'bg-purple-500',
    'bg-pink-500',
    'bg-indigo-500',
    'bg-red-500',
    'bg-orange-500',
  ]

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
      <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
        Distribución de Entidades
      </h3>
      <div className="space-y-3">
        {entries.map(([tipo, count], idx) => {
          const percentage = total > 0 ? (count / total) * 100 : 0
          return (
            <div key={tipo}>
              <div className="mb-1 flex items-center justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-300">{tipo}</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {count.toLocaleString()}
                </span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
                <div
                  className={cn('h-full rounded-full transition-all', colors[idx % colors.length])}
                  style={{ width: `${percentage}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>
      {entries.length === 0 && (
        <p className="text-center text-gray-500 dark:text-gray-400">
          No hay datos de entidades disponibles
        </p>
      )}
    </div>
  )
}

// Componente de vencimientos
function VencimientosResumen({ vencimientos }: { vencimientos: EstadisticasGenerales['vencimientos'] }) {
  const items = [
    { label: 'Vencidos', value: vencimientos.vencidos, color: 'text-red-500 bg-red-500/10' },
    { label: 'Críticos', value: vencimientos.criticos, color: 'text-orange-500 bg-orange-500/10' },
    { label: 'Urgentes', value: vencimientos.urgentes, color: 'text-yellow-500 bg-yellow-500/10' },
    { label: 'Próximos', value: vencimientos.proximos, color: 'text-blue-500 bg-blue-500/10' },
  ]

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Vencimientos
        </h3>
        <span className="text-2xl font-bold text-gray-900 dark:text-white">
          {vencimientos.total}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-3">
        {items.map(item => (
          <div
            key={item.label}
            className={cn('rounded-lg p-3 text-center', item.color)}
          >
            <p className="text-2xl font-bold">{item.value}</p>
            <p className="text-xs font-medium">{item.label}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function EstadisticasPage() {
  const [stats, setStats] = useState<EstadisticasGenerales | null>(null)
  const [health, setHealth] = useState<{
    backend: boolean
    database: boolean
    rag: boolean
    ollama: boolean
  } | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const loadData = async () => {
    try {
      const [statsData, healthData] = await Promise.all([
        estadisticasApi.getEstadisticasGenerales(),
        estadisticasApi.getHealthStatus(),
      ])
      setStats(statsData)
      setHealth(healthData)
    } catch (error) {
      console.error('Error cargando estadísticas:', error)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    loadData()
    // Actualizar cada 30 segundos
    const interval = setInterval(loadData, 30000)
    return () => clearInterval(interval)
  }, [])

  const handleRefresh = () => {
    setRefreshing(true)
    loadData()
  }

  if (loading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-500" />
          <p className="text-gray-500 dark:text-gray-400">Cargando estadísticas...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Estadísticas del Sistema
          </h1>
          <p className="text-gray-500 dark:text-gray-400">
            Métricas y estado general de sintaXis
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
        >
          <RefreshCw className={cn('h-4 w-4', refreshing && 'animate-spin')} />
          Actualizar
        </button>
      </div>

      {/* Estadísticas principales */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Expedientes"
          value={stats?.expedientes.total || 0}
          subtitle={`${stats?.expedientes.monitoreados || 0} monitoreados`}
          icon={FileText}
          color="blue"
        />
        <StatCard
          title="Actuaciones"
          value={stats?.actuaciones.total || 0}
          subtitle={`${stats?.actuaciones.indexadas_rag || 0} indexadas`}
          icon={Activity}
          color="green"
        />
        <StatCard
          title="Entidades"
          value={stats?.entidades.total || 0}
          subtitle="Extraídas por IA"
          icon={Users}
          color="purple"
        />
        <StatCard
          title="Documentos RAG"
          value={stats?.rag.documentos_indexados || 0}
          subtitle={`BM25: ${stats?.rag.bm25_documentos || 0}`}
          icon={Brain}
          color="indigo"
        />
      </div>

      {/* Segunda fila */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Distribución de entidades */}
        <div className="lg:col-span-2">
          <EntidadesDistribucion porTipo={stats?.entidades.por_tipo || {}} />
        </div>

        {/* Vencimientos */}
        <VencimientosResumen vencimientos={stats?.vencimientos || {
          total: 0,
          vencidos: 0,
          criticos: 0,
          urgentes: 0,
          proximos: 0,
        }} />
      </div>

      {/* Estado de servicios */}
      <div>
        <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
          Estado de Servicios
        </h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <ServiceStatus
            name="Backend API"
            status={health?.backend || false}
            description="Servidor FastAPI principal"
          />
          <ServiceStatus
            name="Base de Datos"
            status={health?.database || false}
            description="MySQL / MariaDB"
          />
          <ServiceStatus
            name="RAG (Qdrant)"
            status={health?.rag || false}
            description="Índice vectorial para búsqueda semántica"
          />
          <ServiceStatus
            name="Ollama LLM"
            status={health?.ollama || false}
            description="Modelo de lenguaje local"
          />
        </div>
      </div>

      {/* Información del sistema */}
      <div className="rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
        <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
          Información del Sistema
        </h2>
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="flex items-center gap-3">
            <Database className="h-5 w-5 text-gray-400" />
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Versión</p>
              <p className="font-medium text-gray-900 dark:text-white">
                {stats?.sistema.version || 'v6.0.0'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <BarChart3 className="h-5 w-5 text-gray-400" />
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Colección RAG</p>
              <p className="font-medium text-gray-900 dark:text-white">
                {stats?.rag.coleccion || 'actuaciones'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Clock className="h-5 w-5 text-gray-400" />
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Última sync</p>
              <p className="font-medium text-gray-900 dark:text-white">
                {stats?.sistema.ultima_sincronizacion
                  ? new Date(stats.sistema.ultima_sincronizacion).toLocaleString()
                  : 'No disponible'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Alertas si hay problemas */}
      {health && (!health.backend || !health.database || !health.rag) && (
        <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4 dark:border-yellow-900/50 dark:bg-yellow-900/20">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
            <div>
              <p className="font-medium text-yellow-800 dark:text-yellow-200">
                Algunos servicios no están disponibles
              </p>
              <p className="text-sm text-yellow-700 dark:text-yellow-300">
                Verifica que todos los servicios estén corriendo correctamente.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
