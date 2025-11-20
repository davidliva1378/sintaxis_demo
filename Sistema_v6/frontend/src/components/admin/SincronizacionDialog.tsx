import { useEffect, useState } from 'react'
import { Database, RefreshCw, FileJson, AlertCircle, CheckCircle2, XCircle } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { adminApi } from '@/api/adminApi'
import { EstadoSincronizacion, ComparacionSincronizacion, ResultadoSincronizacion } from '@/types/admin'

interface SincronizacionDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export default function SincronizacionDialog({ open, onOpenChange }: SincronizacionDialogProps) {
  const [estado, setEstado] = useState<EstadoSincronizacion | null>(null)
  const [comparacion, setComparacion] = useState<ComparacionSincronizacion | null>(null)
  const [resultado, setResultado] = useState<ResultadoSincronizacion | null>(null)
  const [loading, setLoading] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) {
      loadData()
    } else {
      // Reset state when dialog closes
      setResultado(null)
      setError(null)
    }
  }, [open])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [estadoData, comparacionData] = await Promise.all([
        adminApi.getEstadoSincronizacion(),
        adminApi.compararSincronizacion(50)
      ])
      setEstado(estadoData)
      setComparacion(comparacionData)
    } catch (err) {
      setError('Error al cargar estado de sincronizacion')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleSync = async () => {
    setSyncing(true)
    setError(null)
    setResultado(null)
    try {
      const result = await adminApi.ejecutarSincronizacion()
      setResultado(result)
      // Reload data after sync
      await loadData()
    } catch (err) {
      setError('Error al ejecutar sincronizacion')
      console.error(err)
    } finally {
      setSyncing(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Sincronizacion MySQL
          </DialogTitle>
          <DialogDescription>
            Estado de sincronizacion entre el indice JSON y la base de datos MySQL
          </DialogDescription>
        </DialogHeader>

        {loading && (
          <div className="flex items-center justify-center py-8">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100 mx-auto"></div>
              <p className="mt-2 text-sm text-gray-500">Cargando estado...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-red-600" />
              <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
            </div>
          </div>
        )}

        {estado && !loading && (
          <div className="space-y-6">
            {/* Estado de Sincronizacion */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                <div className="flex items-center gap-3">
                  <FileJson className="h-8 w-8 text-blue-600 dark:text-blue-400" />
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">En JSON</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {estado.total_json}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                <div className="flex items-center gap-3">
                  <Database className="h-8 w-8 text-green-600 dark:text-green-400" />
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">En MySQL</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {estado.total_mysql}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Barra de Progreso */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">Progreso de Sincronizacion</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {estado.porcentaje_sincronizado}%
                </span>
              </div>
              <Progress value={estado.porcentaje_sincronizado} className="h-3" />
              <div className="flex justify-between text-xs text-gray-500">
                <span>{estado.sincronizados} sincronizados</span>
                <span>{estado.pendientes} pendientes</span>
              </div>
            </div>

            {/* Diferencias */}
            {comparacion && comparacion.total_diferencias > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
                  Diferencias Encontradas ({comparacion.total_diferencias})
                </h3>
                <div className="border dark:border-gray-700 rounded-lg overflow-hidden">
                  <div className="max-h-48 overflow-y-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50 dark:bg-gray-800 sticky top-0">
                        <tr>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                            Expediente
                          </th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                            Estado
                          </th>
                          <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                            ID
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                        {comparacion.diferencias.map((diff, idx) => (
                          <tr key={idx} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                            <td className="px-3 py-2 font-mono text-xs">
                              {diff.numero_normalizado}
                            </td>
                            <td className="px-3 py-2">
                              {diff.estado === 'solo_json' ? (
                                <span className="inline-flex items-center gap-1 text-xs text-yellow-600 dark:text-yellow-400">
                                  <AlertCircle className="h-3 w-3" />
                                  Solo en JSON
                                </span>
                              ) : diff.estado === 'solo_mysql' ? (
                                <span className="inline-flex items-center gap-1 text-xs text-red-600 dark:text-red-400">
                                  <XCircle className="h-3 w-3" />
                                  Solo en MySQL
                                </span>
                              ) : (
                                <span className="inline-flex items-center gap-1 text-xs text-orange-600">
                                  Desincronizado
                                </span>
                              )}
                            </td>
                            <td className="px-3 py-2 text-right text-xs text-gray-500">
                              {diff.id_json || diff.id_mysql}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
                <p className="mt-2 text-xs text-gray-500">
                  {comparacion.solo_en_json} solo en JSON, {comparacion.solo_en_mysql} solo en MySQL
                </p>
              </div>
            )}

            {/* Mensaje si esta sincronizado */}
            {comparacion && comparacion.total_diferencias === 0 && (
              <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-green-600" />
                  <p className="text-sm text-green-800 dark:text-green-200">
                    Todo sincronizado correctamente
                  </p>
                </div>
              </div>
            )}

            {/* Resultado de Sincronizacion */}
            {resultado && (
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2">
                  Resultado de Sincronizacion
                </h4>
                <div className="grid grid-cols-4 gap-2 text-sm">
                  <div>
                    <p className="text-gray-500">Procesados</p>
                    <p className="font-bold text-gray-900 dark:text-white">{resultado.procesados}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Creados</p>
                    <p className="font-bold text-green-600">{resultado.creados}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Actualizados</p>
                    <p className="font-bold text-blue-600">{resultado.actualizados}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Errores</p>
                    <p className="font-bold text-red-600">{resultado.errores}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Boton de Sincronizacion */}
            <div className="flex justify-end gap-3">
              <Button variant="outline" onClick={loadData} disabled={loading || syncing}>
                <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Actualizar
              </Button>
              <Button
                onClick={handleSync}
                disabled={syncing || (comparacion?.total_diferencias === 0)}
              >
                {syncing ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Sincronizando...
                  </>
                ) : (
                  <>
                    <Database className="h-4 w-4 mr-2" />
                    Sincronizar Ahora
                  </>
                )}
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
