/**
 * CambiarPassword - Componente para cambiar la contraseña del usuario
 */

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Lock, Eye, EyeOff, Save } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { toast } from 'sonner'

// Schema de validación
const passwordSchema = z.object({
  current_password: z
    .string()
    .min(8, 'La contraseña debe tener al menos 8 caracteres'),
  new_password: z
    .string()
    .min(8, 'La contraseña nueva debe tener al menos 8 caracteres')
    .max(100, 'La contraseña no puede superar los 100 caracteres'),
  confirm_password: z
    .string()
    .min(8, 'Confirma la contraseña nueva'),
}).refine((data) => data.new_password === data.confirm_password, {
  message: 'Las contraseñas no coinciden',
  path: ['confirm_password'],
})

type PasswordForm = z.infer<typeof passwordSchema>

export default function CambiarPassword() {
  const [showCurrentPassword, setShowCurrentPassword] = useState(false)
  const [showNewPassword, setShowNewPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<PasswordForm>({
    resolver: zodResolver(passwordSchema),
    defaultValues: {
      current_password: '',
      new_password: '',
      confirm_password: '',
    },
  })

  const onSubmit = async (data: PasswordForm) => {
    setIsSubmitting(true)

    try {
      // TODO: Reemplazar con llamada real a la API
      // await apiClient.put('/api/v1/auth/change-password', {
      //   current_password: data.current_password,
      //   new_password: data.new_password,
      // })

      // Mock data por ahora
      await new Promise(resolve => setTimeout(resolve, 1000))

      toast.success('Contraseña actualizada', {
        description: 'Tu contraseña se cambió correctamente',
      })

      reset()
    } catch (error: any) {
      console.error('Error al cambiar contraseña:', error)
      toast.error('Error al cambiar contraseña', {
        description: error.response?.data?.detail || 'Verifica tu contraseña actual',
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Card className="p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-purple-100 dark:bg-purple-900/20 rounded-lg">
          <Lock className="h-5 w-5 text-purple-600 dark:text-purple-400" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Cambiar Contraseña
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Actualiza tu contraseña de acceso al sistema
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Contraseña actual */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Contraseña actual
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Lock className="h-5 w-5 text-gray-400" />
            </div>
            <Input
              {...register('current_password')}
              type={showCurrentPassword ? 'text' : 'password'}
              placeholder="Ingresa tu contraseña actual"
              disabled={isSubmitting}
              className={`pl-10 pr-10 ${errors.current_password ? 'border-red-500' : ''}`}
              autoComplete="current-password"
            />
            <button
              type="button"
              onClick={() => setShowCurrentPassword(!showCurrentPassword)}
              className="absolute inset-y-0 right-0 pr-3 flex items-center"
            >
              {showCurrentPassword ? (
                <EyeOff className="h-5 w-5 text-gray-400 hover:text-gray-600" />
              ) : (
                <Eye className="h-5 w-5 text-gray-400 hover:text-gray-600" />
              )}
            </button>
          </div>
          {errors.current_password && (
            <p className="mt-1 text-sm text-red-600 dark:text-red-400">
              {errors.current_password.message}
            </p>
          )}
        </div>

        {/* Contraseña nueva */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Contraseña nueva
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Lock className="h-5 w-5 text-gray-400" />
            </div>
            <Input
              {...register('new_password')}
              type={showNewPassword ? 'text' : 'password'}
              placeholder="Ingresa tu contraseña nueva"
              disabled={isSubmitting}
              className={`pl-10 pr-10 ${errors.new_password ? 'border-red-500' : ''}`}
              autoComplete="new-password"
            />
            <button
              type="button"
              onClick={() => setShowNewPassword(!showNewPassword)}
              className="absolute inset-y-0 right-0 pr-3 flex items-center"
            >
              {showNewPassword ? (
                <EyeOff className="h-5 w-5 text-gray-400 hover:text-gray-600" />
              ) : (
                <Eye className="h-5 w-5 text-gray-400 hover:text-gray-600" />
              )}
            </button>
          </div>
          {errors.new_password && (
            <p className="mt-1 text-sm text-red-600 dark:text-red-400">
              {errors.new_password.message}
            </p>
          )}
        </div>

        {/* Confirmar contraseña */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Confirmar contraseña nueva
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Lock className="h-5 w-5 text-gray-400" />
            </div>
            <Input
              {...register('confirm_password')}
              type={showConfirmPassword ? 'text' : 'password'}
              placeholder="Confirma tu contraseña nueva"
              disabled={isSubmitting}
              className={`pl-10 pr-10 ${errors.confirm_password ? 'border-red-500' : ''}`}
              autoComplete="new-password"
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              className="absolute inset-y-0 right-0 pr-3 flex items-center"
            >
              {showConfirmPassword ? (
                <EyeOff className="h-5 w-5 text-gray-400 hover:text-gray-600" />
              ) : (
                <Eye className="h-5 w-5 text-gray-400 hover:text-gray-600" />
              )}
            </button>
          </div>
          {errors.confirm_password && (
            <p className="mt-1 text-sm text-red-600 dark:text-red-400">
              {errors.confirm_password.message}
            </p>
          )}
        </div>

        {/* Recomendaciones de seguridad */}
        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
          <p className="text-sm font-medium text-gray-900 dark:text-white mb-2">
            Recomendaciones de seguridad:
          </p>
          <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1 list-disc list-inside">
            <li>Usa al menos 8 caracteres</li>
            <li>Combina mayúsculas, minúsculas, números y símbolos</li>
            <li>No uses contraseñas obvias o fáciles de adivinar</li>
            <li>No compartas tu contraseña con nadie</li>
          </ul>
        </div>

        {/* Botón Guardar */}
        <div className="flex justify-end pt-4 border-t border-gray-200 dark:border-gray-700">
          <Button type="submit" disabled={isSubmitting}>
            <Save className="h-4 w-4 mr-2" />
            {isSubmitting ? 'Cambiando contraseña...' : 'Cambiar contraseña'}
          </Button>
        </div>
      </form>
    </Card>
  )
}
