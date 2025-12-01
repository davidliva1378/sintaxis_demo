import { useState, useEffect } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  FileText,
  Download,
  Calendar,
  File,
  Eye,
  Search,
  Filter,
  ChevronLeft,
  ChevronRight,
  X
} from 'lucide-react'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'
import { toast } from 'sonner'
import type { Actuacion } from '@/types/expediente'
import PDFViewer from './PDFViewer'
import TextoActuacionPanel from './TextoActuacionPanel'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface ActuacionesListProps {
  actuaciones: Actuacion[]
  expedienteNumero: string
}

export default function ActuacionesList({ actuaciones, expedienteNumero }: ActuacionesListProps) {
  const [pdfViewerOpen, setPdfViewerOpen] = useState(false)
  const [selectedActuacion, setSelectedActuacion] = useState<Actuacion | null>(null)
  const [expandedTexts, setExpandedTexts] = useState<Set<number>>(new Set())

  // Filtros y Paginación
  const [searchTerm, setSearchTerm] = useState(() => {
    return localStorage.getItem(`actuaciones_search_${expedienteNumero}`) || ''
  })
  const [filterType, setFilterType] = useState<string>(() => {
    return localStorage.getItem('actuaciones_filter_type') || 'todos'
  })
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 10

  // Persistencia de filtros
  useEffect(() => {
    localStorage.setItem(`actuaciones_search_${expedienteNumero}`, searchTerm)
  }, [searchTerm, expedienteNumero])

  useEffect(() => {
    localStorage.setItem('actuaciones_filter_type', filterType)
  }, [filterType])

  // Reset página al filtrar
  useEffect(() => {
    setCurrentPage(1)
  }, [searchTerm, filterType])

  const tiposDisponibles = Array.from(new Set(actuaciones.map(a => a.tipo).filter(Boolean))) as string[]

  const filteredActuaciones = actuaciones.filter(act => {
    const matchesSearch = searchTerm === '' ||
      act.detalle?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      act.tipo?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      act.foja?.toString().includes(searchTerm)

    const matchesType = filterType === 'todos' || act.tipo === filterType

    return matchesSearch && matchesType
  })

  const totalPages = Math.ceil(filteredActuaciones.length / itemsPerPage)
  const paginatedActuaciones = filteredActuaciones.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  )
  const handleDescargarPdf = async (indice: number, nombreArchivo: string) => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `${API_BASE_URL}/api/v1/expedientes/${encodeURIComponent(expedienteNumero)}/actuaciones/${indice}/pdf`,
        {
          headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        }
      )

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Error al descargar' }))
        throw new Error(error.detail || `Error ${response.status}`)
      }

      // Crear blob y descargar
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = nombreArchivo
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      toast.success('PDF descargado', { description: nombreArchivo })
    } catch (error) {
      toast.error('Error al descargar PDF', {
        description: error instanceof Error ? error.message : 'Error desconocido'
      })
    }
  }

  const handleVisualizarPdf = (actuacion: Actuacion) => {
    setSelectedActuacion(actuacion)
    setPdfViewerOpen(true)
  }

  const toggleText = (indice: number) => {
    const newSet = new Set(expandedTexts)
    if (newSet.has(indice)) {
      newSet.delete(indice)
    } else {
      newSet.add(indice)
    }
    setExpandedTexts(newSet)
  }
  const formatFecha = (fecha: string | null) => {
    if (!fecha) return 'Sin fecha'

    try {
      const parsedDate = new Date(fecha)
      return format(parsedDate, "dd 'de' MMMM 'de' yyyy", { locale: es })
    } catch {
      return fecha
    }
  }

  if (actuaciones.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500 dark:text-gray-400">
            No hay actuaciones registradas
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {/* Filtros */}
      <div className="flex flex-col sm:flex-row gap-3 bg-gray-50 dark:bg-gray-900/50 p-3 rounded-lg border border-gray-100 dark:border-gray-800">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
          <Input
            placeholder="Buscar por detalle, tipo o foja..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-9 bg-white dark:bg-gray-950"
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className="absolute right-2.5 top-2.5 text-gray-400 hover:text-gray-600"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
        <div className="w-full sm:w-[200px]">
          <Select value={filterType} onValueChange={setFilterType}>
            <SelectTrigger className="bg-white dark:bg-gray-950">
              <div className="flex items-center gap-2">
                <Filter className="h-4 w-4 text-gray-500" />
                <SelectValue placeholder="Tipo de actuación" />
              </div>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="todos">Todos los tipos</SelectItem>
              {tiposDisponibles.map(tipo => (
                <SelectItem key={tipo} value={tipo}>{tipo}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Resumen de resultados */}
      <div className="text-xs text-gray-500 px-1 flex justify-between items-center">
        <span>
          Mostrando {paginatedActuaciones.length} de {filteredActuaciones.length} actuaciones
          {actuaciones.length !== filteredActuaciones.length && ` (filtradas de ${actuaciones.length})`}
        </span>
      </div>

      {/* Lista */}
      {paginatedActuaciones.length === 0 ? (
        <div className="text-center py-12 border-2 border-dashed border-gray-200 dark:border-gray-800 rounded-lg">
          <Search className="h-10 w-10 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No se encontraron actuaciones con los filtros actuales</p>
          <Button variant="link" onClick={() => { setSearchTerm(''); setFilterType('todos') }}>
            Limpiar filtros
          </Button>
        </div>
      ) : (
        paginatedActuaciones.map((actuacion) => (
          <Card key={actuacion.indice}>
            <CardContent className="p-4">
              <div className="flex gap-4">
                {/* Índice */}
                <div className="flex-shrink-0">
                  <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/20 flex items-center justify-center font-semibold text-blue-600">
                    {actuacion.indice}
                  </div>
                </div>

                {/* Contenido */}
                <div className="flex-1 min-w-0 space-y-2">
                  {/* Tipo */}
                  {actuacion.tipo && (
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-500 dark:text-gray-400 min-w-[60px]">
                        Tipo:
                      </span>
                      <Badge variant="outline">
                        {actuacion.tipo}
                      </Badge>
                      {actuacion.tiene_archivo && (
                        <div className="flex items-center gap-2 ml-auto">
                          {/* Indicador de tipo de contenido (OCR vs Texto) */}
                          {actuacion.metodo_extraccion && (
                            <Badge
                              variant="secondary"
                              className={`text-[10px] h-5 px-1.5 ${actuacion.metodo_extraccion.includes('ocr')
                                ? 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400'
                                : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                                }`}
                            >
                              {actuacion.metodo_extraccion.includes('ocr') ? 'PDF IMG' : 'PDF TXT'}
                            </Badge>
                          )}

                          <div className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
                            <File className="h-4 w-4" />
                            {actuacion.tipo_archivo?.toUpperCase() || 'PDF'}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Oficina */}
                  <div className="flex items-start gap-2">
                    <span className="text-sm font-medium text-gray-500 dark:text-gray-400 min-w-[60px]">
                      Oficina:
                    </span>
                    <div>
                      <p className="text-sm text-gray-900 dark:text-white font-medium">
                        {actuacion.oficina}
                      </p>
                      {actuacion.oficina_completa && actuacion.oficina_completa !== actuacion.oficina && (
                        <p className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">
                          ({actuacion.oficina_completa})
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Fecha */}
                  {actuacion.fecha && (
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-500 dark:text-gray-400 min-w-[60px]">
                        Fecha:
                      </span>
                      <div className="flex items-center gap-1 text-sm text-gray-700 dark:text-gray-300">
                        <Calendar className="h-4 w-4" />
                        {formatFecha(actuacion.fecha)}
                      </div>
                    </div>
                  )}

                  {/* Foja */}
                  {actuacion.foja && (
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-500 dark:text-gray-400 min-w-[60px]">
                        Foja:
                      </span>
                      <div className="flex items-center gap-1 text-sm text-gray-700 dark:text-gray-300">
                        <FileText className="h-4 w-4" />
                        {actuacion.foja}
                      </div>
                    </div>
                  )}

                  {/* Detalle */}
                  {actuacion.detalle && (
                    <div className="flex gap-2">
                      <span className="text-sm font-medium text-gray-500 dark:text-gray-400 min-w-[60px] flex-shrink-0">
                        Detalle:
                      </span>
                      <p className="text-sm text-gray-700 dark:text-gray-300 flex-1">
                        {actuacion.detalle}
                      </p>
                    </div>
                  )}

                  {/* Archivo adjunto */}
                  {actuacion.tiene_archivo && actuacion.nombre_archivo && (
                    <>
                      <div className="flex items-center gap-2 mt-2 flex-wrap">
                        <button
                          className="flex items-center gap-1 px-3 py-1 text-sm text-blue-600 bg-blue-50 dark:bg-blue-900/20 rounded hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors"
                          onClick={() => handleVisualizarPdf(actuacion)}
                        >
                          <Eye className="h-4 w-4" />
                          Ver PDF
                        </button>
                        <button
                          className="flex items-center gap-1 px-3 py-1 text-sm text-green-600 bg-green-50 dark:bg-green-900/20 rounded hover:bg-green-100 dark:hover:bg-green-900/30 transition-colors"
                          onClick={() => handleDescargarPdf(actuacion.indice, actuacion.nombre_archivo!)}
                        >
                          <Download className="h-4 w-4" />
                          Descargar
                        </button>
                        <button
                          className={`flex items-center gap-1 px-3 py-1 text-sm rounded transition-colors ${expandedTexts.has(actuacion.indice)
                              ? 'text-purple-700 bg-purple-100 dark:bg-purple-900/30 dark:text-purple-400'
                              : 'text-purple-600 bg-purple-50 dark:bg-purple-900/20 hover:bg-purple-100 dark:hover:bg-purple-900/30'
                            }`}
                          onClick={() => toggleText(actuacion.indice)}
                        >
                          <FileText className="h-4 w-4" />
                          {expandedTexts.has(actuacion.indice) ? 'Ocultar Texto' : 'Ver Texto'}
                        </button>
                        {actuacion.descargado && (
                          <Badge variant="secondary" className="text-xs">
                            Descargado
                          </Badge>
                        )}
                      </div>
                      {/* Panel de texto extraido */}
                      <TextoActuacionPanel
                        expedienteNumero={expedienteNumero}
                        actuacionIndice={actuacion.indice}
                        nombreArchivo={actuacion.nombre_archivo}
                        expanded={expandedTexts.has(actuacion.indice)}
                        onToggle={() => toggleText(actuacion.indice)}
                      />
                    </>
                  )}

                  {/* Marcadores */}
                  <div className="flex gap-2 mt-2">
                    {actuacion.es_historica && (
                      <Badge variant="outline" className="text-xs">
                        Histórica
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))
      )}

      {/* Paginación */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-4 border-t border-gray-100 dark:border-gray-800">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
            disabled={currentPage === 1}
          >
            <ChevronLeft className="h-4 w-4 mr-1" />
            Anterior
          </Button>
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Página {currentPage} de {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
          >
            Siguiente
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
      )}

      {/* PDF Viewer Modal */}
      {selectedActuacion && (
        <PDFViewer
          open={pdfViewerOpen}
          onOpenChange={setPdfViewerOpen}
          expedienteNumero={expedienteNumero}
          actuacionIndice={selectedActuacion.indice}
          actuacionTipo={selectedActuacion.tipo || undefined}
          actuacionFecha={selectedActuacion.fecha || undefined}
          actuacionDetalle={selectedActuacion.detalle || undefined}
          nombreArchivo={selectedActuacion.nombre_archivo!}
        />
      )}
    </div>
  )
}
