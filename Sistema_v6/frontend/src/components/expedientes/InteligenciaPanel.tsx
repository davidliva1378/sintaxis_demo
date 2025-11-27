/**
 * Panel de Inteligencia consolidado para un expediente.
 * Reemplaza los tabs "Analisis IA" y "Entidades" con una vista unificada.
 *
 * Secciones:
 * - Resumen ejecutivo (LLM)
 * - Partes procesales (Actor, Demandado, Abogados, Juez)
 * - Entidades normalizadas (fechas, montos, nombres, normas)
 * - Detalle por actuacion
 */

import { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import {
  obtenerInteligenciaExpediente,
  InteligenciaExpedienteResponse,
  EntidadNormalizadaDTO,
  ParteProcesalDTO,
  AnalisisActuacionDTO
} from '@/api/expedientesApi'
import { generarResumenExpediente } from '@/api/ragApi'
import { toast } from 'sonner'
import {
  Brain,
  Users,
  Tag,
  FileText,
  AlertCircle,
  ChevronDown,
  ChevronRight,
  Calendar,
  DollarSign,
  User,
  Scale,
  BookOpen,
  Building,
  CheckCircle2,
  XCircle,
  Sparkles,
  Loader2,
  RefreshCw,
  Network
} from 'lucide-react'
import { RelacionesGraph } from './RelacionesGraph'

interface InteligenciaPanelProps {
  numeroExpediente: string
}

// Colores por tipo de entidad
const COLORES_ENTIDAD: Record<string, string> = {
  'FECHA': 'bg-blue-100 text-blue-800 border-blue-200',
  'MONTO': 'bg-green-100 text-green-800 border-green-200',
  'PERSONA': 'bg-purple-100 text-purple-800 border-purple-200',
  'JUEZ': 'bg-indigo-100 text-indigo-800 border-indigo-200',
  'ABOGADO': 'bg-violet-100 text-violet-800 border-violet-200',
  'ACTOR': 'bg-orange-100 text-orange-800 border-orange-200',
  'DEMANDADO': 'bg-red-100 text-red-800 border-red-200',
  'NORMA': 'bg-amber-100 text-amber-800 border-amber-200',
  'LEY': 'bg-yellow-100 text-yellow-800 border-yellow-200',
  'ARTICULO': 'bg-lime-100 text-lime-800 border-lime-200',
  'TRIBUNAL': 'bg-cyan-100 text-cyan-800 border-cyan-200',
  'EXPEDIENTE': 'bg-teal-100 text-teal-800 border-teal-200',
  'OTROS': 'bg-gray-100 text-gray-800 border-gray-200',
  'default': 'bg-gray-100 text-gray-700 border-gray-200'
}

// Iconos por tipo de entidad
const ICONOS_ENTIDAD: Record<string, typeof Calendar> = {
  'FECHA': Calendar,
  'MONTO': DollarSign,
  'PERSONA': User,
  'JUEZ': Scale,
  'ABOGADO': User,
  'ACTOR': User,
  'DEMANDADO': User,
  'NORMA': BookOpen,
  'LEY': BookOpen,
  'ARTICULO': BookOpen,
  'TRIBUNAL': Building,
  'EXPEDIENTE': FileText,
}

function getColorEntidad(tipo: string): string {
  return COLORES_ENTIDAD[tipo.toUpperCase()] || COLORES_ENTIDAD['default']
}

function getIconoEntidad(tipo: string) {
  return ICONOS_ENTIDAD[tipo.toUpperCase()] || Tag
}

export function InteligenciaPanel({ numeroExpediente }: InteligenciaPanelProps) {
  const [data, setData] = useState<InteligenciaExpedienteResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedActuacion, setExpandedActuacion] = useState<number | null>(null)
  const [resumenGenerado, setResumenGenerado] = useState<string | null>(null)
  const [generandoResumen, setGenerandoResumen] = useState(false)

  useEffect(() => {
    const controller = new AbortController()
    let isMounted = true
    let timedOut = false

    const timeoutId = setTimeout(() => {
      timedOut = true
      controller.abort()
    }, 30000) // 30 segundos timeout

    const fetchData = async () => {
      try {
        setLoading(true)
        setError(null)
        const result = await obtenerInteligenciaExpediente(numeroExpediente, controller.signal)
        if (isMounted) {
          setData(result)
        }
      } catch (err) {
        // Solo mostrar error de timeout si realmente fue timeout (no cleanup por desmontaje)
        if (err instanceof Error && err.name === 'AbortError') {
          if (timedOut && isMounted) {
            setError('La carga tardó demasiado. El servidor puede estar procesando datos. Intente nuevamente.')
          }
          // Si no fue timeout, fue abort por cleanup - no hacer nada
        } else if (isMounted) {
          setError(err instanceof Error ? err.message : 'Error desconocido')
        }
      } finally {
        clearTimeout(timeoutId)
        if (isMounted) {
          setLoading(false)
        }
      }
    }

    fetchData()

    return () => {
      isMounted = false
      clearTimeout(timeoutId)
      controller.abort()
    }
  }, [numeroExpediente])

  if (loading) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary mb-4"></div>
          <p className="text-muted-foreground font-medium">
            Cargando datos de inteligencia...
          </p>
          <p className="text-xs text-muted-foreground mt-2">
            Esto puede tomar unos segundos
          </p>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle className="text-destructive flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            Error al cargar inteligencia
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">{error}</p>
        </CardContent>
      </Card>
    )
  }

  if (!data) {
    return null
  }

  const toggleActuacion = (id: number) => {
    setExpandedActuacion(expandedActuacion === id ? null : id)
  }

  const porcentajeIA = data.total_actuaciones > 0
    ? Math.round((data.actuaciones_con_ia / data.total_actuaciones) * 100)
    : 0

  const porcentajeIndexado = data.total_actuaciones > 0
    ? Math.round((data.actuaciones_indexadas / data.total_actuaciones) * 100)
    : 0

  const handleGenerarResumen = async () => {
    setGenerandoResumen(true)
    try {
      const resumen = await generarResumenExpediente(numeroExpediente)
      setResumenGenerado(resumen)
      toast.success('Resumen generado exitosamente')
    } catch (error) {
      console.error('Error generando resumen:', error)
      toast.error('Error al generar el resumen. Verifica que Ollama esté corriendo.')
    } finally {
      setGenerandoResumen(false)
    }
  }

  // Resumen a mostrar: generado dinámicamente o el existente del backend
  const resumenMostrar = resumenGenerado || data.resumen_ejecutivo

  return (
    <div className="space-y-6">
      {/* Resumen Ejecutivo con botón para generar/regenerar */}
      <Card className="border-l-4 border-l-purple-500">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-purple-500" />
              Resumen Ejecutivo
            </CardTitle>
            <Button
              variant="outline"
              size="sm"
              onClick={handleGenerarResumen}
              disabled={generandoResumen}
              className="flex items-center gap-2"
            >
              {generandoResumen ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Generando...
                </>
              ) : resumenMostrar ? (
                <>
                  <RefreshCw className="h-4 w-4" />
                  Regenerar
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  Generar Resumen
                </>
              )}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {resumenMostrar ? (
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{resumenMostrar}</p>
          ) : (
            <div className="text-center py-4 text-muted-foreground">
              <Brain className="h-8 w-8 mx-auto mb-2 opacity-30" />
              <p className="text-sm">No hay resumen disponible</p>
              <p className="text-xs mt-1">Haz clic en "Generar Resumen" para crear uno con IA</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Estadisticas rapidas */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Actuaciones</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.total_actuaciones}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Entidades</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.total_entidades}</div>
            <p className="text-xs text-muted-foreground">
              {Object.keys(data.entidades_normalizadas).length} tipos
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Brain className="h-4 w-4 text-purple-500" />
              Clasificadas IA
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-1">
              <div className="text-2xl font-bold">{data.actuaciones_con_ia}</div>
              <Progress value={porcentajeIA} className="h-1.5" />
              <p className="text-xs text-muted-foreground">{porcentajeIA}%</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <FileText className="h-4 w-4 text-blue-500" />
              Indexadas RAG
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-1">
              <div className="text-2xl font-bold">{data.actuaciones_indexadas}</div>
              <Progress value={porcentajeIndexado} className="h-1.5" />
              <p className="text-xs text-muted-foreground">{porcentajeIndexado}%</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs para las secciones principales */}
      <Tabs defaultValue="partes" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="partes" className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            Partes
          </TabsTrigger>
          <TabsTrigger value="entidades" className="flex items-center gap-2">
            <Tag className="h-4 w-4" />
            Entidades
          </TabsTrigger>
          <TabsTrigger value="grafo" className="flex items-center gap-2">
            <Network className="h-4 w-4" />
            Grafo
          </TabsTrigger>
          <TabsTrigger value="actuaciones" className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Por Actuacion
          </TabsTrigger>
        </TabsList>

        {/* Tab: Partes Procesales */}
        <TabsContent value="partes" className="mt-4">
          <PartesProcealesSection partes={data.partes_procesales} />
        </TabsContent>

        {/* Tab: Entidades Normalizadas */}
        <TabsContent value="entidades" className="mt-4">
          <EntidadesNormalizadasSection entidades={data.entidades_normalizadas} />
        </TabsContent>

        {/* Tab: Grafo de Relaciones */}
        <TabsContent value="grafo" className="mt-4">
          <RelacionesGraph
            entidades={data.entidades_normalizadas}
            partes={data.partes_procesales}
            expedienteNumero={numeroExpediente}
            height={550}
          />
        </TabsContent>

        {/* Tab: Detalle por Actuacion */}
        <TabsContent value="actuaciones" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Analisis por Actuacion</CardTitle>
              <CardDescription>
                Clasificacion IA y entidades extraidas de cada actuacion
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {data.analisis_actuaciones.map((act) => (
                  <ActuacionItem
                    key={act.id}
                    actuacion={act}
                    isExpanded={expandedActuacion === act.id}
                    onToggle={() => toggleActuacion(act.id)}
                  />
                ))}
                {data.analisis_actuaciones.length === 0 && (
                  <div className="text-center py-8 text-muted-foreground">
                    <FileText className="h-12 w-12 mx-auto mb-3 opacity-20" />
                    <p>No hay actuaciones para mostrar</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

// ============================================================================
// Componentes auxiliares
// ============================================================================

interface PartesProcesalesSectionProps {
  partes: Record<string, ParteProcesalDTO[]>
}

function PartesProcealesSection({ partes }: PartesProcesalesSectionProps) {
  const rolesOrden = ['ACTOR', 'DEMANDADO', 'ABOGADO', 'JUEZ', 'PERITO']
  const rolesLabels: Record<string, string> = {
    'ACTOR': 'Actores',
    'DEMANDADO': 'Demandados',
    'ABOGADO': 'Abogados',
    'JUEZ': 'Jueces',
    'PERITO': 'Peritos'
  }
  const rolesIcons: Record<string, typeof User> = {
    'ACTOR': User,
    'DEMANDADO': User,
    'ABOGADO': Scale,
    'JUEZ': Scale,
    'PERITO': User
  }

  const tienePartes = Object.values(partes).some(arr => arr.length > 0)

  if (!tienePartes) {
    return (
      <Card>
        <CardContent className="py-8 text-center">
          <Users className="h-12 w-12 mx-auto mb-3 opacity-20" />
          <p className="text-muted-foreground">No se identificaron partes procesales</p>
          <p className="text-sm text-muted-foreground mt-1">
            Procesa el expediente para extraer las partes automaticamente
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {rolesOrden.map(rol => {
        const partesRol = partes[rol] || []
        if (partesRol.length === 0) return null

        const Icon = rolesIcons[rol] || User
        const colorClass = getColorEntidad(rol)

        return (
          <Card key={rol}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Icon className="h-4 w-4" />
                {rolesLabels[rol] || rol} ({partesRol.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {partesRol.map((parte, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <Badge variant="outline" className={colorClass}>
                      {parte.nombre}
                    </Badge>
                    {parte.abogado && (
                      <span className="text-xs text-muted-foreground">
                        (Rep: {parte.abogado})
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}

interface EntidadesNormalizadasSectionProps {
  entidades: Record<string, EntidadNormalizadaDTO[]>
}

function EntidadesNormalizadasSection({ entidades }: EntidadesNormalizadasSectionProps) {
  const tiposOrden = ['FECHA', 'MONTO', 'NORMA', 'TRIBUNAL', 'PERSONA', 'OTROS']
  const tiposLabels: Record<string, string> = {
    'FECHA': 'Fechas',
    'MONTO': 'Montos',
    'NORMA': 'Normas Legales',
    'TRIBUNAL': 'Tribunales',
    'PERSONA': 'Personas',
    'OTROS': 'Otras Entidades'
  }

  const tieneEntidades = Object.values(entidades).some(arr => arr.length > 0)

  if (!tieneEntidades) {
    return (
      <Card>
        <CardContent className="py-8 text-center">
          <Tag className="h-12 w-12 mx-auto mb-3 opacity-20" />
          <p className="text-muted-foreground">No se extrajeron entidades</p>
          <p className="text-sm text-muted-foreground mt-1">
            Las entidades se extraen automaticamente del texto de las actuaciones
          </p>
        </CardContent>
      </Card>
    )
  }

  // Ordenar tipos segun orden preferido + otros
  const tiposPresentes = Object.keys(entidades).sort((a, b) => {
    const idxA = tiposOrden.indexOf(a)
    const idxB = tiposOrden.indexOf(b)
    if (idxA === -1 && idxB === -1) return a.localeCompare(b)
    if (idxA === -1) return 1
    if (idxB === -1) return -1
    return idxA - idxB
  })

  return (
    <div className="space-y-4">
      {tiposPresentes.map(tipo => {
        const items = entidades[tipo]
        if (!items || items.length === 0) return null

        const Icon = getIconoEntidad(tipo)
        const colorClass = getColorEntidad(tipo)

        return (
          <Card key={tipo}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Icon className="h-4 w-4" />
                {tiposLabels[tipo] || tipo} ({items.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {items.map((entidad, idx) => (
                  <div
                    key={idx}
                    className={`group relative px-3 py-1.5 rounded-md border text-sm ${colorClass}`}
                    title={`Original: ${entidad.original}\nConfianza: ${(entidad.score * 100).toFixed(0)}%`}
                  >
                    <span className="font-medium">{entidad.normalized}</span>
                    {entidad.score < 0.8 && (
                      <span className="ml-1 text-xs opacity-60">
                        ({(entidad.score * 100).toFixed(0)}%)
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}

interface ActuacionItemProps {
  actuacion: AnalisisActuacionDTO
  isExpanded: boolean
  onToggle: () => void
}

function ActuacionItem({ actuacion, isExpanded, onToggle }: ActuacionItemProps) {
  const getConfianzaColor = (confianza: number | undefined) => {
    if (!confianza) return 'bg-gray-100 text-gray-800'
    if (confianza >= 0.8) return 'bg-green-100 text-green-800'
    if (confianza >= 0.6) return 'bg-yellow-100 text-yellow-800'
    return 'bg-red-100 text-red-800'
  }

  return (
    <Collapsible open={isExpanded} onOpenChange={onToggle}>
      <div className="border rounded-lg">
        <CollapsibleTrigger asChild>
          <button className="w-full p-3 flex items-center justify-between hover:bg-muted/50 transition-colors">
            <div className="flex items-center gap-3">
              {isExpanded ? (
                <ChevronDown className="h-4 w-4 text-muted-foreground" />
              ) : (
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              )}
              <span className="font-medium text-sm">#{actuacion.id}</span>
              <span className="text-sm text-muted-foreground truncate max-w-[300px]">
                {actuacion.tipo}
              </span>
            </div>
            <div className="flex items-center gap-2">
              {/* Cantidad de entidades */}
              {actuacion.entidades.length > 0 && (
                <Badge variant="outline" className="text-xs">
                  <Tag className="h-3 w-3 mr-1" />
                  {actuacion.entidades.length}
                </Badge>
              )}

              {/* Badge de clasificacion IA */}
              {actuacion.tipo_ia ? (
                <Badge variant="secondary" className={getConfianzaColor(actuacion.confianza_ia)}>
                  {actuacion.tipo_ia}
                </Badge>
              ) : (
                <Badge variant="outline" className="text-muted-foreground">
                  Sin clasificar
                </Badge>
              )}

              {/* Indicador de indexacion RAG */}
              {actuacion.indexado_rag ? (
                <CheckCircle2 className="h-4 w-4 text-green-500" />
              ) : (
                <XCircle className="h-4 w-4 text-gray-300" />
              )}
            </div>
          </button>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <div className="px-4 pb-4 pt-2 border-t bg-muted/30">
            <div className="grid gap-3 text-sm">
              {/* Info basica */}
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-muted-foreground text-xs mb-1">Tipo original</p>
                  <p className="font-medium">{actuacion.tipo}</p>
                </div>
                <div>
                  <p className="text-muted-foreground text-xs mb-1">Fecha</p>
                  <p className="font-medium">{actuacion.fecha || '-'}</p>
                </div>
                <div>
                  <p className="text-muted-foreground text-xs mb-1">Clasificacion IA</p>
                  <p className="font-medium">{actuacion.tipo_ia || '-'}</p>
                  {actuacion.confianza_ia && (
                    <span className="text-xs text-muted-foreground">
                      ({(actuacion.confianza_ia * 100).toFixed(0)}% confianza)
                    </span>
                  )}
                </div>
              </div>

              {/* Entidades de esta actuacion */}
              {actuacion.entidades.length > 0 && (
                <div className="border-t pt-3 mt-2">
                  <p className="text-muted-foreground text-xs mb-2 font-medium">
                    Entidades extraidas ({actuacion.entidades.length})
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {actuacion.entidades.map((ent, idx) => (
                      <Badge
                        key={idx}
                        variant="outline"
                        className={`text-xs ${getColorEntidad(ent.label)}`}
                        title={`${ent.label}: ${ent.original} -> ${ent.normalized}`}
                      >
                        {ent.label}: {ent.normalized}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </CollapsibleContent>
      </div>
    </Collapsible>
  )
}

export default InteligenciaPanel
