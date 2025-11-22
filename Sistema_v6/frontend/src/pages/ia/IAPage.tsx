import { useState } from 'react'
import { toast } from 'sonner'
import { Brain, Search, FileText, Sparkles, Activity, Cpu } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import * as iaApi from '@/api/iaApi'

export default function IAPage() {
  const [loading, setLoading] = useState(false)
  const [texto, setTexto] = useState('')

  // Resultados
  const [clasificacion, setClasificacion] = useState<iaApi.ClasificarResponse | null>(null)
  const [entidades, setEntidades] = useState<Record<string, string[]> | null>(null)
  const [respuestaRAG, setRespuestaRAG] = useState<iaApi.PreguntarResponse | null>(null)
  const [resultadosBusqueda, setResultadosBusqueda] = useState<iaApi.ResultadoBusqueda[]>([])
  const [textoGenerado, setTextoGenerado] = useState<string>('')
  const [status, setStatus] = useState<iaApi.IAStatus | null>(null)

  // Modelos
  const [modelos, setModelos] = useState<string[]>([])
  const [modeloActual, setModeloActual] = useState<string>('')

  // === Clasificacion ===
  const handleClasificar = async () => {
    if (!texto.trim()) {
      toast.error('Ingrese texto para clasificar')
      return
    }

    setLoading(true)
    try {
      const result = await iaApi.clasificarActuacion({
        texto,
        usar_llm: true
      })
      setClasificacion(result)
      toast.success('Clasificacion completada')
    } catch (error) {
      toast.error('Error al clasificar: ' + (error as Error).message)
    } finally {
      setLoading(false)
    }
  }

  // === NER ===
  const handleExtraerEntidades = async () => {
    if (!texto.trim()) {
      toast.error('Ingrese texto para extraer entidades')
      return
    }

    setLoading(true)
    try {
      const result = await iaApi.extraerEntidadesJuridicas(texto)
      setEntidades(result)
      toast.success('Entidades extraidas')
    } catch (error) {
      toast.error('Error al extraer entidades: ' + (error as Error).message)
    } finally {
      setLoading(false)
    }
  }

  // === RAG ===
  const handlePreguntar = async () => {
    if (!texto.trim()) {
      toast.error('Ingrese una pregunta')
      return
    }

    setLoading(true)
    try {
      const result = await iaApi.preguntar({
        pregunta: texto,
        n_contextos: 5
      })
      setRespuestaRAG(result)
      setResultadosBusqueda([])
      toast.success('Respuesta generada')
    } catch (error) {
      toast.error('Error al preguntar: ' + (error as Error).message)
    } finally {
      setLoading(false)
    }
  }

  // === Busqueda Hibrida ===
  const handleBuscarHibrido = async () => {
    if (!texto.trim()) {
      toast.error('Ingrese un texto para buscar')
      return
    }

    setLoading(true)
    try {
      const result = await iaApi.buscarHibrido({
        query: texto,
        n_results: 10
      })
      setResultadosBusqueda(result)
      setRespuestaRAG(null)
      toast.success(`Encontrados ${result.length} resultados`)
    } catch (error) {
      toast.error('Error en busqueda: ' + (error as Error).message)
    } finally {
      setLoading(false)
    }
  }

  // === LLM ===
  const handleGenerar = async () => {
    if (!texto.trim()) {
      toast.error('Ingrese un prompt')
      return
    }

    setLoading(true)
    try {
      const result = await iaApi.generarTexto({
        prompt: texto,
        temperature: 0.7,
        max_tokens: 1000
      })
      if (result && result.trim()) {
        setTextoGenerado(result)
        toast.success('Texto generado')
      } else {
        toast.warning('El modelo no genero texto. Intente con otro prompt.')
      }
    } catch (error) {
      toast.error('Error al generar: ' + (error as Error).message)
    } finally {
      setLoading(false)
    }
  }

  const handleResumirTexto = async () => {
    if (!texto.trim()) {
      toast.error('Ingrese texto para resumir')
      return
    }

    setLoading(true)
    try {
      const result = await iaApi.resumirTexto(texto, 300)
      if (result && result.trim()) {
        setTextoGenerado(result)
        toast.success('Resumen generado')
      } else {
        toast.warning('El modelo no genero resumen. Intente con otro texto.')
      }
    } catch (error) {
      toast.error('Error al resumir: ' + (error as Error).message)
    } finally {
      setLoading(false)
    }
  }

  // === Status ===
  const handleCheckStatus = async () => {
    setLoading(true)
    try {
      const result = await iaApi.getIAStatus()
      setStatus(result)

      // Cargar modelos disponibles
      const modelosData = await iaApi.getModelos()
      setModelos(modelosData.models)
      setModeloActual(modelosData.current)

      toast.success('Estado obtenido')
    } catch (error) {
      toast.error('Error al obtener estado: ' + (error as Error).message)
    } finally {
      setLoading(false)
    }
  }

  // === Cambiar modelo ===
  const handleChangeModel = async (model: string) => {
    setLoading(true)
    try {
      await iaApi.setModelo(model)
      setModeloActual(model)
      toast.success(`Modelo cambiado a ${model}`)
    } catch (error) {
      toast.error('Error al cambiar modelo: ' + (error as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Inteligencia Artificial</h1>
          <p className="text-muted-foreground">
            Prueba los servicios de IA del sistema
          </p>
        </div>
        <Button onClick={handleCheckStatus} variant="outline">
          <Activity className="mr-2 h-4 w-4" />
          Ver Estado
        </Button>
      </div>

      {status && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Estado de Servicios</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-4 flex-wrap">
              <Badge variant={status.clasificador === 'ok' ? 'default' : 'destructive'}>
                Clasificador: {status.clasificador}
              </Badge>
              <Badge variant={status.ner === 'ok' ? 'default' : 'secondary'}>
                NER: {status.ner}
              </Badge>
              <Badge variant={status.rag === 'ok' ? 'default' : 'secondary'}>
                RAG: {status.rag}
              </Badge>
              <Badge variant={status.llm === 'ok' ? 'default' : 'destructive'}>
                LLM: {status.llm}
              </Badge>
            </div>

            {modelos.length > 0 && (
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Cpu className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium">Modelo LLM:</span>
                </div>
                <Select value={modeloActual} onValueChange={handleChangeModel}>
                  <SelectTrigger className="w-[200px]">
                    <SelectValue placeholder="Seleccionar modelo" />
                  </SelectTrigger>
                  <SelectContent>
                    {modelos.map((modelo) => (
                      <SelectItem key={modelo} value={modelo}>
                        {modelo}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="clasificar" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="clasificar">
            <Brain className="mr-2 h-4 w-4" />
            Clasificar
          </TabsTrigger>
          <TabsTrigger value="ner">
            <FileText className="mr-2 h-4 w-4" />
            Entidades
          </TabsTrigger>
          <TabsTrigger value="rag">
            <Search className="mr-2 h-4 w-4" />
            RAG
          </TabsTrigger>
          <TabsTrigger value="llm">
            <Sparkles className="mr-2 h-4 w-4" />
            Generar
          </TabsTrigger>
        </TabsList>

        {/* === Clasificacion === */}
        <TabsContent value="clasificar">
          <Card>
            <CardHeader>
              <CardTitle>Clasificar Actuacion</CardTitle>
              <CardDescription>
                Clasifica el tipo de actuacion judicial basandose en su contenido
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                placeholder="Ingrese el texto de la actuacion..."
                value={texto}
                onChange={(e) => setTexto(e.target.value)}
                rows={6}
              />
              <Button onClick={handleClasificar} disabled={loading}>
                {loading ? <LoadingSpinner /> : 'Clasificar'}
              </Button>

              {clasificacion && (
                <div className="mt-4 p-4 bg-muted rounded-lg space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">Tipo:</span>
                    <Badge>{clasificacion.tipo}</Badge>
                  </div>
                  <div>
                    <span className="font-medium">Confianza:</span>{' '}
                    {(clasificacion.confianza * 100).toFixed(1)}%
                  </div>
                  <div>
                    <span className="font-medium">Justificacion:</span>{' '}
                    {clasificacion.justificacion}
                  </div>
                  {clasificacion.metodo && (
                    <div>
                      <span className="font-medium">Metodo:</span>{' '}
                      {clasificacion.metodo}
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* === NER === */}
        <TabsContent value="ner">
          <Card>
            <CardHeader>
              <CardTitle>Extraccion de Entidades</CardTitle>
              <CardDescription>
                Extrae entidades juridicas del texto (personas, fechas, montos, etc.)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                placeholder="Ingrese el texto para extraer entidades..."
                value={texto}
                onChange={(e) => setTexto(e.target.value)}
                rows={6}
              />
              <Button onClick={handleExtraerEntidades} disabled={loading}>
                {loading ? <LoadingSpinner /> : 'Extraer Entidades'}
              </Button>

              {entidades && Object.keys(entidades).length > 0 && (
                <div className="mt-4 p-4 bg-muted rounded-lg space-y-3">
                  {Object.entries(entidades).map(([tipo, valores]) => (
                    <div key={tipo}>
                      <span className="font-medium text-sm">{tipo}:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {valores.map((valor, i) => (
                          <Badge key={i} variant="outline">{valor}</Badge>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* === RAG === */}
        <TabsContent value="rag">
          <Card>
            <CardHeader>
              <CardTitle>Busqueda Hibrida (BM25 + Semantica)</CardTitle>
              <CardDescription>
                Busca en las actuaciones indexadas usando BM25 + embeddings con RRF
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                placeholder="Escriba una consulta o pregunta..."
                value={texto}
                onChange={(e) => setTexto(e.target.value)}
                rows={4}
              />
              <div className="flex gap-2">
                <Button onClick={handleBuscarHibrido} disabled={loading}>
                  {loading ? <LoadingSpinner /> : 'Buscar'}
                </Button>
                <Button onClick={handlePreguntar} disabled={loading} variant="secondary">
                  {loading ? <LoadingSpinner /> : 'Preguntar (RAG)'}
                </Button>
              </div>

              {/* Resultados de busqueda hibrida */}
              {resultadosBusqueda.length > 0 && (
                <div className="mt-4 space-y-4">
                  <div className="font-medium">Resultados de busqueda ({resultadosBusqueda.length}):</div>
                  <div className="space-y-3 max-h-[500px] overflow-y-auto">
                    {resultadosBusqueda.map((resultado, i) => {
                      // Extraer info del ID (ej: "56_chunk_0" -> actuacion 56, chunk 0)
                      const idParts = resultado.id.split('_chunk_')
                      const actuacionId = idParts[0]
                      const chunkIndex = idParts[1] ? parseInt(idParts[1]) : 0
                      const totalChunks = resultado.metadata?.total_chunks as number || 1

                      return (
                        <div key={i} className="p-4 bg-muted rounded-lg text-sm border">
                          {/* Header: Expediente y fecha */}
                          <div className="flex justify-between items-start mb-2">
                            <div className="space-y-1">
                              {resultado.metadata?.expediente_numero && (
                                <div className="font-semibold text-primary">
                                  {String(resultado.metadata.expediente_numero)}
                                </div>
                              )}
                              <div className="text-xs text-muted-foreground">
                                Actuacion #{actuacionId}
                                {totalChunks > 1 && ` (Fragmento ${chunkIndex + 1}/${totalChunks})`}
                              </div>
                            </div>
                            <div className="text-right">
                              {resultado.metadata?.fecha && (
                                <div className="text-xs text-muted-foreground">
                                  {String(resultado.metadata.fecha)}
                                </div>
                              )}
                              <div className="font-mono text-xs">
                                Score: {((resultado.hybrid_score || resultado.score) * 100).toFixed(1)}%
                              </div>
                            </div>
                          </div>

                          {/* Tipo de actuacion */}
                          {resultado.metadata?.tipo && (
                            <Badge variant="outline" className="mb-2">
                              {String(resultado.metadata.tipo)}
                            </Badge>
                          )}

                          {/* Contenido */}
                          <p className="text-sm whitespace-pre-wrap line-clamp-4 mb-2">
                            {resultado.document}
                          </p>

                          {/* Detalle si existe */}
                          {resultado.metadata?.detalle && (
                            <div className="text-xs text-muted-foreground border-t pt-2 mt-2">
                              <span className="font-medium">Detalle:</span> {String(resultado.metadata.detalle).slice(0, 150)}
                              {String(resultado.metadata.detalle).length > 150 && '...'}
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* Respuesta RAG */}
              {respuestaRAG && (
                <div className="mt-4 space-y-4">
                  <div className="p-4 bg-muted rounded-lg">
                    <div className="font-medium mb-2">Respuesta:</div>
                    <p className="whitespace-pre-wrap">{respuestaRAG.respuesta}</p>
                    <div className="mt-2 text-sm text-muted-foreground">
                      Confianza: {(respuestaRAG.confianza * 100).toFixed(1)}%
                    </div>
                  </div>

                  {respuestaRAG.fuentes.length > 0 && (
                    <div>
                      <div className="font-medium mb-2">Fuentes:</div>
                      <div className="space-y-2">
                        {respuestaRAG.fuentes.map((fuente, i) => (
                          <div key={i} className="p-3 bg-background border rounded text-sm">
                            <div className="flex justify-between mb-1">
                              <Badge variant="outline">{fuente.id}</Badge>
                              <span className="text-muted-foreground">
                                {(fuente.score * 100).toFixed(1)}%
                              </span>
                            </div>
                            <p className="text-muted-foreground">{fuente.fragmento}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* === LLM === */}
        <TabsContent value="llm">
          <Card>
            <CardHeader>
              <CardTitle>Generacion de Texto</CardTitle>
              <CardDescription>
                Genera texto o resume documentos usando el modelo de lenguaje
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                placeholder="Ingrese un prompt o texto para resumir..."
                value={texto}
                onChange={(e) => setTexto(e.target.value)}
                rows={6}
              />
              <div className="flex gap-2">
                <Button onClick={handleGenerar} disabled={loading}>
                  {loading ? <LoadingSpinner /> : 'Generar'}
                </Button>
                <Button onClick={handleResumirTexto} disabled={loading} variant="secondary">
                  {loading ? <LoadingSpinner /> : 'Resumir'}
                </Button>
              </div>

              {textoGenerado && (
                <div className="mt-4 p-4 bg-muted rounded-lg">
                  <div className="font-medium mb-2">Resultado:</div>
                  <p className="whitespace-pre-wrap">{textoGenerado}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
