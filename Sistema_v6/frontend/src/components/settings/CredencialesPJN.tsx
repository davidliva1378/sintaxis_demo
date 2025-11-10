/**
 * CredencialesPJN - Componente para gestionar credenciales del Portal Judicial
 */

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Key, Eye, EyeOff, Save, Trash2, Shield, AlertCircle } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { useAuthStore } from '@/stores/authStore'

// Schema de validación
const credencialesSchema = z.object({
  pjn_usuario: z
    .string()
    .min(3, 'El usuario debe tener al menos 3 caracteres')
    .max(100, 'El usuario no puede superar los 100 caracteres'),
  pjn_password: z
    .string()
    .min(6, 'La contraseña debe tener al menos 6 caracteres')
    .max(100, 'La contraseña no puede superar los 100 caracteres'),
})

type CredencialesForm = z.infer<typeof credencialesSchema>

export default function CredencialesPJN() {
  const { user, updatePJNCredentials, fetchUser } = useAuthStore()
  const [showPassword, setShowPassword] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
    reset,
  } = useForm<CredencialesForm>({
    resolver: zodResolver(credencialesSchema),
    defaultValues: {
      pjn_usuario: '',
      pjn_password: '',
    },
  })

  const onSubmit = async (data: CredencialesForm) => {
    setIsSubmitting(true)

    try {
      // Las credenciales se encriptan en el store antes de enviar
      await updatePJNCredentials(data.pjn_usuario, data.pjn_password)

      await fetchUser()

      reset({
        pjn_usuario: '',
        pjn_password: '',
      })
    } catch (error: any) {
      console.error('Error al actualizar credenciales:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDelete = async () => {
    if (
      !confirm(
        '¿Estás seguro de eliminar las credenciales del PJN?\n\nNo podrás extraer ni monitorear expedientes hasta que las configures nuevamente.'
      )
    ) {
      return
    }

    setIsDeleting(true)

    try {
      // TODO: Reemplazar con llamada real a la API
      // await apiClient.delete('/api/v1/auth/credentials')

      // Mock data por ahora
      await new Promise(resolve => setTimeout(resolve, 500))

      await fetchUser()
    } catch (error: any) {
      console.error('Error al eliminar credenciales:', error)
    } finally {
      setIsDeleting(false)
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
        <div className="p-2 bg-green-100 dark:bg-green-900/20 rounded-lg">
          <Shield className="h-5 w-5 text-green-600 dark:text-green-400" />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Credenciales Portal Judicial
            </h2>
            <Badge
              variant={user.has_pjn_credentials ? 'default' : 'outline'}
              className={
                user.has_pjn_credentials
                  ? 'bg-green-600'
                  : 'border-orange-600 text-orange-600 dark:text-orange-400'
              }
            >
              {user.has_pjn_credentials ? 'Configuradas' : 'Sin configurar'}
            </Badge>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Credenciales para acceder al Portal Judicial Nacional
          </p>
        </div>
      </div>

      {/* Alerta de seguridad */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6">
        <div className="flex gap-3">
          <AlertCircle className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-900 dark:text-blue-200">
            <p className="font-medium mb-1">Seguridad de credenciales</p>
            <p className="text-blue-800 dark:text-blue-300">
              Tus credenciales se almacenan encriptadas con AES-256 y solo se desencriptan
              cuando es necesario acceder al Portal Judicial. Nunca se muestran en texto plano.
            </p>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Usuario PJN */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Usuario PJN
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Key className="h-5 w-5 text-gray-400" />
            </div>
            <Input
              {...register('pjn_usuario')}
              placeholder="Tu usuario del Portal Judicial"
              disabled={isSubmitting}
              className={`pl-10 ${errors.pjn_usuario ? 'border-red-500' : ''}`}
              autoComplete="off"
            />
          </div>
          {errors.pjn_usuario && (
            <p className="mt-1 text-sm text-red-600 dark:text-red-400">
              {errors.pjn_usuario.message}
            </p>
          )}
        </div>

        {/* Contraseña PJN */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Contraseña PJN
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Key className="h-5 w-5 text-gray-400" />
            </div>
            <Input
              {...register('pjn_password')}
              type={showPassword ? 'text' : 'password'}
              placeholder="Tu contraseña del Portal Judicial"
              disabled={isSubmitting}
              className={`pl-10 pr-10 ${errors.pjn_password ? 'border-red-500' : ''}`}
              autoComplete="off"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute inset-y-0 right-0 pr-3 flex items-center"
            >
              {showPassword ? (
                <EyeOff className="h-5 w-5 text-gray-400 hover:text-gray-600" />
              ) : (
                <Eye className="h-5 w-5 text-gray-400 hover:text-gray-600" />
              )}
            </button>
          </div>
          {errors.pjn_password && (
            <p className="mt-1 text-sm text-red-600 dark:text-red-400">
              {errors.pjn_password.message}
            </p>
          )}
        </div>

        {/* Info adicional */}
        {user.has_pjn_credentials && (
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Ya tienes credenciales configuradas. Si ingresas nuevas credenciales, las anteriores
              serán reemplazadas.
            </p>
          </div>
        )}

        {/* Botones */}
        <div className="flex gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
          {user.has_pjn_credentials && (
            <Button
              type="button"
              variant="outline"
              onClick={handleDelete}
              disabled={isDeleting || isSubmitting}
              className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              {isDeleting ? 'Eliminando...' : 'Eliminar credenciales'}
            </Button>
          )}

          <Button
            type="submit"
            disabled={!isDirty || isSubmitting}
            className="ml-auto"
          >
            <Save className="h-4 w-4 mr-2" />
            {isSubmitting ? 'Guardando...' : 'Guardar credenciales'}
          </Button>
        </div>
      </form>
    </Card>
  )
}
