/**
 * LoadingSpinner - Componente de spinner de carga
 * Muestra diferentes tipos de indicadores de carga
 */

import { Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl'
  variant?: 'default' | 'primary' | 'secondary'
  text?: string
  fullscreen?: boolean
  className?: string
}

const sizeClasses = {
  sm: 'h-4 w-4',
  md: 'h-6 w-6',
  lg: 'h-8 w-8',
  xl: 'h-12 w-12',
}

const variantClasses = {
  default: 'text-gray-400',
  primary: 'text-blue-600',
  secondary: 'text-purple-600',
}

export function LoadingSpinner({
  size = 'md',
  variant = 'default',
  text,
  fullscreen = false,
  className,
}: LoadingSpinnerProps) {
  const spinner = (
    <div className={cn('flex flex-col items-center justify-center gap-3', className)}>
      <Loader2
        className={cn(
          'animate-spin',
          sizeClasses[size],
          variantClasses[variant]
        )}
      />
      {text && (
        <p className="text-sm text-gray-600 dark:text-gray-400 animate-pulse">
          {text}
        </p>
      )}
    </div>
  )

  if (fullscreen) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm z-50">
        {spinner}
      </div>
    )
  }

  return spinner
}

// Variantes específicas para diferentes contextos
export function PageLoader({ text = 'Cargando...' }: { text?: string }) {
  return (
    <div className="flex items-center justify-center py-12">
      <LoadingSpinner size="lg" variant="primary" text={text} />
    </div>
  )
}

export function InlineLoader({ text }: { text?: string }) {
  return (
    <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
      <Loader2 className="h-4 w-4 animate-spin" />
      {text && <span>{text}</span>}
    </div>
  )
}

export function FullPageLoader({ text = 'Cargando...' }: { text?: string }) {
  return <LoadingSpinner size="xl" variant="primary" text={text} fullscreen />
}

export function ButtonLoader() {
  return <Loader2 className="h-4 w-4 animate-spin" />
}

// Spinner dots (alternativa al spinner circular)
export function LoadingDots({ className }: { className?: string }) {
  return (
    <div className={cn('flex items-center justify-center gap-1', className)}>
      <div className="h-2 w-2 rounded-full bg-gray-400 dark:bg-gray-500 animate-bounce [animation-delay:-0.3s]" />
      <div className="h-2 w-2 rounded-full bg-gray-400 dark:bg-gray-500 animate-bounce [animation-delay:-0.15s]" />
      <div className="h-2 w-2 rounded-full bg-gray-400 dark:bg-gray-500 animate-bounce" />
    </div>
  )
}

// Progress bar lineal
export function LoadingBar({ progress }: { progress?: number }) {
  return (
    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
      <div
        className="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-out"
        style={{
          width: progress ? `${progress}%` : '100%',
          animation: progress === undefined ? 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite' : undefined,
        }}
      />
    </div>
  )
}

// Skeleton text loader (alternativa al Skeleton component)
export function SkeletonText({ lines = 3 }: { lines?: number }) {
  return (
    <div className="space-y-2">
      {[...Array(lines)].map((_, i) => (
        <div
          key={i}
          className="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"
          style={{
            width: i === lines - 1 ? '60%' : '100%',
          }}
        />
      ))}
    </div>
  )
}
