/**
 * Tests para authStore
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useAuthStore } from '../authStore'
import { createMockUser } from '@/test/utils'

// Mock de apiClient
vi.mock('@/lib/api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

describe('authStore', () => {
  beforeEach(() => {
    // Reset store antes de cada test
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
    })

    // Clear localStorage
    localStorage.clear()

    // Clear mocks
    vi.clearAllMocks()
  })

  describe('Estado inicial', () => {
    it('tiene estado inicial correcto', () => {
      const state = useAuthStore.getState()

      expect(state.user).toBeNull()
      expect(state.token).toBeNull()
      expect(state.isAuthenticated).toBe(false)
      expect(state.isLoading).toBe(false)
    })
  })

  describe('logout', () => {
    it('limpia el estado correctamente', () => {
      // Setup: Simular usuario autenticado
      const mockUser = createMockUser()
      localStorage.setItem('access_token', 'test_token')
      useAuthStore.setState({
        user: mockUser,
        token: 'test_token',
        isAuthenticated: true,
      })

      // Act: Hacer logout
      useAuthStore.getState().logout()

      // Assert
      const state = useAuthStore.getState()
      expect(state.user).toBeNull()
      expect(state.token).toBeNull()
      expect(state.isAuthenticated).toBe(false)
      expect(localStorage.getItem('access_token')).toBeNull()
    })
  })

  describe('Estado de autenticación', () => {
    it('isAuthenticated es true cuando hay token', () => {
      useAuthStore.setState({
        token: 'test_token',
        isAuthenticated: true,
      })

      const state = useAuthStore.getState()
      expect(state.isAuthenticated).toBe(true)
    })

    it('isAuthenticated es false cuando no hay token', () => {
      useAuthStore.setState({
        token: null,
        isAuthenticated: false,
      })

      const state = useAuthStore.getState()
      expect(state.isAuthenticated).toBe(false)
    })
  })

  describe('Usuario', () => {
    it('puede setear usuario', () => {
      const mockUser = createMockUser({
        username: 'testuser',
        email: 'test@example.com',
      })

      useAuthStore.setState({ user: mockUser })

      const state = useAuthStore.getState()
      expect(state.user).toEqual(mockUser)
      expect(state.user?.username).toBe('testuser')
      expect(state.user?.email).toBe('test@example.com')
    })

    it('puede actualizar propiedades del usuario', () => {
      const mockUser = createMockUser({ has_pjn_credentials: false })
      useAuthStore.setState({ user: mockUser })

      // Actualizar credenciales PJN
      useAuthStore.setState({
        user: {
          ...mockUser,
          has_pjn_credentials: true,
        },
      })

      const state = useAuthStore.getState()
      expect(state.user?.has_pjn_credentials).toBe(true)
    })
  })

  describe('Loading state', () => {
    it('puede setear isLoading', () => {
      useAuthStore.setState({ isLoading: true })
      expect(useAuthStore.getState().isLoading).toBe(true)

      useAuthStore.setState({ isLoading: false })
      expect(useAuthStore.getState().isLoading).toBe(false)
    })
  })
})
