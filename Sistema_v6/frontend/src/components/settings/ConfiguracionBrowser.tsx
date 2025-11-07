/**
 * ConfiguracionBrowser - Configuración del navegador Playwright
 */

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Globe, Save, Eye, EyeOff, Clock } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { toast } from 'sonner'

// Schema de validación
const browserSchema = z.object({
  headless: z.boolean(),
  timeout_ms: z.number().min(1000).max(300000),
  navigation_timeout_ms: z.number().min(1000).max(300000),
  user_agent: z.string().nullable().optional(),
})

type BrowserForm = z.infer<typeof browserSchema>

export default function ConfiguracionBrowser() {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
    watch,
    reset,
    setValue,
  } = useForm<BrowserForm>({
    resolver: zodResolver(browserSchema),
    defaultValues: {
      headless: true,
      timeout_ms: 30000,
      navigation_timeout_ms: 60000,
      user_agent: null,
    },
  })

  const headlessWatch = watch('headless')

  // Cargar configuración actual del servidor
  useEffect(() => {
    const cargarConfiguracion = async () => {
      try {
        const response = await fetch('/api/v1/config/sistema')
        if (!response.ok) throw new Error('Error al cargar configuración')

        const data = await response.json()
        const browser = data.browser

        setValue('headless', browser.headless)
        setValue('timeout_ms', browser.timeout_ms)
        setValue('navigation_timeout_ms', browser.navigation_timeout_ms)
        setValue('user_agent', browser.user_agent)

        setIsLoading(false)
      } catch (error) {
        console.error('Error cargando configuración:', error)
        toast.error('Error al cargar configuración')
        setIsLoading(false)
      }
    }

    cargarConfiguracion()
  }, [setValue])

  const onSubmit = async (data: BrowserForm) => {
    setIsSubmitting(true)

    try {
      const response = await fetch('/api/v1/config/sistema', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          browser: {
            headless: data.headless,
            timeout_ms: data.timeout_ms,
            navigation_timeout_ms: data.navigation_timeout_ms,
            user_agent: data.user_agent || null,
          },
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Error al actualizar')
      }

      const result = await response.json()

      toast.success('Configuración actualizada', {
        description: result.message,
      })

      reset(data)
    } catch (error: any) {
      console.error('Error al actualizar configuración:', error)
      toast.error('Error al actualizar', {
        description: error.message,
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isLoading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
        </div>
      </Card>
    )
  }

  return (
    <Card className="p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
          <Globe className="h-5 w-5 text-blue-600 dark:text-blue-400" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Configuración del Navegador
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Ajusta el comportamiento de Playwright para scraping del PJN
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Modo Headless */}
        <div>
          <label className="flex items-center justify-between p-4 rounded-lg border border-gray-200 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800">
            <div className="flex items-center gap-3">
              {headlessWatch ? (
                <EyeOff className="h-5 w-5 text-gray-400" />
              ) : (
                <Eye className="h-5 w-5 text-gray-400" />
              )}
              <div>
                <div className="text-sm font-medium text-gray-900 dark:text-white">
                  Modo Headless (sin interfaz gráfica)
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400">
                  {headlessWatch
                    ? 'El navegador se ejecuta en segundo plano sin ventana visible'
                    : 'El navegador mostrará una ventana visible (útil para debugging)'}
                </div>
              </div>
            </div>
            <input
              {...register('headless')}
              type="checkbox"
              className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
            />
          </label>
          <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            ⚠️ Desactivar headless solo para desarrollo/debugging. En producción siempre debe estar activo.
          </p>
        </div>

        {/* Timeouts */}
        <div className="space-y-4">
          <h3 className="text-sm font-medium text-gray-900 dark:text-white flex items-center gap-2">
            <Clock className="h-4 w-4" />
            Timeouts
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Timeout general (ms)
              </label>
              <input
                {...register('timeout_ms', { valueAsNumber: true })}
                type="number"
                min="1000"
                step="1000"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Timeout para operaciones comunes (30000 = 30 segundos)
              </p>
              {errors.timeout_ms && (
                <p className="mt-1 text-xs text-red-600">{errors.timeout_ms.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Timeout de navegación (ms)
              </label>
              <input
                {...register('navigation_timeout_ms', { valueAsNumber: true })}
                type="number"
                min="1000"
                step="1000"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Timeout para carga de páginas (60000 = 1 minuto)
              </p>
              {errors.navigation_timeout_ms && (
                <p className="mt-1 text-xs text-red-600">{errors.navigation_timeout_ms.message}</p>
              )}
            </div>
          </div>
        </div>

        {/* User Agent */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            User Agent personalizado (opcional)
          </label>
          <input
            {...register('user_agent')}
            type="text"
            placeholder="Dejar vacío para usar el User Agent por defecto de Playwright"
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          />
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            Ejemplo: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...
          </p>
          {errors.user_agent && (
            <p className="mt-1 text-xs text-red-600">{errors.user_agent.message}</p>
          )}
        </div>

        {/* Información adicional */}
        <div className="p-4 bg-blue-50 dark:bg-blue-900/10 rounded-lg border border-blue-200 dark:border-blue-800">
          <h4 className="text-sm font-medium text-blue-900 dark:text-blue-300 mb-2">
            ℹ️ Información sobre timeouts
          </h4>
          <ul className="space-y-1 text-xs text-blue-800 dark:text-blue-400">
            <li>• <strong>Timeout general:</strong> Aplica a elementos del DOM, espera de selectores, etc.</li>
            <li>• <strong>Timeout de navegación:</strong> Aplica a page.goto(), navegación entre páginas, redirects.</li>
            <li>• Si experimentas errores de timeout, aumenta estos valores gradualmente.</li>
            <li>• Valores muy altos pueden hacer que el scraping sea más lento.</li>
          </ul>
        </div>

        {/* Botón Guardar */}
        <div className="flex justify-end pt-4 border-t border-gray-200 dark:border-gray-700">
          <Button
            type="submit"
            disabled={!isDirty || isSubmitting}
            className="flex items-center gap-2"
          >
            <Save className="h-4 w-4" />
            {isSubmitting ? 'Guardando...' : 'Guardar configuración'}
          </Button>
        </div>
      </form>
    </Card>
  )
}
