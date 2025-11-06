/**
 * WorkspaceDetailPage - Vista de detalle de un workspace con sus expedientes
 */

import { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Loader2, FolderOpen, FileText, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useWorkspacesStore } from '@/stores/workspacesStore'
import {
  Folder,
  FolderOpen as FolderOpenIcon,
  Briefcase,
  Archive,
  Bookmark,
  Star,
  Heart,
  Flag,
  Target,
  Award,
  Layers,
  Package,
  Inbox,
  Clipboard,
} from 'lucide-react'

// Mapeo de iconos
const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  folder: Folder,
  'folder-open': FolderOpenIcon,
  briefcase: Briefcase,
  archive: Archive,
  bookmark: Bookmark,
  star: Star,
  heart: Heart,
  flag: Flag,
  target: Target,
  award: Award,
  layers: Layers,
  package: Package,
  inbox: Inbox,
  'file-text': FileText,
  clipboard: Clipboard,
}

// Mapeo de colores para situaciones
const SITUACION_COLORS: Record<string, string> = {
  'EN TRAMITE': 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
  'SENTENCIA': 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
  'ARCHIVADO': 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400',
  'SUSPENDIDO': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400',
}

export default function WorkspaceDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { workspaceActual, isLoading, obtenerWorkspace, removerExpediente, limpiarWorkspaceActual } =
    useWorkspacesStore()

  useEffect(() => {
    if (id) {
      obtenerWorkspace(parseInt(id))
    }

    return () => {
      limpiarWorkspaceActual()
    }
  }, [id, obtenerWorkspace, limpiarWorkspaceActual])

  const handleVolver = () => {
    navigate('/workspaces')
  }

  const handleVerExpediente = (numero: string) => {
    navigate(`/expedientes/${numero}`)
  }

  const handleRemoverExpediente = async (numero: string) => {
    if (!workspaceActual) return

    if (
      confirm(`¿Estás seguro de remover este expediente del workspace?\n\nEl expediente no se eliminará del sistema.`)
    ) {
      await removerExpediente(workspaceActual.id, numero)
    }
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        <span className="ml-3 text-gray-600 dark:text-gray-400">
          Cargando workspace...
        </span>
      </div>
    )
  }

  // No encontrado
  if (!workspaceActual && !isLoading) {
    return (
      <div className="space-y-6">
        <Button variant="outline" onClick={handleVolver}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Volver
        </Button>

        <Card className="p-12">
          <div className="text-center">
            <FolderOpen className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Workspace no encontrado
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              El workspace que buscas no existe o fue eliminado
            </p>
          </div>
        </Card>
      </div>
    )
  }

  if (!workspaceActual) return null

  const IconComponent = workspaceActual.icon
    ? ICON_MAP[workspaceActual.icon] || Folder
    : Folder

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Button variant="outline" onClick={handleVolver}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Volver
        </Button>
      </div>

      {/* Info del Workspace */}
      <Card className="p-6 border-l-4" style={{ borderLeftColor: workspaceActual.color || '#3b82f6' }}>
        <div className="flex items-start gap-6">
          <div
            className="p-4 rounded-lg flex-shrink-0"
            style={{ backgroundColor: `${workspaceActual.color}20` }}
          >
            <IconComponent
              className="h-10 w-10"
              style={{ color: workspaceActual.color || '#3b82f6' }}
            />
          </div>

          <div className="flex-1">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              {workspaceActual.nombre}
            </h1>
            {workspaceActual.descripcion && (
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                {workspaceActual.descripcion}
              </p>
            )}

            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-gray-500 dark:text-gray-400" />
                <span className="text-gray-700 dark:text-gray-300">
                  <span className="font-semibold">{workspaceActual.expedientes_count}</span>{' '}
                  {workspaceActual.expedientes_count === 1 ? 'expediente' : 'expedientes'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Lista de Expedientes */}
      {workspaceActual.expedientes.length === 0 ? (
        <Card className="p-12">
          <div className="text-center">
            <FileText className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              No hay expedientes en este workspace
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Agrega expedientes desde el módulo de Expedientes
            </p>
          </div>
        </Card>
      ) : (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Expedientes ({workspaceActual.expedientes.length})
          </h2>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {workspaceActual.expedientes.map(expediente => (
              <Card key={expediente.numero} className="p-6 hover:shadow-lg transition-shadow group">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-1">
                      {expediente.numero}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                      {expediente.caratula}
                    </p>
                  </div>

                  <Button
                    variant="ghost"
                    size="sm"
                    className="opacity-0 group-hover:opacity-100 transition-opacity text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"
                    onClick={() => handleRemoverExpediente(expediente.numero)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>

                {expediente.dependencia && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                    {expediente.dependencia}
                  </p>
                )}

                <div className="flex items-center justify-between">
                  {expediente.situacion && (
                    <Badge
                      className={
                        SITUACION_COLORS[expediente.situacion] ||
                        'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400'
                      }
                    >
                      {expediente.situacion}
                    </Badge>
                  )}

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleVerExpediente(expediente.numero)}
                  >
                    Ver detalle
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
