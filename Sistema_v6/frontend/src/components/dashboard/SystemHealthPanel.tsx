/**
 * SystemHealthPanel - Panel de estado de salud del sistema.
 *
 * Muestra el estado de todos los servicios:
 * - Backend API
 * - MySQL Database
 * - Qdrant (RAG)
 * - Ollama (LLM)
 * - Monitoreo Scheduler
 */

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  HelpCircle,
  Server,
  RefreshCw,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  getSystemHealth,
  SystemHealth,
  ServiceHealthStatus,
  getServiceStatusColor,
} from '@/api/dashboardApi'

interface SystemHealthPanelProps {
  className?: string
  onError?: (error: Error) => void
}

const statusIcons: Record<
  ServiceHealthStatus['status'],
  React.ComponentType<{ className?: string }>
> = {
  ok: CheckCircle,
  error: XCircle,
  warning: AlertTriangle,
  unknown: HelpCircle,
}

const overallStatusConfig: Record<
  SystemHealth['overall_status'],
  { label: string; color: string; bgColor: string }
> = {
  healthy: {
    label: 'Sistema Operativo',
    color: 'text-green-600',
    bgColor: 'bg-green-100 dark:bg-green-900/20',
  },
  degraded: {
    label: 'Rendimiento Degradado',
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-100 dark:bg-yellow-900/20',
  },
  critical: {
    label: 'Estado Critico',
    color: 'text-red-600',
    bgColor: 'bg-red-100 dark:bg-red-900/20',
  },
}

export default function SystemHealthPanel({ className = '', onError }: SystemHealthPanelProps) {
  const [health, setHealth] = useState<SystemHealth | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)

  const fetchHealth = async (isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true)
      else setLoading(true)
      setError(null)

      const data = await getSystemHealth()
      setHealth(data)
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Error al verificar estado'
      setError(errorMsg)
      onError?.(err instanceof Error ? err : new Error(errorMsg))
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    fetchHealth()

    // Refrescar cada 60 segundos
    const interval = setInterval(() => fetchHealth(true), 60000)
    return () => clearInterval(interval)
  }, [])

  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('es-AR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  }

  if (loading) {
    return (
      <Card className={className}>
        <CardHeader>
          <Skeleton className="h-5 w-48" />
          <Skeleton className="h-4 w-32" />
        </CardHeader>
        <CardContent className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div className="flex items-center gap-3">
                <Skeleton className="h-5 w-5 rounded-full" />
                <Skeleton className="h-4 w-24" />
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
          <CardTitle className="text-red-600">Error de Conexion</CardTitle>
          <CardDescription>{error}</CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={() => fetchHealth()} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Reintentar
          </Button>
        </CardContent>
      </Card>
    )
  }

  if (!health) return null

  const overallConfig = overallStatusConfig[health.overall_status]

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Server className="h-5 w-5 text-gray-500" />
              Estado del Sistema
            </CardTitle>
            <CardDescription>
              Ultima verificacion: {formatTimestamp(health.timestamp)}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge className={`${overallConfig.bgColor} ${overallConfig.color}`}>
              {overallConfig.label}
            </Badge>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => fetchHealth(true)}
              disabled={refreshing}
              className="h-8 w-8"
            >
              <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {health.services.map((service) => {
            const StatusIcon = statusIcons[service.status]
            const colorClasses = getServiceStatusColor(service.status)

            return (
              <div
                key={service.name}
                className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className={`rounded-full p-1 ${colorClasses}`}>
                    <StatusIcon className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="font-medium text-sm">{service.name}</p>
                    {service.message && (
                      <p className="text-xs text-gray-500">{service.message}</p>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {service.response_time_ms !== undefined && service.response_time_ms !== null && (
                    <span className="text-xs text-gray-400">
                      {service.response_time_ms.toFixed(0)}ms
                    </span>
                  )}
                  <Badge
                    variant={service.status === 'ok' ? 'default' : 'secondary'}
                    className={`text-xs ${
                      service.status === 'ok'
                        ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                        : service.status === 'error'
                        ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                        : service.status === 'warning'
                        ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                        : 'bg-gray-100 text-gray-600'
                    }`}
                  >
                    {service.status.toUpperCase()}
                  </Badge>
                </div>
              </div>
            )
          })}
        </div>

        {/* Summary footer */}
        <div className="mt-4 pt-3 border-t border-gray-200 dark:border-gray-700">
          <div className="flex justify-between text-xs text-gray-500">
            <span>
              {health.services.filter((s) => s.status === 'ok').length} de{' '}
              {health.services.length} servicios operativos
            </span>
            <span>
              {health.services.filter((s) => s.status === 'error').length > 0 && (
                <span className="text-red-500">
                  {health.services.filter((s) => s.status === 'error').length} con errores
                </span>
              )}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
