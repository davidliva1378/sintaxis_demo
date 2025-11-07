import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import Sidebar from './Sidebar'
import Header from './Header'

interface MainLayoutProps {
  children: React.ReactNode
}

export default function MainLayout({ children }: MainLayoutProps) {
  const navigate = useNavigate()
  const { user, isAuthenticated, fetchUser } = useAuthStore()

  useEffect(() => {
    // Fetch user data if authenticated but user not loaded
    if (isAuthenticated && !user) {
      fetchUser().catch(() => {
        // If fetch fails, redirect to login
        navigate('/login')
      })
    }
  }, [isAuthenticated, user, fetchUser, navigate])

  // Show loading state while fetching user
  if (isAuthenticated && !user) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <div className="mb-4 h-12 w-12 animate-spin rounded-full border-4 border-blue-500 border-t-transparent mx-auto"></div>
          <p className="text-gray-600 dark:text-gray-400">Cargando...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Header */}
        <Header />

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto">
          <div className="container mx-auto p-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
