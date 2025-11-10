/**
 * EmptyState - Componente para mostrar estados vacíos
 * Muestra un mensaje cuando no hay datos disponibles
 */

import React from 'react'
import { LucideIcon } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

export interface EmptyStateProps {
  icon?: LucideIcon
  emoji?: string
  title: string
  description: string
  action?: {
    label: string
    onClick: () => void
    icon?: LucideIcon
  }
  secondaryAction?: {
    label: string
    onClick: () => void
    icon?: LucideIcon
  }
  variant?: 'default' | 'card'
}

export function EmptyState({
  icon: Icon,
  emoji,
  title,
  description,
  action,
  secondaryAction,
  variant = 'default',
}: EmptyStateProps) {
  const content = (
    <div className="text-center py-12 px-4">
      {/* Icon or Emoji */}
      {Icon ? (
        <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-gray-100 dark:bg-gray-800 mb-6">
          <Icon className="h-8 w-8 text-gray-400 dark:text-gray-500" />
        </div>
      ) : emoji ? (
        <div className="text-6xl mb-6">{emoji}</div>
      ) : null}

      {/* Title */}
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
        {title}
      </h3>

      {/* Description */}
      <p className="text-gray-600 dark:text-gray-400 mb-6 max-w-md mx-auto">
        {description}
      </p>

      {/* Actions */}
      {(action || secondaryAction) && (
        <div className="flex gap-3 justify-center">
          {action && (
            <Button onClick={action.onClick} className="gap-2">
              {action.icon && <action.icon className="h-4 w-4" />}
              {action.label}
            </Button>
          )}
          {secondaryAction && (
            <Button onClick={secondaryAction.onClick} variant="outline" className="gap-2">
              {secondaryAction.icon && <secondaryAction.icon className="h-4 w-4" />}
              {secondaryAction.label}
            </Button>
          )}
        </div>
      )}
    </div>
  )

  if (variant === 'card') {
    return <Card>{content}</Card>
  }

  return content
}

// Variantes predefinidas para casos comunes
export function EmptyExpedientes({ onExtraer }: { onExtraer: () => void }) {
  return (
    <EmptyState
      emoji="📋"
      title="No hay expedientes"
      description="Comienza extrayendo expedientes del Portal Judicial Nacional"
      variant="card"
      action={{
        label: 'Extraer Primer Expediente',
        onClick: onExtraer,
      }}
    />
  )
}

export function EmptyWorkspaces({ onCreate }: { onCreate: () => void }) {
  return (
    <EmptyState
      emoji="📁"
      title="No hay workspaces"
      description="Crea tu primer workspace para organizar tus expedientes por grupos"
      variant="card"
      action={{
        label: 'Crear Workspace',
        onClick: onCreate,
      }}
    />
  )
}

export function EmptyMonitoreo({ onAgregar }: { onAgregar: () => void }) {
  return (
    <EmptyState
      emoji="🔔"
      title="No hay expedientes en monitoreo"
      description="Agrega expedientes al monitoreo para recibir alertas de cambios automáticamente"
      variant="card"
      action={{
        label: 'Ir a Expedientes',
        onClick: onAgregar,
      }}
    />
  )
}

export function EmptyCambios() {
  return (
    <EmptyState
      emoji="✅"
      title="No hay cambios detectados"
      description="Cuando el sistema detecte cambios en los expedientes monitoreados, aparecerán aquí"
      variant="card"
    />
  )
}

export function EmptySearch({ query, onClear }: { query: string; onClear: () => void }) {
  return (
    <EmptyState
      emoji="🔍"
      title="No se encontraron resultados"
      description={`No se encontraron expedientes que coincidan con "${query}"`}
      variant="card"
      action={{
        label: 'Limpiar búsqueda',
        onClick: onClear,
      }}
    />
  )
}

export function EmptyWithImage({
  imageSrc,
  title,
  description,
  action,
}: {
  imageSrc: string
  title: string
  description: string
  action?: EmptyStateProps['action']
}) {
  return (
    <div className="text-center py-12 px-4">
      <img
        src={imageSrc}
        alt={title}
        className="mx-auto h-48 w-48 mb-6 opacity-50"
      />
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
        {title}
      </h3>
      <p className="text-gray-600 dark:text-gray-400 mb-6 max-w-md mx-auto">
        {description}
      </p>
      {action && (
        <Button onClick={action.onClick} className="gap-2">
          {action.icon && <action.icon className="h-4 w-4" />}
          {action.label}
        </Button>
      )}
    </div>
  )
}
