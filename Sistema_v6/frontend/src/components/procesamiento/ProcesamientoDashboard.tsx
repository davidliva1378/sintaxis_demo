import { useEffect, useState } from 'react'
import { BarChart3, AlertCircle, Clock, FileCheck, TrendingDown, Calendar } from 'lucide-react'
import { obtenerDashboardData } from '@/api/procesamientoApi'
import {
  EstadisticasGlobales,
  VencimientoUrgente,
  ActuacionPorUtilidad,
  UtilidadJuridica,
} from '@/types/procesamiento'
import VencimientosUrgentesLista from './VencimientosUrgentesLista'
import ActuacionCard from './ActuacionCard'

export default function ProcesamientoDashboard() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [estadisticas, setEstadisticas] = useState<EstadisticasGlobales | null>(null)
  const [vencimientos, setVencimientos] = useState<VencimientoUrgente[]>([])
  const [actuacionesAlta, setActuacionesAlta] = useState<ActuacionPorUtilidad[]>([])

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await obtenerDashboardData()
      setEstadisticas(data.estadisticas)
      setVencimientos(data.vencimientos_urgentes)
      setActuacionesAlta(data.actuaciones_alta)
    } catch (err) {
      setError('Error al cargar datos del dashboard')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-sm text-gray-500">Cargando dashboard...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
        <div className="flex items-center gap-2">
          <AlertCircle className="h-5 w-5 text-red-600" />
          <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
        </div>
        <button
          onClick={loadDashboardData}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Reintentar
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Procesamiento de Actuaciones
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Clasificación automática, vencimientos y análisis de expedientes
          </p>
        </div>
        <button
          onClick={loadDashboardData}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Actualizar
        </button>
      </div>

      {/* Estadísticas Globales */}
      {estadisticas && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Expedientes Procesados */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <div className="flex items-center gap-3">
              <FileCheck className="h-8 w-8 text-blue-600 dark:text-blue-400" />
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Expedientes</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {estadisticas.total_expedientes_procesados.toLocaleString()}
                </p>
              </div>
            </div>
          </div>

          {/* Vencimientos Urgentes */}
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <div className="flex items-center gap-3">
              <AlertCircle className="h-8 w-8 text-red-600 dark:text-red-400" />
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Vencimientos Urgentes</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {estadisticas.total_vencimientos_urgentes.toLocaleString()}
                </p>
              </div>
            </div>
          </div>

          {/* Reducción Promedio */}
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
            <div className="flex items-center gap-3">
              <TrendingDown className="h-8 w-8 text-green-600 dark:text-green-400" />
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Reducción Promedio</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {estadisticas.reduccion_promedio_pct.toFixed(1)}%
                </p>
              </div>
            </div>
          </div>

          {/* Actuaciones Procesadas */}
          <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-4">
            <div className="flex items-center gap-3">
              <BarChart3 className="h-8 w-8 text-purple-600 dark:text-purple-400" />
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Actuaciones</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {estadisticas.total_actuaciones_procesadas.toLocaleString()}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Vencimientos Urgentes */}
      {vencimientos.length > 0 && (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
          <div className="flex items-center gap-2 mb-4">
            <Clock className="h-5 w-5 text-red-600" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Vencimientos Urgentes ({vencimientos.length})
            </h2>
          </div>
          <VencimientosUrgentesLista vencimientos={vencimientos} />
        </div>
      )}

      {/* Actuaciones de Alta Utilidad */}
      {actuacionesAlta.length > 0 && (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
          <div className="flex items-center gap-2 mb-4">
            <FileCheck className="h-5 w-5 text-red-600" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Actuaciones de Alta Utilidad ({actuacionesAlta.length})
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {actuacionesAlta.slice(0, 9).map((actuacion) => (
              <ActuacionCard key={actuacion.id} actuacion={actuacion} />
            ))}
          </div>
          {actuacionesAlta.length > 9 && (
            <div className="mt-4 text-center">
              <button className="text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400">
                Ver todas las actuaciones de alta utilidad →
              </button>
            </div>
          )}
        </div>
      )}

      {/* Estado vacío */}
      {!loading && vencimientos.length === 0 && actuacionesAlta.length === 0 && (
        <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-12 text-center">
          <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            No hay datos para mostrar
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Procesa expedientes para ver estadísticas y vencimientos urgentes
          </p>
        </div>
      )}
    </div>
  )
}
