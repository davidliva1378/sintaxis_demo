import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import {
  Star,
  Loader2,
  FileText,
  Tag,
  Search,
  ExternalLink,
  Download
} from 'lucide-react'
import { toast } from 'sonner'
import {
  obtenerDestacadosGlobal,
  exportarNotas,
  type DestacadosGlobalResponse,
  type DestacadoGlobal
} from '@/api/analisisApi'

export default function DestacadosPage() {
  const [data, setData] = useState<DestacadosGlobalResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [busqueda, setBusqueda] = useState('')

  useEffect(() => {
    cargarDestacados()
  }, [])

  const cargarDestacados = async () => {
    setIsLoading(true)
    try {
      const result = await obtenerDestacadosGlobal()
      setData(result)
    } catch (error) {
      toast.error('Error al cargar destacados')
      setData({ total_destacados: 0, expedientes: {} })
    } finally {
      setIsLoading(false)
    }
  }

  const handleExportar = async (expedienteNumero: string, formato: 'json' | 'csv') => {
    try {
      await exportarNotas(expedienteNumero, formato)
      toast.success(`Exportado en ${formato.toUpperCase()}`)
    } catch (error) {
      toast.error('Error al exportar')
    }
  }

  // Filtrar expedientes por busqueda
  const expedientesFiltrados = data
    ? Object.entries(data.expedientes).filter(([numero, notas]) => {
        if (!busqueda.trim()) return true
        const term = busqueda.toLowerCase()

        // Buscar en numero de expediente
        if (numero.toLowerCase().includes(term)) return true

        // Buscar en notas y tags
        return notas.some(nota =>
          nota.nota?.toLowerCase().includes(term) ||
          nota.tags.some(tag => tag.toLowerCase().includes(term))
        )
      })
    : []

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Loader2 className="h-12 w-12 animate-spin text-yellow-500" />
        <p className="mt-4 text-gray-600">Cargando destacados...</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <Star className="h-8 w-8 text-yellow-500 fill-yellow-500" />
            Mis Destacados
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Vista global de todas tus actuaciones destacadas
          </p>
        </div>
        <Badge variant="secondary" className="text-lg px-4 py-2">
          {data?.total_destacados || 0} destacados
        </Badge>
      </div>

      {/* Busqueda */}
      <Card>
        <CardContent className="pt-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Buscar en expedientes, notas y tags..."
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              className="pl-9"
            />
          </div>
        </CardContent>
      </Card>

      {/* Lista de expedientes con destacados */}
      {expedientesFiltrados.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Star className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">
              {busqueda ? 'No se encontraron resultados' : 'No tienes actuaciones destacadas'}
            </p>
            <p className="text-sm text-gray-400 mt-2">
              Destaca actuaciones desde la vista de expediente para verlas aqui
            </p>
          </CardContent>
        </Card>
      ) : (
        expedientesFiltrados.map(([expedienteNumero, notas]) => (
          <Card key={expedienteNumero}>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <FileText className="h-5 w-5 text-blue-600" />
                  <CardTitle className="text-lg">{expedienteNumero}</CardTitle>
                  <Badge variant="outline">{notas.length} destacados</Badge>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleExportar(expedienteNumero, 'json')}
                    title="Exportar JSON"
                  >
                    <Download className="h-4 w-4 mr-1" />
                    JSON
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleExportar(expedienteNumero, 'csv')}
                    title="Exportar CSV"
                  >
                    <Download className="h-4 w-4 mr-1" />
                    CSV
                  </Button>
                  <Link to={`/expedientes/${encodeURIComponent(expedienteNumero)}`}>
                    <Button variant="outline" size="sm">
                      <ExternalLink className="h-4 w-4 mr-1" />
                      Ver expediente
                    </Button>
                  </Link>
                </div>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="space-y-3">
                {notas.map((nota) => (
                  <NotaDestacadaCard key={nota.id} nota={nota} />
                ))}
              </div>
            </CardContent>
          </Card>
        ))
      )}
    </div>
  )
}

function NotaDestacadaCard({ nota }: { nota: DestacadoGlobal }) {
  return (
    <div
      className={`p-3 rounded-lg border ${
        nota.color ? '' : 'bg-yellow-50/50 dark:bg-yellow-900/10 border-yellow-200 dark:border-yellow-800'
      }`}
      style={nota.color ? { backgroundColor: nota.color, borderColor: nota.color } : undefined}
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0">
          <div className="w-8 h-8 rounded-full bg-yellow-100 text-yellow-700 flex items-center justify-center font-semibold text-sm">
            {nota.actuacion_indice}
          </div>
        </div>
        <div className="flex-1 min-w-0">
          {nota.nota ? (
            <p className="text-sm text-gray-700 dark:text-gray-300">{nota.nota}</p>
          ) : (
            <p className="text-sm text-gray-400 italic">Sin nota</p>
          )}
          {nota.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {nota.tags.map(tag => (
                <Badge key={tag} variant="secondary" className="text-xs">
                  <Tag className="h-3 w-3 mr-1" />
                  {tag}
                </Badge>
              ))}
            </div>
          )}
        </div>
        <Star className="h-4 w-4 text-yellow-500 fill-yellow-500 flex-shrink-0" />
      </div>
    </div>
  )
}
