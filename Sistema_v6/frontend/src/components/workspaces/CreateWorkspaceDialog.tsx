/**
 * CreateWorkspaceDialog - Modal para crear o editar un workspace
 */

import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'
import type { Workspace, WorkspaceCrear } from '@/types/workspace'
import { WORKSPACE_COLORS, WORKSPACE_ICONS } from '@/types/workspace'
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

interface CreateWorkspaceDialogProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: WorkspaceCrear) => Promise<void>
  workspace?: Workspace | null // Si está presente, es modo edición
}

// Schema de validación
const workspaceSchema = z.object({
  nombre: z
    .string()
    .min(3, 'El nombre debe tener al menos 3 caracteres')
    .max(50, 'El nombre no puede superar los 50 caracteres'),
  descripcion: z
    .string()
    .max(200, 'La descripción no puede superar los 200 caracteres')
    .optional(),
  color: z.string().optional(),
  icon: z.string().optional(),
})

type WorkspaceForm = z.infer<typeof workspaceSchema>

// Mapeo de iconos string a componentes
const ICON_COMPONENTS: Record<string, React.ComponentType<{ className?: string }>> = {
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

export default function CreateWorkspaceDialog({
  isOpen,
  onClose,
  onSubmit,
  workspace,
}: CreateWorkspaceDialogProps) {
  const isEditMode = !!workspace

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    watch,
    setValue,
    reset,
  } = useForm<WorkspaceForm>({
    resolver: zodResolver(workspaceSchema),
    defaultValues: {
      nombre: '',
      descripcion: '',
      color: '#3b82f6',
      icon: 'folder',
    },
  })

  const colorSeleccionado = watch('color') || '#3b82f6'
  const iconoSeleccionado = watch('icon') || 'folder'

  // Cargar datos del workspace en modo edición
  useEffect(() => {
    if (workspace) {
      reset({
        nombre: workspace.nombre,
        descripcion: workspace.descripcion || '',
        color: workspace.color || '#3b82f6',
        icon: workspace.icon || 'folder',
      })
    } else {
      reset({
        nombre: '',
        descripcion: '',
        color: '#3b82f6',
        icon: 'folder',
      })
    }
  }, [workspace, reset])

  const handleFormSubmit = async (data: WorkspaceForm) => {
    await onSubmit(data as WorkspaceCrear)
    reset()
    onClose()
  }

  const handleClose = () => {
    reset()
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
            {isEditMode ? 'Editar Workspace' : 'Crear Workspace'}
          </h2>
          <button
            onClick={handleClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            disabled={isSubmitting}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Contenido */}
        <form onSubmit={handleSubmit(handleFormSubmit)} className="p-6 space-y-6">
          {/* Nombre */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Nombre *
            </label>
            <Input
              {...register('nombre')}
              placeholder="Ej: Casos Urgentes"
              disabled={isSubmitting}
              className={errors.nombre ? 'border-red-500' : ''}
            />
            {errors.nombre && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                {errors.nombre.message}
              </p>
            )}
          </div>

          {/* Descripción */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Descripción
            </label>
            <textarea
              {...register('descripcion')}
              placeholder="Descripción opcional del workspace..."
              rows={3}
              disabled={isSubmitting}
              className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-100 ${
                errors.descripcion ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {errors.descripcion && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                {errors.descripcion.message}
              </p>
            )}
          </div>

          {/* Color */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Color
            </label>
            <div className="grid grid-cols-9 gap-2">
              {WORKSPACE_COLORS.map(color => (
                <button
                  key={color.value}
                  type="button"
                  onClick={() => setValue('color', color.value)}
                  disabled={isSubmitting}
                  className={`w-10 h-10 rounded-lg transition-all ${
                    colorSeleccionado === color.value
                      ? 'ring-2 ring-offset-2 ring-gray-900 dark:ring-gray-100 scale-110'
                      : 'hover:scale-105'
                  }`}
                  style={{ backgroundColor: color.value }}
                  title={color.label}
                />
              ))}
            </div>
          </div>

          {/* Icono */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Icono
            </label>
            <div className="grid grid-cols-8 gap-2">
              {WORKSPACE_ICONS.map(iconName => {
                const IconComponent = ICON_COMPONENTS[iconName]
                return (
                  <button
                    key={iconName}
                    type="button"
                    onClick={() => setValue('icon', iconName)}
                    disabled={isSubmitting}
                    className={`p-3 rounded-lg border-2 transition-all ${
                      iconoSeleccionado === iconName
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 scale-110'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 hover:scale-105'
                    }`}
                  >
                    <IconComponent className="h-5 w-5 text-gray-700 dark:text-gray-300" />
                  </button>
                )
              })}
            </div>
          </div>

          {/* Vista previa */}
          <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Vista previa
            </label>
            <div
              className="p-4 rounded-lg border-l-4 flex items-center gap-4"
              style={{
                borderLeftColor: colorSeleccionado,
                backgroundColor: `${colorSeleccionado}10`,
              }}
            >
              <div
                className="p-3 rounded-lg"
                style={{ backgroundColor: `${colorSeleccionado}20` }}
              >
                {(() => {
                  const IconComponent = ICON_COMPONENTS[iconoSeleccionado]
                  return (
                    <IconComponent
                      className="h-6 w-6"
                      style={{ color: colorSeleccionado }}
                    />
                  )
                })()}
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                  {watch('nombre') || 'Nombre del workspace'}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {watch('descripcion') || 'Descripción del workspace'}
                </p>
              </div>
            </div>
          </div>

          {/* Botones */}
          <div className="flex gap-3 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={isSubmitting}
              className="flex-1"
            >
              Cancelar
            </Button>
            <Button type="submit" disabled={isSubmitting} className="flex-1">
              {isSubmitting
                ? isEditMode
                  ? 'Guardando...'
                  : 'Creando...'
                : isEditMode
                ? 'Guardar cambios'
                : 'Crear workspace'}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  )
}
