/**
 * MonitoreoPage - Página principal del módulo de Monitoreo
 */

import { useEffect, useState } from 'react'
import { Activity, Play, Pause, Plus, Bell, Clock, TrendingUp, AlertCircle, Settings, RefreshCw } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useMonitoreoStore } from '@/stores/monitoreoStore'
import MonitoreoCard from '@/components/monitoreo/MonitoreoCard'
import LogsList from '@/components/monitoreo/LogsList'
import { formatDistanceToNow } from 'date-fns'
import { es } from 'date-fns/locale'
import { toast } from 'sonner'
import * as monitoreoApi from '@/api/monitoreoApi'

export default function MonitoreoPage() {
  const {
    configuracion,
    expedientes,
    estadisticas,
    estadoScheduler,
    isLoading,
    listarExpedientes,
    obtenerEstadisticas,
    obtenerEstadoScheduler,
    toggleMonitoreo,
    toggleExpediente,
    removerExpediente,
    verificarExpediente,
    listarCambios,
  } = useMonitoreoStore()

  const [showChanges, setShowChanges] = useState(false)
  const [selectedExpedienteId, setSelectedExpedienteId] = useState<number | undefined>()
  const [isVerifyingGlobal, setIsVerifyingGlobal] = useState(false)

  useEffect(() => {
    listarExpedientes()
    obtenerEstadisticas()
    listarCambios() // Cargar cambios globales al iniciar
  }, [listarExpedientes, obtenerEstadisticas, listarCambios])

  // Polling: actualizar estado del scheduler cada 10 segundos
  useEffect(() => {
    // Actualizar inmediatamente
    obtenerEstadisticas()
    obtenerEstadoScheduler()

    // Configurar polling
    const interval = setInterval(() => {
      obtenerEstadisticas()
      obtenerEstadoScheduler()
      listarExpedientes() // Recargar expedientes para actualizar "última verificación"
    }, 10000) // 10 segundos

    // Cleanup al desmontar
    return () => clearInterval(interval)
  }, [obtenerEstadisticas, obtenerEstadoScheduler, listarExpedientes])

  const handleToggleMonitoreo = async () => {
    if (configuracion) {
      await toggleMonitoreo(!configuracion.activo)
      obtenerEstadisticas()
    }
  }

  const handleToggleExpediente = async (id: number, activo: boolean) => {
    await toggleExpediente(id, activo)
    obtenerEstadisticas()
  }

  const handleRemoverExpediente = async (id: number) => {
    await removerExpediente(id)
    obtenerEstadisticas()
  }

  const handleVerificarExpediente = async (id: number) => {
    await verificarExpediente(id)
  }

  const handleVerificarGlobal = async () => {
    setIsVerifyingGlobal(true)
    toast.info('Verificando expedientes...', {
      id: 'global-verify',
      description: 'Conectando con PJN...'
    })

    try {
      const response = await monitoreoApi.verificarManual()
      toast.dismiss('global-verify')

      if (response.success) {
        toast.success('Verificación completada', {
          description: `${response.cambios_detectados} cambio(s) detectado(s) en ${response.total_expedientes} expediente(s)`
        })
        // Actualizar datos
        await obtenerEstadisticas()
        await listarCambios()
        await listarExpedientes() // Recargar expedientes para actualizar "última verificación"
      } else {
        toast.error('Error en verificación', {
          description: response.error || 'Error desconocido'
        })
      }
    } catch (error: any) {
      toast.dismiss('global-verify')
      toast.error('Error al verificar', {
        description: error.message || 'Error de conexión'
      })
    } finally {
      setIsVerifyingGlobal(false)
    }
  }

  const handleViewChanges = (id: number) => {
    setSelectedExpedienteId(id)
    setShowChanges(true)
  }

  const formatFecha = (fecha: string | undefined) => {
    if (!fecha) return 'N/A'
    try {
      return formatDistanceToNow(new Date(fecha), { addSuffix: true, locale: es })
    } catch {
      return fecha
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Monitoreo Automático
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Verificación automática de cambios en expedientes seleccionados
          </p>
        </div>

        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={handleVerificarGlobal}
            disabled={isVerifyingGlobal || expedientes.length === 0}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isVerifyingGlobal ? 'animate-spin' : ''}`} />
            {isVerifyingGlobal ? 'Verificando...' : 'Verificar Ahora'}
          </Button>
          <Link to="/settings">
            <Button variant="outline">
              <Settings className="h-4 w-4 mr-2" />
              Configuración
            </Button>
          </Link>
          {configuracion && (
            <Button
              onClick={handleToggleMonitoreo}
              variant={configuracion.activo ? 'default' : 'outline'}
              className={
                configuracion.activo
                  ? 'bg-green-600 hover:bg-green-700'
                  : ''
              }
            >
              {configuracion.activo ? (
                <>
                  <Pause className="h-4 w-4 mr-2" />
                  Pausar Monitoreo
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Activar Monitoreo
                </>
              )}
            </Button>
          )}
        </div>
      </div>

      {/* Estado del sistema */}
      {configuracion && (
        <Card className={`p-6 ${configuracion.activo ? 'border-l-4 border-l-green-500' : 'border-l-4 border-l-gray-300'}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className={`p-3 rounded-lg ${configuracion.activo ? 'bg-green-100 dark:bg-green-900/20' : 'bg-gray-100 dark:bg-gray-800'}`}>
                <Activity className={`h-6 w-6 ${configuracion.activo ? 'text-green-600 dark:text-green-400' : 'text-gray-600 dark:text-gray-400'}`} />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Estado del sistema:{' '}
                  <Badge
                    variant={configuracion.activo ? 'default' : 'outline'}
                    className={configuracion.activo ? 'bg-green-600' : ''}
                  >
                    {configuracion.activo ? 'ACTIVO' : 'PAUSADO'}
                  </Badge>
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Frecuencia: <span className="font-medium">Cada {configuracion.frecuencia.replace('min', ' minutos').replace('hora', ' hora')}</span>
                  {' • '}
                  Horario: {configuracion.hora_inicio} - {configuracion.hora_fin}
                </p>
              </div>
            </div>

            {estadisticas && (
              <div className="text-right">
                <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">
                  {configuracion.activo ? 'Última ejecución' : 'Última vez activo'}
                </div>
                <div className="text-sm font-medium text-gray-900 dark:text-white">
                  {formatFecha(estadisticas.ultima_ejecucion)}
                </div>
                {configuracion.activo && estadisticas.proxima_ejecucion && (
                  <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Próxima: {formatFecha(estadisticas.proxima_ejecucion)}
                  </div>
                )}
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Estadísticas */}
      {estadisticas && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Expedientes Monitoreados
                </p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
                  {estadisticas.total_expedientes}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                  {estadisticas.expedientes_activos} activos
                </p>
              </div>
              <div className="p-3 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
                <Activity className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Cambios Hoy
                </p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
                  {estadisticas.cambios_hoy}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                  {estadisticas.cambios_semana} esta semana
                </p>
              </div>
              <div className="p-3 bg-green-100 dark:bg-green-900/20 rounded-lg">
                <TrendingUp className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Sin Leer
                </p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
                  {estadisticas.cambios_sin_leer}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                  {estadisticas.cambios_mes} este mes
                </p>
              </div>
              <div className="p-3 bg-orange-100 dark:bg-orange-900/20 rounded-lg">
                <AlertCircle className="h-6 w-6 text-orange-600 dark:text-orange-400" />
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Total Mes
                </p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
                  {estadisticas.cambios_mes}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                  Cambios detectados
                </p>
              </div>
              <div className="p-3 bg-purple-100 dark:bg-purple-900/20 rounded-lg">
                <Bell className="h-6 w-6 text-purple-600 dark:text-purple-400" />
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Tabs: Expedientes / Cambios */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <div className="flex gap-6">
          <button
            onClick={() => setShowChanges(false)}
            className={`pb-3 px-1 border-b-2 transition-colors ${
              !showChanges
                ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
            }`}
          >
            <span className="font-medium">Expedientes Monitoreados</span>
            <Badge className="ml-2">{expedientes.length}</Badge>
          </button>
          <button
            onClick={() => {
              setShowChanges(true)
              setSelectedExpedienteId(undefined)
            }}
            className={`pb-3 px-1 border-b-2 transition-colors ${
              showChanges
                ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
            }`}
          >
            <span className="font-medium">Historial de Cambios</span>
            {estadisticas && estadisticas.cambios_sin_leer > 0 && (
              <Badge className="ml-2 bg-orange-600">{estadisticas.cambios_sin_leer}</Badge>
            )}
          </button>
        </div>
      </div>

      {/* Contenido de tabs */}
      {!showChanges ? (
        /* Tab: Expedientes Monitoreados */
        expedientes.length === 0 ? (
          <Card className="p-12">
            <div className="text-center">
              <Activity className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                No hay expedientes monitoreados
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6 max-w-md mx-auto">
                Agrega expedientes al monitoreo desde el módulo de Expedientes para recibir
                notificaciones automáticas cuando haya cambios
              </p>
              <Button onClick={() => window.location.href = '/expedientes'}>
                <Plus className="h-4 w-4 mr-2" />
                Ir a Expedientes
              </Button>
            </div>
          </Card>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {expedientes.map(expediente => (
              <MonitoreoCard
                key={expediente.id}
                expediente={expediente}
                ejecutando={estadoScheduler?.ejecutando || false}
                onToggle={handleToggleExpediente}
                onRemove={handleRemoverExpediente}
                onVerify={handleVerificarExpediente}
                onViewChanges={handleViewChanges}
              />
            ))}
          </div>
        )
      ) : (
        /* Tab: Historial de Cambios */
        <div>
          {selectedExpedienteId && (
            <div className="mb-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSelectedExpedienteId(undefined)}
              >
                ← Ver todos los cambios
              </Button>
            </div>
          )}
          <LogsList expedienteId={selectedExpedienteId} />
        </div>
      )}
    </div>
  )
}
