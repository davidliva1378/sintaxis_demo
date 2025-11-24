/**
 * ConfiguracionMonitoreo - Configuración de monitoreo automático
 * Sistema híbrido:
 * - Monitoreo (MySQL): /api/v1/monitoreo/configuracion
 * - Extracción (.env): /api/v1/config/sistema
 */

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Activity, Save, Clock, Calendar, Settings, AlertCircle } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { toast } from 'sonner'
import * as monitoreoApi from '@/api/monitoreoApi'
import apiClient from '@/api/client'

// Schema para configuración de monitoreo (MySQL)
const monitoreoSchema = z.object({
  activo: z.boolean(),
  frecuencia: z.enum(['5min', '15min', '30min', '1hora', '3horas', '6horas', '12horas', '24horas']),
  notificar_email: z.boolean(),
  notificar_sistema: z.boolean(),
  // Validar formato HH:MM
  hora_inicio: z.string().regex(/^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/, 'Hora debe tener formato HH:MM'),
  hora_fin: z.string().regex(/^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/, 'Hora debe tener formato HH:MM'),
  dias_semana: z.array(z.number()).min(1),
}).refine(
  (data) => {
    // Validar que hora_inicio y hora_fin NO sean idénticas
    // Permite hora_inicio > hora_fin para soportar horarios que cruzan medianoche
    // Ejemplos válidos:
    // - 08:00 - 18:00 (horario normal)
    // - 22:00 - 06:00 (horario nocturno, cruza medianoche)
    // - 06:00 - 05:59 (monitoreo casi 24h, cruza medianoche)
    // Ejemplo inválido:
    // - 10:00 - 10:00 (0 horas, sin sentido)
    const inicio = data.hora_inicio.split(':').map(Number)
    const fin = data.hora_fin.split(':').map(Number)
    const minutosInicio = inicio[0] * 60 + inicio[1]
    const minutosFin = fin[0] * 60 + fin[1]
    return minutosInicio !== minutosFin
  },
  {
    message: 'Las horas de inicio y fin no pueden ser idénticas',
    path: ['hora_fin'], // Mostrar error en el campo hora_fin
  }
)

// Schema para configuración de extracción (.env)
const extraccionSchema = z.object({
  fecha_corte_dias: z.number().min(1).max(365).nullable(),
  max_paginas_monitoreo: z.number().min(1).max(500).nullable(),
  tiempo_maximo_extraccion: z.number().min(60).max(3600).nullable(),
  detener_en_duplicado: z.boolean(),
  orden_extraccion: z.enum(['fecha', 'caratula', 'oficina', 'situacion']),
  mostrar_navegador: z.boolean(),
})

type MonitoreoForm = z.infer<typeof monitoreoSchema>
type ExtraccionForm = z.infer<typeof extraccionSchema>

export default function ConfiguracionMonitoreo() {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  // Estado para extracción (separado porque usa otro endpoint)
  const [extraccionData, setExtraccionData] = useState<ExtraccionForm>({
    fecha_corte_dias: 30,
    max_paginas_monitoreo: 50,
    tiempo_maximo_extraccion: 600,
    detener_en_duplicado: true,
    orden_extraccion: 'fecha',
    mostrar_navegador: false,
  })
  const [extraccionDirty, setExtraccionDirty] = useState(false)

  // Form para monitoreo (MySQL)
  const {
    register,
    handleSubmit,
    formState,
    reset,
    setValue,
    watch,
    getValues,
  } = useForm<MonitoreoForm>({
    resolver: zodResolver(monitoreoSchema),
    defaultValues: {
      activo: true,
      frecuencia: '30min',
      notificar_email: false,
      notificar_sistema: true,
      hora_inicio: '08:00',
      hora_fin: '18:00',
      dias_semana: [1, 2, 3, 4, 5],
    },
  })

  const diasSemanaWatch = watch('dias_semana')

  // Cargar ambas configuraciones
  useEffect(() => {
    const cargarConfiguraciones = async () => {
      try {
        // Cargar configuración de monitoreo (MySQL)
        const configMonitoreo = await monitoreoApi.obtenerConfiguracion()

        // Validar que la configuración se cargó correctamente
        if (!configMonitoreo) {
          throw new Error('No se pudo obtener la configuración de monitoreo')
        }

        // Transformar horas de HH:MM:SS a HH:MM si es necesario
        const formatearHora = (hora: string | null | undefined): string => {
          if (!hora) return '08:00'
          // Separar por ':' y tomar solo horas:minutos (ignorar segundos)
          const partes = hora.split(':')
          if (partes.length >= 2) {
            // Asegurar formato HH:MM con padding de ceros
            const horas = partes[0].padStart(2, '0')
            const minutos = partes[1].padStart(2, '0')
            return `${horas}:${minutos}`
          }
          return hora
        }

        reset({
          activo: configMonitoreo.activo ?? true,
          frecuencia: (configMonitoreo.frecuencia as MonitoreoForm['frecuencia']) ?? '30min',
          notificar_email: configMonitoreo.notificar_email ?? false,
          notificar_sistema: configMonitoreo.notificar_sistema ?? true,
          hora_inicio: formatearHora(configMonitoreo.hora_inicio),
          hora_fin: formatearHora(configMonitoreo.hora_fin),
          dias_semana: configMonitoreo.dias_semana || [1, 2, 3, 4, 5],
        })

        // Cargar configuración de extracción (.env)
        const respExtraccion = await apiClient.get('/api/v1/config/sistema')
        if (respExtraccion.data) {
          const data = respExtraccion.data
          setExtraccionData({
            fecha_corte_dias: data.monitoreo.fecha_corte_dias ?? 30,
            max_paginas_monitoreo: data.monitoreo.max_paginas_monitoreo ?? 50,
            tiempo_maximo_extraccion: data.monitoreo.tiempo_maximo_extraccion ?? 600,
            detener_en_duplicado: data.monitoreo.detener_en_duplicado ?? true,
            orden_extraccion: data.monitoreo.orden_extraccion ?? 'fecha',
            mostrar_navegador: !data.browser.headless,
          })
        }

        setIsLoading(false)
      } catch (error: any) {
        console.error('Error cargando configuración:', error)

        // Mostrar mensaje de error más detallado
        const errorMsg = error?.response?.data?.detail || error?.message || 'Error desconocido al cargar configuración'
        toast.error('Error al cargar la configuración', {
          description: errorMsg,
          duration: 5000,
        })

        setIsLoading(false)
      }
    }

    cargarConfiguraciones()
  }, [reset])

  // Handler para cambios en extracción
  const handleExtraccionChange = (field: keyof ExtraccionForm, value: any) => {
    setExtraccionData(prev => ({ ...prev, [field]: value }))
    setExtraccionDirty(true)
  }

  // Toggle de días
  const toggleDia = (dia: number) => {
    const current = diasSemanaWatch || []
    if (current.includes(dia)) {
      setValue('dias_semana', current.filter(d => d !== dia), { shouldDirty: true })
    } else {
      setValue('dias_semana', [...current, dia].sort(), { shouldDirty: true })
    }
  }

  // Guardar ambas configuraciones
  const onSubmit = async (monitoreoData: MonitoreoForm) => {
    setIsSubmitting(true)

    try {
      // 1. Guardar configuración de monitoreo (MySQL)
      if (formState.isDirty) {
        await monitoreoApi.actualizarConfiguracion({
          activo: monitoreoData.activo,
          frecuencia: monitoreoData.frecuencia,
          notificar_email: monitoreoData.notificar_email,
          notificar_sistema: monitoreoData.notificar_sistema,
          hora_inicio: monitoreoData.hora_inicio,
          hora_fin: monitoreoData.hora_fin,
          dias_semana: monitoreoData.dias_semana,
        })
      }

      // 2. Guardar configuración de extracción (.env)
      if (extraccionDirty) {
        await apiClient.put('/api/v1/config/sistema', {
          browser: {
            headless: !extraccionData.mostrar_navegador,
            timeout_ms: 30000,
            navigation_timeout_ms: 60000,
          },
          monitoreo: {
            intervalo_segundos: 1800, // Se mantiene el valor existente
            dias_actividad: 30,
            max_reintentos: 3,
            notificar_cambios: true,
            descargar_archivos: true,
            fecha_corte_dias: extraccionData.fecha_corte_dias,
            max_paginas_monitoreo: extraccionData.max_paginas_monitoreo,
            tiempo_maximo_extraccion: extraccionData.tiempo_maximo_extraccion,
            detener_en_duplicado: extraccionData.detener_en_duplicado,
            orden_extraccion: extraccionData.orden_extraccion,
            intervalos_laboral_expedientes: null,
            intervalos_laboral_entradas: null,
            intervalos_no_laboral_expedientes: null,
            intervalos_no_laboral_entradas: null,
            dias_laborales: ['lunes', 'martes', 'miercoles', 'jueves', 'viernes'],
            hora_inicio: '08:00',
            hora_fin: '18:00',
          },
        })
      }

      toast.success('Configuración actualizada', {
        description: extraccionDirty
          ? 'Cambios aplicados. Reinicia el servidor para aplicar cambios de extracción.'
          : 'Los cambios se aplicaron correctamente',
      })

      reset(monitoreoData)
      setExtraccionDirty(false)
    } catch (error: any) {
      toast.error('Error al actualizar', {
        description: error.response?.data?.detail || error.message,
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const DIAS_SEMANA = [
    { value: 0, label: 'Dom' },
    { value: 1, label: 'Lun' },
    { value: 2, label: 'Mar' },
    { value: 3, label: 'Mié' },
    { value: 4, label: 'Jue' },
    { value: 5, label: 'Vie' },
    { value: 6, label: 'Sáb' },
  ]

  const FRECUENCIAS = [
    { value: '5min', label: 'Cada 5 minutos' },
    { value: '15min', label: 'Cada 15 minutos' },
    { value: '30min', label: 'Cada 30 minutos' },
    { value: '1hora', label: 'Cada hora' },
    { value: '3horas', label: 'Cada 3 horas' },
    { value: '6horas', label: 'Cada 6 horas' },
    { value: '12horas', label: 'Cada 12 horas' },
    { value: '24horas', label: 'Cada 24 horas' },
  ]

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
            Define cuándo y cómo el sistema verifica cambios en expedientes
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit, (errors) => {
        console.log('🔍 DEBUG errores de validación:', errors)
        console.log('🔍 DEBUG formState.errors:', formState.errors)
      })} className="space-y-6">
        {/* Estado del monitoreo */}
        <div className="space-y-4">
          <label className="flex items-center justify-between p-4 rounded-lg border border-gray-200 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800">
            <div>
              <div className="text-sm font-medium text-gray-900 dark:text-white">
                Monitoreo activo
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                Habilita o deshabilita la verificación automática
              </div>
            </div>
            <input
              {...register('activo')}
              type="checkbox"
              className="w-5 h-5 text-green-600 rounded focus:ring-green-500"
            />
          </label>
        </div>

        {/* Frecuencia */}
        <div className="space-y-4">
          <h3 className="text-sm font-medium text-gray-900 dark:text-white">
            Frecuencia de Verificación
          </h3>
          <select
            {...register('frecuencia')}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          >
            {FRECUENCIAS.map(f => (
              <option key={f.value} value={f.value}>{f.label}</option>
            ))}
          </select>
        </div>

        {/* Horario */}
        <div className="space-y-4">
          <h3 className="text-sm font-medium text-gray-900 dark:text-white flex items-center gap-2">
            <Clock className="h-4 w-4" />
            Horario de Verificación
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Hora inicio
              </label>
              <input
                {...register('hora_inicio')}
                type="time"
                className={`w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white ${
                  formState.errors.hora_inicio
                    ? 'border-red-500 focus:ring-red-500'
                    : 'border-gray-300 dark:border-gray-700'
                }`}
              />
              {formState.errors.hora_inicio && (
                <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                  {formState.errors.hora_inicio.message}
                </p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Hora fin
              </label>
              <input
                {...register('hora_fin')}
                type="time"
                className={`w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white ${
                  formState.errors.hora_fin
                    ? 'border-red-500 focus:ring-red-500'
                    : 'border-gray-300 dark:border-gray-700'
                }`}
              />
              {formState.errors.hora_fin && (
                <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                  {formState.errors.hora_fin.message}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Días */}
        <div className="space-y-4">
          <h3 className="text-sm font-medium text-gray-900 dark:text-white flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            Días de Verificación
          </h3>
          <div className="flex flex-wrap gap-2">
            {DIAS_SEMANA.map(dia => (
              <button
                key={dia.value}
                type="button"
                onClick={() => toggleDia(dia.value)}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  diasSemanaWatch?.includes(dia.value)
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                }`}
              >
                {dia.label}
              </button>
            ))}
          </div>
        </div>

        {/* Notificaciones */}
        <div className="space-y-4">
          <h3 className="text-sm font-medium text-gray-900 dark:text-white">
            Notificaciones
          </h3>
          <div className="space-y-3">
            <label className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800">
              <input
                {...register('notificar_sistema')}
                type="checkbox"
                className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
              />
              <div>
                <div className="text-sm font-medium text-gray-900 dark:text-white">
                  Notificaciones del sistema
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  Mostrar notificaciones en la aplicación
                </div>
              </div>
            </label>
            <label className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800">
              <input
                {...register('notificar_email')}
                type="checkbox"
                className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
              />
              <div>
                <div className="text-sm font-medium text-gray-900 dark:text-white">
                  Notificaciones por email
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  Enviar resumen de cambios por correo electrónico
                </div>
              </div>
            </label>
          </div>
        </div>

        {/* Separador */}
        <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-amber-100 dark:bg-amber-900/20 rounded-lg">
              <Settings className="h-5 w-5 text-amber-600 dark:text-amber-400" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
                Opciones de Extracción
              </h3>
              <p className="text-xs text-gray-600 dark:text-gray-400">
                Configura cómo se extraen los expedientes del PJN
              </p>
            </div>
          </div>

          {/* Mostrar navegador */}
          <label className="flex items-center gap-3 p-3 rounded-lg border border-amber-200 dark:border-amber-800 cursor-pointer hover:bg-amber-50 dark:hover:bg-amber-900/20 mb-4">
            <input
              type="checkbox"
              checked={extraccionData.mostrar_navegador}
              onChange={(e) => handleExtraccionChange('mostrar_navegador', e.target.checked)}
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
                type="number"
                min="1"
                max="365"
                value={extraccionData.fecha_corte_dias ?? ''}
                onChange={(e) => handleExtraccionChange('fecha_corte_dias', e.target.value ? parseInt(e.target.value) : null)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Solo extraer expedientes con actividad en los últimos N días
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Máximo de páginas
              </label>
              <input
                type="number"
                min="1"
                max="500"
                value={extraccionData.max_paginas_monitoreo ?? ''}
                onChange={(e) => handleExtraccionChange('max_paginas_monitoreo', e.target.value ? parseInt(e.target.value) : null)}
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
                type="number"
                min="60"
                max="3600"
                value={extraccionData.tiempo_maximo_extraccion ?? ''}
                onChange={(e) => handleExtraccionChange('tiempo_maximo_extraccion', e.target.value ? parseInt(e.target.value) : null)}
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
                value={extraccionData.orden_extraccion}
                onChange={(e) => handleExtraccionChange('orden_extraccion', e.target.value)}
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

          <label className="flex items-center gap-3 p-3 mt-4 rounded-lg border border-gray-200 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800">
            <input
              type="checkbox"
              checked={extraccionData.detener_en_duplicado}
              onChange={(e) => handleExtraccionChange('detener_en_duplicado', e.target.checked)}
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

          {extraccionDirty && (
            <div className="mt-4 p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
              <div className="flex items-start gap-2">
                <AlertCircle className="h-4 w-4 text-amber-600 dark:text-amber-400 mt-0.5" />
                <p className="text-xs text-amber-800 dark:text-amber-300">
                  Los cambios de extracción requieren reiniciar el servidor para aplicarse.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Botón Guardar */}
        <div className="flex justify-end pt-4 border-t border-gray-200 dark:border-gray-700">
          <Button
            type="submit"
            disabled={(!formState.isDirty && !extraccionDirty) || isSubmitting}
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
