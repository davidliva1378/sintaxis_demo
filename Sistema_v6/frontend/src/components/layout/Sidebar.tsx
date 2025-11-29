import { Link, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard,
  FileText,
  FolderOpen,
  Activity,
  Zap,
  Calendar,
  PenTool,
  Star,
  Settings,
  Brain,
  Clock,
  BarChart3,
} from 'lucide-react'

const navigation = [
  {
    name: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
  },
  {
    name: 'Expedientes',
    href: '/expedientes',
    icon: FileText,
  },
  {
    name: 'Workspaces',
    href: '/workspaces',
    icon: FolderOpen,
  },
  {
    name: 'Monitoreo',
    href: '/monitoreo',
    icon: Activity,
  },
  {
    name: 'Procesamiento',
    href: '/procesamiento',
    icon: Zap,
  },
  {
    name: 'Vencimientos',
    href: '/vencimientos',
    icon: Clock,
  },
  {
    name: 'Agenda',
    href: '/agenda',
    icon: Calendar,
  },
  {
    name: 'Escritos',
    href: '/escritos',
    icon: PenTool,
  },
  {
    name: 'Destacados',
    href: '/destacados',
    icon: Star,
  },
  {
    name: 'IA',
    href: '/ia',
    icon: Brain,
    badge: 'Beta',
  },

  {
    name: 'Estadísticas',
    href: '/estadisticas',
    icon: BarChart3,
  },
  {
    name: 'Configuración',
    href: '/settings',
    icon: Settings,
  },
]

export default function Sidebar() {
  const location = useLocation()

  return (
    <div className="flex h-full w-64 flex-col bg-gray-900 dark:bg-gray-950">
      {/* Logo */}
      <div className="flex h-16 items-center justify-center border-b border-gray-800 px-4">
        <h1 className="text-xl font-bold text-white">
          Sistema PJN <span className="text-blue-500">v6</span>
        </h1>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href
          const Icon = item.icon

          return (
            <Link
              key={item.name}
              to={item.href}
              className={cn(
                'group flex items-center justify-between rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-gray-800 text-white'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-white'
              )}
            >
              <div className="flex items-center gap-3">
                <Icon className="h-5 w-5" />
                <span>{item.name}</span>
              </div>
              {item.badge && (
                <span className="rounded-full bg-gray-700 px-2 py-0.5 text-xs text-gray-300">
                  {item.badge}
                </span>
              )}
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-gray-800 p-4">
        <p className="text-center text-xs text-gray-500">
          © 2025 Sistema PJN v6
        </p>
      </div>
    </div>
  )
}
