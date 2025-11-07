/**
 * Common components - Barrel export
 * Exporta todos los componentes comunes para facilitar imports
 */

export { ErrorBoundary, withErrorBoundary } from './ErrorBoundary'
export { EmptyState, EmptyExpedientes, EmptyWorkspaces, EmptyMonitoreo, EmptyCambios, EmptySearch, EmptyWithImage } from './EmptyState'
export { LoadingSpinner, PageLoader, InlineLoader, FullPageLoader, ButtonLoader, LoadingDots, LoadingBar, SkeletonText } from './LoadingSpinner'
export type { EmptyStateProps } from './EmptyState'
export type { LoadingSpinnerProps } from './LoadingSpinner'
