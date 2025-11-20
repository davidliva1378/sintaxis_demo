import { useState } from 'react'
import { RotateCcw, AlertTriangle, Info, CheckCircle2, Shield, Zap } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Checkbox } from '@/components/ui/checkbox'
import { Switch } from '@/components/ui/switch'
import { Badge } from '@/components/ui/badge'
import { adminApi } from '@/api/adminApi'
import { NivelReseteo, ResultadoReseteo } from '@/types/admin'

interface ResetSystemDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

const NIVELES_INFO = {
  [NivelReseteo.LISTADOS]: {
    label: 'Listados Temporales',
    description: 'Solo elimina listados de extracción masiva (~5 MB)',
    color: 'text-blue-600 dark:text-blue-400',
    impact: 'Mínimo',
  },
  [NivelReseteo.PDFS]: {
    label: 'PDFs de Actuaciones',
    description: 'Elimina todos los PDFs descargados, mantiene JSONs (~680 MB)',
    color: 'text-yellow-600 dark:text-yellow-400',
    impact: 'Moderado',
  },
  [NivelReseteo.EXPEDIENTES]: {
    label: 'Expedientes Completos',
    description: 'Elimina todos los expedientes procesados (~695 MB)',
    color: 'text-orange-600 dark:text-orange-400',
    impact: 'Alto',
  },
  [NivelReseteo.COMPLETO]: {
    label: 'Reset Completo',
    description: 'Elimina todo excepto base de datos y configuración (~700 MB)',
    color: 'text-red-600 dark:text-red-400',
    impact: 'Muy Alto',
  },
  [NivelReseteo.NUCLEAR]: {
    label: 'Reset Nuclear',
    description: 'Elimina absolutamente todo incluyendo base de datos (~700 MB)',
    color: 'text-red-800 dark:text-red-200',
    impact: 'Crítico',
  },
}

export default function ResetSystemDialog({ open, onOpenChange }: ResetSystemDialogProps) {
  const [nivel, setNivel] = useState<NivelReseteo>(NivelReseteo.LISTADOS)
  const [confirmacion, setConfirmacion] = useState('')
  const [crearBackup, setCrearBackup] = useState(true)
  const [dryRun, setDryRun] = useState(true)
  const [incluirProcesamientoMySQL, setIncluirProcesamientoMySQL] = useState(false)
  const [loading, setLoading] = useState(false)
  const [resultado, setResultado] = useState<ResultadoReseteo | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Mostrar opción MySQL solo para niveles COMPLETO y NUCLEAR
  const mostrarOpcionMySQL = nivel === NivelReseteo.COMPLETO || nivel === NivelReseteo.NUCLEAR

  const confirmacionEsperada = `CONFIRMAR-${nivel.toUpperCase()}`
  const confirmacionValida = confirmacion === confirmacionEsperada

  const handleReset = async () => {
    if (!confirmacionValida && !dryRun) {
      setError('La confirmación no coincide')
      return
    }

    setLoading(true)
    setError(null)
    setResultado(null)

    try {
      const result = await adminApi.resetearSistema({
        nivel,
        confirmacion: confirmacionEsperada,
        crear_backup: crearBackup,
        dry_run: dryRun,
        incluir_procesamiento_mysql: mostrarOpcionMySQL ? incluirProcesamientoMySQL : undefined,
      })
      setResultado(result)

      // Si fue exitoso y no era dry-run, resetear el formulario
      if (!dryRun) {
        setConfirmacion('')
        setDryRun(true)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al ejecutar reseteo')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    setNivel(NivelReseteo.LISTADOS)
    setConfirmacion('')
    setCrearBackup(true)
    setDryRun(true)
    setIncluirProcesamientoMySQL(false)
    setResultado(null)
    setError(null)
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <RotateCcw className="h-5 w-5" />
            Resetear Sistema
          </DialogTitle>
          <DialogDescription>
            Elimina datos del sistema según el nivel seleccionado. Use con precaución.
          </DialogDescription>
        </DialogHeader>

        {!resultado ? (
          <div className="space-y-6">
            {/* Selección de Nivel */}
            <div>
              <Label className="text-base font-semibold mb-3 block">Nivel de Reseteo</Label>
              <RadioGroup value={nivel} onValueChange={(value) => setNivel(value as NivelReseteo)}>
                {Object.entries(NIVELES_INFO).map(([key, info]) => (
                  <div
                    key={key}
                    className="flex items-start space-x-3 p-3 rounded-lg border hover:bg-gray-50 dark:hover:bg-gray-800"
                  >
                    <RadioGroupItem value={key} id={key} className="mt-1" />
                    <div className="flex-1">
                      <Label htmlFor={key} className="cursor-pointer">
                        <div className="flex items-center gap-2">
                          <span className={`font-semibold ${info.color}`}>{info.label}</span>
                          <span className="text-xs px-2 py-0.5 rounded-full bg-gray-200 dark:bg-gray-700">
                            {info.impact}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          {info.description}
                        </p>
                      </Label>
                    </div>
                  </div>
                ))}
              </RadioGroup>
            </div>

            {/* Modo de Ejecución - Banner prominente */}
            <div className={`rounded-lg border-2 p-4 ${
              dryRun
                ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-300 dark:border-blue-700'
                : 'bg-red-50 dark:bg-red-900/20 border-red-400 dark:border-red-700'
            }`}>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  {dryRun ? (
                    <Shield className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                  ) : (
                    <Zap className="h-6 w-6 text-red-600 dark:text-red-400" />
                  )}
                  <div>
                    <div className="flex items-center gap-2">
                      <Label className="text-base font-semibold">Modo de Ejecución</Label>
                      <Badge variant={dryRun ? "default" : "destructive"} className="text-xs">
                        {dryRun ? "SIMULACIÓN" : "REAL - PELIGRO"}
                      </Badge>
                    </div>
                    <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                      {dryRun
                        ? "Solo muestra qué se eliminaría, sin borrar nada"
                        : "⚠️ Eliminará archivos permanentemente"}
                    </p>
                  </div>
                </div>
                <Switch
                  id="dryRun"
                  checked={dryRun}
                  onCheckedChange={(checked) => setDryRun(checked)}
                />
              </div>

              {!dryRun && (
                <div className="bg-red-100 dark:bg-red-900/40 border border-red-300 dark:border-red-800 rounded p-3 mt-3">
                  <p className="text-sm font-semibold text-red-900 dark:text-red-200 flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4" />
                    Modo Real Activado
                  </p>
                  <p className="text-xs text-red-800 dark:text-red-300 mt-1">
                    Los archivos se eliminarán permanentemente. Asegúrate de crear un backup.
                  </p>
                </div>
              )}
            </div>

            {/* Opciones adicionales */}
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 rounded-lg border bg-gray-50 dark:bg-gray-800/50">
                <div className="flex items-center gap-2">
                  <Label htmlFor="backup" className="text-sm font-medium cursor-pointer">
                    Crear backup antes de eliminar
                  </Label>
                  {!dryRun && (
                    <Badge variant="outline" className="text-xs">Recomendado</Badge>
                  )}
                </div>
                <Switch
                  id="backup"
                  checked={crearBackup}
                  onCheckedChange={(checked) => setCrearBackup(checked)}
                  disabled={dryRun}
                />
              </div>

              {/* Opción MySQL - solo para COMPLETO y NUCLEAR */}
              {mostrarOpcionMySQL && (
                <div className="flex items-center justify-between p-3 rounded-lg border bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800">
                  <div>
                    <Label htmlFor="mysql" className="text-sm font-medium cursor-pointer">
                      Incluir datos de procesamiento MySQL
                    </Label>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      Elimina clasificaciones, vencimientos y estadísticas
                    </p>
                  </div>
                  <Switch
                    id="mysql"
                    checked={incluirProcesamientoMySQL}
                    onCheckedChange={(checked) => setIncluirProcesamientoMySQL(checked)}
                  />
                </div>
              )}
            </div>

            {/* Confirmación */}
            {!dryRun && (
              <div>
                <Label htmlFor="confirmacion" className="text-sm font-semibold">
                  Confirmación Requerida
                </Label>
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                  Escriba exactamente: <code className="bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded">{confirmacionEsperada}</code>
                </p>
                <Input
                  id="confirmacion"
                  value={confirmacion}
                  onChange={(e) => setConfirmacion(e.target.value)}
                  placeholder={confirmacionEsperada}
                  className={!confirmacionValida && confirmacion ? 'border-red-500' : ''}
                />
              </div>
            )}

            {/* Advertencia */}
            {nivel !== NivelReseteo.LISTADOS && (
              <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
                <div className="flex gap-3">
                  <AlertTriangle className="h-5 w-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-semibold text-amber-900 dark:text-amber-200">
                      Advertencia
                    </p>
                    <p className="text-sm text-amber-800 dark:text-amber-300 mt-1">
                      Esta operación eliminará datos permanentemente. Asegúrese de tener backups antes de continuar.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Error */}
            {error && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {/* Resultado */}
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
              <div className="flex items-center gap-3 mb-3">
                <CheckCircle2 className="h-6 w-6 text-green-600 dark:text-green-400" />
                <div>
                  <p className="font-semibold text-green-900 dark:text-green-200">
                    {resultado.dry_run ? 'Simulación Completada' : 'Reseteo Completado'}
                  </p>
                  <p className="text-sm text-green-700 dark:text-green-300">
                    {new Date(resultado.timestamp).toLocaleString('es-AR')}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-3">
                <div className="bg-white dark:bg-gray-900 rounded p-3">
                  <p className="text-sm text-gray-600 dark:text-gray-400">Archivos {resultado.dry_run ? 'a eliminar' : 'eliminados'}</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {resultado.archivos_eliminados}
                  </p>
                </div>
                <div className="bg-white dark:bg-gray-900 rounded p-3">
                  <p className="text-sm text-gray-600 dark:text-gray-400">Espacio {resultado.dry_run ? 'a liberar' : 'liberado'}</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {resultado.espacio_liberado_mb.toFixed(1)} MB
                  </p>
                </div>
              </div>

              {resultado.backup_path && (
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded p-3 mb-3">
                  <p className="text-xs text-blue-700 dark:text-blue-300">
                    <Info className="h-3 w-3 inline mr-1" />
                    Backup creado en: {resultado.backup_path}
                  </p>
                </div>
              )}

              {resultado.detalles.length > 0 && (
                <div>
                  <p className="text-sm font-semibold text-gray-900 dark:text-white mb-2">Detalles:</p>
                  <ul className="text-sm text-gray-700 dark:text-gray-300 space-y-1">
                    {resultado.detalles.map((detalle, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-gray-400">•</span>
                        <span>{detalle}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}

        <DialogFooter>
          {!resultado ? (
            <>
              <Button variant="outline" onClick={handleClose}>
                Cancelar
              </Button>
              <Button
                onClick={handleReset}
                disabled={loading || (!dryRun && !confirmacionValida)}
                variant={dryRun ? "default" : "destructive"}
                className={
                  dryRun
                    ? 'bg-blue-600 hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-700'
                    : nivel === NivelReseteo.NUCLEAR
                    ? 'bg-red-700 hover:bg-red-800 dark:bg-red-700 dark:hover:bg-red-800'
                    : 'bg-red-600 hover:bg-red-700 dark:bg-red-600 dark:hover:bg-red-700'
                }
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Procesando...
                  </>
                ) : (
                  <>
                    {dryRun ? (
                      <Shield className="mr-2 h-4 w-4" />
                    ) : (
                      <Zap className="mr-2 h-4 w-4" />
                    )}
                    {dryRun ? '🔍 Simular' : '⚠️ Ejecutar'} Reseteo
                  </>
                )}
              </Button>
            </>
          ) : (
            <Button onClick={handleClose}>Cerrar</Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
