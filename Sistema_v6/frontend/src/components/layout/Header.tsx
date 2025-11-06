import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import ThemeToggle from './ThemeToggle'
import { LogOut, User, Shield } from 'lucide-react'

export default function Header() {
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2)
  }

  return (
    <header className="sticky top-0 z-10 flex h-16 items-center justify-between border-b bg-white px-6 dark:bg-gray-900 dark:border-gray-800">
      {/* Page Title / Breadcrumb */}
      <div className="flex items-center gap-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          Sistema de Gestión PJN
        </h2>
      </div>

      {/* Right Side - User Info & Actions */}
      <div className="flex items-center gap-4">
        {/* PJN Credentials Status */}
        {user && (
          <div className="hidden sm:flex items-center gap-2">
            {user.has_pjn_credentials ? (
              <Badge variant="default" className="bg-green-500 hover:bg-green-600">
                <Shield className="mr-1 h-3 w-3" />
                PJN Configurado
              </Badge>
            ) : (
              <Badge variant="destructive">
                <Shield className="mr-1 h-3 w-3" />
                PJN No Configurado
              </Badge>
            )}
          </div>
        )}

        {/* Theme Toggle */}
        <ThemeToggle />

        {/* User Info */}
        {user && (
          <div className="flex items-center gap-3 border-l pl-4 dark:border-gray-700">
            <div className="hidden text-right sm:block">
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                {user.username}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {user.is_superuser ? (
                  <span className="flex items-center gap-1">
                    <Shield className="h-3 w-3" />
                    Administrador
                  </span>
                ) : (
                  'Usuario'
                )}
              </p>
            </div>

            <Avatar className="h-9 w-9">
              <AvatarFallback className="bg-blue-500 text-white text-sm">
                {getInitials(user.username)}
              </AvatarFallback>
            </Avatar>

            <Button
              variant="ghost"
              size="icon"
              onClick={handleLogout}
              className="h-9 w-9"
              title="Cerrar sesión"
            >
              <LogOut className="h-5 w-5" />
            </Button>
          </div>
        )}
      </div>
    </header>
  )
}
