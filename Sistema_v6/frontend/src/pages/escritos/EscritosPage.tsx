import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import {
  FileText,
  Plus,
  Edit2,
  Trash2,
  Send,
  CheckCircle,
  Loader2,
  FileEdit,
  Clock,
  Files,
  LayoutTemplate
} from 'lucide-react'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'
import { toast } from 'sonner'
import {
  listarEscritos,
  crearEscrito,
  actualizarEscrito,
  eliminarEscrito,
  marcarPresentado,
  confirmarPresentacion,
  obtenerEstadisticas,
  listarPlantillas
} from '@/api/escritosApi'
import type { Escrito, EstadisticasEscritos, Plantilla, EstadoEscrito } from '@/types/escritos'

export default function EscritosPage() {
  const [escritos, setEscritos] = useState<Escrito[]>([])
  const [plantillas, setPlantillas] = useState<Plantilla[]>([])
  const [estadisticas, setEstadisticas] = useState<EstadisticasEscritos | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingEscrito, setEditingEscrito] = useState<Escrito | null>(null)
  const [filtroEstado, setFiltroEstado] = useState<string>('')

  // Form state
  const [titulo, setTitulo] = useState('')
  const [contenido, setContenido] = useState('')
  const [expedienteNumero, setExpedienteNumero] = useState('')
  const [plantillaId, setPlantillaId] = useState<number | null>(null)
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    cargarDatos()
  }, [filtroEstado])

  const cargarDatos = async () => {
    setIsLoading(true)
    try {
      const [escritosData, statsData, plantillasData] = await Promise.all([
        listarEscritos(filtroEstado ? { estado: filtroEstado as EstadoEscrito } : {}),
        obtenerEstadisticas(),
        listarPlantillas()
      ])
      setEscritos(escritosData)
      setEstadisticas(statsData)
      setPlantillas(plantillasData)
    } catch (error) {
      toast.error('Error al cargar escritos')
    } finally {
      setIsLoading(false)
    }
  }

  const handlePlantillaSelect = (plantillaIdStr: string) => {
    const id = parseInt(plantillaIdStr)
    setPlantillaId(id || null)
    if (id) {
      const plantilla = plantillas.find(p => p.id === id)
      if (plantilla) {
        setContenido(plantilla.contenido)
        if (!titulo) {
          setTitulo(plantilla.nombre)
        }
      }
    }
  }

  const handleCrearEscrito = async () => {
    if (!titulo.trim() || !contenido.trim()) {
      toast.error('Titulo y contenido son requeridos')
      return
    }

    setIsSaving(true)
    try {
      if (editingEscrito) {
        await actualizarEscrito(editingEscrito.id, {
          titulo: titulo.trim(),
          contenido: contenido.trim(),
          expediente_numero: expedienteNumero.trim() || null
        })
        toast.success('Escrito actualizado')
      } else {
        await crearEscrito({
          titulo: titulo.trim(),
          contenido: contenido.trim(),
          expediente_numero: expedienteNumero.trim() || null,
          plantilla_id: plantillaId
        })
        toast.success('Escrito creado')
      }
      resetForm()
      await cargarDatos()
    } catch (error) {
      toast.error('Error al guardar escrito')
    } finally {
      setIsSaving(false)
    }
  }

  const handleEditar = (escrito: Escrito) => {
    setEditingEscrito(escrito)
    setTitulo(escrito.titulo)
    setContenido(escrito.contenido)
    setExpedienteNumero(escrito.expediente_numero || '')
    setPlantillaId(escrito.plantilla_id)
    setShowForm(true)
  }

  const handleEliminar = async (escritoId: number) => {
    if (!confirm('Eliminar este escrito?')) return
    try {
      await eliminarEscrito(escritoId)
      toast.success('Escrito eliminado')
      await cargarDatos()
    } catch (error) {
      toast.error('Error al eliminar escrito')
    }
  }

  const handlePresentar = async (escritoId: number) => {
    try {
      await marcarPresentado(escritoId)
      toast.success('Escrito marcado como presentado')
      await cargarDatos()
    } catch (error) {
      toast.error('Error al marcar como presentado')
    }
  }

  const handleConfirmar = async (escritoId: number) => {
    try {
      await confirmarPresentacion(escritoId)
      toast.success('Presentacion confirmada')
      await cargarDatos()
    } catch (error) {
      toast.error('Error al confirmar presentacion')
    }
  }

  const resetForm = () => {
    setShowForm(false)
    setEditingEscrito(null)
    setTitulo('')
    setContenido('')
    setExpedienteNumero('')
    setPlantillaId(null)
  }

  const formatFecha = (fecha: string) => {
    try {
      return format(new Date(fecha), "dd MMM yyyy HH:mm", { locale: es })
    } catch {
      return fecha
    }
  }

  const getEstadoColor = (estado: EstadoEscrito) => {
    switch (estado) {
      case 'borrador': return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400'
      case 'revision': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
      case 'presentado': return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400'
      case 'confirmado': return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
    }
  }

  const getEstadoLabel = (estado: EstadoEscrito) => {
    switch (estado) {
      case 'borrador': return 'Borrador'
      case 'revision': return 'En Revision'
      case 'presentado': return 'Presentado'
      case 'confirmado': return 'Confirmado'
    }
  }

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
        <p className="mt-4 text-gray-600">Cargando escritos...</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Escritos</h1>
          <p className="text-gray-600 dark:text-gray-400">Gestiona tus escritos judiciales</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>
          <Plus className="h-4 w-4 mr-2" />
          Nuevo Escrito
        </Button>
      </div>

      {/* Stats */}
      {estadisticas && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">Total</p>
                  <p className="text-2xl font-bold">{estadisticas.total_escritos}</p>
                </div>
                <Files className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">Borradores</p>
                  <p className="text-2xl font-bold">{estadisticas.borradores}</p>
                </div>
                <FileEdit className="h-8 w-8 text-gray-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">Presentados</p>
                  <p className="text-2xl font-bold">{estadisticas.presentados}</p>
                </div>
                <Send className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">Confirmados</p>
                  <p className="text-2xl font-bold text-green-600">{estadisticas.confirmados}</p>
                </div>
                <CheckCircle className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Form */}
      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>{editingEscrito ? 'Editar Escrito' : 'Nuevo Escrito'}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="text-sm font-medium">Titulo</label>
                <Input
                  value={titulo}
                  onChange={(e) => setTitulo(e.target.value)}
                  placeholder="Titulo del escrito"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Expediente (opcional)</label>
                <Input
                  value={expedienteNumero}
                  onChange={(e) => setExpedienteNumero(e.target.value)}
                  placeholder="Numero de expediente"
                />
              </div>
            </div>
            {!editingEscrito && plantillas.length > 0 && (
              <div>
                <label className="text-sm font-medium">Plantilla (opcional)</label>
                <select
                  className="w-full h-10 px-3 rounded-md border border-input bg-background"
                  value={plantillaId || ''}
                  onChange={(e) => handlePlantillaSelect(e.target.value)}
                >
                  <option value="">Sin plantilla</option>
                  {plantillas.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.nombre} ({p.categoria})
                    </option>
                  ))}
                </select>
              </div>
            )}
            <div>
              <label className="text-sm font-medium">Contenido</label>
              <Textarea
                value={contenido}
                onChange={(e) => setContenido(e.target.value)}
                placeholder="Contenido del escrito..."
                rows={12}
                className="font-mono text-sm"
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={resetForm}>
                Cancelar
              </Button>
              <Button onClick={handleCrearEscrito} disabled={isSaving}>
                {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : (editingEscrito ? 'Actualizar' : 'Crear')}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filtros */}
      <div className="flex gap-2">
        <Button
          variant={filtroEstado === '' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setFiltroEstado('')}
        >
          Todos
        </Button>
        <Button
          variant={filtroEstado === 'borrador' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setFiltroEstado('borrador')}
        >
          Borradores
        </Button>
        <Button
          variant={filtroEstado === 'presentado' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setFiltroEstado('presentado')}
        >
          Presentados
        </Button>
        <Button
          variant={filtroEstado === 'confirmado' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setFiltroEstado('confirmado')}
        >
          Confirmados
        </Button>
      </div>

      {/* Lista de Escritos */}
      <Card>
        <CardHeader>
          <CardTitle>Mis Escritos</CardTitle>
        </CardHeader>
        <CardContent>
          {escritos.length === 0 ? (
            <div className="py-8 text-center">
              <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">No hay escritos</p>
            </div>
          ) : (
            <div className="space-y-3">
              {escritos.map((escrito) => (
                <div
                  key={escrito.id}
                  className="p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800/50"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <FileText className="h-4 w-4 text-gray-500" />
                        <span className="font-medium">{escrito.titulo}</span>
                        <Badge className={getEstadoColor(escrito.estado)}>
                          {getEstadoLabel(escrito.estado)}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-gray-500">
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {formatFecha(escrito.updated_at)}
                        </span>
                        {escrito.expediente_numero && (
                          <span>Exp: {escrito.expediente_numero}</span>
                        )}
                        {escrito.fecha_presentacion && (
                          <span>Presentado: {formatFecha(escrito.fecha_presentacion)}</span>
                        )}
                      </div>
                      <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                        {escrito.contenido.substring(0, 200)}...
                      </p>
                    </div>
                    <div className="flex items-center gap-1 ml-4">
                      {escrito.estado === 'borrador' && (
                        <>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleEditar(escrito)}
                            title="Editar"
                          >
                            <Edit2 className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handlePresentar(escrito.id)}
                            title="Marcar como presentado"
                          >
                            <Send className="h-4 w-4 text-blue-600" />
                          </Button>
                        </>
                      )}
                      {escrito.estado === 'presentado' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleConfirmar(escrito.id)}
                          title="Confirmar presentacion"
                        >
                          <CheckCircle className="h-4 w-4 text-green-600" />
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEliminar(escrito.id)}
                        title="Eliminar"
                      >
                        <Trash2 className="h-4 w-4 text-red-600" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
