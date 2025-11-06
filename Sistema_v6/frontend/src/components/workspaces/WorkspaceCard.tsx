/**
 * WorkspaceCard - Card para mostrar un workspace en el listado
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { formatDistanceToNow } from 'date-fns'
import { es } from 'date-fns/locale'
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
  MoreVertical,
  Edit2,
  Trash2,
  FolderInput,
} from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import type { Workspace } from '@/types/workspace'

interface WorkspaceCardProps {
  workspace: Workspace
  onEdit: (workspace: Workspace) => void
  onDelete: (id: number) => void
  onViewDetails: (id: number) => void
}

// Mapeo de iconos string a componentes
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

export default function WorkspaceCard({
  workspace,
  onEdit,
  onDelete,
  onViewDetails,
}: WorkspaceCardProps) {
  const [showMenu, setShowMenu] = useState(false)
  const navigate = useNavigate()

  // Obtener componente de icono
  const IconComponent = workspace.icon ? ICON_MAP[workspace.icon] || Folder : Folder

  // Formatear fecha de última actualización
  const fechaRelativa = formatDistanceToNow(new Date(workspace.updated_at), {
    addSuffix: true,
    locale: es,
  })

  const handleCardClick = () => {
    onViewDetails(workspace.id)
  }

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation()
    setShowMenu(false)
    onEdit(workspace)
  }

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation()
    setShowMenu(false)
    if (
      confirm(
        `¿Estás seguro de eliminar el workspace "${workspace.nombre}"?\n\nLos expedientes no se eliminarán, solo se removerá su asociación con este workspace.`
      )
    ) {
      onDelete(workspace.id)
    }
  }

  return (
    <Card
      className="p-6 hover:shadow-lg transition-all duration-200 cursor-pointer border-l-4 group relative"
      style={{ borderLeftColor: workspace.color || '#3b82f6' }}
      onClick={handleCardClick}
    >
      {/* Botón menú */}
      <div className="absolute top-4 right-4">
        <div className="relative">
          <Button
            variant="ghost"
            size="sm"
            className="opacity-0 group-hover:opacity-100 transition-opacity"
            onClick={e => {
              e.stopPropagation()
              setShowMenu(!showMenu)
            }}
          >
            <MoreVertical className="h-4 w-4" />
          </Button>

          {/* Menú dropdown */}
          {showMenu && (
            <>
              {/* Backdrop para cerrar el menú */}
              <div
                className="fixed inset-0 z-10"
                onClick={e => {
                  e.stopPropagation()
                  setShowMenu(false)
                }}
              />
              {/* Menú */}
              <div className="absolute right-0 top-8 z-20 w-48 bg-white dark:bg-gray-800 rounded-md shadow-lg border border-gray-200 dark:border-gray-700 py-1">
                <button
                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
                  onClick={handleEdit}
                >
                  <Edit2 className="h-4 w-4" />
                  Editar
                </button>
                <button
                  className="w-full px-4 py-2 text-left text-sm hover:bg-red-50 dark:hover:bg-red-900/20 text-red-600 dark:text-red-400 flex items-center gap-2"
                  onClick={handleDelete}
                >
                  <Trash2 className="h-4 w-4" />
                  Eliminar
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Header con icono y nombre */}
      <div className="flex items-start gap-4 mb-3">
        <div
          className="p-3 rounded-lg"
          style={{ backgroundColor: `${workspace.color}20` }}
        >
          <IconComponent
            className="h-6 w-6"
            style={{ color: workspace.color || '#3b82f6' }}
          />
        </div>

        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 truncate">
            {workspace.nombre}
          </h3>
          {workspace.descripcion && (
            <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 mt-1">
              {workspace.descripcion}
            </p>
          )}
        </div>
      </div>

      {/* Estadísticas */}
      <div className="flex items-center gap-4 mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <FolderInput className="h-4 w-4 text-gray-500 dark:text-gray-400" />
          <span className="text-sm text-gray-700 dark:text-gray-300">
            <span className="font-semibold">{workspace.expedientes_count}</span>{' '}
            {workspace.expedientes_count === 1 ? 'expediente' : 'expedientes'}
          </span>
        </div>

        <div className="ml-auto">
          <span className="text-xs text-gray-500 dark:text-gray-400">
            Actualizado {fechaRelativa}
          </span>
        </div>
      </div>

      {/* Botón de acción */}
      <div className="mt-4">
        <Button
          variant="outline"
          size="sm"
          className="w-full"
          onClick={handleCardClick}
        >
          Ver expedientes
        </Button>
      </div>
    </Card>
  )
}
