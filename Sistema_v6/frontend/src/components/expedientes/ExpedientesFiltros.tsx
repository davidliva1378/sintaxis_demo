import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Search, X, Filter } from 'lucide-react'
import type { ExpedienteFiltros } from '@/types/expediente'

interface ExpedientesFiltrosProps {
  filtros: ExpedienteFiltros
  onFiltrosChange: (filtros: ExpedienteFiltros) => void
  onLimpiar: () => void
  onBuscar: () => void
}

export default function ExpedientesFiltros({
  filtros,
  onFiltrosChange,
  onLimpiar,
  onBuscar,
}: ExpedientesFiltrosProps) {
  const [mostrarFiltros, setMostrarFiltros] = useState(false)

  const handleChange = (campo: keyof ExpedienteFiltros, valor: string) => {
    onFiltrosChange({
      ...filtros,
      [campo]: valor || undefined,
    })
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      onBuscar()
    }
  }

  const hayFiltrosActivos = Object.keys(filtros).some((key) => filtros[key as keyof ExpedienteFiltros])

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            <CardTitle>Filtros de Búsqueda</CardTitle>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setMostrarFiltros(!mostrarFiltros)}
          >
            {mostrarFiltros ? 'Ocultar' : 'Mostrar'}
          </Button>
        </div>
      </CardHeader>

      {mostrarFiltros && (
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <div className="space-y-2">
              <label className="text-sm font-medium">Número de Expediente</label>
              <Input
                placeholder="Ej: JUZ-FAM-2024-0123"
                value={filtros.numero || ''}
                onChange={(e) => handleChange('numero', e.target.value)}
                onKeyPress={handleKeyPress}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Carátula</label>
              <Input
                placeholder="Buscar en carátula..."
                value={filtros.caratula || ''}
                onChange={(e) => handleChange('caratula', e.target.value)}
                onKeyPress={handleKeyPress}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Dependencia</label>
              <Input
                placeholder="Ej: JUZGADO DE FAMILIA"
                value={filtros.dependencia || ''}
                onChange={(e) => handleChange('dependencia', e.target.value)}
                onKeyPress={handleKeyPress}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Situación</label>
              <Input
                placeholder="Ej: EN TRAMITE"
                value={filtros.situacion || ''}
                onChange={(e) => handleChange('situacion', e.target.value)}
                onKeyPress={handleKeyPress}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Fecha Desde</label>
              <Input
                type="date"
                value={filtros.fecha_desde || ''}
                onChange={(e) => handleChange('fecha_desde', e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Fecha Hasta</label>
              <Input
                type="date"
                value={filtros.fecha_hasta || ''}
                onChange={(e) => handleChange('fecha_hasta', e.target.value)}
              />
            </div>
          </div>

          <div className="flex gap-2 mt-4">
            <Button onClick={onBuscar} className="flex-1">
              <Search className="h-4 w-4 mr-2" />
              Buscar
            </Button>
            {hayFiltrosActivos && (
              <Button onClick={onLimpiar} variant="outline">
                <X className="h-4 w-4 mr-2" />
                Limpiar
              </Button>
            )}
          </div>
        </CardContent>
      )}
    </Card>
  )
}
