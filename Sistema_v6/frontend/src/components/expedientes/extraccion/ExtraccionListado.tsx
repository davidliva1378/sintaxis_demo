import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import type { ExpedienteResumen } from '@/types/expediente'

interface ExtraccionListadoProps {
    expedientesFiltrados: ExpedienteResumen[]
    expedientesSeleccionados: Set<string>
    paginaActual: number
    setPaginaActual: (pagina: number) => void
    itemsPorPagina: number
    onToggleExpediente: (numero: string) => void
    onSeleccionarTodos: (checked: boolean) => void
    formatearFecha: (fecha: string) => string
}

export function ExtraccionListado({
    expedientesFiltrados,
    expedientesSeleccionados,
    paginaActual,
    setPaginaActual,
    itemsPorPagina,
    onToggleExpediente,
    onSeleccionarTodos,
    formatearFecha
}: ExtraccionListadoProps) {
    // Calcular paginación
    const totalPaginas = Math.ceil(expedientesFiltrados.length / itemsPorPagina)
    const indiceInicio = (paginaActual - 1) * itemsPorPagina
    const indiceFin = Math.min(indiceInicio + itemsPorPagina, expedientesFiltrados.length)
    const expedientesPaginados = expedientesFiltrados.slice(indiceInicio, indiceFin)

    return (
        <div className="col-span-9 flex flex-col h-full overflow-hidden border rounded-lg">
            <div className="flex-1 overflow-auto">
                <table className="w-full">
                    <thead className="bg-gray-50 dark:bg-gray-900 sticky top-0 z-10">
                        <tr>
                            <th className="w-12 p-3 text-left">
                                <Checkbox
                                    checked={expedientesSeleccionados.size === expedientesFiltrados.length && expedientesFiltrados.length > 0}
                                    onCheckedChange={(checked) => onSeleccionarTodos(checked as boolean)}
                                />
                            </th>
                            <th className="p-3 text-left text-sm font-medium">Número</th>
                            <th className="p-3 text-left text-sm font-medium">Carátula</th>
                            <th className="p-3 text-left text-sm font-medium">Dependencia</th>
                            <th className="p-3 text-left text-sm font-medium">Situación</th>
                            <th className="p-3 text-left text-sm font-medium">Última Actuación</th>
                        </tr>
                    </thead>
                    <tbody>
                        {expedientesPaginados.map((expediente) => (
                            <tr
                                key={expediente.numero}
                                className={`border-t hover:bg-gray-50 dark:hover:bg-gray-900/50 cursor-pointer ${expediente.ya_agregado ? 'bg-gray-50/50 dark:bg-gray-900/30' : ''}`}
                                onClick={() => !expediente.ya_agregado && onToggleExpediente(expediente.numero)}
                            >
                                <td className="p-3">
                                    <Checkbox
                                        checked={expedientesSeleccionados.has(expediente.numero)}
                                        disabled={!!expediente.ya_agregado}
                                        onClick={(e) => e.stopPropagation()}
                                        onCheckedChange={() => !expediente.ya_agregado && onToggleExpediente(expediente.numero)}
                                    />
                                </td>
                                <td className="p-3 text-sm font-mono">
                                    <div className="flex flex-col">
                                        <span>{expediente.numero}</span>
                                        {expediente.ya_agregado && (
                                            <span className="text-[10px] bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 px-1.5 py-0.5 rounded-full w-fit mt-1">
                                                Ya Agregado
                                            </span>
                                        )}
                                    </div>
                                </td>
                                <td className="p-3 text-sm">{expediente.caratula}</td>
                                <td className="p-3 text-sm text-gray-600 dark:text-gray-400">{expediente.dependencia}</td>
                                <td className="p-3">
                                    <span className={`text-xs px-2 py-1 rounded-full ${expediente.situacion?.toLowerCase().includes('trámite')
                                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100'
                                        : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-100'
                                        }`}>
                                        {expediente.situacion}
                                    </span>
                                </td>
                                <td className="p-3 text-sm text-gray-600 dark:text-gray-400">
                                    {formatearFecha(expediente.ultima_actuacion)}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Controles de Paginación */}
            {expedientesFiltrados.length > itemsPorPagina && (
                <div className="flex items-center justify-between px-4 py-3 border-t bg-white dark:bg-gray-950">
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                        Mostrando {indiceInicio + 1}-{indiceFin} de {expedientesFiltrados.length} expedientes
                    </div>
                    <div className="flex gap-2">
                        <Button
                            variant="outline"
                            size="sm"
                            disabled={paginaActual === 1}
                            onClick={() => setPaginaActual(1)}
                        >
                            Primera
                        </Button>
                        <Button
                            variant="outline"
                            size="sm"
                            disabled={paginaActual === 1}
                            onClick={() => setPaginaActual(paginaActual - 1)}
                        >
                            Anterior
                        </Button>
                        <span className="px-3 py-1 text-sm flex items-center">
                            Página {paginaActual} de {totalPaginas}
                        </span>
                        <Button
                            variant="outline"
                            size="sm"
                            disabled={paginaActual >= totalPaginas}
                            onClick={() => setPaginaActual(paginaActual + 1)}
                        >
                            Siguiente
                        </Button>
                        <Button
                            variant="outline"
                            size="sm"
                            disabled={paginaActual >= totalPaginas}
                            onClick={() => setPaginaActual(totalPaginas)}
                        >
                            Última
                        </Button>
                    </div>
                </div>
            )}
        </div>
    )
}
