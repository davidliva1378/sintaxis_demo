import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { Toaster } from 'sonner'
import SplashScreen from './components/common/SplashScreen'
import LoginPage from './pages/auth/LoginPage'
import RegisterPage from './pages/auth/RegisterPage'
import DashboardPage from './pages/dashboard/DashboardPage'
import ExpedientesPage from './pages/expedientes/ExpedientesPage'
import ExpedienteDetallePage from './pages/expedientes/ExpedienteDetallePage'
import WorkspacesPage from './pages/workspaces/WorkspacesPage'
import WorkspaceDetailPage from './pages/workspaces/WorkspaceDetailPage'
import MonitoreoPage from './pages/monitoreo/MonitoreoPage'
import ProcesamientoPage from './pages/procesamiento/ProcesamientoPage'
import SettingsPage from './pages/settings/SettingsPage'
import AgendaPage from './pages/agenda/AgendaPage'
import EscritosPage from './pages/escritos/EscritosPage'
import DestacadosPage from './pages/destacados/DestacadosPage'
import IAPage from './pages/ia/IAPage'
import VencimientosPage from './pages/vencimientos/VencimientosPage'
import EstadisticasPage from './pages/estadisticas/EstadisticasPage'
import ProtectedRoute from './components/layout/ProtectedRoute'
import MainLayout from './components/layout/MainLayout'
import { ErrorBoundary } from './components/common/ErrorBoundary'
import { useThemeStore } from './stores/themeStore'

function App() {
  const theme = useThemeStore((state) => state.theme)
  const [showSplash, setShowSplash] = useState(() => {
    // Solo mostrar splash una vez por sesión
    return !sessionStorage.getItem('splashShown')
  })

  useEffect(() => {
    // Apply theme to document
    if (theme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [theme])

  const handleSplashComplete = () => {
    setShowSplash(false)
    sessionStorage.setItem('splashShown', 'true')
  }

  return (
    <ErrorBoundary>
      {/* Splash Screen - solo se muestra una vez por sesión */}
      {showSplash && <SplashScreen onComplete={handleSplashComplete} />}
      <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Protected Routes */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <DashboardPage />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/expedientes"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <ExpedientesPage />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/expedientes/:numero"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <ExpedienteDetallePage />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/workspaces"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <WorkspacesPage />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/workspaces/:id"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <WorkspaceDetailPage />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/monitoreo"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <MonitoreoPage />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/procesamiento"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <ProcesamientoPage />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <SettingsPage />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/agenda"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <AgendaPage />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/escritos"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <EscritosPage />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/destacados"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <DestacadosPage />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/ia"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <IAPage />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/vencimientos"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <VencimientosPage />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/estadisticas"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <EstadisticasPage />
                </MainLayout>
              </ProtectedRoute>
            }
          />
          {/* Redirects de rutas obsoletas a /ia */}
          <Route path="/asistente-ia" element={<Navigate to="/ia" replace />} />
          <Route path="/rag" element={<Navigate to="/ia" replace />} />

          {/* Redirect root to dashboard */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />

          {/* 404 redirect to dashboard */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
      <Toaster
        position="top-right"
        theme={theme}
        richColors
        closeButton
        duration={4000}
      />
    </ErrorBoundary>
  )
}

export default App
