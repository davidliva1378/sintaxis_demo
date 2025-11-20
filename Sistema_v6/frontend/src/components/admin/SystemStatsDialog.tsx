import { useEffect, useState } from 'react'
import { BarChart3, HardDrive, FileText, Download, Activity, Calendar } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { adminApi } from '@/api/adminApi'
import { EstadisticasSistema } from '@/types/admin'
import { formatBytes } from '@/lib/utils'

interface SystemStatsDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export default function SystemStatsDialog({ open, onOpenChange }: SystemStatsDialogProps) {
  const [stats, setStats] = useState<EstadisticasSistema | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) {
      loadStats()
    }
  }, [open])

  const loadStats = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await adminApi.getEstadisticas()
      setStats(data)
    } catch (err) {
      setError('Error al cargar estadísticas del sistema')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Estadísticas del Sistema
          </DialogTitle>
          <DialogDescription>
            Información sobre el uso de espacio y recursos del sistema
          </DialogDescription>
        </DialogHeader>

        {loading && (
          <div className="flex items-center justify-center py-8">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100 mx-auto"></div>
              <p className="mt-2 text-sm text-gray-500">Cargando estadísticas...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
          </div>
        )}

        {stats && !loading && (
          <div className="space-y-6">
            {/* Resumen General */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                <div className="flex items-center gap-3">
                  <HardDrive className="h-8 w-8 text-blue-600 dark:text-blue-400" />
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Espacio Total</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {formatBytes(stats.espacio_total_mb * 1024 * 1024)}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                <div className="flex items-center gap-3">
                  <FileText className="h-8 w-8 text-green-600 dark:text-green-400" />
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Expedientes</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {stats.expedientes_procesados}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-4">
                <div className="flex items-center gap-3">
                  <Download className="h-8 w-8 text-purple-600 dark:text-purple-400" />
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">PDFs Descargados</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {stats.pdfs_descargados}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg p-4">
                <div className="flex items-center gap-3">
                  <Activity className="h-8 w-8 text-orange-600 dark:text-orange-400" />
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Sesiones Activas</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {stats.sesiones_activas}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Desglose de Espacio */}
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
                Desglose de Espacio
              </h3>
              <div className="space-y-2">
                <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <span className="text-sm text-gray-700 dark:text-gray-300">Extracción Masiva</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    {formatBytes(stats.desglose.extraccion_masiva_mb * 1024 * 1024)}
                  </span>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <span className="text-sm text-gray-700 dark:text-gray-300">Expedientes</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    {formatBytes(stats.desglose.expedientes_mb * 1024 * 1024)}
                  </span>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <span className="text-sm text-gray-700 dark:text-gray-300">Cache</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    {formatBytes(stats.desglose.cache_mb * 1024 * 1024)}
                  </span>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <span className="text-sm text-gray-700 dark:text-gray-300">Logs</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    {formatBytes(stats.desglose.logs_mb * 1024 * 1024)}
                  </span>
                </div>
              </div>
            </div>

            {/* Último Backup */}
            {stats.ultimo_backup && (
              <div className="flex items-center gap-2 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <Calendar className="h-4 w-4 text-gray-500" />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Último backup: {new Date(stats.ultimo_backup).toLocaleString('es-AR')}
                </span>
              </div>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
