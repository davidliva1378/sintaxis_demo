/**
 * AddToWorkspaceDialog - Modal para agregar expediente a un workspace
 */

import { useEffect, useState } from 'react'
import { X, Plus, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { useWorkspacesStore } from '@/stores/workspacesStore'
import { toast } from 'sonner'
import {
  Folder,
  FolderOpen,
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
  FileText,
  Clipboard,
} from 'lucide-react'

interface AddToWorkspaceDialogProps {
  isOpen: boolean
  onClose: () => void
  expedienteNumero: string
  expedienteCaratula: string
}

// Mapeo de iconos
const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  folder: Folder,
  'folder-open': FolderOpen,
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

export default function AddToWorkspaceDialog({
  isOpen,
  onClose,
  expedienteNumero,
  expedienteCaratula,
}: AddToWorkspaceDialogProps) {
  const { workspaces, listarWorkspaces, agregarExpediente } = useWorkspacesStore()
  const [selectedWorkspaces, setSelectedWorkspaces] = useState<Set<number>>(new Set())
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (isOpen) {
      listarWorkspaces()
      setSelectedWorkspaces(new Set())
    }
  }, [isOpen, listarWorkspaces])

  const toggleWorkspace = (workspaceId: number) => {
    const newSet = new Set(selectedWorkspaces)
    if (newSet.has(workspaceId)) {
      newSet.delete(workspaceId)
    } else {
      newSet.add(workspaceId)
    }
    setSelectedWorkspaces(newSet)
  }

  const handleSubmit = async () => {
    if (selectedWorkspaces.size === 0) {
      toast.error('Debes seleccionar al menos un workspace')
      return
    }

    setIsSubmitting(true)

    try {
      // Agregar a todos los workspaces seleccionados
      const promises = Array.from(selectedWorkspaces).map(workspaceId =>
        agregarExpediente(workspaceId, expedienteNumero)
      )
      await Promise.all(promises)

      toast.success('Expediente agregado', {
        description: `Se agregó a ${selectedWorkspaces.size} workspace${
          selectedWorkspaces.size > 1 ? 's' : ''
        }`,
      })

      onClose()
    } catch (error) {
      toast.error('Error al agregar expediente')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
              Agregar a Workspace
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {expedienteCaratula}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            disabled={isSubmitting}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Contenido */}
        <div className="p-6">
          {workspaces.length === 0 ? (
            <div className="text-center py-12">
              <Folder className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                No tienes workspaces todavía
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Crea un workspace primero para organizar tus expedientes
              </p>
              <Button onClick={onClose}>Entendido</Button>
            </div>
          ) : (
            <>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Selecciona uno o más workspaces donde agregar este expediente:
              </p>

              <div className="space-y-3 max-h-96 overflow-y-auto">
                {workspaces.map(workspace => {
                  const IconComponent = workspace.icon
                    ? ICON_MAP[workspace.icon] || Folder
                    : Folder
                  const isSelected = selectedWorkspaces.has(workspace.id)

                  return (
                    <button
                      key={workspace.id}
                      onClick={() => toggleWorkspace(workspace.id)}
                      disabled={isSubmitting}
                      className={`w-full p-4 rounded-lg border-2 transition-all text-left ${
                        isSelected
                          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                      }`}
                    >
                      <div className="flex items-center gap-4">
                        <div
                          className="p-3 rounded-lg flex-shrink-0"
                          style={{ backgroundColor: `${workspace.color}20` }}
                        >
                          <IconComponent
                            className="h-5 w-5"
                            style={{ color: workspace.color || '#3b82f6' }}
                          />
                        </div>

                        <div className="flex-1 min-w-0">
                          <h4 className="font-semibold text-gray-900 dark:text-gray-100 truncate">
                            {workspace.nombre}
                          </h4>
                          {workspace.descripcion && (
                            <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
                              {workspace.descripcion}
                            </p>
                          )}
                          <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                            {workspace.expedientes_count}{' '}
                            {workspace.expedientes_count === 1
                              ? 'expediente'
                              : 'expedientes'}
                          </p>
                        </div>

                        {isSelected && (
                          <Check className="h-6 w-6 text-blue-600 dark:text-blue-400 flex-shrink-0" />
                        )}
                      </div>
                    </button>
                  )
                })}
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        {workspaces.length > 0 && (
          <div className="flex gap-3 p-6 border-t border-gray-200 dark:border-gray-700">
            <Button
              variant="outline"
              onClick={onClose}
              disabled={isSubmitting}
              className="flex-1"
            >
              Cancelar
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={isSubmitting || selectedWorkspaces.size === 0}
              className="flex-1"
            >
              {isSubmitting ? (
                'Agregando...'
              ) : (
                <>
                  <Plus className="h-4 w-4 mr-2" />
                  Agregar a {selectedWorkspaces.size} workspace
                  {selectedWorkspaces.size !== 1 ? 's' : ''}
                </>
              )}
            </Button>
          </div>
        )}
      </Card>
    </div>
  )
}
