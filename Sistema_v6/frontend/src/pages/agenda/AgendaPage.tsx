import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
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
  Bell,
  RefreshCw,
  FileWarning
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
import { useVencimientosStore } from '@/stores/vencimientosStore'
import type { Vencimiento } from '@/stores/vencimientosStore'

export default function AgendaPage() {
  const [eventos, setEventos] = useState<Evento[]>([])
  const [resumen, setResumen] = useState<ResumenAgenda | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [activeTab, setActiveTab] = useState('eventos')

  // Store de vencimientos
  const {
    vencimientos,
    estadisticas,
    isLoading: isLoadingVencimientos,
    listarVencimientos,
    obtenerEstadisticas,
    atenderVencimiento,
    cancelarVencimiento
  } = useVencimientosStore()

  // Form state
  const [nuevoTitulo, setNuevoTitulo] = useState('')
  const [nuevaFecha, setNuevaFecha] = useState('')
  const [nuevoTipo, setNuevoTipo] = useState<TipoEvento>('tarea')
  const [nuevaPrioridad, setNuevaPrioridad] = useState<Prioridad>('media')
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    cargarDatos()
    // Cargar vencimientos pendientes
    listarVencimientos({ estado: 'pendiente' })
    obtenerEstadisticas()
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

      {/* Stats combinados */}
      <div className="grid gap-4 md:grid-cols-5">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Eventos</p>
                <p className="text-2xl font-bold">{resumen?.total_pendientes || 0}</p>
              </div>
              <ListTodo className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Vencimientos</p>
                <p className="text-2xl font-bold">{estadisticas?.pendientes || 0}</p>
              </div>
              <FileWarning className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Urgentes (3d)</p>
                <p className="text-2xl font-bold text-orange-600">{estadisticas?.urgentes_3_dias || 0}</p>
              </div>
              <Clock className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Proximos (7d)</p>
                <p className="text-2xl font-bold">{estadisticas?.proximos_7_dias || 0}</p>
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
                <p className="text-2xl font-bold text-red-600">{estadisticas?.vencidos || 0}</p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
      </div>

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

      {/* Tabs: Eventos y Vencimientos */}
      <Tabs defaultValue="eventos" className="space-y-4">
        <TabsList>
          <TabsTrigger value="eventos" className="flex items-center gap-2">
            <ListTodo className="h-4 w-4" />
            Eventos ({eventos.length})
          </TabsTrigger>
          <TabsTrigger value="vencimientos" className="flex items-center gap-2">
            <FileWarning className="h-4 w-4" />
            Vencimientos ({vencimientos.length})
          </TabsTrigger>
        </TabsList>

        {/* Tab: Eventos */}
        <TabsContent value="eventos">
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
        </TabsContent>

        {/* Tab: Vencimientos */}
        <TabsContent value="vencimientos">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Vencimientos Procesales</CardTitle>
                <CardDescription>
                  Plazos detectados automaticamente en actuaciones
                </CardDescription>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  listarVencimientos({ estado: 'pendiente' })
                  obtenerEstadisticas()
                }}
                disabled={isLoadingVencimientos}
              >
                {isLoadingVencimientos ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
              </Button>
            </CardHeader>
            <CardContent>
              {isLoadingVencimientos ? (
                <div className="py-8 text-center">
                  <Loader2 className="h-8 w-8 animate-spin mx-auto text-blue-500" />
                  <p className="text-gray-500 mt-2">Cargando vencimientos...</p>
                </div>
              ) : vencimientos.length === 0 ? (
                <div className="py-8 text-center">
                  <FileWarning className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500">No hay vencimientos pendientes</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {vencimientos.map((venc) => (
                    <VencimientoCard
                      key={venc.id}
                      vencimiento={venc}
                      onAtender={() => atenderVencimiento(venc.id)}
                      onCancelar={() => cancelarVencimiento(venc.id)}
                    />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

// Componente para mostrar vencimiento en agenda
function VencimientoCard({
  vencimiento,
  onAtender,
  onCancelar
}: {
  vencimiento: Vencimiento
  onAtender: () => void
  onCancelar: () => void
}) {
  const [procesando, setProcesando] = useState(false)

  const getUrgenciaBorder = (urgencia: string) => {
    switch (urgencia) {
      case 'vencido': return 'border-black bg-black/5'
      case 'critico': return 'border-red-200 bg-red-50 dark:bg-red-900/10'
      case 'urgente': return 'border-orange-200 bg-orange-50 dark:bg-orange-900/10'
      case 'proximo': return 'border-yellow-200 bg-yellow-50 dark:bg-yellow-900/10'
      default: return 'border-gray-200 dark:border-gray-700'
    }
  }

  const getUrgenciaBadge = (urgencia: string) => {
    switch (urgencia) {
      case 'vencido': return 'bg-black text-white'
      case 'critico': return 'bg-red-600 text-white'
      case 'urgente': return 'bg-orange-500 text-white'
      case 'proximo': return 'bg-yellow-400 text-gray-900'
      default: return 'bg-green-500 text-white'
    }
  }

  const handleAtender = async () => {
    setProcesando(true)
    try {
      await onAtender()
    } finally {
      setProcesando(false)
    }
  }

  const handleCancelar = async () => {
    setProcesando(true)
    try {
      await onCancelar()
    } finally {
      setProcesando(false)
    }
  }

  return (
    <div className={`p-4 rounded-lg border ${getUrgenciaBorder(vencimiento.nivel_urgencia)}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1 space-y-1">
          <div className="flex items-center gap-2">
            <FileWarning className="h-4 w-4" />
            <span className="font-medium">{vencimiento.expediente_numero}</span>
            <Badge className={getUrgenciaBadge(vencimiento.nivel_urgencia)}>
              {vencimiento.nivel_urgencia.toUpperCase()}
            </Badge>
            <Badge variant="outline">
              {vencimiento.tipo.replace('_', ' ')}
            </Badge>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-1">
            {vencimiento.descripcion}
          </p>
          <div className="flex items-center gap-4 text-sm text-gray-500">
            <span className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              Vence: {format(new Date(vencimiento.fecha_vencimiento), "dd/MM/yyyy", { locale: es })}
            </span>
            <span className="font-medium">
              {vencimiento.dias_restantes < 0
                ? `${Math.abs(vencimiento.dias_restantes)} dias vencido`
                : vencimiento.dias_restantes === 0
                ? 'Vence HOY'
                : `${vencimiento.dias_restantes} dias restantes`}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleAtender}
            disabled={procesando}
            title="Marcar como atendido"
          >
            {procesando ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Check className="h-4 w-4 text-green-600" />
            )}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleCancelar}
            disabled={procesando}
            title="Cancelar vencimiento"
          >
            <Trash2 className="h-4 w-4 text-red-600" />
          </Button>
        </div>
      </div>
    </div>
  )
}
