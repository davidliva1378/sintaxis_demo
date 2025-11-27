import { useAuthStore } from '@/stores/authStore'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import ActivityChart from '@/components/dashboard/ActivityChart'
import StatsChart from '@/components/dashboard/StatsChart'
import RecentActivity from '@/components/dashboard/RecentActivity'
import KPICards from '@/components/dashboard/KPICards'
import VencimientosWidget from '@/components/dashboard/VencimientosWidget'
import SystemHealthPanel from '@/components/dashboard/SystemHealthPanel'
import {
  FileText,
  FolderOpen,
  Activity,
  Settings,
  AlertCircle
} from 'lucide-react'
import { subDays, format } from 'date-fns'

export default function DashboardPage() {
  const { user } = useAuthStore()

  const quickActions = [
    {
      title: 'Extraer Expedientes',
      description: 'Extraer expedientes del PJN',
      icon: FileText,
      href: '/expedientes',
      status: 'Disponible',
    },
    {
      title: 'Iniciar Monitoreo',
      description: 'Monitorear cambios automaticamente',
      icon: Activity,
      href: '/monitoreo',
      status: 'Disponible',
    },
    {
      title: 'Crear Workspace',
      description: 'Organizar expedientes por carpetas',
      icon: FolderOpen,
      href: '/workspaces',
      status: 'Disponible',
    },
    {
      title: 'Configurar PJN',
      description: 'Configurar credenciales del PJN',
      icon: Settings,
      href: '/settings',
      status: user?.has_pjn_credentials ? 'Configurado' : 'Pendiente',
    },
  ]

  // Datos de ejemplo para graficos (seran reemplazados con datos reales en futuras fases)
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
      title: 'Expediente extraido',
      description: 'Expediente JUZ-FAM-2024-0123 extraido exitosamente',
      timestamp: subDays(new Date(), 0),
      status: 'success' as const,
    },
    {
      id: '2',
      type: 'monitoreo' as const,
      title: 'Actualizacion detectada',
      description: 'Se detecto nueva actuacion en expediente JUZ-CIV-2024-0456',
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
                Ve a <a href="/settings" className="underline font-medium">Configuracion</a> para completar este paso.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* KPI Cards - Datos reales desde backend */}
      <KPICards />

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Acciones Rapidas
        </h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {quickActions.map((action) => {
            const Icon = action.icon
            const isAvailable = action.status === 'Configurado' || action.status === 'Disponible'
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

      {/* Vencimientos + System Health Row */}
      <div className="grid gap-6 lg:grid-cols-2">
        <VencimientosWidget />
        <SystemHealthPanel />
      </div>

      {/* Charts Section */}
      <div className="grid gap-6 lg:grid-cols-2">
        <ActivityChart data={activityData} />
        <StatsChart data={statsData} />
      </div>

      {/* Recent Activity */}
      <RecentActivity activities={recentActivities} />
    </div>
  )
}
