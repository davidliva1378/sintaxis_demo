/**
 * KPICards - Tarjetas de KPIs del Dashboard.
 *
 * Muestra las metricas principales del sistema:
 * - Total expedientes
 * - Expedientes esta semana
 * - Vencimientos urgentes/vencidos
 * - Expedientes monitoreados
 * - % procesado con IA
 * - Total actuaciones
 * - Documentos RAG indexados
 */

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import {
  FileText,
  Calendar,
  AlertTriangle,
  AlertCircle,
  Eye,
  Brain,
  Activity,
  Database,
} from 'lucide-react'
import { getDashboardStats, DashboardStats } from '@/api/dashboardApi'

interface KPICardData {
  title: string
  value: string | number
  description: string
  icon: React.ComponentType<{ className?: string }>
  color: string
  bgColor: string
  trend?: {
    value: number
    isPositive: boolean
  }
}

interface KPICardsProps {
  className?: string
  onError?: (error: Error) => void
}

export default function KPICards({ className = '', onError }: KPICardsProps) {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchStats() {
      try {
        setLoading(true)
        setError(null)
        const data = await getDashboardStats()
        setStats(data)
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Error al cargar estadisticas'
        setError(errorMsg)
        onError?.(err instanceof Error ? err : new Error(errorMsg))
      } finally {
        setLoading(false)
      }
    }

    fetchStats()

    // Refrescar cada 30 segundos
    const interval = setInterval(fetchStats, 30000)
    return () => clearInterval(interval)
  }, [onError])

  const buildKPICards = (data: DashboardStats): KPICardData[] => [
    {
      title: 'Expedientes',
      value: data.total_expedientes.toLocaleString(),
      description: 'Total en el sistema',
      icon: FileText,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100 dark:bg-blue-900/20',
    },
    {
      title: 'Esta Semana',
      value: data.expedientes_semana.toLocaleString(),
      description: 'Nuevos expedientes',
      icon: Calendar,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100 dark:bg-purple-900/20',
    },
    {
      title: 'Urgentes',
      value: data.vencimientos_urgentes,
      description: 'Vencimientos proximos',
      icon: AlertTriangle,
      color: data.vencimientos_urgentes > 0 ? 'text-orange-600' : 'text-green-600',
      bgColor:
        data.vencimientos_urgentes > 0
          ? 'bg-orange-100 dark:bg-orange-900/20'
          : 'bg-green-100 dark:bg-green-900/20',
    },
    {
      title: 'Vencidos',
      value: data.vencimientos_vencidos,
      description: 'Requieren atencion',
      icon: AlertCircle,
      color: data.vencimientos_vencidos > 0 ? 'text-red-600' : 'text-green-600',
      bgColor:
        data.vencimientos_vencidos > 0
          ? 'bg-red-100 dark:bg-red-900/20'
          : 'bg-green-100 dark:bg-green-900/20',
    },
    {
      title: 'Monitoreados',
      value: data.expedientes_monitoreados,
      description: 'En monitoreo activo',
      icon: Eye,
      color: 'text-green-600',
      bgColor: 'bg-green-100 dark:bg-green-900/20',
    },
    {
      title: 'Procesado IA',
      value: `${data.porcentaje_procesado_ia.toFixed(1)}%`,
      description: 'Actuaciones con IA',
      icon: Brain,
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-100 dark:bg-indigo-900/20',
    },
    {
      title: 'Actuaciones',
      value: data.total_actuaciones.toLocaleString(),
      description: 'Total procesadas',
      icon: Activity,
      color: 'text-cyan-600',
      bgColor: 'bg-cyan-100 dark:bg-cyan-900/20',
    },
    {
      title: 'RAG Index',
      value: data.documentos_indexados_rag.toLocaleString(),
      description: 'Documentos indexados',
      icon: Database,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-100 dark:bg-emerald-900/20',
    },
  ]

  if (loading) {
    return (
      <div className={`grid gap-4 md:grid-cols-2 lg:grid-cols-4 ${className}`}>
        {Array.from({ length: 8 }).map((_, i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-8 w-8 rounded-full" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16 mb-1" />
              <Skeleton className="h-3 w-20" />
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <Card className={`border-red-200 bg-red-50 dark:bg-red-900/20 ${className}`}>
        <CardContent className="flex items-center gap-3 p-4">
          <AlertCircle className="h-5 w-5 text-red-600" />
          <div>
            <p className="font-medium text-red-900 dark:text-red-100">
              Error al cargar estadisticas
            </p>
            <p className="text-sm text-red-700 dark:text-red-200">{error}</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!stats) return null

  const kpiCards = buildKPICards(stats)

  return (
    <div className={`grid gap-4 md:grid-cols-2 lg:grid-cols-4 ${className}`}>
      {kpiCards.map((card) => {
        const Icon = card.icon
        return (
          <Card key={card.title} className="hover:shadow-md transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
                {card.title}
              </CardTitle>
              <div className={`rounded-full p-2 ${card.bgColor}`}>
                <Icon className={`h-4 w-4 ${card.color}`} />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{card.value}</div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{card.description}</p>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
