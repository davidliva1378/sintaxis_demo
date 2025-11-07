import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { FileText, FolderOpen, Activity, Settings, Clock } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { es } from 'date-fns/locale'

interface ActivityItem {
  id: string
  type: 'expediente' | 'workspace' | 'monitoreo' | 'settings'
  title: string
  description: string
  timestamp: Date
  status?: 'success' | 'warning' | 'info' | 'error'
}

interface RecentActivityProps {
  activities: ActivityItem[]
}

const getIcon = (type: ActivityItem['type']) => {
  switch (type) {
    case 'expediente':
      return <FileText className="h-5 w-5" />
    case 'workspace':
      return <FolderOpen className="h-5 w-5" />
    case 'monitoreo':
      return <Activity className="h-5 w-5" />
    case 'settings':
      return <Settings className="h-5 w-5" />
  }
}

const getStatusColor = (status?: ActivityItem['status']) => {
  switch (status) {
    case 'success':
      return 'bg-green-100 dark:bg-green-900/20 text-green-600'
    case 'warning':
      return 'bg-orange-100 dark:bg-orange-900/20 text-orange-600'
    case 'error':
      return 'bg-red-100 dark:bg-red-900/20 text-red-600'
    default:
      return 'bg-blue-100 dark:bg-blue-900/20 text-blue-600'
  }
}

export default function RecentActivity({ activities }: RecentActivityProps) {
  if (activities.length === 0) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Actividad Reciente</CardTitle>
              <CardDescription>Últimas acciones en el sistema</CardDescription>
            </div>
            <Clock className="h-5 w-5 text-gray-400" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <p>No hay actividad reciente</p>
            <p className="text-sm mt-2">
              Las acciones que realices aparecerán aquí
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Actividad Reciente</CardTitle>
            <CardDescription>Últimas {activities.length} acciones</CardDescription>
          </div>
          <Clock className="h-5 w-5 text-gray-400" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {activities.map((activity, index) => (
            <div
              key={activity.id}
              className="flex gap-4 pb-4 border-b border-gray-200 dark:border-gray-700 last:border-0 last:pb-0"
            >
              <div className={`rounded-full p-2 h-fit ${getStatusColor(activity.status)}`}>
                {getIcon(activity.type)}
              </div>
              <div className="flex-1 space-y-1">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    {activity.title}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {formatDistanceToNow(activity.timestamp, { addSuffix: true, locale: es })}
                  </p>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {activity.description}
                </p>
                {activity.status && (
                  <Badge variant="outline" className="text-xs">
                    {activity.status === 'success' && 'Completado'}
                    {activity.status === 'warning' && 'Advertencia'}
                    {activity.status === 'error' && 'Error'}
                    {activity.status === 'info' && 'Información'}
                  </Badge>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
