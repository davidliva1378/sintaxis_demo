/**
 * Pagina de Asistente IA con chat conversacional
 */

import { useState, useRef, useEffect } from 'react'
import { Send, Trash2, Bot, User, FileText, ChevronDown, ChevronUp, Filter } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { chatIAStream, MensajeChat, ChatResponse } from '@/api/iaApi'

interface Mensaje {
  id: string
  rol: 'usuario' | 'asistente'
  contenido: string
  fuentes?: ChatResponse['fuentes']
  timestamp: Date
}

// Key para localStorage
const STORAGE_KEY = 'asistente-ia-historial'

// Funciones de persistencia
const cargarMensajesDeStorage = (): Mensaje[] => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      const parsed = JSON.parse(saved)
      // Convertir strings de timestamp a Date
      return parsed.map((m: Mensaje & { timestamp: string }) => ({
        ...m,
        timestamp: new Date(m.timestamp)
      }))
    }
  } catch (e) {
    console.error('Error cargando mensajes de localStorage:', e)
  }
  return []
}

const guardarMensajesEnStorage = (mensajes: Mensaje[]) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(mensajes))
  } catch (e) {
    console.error('Error guardando mensajes en localStorage:', e)
  }
}

const limpiarStorage = () => {
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch (e) {
    console.error('Error limpiando localStorage:', e)
  }
}

export default function AsistenteIAPage() {
  // Cargar mensajes iniciales desde localStorage
  const [mensajes, setMensajes] = useState<Mensaje[]>(() => cargarMensajesDeStorage())
  const [inputMensaje, setInputMensaje] = useState('')
  const [expedienteFiltro, setExpedienteFiltro] = useState('')
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [fuentesExpandidas, setFuentesExpandidas] = useState<Record<string, boolean>>({})

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Guardar mensajes en localStorage cuando cambien
  useEffect(() => {
    if (mensajes.length > 0) {
      guardarMensajesEnStorage(mensajes)
    }
  }, [mensajes])

  // Auto-scroll al final cuando hay nuevos mensajes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [mensajes])

  // Focus en input al cargar
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const enviarMensaje = async () => {
    if (!inputMensaje.trim() || cargando) return

    const nuevoMensajeUsuario: Mensaje = {
      id: `user-${Date.now()}`,
      rol: 'usuario',
      contenido: inputMensaje.trim(),
      timestamp: new Date()
    }

    // ID para el mensaje del asistente que se va a crear
    const assistantMessageId = `assistant-${Date.now()}`

    setMensajes(prev => [...prev, nuevoMensajeUsuario])
    setInputMensaje('')
    setCargando(true)
    setError(null)

    // Crear mensaje vacío del asistente para ir llenándolo
    const mensajeAsistenteInicial: Mensaje = {
      id: assistantMessageId,
      rol: 'asistente',
      contenido: '',
      fuentes: [],
      timestamp: new Date()
    }

    setMensajes(prev => [...prev, mensajeAsistenteInicial])

    try {
      // Preparar historial para la API
      const historial: MensajeChat[] = mensajes.map(m => ({
        rol: m.rol,
        contenido: m.contenido
      }))

      await chatIAStream(
        {
          mensaje: nuevoMensajeUsuario.contenido,
          expediente_numero: expedienteFiltro || undefined,
          historial,
          n_contextos: 5
        },
        // onToken: agregar cada token al mensaje
        (token) => {
          setMensajes(prev =>
            prev.map(m =>
              m.id === assistantMessageId
                ? { ...m, contenido: m.contenido + token }
                : m
            )
          )
        },
        // onFuentes: actualizar las fuentes
        (fuentes) => {
          setMensajes(prev =>
            prev.map(m =>
              m.id === assistantMessageId
                ? { ...m, fuentes }
                : m
            )
          )
        },
        // onDone: streaming completado
        () => {
          setCargando(false)
          inputRef.current?.focus()
        },
        // onError: manejar error
        (errorMsg) => {
          setError(errorMsg)
          setCargando(false)
          inputRef.current?.focus()
        }
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al enviar mensaje')
      setCargando(false)
      inputRef.current?.focus()
    }
  }

  const limpiarConversacion = () => {
    setMensajes([])
    setError(null)
    setFuentesExpandidas({})
    limpiarStorage()  // También limpiar localStorage
    inputRef.current?.focus()
  }

  const toggleFuentes = (mensajeId: string) => {
    setFuentesExpandidas(prev => ({
      ...prev,
      [mensajeId]: !prev[mensajeId]
    }))
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      enviarMensaje()
    }
  }

  return (
    <div className="container mx-auto p-4 h-[calc(100vh-8rem)] flex flex-col">
      <Card className="flex-1 flex flex-col overflow-hidden">
        <CardHeader className="flex-shrink-0 border-b">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bot className="h-6 w-6 text-primary" />
              <CardTitle>Asistente IA</CardTitle>
            </div>
            <div className="flex items-center gap-2">
              {/* Filtro por expediente */}
              <div className="flex items-center gap-2">
                <Filter className="h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Filtrar por expediente..."
                  value={expedienteFiltro}
                  onChange={(e) => setExpedienteFiltro(e.target.value)}
                  className="w-48 h-8 text-sm"
                />
                {expedienteFiltro && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setExpedienteFiltro('')}
                  >
                    Limpiar
                  </Button>
                )}
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={limpiarConversacion}
                disabled={mensajes.length === 0}
              >
                <Trash2 className="h-4 w-4 mr-1" />
                Limpiar
              </Button>
            </div>
          </div>
          {expedienteFiltro && (
            <p className="text-sm text-muted-foreground mt-2">
              Filtrando por expediente: <Badge variant="secondary">{expedienteFiltro}</Badge>
            </p>
          )}
        </CardHeader>

        <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
          {mensajes.length === 0 ? (
            <div className="h-full flex items-center justify-center text-center">
              <div className="space-y-4">
                <Bot className="h-16 w-16 mx-auto text-muted-foreground/50" />
                <div>
                  <p className="text-lg font-medium">Asistente Juridico IA</p>
                  <p className="text-sm text-muted-foreground">
                    Pregunta sobre tus expedientes y actuaciones.
                    <br />
                    El asistente buscara informacion relevante y te respondera.
                  </p>
                </div>
                <div className="text-xs text-muted-foreground">
                  Ejemplos de preguntas:
                  <ul className="mt-2 space-y-1">
                    <li>"¿Cuales son las ultimas actuaciones del expediente?"</li>
                    <li>"Resume los alegatos presentados"</li>
                    <li>"¿Que plazos estan pendientes?"</li>
                  </ul>
                </div>
              </div>
            </div>
          ) : (
            <>
              {mensajes.map((mensaje) => (
                <div
                  key={mensaje.id}
                  className={`flex gap-3 ${
                    mensaje.rol === 'usuario' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  {mensaje.rol === 'asistente' && (
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                      <Bot className="h-5 w-5 text-primary" />
                    </div>
                  )}

                  <div
                    className={`max-w-[80%] rounded-lg p-3 ${
                      mensaje.rol === 'usuario'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted'
                    }`}
                  >
                    <p className="whitespace-pre-wrap text-sm">{mensaje.contenido}</p>

                    {/* Fuentes para respuestas del asistente */}
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
                              <div
                                key={idx}
                                className="text-xs p-2 bg-background rounded border"
                              >
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
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center">
                      <User className="h-5 w-5 text-primary-foreground" />
                    </div>
                  )}
                </div>
              ))}

              {cargando && (
                <div className="flex gap-3 justify-start">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                    <Bot className="h-5 w-5 text-primary animate-pulse" />
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

        {/* Input de mensaje */}
        <div className="flex-shrink-0 border-t p-4">
          {error && (
            <p className="text-sm text-destructive mb-2">{error}</p>
          )}
          <div className="flex gap-2">
            <Input
              ref={inputRef}
              placeholder="Escribe tu pregunta..."
              value={inputMensaje}
              onChange={(e) => setInputMensaje(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={cargando}
              className="flex-1"
            />
            <Button
              onClick={enviarMensaje}
              disabled={!inputMensaje.trim() || cargando}
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )
}
