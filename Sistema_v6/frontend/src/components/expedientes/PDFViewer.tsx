import { Download, ExternalLink, X, FileText, Calendar } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface PDFViewerProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  expedienteNumero: string
  actuacionIndice: number
  actuacionTipo?: string
  actuacionFecha?: string
  actuacionDetalle?: string
  nombreArchivo: string
}

export default function PDFViewer({
  open,
  onOpenChange,
  expedienteNumero,
  actuacionIndice,
  actuacionTipo,
  actuacionFecha,
  actuacionDetalle,
  nombreArchivo,
}: PDFViewerProps) {
  const pdfUrl = `${API_BASE_URL}/api/v1/expedientes/${encodeURIComponent(expedienteNumero)}/actuaciones/${actuacionIndice}/pdf`

  const formatFecha = (fecha: string | undefined) => {
    if (!fecha) return null
    try {
      return format(new Date(fecha), "dd 'de' MMMM 'de' yyyy", { locale: es })
    } catch {
      return fecha
    }
  }

  const handleDownload = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(pdfUrl, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      })

      if (!response.ok) throw new Error('Error al descargar')

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = nombreArchivo
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Error downloading PDF:', error)
    }
  }

  const handleOpenExternal = () => {
    window.open(pdfUrl, '_blank')
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-6xl w-[95vw] h-[90vh] flex flex-col p-0">
        <DialogHeader className="px-6 py-4 border-b flex-shrink-0">
          <div className="flex items-start justify-between">
            <div className="space-y-2">
              <DialogTitle className="text-xl font-semibold">
                {nombreArchivo}
              </DialogTitle>
              <div className="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400">
                {actuacionTipo && (
                  <Badge variant="outline">
                    <FileText className="h-3 w-3 mr-1" />
                    {actuacionTipo}
                  </Badge>
                )}
                {actuacionFecha && (
                  <span className="flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {formatFecha(actuacionFecha)}
                  </span>
                )}
                <span className="text-xs">
                  Actuacion #{actuacionIndice}
                </span>
              </div>
              {actuacionDetalle && (
                <p className="text-sm text-gray-500 dark:text-gray-400 line-clamp-2 max-w-2xl">
                  {actuacionDetalle}
                </p>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleOpenExternal}
                title="Abrir en nueva pestana"
              >
                <ExternalLink className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleDownload}
                title="Descargar"
              >
                <Download className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </DialogHeader>

        <div className="flex-1 overflow-hidden bg-gray-100 dark:bg-gray-900">
          <iframe
            src={pdfUrl}
            className="w-full h-full border-0"
            title={`PDF: ${nombreArchivo}`}
          />
        </div>
      </DialogContent>
    </Dialog>
  )
}
