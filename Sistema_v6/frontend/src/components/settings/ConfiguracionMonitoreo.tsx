/**
 * ConfiguracionMonitoreo - Configuración de monitoreo automático
 * Incluye modo simple y modo avanzado con horarios laborales
 */

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Activity, Save, Clock, Calendar, AlertCircle } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { toast } from 'sonner'

// Schema de validación
const monitoreoSchema = z.object({
  // Modo simple
  intervalo_minutos: z.number().min(0).max(1440),  // En minutos para el usuario
  dias_actividad: z.number().min(1).max(365),
  max_reintentos: z.number().min(1).max(10),
  notificar_cambios: z.boolean(),
  descargar_archivos: z.boolean(),

  // Opciones de extracción
  extraccion_completa: z.boolean(),  // Sin límite de fecha
  mostrar_navegador: z.boolean(),  // headless = false para depuración
  fecha_corte_dias: z.number().min(1).max(365).optional().nullable(),
  max_paginas_monitoreo: z.number().min(1).max(500).optional().nullable(),
  tiempo_maximo_extraccion: z.number().min(60).max(3600).optional().nullable(),
  detener_en_duplicado: z.boolean(),
  orden_extraccion: z.enum(['fecha', 'caratula', 'oficina', 'situacion']),

  // Modo avanzado (opcional)
  modo_avanzado: z.boolean(),
  intervalos_laboral_expedientes: z.number().min(1).max(1440).optional().nullable(),
  intervalos_laboral_entradas: z.number().min(1).max(1440).optional().nullable(),
  intervalos_no_laboral_expedientes: z.number().min(1).max(1440).optional().nullable(),
  intervalos_no_laboral_entradas: z.number().min(1).max(1440).optional().nullable(),
  dias_laborales: z.array(z.string()).min(1),
  hora_inicio: z.string().min(5).max(5),  // Formato HH:MM
  hora_fin: z.string().min(5).max(5),  // Formato HH:MM
})

type MonitoreoForm = z.infer<typeof monitoreoSchema>

export default function ConfiguracionMonitoreo() {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [modoAvanzado, setModoAvanzado] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
    watch,
    reset,
    setValue,
  } = useForm<MonitoreoForm>({
    resolver: zodResolver(monitoreoSchema),
    defaultValues: {
      intervalo_minutos: 30,  // 30 minutos por defecto
      dias_actividad: 30,
      max_reintentos: 3,
      notificar_cambios: true,
      descargar_archivos: true,
      // Opciones de extracción
      extraccion_completa: false,
      mostrar_navegador: false,
      fecha_corte_dias: 30,
      max_paginas_monitoreo: 50,
      tiempo_maximo_extraccion: 600,
      detener_en_duplicado: true,
      orden_extraccion: 'fecha' as const,
      // Modo avanzado
      modo_avanzado: false,
      intervalos_laboral_expedientes: null,
      intervalos_laboral_entradas: null,
      intervalos_no_laboral_expedientes: null,
      intervalos_no_laboral_entradas: null,
      dias_laborales: ['lunes', 'martes', 'miercoles', 'jueves', 'viernes'],
      hora_inicio: '08:00',
      hora_fin: '18:00',
    },
  })

  const modoAvanzadoWatch = watch('modo_avanzado')
  const extraccionCompletaWatch = watch('extraccion_completa')

  // Cargar configuración actual del servidor
  useEffect(() => {
    const cargarConfiguracion = async () => {
      try {
        const response = await fetch('/api/v1/config/sistema')
        if (!response.ok) throw new Error('Error al cargar configuración')

        const data = await response.json()
        const monitoreo = data.monitoreo

        const tieneConfigAvanzada =
          monitoreo.intervalos_laboral_expedientes != null
        const esExtraccionCompleta = monitoreo.fecha_corte_dias == null

        const formData = {
          intervalo_minutos: Math.floor(monitoreo.intervalo_segundos / 60),
          dias_actividad: monitoreo.dias_actividad,
          max_reintentos: monitoreo.max_reintentos,
          notificar_cambios: monitoreo.notificar_cambios,
          descargar_archivos: monitoreo.descargar_archivos,
          extraccion_completa: esExtraccionCompleta,
          mostrar_navegador: !data.browser.headless,
          fecha_corte_dias: monitoreo.fecha_corte_dias ?? 30,
          max_paginas_monitoreo: monitoreo.max_paginas_monitoreo ?? 50,
          tiempo_maximo_extraccion: monitoreo.tiempo_maximo_extraccion ?? 600,
          detener_en_duplicado: monitoreo.detener_en_duplicado ?? true,
          orden_extraccion: monitoreo.orden_extraccion ?? 'fecha',
          modo_avanzado: tieneConfigAvanzada,
          intervalos_laboral_expedientes: monitoreo.intervalos_laboral_expedientes,
          intervalos_laboral_entradas: monitoreo.intervalos_laboral_entradas,
          intervalos_no_laboral_expedientes: monitoreo.intervalos_no_laboral_expedientes,
          intervalos_no_laboral_entradas: monitoreo.intervalos_no_laboral_entradas,
          dias_laborales: monitoreo.dias_laborales || ['lunes', 'martes', 'miercoles', 'jueves', 'viernes'],
          hora_inicio: monitoreo.hora_inicio || '08:00',
          hora_fin: monitoreo.hora_fin || '18:00',
        }

        reset(formData, { keepDefaultValues: false })

        setModoAvanzado(tieneConfigAvanzada)

        setIsLoading(false)
      } catch (error) {
        console.error('Error cargando configuración:', error)
        toast.error('Error al cargar configuración')
        setIsLoading(false)
      }
    }

    cargarConfiguracion()
  }, [reset])

  // Sincronizar estado de modo avanzado con el form
  useEffect(() => {
    setModoAvanzado(modoAvanzadoWatch)
  }, [modoAvanzadoWatch])

  const onSubmit = async (data: MonitoreoForm) => {
    setIsSubmitting(true)

    try {
      const response = await fetch('/api/v1/config/sistema', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          // Browser config para headless (incluir todos los campos requeridos)
          browser: {
            headless: !data.mostrar_navegador,
            timeout_ms: 30000,
            navigation_timeout_ms: 60000,
          },
          monitoreo: {
            // Convertir minutos a segundos para el backend
            intervalo_segundos: data.intervalo_minutos * 60,
            dias_actividad: data.dias_actividad,
            max_reintentos: data.max_reintentos,
            notificar_cambios: data.notificar_cambios,
            descargar_archivos: data.descargar_archivos,
            // Opciones de extracción
            fecha_corte_dias: data.extraccion_completa ? null : data.fecha_corte_dias,
            max_paginas_monitoreo: data.max_paginas_monitoreo,
            tiempo_maximo_extraccion: data.tiempo_maximo_extraccion,
            detener_en_duplicado: data.detener_en_duplicado,
            orden_extraccion: data.orden_extraccion,
            // Campos avanzados (siempre enviar, backend los requiere)
            intervalos_laboral_expedientes: data.modo_avanzado ? data.intervalos_laboral_expedientes : null,
            intervalos_laboral_entradas: data.modo_avanzado ? data.intervalos_laboral_entradas : null,
            intervalos_no_laboral_expedientes: data.modo_avanzado ? data.intervalos_no_laboral_expedientes : null,
            intervalos_no_laboral_entradas: data.modo_avanzado ? data.intervalos_no_laboral_entradas : null,
            dias_laborales: data.dias_laborales,
            hora_inicio: data.hora_inicio,
            hora_fin: data.hora_fin,
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
        <div className="p-2 bg-green-100 dark:bg-green-900/20 rounded-lg">
          <Activity className="h-5 w-5 text-green-600 dark:text-green-400" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Configuración de Monitoreo
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Define cómo el sistema monitorea cambios en expedientes
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Configuración Básica */}
        <div className="space-y-4">
          <h3 className="text-sm font-medium text-gray-900 dark:text-white">
            Configuración Básica
          </h3>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Intervalo de verificación (minutos)
            </label>
            <input
              {...register('intervalo_minutos', { valueAsNumber: true })}
              type="number"
              min="0"
              max="1440"
              disabled={modoAvanzado}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white disabled:opacity-50 disabled:cursor-not-allowed"
            />
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              {modoAvanzado
                ? 'Deshabilitado en modo avanzado (se usan intervalos diferenciados)'
                : '30 = cada 30 minutos, 60 = cada hora, 0 = ejecutar una sola vez'}
            </p>
            {errors.intervalo_minutos && (
              <p className="mt-1 text-xs text-red-600">{errors.intervalo_minutos.message}</p>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Días de actividad
              </label>
              <input
                {...register('dias_actividad', { valueAsNumber: true })}
                type="number"
                min="1"
                max="365"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Días hacia atrás para considerar un expediente "activo"
              </p>
              {errors.dias_actividad && (
                <p className="mt-1 text-xs text-red-600">{errors.dias_actividad.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Máximo de reintentos
              </label>
              <input
                {...register('max_reintentos', { valueAsNumber: true })}
                type="number"
                min="1"
                max="10"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              />
              {errors.max_reintentos && (
                <p className="mt-1 text-xs text-red-600">{errors.max_reintentos.message}</p>
              )}
            </div>
          </div>

          {/* Checkboxes */}
          <div className="space-y-3">
            <label className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800">
              <input
                {...register('notificar_cambios')}
                type="checkbox"
                className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
              />
              <div>
                <div className="text-sm font-medium text-gray-900 dark:text-white">
                  Notificar cambios
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  Enviar notificaciones cuando se detecten cambios
                </div>
              </div>
            </label>

            <label className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800">
              <input
                {...register('descargar_archivos')}
                type="checkbox"
                className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
              />
              <div>
                <div className="text-sm font-medium text-gray-900 dark:text-white">
                  Descargar archivos automáticamente
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  Descarga archivos nuevos de forma automática
                </div>
              </div>
            </label>
          </div>
        </div>

        {/* Opciones de Extracción */}
        <div className="space-y-4 border-t border-gray-200 dark:border-gray-700 pt-6">
          <h3 className="text-sm font-medium text-gray-900 dark:text-white">
            Opciones de Extracción
          </h3>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Configura cómo se extraen los expedientes del PJN para optimizar el monitoreo
          </p>

          {/* Checkbox Extracción completa */}
          <label className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800">
            <input
              {...register('extraccion_completa')}
              type="checkbox"
              className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
            />
            <div>
              <div className="text-sm font-medium text-gray-900 dark:text-white">
                Extracción completa (sin límite de fecha)
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                Extrae todos los expedientes sin importar su fecha de actividad
              </div>
            </div>
          </label>

          {/* Checkbox Mostrar navegador */}
          <label className="flex items-center gap-3 p-3 rounded-lg border border-amber-200 dark:border-amber-800 cursor-pointer hover:bg-amber-50 dark:hover:bg-amber-900/20 mb-4">
            <input
              {...register('mostrar_navegador')}
              type="checkbox"
              className="w-4 h-4 text-amber-600 rounded focus:ring-amber-500"
            />
            <div>
              <div className="text-sm font-medium text-gray-900 dark:text-white">
                Mostrar navegador (depuración)
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                Muestra el navegador durante la extracción para depurar problemas
              </div>
            </div>
          </label>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Fecha de corte (días)
              </label>
              <input
                {...register('fecha_corte_dias', { valueAsNumber: true })}
                type="number"
                min="1"
                max="365"
                disabled={extraccionCompletaWatch}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white disabled:opacity-50 disabled:cursor-not-allowed"
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                {extraccionCompletaWatch
                  ? 'Deshabilitado (extracción completa activa)'
                  : 'Solo extraer expedientes con actividad en los últimos N días'}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Máximo de páginas
              </label>
              <input
                {...register('max_paginas_monitoreo', { valueAsNumber: true })}
                type="number"
                min="1"
                max="500"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Límite de páginas a extraer del PJN
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Tiempo máximo (segundos)
              </label>
              <input
                {...register('tiempo_maximo_extraccion', { valueAsNumber: true })}
                type="number"
                min="60"
                max="3600"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Timeout para la extracción (600 = 10 minutos)
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Orden de extracción
              </label>
              <select
                {...register('orden_extraccion')}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              >
                <option value="fecha">Fecha</option>
                <option value="caratula">Carátula</option>
                <option value="oficina">Oficina</option>
                <option value="situacion">Situación</option>
              </select>
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Ordenar por fecha es lo más eficiente
              </p>
            </div>
          </div>

          <label className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800">
            <input
              {...register('detener_en_duplicado')}
              type="checkbox"
              className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
            />
            <div>
              <div className="text-sm font-medium text-gray-900 dark:text-white">
                Detener en duplicado
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                Detiene la extracción al encontrar expedientes ya conocidos
              </div>
            </div>
          </label>
        </div>

        {/* Toggle Modo Avanzado */}
        <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
          <label className="flex items-center justify-between p-4 rounded-lg border border-gray-200 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800">
            <div className="flex items-center gap-3">
              <Clock className="h-5 w-5 text-gray-400" />
              <div>
                <div className="text-sm font-medium text-gray-900 dark:text-white">
                  Modo Avanzado (Horarios Laborales)
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400">
                  Intervalos diferenciados según horario y tipo de contenido
                </div>
              </div>
            </div>
            <input
              {...register('modo_avanzado')}
              type="checkbox"
              className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
            />
          </label>
        </div>

        {/* Configuración Avanzada (condicional) */}
        {modoAvanzado && (
          <div className="space-y-4 p-4 bg-blue-50 dark:bg-blue-900/10 rounded-lg border border-blue-200 dark:border-blue-800">
            <div className="flex items-start gap-2 mb-4">
              <AlertCircle className="h-4 w-4 text-blue-600 dark:text-blue-400 mt-0.5" />
              <p className="text-xs text-blue-800 dark:text-blue-300">
                En modo avanzado, el intervalo básico se ignora y se usan los intervalos específicos por tipo y horario.
              </p>
            </div>

            <h3 className="text-sm font-medium text-blue-900 dark:text-blue-300">
              Intervalos en Minutos
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Laboral - Expedientes (min)
                </label>
                <input
                  {...register('intervalos_laboral_expedientes', { valueAsNumber: true })}
                  type="number"
                  min="1"
                  placeholder="10"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Laboral - Entradas (min)
                </label>
                <input
                  {...register('intervalos_laboral_entradas', { valueAsNumber: true })}
                  type="number"
                  min="1"
                  placeholder="15"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  No Laboral - Expedientes (min)
                </label>
                <input
                  {...register('intervalos_no_laboral_expedientes', { valueAsNumber: true })}
                  type="number"
                  min="1"
                  placeholder="60"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  No Laboral - Entradas (min)
                </label>
                <input
                  {...register('intervalos_no_laboral_entradas', { valueAsNumber: true })}
                  type="number"
                  min="1"
                  placeholder="30"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                Días laborales
              </label>
              <div className="flex flex-wrap gap-2">
                {['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo'].map(dia => (
                  <label key={dia} className="inline-flex items-center px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800">
                    <input
                      type="checkbox"
                      value={dia}
                      {...register('dias_laborales')}
                      className="mr-2 w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                    />
                    <span className="capitalize text-sm text-gray-700 dark:text-gray-300">{dia}</span>
                  </label>
                ))}
              </div>
              {errors.dias_laborales && (
                <p className="mt-1 text-xs text-red-600">{errors.dias_laborales.message}</p>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Hora inicio laboral
                </label>
                <input
                  {...register('hora_inicio')}
                  type="time"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                />
                {errors.hora_inicio && (
                  <p className="mt-1 text-xs text-red-600">{errors.hora_inicio.message}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Hora fin laboral
                </label>
                <input
                  {...register('hora_fin')}
                  type="time"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                />
                {errors.hora_fin && (
                  <p className="mt-1 text-xs text-red-600">{errors.hora_fin.message}</p>
                )}
              </div>
            </div>
          </div>
        )}

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
