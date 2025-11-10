/**
 * Testing utilities
 * Helpers para facilitar la escritura de tests
 */

import { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { vi } from 'vitest'

/**
 * Custom render que incluye providers comunes
 */
export function renderWithRouter(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) {
  return render(ui, {
    wrapper: ({ children }) => <BrowserRouter>{children}</BrowserRouter>,
    ...options,
  })
}

/**
 * Mock de navigate de react-router
 */
export const mockNavigate = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

/**
 * Espera a que un elemento aparezca o desaparezca
 */
export const waitForElementToBeRemoved = async (
  callback: () => HTMLElement | null,
  options?: { timeout?: number }
) => {
  const timeout = options?.timeout || 1000
  const startTime = Date.now()

  while (callback() !== null) {
    if (Date.now() - startTime > timeout) {
      throw new Error('Timeout waiting for element to be removed')
    }
    await new Promise((resolve) => setTimeout(resolve, 50))
  }
}

/**
 * Mock de toast de sonner
 */
export const mockToast = {
  success: vi.fn(),
  error: vi.fn(),
  warning: vi.fn(),
  info: vi.fn(),
  loading: vi.fn(),
  promise: vi.fn(),
  dismiss: vi.fn(),
}

vi.mock('sonner', () => ({
  toast: mockToast,
  Toaster: () => null,
}))

/**
 * Helper para crear mock de usuario
 */
export const createMockUser = (overrides = {}) => ({
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  is_active: true,
  is_superuser: false,
  has_pjn_credentials: false,
  created_at: '2024-01-01T00:00:00Z',
  ...overrides,
})

/**
 * Helper para crear mock de expediente
 */
export const createMockExpediente = (overrides = {}) => ({
  numero: 'ABC123/2024',
  caratula: 'Expediente de prueba',
  dependencia: 'Juzgado Civil 1',
  fecha_inicio: '2024-01-01',
  estado: 'Activo',
  updated_at: '2024-01-01T00:00:00Z',
  ...overrides,
})

/**
 * Helper para crear mock de workspace
 */
export const createMockWorkspace = (overrides = {}) => ({
  id: 1,
  nombre: 'Workspace de prueba',
  descripcion: 'Descripción de prueba',
  color: '#3B82F6',
  icon: 'folder',
  usuario_id: 1,
  expedientes_count: 0,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  ...overrides,
})

/**
 * Helper para limpiar mocks después de cada test
 */
export const clearAllMocks = () => {
  vi.clearAllMocks()
  localStorage.clear()
  mockNavigate.mockClear()
  Object.values(mockToast).forEach((mock) => mock.mockClear())
}
