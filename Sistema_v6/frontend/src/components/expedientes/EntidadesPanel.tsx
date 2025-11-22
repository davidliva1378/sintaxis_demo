/**
 * Panel de Entidades NER para un expediente
 * Muestra entidades extraidas por IA y permite agregar manuales
 */

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  obtenerEntidades,
  obtenerEstadisticasEntidades,
  obtenerTiposEntidad,
  crearEntidad,
  eliminarEntidad,
  Entidad,
  EstadisticasEntidadesResponse
} from '@/api/entidadesApi'
import {
  obtenerTiposEntidadCompletos,
  crearTipoEntidad,
  eliminarTipoEntidad,
  TipoEntidad
} from '@/api/tiposEntidadApi'
import {
  Tag,
  Plus,
  Trash2,
  AlertCircle,
  Bot,
  User,
  X,
  Settings,
  Lock
} from 'lucide-react'
import { toast } from 'sonner'

interface EntidadesPanelProps {
  numeroExpediente: string
}

export function EntidadesPanel({ numeroExpediente }: EntidadesPanelProps) {
  const [entidades, setEntidades] = useState<Entidad[]>([])
  const [estadisticas, setEstadisticas] = useState<EstadisticasEntidadesResponse | null>(null)
  const [tipos, setTipos] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Formulario para nueva entidad
  const [showForm, setShowForm] = useState(false)
  const [nuevoTipo, setNuevoTipo] = useState('')
  const [nuevoValor, setNuevoValor] = useState('')
  const [nuevaNota, setNuevaNota] = useState('')
  const [creando, setCreando] = useState(false)

  // Filtros
  const [filtroTipo, setFiltroTipo] = useState<string>('all')
  const [filtroOrigen, setFiltroOrigen] = useState<string>('all')

  // Modal de gestión de tipos
  const [showTiposModal, setShowTiposModal] = useState(false)
  const [tiposCompletos, setTiposCompletos] = useState<TipoEntidad[]>([])
  const [loadingTipos, setLoadingTipos] = useState(false)
  const [nuevoTipoNombre, setNuevoTipoNombre] = useState('')
  const [nuevoTipoDescripcion, setNuevoTipoDescripcion] = useState('')
  const [creandoTipo, setCreandoTipo] = useState(false)

  useEffect(() => {
    cargarDatos()
  }, [numeroExpediente])

  const cargarTiposCompletos = async () => {
    try {
      setLoadingTipos(true)
      const response = await obtenerTiposEntidadCompletos(false, true)
      setTiposCompletos(response.tipos)
    } catch (err) {
      toast.error('Error cargando tipos de entidad')
    } finally {
      setLoadingTipos(false)
    }
  }

  const handleCrearTipo = async () => {
    if (!nuevoTipoNombre.trim()) {
      toast.error('El nombre es requerido')
      return
    }

    try {
      setCreandoTipo(true)
      await crearTipoEntidad({
        nombre: nuevoTipoNombre.trim().toUpperCase(),
        descripcion: nuevoTipoDescripcion.trim() || undefined
      })
      toast.success('Tipo de entidad creado')
      setNuevoTipoNombre('')
      setNuevoTipoDescripcion('')
      await cargarTiposCompletos()
      await cargarDatos()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Error al crear tipo')
    } finally {
      setCreandoTipo(false)
    }
  }

  const handleEliminarTipo = async (tipoId: number, nombre: string) => {
    try {
      await eliminarTipoEntidad(tipoId)
      toast.success(`Tipo '${nombre}' eliminado`)
      await cargarTiposCompletos()
      await cargarDatos()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Error al eliminar')
    }
  }

  const cargarDatos = async () => {
    try {
      setLoading(true)
      setError(null)

      const [entidadesRes, estadisticasRes, tiposRes] = await Promise.all([
        obtenerEntidades(numeroExpediente),
        obtenerEstadisticasEntidades(numeroExpediente),
        obtenerTiposEntidad(numeroExpediente)
      ])

      setEntidades(entidadesRes.entidades)
      setEstadisticas(estadisticasRes)
      setTipos(tiposRes.tipos)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido')
    } finally {
      setLoading(false)
    }
  }

  const handleCrearEntidad = async () => {
    if (!nuevoTipo || !nuevoValor.trim()) {
      toast.error('Tipo y valor son requeridos')
      return
    }

    try {
      setCreando(true)
      await crearEntidad(numeroExpediente, {
        entity_type: nuevoTipo,
        entity_value: nuevoValor.trim(),
        notas: nuevaNota.trim() || undefined
      })

      toast.success('Entidad creada')
      setNuevoTipo('')
      setNuevoValor('')
      setNuevaNota('')
      setShowForm(false)
      await cargarDatos()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Error al crear')
    } finally {
      setCreando(false)
    }
  }

  const handleEliminar = async (entidadId: number) => {
    try {
      await eliminarEntidad(numeroExpediente, entidadId)
      toast.success('Entidad eliminada')
      await cargarDatos()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Error al eliminar')
    }
  }

  const getColorForType = (tipo: string): string => {
    const colors: Record<string, string> = {
      PERSONA: 'bg-blue-100 text-blue-800',
      ORGANIZACION: 'bg-purple-100 text-purple-800',
      TRIBUNAL: 'bg-indigo-100 text-indigo-800',
      JUEZ: 'bg-cyan-100 text-cyan-800',
      ABOGADO: 'bg-teal-100 text-teal-800',
      FECHA: 'bg-orange-100 text-orange-800',
      MONTO: 'bg-green-100 text-green-800',
      NORMA: 'bg-red-100 text-red-800',
      PLAZO: 'bg-yellow-100 text-yellow-800',
      EXPEDIENTE: 'bg-gray-100 text-gray-800',
      DOMICILIO: 'bg-pink-100 text-pink-800',
      DECRETO: 'bg-amber-100 text-amber-800',
      CONCEPTO: 'bg-lime-100 text-lime-800',
    }
    return colors[tipo] || 'bg-gray-100 text-gray-800'
  }

  // Filtrar entidades
  const entidadesFiltradas = entidades.filter(e => {
    if (filtroTipo !== 'all' && e.entity_type !== filtroTipo) return false
    if (filtroOrigen !== 'all' && e.origen !== filtroOrigen) return false
    return true
  })

  // Agrupar por tipo
  const entidadesPorTipo = entidadesFiltradas.reduce((acc, e) => {
    if (!acc[e.entity_type]) acc[e.entity_type] = []
    acc[e.entity_type].push(e)
    return acc
  }, {} as Record<string, Entidad[]>)

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (error) {
    return (
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle className="text-destructive flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            Error al cargar entidades
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">{error}</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Estadisticas */}
      {estadisticas && (
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Total Entidades</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{estadisticas.total}</div>
              <p className="text-xs text-muted-foreground">
                {estadisticas.por_tipo.length} tipos diferentes
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Bot className="h-4 w-4 text-purple-500" />
                Extraidas por IA
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{estadisticas.total_ia}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <User className="h-4 w-4 text-blue-500" />
                Agregadas Manual
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{estadisticas.total_manual}</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filtros y acciones */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Tag className="h-5 w-5" />
                Entidades Extraidas
              </CardTitle>
              <CardDescription>
                Entidades NER del expediente (IA + manuales)
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Dialog open={showTiposModal} onOpenChange={(open) => {
                setShowTiposModal(open)
                if (open) cargarTiposCompletos()
              }}>
                <DialogTrigger asChild>
                  <Button variant="outline" size="sm">
                    <Settings className="h-4 w-4 mr-1" />
                    Tipos
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                  <DialogHeader>
                    <DialogTitle>Gestionar Tipos de Entidad</DialogTitle>
                    <DialogDescription>
                      Agrega tipos personalizados o revisa los existentes
                    </DialogDescription>
                  </DialogHeader>

                  {/* Formulario nuevo tipo */}
                  <div className="p-4 border rounded-lg bg-muted/30 mb-4">
                    <h4 className="font-medium mb-3">Nuevo Tipo Personalizado</h4>
                    <div className="grid gap-3">
                      <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-2">
                          <Label htmlFor="nuevo-tipo-nombre">Nombre</Label>
                          <Input
                            id="nuevo-tipo-nombre"
                            placeholder="Ej: CUIL, CUENTA_BANCARIA"
                            value={nuevoTipoNombre}
                            onChange={e => setNuevoTipoNombre(e.target.value.toUpperCase())}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="nuevo-tipo-desc">Descripcion</Label>
                          <Input
                            id="nuevo-tipo-desc"
                            placeholder="Descripcion del tipo"
                            value={nuevoTipoDescripcion}
                            onChange={e => setNuevoTipoDescripcion(e.target.value)}
                          />
                        </div>
                      </div>
                      <Button
                        onClick={handleCrearTipo}
                        disabled={creandoTipo || !nuevoTipoNombre.trim()}
                        className="w-fit"
                        size="sm"
                      >
                        <Plus className="h-4 w-4 mr-1" />
                        {creandoTipo ? 'Creando...' : 'Crear Tipo'}
                      </Button>
                    </div>
                  </div>

                  {/* Lista de tipos existentes */}
                  <div>
                    <h4 className="font-medium mb-3">Tipos Disponibles ({tiposCompletos.length})</h4>
                    {loadingTipos ? (
                      <div className="space-y-2">
                        <Skeleton className="h-8 w-full" />
                        <Skeleton className="h-8 w-full" />
                        <Skeleton className="h-8 w-full" />
                      </div>
                    ) : (
                      <div className="space-y-2 max-h-[300px] overflow-y-auto">
                        {tiposCompletos.map(tipo => (
                          <div
                            key={tipo.id}
                            className="flex items-center justify-between p-2 border rounded hover:bg-muted/50"
                          >
                            <div className="flex items-center gap-2">
                              {tipo.es_predefinido && (
                                <Lock className="h-3 w-3 text-muted-foreground" />
                              )}
                              <Badge className={getColorForType(tipo.nombre)}>
                                {tipo.nombre}
                              </Badge>
                              {tipo.descripcion && (
                                <span className="text-sm text-muted-foreground">
                                  {tipo.descripcion}
                                </span>
                              )}
                              {!tipo.activo && (
                                <Badge variant="outline" className="text-xs">
                                  Inactivo
                                </Badge>
                              )}
                            </div>
                            {!tipo.es_predefinido && (
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-6 w-6"
                                onClick={() => handleEliminarTipo(tipo.id, tipo.nombre)}
                              >
                                <Trash2 className="h-3 w-3 text-destructive" />
                              </Button>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </DialogContent>
              </Dialog>

              <Button onClick={() => setShowForm(!showForm)} size="sm">
                {showForm ? <X className="h-4 w-4 mr-1" /> : <Plus className="h-4 w-4 mr-1" />}
                {showForm ? 'Cancelar' : 'Nueva'}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Formulario nueva entidad */}
          {showForm && (
            <div className="mb-6 p-4 border rounded-lg bg-muted/30">
              <h4 className="font-medium mb-3">Nueva Entidad Manual</h4>
              <div className="grid gap-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="tipo-entidad">Tipo de entidad</Label>
                    <Select value={nuevoTipo} onValueChange={setNuevoTipo}>
                      <SelectTrigger id="tipo-entidad">
                        <SelectValue placeholder="Seleccionar tipo" />
                      </SelectTrigger>
                      <SelectContent>
                        {tipos.map(tipo => (
                          <SelectItem key={tipo} value={tipo}>{tipo}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-muted-foreground">
                      Ej: PERSONA, MONTO, NORMA, FECHA
                    </p>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="valor-entidad">Valor de la entidad</Label>
                    <Input
                      id="valor-entidad"
                      placeholder="Ingrese el valor"
                      value={nuevoValor}
                      onChange={e => setNuevoValor(e.target.value)}
                    />
                    <p className="text-xs text-muted-foreground">
                      Ej: Juan Perez, $50.000, Art. 72 Ley 24.522
                    </p>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="notas-entidad">Notas (opcional)</Label>
                  <Input
                    id="notas-entidad"
                    placeholder="Contexto adicional sobre la entidad"
                    value={nuevaNota}
                    onChange={e => setNuevaNota(e.target.value)}
                  />
                </div>
                <Button
                  onClick={handleCrearEntidad}
                  disabled={creando || !nuevoTipo || !nuevoValor.trim()}
                  className="w-fit"
                >
                  {creando ? 'Creando...' : 'Crear Entidad'}
                </Button>
              </div>
            </div>
          )}

          {/* Filtros */}
          <div className="flex gap-3 mb-4">
            <Select value={filtroTipo} onValueChange={setFiltroTipo}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filtrar por tipo" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos los tipos</SelectItem>
                {tipos.map(tipo => (
                  <SelectItem key={tipo} value={tipo}>{tipo}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={filtroOrigen} onValueChange={setFiltroOrigen}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Origen" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos</SelectItem>
                <SelectItem value="ia">Solo IA</SelectItem>
                <SelectItem value="manual">Solo Manual</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Lista de entidades */}
          {entidadesFiltradas.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Tag className="h-12 w-12 mx-auto mb-3 opacity-20" />
              <p>No hay entidades para mostrar</p>
              <p className="text-sm">Las entidades se extraen automaticamente con IA o puedes agregarlas manualmente</p>
            </div>
          ) : (
            <div className="space-y-4">
              {Object.entries(entidadesPorTipo).map(([tipo, items]) => (
                <div key={tipo}>
                  <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                    <Badge className={getColorForType(tipo)}>{tipo}</Badge>
                    <span className="text-muted-foreground">({items.length})</span>
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {items.map(entidad => (
                      <div
                        key={entidad.id}
                        className="group flex items-center gap-1 px-2 py-1 border rounded-md bg-background hover:bg-muted/50"
                      >
                        {entidad.origen === 'ia' ? (
                          <Bot className="h-3 w-3 text-purple-500" />
                        ) : (
                          <User className="h-3 w-3 text-blue-500" />
                        )}
                        <span className="text-sm">{entidad.entity_value}</span>
                        {entidad.score && (
                          <span className="text-xs text-muted-foreground">
                            ({(entidad.score * 100).toFixed(0)}%)
                          </span>
                        )}
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-5 w-5 opacity-0 group-hover:opacity-100 transition-opacity"
                          onClick={() => handleEliminar(entidad.id)}
                        >
                          <Trash2 className="h-3 w-3 text-destructive" />
                        </Button>
                      </div>
                    ))}
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

export default EntidadesPanel
