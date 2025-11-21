import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import {
  Calendar,
  Clock,
  Plus,
  Check,
  Trash2,
  AlertTriangle,
  Loader2,
  CalendarDays,
  ListTodo,
  Bell
} from 'lucide-react'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'
import { toast } from 'sonner'
import {
  listarEventos,
  crearEvento,
  completarEvento,
  eliminarEvento,
  obtenerResumen
} from '@/api/agendaApi'
import type { Evento, ResumenAgenda, TipoEvento, Prioridad } from '@/types/agenda'

export default function AgendaPage() {
  const [eventos, setEventos] = useState<Evento[]>([])
  const [resumen, setResumen] = useState<ResumenAgenda | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)

  // Form state
  const [nuevoTitulo, setNuevoTitulo] = useState('')
  const [nuevaFecha, setNuevaFecha] = useState('')
  const [nuevoTipo, setNuevoTipo] = useState<TipoEvento>('tarea')
  const [nuevaPrioridad, setNuevaPrioridad] = useState<Prioridad>('media')
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    cargarDatos()
  }, [])

  const cargarDatos = async () => {
    setIsLoading(true)
    try {
      const [eventosData, resumenData] = await Promise.all([
        listarEventos({ estado: 'pendiente' }),
        obtenerResumen()
      ])
      setEventos(eventosData)
      setResumen(resumenData)
    } catch (error) {
      toast.error('Error al cargar agenda')
    } finally {
      setIsLoading(false)
    }
  }

  const handleCrearEvento = async () => {
    if (!nuevoTitulo.trim() || !nuevaFecha) {
      toast.error('Completa titulo y fecha')
      return
    }

    setIsSaving(true)
    try {
      await crearEvento({
        titulo: nuevoTitulo.trim(),
        fecha_inicio: new Date(nuevaFecha).toISOString(),
        tipo: nuevoTipo,
        prioridad: nuevaPrioridad
      })
      toast.success('Evento creado')
      setNuevoTitulo('')
      setNuevaFecha('')
      setShowForm(false)
      await cargarDatos()
    } catch (error) {
      toast.error('Error al crear evento')
    } finally {
      setIsSaving(false)
    }
  }

  const handleCompletar = async (eventoId: number) => {
    try {
      await completarEvento(eventoId)
      toast.success('Evento completado')
      await cargarDatos()
    } catch (error) {
      toast.error('Error al completar evento')
    }
  }

  const handleEliminar = async (eventoId: number) => {
    try {
      await eliminarEvento(eventoId)
      toast.success('Evento eliminado')
      await cargarDatos()
    } catch (error) {
      toast.error('Error al eliminar evento')
    }
  }

  const formatFecha = (fecha: string) => {
    try {
      return format(new Date(fecha), "dd MMM yyyy 'a las' HH:mm", { locale: es })
    } catch {
      return fecha
    }
  }

  const getPrioridadColor = (prioridad: Prioridad) => {
    switch (prioridad) {
      case 'urgente': return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
      case 'alta': return 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400'
      case 'media': return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400'
      case 'baja': return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400'
    }
  }

  const getTipoIcon = (tipo: TipoEvento) => {
    switch (tipo) {
      case 'vencimiento': return <AlertTriangle className="h-4 w-4" />
      case 'audiencia': return <Calendar className="h-4 w-4" />
      case 'tarea': return <ListTodo className="h-4 w-4" />
      case 'recordatorio': return <Bell className="h-4 w-4" />
      default: return <CalendarDays className="h-4 w-4" />
    }
  }

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
        <p className="mt-4 text-gray-600">Cargando agenda...</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Agenda</h1>
          <p className="text-gray-600 dark:text-gray-400">Gestiona tus eventos y tareas</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>
          <Plus className="h-4 w-4 mr-2" />
          Nuevo Evento
        </Button>
      </div>

      {/* Stats */}
      {resumen && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">Pendientes</p>
                  <p className="text-2xl font-bold">{resumen.total_pendientes}</p>
                </div>
                <ListTodo className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">Hoy</p>
                  <p className="text-2xl font-bold">{resumen.total_hoy}</p>
                </div>
                <Calendar className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">Esta Semana</p>
                  <p className="text-2xl font-bold">{resumen.total_semana}</p>
                </div>
                <CalendarDays className="h-8 w-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">Vencidos</p>
                  <p className="text-2xl font-bold text-red-600">{resumen.total_vencidos}</p>
                </div>
                <AlertTriangle className="h-8 w-8 text-red-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Form */}
      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Nuevo Evento</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="text-sm font-medium">Titulo</label>
                <Input
                  value={nuevoTitulo}
                  onChange={(e) => setNuevoTitulo(e.target.value)}
                  placeholder="Descripcion del evento"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Fecha y Hora</label>
                <Input
                  type="datetime-local"
                  value={nuevaFecha}
                  onChange={(e) => setNuevaFecha(e.target.value)}
                />
              </div>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="text-sm font-medium">Tipo</label>
                <select
                  className="w-full h-10 px-3 rounded-md border border-input bg-background"
                  value={nuevoTipo}
                  onChange={(e) => setNuevoTipo(e.target.value as TipoEvento)}
                >
                  <option value="tarea">Tarea</option>
                  <option value="vencimiento">Vencimiento</option>
                  <option value="audiencia">Audiencia</option>
                  <option value="recordatorio">Recordatorio</option>
                  <option value="otro">Otro</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium">Prioridad</label>
                <select
                  className="w-full h-10 px-3 rounded-md border border-input bg-background"
                  value={nuevaPrioridad}
                  onChange={(e) => setNuevaPrioridad(e.target.value as Prioridad)}
                >
                  <option value="baja">Baja</option>
                  <option value="media">Media</option>
                  <option value="alta">Alta</option>
                  <option value="urgente">Urgente</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowForm(false)}>
                Cancelar
              </Button>
              <Button onClick={handleCrearEvento} disabled={isSaving}>
                {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Crear'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Lista de Eventos */}
      <Card>
        <CardHeader>
          <CardTitle>Eventos Pendientes</CardTitle>
        </CardHeader>
        <CardContent>
          {eventos.length === 0 ? (
            <div className="py-8 text-center">
              <Calendar className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">No hay eventos pendientes</p>
            </div>
          ) : (
            <div className="space-y-3">
              {eventos.map((evento) => (
                <div
                  key={evento.id}
                  className={`p-4 rounded-lg border ${
                    evento.urgencia === 'vencido'
                      ? 'border-red-200 bg-red-50 dark:bg-red-900/10'
                      : evento.urgencia === 'proximo'
                      ? 'border-yellow-200 bg-yellow-50 dark:bg-yellow-900/10'
                      : 'border-gray-200 dark:border-gray-700'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        {getTipoIcon(evento.tipo)}
                        <span className="font-medium">{evento.titulo}</span>
                        <Badge className={getPrioridadColor(evento.prioridad)}>
                          {evento.prioridad}
                        </Badge>
                        {evento.urgencia === 'vencido' && (
                          <Badge variant="destructive">Vencido</Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-4 text-sm text-gray-500">
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {formatFecha(evento.fecha_inicio)}
                        </span>
                        {evento.expediente_numero && (
                          <span>Exp: {evento.expediente_numero}</span>
                        )}
                        {evento.dias_restantes !== null && evento.dias_restantes > 0 && (
                          <span>En {evento.dias_restantes} dias</span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleCompletar(evento.id)}
                        title="Completar"
                      >
                        <Check className="h-4 w-4 text-green-600" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEliminar(evento.id)}
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
