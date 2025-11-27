import { useEffect, useState, useMemo } from 'react'
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
  Download,
  Edit2,
  Check,
  X,
  Plus,
  Palette,
  Filter,
  BarChart3,
  Trash2
} from 'lucide-react'
import { toast } from 'sonner'
import {
  obtenerDestacadosGlobal,
  exportarNotas,
  actualizarNotaActuacion,
  type DestacadosGlobalResponse,
  type DestacadoGlobal
} from '@/api/analisisApi'
import { cn } from '@/lib/utils'

// Colores disponibles para destacados
const COLORES_DISPONIBLES = [
  { name: 'Amarillo', value: '#fef9c3', border: '#fde047' },
  { name: 'Verde', value: '#dcfce7', border: '#86efac' },
  { name: 'Azul', value: '#dbeafe', border: '#93c5fd' },
  { name: 'Rosa', value: '#fce7f3', border: '#f9a8d4' },
  { name: 'Naranja', value: '#ffedd5', border: '#fdba74' },
  { name: 'Morado', value: '#f3e8ff', border: '#d8b4fe' },
  { name: 'Rojo', value: '#fee2e2', border: '#fca5a5' },
  { name: 'Cyan', value: '#cffafe', border: '#67e8f9' },
]

// Tags sugeridos comunes en contexto legal
const TAGS_SUGERIDOS = [
  'importante', 'urgente', 'revisar', 'sentencia', 'plazo',
  'prueba', 'apelación', 'notificación', 'audiencia', 'pericia'
]

export default function DestacadosPage() {
  const [data, setData] = useState<DestacadosGlobalResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [busqueda, setBusqueda] = useState('')
  const [tagFiltro, setTagFiltro] = useState<string | null>(null)
  const [mostrarEstadisticas, setMostrarEstadisticas] = useState(false)

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

  const handleExportarTodos = async (formato: 'json' | 'csv') => {
    try {
      for (const expedienteNumero of Object.keys(data?.expedientes || {})) {
        await exportarNotas(expedienteNumero, formato)
      }
      toast.success(`Todos los destacados exportados en ${formato.toUpperCase()}`)
    } catch (error) {
      toast.error('Error al exportar')
    }
  }

  // Extraer todos los tags únicos
  const allTags = useMemo(() => {
    if (!data) return []
    const tagSet = new Set<string>()
    Object.values(data.expedientes).forEach(notas => {
      notas.forEach(nota => {
        nota.tags.forEach(tag => tagSet.add(tag))
      })
    })
    return Array.from(tagSet).sort()
  }, [data])

  // Estadísticas de tags
  const tagStats = useMemo(() => {
    if (!data) return {}
    const stats: Record<string, number> = {}
    Object.values(data.expedientes).forEach(notas => {
      notas.forEach(nota => {
        nota.tags.forEach(tag => {
          stats[tag] = (stats[tag] || 0) + 1
        })
      })
    })
    return stats
  }, [data])

  // Filtrar expedientes por busqueda y tag
  const expedientesFiltrados = useMemo(() => {
    if (!data) return []

    return Object.entries(data.expedientes).filter(([numero, notas]) => {
      // Filtro por tag
      if (tagFiltro) {
        const tieneTagt = notas.some(nota => nota.tags.includes(tagFiltro))
        if (!tieneTagt) return false
      }

      // Filtro por búsqueda
      if (!busqueda.trim()) return true
      const term = busqueda.toLowerCase()

      if (numero.toLowerCase().includes(term)) return true

      return notas.some(nota =>
        nota.nota?.toLowerCase().includes(term) ||
        nota.tags.some(tag => tag.toLowerCase().includes(term))
      )
    })
  }, [data, busqueda, tagFiltro])

  // Actualizar nota localmente después de editar
  const handleNotaActualizada = (expedienteNumero: string, notaActualizada: DestacadoGlobal) => {
    if (!data) return
    setData({
      ...data,
      expedientes: {
        ...data.expedientes,
        [expedienteNumero]: data.expedientes[expedienteNumero].map(n =>
          n.id === notaActualizada.id ? notaActualizada : n
        )
      }
    })
  }

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Loader2 className="h-12 w-12 animate-spin text-yellow-500" />
        <p className="mt-4 text-gray-600 dark:text-gray-400">Cargando destacados...</p>
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
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setMostrarEstadisticas(!mostrarEstadisticas)}
          >
            <BarChart3 className="h-4 w-4 mr-1" />
            {mostrarEstadisticas ? 'Ocultar' : 'Estadísticas'}
          </Button>
          <Badge variant="secondary" className="text-lg px-4 py-2">
            {data?.total_destacados || 0} destacados
          </Badge>
        </div>
      </div>

      {/* Estadísticas de Tags */}
      {mostrarEstadisticas && allTags.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Uso de Tags
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {Object.entries(tagStats)
                .sort((a, b) => b[1] - a[1])
                .map(([tag, count]) => (
                  <button
                    key={tag}
                    onClick={() => setTagFiltro(tagFiltro === tag ? null : tag)}
                    className={cn(
                      'inline-flex items-center gap-1 rounded-full px-3 py-1 text-sm transition-colors',
                      tagFiltro === tag
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300'
                    )}
                  >
                    <Tag className="h-3 w-3" />
                    {tag}
                    <span className="ml-1 rounded-full bg-white/20 px-1.5 text-xs">
                      {count}
                    </span>
                  </button>
                ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Búsqueda y Filtros */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Buscar en expedientes, notas y tags..."
                value={busqueda}
                onChange={(e) => setBusqueda(e.target.value)}
                className="pl-9"
              />
            </div>

            {/* Filtro por tags */}
            {allTags.length > 0 && (
              <div className="flex items-center gap-2">
                <Filter className="h-4 w-4 text-gray-400" />
                <select
                  value={tagFiltro || ''}
                  onChange={(e) => setTagFiltro(e.target.value || null)}
                  className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
                >
                  <option value="">Todos los tags</option>
                  {allTags.map(tag => (
                    <option key={tag} value={tag}>{tag} ({tagStats[tag]})</option>
                  ))}
                </select>
              </div>
            )}

            {/* Exportar todos */}
            {(data?.total_destacados || 0) > 0 && (
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleExportarTodos('json')}
                >
                  <Download className="h-4 w-4 mr-1" />
                  Exportar Todo
                </Button>
              </div>
            )}
          </div>

          {/* Tag activo */}
          {tagFiltro && (
            <div className="mt-3 flex items-center gap-2">
              <span className="text-sm text-gray-500">Filtrando por:</span>
              <Badge variant="secondary" className="gap-1">
                <Tag className="h-3 w-3" />
                {tagFiltro}
                <button
                  onClick={() => setTagFiltro(null)}
                  className="ml-1 hover:text-red-500"
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Lista de expedientes con destacados */}
      {expedientesFiltrados.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Star className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 dark:text-gray-400">
              {busqueda || tagFiltro ? 'No se encontraron resultados' : 'No tienes actuaciones destacadas'}
            </p>
            <p className="text-sm text-gray-400 mt-2">
              Destaca actuaciones desde la vista de expediente para verlas aquí
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
                {notas
                  .filter(nota => !tagFiltro || nota.tags.includes(tagFiltro))
                  .map((nota) => (
                    <NotaDestacadaCard
                      key={nota.id}
                      nota={nota}
                      expedienteNumero={expedienteNumero}
                      onActualizada={(n) => handleNotaActualizada(expedienteNumero, n)}
                    />
                  ))}
              </div>
            </CardContent>
          </Card>
        ))
      )}
    </div>
  )
}

interface NotaDestacadaCardProps {
  nota: DestacadoGlobal
  expedienteNumero: string
  onActualizada: (nota: DestacadoGlobal) => void
}

function NotaDestacadaCard({ nota, expedienteNumero, onActualizada }: NotaDestacadaCardProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editNota, setEditNota] = useState(nota.nota || '')
  const [editTags, setEditTags] = useState<string[]>(nota.tags)
  const [editColor, setEditColor] = useState(nota.color)
  const [newTag, setNewTag] = useState('')
  const [showColorPicker, setShowColorPicker] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  const handleSave = async () => {
    setIsSaving(true)
    try {
      await actualizarNotaActuacion(expedienteNumero, nota.actuacion_indice, {
        nota: editNota || null,
        tags: editTags,
        color: editColor
      })
      onActualizada({
        ...nota,
        nota: editNota || null,
        tags: editTags,
        color: editColor
      })
      setIsEditing(false)
      toast.success('Nota actualizada')
    } catch (error) {
      toast.error('Error al guardar')
    } finally {
      setIsSaving(false)
    }
  }

  const handleCancel = () => {
    setEditNota(nota.nota || '')
    setEditTags(nota.tags)
    setEditColor(nota.color)
    setIsEditing(false)
    setShowColorPicker(false)
  }

  const handleAddTag = () => {
    const tag = newTag.trim().toLowerCase()
    if (tag && !editTags.includes(tag)) {
      setEditTags([...editTags, tag])
      setNewTag('')
    }
  }

  const handleRemoveTag = (tagToRemove: string) => {
    setEditTags(editTags.filter(t => t !== tagToRemove))
  }

  const colorInfo = COLORES_DISPONIBLES.find(c => c.value === editColor) ||
    { name: 'Amarillo', value: '#fef9c3', border: '#fde047' }

  const cardStyle = editColor
    ? { backgroundColor: editColor, borderColor: colorInfo.border }
    : undefined

  return (
    <div
      className={cn(
        'p-4 rounded-lg border transition-all',
        !editColor && 'bg-yellow-50/50 dark:bg-yellow-900/10 border-yellow-200 dark:border-yellow-800'
      )}
      style={cardStyle}
    >
      <div className="flex items-start gap-3">
        {/* Índice */}
        <div className="flex-shrink-0">
          <div
            className="w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm"
            style={{
              backgroundColor: editColor ? 'rgba(255,255,255,0.5)' : '#fef3c7',
              color: '#92400e'
            }}
          >
            #{nota.actuacion_indice}
          </div>
        </div>

        {/* Contenido */}
        <div className="flex-1 min-w-0">
          {isEditing ? (
            <div className="space-y-3">
              {/* Editor de nota */}
              <textarea
                value={editNota}
                onChange={(e) => setEditNota(e.target.value)}
                placeholder="Escribe una nota..."
                className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm resize-none dark:border-gray-600 dark:bg-gray-800"
                rows={3}
              />

              {/* Editor de tags */}
              <div className="space-y-2">
                <div className="flex flex-wrap gap-1">
                  {editTags.map(tag => (
                    <Badge key={tag} variant="secondary" className="gap-1">
                      <Tag className="h-3 w-3" />
                      {tag}
                      <button
                        onClick={() => handleRemoveTag(tag)}
                        className="ml-1 hover:text-red-500"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Input
                      value={newTag}
                      onChange={(e) => setNewTag(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddTag())}
                      placeholder="Nuevo tag..."
                      className="h-8 text-sm"
                      list="tags-sugeridos"
                    />
                    <datalist id="tags-sugeridos">
                      {TAGS_SUGERIDOS.filter(t => !editTags.includes(t)).map(tag => (
                        <option key={tag} value={tag} />
                      ))}
                    </datalist>
                  </div>
                  <Button size="sm" variant="outline" onClick={handleAddTag}>
                    <Plus className="h-3 w-3" />
                  </Button>
                </div>
              </div>

              {/* Selector de color */}
              <div className="relative">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setShowColorPicker(!showColorPicker)}
                  className="gap-2"
                >
                  <Palette className="h-3 w-3" />
                  <span
                    className="w-4 h-4 rounded border"
                    style={{ backgroundColor: editColor || '#fef9c3' }}
                  />
                  Color
                </Button>
                {showColorPicker && (
                  <div className="absolute top-full left-0 mt-1 p-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg border z-10">
                    <div className="grid grid-cols-4 gap-2">
                      {COLORES_DISPONIBLES.map(color => (
                        <button
                          key={color.value}
                          onClick={() => {
                            setEditColor(color.value)
                            setShowColorPicker(false)
                          }}
                          className={cn(
                            'w-8 h-8 rounded border-2 transition-transform hover:scale-110',
                            editColor === color.value && 'ring-2 ring-blue-500'
                          )}
                          style={{ backgroundColor: color.value, borderColor: color.border }}
                          title={color.name}
                        />
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Botones de acción */}
              <div className="flex gap-2">
                <Button size="sm" onClick={handleSave} disabled={isSaving}>
                  {isSaving ? (
                    <Loader2 className="h-3 w-3 animate-spin mr-1" />
                  ) : (
                    <Check className="h-3 w-3 mr-1" />
                  )}
                  Guardar
                </Button>
                <Button size="sm" variant="outline" onClick={handleCancel}>
                  <X className="h-3 w-3 mr-1" />
                  Cancelar
                </Button>
              </div>
            </div>
          ) : (
            <>
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
            </>
          )}
        </div>

        {/* Acciones */}
        <div className="flex items-center gap-1">
          {!isEditing && (
            <button
              onClick={() => setIsEditing(true)}
              className="p-1.5 rounded hover:bg-black/10 transition-colors"
              title="Editar"
            >
              <Edit2 className="h-4 w-4 text-gray-500" />
            </button>
          )}
          <Star className="h-4 w-4 text-yellow-500 fill-yellow-500 flex-shrink-0" />
        </div>
      </div>
    </div>
  )
}
