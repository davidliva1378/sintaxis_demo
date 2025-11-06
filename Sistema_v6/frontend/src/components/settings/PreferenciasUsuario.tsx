/**
 * PreferenciasUsuario - Componente para gestionar preferencias de la aplicación
 */

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Settings, Save, Moon, Sun, Bell, Mail, Clock } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { toast } from 'sonner'

// Schema de validación
const preferenciasSchema = z.object({
  tema: z.enum(['claro', 'oscuro', 'sistema']),
  notificaciones_email: z.boolean(),
  notificaciones_push: z.boolean(),
  notificaciones_cambios: z.boolean(),
  zona_horaria: z.string(),
  idioma: z.enum(['es', 'en']),
})

type PreferenciasForm = z.infer<typeof preferenciasSchema>

export default function PreferenciasUsuario() {
  const [isSubmitting, setIsSubmitting] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
    watch,
    reset,
  } = useForm<PreferenciasForm>({
    resolver: zodResolver(preferenciasSchema),
    defaultValues: {
      tema: 'sistema',
      notificaciones_email: true,
      notificaciones_push: false,
      notificaciones_cambios: true,
      zona_horaria: 'America/Argentina/Buenos_Aires',
      idioma: 'es',
    },
  })

  const temaActual = watch('tema')

  const onSubmit = async (data: PreferenciasForm) => {
    setIsSubmitting(true)

    try {
      // TODO: Reemplazar con llamada real a la API
      // await apiClient.put('/api/v1/usuarios/preferencias', data)

      // Mock data por ahora
      await new Promise(resolve => setTimeout(resolve, 1000))

      toast.success('Preferencias actualizadas', {
        description: 'Tus preferencias se guardaron correctamente',
      })

      reset(data)
    } catch (error: any) {
      console.error('Error al actualizar preferencias:', error)
      toast.error('Error al actualizar preferencias', {
        description: error.response?.data?.detail || 'Intenta nuevamente',
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Card className="p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-indigo-100 dark:bg-indigo-900/20 rounded-lg">
          <Settings className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Preferencias de la Aplicación
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Personaliza tu experiencia en el sistema
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Tema */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Tema de la aplicación
          </label>
          <div className="grid grid-cols-3 gap-3">
            <label
              className={`
                relative flex flex-col items-center gap-2 p-4 rounded-lg border-2 cursor-pointer transition-all
                ${temaActual === 'claro'
                  ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'}
              `}
            >
              <input
                {...register('tema')}
                type="radio"
                value="claro"
                className="sr-only"
              />
              <Sun className={`h-6 w-6 ${temaActual === 'claro' ? 'text-blue-600' : 'text-gray-400'}`} />
              <span className={`text-sm font-medium ${temaActual === 'claro' ? 'text-blue-600' : 'text-gray-700 dark:text-gray-300'}`}>
                Claro
              </span>
            </label>

            <label
              className={`
                relative flex flex-col items-center gap-2 p-4 rounded-lg border-2 cursor-pointer transition-all
                ${temaActual === 'oscuro'
                  ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'}
              `}
            >
              <input
                {...register('tema')}
                type="radio"
                value="oscuro"
                className="sr-only"
              />
              <Moon className={`h-6 w-6 ${temaActual === 'oscuro' ? 'text-blue-600' : 'text-gray-400'}`} />
              <span className={`text-sm font-medium ${temaActual === 'oscuro' ? 'text-blue-600' : 'text-gray-700 dark:text-gray-300'}`}>
                Oscuro
              </span>
            </label>

            <label
              className={`
                relative flex flex-col items-center gap-2 p-4 rounded-lg border-2 cursor-pointer transition-all
                ${temaActual === 'sistema'
                  ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'}
              `}
            >
              <input
                {...register('tema')}
                type="radio"
                value="sistema"
                className="sr-only"
              />
              <Settings className={`h-6 w-6 ${temaActual === 'sistema' ? 'text-blue-600' : 'text-gray-400'}`} />
              <span className={`text-sm font-medium ${temaActual === 'sistema' ? 'text-blue-600' : 'text-gray-700 dark:text-gray-300'}`}>
                Sistema
              </span>
            </label>
          </div>
        </div>

        {/* Notificaciones */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Notificaciones
          </label>
          <div className="space-y-3">
            <label className="flex items-center justify-between p-4 rounded-lg border border-gray-200 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800">
              <div className="flex items-center gap-3">
                <Mail className="h-5 w-5 text-gray-400" />
                <div>
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    Notificaciones por email
                  </div>
                  <div className="text-xs text-gray-600 dark:text-gray-400">
                    Recibe resúmenes diarios por correo electrónico
                  </div>
                </div>
              </div>
              <input
                {...register('notificaciones_email')}
                type="checkbox"
                className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
              />
            </label>

            <label className="flex items-center justify-between p-4 rounded-lg border border-gray-200 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800">
              <div className="flex items-center gap-3">
                <Bell className="h-5 w-5 text-gray-400" />
                <div>
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    Notificaciones push
                  </div>
                  <div className="text-xs text-gray-600 dark:text-gray-400">
                    Recibe alertas en tiempo real en el navegador
                  </div>
                </div>
              </div>
              <input
                {...register('notificaciones_push')}
                type="checkbox"
                className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
              />
            </label>

            <label className="flex items-center justify-between p-4 rounded-lg border border-gray-200 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800">
              <div className="flex items-center gap-3">
                <Bell className="h-5 w-5 text-gray-400" />
                <div>
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    Notificar cambios en expedientes
                  </div>
                  <div className="text-xs text-gray-600 dark:text-gray-400">
                    Alerta cuando haya cambios en expedientes monitoreados
                  </div>
                </div>
              </div>
              <input
                {...register('notificaciones_cambios')}
                type="checkbox"
                className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
              />
            </label>
          </div>
        </div>

        {/* Zona Horaria */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Zona horaria
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Clock className="h-5 w-5 text-gray-400" />
            </div>
            <select
              {...register('zona_horaria')}
              disabled={isSubmitting}
              className="pl-10 w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="America/Argentina/Buenos_Aires">Argentina (Buenos Aires)</option>
              <option value="America/Argentina/Cordoba">Argentina (Córdoba)</option>
              <option value="America/Argentina/Mendoza">Argentina (Mendoza)</option>
              <option value="America/Montevideo">Uruguay (Montevideo)</option>
              <option value="America/Santiago">Chile (Santiago)</option>
              <option value="America/Sao_Paulo">Brasil (São Paulo)</option>
              <option value="America/Mexico_City">México (Ciudad de México)</option>
              <option value="America/New_York">Estados Unidos (New York)</option>
              <option value="Europe/Madrid">España (Madrid)</option>
            </select>
          </div>
        </div>

        {/* Idioma */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Idioma de la aplicación
          </label>
          <div className="flex gap-3">
            <label
              className={`
                flex-1 flex items-center justify-center gap-2 p-3 rounded-lg border-2 cursor-pointer transition-all
                ${watch('idioma') === 'es'
                  ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'}
              `}
            >
              <input
                {...register('idioma')}
                type="radio"
                value="es"
                className="sr-only"
              />
              <span className={`text-sm font-medium ${watch('idioma') === 'es' ? 'text-blue-600' : 'text-gray-700 dark:text-gray-300'}`}>
                🇦🇷 Español
              </span>
              {watch('idioma') === 'es' && (
                <Badge variant="default" className="bg-blue-600 text-xs">
                  Actual
                </Badge>
              )}
            </label>

            <label
              className={`
                flex-1 flex items-center justify-center gap-2 p-3 rounded-lg border-2 cursor-pointer transition-all
                ${watch('idioma') === 'en'
                  ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'}
              `}
            >
              <input
                {...register('idioma')}
                type="radio"
                value="en"
                className="sr-only"
              />
              <span className={`text-sm font-medium ${watch('idioma') === 'en' ? 'text-blue-600' : 'text-gray-700 dark:text-gray-300'}`}>
                🇺🇸 English
              </span>
              {watch('idioma') === 'en' && (
                <Badge variant="default" className="bg-blue-600 text-xs">
                  Current
                </Badge>
              )}
            </label>
          </div>
          <p className="mt-2 text-xs text-gray-600 dark:text-gray-400">
            Nota: El idioma inglés estará disponible en una versión futura
          </p>
        </div>

        {/* Botón Guardar */}
        <div className="flex justify-end pt-4 border-t border-gray-200 dark:border-gray-700">
          <Button
            type="submit"
            disabled={!isDirty || isSubmitting}
          >
            <Save className="h-4 w-4 mr-2" />
            {isSubmitting ? 'Guardando...' : 'Guardar preferencias'}
          </Button>
        </div>
      </form>
    </Card>
  )
}
