import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Loader2, Pause, Play, XCircle, FileDown } from 'lucide-react'
import type { ProgresoExtraccion } from '@/stores/extraccionStore'

interface ExtraccionProgresoProps {
    estado: string
    progreso: ProgresoExtraccion
    tipoExtraccion: 'masiva' | 'seleccionados'
    procesarConPDF: boolean
    totalEsperado: number | null
    onPausar: () => void
    onReanudar: () => void
    onCancelar: () => void
}

export function ExtraccionProgreso({
    estado,
    progreso,
    tipoExtraccion,
    procesarConPDF,
    totalEsperado,
    onPausar,
    onReanudar,
    onCancelar
}: ExtraccionProgresoProps) {
    return (
        <div className="space-y-6">
            {/* Indicador de inicio cuando está iniciando */}
            {estado === 'iniciando' && (
                <div className="flex flex-col items-center justify-center py-12 space-y-4">
                    <Loader2 className="h-16 w-16 animate-spin text-blue-600" />
                    <div className="text-center space-y-2">
                        <h3 className="font-semibold text-lg">Iniciando Procesamiento</h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                            Preparando {tipoExtraccion === 'masiva' ? 'extracción masiva' : 'procesamiento de expedientes seleccionados'}...
                        </p>
                    </div>
                </div>
            )}

            {/* Barra de progreso (solo mostrar cuando ya está extrayendo o pausado) */}
            {(estado === 'extrayendo' || estado === 'pausado') && (
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
                            <h3 className="font-semibold text-lg">
                                {tipoExtraccion === 'masiva'
                                    ? 'Extracción Masiva en Progreso'
                                    : `Procesando ${progreso.total} Expedientes Seleccionados`}
                            </h3>
                        </div>
                        {procesarConPDF && (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-300 border border-blue-300 dark:border-blue-700 rounded-full">
                                <FileDown className="h-3 w-3" />
                                Descargando PDFs
                            </span>
                        )}
                    </div>
                    <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                        {progreso.total > 0 ? (
                            <>
                                <span className="font-mono">Página {progreso.actual}/{progreso.total}</span>
                                {totalEsperado && totalEsperado > 0 && (
                                    <>
                                        <span>•</span>
                                        <span className="font-semibold text-blue-600">
                                            ~{(progreso.actual * 15).toLocaleString()}/{totalEsperado.toLocaleString()} expedientes
                                        </span>
                                    </>
                                )}
                                <span>•</span>
                                <span>{progreso.porcentaje.toFixed(1)}%</span>
                            </>
                        ) : (
                            <span className="font-mono">Página {progreso.actual} • Calculando total...</span>
                        )}
                    </div>

                    <Progress value={progreso.porcentaje} className="h-3" />

                    {/* Información de progreso */}
                    <div className="grid grid-cols-2 gap-4 text-sm">
                        <div className="space-y-1">
                            <div className="text-gray-600 dark:text-gray-400">Fase Actual</div>
                            <div className="font-semibold">{progreso.fase || 'Iniciando...'}</div>
                        </div>
                        <div className="space-y-1">
                            <div className="text-gray-600 dark:text-gray-400">Estado</div>
                            <div className="font-semibold capitalize">{estado}</div>
                        </div>
                        <div className="space-y-1">
                            <div className="text-gray-600 dark:text-gray-400">Errores</div>
                            <div className="font-semibold text-red-600">{progreso.errores}</div>
                        </div>
                        <div className="space-y-1">
                            <div className="text-gray-600 dark:text-gray-400">Tiempo Transcurrido</div>
                            <div className="font-semibold font-mono">
                                {Math.floor(progreso.tiempoTranscurrido / 60)}:{String(Math.floor(progreso.tiempoTranscurrido % 60)).padStart(2, '0')}
                            </div>
                        </div>
                        {progreso.velocidad && (
                            <div className="space-y-1">
                                <div className="text-gray-600 dark:text-gray-400">Velocidad</div>
                                <div className="font-semibold">{progreso.velocidad.toFixed(2)} exp/s</div>
                            </div>
                        )}
                        {progreso.tiempoEstimado && (
                            <div className="space-y-1">
                                <div className="text-gray-600 dark:text-gray-400">Tiempo Estimado</div>
                                <div className="font-semibold font-mono">
                                    {Math.floor(progreso.tiempoEstimado / 60)}:{String(Math.floor(progreso.tiempoEstimado % 60)).padStart(2, '0')}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Mensaje actual */}
                    <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                        <p className="text-sm font-mono">{progreso.mensaje || 'Esperando actualizaciones...'}</p>
                    </div>

                    {/* Controles de extracción */}
                    <div className="flex gap-2">
                        {estado === 'extrayendo' && (
                            <Button
                                onClick={onPausar}
                                variant="outline"
                                className="flex-1"
                            >
                                <Pause className="h-4 w-4 mr-2" />
                                Pausar
                            </Button>
                        )}
                        {estado === 'pausado' && (
                            <Button
                                onClick={onReanudar}
                                variant="outline"
                                className="flex-1"
                            >
                                <Play className="h-4 w-4 mr-2" />
                                Reanudar
                            </Button>
                        )}
                        <Button
                            onClick={onCancelar}
                            variant="destructive"
                            className="flex-1"
                        >
                            <XCircle className="h-4 w-4 mr-2" />
                            Cancelar
                        </Button>
                    </div>
                </div>
            )}
        </div>
    )
}
