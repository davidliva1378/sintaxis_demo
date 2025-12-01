import { Button } from '@/components/ui/button'
import { Download, FileJson, FileSpreadsheet, FileText } from 'lucide-react'
import { ComparacionDetalladaPanel } from './ComparacionDetalladaPanel'
import type { ExpedienteResumen } from '@/types/expediente'
import type { ProgresoExtraccion } from '@/stores/extraccionStore'
import type { ComparacionDetallada } from '@/types/expediente'

interface ExtraccionReporteProps {
    estado: string
    tipoExtraccion: 'masiva' | 'seleccionados'
    procesarConPDF: boolean
    expedientesExtraidos: ExpedienteResumen[]
    progreso: ProgresoExtraccion
    totalEsperado: number | null
    paginasProcesadas: number
    archivosDescargados: number
    comparacion: ComparacionDetallada | null
    motivoFinalizacion: string | null
    onVolverAFiltrado: () => void
    onCerrar: () => void
    onContinuar: () => void
    onDescargar: (formato: 'json' | 'excel' | 'csv' | 'html') => void
}

export function ExtraccionReporte({
    estado,
    tipoExtraccion,
    procesarConPDF,
    expedientesExtraidos,
    progreso,
    totalEsperado,
    paginasProcesadas,
    archivosDescargados,
    comparacion,
    motivoFinalizacion,
    onVolverAFiltrado,
    onCerrar,
    onContinuar,
    onDescargar
}: ExtraccionReporteProps) {
    if (estado !== 'completado') return null

    return (
        <div className="space-y-6 py-8">
            {/* Header con ícono de éxito */}
            <div className="flex flex-col items-center gap-4">
                <div className="w-16 h-16 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
                    <Download className="h-8 w-8 text-green-600 dark:text-green-400" />
                </div>
                <div className="text-center">
                    <h2 className="text-2xl font-bold text-green-900 dark:text-green-100">
                        {tipoExtraccion === 'masiva'
                            ? '¡Extracción Masiva Completada!'
                            : '¡Procesamiento Completado!'}
                    </h2>
                    <p className="text-gray-600 dark:text-gray-400 mt-1">
                        {tipoExtraccion === 'masiva'
                            ? 'Los expedientes han sido extraídos exitosamente'
                            : 'Los expedientes seleccionados han sido procesados exitosamente'}
                    </p>
                </div>
            </div>

            {/* Motivo de Finalización */}
            {motivoFinalizacion && (
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                        <div className="text-blue-600 dark:text-blue-400 text-lg">
                            ℹ️
                        </div>
                        <div className="flex-1">
                            <h4 className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-1">
                                Motivo de Finalización
                            </h4>
                            <p className="text-sm text-blue-700 dark:text-blue-300">
                                {motivoFinalizacion}
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {/* Estadísticas */}
            <div className={`grid ${procesarConPDF ? 'grid-cols-4' : 'grid-cols-3'} gap-4`}>
                {/* Total Extraído con completitud */}
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                    <div className="text-sm text-blue-600 dark:text-blue-400 font-medium mb-1">
                        Total Extraído
                    </div>
                    <div className="text-3xl font-bold text-blue-900 dark:text-blue-100">
                        {expedientesExtraidos.length}
                    </div>
                    {totalEsperado && totalEsperado > 0 && (
                        <div className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                            de {totalEsperado.toLocaleString()} ({((expedientesExtraidos.length / totalEsperado) * 100).toFixed(1)}%)
                            {expedientesExtraidos.length >= totalEsperado ? ' ✅' : ' ⚠️'}
                        </div>
                    )}
                    {!totalEsperado && (
                        <div className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                            expedientes
                        </div>
                    )}
                </div>

                {/* Tiempo Total */}
                <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-4">
                    <div className="text-sm text-purple-600 dark:text-purple-400 font-medium mb-1">
                        Tiempo Total
                    </div>
                    <div className="text-3xl font-bold text-purple-900 dark:text-purple-100">
                        {(() => {
                            // Calcular duración si hay tiempo_inicio y tiempo_fin en la sesión
                            const inicio = progreso.tiempoTranscurrido || 0
                            const minutos = Math.floor(inicio / 60)
                            const segundos = Math.floor(inicio % 60)
                            return minutos > 0 ? `${minutos}m` : `${segundos}s`
                        })()}
                    </div>
                    <div className="text-xs text-purple-600 dark:text-purple-400 mt-1">
                        duración
                    </div>
                </div>

                {/* Páginas Procesadas (solo para extracción masiva inicial, no para expedientes seleccionados) */}
                {tipoExtraccion === 'masiva' && (
                    <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
                        <div className="text-sm text-amber-600 dark:text-amber-400 font-medium mb-1">
                            Páginas Procesadas
                        </div>
                        <div className="text-3xl font-bold text-amber-900 dark:text-amber-100">
                            {paginasProcesadas || 0}
                        </div>
                        <div className="text-xs text-amber-600 dark:text-amber-400 mt-1">
                            páginas
                        </div>
                    </div>
                )}

                {/* Archivos Descargados (solo si procesarConPDF) */}
                {procesarConPDF && (
                    <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                        <div className="text-sm text-green-600 dark:text-green-400 font-medium mb-1">
                            Archivos Descargados
                        </div>
                        <div className="text-3xl font-bold text-green-900 dark:text-green-100">
                            {archivosDescargados || '0'}
                        </div>
                        <div className="text-xs text-green-600 dark:text-green-400 mt-1">
                            archivos
                        </div>
                    </div>
                )}
            </div>

            {/* Comparación con BASE */}
            {comparacion && (
                <div className="border-t pt-4">
                    <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <span>📊</span> Comparación con BASE
                    </h3>
                    <ComparacionDetalladaPanel comparacion={comparacion} />
                </div>
            )}

            {/* Descarga de Reportes */}
            <div className="flex flex-col items-center gap-3 border-t pt-4">
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Descargar Reporte
                </h3>
                <div className="flex gap-2">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onDescargar('json')}
                        className="gap-2"
                    >
                        <FileJson className="h-4 w-4" />
                        JSON
                    </Button>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onDescargar('excel')}
                        className="gap-2"
                    >
                        <FileSpreadsheet className="h-4 w-4" />
                        Excel
                    </Button>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onDescargar('csv')}
                        className="gap-2"
                    >
                        <FileText className="h-4 w-4" />
                        CSV
                    </Button>
                </div>
            </div>

            {/* Botones contextuales según tipo de extracción */}
            <div className="flex flex-col items-center gap-4 pt-4">
                {tipoExtraccion === 'seleccionados' ? (
                    // Botones para extracción de seleccionados
                    <div className="flex gap-3 justify-center flex-wrap">
                        <Button
                            onClick={onVolverAFiltrado}
                            variant="outline"
                            size="lg"
                        >
                            Procesar Más Expedientes
                        </Button>
                        <Button
                            onClick={onCerrar}
                            size="lg"
                            className="min-w-[150px]"
                        >
                            Cerrar
                        </Button>
                    </div>
                ) : (
                    // Mensaje estático para extracción masiva
                    <>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                            Revise los resultados y presione Continuar para ver el listado.
                        </p>
                        <Button
                            onClick={onContinuar}
                            size="lg"
                            className="min-w-[200px]"
                        >
                            Continuar
                        </Button>
                    </>
                )}
            </div>
        </div>
    )
}
