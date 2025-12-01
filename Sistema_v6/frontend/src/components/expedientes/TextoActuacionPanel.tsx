import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  FileText,
  Loader2,
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
  Table2,
  Image,
  FileType,
  Info
} from 'lucide-react'
import { toast } from 'sonner'
import {
  obtenerTextoActuacion,
  type TextoExtraidoResponse
} from '@/api/expedientesApi'

interface TextoActuacionPanelProps {
  expedienteNumero: string
  actuacionIndice: number
  nombreArchivo?: string
  expanded?: boolean
  onToggle?: () => void
}

export default function TextoActuacionPanel({
  expedienteNumero,
  actuacionIndice,
  nombreArchivo,
  expanded,
  onToggle
}: TextoActuacionPanelProps) {
  const [internalExpanded, setInternalExpanded] = useState(false)

  const isExpanded = expanded !== undefined ? expanded : internalExpanded
  const handleToggle = onToggle || (() => setInternalExpanded(!internalExpanded))

  const [isLoading, setIsLoading] = useState(false)
  const [texto, setTexto] = useState<TextoExtraidoResponse | null>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (isExpanded && !texto) {
      cargarTexto()
    }
  }, [isExpanded])

  const cargarTexto = async () => {
    setIsLoading(true)
    try {
      const result = await obtenerTextoActuacion(expedienteNumero, actuacionIndice)
      setTexto(result)
    } catch (error) {
      toast.error('Error al cargar texto')
      setTexto({
        tiene_texto: false,
        texto_completo: null,
        texto_normalizado: null,
        preview: null,
        metadata: null,
        texto_por_pagina: null
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleCopy = async () => {
    if (texto?.texto_completo) {
      await navigator.clipboard.writeText(texto.texto_completo)
      setCopied(true)
      toast.success('Texto copiado al portapapeles')
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const getMetodoIcon = (metodo?: string) => {
    switch (metodo) {
      case 'ocr':
        return <Image className="h-3 w-3" />
      case 'pdfplumber':
        return <Table2 className="h-3 w-3" />
      default:
        return <FileType className="h-3 w-3" />
    }
  }

  const getMetodoLabel = (metodo?: string) => {
    switch (metodo) {
      case 'ocr':
        return 'OCR'
      case 'pdfplumber':
        return 'PDF Plumber'
      case 'embebido':
        return 'Texto embebido'
      case 'mixto':
        return 'Mixto'
      default:
        return 'Desconocido'
    }
  }

  return (
    <Card className="mt-2 border-blue-200 dark:border-blue-800">
      <CardHeader className="p-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-blue-600" />
            <CardTitle className="text-sm">
              Texto extraido
              {nombreArchivo && (
                <span className="text-xs text-gray-500 ml-2">({nombreArchivo})</span>
              )}
            </CardTitle>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleToggle}
          >
            {isExpanded ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>
        </div>
      </CardHeader>

      {isExpanded && (
        <CardContent className="pt-0 pb-3">
          {isLoading ? (
            <div className="flex items-center justify-center py-4">
              <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
              <span className="ml-2 text-sm text-gray-500">Cargando texto...</span>
            </div>
          ) : texto?.tiene_texto ? (
            <div className="space-y-3">
              {/* Metadata */}
              {texto.metadata && (
                <div className="flex flex-wrap gap-2 text-xs">
                  <Badge variant="outline" className="gap-1">
                    {getMetodoIcon(texto.metadata.metodo_extraccion)}
                    {getMetodoLabel(texto.metadata.metodo_extraccion)}
                  </Badge>
                  {texto.metadata.total_paginas && (
                    <Badge variant="secondary">
                      {texto.metadata.total_paginas} pag
                    </Badge>
                  )}
                  {texto.metadata.total_palabras && (
                    <Badge variant="secondary">
                      {texto.metadata.total_palabras.toLocaleString()} palabras
                    </Badge>
                  )}
                  {texto.metadata.tiene_tablas && (
                    <Badge variant="outline" className="gap-1 text-amber-600 border-amber-300">
                      <Table2 className="h-3 w-3" />
                      Tablas
                    </Badge>
                  )}
                  {texto.metadata.requirio_ocr && (
                    <Badge variant="outline" className="gap-1 text-purple-600 border-purple-300">
                      <Image className="h-3 w-3" />
                      OCR
                    </Badge>
                  )}
                </div>
              )}

              {/* Texto */}
              <div className="relative">
                <div className="max-h-[500px] overflow-y-auto rounded-lg bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-800 p-4 text-sm font-mono leading-relaxed shadow-inner">
                  <pre className="whitespace-pre-wrap break-words text-gray-700 dark:text-gray-300 font-medium">
                    {texto.texto_normalizado || texto.texto_completo || 'Sin texto'}
                  </pre>
                </div>

                {/* Copy button */}
                <Button
                  variant="outline"
                  size="sm"
                  className="absolute top-2 right-2"
                  onClick={handleCopy}
                >
                  {copied ? (
                    <Check className="h-3 w-3 text-green-500" />
                  ) : (
                    <Copy className="h-3 w-3" />
                  )}
                </Button>
              </div>

              {/* Pages info */}
              {texto.texto_por_pagina && texto.texto_por_pagina.length > 1 && (
                <div className="text-xs text-gray-500 flex items-center gap-1">
                  <Info className="h-3 w-3" />
                  Texto de {texto.texto_por_pagina.length} paginas concatenado
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-8 text-center bg-gray-50 dark:bg-gray-900/50 rounded-lg border border-dashed border-gray-200 dark:border-gray-800">
              <div className="bg-gray-100 dark:bg-gray-800 p-3 rounded-full mb-3">
                <FileText className="h-6 w-6 text-gray-400" />
              </div>
              <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-1">
                No hay texto extraído disponible
              </h3>
              <p className="text-xs text-gray-500 max-w-xs mb-4">
                El texto de esta actuación no ha sido procesado o no se pudo extraer automáticamente.
              </p>
              {nombreArchivo && (
                <Button variant="outline" size="sm" className="gap-2" onClick={() => toast.info(`Abre el PDF "${nombreArchivo}" desde la lista principal`)}>
                  <FileType className="h-3 w-3" />
                  Ver PDF Original
                </Button>
              )}
            </div>
          )}
        </CardContent>
      )}
    </Card>
  )
}
