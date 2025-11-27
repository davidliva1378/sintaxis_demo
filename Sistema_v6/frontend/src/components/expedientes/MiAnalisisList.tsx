import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import {
  Star,
  StarOff,
  MessageSquare,
  Tag,
  Trash2,
  Save,
  X,
  Plus,
  Loader2,
  StickyNote,
  Filter,
  Palette,
  Search,
  Download
} from 'lucide-react'
import { toast } from 'sonner'
import {
  obtenerNotasExpediente,
  crearNotaActuacion,
  eliminarNotaActuacion,
  toggleDestacado,
  type NotaActuacion,
  type NotasExpediente
} from '@/api/analisisApi'
import type { Actuacion } from '@/types/expediente'

interface MiAnalisisListProps {
  actuaciones: Actuacion[]
  expedienteNumero: string
}

// Colores predefinidos para notas
const COLORES_NOTA = [
  { value: null, label: 'Sin color', bg: 'bg-blue-50 dark:bg-blue-900/20', preview: 'bg-gray-200' },
  { value: '#fef3c7', label: 'Amarillo', bg: 'bg-amber-100', preview: 'bg-amber-200' },
  { value: '#dcfce7', label: 'Verde', bg: 'bg-green-100', preview: 'bg-green-300' },
  { value: '#dbeafe', label: 'Azul', bg: 'bg-blue-100', preview: 'bg-blue-300' },
  { value: '#fce7f3', label: 'Rosa', bg: 'bg-pink-100', preview: 'bg-pink-300' },
  { value: '#f3e8ff', label: 'Morado', bg: 'bg-purple-100', preview: 'bg-purple-300' },
  { value: '#ffedd5', label: 'Naranja', bg: 'bg-orange-100', preview: 'bg-orange-300' },
]

export default function MiAnalisisList({ actuaciones, expedienteNumero }: MiAnalisisListProps) {
  const [notasData, setNotasData] = useState<NotasExpediente | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [editingIndice, setEditingIndice] = useState<number | null>(null)
  const [editNota, setEditNota] = useState('')
  const [editTags, setEditTags] = useState<string[]>([])
  const [editColor, setEditColor] = useState<string | null>(null)
  const [newTag, setNewTag] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [filtro, setFiltro] = useState<'todas' | 'destacadas' | 'con_notas'>('todas')
  const [busquedaTag, setBusquedaTag] = useState('')

  useEffect(() => {
    cargarNotas()
  }, [expedienteNumero])

  const cargarNotas = async () => {
    try {
      setIsLoading(true)
      const data = await obtenerNotasExpediente(expedienteNumero)
      setNotasData(data)
    } catch (error) {
      // Si no hay notas, inicializar vacio
      setNotasData({
        expediente_numero: expedienteNumero,
        total_notas: 0,
        total_destacados: 0,
        notas: []
      })
    } finally {
      setIsLoading(false)
    }
  }

  const getNotaForActuacion = (indice: number): NotaActuacion | undefined => {
    return notasData?.notas.find(n => n.actuacion_indice === indice)
  }

  const handleToggleDestacado = async (indice: number) => {
    try {
      const result = await toggleDestacado(expedienteNumero, indice)
      await cargarNotas()
      toast.success(result.destacado ? 'Actuacion destacada' : 'Destacado removido')
    } catch (error) {
      toast.error('Error al cambiar destacado')
    }
  }

  const handleStartEdit = (actuacion: Actuacion) => {
    const nota = getNotaForActuacion(actuacion.indice)
    setEditingIndice(actuacion.indice)
    setEditNota(nota?.nota || '')
    setEditTags(nota?.tags || [])
    setEditColor(nota?.color || null)
  }

  const handleCancelEdit = () => {
    setEditingIndice(null)
    setEditNota('')
    setEditTags([])
    setEditColor(null)
    setNewTag('')
  }

  const handleAddTag = () => {
    if (newTag.trim() && !editTags.includes(newTag.trim())) {
      setEditTags([...editTags, newTag.trim()])
      setNewTag('')
    }
  }

  const handleRemoveTag = (tag: string) => {
    setEditTags(editTags.filter(t => t !== tag))
  }

  const handleSaveNota = async () => {
    if (editingIndice === null) return

    setIsSaving(true)
    try {
      await crearNotaActuacion(expedienteNumero, {
        actuacion_indice: editingIndice,
        nota: editNota || null,
        tags: editTags,
        destacado: getNotaForActuacion(editingIndice)?.destacado || false,
        color: editColor
      })
      await cargarNotas()
      handleCancelEdit()
      toast.success('Nota guardada')
    } catch (error) {
      toast.error('Error al guardar nota')
    } finally {
      setIsSaving(false)
    }
  }

  const handleDeleteNota = async (indice: number) => {
    try {
      await eliminarNotaActuacion(expedienteNumero, indice)
      await cargarNotas()
      toast.success('Nota eliminada')
    } catch (error) {
      toast.error('Error al eliminar nota')
    }
  }

  const handleExportar = () => {
    if (!notasData || notasData.total_notas === 0) {
      toast.error('No hay notas para exportar')
      return
    }

    // Preparar datos para exportar
    const exportData = {
      expediente: expedienteNumero,
      fecha_exportacion: new Date().toISOString(),
      total_notas: notasData.total_notas,
      total_destacados: notasData.total_destacados,
      notas: notasData.notas.map(nota => {
        const actuacion = actuaciones.find(a => a.indice === nota.actuacion_indice)
        return {
          actuacion_indice: nota.actuacion_indice,
          actuacion_tipo: actuacion?.tipo || '',
          actuacion_fecha: actuacion?.fecha || '',
          actuacion_detalle: actuacion?.detalle || '',
          nota: nota.nota,
          tags: nota.tags,
          destacado: nota.destacado,
          color: nota.color
        }
      })
    }

    // Crear archivo y descargar
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `analisis_${expedienteNumero.replace(/\//g, '_')}_${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)

    toast.success('Analisis exportado correctamente')
  }

  // Filtrar actuaciones
  const actuacionesFiltradas = actuaciones.filter(act => {
    const nota = getNotaForActuacion(act.indice)

    // Filtro por estado
    if (filtro === 'destacadas') {
      if (!nota?.destacado) return false
    }
    if (filtro === 'con_notas') {
      if (!nota || (!nota.nota && nota.tags.length === 0)) return false
    }

    // Búsqueda por tags
    if (busquedaTag.trim()) {
      const searchTerm = busquedaTag.toLowerCase().trim()
      const matchTags = nota?.tags.some(tag => tag.toLowerCase().includes(searchTerm))
      const matchNota = nota?.nota?.toLowerCase().includes(searchTerm)
      if (!matchTags && !matchNota) return false
    }

    return true
  })

  if (isLoading) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-500">Cargando analisis...</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header con filtros */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg flex items-center gap-2">
              <StickyNote className="h-5 w-5" />
              Mi Analisis
            </CardTitle>
            <div className="flex items-center gap-2">
              <Badge variant="outline">
                {notasData?.total_notas || 0} notas
              </Badge>
              <Badge variant="secondary">
                {notasData?.total_destacados || 0} destacadas
              </Badge>
              <Button
                variant="outline"
                size="sm"
                onClick={handleExportar}
                disabled={!notasData || notasData.total_notas === 0}
                title="Exportar analisis a JSON"
              >
                <Download className="h-4 w-4 mr-1" />
                Exportar
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-0 space-y-3">
          {/* Búsqueda */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Buscar en notas y tags..."
              value={busquedaTag}
              onChange={(e) => setBusquedaTag(e.target.value)}
              className="pl-9"
            />
          </div>
          {/* Filtros */}
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-gray-500" />
            <div className="flex gap-1">
              <Button
                variant={filtro === 'todas' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFiltro('todas')}
              >
                Todas ({actuaciones.length})
              </Button>
              <Button
                variant={filtro === 'destacadas' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFiltro('destacadas')}
              >
                Destacadas ({notasData?.total_destacados || 0})
              </Button>
              <Button
                variant={filtro === 'con_notas' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFiltro('con_notas')}
              >
                Con notas ({notasData?.total_notas || 0})
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Lista de actuaciones */}
      {actuacionesFiltradas.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center">
            <StickyNote className="h-10 w-10 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">
              {filtro === 'todas'
                ? 'No hay actuaciones'
                : filtro === 'destacadas'
                ? 'No hay actuaciones destacadas'
                : 'No hay actuaciones con notas'}
            </p>
          </CardContent>
        </Card>
      ) : (
        actuacionesFiltradas.map((actuacion) => {
          const nota = getNotaForActuacion(actuacion.indice)
          const isEditing = editingIndice === actuacion.indice

          return (
            <Card key={actuacion.indice} className={nota?.destacado ? 'border-yellow-400 bg-yellow-50/50 dark:bg-yellow-900/10' : ''}>
              <CardContent className="p-4">
                <div className="flex gap-4">
                  {/* Indice */}
                  <div className="flex-shrink-0">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                      nota?.destacado
                        ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30'
                        : 'bg-gray-100 text-gray-600 dark:bg-gray-800'
                    }`}>
                      {actuacion.indice}
                    </div>
                  </div>

                  {/* Contenido */}
                  <div className="flex-1 min-w-0 space-y-2">
                    {/* Tipo y acciones */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {actuacion.tipo && (
                          <Badge variant="outline" className="text-xs">
                            {actuacion.tipo}
                          </Badge>
                        )}
                        {actuacion.fecha && (
                          <span className="text-xs text-gray-500">
                            {actuacion.fecha}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleToggleDestacado(actuacion.indice)}
                          title={nota?.destacado ? 'Quitar destacado' : 'Destacar'}
                        >
                          {nota?.destacado ? (
                            <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                          ) : (
                            <StarOff className="h-4 w-4 text-gray-400" />
                          )}
                        </Button>
                        {!isEditing && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleStartEdit(actuacion)}
                            title="Agregar/editar nota"
                          >
                            <MessageSquare className="h-4 w-4" />
                          </Button>
                        )}
                        {nota && !isEditing && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteNota(actuacion.indice)}
                            className="text-red-500 hover:text-red-700"
                            title="Eliminar nota"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </div>

                    {/* Detalle */}
                    {actuacion.detalle && (
                      <p className="text-sm text-gray-700 dark:text-gray-300">
                        {actuacion.detalle}
                      </p>
                    )}

                    {/* Nota existente (modo vista) */}
                    {nota && !isEditing && (
                      <div
                        className={`mt-3 p-3 rounded-md space-y-2 ${
                          nota.color ? '' : 'bg-blue-50 dark:bg-blue-900/20'
                        }`}
                        style={nota.color ? { backgroundColor: nota.color } : undefined}
                      >
                        {nota.nota && (
                          <p className="text-sm text-gray-700 dark:text-gray-300">
                            {nota.nota}
                          </p>
                        )}
                        {nota.tags.length > 0 && (
                          <div className="flex flex-wrap gap-1">
                            {nota.tags.map(tag => (
                              <Badge key={tag} variant="secondary" className="text-xs">
                                <Tag className="h-3 w-3 mr-1" />
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Editor de nota */}
                    {isEditing && (
                      <div className="mt-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-md space-y-3">
                        <Textarea
                          placeholder="Escribe tu nota aqui..."
                          value={editNota}
                          onChange={(e) => setEditNota(e.target.value)}
                          rows={3}
                        />

                        {/* Tags */}
                        <div className="space-y-2">
                          <div className="flex flex-wrap gap-1">
                            {editTags.map(tag => (
                              <Badge key={tag} variant="secondary" className="text-xs">
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
                            <Input
                              placeholder="Agregar etiqueta..."
                              value={newTag}
                              onChange={(e) => setNewTag(e.target.value)}
                              onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddTag())}
                              className="flex-1"
                            />
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={handleAddTag}
                            >
                              <Plus className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>

                        {/* Selector de color */}
                        <div className="space-y-2">
                          <div className="flex items-center gap-2">
                            <Palette className="h-4 w-4 text-gray-500" />
                            <span className="text-sm text-gray-600">Color de nota</span>
                          </div>
                          <div className="flex flex-wrap gap-2">
                            {COLORES_NOTA.map((color) => (
                              <button
                                key={color.label}
                                onClick={() => setEditColor(color.value)}
                                className={`w-6 h-6 rounded-full ${color.preview} border-2 transition-all ${
                                  editColor === color.value
                                    ? 'border-blue-500 scale-110'
                                    : 'border-transparent hover:border-gray-400'
                                }`}
                                title={color.label}
                              />
                            ))}
                          </div>
                        </div>

                        {/* Acciones */}
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={handleCancelEdit}
                          >
                            Cancelar
                          </Button>
                          <Button
                            size="sm"
                            onClick={handleSaveNota}
                            disabled={isSaving}
                          >
                            {isSaving ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <>
                                <Save className="h-4 w-4 mr-1" />
                                Guardar
                              </>
                            )}
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })
      )}
    </div>
  )
}
