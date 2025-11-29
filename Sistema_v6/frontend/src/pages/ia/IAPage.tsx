/**
 * Pagina unificada de IA - Combina RAG, Busqueda y Chat
 *
 * Tabs:
 * - Consulta RAG: Pregunta + respuesta LLM basada en contexto
 * - Busqueda: Busqueda hibrida sin LLM
 * - Chat: Conversacion con historial
 */

import { useState, useEffect, useRef } from 'react'
import { toast } from 'sonner'
import {
  Search,
  Send,
  Loader2,
  Database,
  Settings2,
  Bot,
  User,
  Trash2,
  FileText,
  ChevronDown,
  ChevronUp,
  Filter,
  RefreshCw,
  MessageSquare,
  Sparkles
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import {
  ragApi,
  type RAGQueryResponse,
  type SearchOnlyResponse,
  type StatsResponse,
  type HealthCheckResponse,
  type ModelsResponse,
  type ConfigResponse,
} from '@/api/ragApi'
import type { SearchResult } from '@/types/rag'
import { chatIAStream, MensajeChat, ChatResponse } from '@/api/iaApi'

// === Tipos locales ===

interface RAGConfig {
  model: string
  temperature: number
  limite: number
  denseWeight: number
  sparseWeight: number
  filterExpediente: string
}

interface ChatMensaje {
  id: string
  rol: 'usuario' | 'asistente'
  contenido: string
  fuentes?: ChatResponse['fuentes']
  timestamp: Date
}

// Key para localStorage del chat
const CHAT_STORAGE_KEY = 'ia-chat-historial'

// Funciones de persistencia para chat
const cargarMensajesDeStorage = (): ChatMensaje[] => {
  try {
    const saved = localStorage.getItem(CHAT_STORAGE_KEY)
    if (saved) {
      const parsed = JSON.parse(saved)
      return parsed.map((m: ChatMensaje & { timestamp: string }) => ({
        ...m,
        timestamp: new Date(m.timestamp)
      }))
    }
  } catch (e) {
    console.error('Error cargando mensajes de localStorage:', e)
  }
  return []
}

const guardarMensajesEnStorage = (mensajes: ChatMensaje[]) => {
  try {
    localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(mensajes))
  } catch (e) {
    console.error('Error guardando mensajes en localStorage:', e)
  }
}

const limpiarStorage = () => {
  try {
    localStorage.removeItem(CHAT_STORAGE_KEY)
  } catch (e) {
    console.error('Error limpiando localStorage:', e)
  }
}

export default function IAPage() {
  // === Estado general ===
  const [activeTab, setActiveTab] = useState('chat')
  const [loading, setLoading] = useState(false)
  const [configOpen, setConfigOpen] = useState(true)

  // === Estado de servicios ===
  const [health, setHealth] = useState<HealthCheckResponse | null>(null)
  const [stats, setStats] = useState<StatsResponse | null>(null)
  const [models, setModels] = useState<string[]>([])
  const [serverConfig, setServerConfig] = useState<ConfigResponse | null>(null)

  // === Configuracion local ===
  const [config, setConfig] = useState<RAGConfig>({
    model: '',
    temperature: 0.7,
    limite: 5,
    denseWeight: 0.5,
    sparseWeight: 0.5,
    filterExpediente: ''
  })

  // === Estado de Query RAG ===
  const [queryText, setQueryText] = useState('')
  const [queryResponse, setQueryResponse] = useState<RAGQueryResponse | null>(null)

  // === Estado de Busqueda ===
  const [searchText, setSearchText] = useState('')
  const [searchResults, setSearchResults] = useState<SearchOnlyResponse | null>(null)

  // === Estado de Chat ===
  const [chatMensajes, setChatMensajes] = useState<ChatMensaje[]>(() => cargarMensajesDeStorage())
  const [chatInput, setChatInput] = useState('')
  const [chatCargando, setChatCargando] = useState(false)
  const [fuentesExpandidas, setFuentesExpandidas] = useState<Record<string, boolean>>({})
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const chatInputRef = useRef<HTMLInputElement>(null)

  // === Efectos ===

  // Cargar datos iniciales
  useEffect(() => {
    loadInitialData()
  }, [])

  // Guardar mensajes de chat en localStorage
  useEffect(() => {
    if (chatMensajes.length > 0) {
      guardarMensajesEnStorage(chatMensajes)
    }
  }, [chatMensajes])

  // Auto-scroll en chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMensajes])

  // === Funciones de carga ===

  const loadInitialData = async () => {
    try {
      const [healthData, statsData, modelsData, configData] = await Promise.all([
        ragApi.healthCheck().catch(() => null),
        ragApi.getStats().catch(() => null),
        ragApi.getModels().catch(() => ({ models: [], current: '' })),
        ragApi.getConfig().catch(() => null)
      ])

      if (healthData) setHealth(healthData)
      if (statsData) setStats(statsData)
      if (modelsData) {
        setModels(modelsData.models)
        if (modelsData.current) {
          setConfig(prev => ({ ...prev, model: modelsData.current }))
        }
      }
      if (configData) {
        setServerConfig(configData)
        setConfig(prev => ({
          ...prev,
          model: configData.model,
          temperature: configData.temperature,
          denseWeight: configData.dense_weight,
          sparseWeight: configData.sparse_weight,
          limite: configData.search_limit
        }))
      }
    } catch (err) {
      console.error('Error cargando datos iniciales:', err)
    }
  }

  const refreshStatus = async () => {
    setLoading(true)
    try {
      await loadInitialData()
      toast.success('Estado actualizado')
    } catch (err) {
      toast.error('Error al actualizar estado')
    } finally {
      setLoading(false)
    }
  }

  // === Handlers de Query RAG ===

  const handleQuery = async () => {
    if (!queryText.trim()) return

    setLoading(true)
    setQueryResponse(null)

    try {
      const data = await ragApi.query({
        pregunta: queryText.trim(),
        limite: config.limite,
        filter_expediente: config.filterExpediente || undefined,
        model: config.model || undefined,
        temperature: config.temperature,
        dense_weight: config.denseWeight,
        sparse_weight: config.sparseWeight
      })
      setQueryResponse(data)
      toast.success('Respuesta generada')
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Error al procesar consulta'
      toast.error('Error al consultar', { description: errorMsg })
    } finally {
      setLoading(false)
    }
  }

  // === Handlers de Busqueda ===

  const handleSearch = async () => {
    if (!searchText.trim()) return

    setLoading(true)
    setSearchResults(null)

    try {
      const data = await ragApi.search({
        texto: searchText.trim(),
        limite: config.limite * 2,
        filter_expediente: config.filterExpediente || undefined,
        dense_weight: config.denseWeight,
        sparse_weight: config.sparseWeight
      })
      setSearchResults(data)
      toast.success(`${data.total} resultados encontrados`)
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Error al buscar'
      toast.error('Error al buscar', { description: errorMsg })
    } finally {
      setLoading(false)
    }
  }

  // === Handlers de Chat ===

  const enviarMensajeChat = async () => {
    if (!chatInput.trim() || chatCargando) return

    const nuevoMensajeUsuario: ChatMensaje = {
      id: `user-${Date.now()}`,
      rol: 'usuario',
      contenido: chatInput.trim(),
      timestamp: new Date()
    }

    const assistantMessageId = `assistant-${Date.now()}`

    setChatMensajes(prev => [...prev, nuevoMensajeUsuario])
    setChatInput('')
    setChatCargando(true)

    const mensajeAsistenteInicial: ChatMensaje = {
      id: assistantMessageId,
      rol: 'asistente',
      contenido: '',
      fuentes: [],
      timestamp: new Date()
    }

    setChatMensajes(prev => [...prev, mensajeAsistenteInicial])

    try {
      const historial: MensajeChat[] = chatMensajes.map(m => ({
        rol: m.rol,
        contenido: m.contenido
      }))

      await chatIAStream(
        {
          mensaje: nuevoMensajeUsuario.contenido,
          expediente_numero: config.filterExpediente || undefined,
          historial,
          n_contextos: config.limite,
          model: config.model || undefined,
          temperature: config.temperature
        },
        (token) => {
          setChatMensajes(prev =>
            prev.map(m =>
              m.id === assistantMessageId
                ? { ...m, contenido: m.contenido + token }
                : m
            )
          )
        },
        (fuentes) => {
          setChatMensajes(prev =>
            prev.map(m =>
              m.id === assistantMessageId
                ? { ...m, fuentes }
                : m
            )
          )
        },
        () => {
          setChatCargando(false)
          chatInputRef.current?.focus()
        },
        (errorMsg) => {
          toast.error('Error en chat', { description: errorMsg })
          setChatCargando(false)
          chatInputRef.current?.focus()
        }
      )
    } catch (err) {
      toast.error('Error al enviar mensaje')
      setChatCargando(false)
      chatInputRef.current?.focus()
    }
  }

  const limpiarConversacion = () => {
    setChatMensajes([])
    setFuentesExpandidas({})
    limpiarStorage()
    chatInputRef.current?.focus()
  }

  const toggleFuentes = (mensajeId: string) => {
    setFuentesExpandidas(prev => ({
      ...prev,
      [mensajeId]: !prev[mensajeId]
    }))
  }

  // === Render helpers ===

  const renderSearchResult = (result: SearchResult, index: number) => (
    <Card key={`${result.expediente_numero}-${result.rank}-${index}`} className="mb-3">
      <CardHeader className="pb-2 pt-3 px-4">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-sm font-medium">
              {result.expediente_numero}
            </CardTitle>
            <CardDescription className="text-xs mt-0.5">
              {result.chunk_type} | Score: {(result.score * 100).toFixed(1)}% | Rank #{result.rank}
            </CardDescription>
          </div>
          <Badge variant="outline" className="text-xs">
            {result.chunk_type}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="px-4 pb-3">
        {result.highlights.length > 0 && (
          <div className="text-sm bg-yellow-50 dark:bg-yellow-900/20 p-2 rounded mb-2">
            {result.highlights[0]}
          </div>
        )}
        <details>
          <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground">
            Ver texto completo
          </summary>
          <div className="mt-2 text-sm text-muted-foreground whitespace-pre-wrap max-h-40 overflow-y-auto">
            {result.texto}
          </div>
        </details>
      </CardContent>
    </Card>
  )

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Inteligencia Artificial</h1>
          <p className="text-muted-foreground">
            Consulta y analiza expedientes con IA
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Health Status Badges */}
          {health && (
            <div className="flex gap-1.5">
              <Badge variant={health.overall ? 'default' : 'destructive'} className="text-xs">
                RAG {health.overall ? '✓' : '✗'}
              </Badge>
              <Badge variant={health.ollama ? 'default' : 'secondary'} className="text-xs">
                LLM {health.ollama ? '✓' : '✗'}
              </Badge>
              <Badge variant={health.qdrant ? 'default' : 'destructive'} className="text-xs">
                Qdrant {health.qdrant ? '✓' : '✗'}
              </Badge>
              <Badge variant={health.bm25 ? 'default' : 'destructive'} className="text-xs">
                BM25 {health.bm25 ? '✓' : '✗'}
              </Badge>
            </div>
          )}
          <Button variant="outline" size="sm" onClick={refreshStatus} disabled={loading}>
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      {/* Stats Card */}
      {stats && (
        <Card>
          <CardContent className="pt-4 pb-3">
            <div className="grid grid-cols-4 gap-4 text-sm">
              <div>
                <div className="text-muted-foreground text-xs">Qdrant</div>
                <div className="text-xl font-bold">{stats.qdrant.count}</div>
                <div className="text-xs text-muted-foreground">chunks</div>
              </div>
              <div>
                <div className="text-muted-foreground text-xs">BM25</div>
                <div className="text-xl font-bold">{stats.bm25.total_documents}</div>
                <div className="text-xs text-muted-foreground">documentos</div>
              </div>
              <div>
                <div className="text-muted-foreground text-xs">Pesos Busqueda</div>
                <div className="text-sm font-medium mt-1">
                  Dense: {stats.weights.dense} | Sparse: {stats.weights.sparse}
                </div>
              </div>
              <div>
                <div className="text-muted-foreground text-xs">Modelo Activo</div>
                <div className="text-sm font-medium mt-1 truncate">
                  {config.model || 'No configurado'}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Panel de Configuracion */}
      <Collapsible open={configOpen} onOpenChange={setConfigOpen}>
        <Card>
          <CollapsibleTrigger asChild>
            <CardHeader className="cursor-pointer hover:bg-muted/50 transition-colors py-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Settings2 className="h-4 w-4" />
                  Configuracion
                </CardTitle>
                {configOpen ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </div>
            </CardHeader>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <CardContent className="pt-0 pb-4">
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                {/* Modelo LLM */}
                <div className="space-y-1.5">
                  <Label className="text-xs">Modelo LLM</Label>
                  <Select
                    value={config.model}
                    onValueChange={(value) => setConfig(prev => ({ ...prev, model: value }))}
                  >
                    <SelectTrigger className="h-8 text-xs">
                      <SelectValue placeholder="Seleccionar..." />
                    </SelectTrigger>
                    <SelectContent>
                      {models.map((model) => (
                        <SelectItem key={model} value={model} className="text-xs">
                          {model}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Temperature */}
                <div className="space-y-1.5">
                  <Label className="text-xs">Temperature: {config.temperature.toFixed(2)}</Label>
                  <Slider
                    value={[config.temperature]}
                    min={0}
                    max={1}
                    step={0.05}
                    onValueChange={([value]) => setConfig(prev => ({ ...prev, temperature: value }))}
                    className="mt-2"
                  />
                </div>

                {/* Limite chunks */}
                <div className="space-y-1.5">
                  <Label className="text-xs">Chunks: {config.limite}</Label>
                  <Slider
                    value={[config.limite]}
                    min={1}
                    max={20}
                    step={1}
                    onValueChange={([value]) => setConfig(prev => ({ ...prev, limite: value }))}
                    className="mt-2"
                  />
                </div>

                {/* Dense Weight */}
                <div className="space-y-1.5">
                  <Label className="text-xs">Dense: {config.denseWeight.toFixed(2)}</Label>
                  <Slider
                    value={[config.denseWeight]}
                    min={0}
                    max={1}
                    step={0.05}
                    onValueChange={([value]) => setConfig(prev => ({ ...prev, denseWeight: value }))}
                    className="mt-2"
                  />
                </div>

                {/* Sparse Weight */}
                <div className="space-y-1.5">
                  <Label className="text-xs">Sparse: {config.sparseWeight.toFixed(2)}</Label>
                  <Slider
                    value={[config.sparseWeight]}
                    min={0}
                    max={1}
                    step={0.05}
                    onValueChange={([value]) => setConfig(prev => ({ ...prev, sparseWeight: value }))}
                    className="mt-2"
                  />
                </div>

                {/* Filtro Expediente */}
                <div className="space-y-1.5">
                  <Label className="text-xs">Filtrar Expediente</Label>
                  <div className="flex gap-1">
                    <Input
                      placeholder="Ej: 12345/2024"
                      value={config.filterExpediente}
                      onChange={(e) => setConfig(prev => ({ ...prev, filterExpediente: e.target.value }))}
                      className="h-8 text-xs"
                    />
                    {config.filterExpediente && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 px-2"
                        onClick={() => setConfig(prev => ({ ...prev, filterExpediente: '' }))}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          </CollapsibleContent>
        </Card>
      </Collapsible>

      {/* Tabs principales */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="query">
            <Sparkles className="h-4 w-4 mr-2" />
            Debug RAG
          </TabsTrigger>
          <TabsTrigger value="search">
            <Search className="h-4 w-4 mr-2" />
            Busqueda
          </TabsTrigger>
          <TabsTrigger value="chat">
            <MessageSquare className="h-4 w-4 mr-2" />
            Chat
          </TabsTrigger>
        </TabsList>

        {/* === Tab: Consulta RAG === */}
        <TabsContent value="query" className="space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle>Consulta con IA</CardTitle>
              <CardDescription>
                Realiza preguntas sobre tus expedientes. El sistema buscara informacion relevante
                y generara una respuesta contextual usando el LLM.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                placeholder="¿Cual es el estado del expediente? ¿Que plazos estan pendientes?"
                value={queryText}
                onChange={(e) => setQueryText(e.target.value)}
                rows={3}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    handleQuery()
                  }
                }}
              />
              <Button onClick={handleQuery} disabled={loading || !queryText.trim()}>
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Procesando...
                  </>
                ) : (
                  <>
                    <Send className="mr-2 h-4 w-4" />
                    Consultar
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {queryResponse && (
            <div className="space-y-4">
              {/* Respuesta */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg">Respuesta</CardTitle>
                  <CardDescription>Pregunta: {queryResponse.pregunta}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="prose prose-sm dark:prose-invert max-w-none">
                    <p className="whitespace-pre-wrap">{queryResponse.respuesta}</p>
                  </div>
                  <div className="mt-3 text-xs text-muted-foreground flex gap-4">
                    <span>Modelo: {queryResponse.metadata.model || config.model}</span>
                    <span>Chunks: {queryResponse.metadata.num_chunks}</span>
                    {queryResponse.metadata.temperature && (
                      <span>Temp: {queryResponse.metadata.temperature}</span>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Fuentes */}
              {queryResponse.resultados.length > 0 && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg">Fuentes Consultadas ({queryResponse.resultados.length})</CardTitle>
                  </CardHeader>
                  <CardContent className="max-h-[400px] overflow-y-auto">
                    {queryResponse.resultados.map((result, index) => renderSearchResult(result, index))}
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </TabsContent>

        {/* === Tab: Busqueda === */}
        <TabsContent value="search" className="space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle>Busqueda Hibrida</CardTitle>
              <CardDescription>
                Busca documentos relevantes usando busqueda vectorial (Dense) y BM25 (Sparse)
                con fusion RRF. Sin generacion de respuesta LLM.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Input
                  placeholder="Buscar en expedientes..."
                  value={searchText}
                  onChange={(e) => setSearchText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleSearch()
                  }}
                />
                <Button onClick={handleSearch} disabled={loading || !searchText.trim()}>
                  {loading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Search className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          {searchResults && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg">
                  Resultados ({searchResults.total})
                </CardTitle>
              </CardHeader>
              <CardContent className="max-h-[500px] overflow-y-auto">
                {searchResults.resultados.map((result, index) => renderSearchResult(result, index))}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* === Tab: Chat === */}
        <TabsContent value="chat" className="space-y-0">
          <Card className="h-[calc(100vh-26rem)] flex flex-col">
            <CardHeader className="flex-shrink-0 border-b py-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Bot className="h-5 w-5 text-primary" />
                  <CardTitle className="text-base">Asistente IA</CardTitle>
                </div>
                <div className="flex items-center gap-2">
                  {config.filterExpediente && (
                    <Badge variant="secondary" className="text-xs">
                      <Filter className="h-3 w-3 mr-1" />
                      {config.filterExpediente}
                    </Badge>
                  )}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={limpiarConversacion}
                    disabled={chatMensajes.length === 0}
                  >
                    <Trash2 className="h-4 w-4 mr-1" />
                    Limpiar
                  </Button>
                </div>
              </div>
            </CardHeader>

            <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
              {chatMensajes.length === 0 ? (
                <div className="h-full flex items-center justify-center text-center">
                  <div className="space-y-3">
                    <Bot className="h-12 w-12 mx-auto text-muted-foreground/50" />
                    <div>
                      <p className="font-medium">Asistente Juridico IA</p>
                      <p className="text-sm text-muted-foreground">
                        Pregunta sobre tus expedientes y actuaciones
                      </p>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Ejemplos:
                      <ul className="mt-1 space-y-0.5">
                        <li>"¿Cuales son las ultimas actuaciones?"</li>
                        <li>"Resume los alegatos presentados"</li>
                        <li>"¿Que plazos estan pendientes?"</li>
                      </ul>
                    </div>
                  </div>
                </div>
              ) : (
                <>
                  {chatMensajes.map((mensaje) => (
                    <div
                      key={mensaje.id}
                      className={`flex gap-3 ${mensaje.rol === 'usuario' ? 'justify-end' : 'justify-start'}`}
                    >
                      {mensaje.rol === 'asistente' && (
                        <div className="flex-shrink-0 w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center">
                          <Bot className="h-4 w-4 text-primary" />
                        </div>
                      )}

                      <div
                        className={`max-w-[80%] rounded-lg p-3 ${mensaje.rol === 'usuario'
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted'
                          }`}
                      >
                        <p className="whitespace-pre-wrap text-sm">{mensaje.contenido}</p>

                        {mensaje.rol === 'asistente' && mensaje.fuentes && mensaje.fuentes.length > 0 && (
                          <div className="mt-2 pt-2 border-t border-border/50">
                            <button
                              onClick={() => toggleFuentes(mensaje.id)}
                              className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
                            >
                              <FileText className="h-3 w-3" />
                              {mensaje.fuentes.length} fuente(s)
                              {fuentesExpandidas[mensaje.id] ? (
                                <ChevronUp className="h-3 w-3" />
                              ) : (
                                <ChevronDown className="h-3 w-3" />
                              )}
                            </button>

                            {fuentesExpandidas[mensaje.id] && (
                              <div className="mt-2 space-y-2">
                                {mensaje.fuentes.map((fuente, idx) => (
                                  <div key={idx} className="text-xs p-2 bg-background rounded border">
                                    <div className="flex items-center gap-2 mb-1">
                                      {fuente.expediente && (
                                        <Badge variant="outline" className="text-[10px]">
                                          {fuente.expediente}
                                        </Badge>
                                      )}
                                      <span className="text-muted-foreground">
                                        Score: {(fuente.score * 100).toFixed(0)}%
                                      </span>
                                    </div>
                                    <p className="text-muted-foreground line-clamp-3">
                                      {fuente.fragmento}
                                    </p>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        )}

                        <p className="text-[10px] mt-1 opacity-60">
                          {mensaje.timestamp.toLocaleTimeString()}
                        </p>
                      </div>

                      {mensaje.rol === 'usuario' && (
                        <div className="flex-shrink-0 w-7 h-7 rounded-full bg-primary flex items-center justify-center">
                          <User className="h-4 w-4 text-primary-foreground" />
                        </div>
                      )}
                    </div>
                  ))}

                  {chatCargando && (
                    <div className="flex gap-3 justify-start">
                      <div className="flex-shrink-0 w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center">
                        <Bot className="h-4 w-4 text-primary animate-pulse" />
                      </div>
                      <div className="bg-muted rounded-lg p-3">
                        <div className="flex gap-1">
                          <div className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                          <div className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                          <div className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                        </div>
                      </div>
                    </div>
                  )}

                  <div ref={messagesEndRef} />
                </>
              )}
            </CardContent>

            {/* Input de chat */}
            <div className="flex-shrink-0 border-t p-3">
              <div className="flex gap-2">
                <Input
                  ref={chatInputRef}
                  placeholder="Escribe tu pregunta..."
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      enviarMensajeChat()
                    }
                  }}
                  disabled={chatCargando}
                  className="flex-1"
                />
                <Button
                  onClick={enviarMensajeChat}
                  disabled={!chatInput.trim() || chatCargando}
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
