import { useAuthStore } from '@/stores/authStore'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import ActivityChart from '@/components/dashboard/ActivityChart'
import StatsChart from '@/components/dashboard/StatsChart'
import RecentActivity from '@/components/dashboard/RecentActivity'
import {
  FileText,
  FolderOpen,
  Activity,
  Settings,
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle
} from 'lucide-react'
import { subDays, format } from 'date-fns'

export default function DashboardPage() {
  const { user } = useAuthStore()

  const stats = [
    {
      title: 'Expedientes',
      value: '0',
      description: 'Total de expedientes',
      icon: FileText,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100 dark:bg-blue-900/20',
    },
    {
      title: 'Workspaces',
      value: '0',
      description: 'Espacios de trabajo',
      icon: FolderOpen,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100 dark:bg-purple-900/20',
    },
    {
      title: 'Activos',
      value: '0',
      description: 'En monitoreo',
      icon: Activity,
      color: 'text-green-600',
      bgColor: 'bg-green-100 dark:bg-green-900/20',
    },
    {
      title: 'Actualizaciones',
      value: '0',
      description: 'Últimas 24 horas',
      icon: TrendingUp,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100 dark:bg-orange-900/20',
    },
  ]

  const quickActions = [
    {
      title: 'Extraer Expedientes',
      description: 'Extraer expedientes del PJN',
      icon: FileText,
      href: '/expedientes',
      status: 'Próximamente',
    },
    {
      title: 'Iniciar Monitoreo',
      description: 'Monitorear cambios automáticamente',
      icon: Activity,
      href: '/monitoreo',
      status: 'Próximamente',
    },
    {
      title: 'Crear Workspace',
      description: 'Organizar expedientes por carpetas',
      icon: FolderOpen,
      href: '/workspaces',
      status: 'Próximamente',
    },
    {
      title: 'Configurar PJN',
      description: 'Configurar credenciales del PJN',
      icon: Settings,
      href: '/settings',
      status: user?.has_pjn_credentials ? 'Configurado' : 'Pendiente',
    },
  ]

  // Datos de ejemplo para gráficos (serán reemplazados con datos reales en futuras fases)
  const activityData = Array.from({ length: 30 }, (_, i) => ({
    date: format(subDays(new Date(), 29 - i), 'dd/MM'),
    expedientes: Math.floor(Math.random() * 10),
    actualizaciones: Math.floor(Math.random() * 15),
  }))

  const statsData = [
    { name: 'Ene', activos: 12, completados: 8, pendientes: 4 },
    { name: 'Feb', activos: 15, completados: 10, pendientes: 5 },
    { name: 'Mar', activos: 10, completados: 15, pendientes: 2 },
    { name: 'Abr', activos: 18, completados: 12, pendientes: 6 },
    { name: 'May', activos: 14, completados: 9, pendientes: 5 },
    { name: 'Jun', activos: 16, completados: 11, pendientes: 5 },
  ]

  const recentActivities = [
    {
      id: '1',
      type: 'expediente' as const,
      title: 'Expediente extraído',
      description: 'Expediente JUZ-FAM-2024-0123 extraído exitosamente',
      timestamp: subDays(new Date(), 0),
      status: 'success' as const,
    },
    {
      id: '2',
      type: 'monitoreo' as const,
      title: 'Actualización detectada',
      description: 'Se detectó nueva actuación en expediente JUZ-CIV-2024-0456',
      timestamp: subDays(new Date(), 1),
      status: 'info' as const,
    },
    {
      id: '3',
      type: 'workspace' as const,
      title: 'Workspace creado',
      description: 'Nuevo workspace "Casos Prioritarios" creado',
      timestamp: subDays(new Date(), 2),
      status: 'success' as const,
    },
    {
      id: '4',
      type: 'settings' as const,
      title: 'Credenciales actualizadas',
      description: 'Credenciales del PJN actualizadas correctamente',
      timestamp: subDays(new Date(), 3),
      status: 'success' as const,
    },
  ]

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Bienvenido, {user?.username}
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Panel de control del Sistema PJN v6
        </p>
      </div>

      {/* Warning if PJN not configured */}
      {!user?.has_pjn_credentials && (
        <Card className="border-orange-500 bg-orange-50 dark:bg-orange-900/20">
          <CardContent className="flex items-start gap-3 p-4">
            <AlertCircle className="h-5 w-5 text-orange-600 mt-0.5" />
            <div>
              <h3 className="font-semibold text-orange-900 dark:text-orange-100">
                Credenciales PJN no configuradas
              </h3>
              <p className="text-sm text-orange-800 dark:text-orange-200">
                Para usar las funciones de scraping, necesitas configurar tus credenciales del Portal Judicial Nacional.
                Ve a <a href="/settings" className="underline font-medium">Configuración</a> para completar este paso.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon
          return (
            <Card key={stat.title}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  {stat.title}
                </CardTitle>
                <div className={`rounded-full p-2 ${stat.bgColor}`}>
                  <Icon className={`h-4 w-4 ${stat.color}`} />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {stat.description}
                </p>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Acciones Rápidas
        </h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {quickActions.map((action) => {
            const Icon = action.icon
            const isAvailable = action.status === 'Configurado'
            const isPending = action.status === 'Pendiente'

            return (
              <Card
                key={action.title}
                className="hover:shadow-lg transition-shadow cursor-pointer group"
              >
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className={`rounded-lg p-2 ${
                      isAvailable
                        ? 'bg-green-100 dark:bg-green-900/20'
                        : isPending
                        ? 'bg-orange-100 dark:bg-orange-900/20'
                        : 'bg-gray-100 dark:bg-gray-800'
                    }`}>
                      <Icon className={`h-5 w-5 ${
                        isAvailable
                          ? 'text-green-600'
                          : isPending
                          ? 'text-orange-600'
                          : 'text-gray-600'
                      }`} />
                    </div>
                    <Badge variant={isAvailable ? "default" : "secondary"} className="text-xs">
                      {action.status}
                    </Badge>
                  </div>
                  <CardTitle className="text-base mt-4 group-hover:text-blue-600 transition-colors">
                    {action.title}
                  </CardTitle>
                  <CardDescription>{action.description}</CardDescription>
                </CardHeader>
              </Card>
            )
          })}
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid gap-6 lg:grid-cols-2">
        <ActivityChart data={activityData} />
        <StatsChart data={statsData} />
      </div>

      {/* Recent Activity */}
      <RecentActivity activities={recentActivities} />

      {/* System Info */}
      <Card>
        <CardHeader>
          <CardTitle>Información del Sistema</CardTitle>
          <CardDescription>Estado actual del sistema</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="flex items-center gap-3">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <div>
                <p className="text-sm font-medium">API Backend</p>
                <p className="text-xs text-gray-500">Conectado</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <div>
                <p className="text-sm font-medium">Base de Datos</p>
                <p className="text-xs text-gray-500">Operativa</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {user?.has_pjn_credentials ? (
                <CheckCircle className="h-5 w-5 text-green-600" />
              ) : (
                <AlertCircle className="h-5 w-5 text-orange-600" />
              )}
              <div>
                <p className="text-sm font-medium">Credenciales PJN</p>
                <p className="text-xs text-gray-500">
                  {user?.has_pjn_credentials ? 'Configuradas' : 'No configuradas'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <div>
                <p className="text-sm font-medium">Versión</p>
                <p className="text-xs text-gray-500">v6.0.0</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
