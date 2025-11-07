/**
 * PerfilUsuario - Componente para editar información del perfil
 */

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { User, Mail, Save, Loader2 } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAuthStore } from '@/stores/authStore'
import { toast } from 'sonner'

// Schema de validación
const perfilSchema = z.object({
  username: z
    .string()
    .min(3, 'El nombre de usuario debe tener al menos 3 caracteres')
    .max(50, 'El nombre de usuario no puede superar los 50 caracteres'),
  email: z
    .string()
    .email('Ingresa un email válido')
    .max(255, 'El email no puede superar los 255 caracteres'),
})

type PerfilForm = z.infer<typeof perfilSchema>

export default function PerfilUsuario() {
  const { user, fetchUser } = useAuthStore()
  const [isSubmitting, setIsSubmitting] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
    reset,
  } = useForm<PerfilForm>({
    resolver: zodResolver(perfilSchema),
    defaultValues: {
      username: '',
      email: '',
    },
  })

  useEffect(() => {
    if (user) {
      reset({
        username: user.username,
        email: user.email,
      })
    }
  }, [user, reset])

  const onSubmit = async (data: PerfilForm) => {
    setIsSubmitting(true)

    try {
      // TODO: Reemplazar con llamada real a la API
      // await apiClient.put('/api/v1/auth/profile', data)

      // Mock data por ahora
      await new Promise(resolve => setTimeout(resolve, 1000))

      await fetchUser()

      toast.success('Perfil actualizado', {
        description: 'Tus datos se actualizaron correctamente',
      })

      reset(data)
    } catch (error: any) {
      console.error('Error al actualizar perfil:', error)
      toast.error('Error al actualizar perfil', {
        description: error.response?.data?.detail || 'Intenta nuevamente',
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!user) {
    return (
      <Card className="p-6">
        <div className="text-center py-4 text-gray-500 dark:text-gray-400">
          Cargando información del usuario...
        </div>
      </Card>
    )
  }

  return (
    <Card className="p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
          <User className="h-5 w-5 text-blue-600 dark:text-blue-400" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Información del Perfil
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Actualiza tu información personal
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Username */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Nombre de usuario
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <User className="h-5 w-5 text-gray-400" />
            </div>
            <Input
              {...register('username')}
              placeholder="usuario"
              disabled={isSubmitting}
              className={`pl-10 ${errors.username ? 'border-red-500' : ''}`}
            />
          </div>
          {errors.username && (
            <p className="mt-1 text-sm text-red-600 dark:text-red-400">
              {errors.username.message}
            </p>
          )}
        </div>

        {/* Email */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Email
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Mail className="h-5 w-5 text-gray-400" />
            </div>
            <Input
              {...register('email')}
              type="email"
              placeholder="usuario@email.com"
              disabled={isSubmitting}
              className={`pl-10 ${errors.email ? 'border-red-500' : ''}`}
            />
          </div>
          {errors.email && (
            <p className="mt-1 text-sm text-red-600 dark:text-red-400">
              {errors.email.message}
            </p>
          )}
        </div>

        {/* Info adicional */}
        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Estado:</span>
              <span className="font-medium text-gray-900 dark:text-white">
                {user.is_active ? '✓ Activo' : '✗ Inactivo'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Rol:</span>
              <span className="font-medium text-gray-900 dark:text-white">
                {user.is_superuser ? 'Administrador' : 'Usuario'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Credenciales PJN:</span>
              <span className="font-medium text-gray-900 dark:text-white">
                {user.has_pjn_credentials ? '✓ Configuradas' : '✗ Sin configurar'}
              </span>
            </div>
          </div>
        </div>

        {/* Botón Guardar */}
        <div className="flex justify-end pt-4 border-t border-gray-200 dark:border-gray-700">
          <Button
            type="submit"
            disabled={!isDirty || isSubmitting}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Guardando...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                Guardar cambios
              </>
            )}
          </Button>
        </div>
      </form>
    </Card>
  )
}
