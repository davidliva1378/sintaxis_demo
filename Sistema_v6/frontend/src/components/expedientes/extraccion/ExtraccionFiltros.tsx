import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Filter } from 'lucide-react'
import type { ExpedienteFiltros } from '@/types/expediente'

interface ExtraccionFiltrosProps {
    filtros: ExpedienteFiltros
    setFiltros: (filtros: ExpedienteFiltros) => void
    opcionesDependencia: Array<{ valor: string; count: number }>
    opcionesSituacion: Array<{ valor: string; count: number }>
    onLimpiar: () => void
    maximizado: boolean
}

export function ExtraccionFiltros({
    filtros,
    setFiltros,
    opcionesDependencia,
    opcionesSituacion,
    onLimpiar,
    maximizado
}: ExtraccionFiltrosProps) {
    return (
        <div className={`col-span-3 space-y-4 overflow-y-auto pr-2 ${maximizado ? 'max-h-[calc(95vh-12rem)]' : ''
            }`}>
            <div className="flex items-center justify-between">
                <h3 className="font-semibold flex items-center gap-2">
                    <Filter className="h-4 w-4" />
                    Filtros
                </h3>
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={onLimpiar}
                >
                    Limpiar
                </Button>
            </div>

            {/* Búsqueda por texto */}
            <div className="space-y-2">
                <label className="text-sm font-medium">Buscar</label>
                <Input
                    placeholder="Número, carátula..."
                    value={filtros.numero || filtros.caratula || ''} // Simplificado para el ejemplo, idealmente separar
                    onChange={(e) => setFiltros({ ...filtros, numero: e.target.value, caratula: e.target.value })}
                />
                {/* Nota: El componente original usaba filtros.texto que no está en la interfaz ExpedienteFiltros estándar, 
            asumimos que se mapea a numero/caratula o se debe extender la interfaz */}
            </div>

            {/* Dependencia (múltiple con checkboxes) */}
            <div className="space-y-2">
                <div className="flex items-center justify-between">
                    <label className="text-sm font-medium">Dependencia</label>
                    <div className="flex gap-1">
                        <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 text-xs"
                            onClick={() => setFiltros({
                                ...filtros,
                                dependencia: opcionesDependencia.map(o => o.valor)
                            })}
                        >
                            Todas
                        </Button>
                        <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 text-xs"
                            onClick={() => setFiltros({ ...filtros, dependencia: [] })}
                        >
                            Ninguna
                        </Button>
                    </div>
                </div>
                <div className="space-y-1 max-h-48 overflow-y-auto border rounded p-2">
                    {opcionesDependencia.map(({ valor, count }) => (
                        <div key={valor} className="flex items-center space-x-2">
                            <Checkbox
                                id={`dep-${valor}`}
                                checked={filtros.dependencia?.includes(valor)}
                                onCheckedChange={(checked) => {
                                    const deps = filtros.dependencia || []
                                    if (checked) {
                                        setFiltros({
                                            ...filtros,
                                            dependencia: [...deps, valor]
                                        })
                                    } else {
                                        setFiltros({
                                            ...filtros,
                                            dependencia: deps.filter(d => d !== valor)
                                        })
                                    }
                                }}
                            />
                            <label
                                htmlFor={`dep-${valor}`}
                                className="text-xs flex-1 cursor-pointer"
                            >
                                {valor} ({count})
                            </label>
                        </div>
                    ))}
                </div>
            </div>

            {/* Situación Procesal (dinámico con checkboxes) */}
            <div className="space-y-2">
                <div className="flex items-center justify-between">
                    <label className="text-sm font-medium">Situación Procesal</label>
                    <div className="flex gap-1">
                        <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 text-xs"
                            onClick={() => setFiltros({
                                ...filtros,
                                situacion: opcionesSituacion.map(o => o.valor)
                            })}
                        >
                            Todas
                        </Button>
                        <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 text-xs"
                            onClick={() => setFiltros({ ...filtros, situacion: [] })}
                        >
                            Ninguna
                        </Button>
                    </div>
                </div>
                <div className="space-y-1">
                    {opcionesSituacion.map(({ valor, count }) => (
                        <div key={valor} className="flex items-center space-x-2">
                            <Checkbox
                                id={`sit-${valor}`}
                                checked={filtros.situacion?.includes(valor)}
                                onCheckedChange={(checked) => {
                                    const sits = filtros.situacion || []
                                    if (checked) {
                                        setFiltros({
                                            ...filtros,
                                            situacion: [...sits, valor]
                                        })
                                    } else {
                                        setFiltros({
                                            ...filtros,
                                            situacion: sits.filter(s => s !== valor)
                                        })
                                    }
                                }}
                            />
                            <label
                                htmlFor={`sit-${valor}`}
                                className="text-sm cursor-pointer"
                            >
                                {valor} ({count})
                            </label>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}
