/**
 * Tests de integración para ProtectedRoute
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import ProtectedRoute from '../ProtectedRoute'
import { useAuthStore } from '@/stores/authStore'
import { createMockUser } from '@/test/utils'

// Mock de navigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
    })
  })

  it('redirige a /login si no está autenticado', () => {
    render(
      <BrowserRouter>
        <Routes>
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <div>Protected Content</div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    )

    // No debería mostrar el contenido protegido
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()

    // Debería haber llamado a navigate con /login
    expect(mockNavigate).toHaveBeenCalledWith('/login', { replace: true })
  })

  it('muestra el contenido si está autenticado', () => {
    // Simular usuario autenticado
    const mockUser = createMockUser()
    useAuthStore.setState({
      user: mockUser,
      token: 'test_token',
      isAuthenticated: true,
    })

    render(
      <BrowserRouter>
        <Routes>
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <div>Protected Content</div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    )

    // Debería mostrar el contenido protegido
    expect(screen.getByText('Protected Content')).toBeInTheDocument()

    // No debería redirigir
    expect(mockNavigate).not.toHaveBeenCalled()
  })

  it('redirige si hay token pero no user', () => {
    useAuthStore.setState({
      user: null,
      token: 'test_token',
      isAuthenticated: true,
    })

    render(
      <BrowserRouter>
        <Routes>
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <div>Protected Content</div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    )

    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
    expect(mockNavigate).toHaveBeenCalledWith('/login', { replace: true })
  })

  it('redirige si hay user pero no está autenticado', () => {
    const mockUser = createMockUser()
    useAuthStore.setState({
      user: mockUser,
      token: null,
      isAuthenticated: false,
    })

    render(
      <BrowserRouter>
        <Routes>
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <div>Protected Content</div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    )

    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
    expect(mockNavigate).toHaveBeenCalledWith('/login', { replace: true })
  })

  it('renderiza children correctamente cuando está autenticado', () => {
    const mockUser = createMockUser()
    useAuthStore.setState({
      user: mockUser,
      token: 'test_token',
      isAuthenticated: true,
    })

    render(
      <BrowserRouter>
        <Routes>
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <div>
                  <h1>Dashboard</h1>
                  <p>Welcome {mockUser.username}</p>
                </div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    )

    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText(`Welcome ${mockUser.username}`)).toBeInTheDocument()
  })
})
