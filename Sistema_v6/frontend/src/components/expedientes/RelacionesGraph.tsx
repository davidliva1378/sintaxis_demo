/**
 * RelacionesGraph - Visualización de relaciones entre entidades usando force-directed graph
 *
 * Muestra las entidades extraídas del expediente como nodos conectados por tipo/relación.
 * Usa react-force-graph-2d para renderizado eficiente en canvas.
 */

import { useEffect, useRef, useState, useCallback, useMemo } from 'react'
import ForceGraph2D, { ForceGraphMethods, NodeObject, LinkObject } from 'react-force-graph-2d'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Slider } from '@/components/ui/slider'
import {
  ZoomIn,
  ZoomOut,
  Maximize2,
  RefreshCw,
  Filter,
  Network,
  Settings2,
  Info
} from 'lucide-react'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { EntidadNormalizadaDTO, ParteProcesalDTO } from '@/api/expedientesApi'

// === Tipos para el grafo ===

interface GraphNode extends NodeObject {
  id: string
  name: string
  type: string
  count: number
  color: string
  val: number // tamaño del nodo
}

interface GraphLink extends LinkObject {
  source: string
  target: string
  value: number
  label?: string
}

interface GraphData {
  nodes: GraphNode[]
  links: GraphLink[]
}

interface RelacionesGraphProps {
  entidades: Record<string, EntidadNormalizadaDTO[]>
  partes?: Record<string, ParteProcesalDTO[]>
  expedienteNumero: string
  height?: number
}

// === Colores por tipo de entidad ===
const COLORES_NODO: Record<string, string> = {
  'FECHA': '#3b82f6',     // blue-500
  'MONTO': '#22c55e',     // green-500
  'PERSONA': '#a855f7',   // purple-500
  'JUEZ': '#6366f1',      // indigo-500
  'ABOGADO': '#8b5cf6',   // violet-500
  'ACTOR': '#f97316',     // orange-500
  'DEMANDADO': '#ef4444', // red-500
  'NORMA': '#f59e0b',     // amber-500
  'LEY': '#eab308',       // yellow-500
  'ARTICULO': '#84cc16',  // lime-500
  'TRIBUNAL': '#06b6d4',  // cyan-500
  'EXPEDIENTE': '#14b8a6',// teal-500
  'ORGANISMO': '#0ea5e9', // sky-500
  'OTROS': '#6b7280',     // gray-500
  'default': '#9ca3af'    // gray-400
}

function getNodeColor(tipo: string): string {
  return COLORES_NODO[tipo.toUpperCase()] || COLORES_NODO['default']
}

// === Componente principal ===

export function RelacionesGraph({
  entidades,
  partes,
  expedienteNumero,
  height = 500
}: RelacionesGraphProps) {
  const graphRef = useRef<ForceGraphMethods | undefined>()
  const containerRef = useRef<HTMLDivElement>(null)
  const [dimensions, setDimensions] = useState({ width: 800, height })
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [filterTypes, setFilterTypes] = useState<string[]>([])
  const [linkDistance, setLinkDistance] = useState(100)
  const [chargeStrength, setChargeStrength] = useState(-150)
  const [showLabels, setShowLabels] = useState(true)

  // Obtener todos los tipos de entidad disponibles
  const availableTypes = useMemo(() => {
    const types = new Set<string>()
    Object.keys(entidades).forEach(t => types.add(t.toUpperCase()))
    if (partes) {
      Object.keys(partes).forEach(t => types.add(t.toUpperCase()))
    }
    return Array.from(types).sort()
  }, [entidades, partes])

  // Construir datos del grafo
  const graphData = useMemo((): GraphData => {
    const nodes: GraphNode[] = []
    const links: GraphLink[] = []
    const nodeMap = new Map<string, GraphNode>()

    // Nodo central: Expediente
    const expedienteNode: GraphNode = {
      id: 'expediente',
      name: expedienteNumero,
      type: 'EXPEDIENTE',
      count: 1,
      color: getNodeColor('EXPEDIENTE'),
      val: 20
    }
    nodes.push(expedienteNode)
    nodeMap.set('expediente', expedienteNode)

    // Agregar nodos de entidades
    Object.entries(entidades).forEach(([tipo, items]) => {
      const tipoUpper = tipo.toUpperCase()

      // Si hay filtros activos y este tipo no está incluido, saltar
      if (filterTypes.length > 0 && !filterTypes.includes(tipoUpper)) {
        return
      }

      // Agrupar por valor normalizado para evitar duplicados
      const grouped = new Map<string, { count: number; items: EntidadNormalizadaDTO[] }>()
      items.forEach(item => {
        const key = item.normalized.toLowerCase().trim()
        if (!grouped.has(key)) {
          grouped.set(key, { count: 0, items: [] })
        }
        const g = grouped.get(key)!
        g.count++
        g.items.push(item)
      })

      // Limitar a top 15 por tipo para no saturar el grafo
      const sortedEntries = Array.from(grouped.entries())
        .sort((a, b) => b[1].count - a[1].count)
        .slice(0, 15)

      sortedEntries.forEach(([key, data]) => {
        const nodeId = `${tipoUpper}_${key}`
        const displayName = data.items[0].normalized

        const node: GraphNode = {
          id: nodeId,
          name: displayName,
          type: tipoUpper,
          count: data.count,
          color: getNodeColor(tipoUpper),
          val: Math.min(5 + data.count * 2, 15) // tamaño proporcional a frecuencia
        }
        nodes.push(node)
        nodeMap.set(nodeId, node)

        // Conectar al expediente central
        links.push({
          source: 'expediente',
          target: nodeId,
          value: data.count,
          label: tipoUpper
        })
      })
    })

    // Agregar partes procesales como nodos especiales
    if (partes) {
      Object.entries(partes).forEach(([rol, items]) => {
        const rolUpper = rol.toUpperCase()

        if (filterTypes.length > 0 && !filterTypes.includes(rolUpper)) {
          return
        }

        items.forEach((parte, idx) => {
          const nodeId = `${rolUpper}_${idx}_${parte.nombre.toLowerCase().replace(/\s+/g, '_')}`

          const node: GraphNode = {
            id: nodeId,
            name: parte.nombre,
            type: rolUpper,
            count: 1,
            color: getNodeColor(rolUpper),
            val: 12 // tamaño fijo para partes
          }
          nodes.push(node)
          nodeMap.set(nodeId, node)

          // Conectar al expediente
          links.push({
            source: 'expediente',
            target: nodeId,
            value: 2,
            label: rolUpper
          })

          // Si tiene abogado, conectar
          if (parte.abogado) {
            const abogadoId = `ABOGADO_${parte.abogado.toLowerCase().replace(/\s+/g, '_')}`
            if (!nodeMap.has(abogadoId)) {
              const abogadoNode: GraphNode = {
                id: abogadoId,
                name: parte.abogado,
                type: 'ABOGADO',
                count: 1,
                color: getNodeColor('ABOGADO'),
                val: 10
              }
              nodes.push(abogadoNode)
              nodeMap.set(abogadoId, abogadoNode)
            }
            links.push({
              source: nodeId,
              target: abogadoId,
              value: 1,
              label: 'representa'
            })
          }
        })
      })
    }

    // Crear conexiones entre entidades relacionadas (mismo tipo o co-ocurrencia)
    // Por ahora solo conectamos normas con artículos si coinciden
    const normas = nodes.filter(n => n.type === 'NORMA' || n.type === 'LEY')
    const articulos = nodes.filter(n => n.type === 'ARTICULO')

    normas.forEach(norma => {
      articulos.forEach(art => {
        // Heurística: si el artículo menciona la misma ley
        if (art.name.toLowerCase().includes(norma.name.toLowerCase().substring(0, 10))) {
          links.push({
            source: norma.id,
            target: art.id,
            value: 1,
            label: 'regula'
          })
        }
      })
    })

    return { nodes, links }
  }, [entidades, partes, expedienteNumero, filterTypes])

  // Actualizar dimensiones al cambiar el contenedor
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const { width } = containerRef.current.getBoundingClientRect()
        setDimensions({ width, height })
      }
    }

    updateDimensions()
    window.addEventListener('resize', updateDimensions)
    return () => window.removeEventListener('resize', updateDimensions)
  }, [height])

  // Handlers de zoom
  const handleZoomIn = useCallback(() => {
    if (graphRef.current) {
      const currentZoom = graphRef.current.zoom()
      graphRef.current.zoom(currentZoom * 1.3, 400)
    }
  }, [])

  const handleZoomOut = useCallback(() => {
    if (graphRef.current) {
      const currentZoom = graphRef.current.zoom()
      graphRef.current.zoom(currentZoom / 1.3, 400)
    }
  }, [])

  const handleCenter = useCallback(() => {
    if (graphRef.current) {
      graphRef.current.centerAt(0, 0, 500)
      graphRef.current.zoom(1, 500)
    }
  }, [])

  const handleReset = useCallback(() => {
    if (graphRef.current) {
      graphRef.current.zoomToFit(400, 50)
    }
  }, [])

  // Toggle filtro de tipo
  const toggleTypeFilter = useCallback((type: string) => {
    setFilterTypes(prev => {
      if (prev.includes(type)) {
        return prev.filter(t => t !== type)
      } else {
        return [...prev, type]
      }
    })
  }, [])

  // Click en nodo
  const handleNodeClick = useCallback((node: GraphNode) => {
    setSelectedNode(node)
    if (graphRef.current) {
      graphRef.current.centerAt(node.x!, node.y!, 500)
      graphRef.current.zoom(2, 500)
    }
  }, [])

  // Custom render de nodos
  const paintNode = useCallback((node: GraphNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const label = node.name
    const fontSize = Math.max(12 / globalScale, 3)
    const nodeRadius = node.val

    // Dibujar círculo
    ctx.beginPath()
    ctx.arc(node.x!, node.y!, nodeRadius, 0, 2 * Math.PI)
    ctx.fillStyle = node.color
    ctx.fill()

    // Borde si está seleccionado
    if (selectedNode?.id === node.id) {
      ctx.strokeStyle = '#fff'
      ctx.lineWidth = 3 / globalScale
      ctx.stroke()
    }

    // Etiqueta
    if (showLabels && globalScale > 0.5) {
      ctx.font = `${fontSize}px Inter, sans-serif`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'

      // Fondo de la etiqueta
      const textWidth = ctx.measureText(label).width
      ctx.fillStyle = 'rgba(0, 0, 0, 0.7)'
      ctx.fillRect(
        node.x! - textWidth / 2 - 2,
        node.y! + nodeRadius + 2,
        textWidth + 4,
        fontSize + 4
      )

      // Texto
      ctx.fillStyle = '#fff'
      ctx.fillText(label, node.x!, node.y! + nodeRadius + fontSize / 2 + 4)
    }
  }, [selectedNode, showLabels])

  // Si no hay datos
  if (graphData.nodes.length <= 1) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Network className="h-5 w-5" />
            Grafo de Relaciones
          </CardTitle>
          <CardDescription>
            No hay suficientes entidades para visualizar
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <Network className="h-16 w-16 text-muted-foreground opacity-20 mb-4" />
          <p className="text-muted-foreground">Procesa el expediente para extraer entidades</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Network className="h-5 w-5 text-primary" />
              Grafo de Relaciones
            </CardTitle>
            <CardDescription>
              {graphData.nodes.length} entidades • {graphData.links.length} conexiones
            </CardDescription>
          </div>

          {/* Controles */}
          <div className="flex items-center gap-2">
            {/* Filtros de tipo */}
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="outline" size="sm" className="gap-2">
                  <Filter className="h-4 w-4" />
                  Filtrar
                  {filterTypes.length > 0 && (
                    <Badge variant="secondary" className="ml-1">
                      {filterTypes.length}
                    </Badge>
                  )}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-64" align="end">
                <div className="space-y-2">
                  <h4 className="font-medium text-sm">Tipos de entidad</h4>
                  <div className="flex flex-wrap gap-1">
                    {availableTypes.map(type => (
                      <Badge
                        key={type}
                        variant={filterTypes.includes(type) || filterTypes.length === 0 ? "default" : "outline"}
                        className="cursor-pointer"
                        style={{
                          backgroundColor: filterTypes.includes(type) || filterTypes.length === 0
                            ? getNodeColor(type)
                            : undefined,
                          borderColor: getNodeColor(type)
                        }}
                        onClick={() => toggleTypeFilter(type)}
                      >
                        {type}
                      </Badge>
                    ))}
                  </div>
                  {filterTypes.length > 0 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="w-full mt-2"
                      onClick={() => setFilterTypes([])}
                    >
                      Limpiar filtros
                    </Button>
                  )}
                </div>
              </PopoverContent>
            </Popover>

            {/* Configuración del grafo */}
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="outline" size="icon">
                  <Settings2 className="h-4 w-4" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-72" align="end">
                <div className="space-y-4">
                  <h4 className="font-medium text-sm">Configuración del grafo</h4>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Distancia enlaces</span>
                      <span className="text-xs text-muted-foreground">{linkDistance}</span>
                    </div>
                    <Slider
                      value={[linkDistance]}
                      onValueChange={([v]) => setLinkDistance(v)}
                      min={30}
                      max={200}
                      step={10}
                    />
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Repulsión</span>
                      <span className="text-xs text-muted-foreground">{Math.abs(chargeStrength)}</span>
                    </div>
                    <Slider
                      value={[Math.abs(chargeStrength)]}
                      onValueChange={([v]) => setChargeStrength(-v)}
                      min={50}
                      max={400}
                      step={25}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-sm">Mostrar etiquetas</span>
                    <Button
                      variant={showLabels ? "default" : "outline"}
                      size="sm"
                      onClick={() => setShowLabels(!showLabels)}
                    >
                      {showLabels ? 'Sí' : 'No'}
                    </Button>
                  </div>
                </div>
              </PopoverContent>
            </Popover>

            {/* Zoom controls */}
            <div className="flex items-center border rounded-md">
              <Button variant="ghost" size="icon" onClick={handleZoomIn}>
                <ZoomIn className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon" onClick={handleZoomOut}>
                <ZoomOut className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon" onClick={handleCenter}>
                <Maximize2 className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon" onClick={handleReset}>
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0 relative" ref={containerRef}>
        {/* Info del nodo seleccionado */}
        {selectedNode && (
          <div className="absolute top-4 left-4 z-10 bg-background/95 border rounded-lg p-3 shadow-lg max-w-xs">
            <div className="flex items-start gap-2">
              <Info className="h-4 w-4 mt-0.5 text-muted-foreground" />
              <div>
                <p className="font-medium">{selectedNode.name}</p>
                <p className="text-sm text-muted-foreground">
                  Tipo: {selectedNode.type}
                </p>
                {selectedNode.count > 1 && (
                  <p className="text-sm text-muted-foreground">
                    Apariciones: {selectedNode.count}
                  </p>
                )}
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6 -mt-1 -mr-1"
                onClick={() => setSelectedNode(null)}
              >
                ×
              </Button>
            </div>
          </div>
        )}

        {/* Leyenda */}
        <div className="absolute bottom-4 left-4 z-10 bg-background/90 border rounded-lg p-2">
          <div className="flex flex-wrap gap-2 max-w-xs">
            {availableTypes.slice(0, 6).map(type => (
              <div key={type} className="flex items-center gap-1">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: getNodeColor(type) }}
                />
                <span className="text-xs">{type}</span>
              </div>
            ))}
            {availableTypes.length > 6 && (
              <span className="text-xs text-muted-foreground">+{availableTypes.length - 6} más</span>
            )}
          </div>
        </div>

        {/* Grafo */}
        <ForceGraph2D
          ref={graphRef as React.MutableRefObject<ForceGraphMethods>}
          graphData={graphData}
          width={dimensions.width}
          height={dimensions.height}
          backgroundColor="#0a0a0a"
          nodeRelSize={1}
          nodeCanvasObject={paintNode}
          nodePointerAreaPaint={(node: GraphNode, color, ctx) => {
            ctx.fillStyle = color
            ctx.beginPath()
            ctx.arc(node.x!, node.y!, node.val + 2, 0, 2 * Math.PI)
            ctx.fill()
          }}
          linkColor={() => 'rgba(255,255,255,0.15)'}
          linkWidth={(link: GraphLink) => Math.sqrt(link.value || 1)}
          linkDirectionalParticles={2}
          linkDirectionalParticleSpeed={0.005}
          linkDirectionalParticleWidth={2}
          linkDirectionalParticleColor={() => 'rgba(255,255,255,0.5)'}
          onNodeClick={(node) => handleNodeClick(node as GraphNode)}
          d3VelocityDecay={0.4}
          d3AlphaDecay={0.02}
          cooldownTicks={100}
          onEngineStop={() => graphRef.current?.zoomToFit(400, 50)}
        />
      </CardContent>
    </Card>
  )
}

export default RelacionesGraph
