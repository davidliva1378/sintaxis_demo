import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { toast } from 'sonner'
import apiClient from '@/lib/api'
import { encryptText } from '@/lib/encryption'
import type { User, TokenResponse } from '@/types/auth'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean

  login: (username: string, password: string) => Promise<void>
  register: (username: string, email: string, password: string) => Promise<void>
  logout: () => void
  fetchUser: () => Promise<void>
  updatePJNCredentials: (usuario: string, password: string) => Promise<void>
  deletePJNCredentials: () => Promise<void>
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: localStorage.getItem('access_token'),
      isAuthenticated: !!localStorage.getItem('access_token'),
      isLoading: false,

      login: async (username: string, password: string) => {
        set({ isLoading: true })
        try {
          const params = new URLSearchParams()
          params.append('username', username)
          params.append('password', password)

          const response = await apiClient.post<TokenResponse>('/api/v1/auth/login', params, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          })

          const { access_token } = response.data
          localStorage.setItem('access_token', access_token)
          set({ token: access_token, isAuthenticated: true })

          await get().fetchUser()
          toast.success('Sesión iniciada correctamente', {
            description: `Bienvenido, ${username}`,
          })
        } finally {
          set({ isLoading: false })
        }
      },

      register: async (username: string, email: string, password: string) => {
        set({ isLoading: true })
        try {
          await apiClient.post('/api/v1/auth/register', {
            username,
            email,
            password,
          })

          toast.success('Cuenta creada exitosamente', {
            description: 'Iniciando sesión...',
          })

          // Auto-login después de registro
          await get().login(username, password)
        } finally {
          set({ isLoading: false })
        }
      },

      logout: () => {
        localStorage.removeItem('access_token')
        set({ user: null, token: null, isAuthenticated: false })
        toast.info('Sesión cerrada', {
          description: 'Hasta pronto',
        })
      },

      fetchUser: async () => {
        try {
          const response = await apiClient.get<User>('/api/v1/auth/me')
          set({ user: response.data })
        } catch (error) {
          // Si falla, hacer logout
          get().logout()
          throw error
        }
      },

      updatePJNCredentials: async (usuario: string, password: string) => {
        try {
          // Encriptar credenciales en el cliente antes de enviar
          const encryptedUsuario = encryptText(usuario)
          const encryptedPassword = encryptText(password)

          const response = await apiClient.put<User>('/api/v1/auth/credentials', {
            pjn_usuario_encrypted: encryptedUsuario,
            pjn_password_encrypted: encryptedPassword,
          })

          set({ user: response.data })
          toast.success('Credenciales PJN actualizadas', {
            description: 'Las credenciales se guardaron correctamente',
          })
        } catch (error) {
          toast.error('Error al actualizar credenciales', {
            description: 'No se pudieron guardar las credenciales PJN',
          })
          throw error
        }
      },

      deletePJNCredentials: async () => {
        try {
          await apiClient.delete('/api/v1/auth/credentials')

          // Update user to reflect credentials deleted
          if (get().user) {
            set({
              user: {
                ...get().user!,
                has_pjn_credentials: false
              }
            })
          }

          toast.success('Credenciales PJN eliminadas', {
            description: 'Las credenciales se eliminaron correctamente',
          })
        } catch (error) {
          toast.error('Error al eliminar credenciales', {
            description: 'No se pudieron eliminar las credenciales PJN',
          })
          throw error
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ token: state.token }),
    }
  )
)
