/**
 * ConfiguracionMonitoreo - Panel de configuración del sistema de monitoreo
 */

import { useState, useEffect } from 'react'
import { Settings, Clock, Bell, Calendar, Save } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useMonitoreoStore } from '@/stores/monitoreoStore'
import { FRECUENCIAS_MONITOREO, DIAS_SEMANA, type FrecuenciaMonitoreo } from '@/types/monitoreo'

export default function ConfiguracionMonitoreo() {
  const { configuracion, obtenerConfiguracion, actualizarConfiguracion } = useMonitoreoStore()

  const [formData, setFormData] = useState({
    frecuencia: '1hora' as FrecuenciaMonitoreo,
    notificar_email: true,
    notificar_sistema: true,
    hora_inicio: '09:00',
    hora_fin: '18:00',
    dias_semana: [1, 2, 3, 4, 5] as number[],
  })

  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    obtenerConfiguracion()
  }, [obtenerConfiguracion])

  useEffect(() => {
    if (configuracion) {
      setFormData({
        frecuencia: configuracion.frecuencia,
        notificar_email: configuracion.notificar_email,
        notificar_sistema: configuracion.notificar_sistema,
        hora_inicio: configuracion.hora_inicio || '09:00',
        hora_fin: configuracion.hora_fin || '18:00',
        dias_semana: configuracion.dias_semana || [1, 2, 3, 4, 5],
      })
    }
  }, [configuracion])

  const toggleDia = (dia: number) => {
    setFormData(prev => ({
      ...prev,
      dias_semana: prev.dias_semana.includes(dia)
        ? prev.dias_semana.filter(d => d !== dia)
        : [...prev.dias_semana, dia].sort(),
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    await actualizarConfiguracion(formData)

    setIsSubmitting(false)
  }

  if (!configuracion) {
    return (
      <Card className="p-6">
        <div className="text-center py-4 text-gray-500 dark:text-gray-400">
          Cargando configuración...
        </div>
      </Card>
    )
  }

  return (
    <Card className="p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-purple-100 dark:bg-purple-900/20 rounded-lg">
          <Settings className="h-5 w-5 text-purple-600 dark:text-purple-400" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Configuración del Monitoreo
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Personaliza cómo y cuándo se verifican los expedientes
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Frecuencia */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Clock className="h-4 w-4 text-gray-500 dark:text-gray-400" />
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Frecuencia de verificación
            </label>
          </div>
          <select
            value={formData.frecuencia}
            onChange={e => setFormData(prev => ({ ...prev, frecuencia: e.target.value as FrecuenciaMonitoreo }))}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isSubmitting}
          >
            {FRECUENCIAS_MONITOREO.map(freq => (
              <option key={freq.value} value={freq.value}>
                {freq.label} - {freq.descripcion}
              </option>
            ))}
          </select>
        </div>

        {/* Horario */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Calendar className="h-4 w-4 text-gray-500 dark:text-gray-400" />
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Horario de monitoreo
            </label>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">
                Hora inicio
              </label>
              <input
                type="time"
                value={formData.hora_inicio}
                onChange={e => setFormData(prev => ({ ...prev, hora_inicio: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                disabled={isSubmitting}
              />
            </div>
            <div>
              <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">
                Hora fin
              </label>
              <input
                type="time"
                value={formData.hora_fin}
                onChange={e => setFormData(prev => ({ ...prev, hora_fin: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                disabled={isSubmitting}
              />
            </div>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
            El monitoreo solo se ejecutará dentro de este rango horario
          </p>
        </div>

        {/* Días de la semana */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Días de la semana
          </label>
          <div className="flex gap-2">
            {DIAS_SEMANA.map(dia => (
              <button
                key={dia.value}
                type="button"
                onClick={() => toggleDia(dia.value)}
                disabled={isSubmitting}
                className={`flex-1 py-2 px-3 rounded-md text-sm font-medium transition-colors ${
                  formData.dias_semana.includes(dia.value)
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
                title={dia.fullLabel}
              >
                {dia.label}
              </button>
            ))}
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
            {formData.dias_semana.length === 0
              ? 'Selecciona al menos un día'
              : `Monitoreo activo ${formData.dias_semana.length} ${formData.dias_semana.length === 1 ? 'día' : 'días'} por semana`}
          </p>
        </div>

        {/* Notificaciones */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Bell className="h-4 w-4 text-gray-500 dark:text-gray-400" />
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Notificaciones
            </label>
          </div>
          <div className="space-y-3">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.notificar_sistema}
                onChange={e => setFormData(prev => ({ ...prev, notificar_sistema: e.target.checked }))}
                disabled={isSubmitting}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <div>
                <div className="text-sm font-medium text-gray-900 dark:text-white">
                  Notificaciones en el sistema
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  Mostrar alertas dentro de la aplicación
                </div>
              </div>
            </label>

            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.notificar_email}
                onChange={e => setFormData(prev => ({ ...prev, notificar_email: e.target.checked }))}
                disabled={isSubmitting}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <div>
                <div className="text-sm font-medium text-gray-900 dark:text-white">
                  Notificaciones por email
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  Recibir alertas en tu correo electrónico
                </div>
              </div>
            </label>
          </div>
        </div>

        {/* Botón Guardar */}
        <div className="flex justify-end pt-4 border-t border-gray-200 dark:border-gray-700">
          <Button type="submit" disabled={isSubmitting || formData.dias_semana.length === 0}>
            <Save className="h-4 w-4 mr-2" />
            {isSubmitting ? 'Guardando...' : 'Guardar cambios'}
          </Button>
        </div>
      </form>
    </Card>
  )
}
