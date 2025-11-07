/**
 * Tests para toast utilities
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { toast as sonnerToast } from 'sonner'
import { toast } from '../toast'

// Mock de sonner
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
    loading: vi.fn(),
    promise: vi.fn(),
    dismiss: vi.fn(),
  },
}))

describe('toast utilities', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('CRUD operations', () => {
    it('created llama sonner.success con mensaje correcto', () => {
      toast.created('Expediente', 'ABC123/2024')

      expect(sonnerToast.success).toHaveBeenCalledWith('Expediente creado', {
        description: '"ABC123/2024" fue creado correctamente',
      })
    })

    it('created funciona sin nombre', () => {
      toast.created('Expediente')

      expect(sonnerToast.success).toHaveBeenCalledWith('Expediente creado', {
        description: 'Creado correctamente',
      })
    })

    it('updated llama sonner.success con mensaje correcto', () => {
      toast.updated('Workspace', 'Mi Workspace')

      expect(sonnerToast.success).toHaveBeenCalledWith('Workspace actualizado', {
        description: '"Mi Workspace" fue actualizado correctamente',
      })
    })

    it('deleted llama sonner.success con mensaje correcto', () => {
      toast.deleted('Monitoreo', 'XYZ456/2024')

      expect(sonnerToast.success).toHaveBeenCalledWith('Monitoreo eliminado', {
        description: '"XYZ456/2024" fue eliminado correctamente',
      })
    })
  })

  describe('Generic toasts', () => {
    it('success llama sonner.success', () => {
      toast.success('Operación exitosa', 'Todo salió bien')

      expect(sonnerToast.success).toHaveBeenCalledWith('Operación exitosa', {
        description: 'Todo salió bien',
      })
    })

    it('error llama sonner.error', () => {
      toast.error('Error al procesar', 'Intenta nuevamente')

      expect(sonnerToast.error).toHaveBeenCalledWith('Error al procesar', {
        description: 'Intenta nuevamente',
      })
    })

    it('error tiene descripción por defecto', () => {
      toast.error('Error al procesar')

      expect(sonnerToast.error).toHaveBeenCalledWith('Error al procesar', {
        description: 'Por favor intenta nuevamente',
      })
    })

    it('warning llama sonner.warning', () => {
      toast.warning('Advertencia', 'Revisa los datos')

      expect(sonnerToast.warning).toHaveBeenCalledWith('Advertencia', {
        description: 'Revisa los datos',
      })
    })

    it('info llama sonner.info', () => {
      toast.info('Información', 'Dato relevante')

      expect(sonnerToast.info).toHaveBeenCalledWith('Información', {
        description: 'Dato relevante',
      })
    })

    it('loading llama sonner.loading', () => {
      toast.loading('Procesando...')

      expect(sonnerToast.loading).toHaveBeenCalledWith('Procesando...', {
        description: 'Por favor espera...',
      })
    })
  })

  describe('Auth operations', () => {
    it('auth.loginSuccess muestra mensaje correcto', () => {
      toast.auth.loginSuccess('admin')

      expect(sonnerToast.success).toHaveBeenCalledWith('Sesión iniciada', {
        description: 'Bienvenido, admin',
      })
    })

    it('auth.logoutSuccess muestra mensaje correcto', () => {
      toast.auth.logoutSuccess()

      expect(sonnerToast.info).toHaveBeenCalledWith('Sesión cerrada', {
        description: 'Hasta pronto',
      })
    })

    it('auth.registerSuccess muestra mensaje correcto', () => {
      toast.auth.registerSuccess()

      expect(sonnerToast.success).toHaveBeenCalledWith('Cuenta creada', {
        description: 'Iniciando sesión...',
      })
    })

    it('auth.passwordChanged muestra mensaje correcto', () => {
      toast.auth.passwordChanged()

      expect(sonnerToast.success).toHaveBeenCalledWith('Contraseña actualizada', {
        description: 'Tu contraseña se cambió correctamente',
      })
    })

    it('auth.credentialsUpdated muestra mensaje correcto', () => {
      toast.auth.credentialsUpdated()

      expect(sonnerToast.success).toHaveBeenCalledWith('Credenciales actualizadas', {
        description: 'Tus credenciales PJN se guardaron de forma segura',
      })
    })
  })

  describe('Expediente operations', () => {
    it('expediente.extracted muestra mensaje correcto', () => {
      toast.expediente.extracted('ABC123/2024')

      expect(sonnerToast.success).toHaveBeenCalledWith('Expediente extraído', {
        description: 'Expediente ABC123/2024 descargado correctamente',
      })
    })

    it('expediente.extracting muestra mensaje de loading', () => {
      toast.expediente.extracting('ABC123/2024')

      expect(sonnerToast.loading).toHaveBeenCalledWith('Extrayendo expediente', {
        description: 'Descargando ABC123/2024 del PJN...',
      })
    })

    it('expediente.notFound muestra mensaje de error', () => {
      toast.expediente.notFound('ABC123/2024')

      expect(sonnerToast.error).toHaveBeenCalledWith('Expediente no encontrado', {
        description: 'El expediente ABC123/2024 no existe o no es accesible',
      })
    })
  })

  describe('Workspace operations', () => {
    it('workspace.created muestra mensaje correcto', () => {
      toast.workspace.created('Mi Workspace')

      expect(sonnerToast.success).toHaveBeenCalledWith('Workspace creado', {
        description: '"Mi Workspace" fue creado correctamente',
      })
    })

    it('workspace.expedienteAdded muestra mensaje correcto', () => {
      toast.workspace.expedienteAdded('ABC123/2024', 'Mi Workspace')

      expect(sonnerToast.success).toHaveBeenCalledWith('Expediente agregado', {
        description: 'ABC123/2024 fue agregado a "Mi Workspace"',
      })
    })
  })

  describe('Monitoreo operations', () => {
    it('monitoreo.started muestra mensaje correcto', () => {
      toast.monitoreo.started('ABC123/2024')

      expect(sonnerToast.success).toHaveBeenCalledWith('Monitoreo iniciado', {
        description: 'ABC123/2024 está siendo monitoreado',
      })
    })

    it('monitoreo.cambioDetectado muestra warning', () => {
      toast.monitoreo.cambioDetectado('ABC123/2024', 'Nueva actuación')

      expect(sonnerToast.warning).toHaveBeenCalledWith('Cambio detectado', {
        description: 'Nueva actuación en ABC123/2024',
      })
    })

    it('monitoreo.verified muestra mensaje correcto', () => {
      toast.monitoreo.verified('ABC123/2024')

      expect(sonnerToast.success).toHaveBeenCalledWith('Verificación completa', {
        description: 'ABC123/2024 no tiene cambios nuevos',
      })
    })
  })

  describe('Utilities', () => {
    it('promise llama sonner.promise', () => {
      const mockPromise = Promise.resolve('success')
      const messages = {
        loading: 'Loading...',
        success: 'Success!',
        error: 'Error!',
      }

      toast.promise(mockPromise, messages)

      expect(sonnerToast.promise).toHaveBeenCalledWith(mockPromise, messages)
    })

    it('dismiss llama sonner.dismiss', () => {
      toast.dismiss()
      expect(sonnerToast.dismiss).toHaveBeenCalledWith(undefined)

      toast.dismiss('toast-id')
      expect(sonnerToast.dismiss).toHaveBeenCalledWith('toast-id')
    })
  })
})
