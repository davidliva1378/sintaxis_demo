/**
 * ConfiguracionScraping - Configuración de extracción de datos del PJN
 */

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Download, Save, Clock, RefreshCw, FileText } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { toast } from 'sonner'

// Schema de validación
const scrapingSchema = z.object({
  timeout_default: z.number().min(1000).max(300000),
  timeout_login: z.number().min(1000).max(300000),
  timeout_descarga: z.number().min(1000).max(300000),
  max_paginas_expedientes: z.number().min(1).max(10000).nullable().optional(),
  max_reintentos_descarga: z.number().min(1).max(10),
})

type ScrapingForm = z.infer<typeof scrapingSchema>

export default function ConfiguracionScraping() {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
    reset,
    setValue,
    watch,
  } = useForm<ScrapingForm>({
    resolver: zodResolver(scrapingSchema),
    defaultValues: {
      timeout_default: 8000,
      timeout_login: 60000,
      timeout_descarga: 30000,
      max_paginas_expedientes: 200,
      max_reintentos_descarga: 3,
    },
  })

  const sinLimite = watch('max_paginas_expedientes') === null

  // Cargar configuración actual del servidor
  useEffect(() => {
    const cargarConfiguracion = async () => {
      try {
        const response = await fetch('/api/v1/config/sistema')
        if (!response.ok) throw new Error('Error al cargar configuración')

        const data = await response.json()
        const scraping = data.scraping

        setValue('timeout_default', scraping.timeout_default)
        setValue('timeout_login', scraping.timeout_login)
        setValue('timeout_descarga', scraping.timeout_descarga)
        setValue('max_paginas_expedientes', scraping.max_paginas_expedientes)
        setValue('max_reintentos_descarga', scraping.max_reintentos_descarga)

        setIsLoading(false)
      } catch (error) {
        console.error('Error cargando configuración:', error)
        toast.error('Error al cargar configuración')
        setIsLoading(false)
      }
    }

    cargarConfiguracion()
  }, [setValue])

  const onSubmit = async (data: ScrapingForm) => {
    setIsSubmitting(true)

    try {
      const response = await fetch('/api/v1/config/sistema', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scraping: {
            timeout_default: data.timeout_default,
            timeout_login: data.timeout_login,
            timeout_descarga: data.timeout_descarga,
            max_paginas_expedientes: data.max_paginas_expedientes,
            max_reintentos_descarga: data.max_reintentos_descarga,
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

  const handleToggleLimite = () => {
    const currentValue = watch('max_paginas_expedientes')
    setValue('max_paginas_expedientes', currentValue === null ? 200 : null, {
      shouldDirty: true,
    })
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
        <div className="p-2 bg-purple-100 dark:bg-purple-900/20 rounded-lg">
          <Download className="h-5 w-5 text-purple-600 dark:text-purple-400" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Configuración de Extracción
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Timeouts, límites y reintentos para scraping del PJN
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Timeouts */}
        <div className="space-y-4">
          <h3 className="text-sm font-medium text-gray-900 dark:text-white flex items-center gap-2">
            <Clock className="h-4 w-4" />
            Timeouts (milisegundos)
          </h3>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Timeout por defecto
            </label>
            <input
              {...register('timeout_default', { valueAsNumber: true })}
              type="number"
              min="1000"
              step="1000"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            />
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Timeout general para operaciones de scraping (8000 = 8 segundos)
            </p>
            {errors.timeout_default && (
              <p className="mt-1 text-xs text-red-600">{errors.timeout_default.message}</p>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Timeout de login
              </label>
              <input
                {...register('timeout_login', { valueAsNumber: true })}
                type="number"
                min="1000"
                step="1000"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Timeout para login en el PJN (60000 = 1 minuto)
              </p>
              {errors.timeout_login && (
                <p className="mt-1 text-xs text-red-600">{errors.timeout_login.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Timeout de descarga
              </label>
              <input
                {...register('timeout_descarga', { valueAsNumber: true })}
                type="number"
                min="1000"
                step="1000"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Timeout para descarga de archivos (30000 = 30 segundos)
              </p>
              {errors.timeout_descarga && (
                <p className="mt-1 text-xs text-red-600">{errors.timeout_descarga.message}</p>
              )}
            </div>
          </div>
        </div>

        {/* Límites */}
        <div className="space-y-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <h3 className="text-sm font-medium text-gray-900 dark:text-white flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Límites de Extracción
          </h3>

          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Máximo de páginas de expedientes
              </label>
              <button
                type="button"
                onClick={handleToggleLimite}
                className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
              >
                {sinLimite ? 'Establecer límite' : 'Sin límite'}
              </button>
            </div>

            {!sinLimite ? (
              <>
                <input
                  {...register('max_paginas_expedientes', { valueAsNumber: true })}
                  type="number"
                  min="1"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                />
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  Máximo de páginas a extraer de la lista de expedientes
                </p>
              </>
            ) : (
              <div className="p-3 bg-yellow-50 dark:bg-yellow-900/10 rounded-lg border border-yellow-200 dark:border-yellow-800">
                <p className="text-sm text-yellow-800 dark:text-yellow-400">
                  ⚠️ Sin límite: se extraerán TODAS las páginas disponibles. Esto puede tardar mucho tiempo.
                </p>
              </div>
            )}
            {errors.max_paginas_expedientes && (
              <p className="mt-1 text-xs text-red-600">{errors.max_paginas_expedientes.message}</p>
            )}
          </div>
        </div>

        {/* Reintentos */}
        <div className="space-y-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <h3 className="text-sm font-medium text-gray-900 dark:text-white flex items-center gap-2">
            <RefreshCw className="h-4 w-4" />
            Reintentos
          </h3>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Máximo de reintentos para descargas
            </label>
            <input
              {...register('max_reintentos_descarga', { valueAsNumber: true })}
              type="number"
              min="1"
              max="10"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            />
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Número de reintentos si falla la descarga de un archivo
            </p>
            {errors.max_reintentos_descarga && (
              <p className="mt-1 text-xs text-red-600">{errors.max_reintentos_descarga.message}</p>
            )}
          </div>
        </div>

        {/* Información adicional */}
        <div className="p-4 bg-blue-50 dark:bg-blue-900/10 rounded-lg border border-blue-200 dark:border-blue-800">
          <h4 className="text-sm font-medium text-blue-900 dark:text-blue-300 mb-2">
            ℹ️ Recomendaciones
          </h4>
          <ul className="space-y-1 text-xs text-blue-800 dark:text-blue-400">
            <li>• <strong>Timeout por defecto:</strong> Si el PJN está lento, aumenta este valor.</li>
            <li>• <strong>Timeout de login:</strong> El login puede tardar en momentos de alta carga.</li>
            <li>• <strong>Límite de páginas:</strong> Establecer un límite evita extracciones muy largas.</li>
            <li>• <strong>Reintentos:</strong> 3 reintentos es un buen balance entre robustez y velocidad.</li>
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
