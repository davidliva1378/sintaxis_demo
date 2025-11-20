import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import { Toaster } from 'sonner'
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
import ProtectedRoute from './components/layout/ProtectedRoute'
import MainLayout from './components/layout/MainLayout'
import { ErrorBoundary } from './components/common/ErrorBoundary'
import { useThemeStore } from './stores/themeStore'

function App() {
  const theme = useThemeStore((state) => state.theme)

  useEffect(() => {
    // Apply theme to document
    if (theme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [theme])

  return (
    <ErrorBoundary>
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
