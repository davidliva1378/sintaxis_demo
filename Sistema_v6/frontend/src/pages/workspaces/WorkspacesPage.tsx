/**
 * WorkspacesPage - Página principal de gestión de Workspaces
 */

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, Loader2, FolderOpen } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import WorkspaceCard from '@/components/workspaces/WorkspaceCard'
import CreateWorkspaceDialog from '@/components/workspaces/CreateWorkspaceDialog'
import { useWorkspacesStore } from '@/stores/workspacesStore'
import type { Workspace, WorkspaceCrear, WorkspaceActualizar } from '@/types/workspace'

export default function WorkspacesPage() {
  const navigate = useNavigate()
  const {
    workspaces,
    isLoading,
    listarWorkspaces,
    crearWorkspace,
    actualizarWorkspace,
    eliminarWorkspace,
  } = useWorkspacesStore()

  const [showDialog, setShowDialog] = useState(false)
  const [workspaceEditando, setWorkspaceEditando] = useState<Workspace | null>(null)

  // Cargar workspaces al montar
  useEffect(() => {
    listarWorkspaces()
  }, [listarWorkspaces])

  const handleCrearNuevo = () => {
    setWorkspaceEditando(null)
    setShowDialog(true)
  }

  const handleEditar = (workspace: Workspace) => {
    setWorkspaceEditando(workspace)
    setShowDialog(true)
  }

  const handleEliminar = async (id: number) => {
    await eliminarWorkspace(id)
  }

  const handleVerDetalles = (id: number) => {
    navigate(`/workspaces/${id}`)
  }

  const handleSubmit = async (data: WorkspaceCrear | WorkspaceActualizar) => {
    if (workspaceEditando) {
      // Modo edición
      await actualizarWorkspace(workspaceEditando.id, data as WorkspaceActualizar)
    } else {
      // Modo creación
      await crearWorkspace(data as WorkspaceCrear)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Workspaces
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Organiza tus expedientes en espacios de trabajo personalizados
          </p>
        </div>

        <Button onClick={handleCrearNuevo} disabled={isLoading}>
          <Plus className="h-4 w-4 mr-2" />
          Nuevo Workspace
        </Button>
      </div>

      {/* Estadísticas */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Total Workspaces
              </p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
                {workspaces.length}
              </p>
            </div>
            <FolderOpen className="h-10 w-10 text-blue-600 dark:text-blue-400" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Total Expedientes
              </p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
                {workspaces.reduce((sum, w) => sum + w.expedientes_count, 0)}
              </p>
            </div>
            <div className="h-10 w-10 bg-green-100 dark:bg-green-900/20 rounded-full flex items-center justify-center">
              <span className="text-green-600 dark:text-green-400 font-bold">
                {workspaces.reduce((sum, w) => sum + w.expedientes_count, 0)}
              </span>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Promedio por Workspace
              </p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
                {workspaces.length > 0
                  ? Math.round(
                      workspaces.reduce((sum, w) => sum + w.expedientes_count, 0) /
                        workspaces.length
                    )
                  : 0}
              </p>
            </div>
            <div className="h-10 w-10 bg-purple-100 dark:bg-purple-900/20 rounded-full flex items-center justify-center">
              <span className="text-purple-600 dark:text-purple-400 font-bold">
                Ø
              </span>
            </div>
          </div>
        </Card>
      </div>

      {/* Loading State */}
      {isLoading && workspaces.length === 0 && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          <span className="ml-3 text-gray-600 dark:text-gray-400">
            Cargando workspaces...
          </span>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && workspaces.length === 0 && (
        <Card className="p-12">
          <div className="text-center">
            <FolderOpen className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              No tienes workspaces todavía
            </h3>
            <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto mb-6">
              Los workspaces te permiten organizar expedientes por carpetas, proyectos o
              cualquier criterio que necesites. ¡Crea tu primer workspace!
            </p>
            <Button onClick={handleCrearNuevo}>
              <Plus className="h-4 w-4 mr-2" />
              Crear Primer Workspace
            </Button>
          </div>
        </Card>
      )}

      {/* Grid de Workspaces */}
      {!isLoading && workspaces.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {workspaces.map(workspace => (
            <WorkspaceCard
              key={workspace.id}
              workspace={workspace}
              onEdit={handleEditar}
              onDelete={handleEliminar}
              onViewDetails={handleVerDetalles}
            />
          ))}
        </div>
      )}

      {/* Dialog de Crear/Editar */}
      <CreateWorkspaceDialog
        isOpen={showDialog}
        onClose={() => {
          setShowDialog(false)
          setWorkspaceEditando(null)
        }}
        onSubmit={handleSubmit}
        workspace={workspaceEditando}
      />
    </div>
  )
}
