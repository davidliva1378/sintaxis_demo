import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Loader2, Pause, Play, XCircle, FileDown, FileText, Cpu, Database } from 'lucide-react'
import type { ProgresoExtraccion } from '@/stores/extraccionStore'

interface ExtraccionProgresoProps {
    estado: string
    progreso: ProgresoExtraccion
    tipoExtraccion: 'masiva' | 'seleccionados'
    procesarConPDF: boolean
    totalEsperado: number | null
    // Nuevos props para feedback de procesamiento detallado
    expedienteProcesando?: string | null
    actuacionActual?: number
    actuacionesTotal?: number
    faseProcesamiento?: string
    mensajeProcesamiento?: string
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
    expedienteProcesando,
    actuacionActual = 0,
    actuacionesTotal = 0,
    faseProcesamiento = '',
    mensajeProcesamiento = '',
    onPausar,
    onReanudar,
    onCancelar
}: ExtraccionProgresoProps) {
    // Helper para obtener icono de fase
    const getFaseIcon = (fase: string) => {
        if (fase.includes('ia')) return <Cpu className="h-4 w-4 text-purple-500" />
        if (fase.includes('guardando')) return <Database className="h-4 w-4 text-green-500" />
        return <FileText className="h-4 w-4 text-blue-500" />
    }

    // Helper para label de fase
    const getFaseLabel = (fase: string) => {
        switch (fase) {
            case 'iniciando': return 'Iniciando'
            case 'extrayendo': return 'Extrayendo texto'
            case 'guardando': return 'Guardando en BD'
            case 'ia': return 'Procesando con IA'
            default: return fase || 'Procesando...'
        }
    }
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

                    {/* Panel de procesamiento detallado (cuando hay expediente procesándose) */}
                    {expedienteProcesando && actuacionesTotal > 0 && (
                        <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-lg space-y-3">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    {getFaseIcon(faseProcesamiento)}
                                    <span className="font-medium text-blue-900 dark:text-blue-100">
                                        Procesando: {expedienteProcesando}
                                    </span>
                                </div>
                                <span className="text-xs bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded">
                                    {getFaseLabel(faseProcesamiento)}
                                </span>
                            </div>

                            {/* Barra de progreso de actuaciones */}
                            <div className="space-y-1">
                                <div className="flex justify-between text-xs text-blue-700 dark:text-blue-300">
                                    <span>Actuación {actuacionActual} de {actuacionesTotal}</span>
                                    <span>{actuacionesTotal > 0 ? Math.round((actuacionActual / actuacionesTotal) * 100) : 0}%</span>
                                </div>
                                <Progress
                                    value={actuacionesTotal > 0 ? (actuacionActual / actuacionesTotal) * 100 : 0}
                                    className="h-2 bg-blue-100 dark:bg-blue-900"
                                />
                            </div>

                            {/* Mensaje de procesamiento */}
                            {mensajeProcesamiento && (
                                <p className="text-xs text-blue-600 dark:text-blue-400 font-mono truncate">
                                    {mensajeProcesamiento}
                                </p>
                            )}
                        </div>
                    )}

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
