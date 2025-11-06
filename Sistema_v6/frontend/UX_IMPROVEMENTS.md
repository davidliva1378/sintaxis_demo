# Mejoras de UX - Sistema PJN v6 Frontend

**Fecha**: 2025-11-05
**Versión**: 1.0.0

Este documento describe las mejoras de experiencia de usuario (UX) implementadas en el frontend del Sistema PJN v6.

---

## 📋 Tabla de Contenidos

1. [Loading States](#loading-states)
2. [Error Handling](#error-handling)
3. [Empty States](#empty-states)
4. [Animaciones](#animaciones)
5. [Toast Notifications](#toast-notifications)
6. [Guía de Uso](#guía-de-uso)

---

## 🔄 Loading States

### Componentes Disponibles

#### `LoadingSpinner`

Spinner de carga versátil con múltiples tamaños y variantes.

```tsx
import { LoadingSpinner } from '@/components/common'

// Básico
<LoadingSpinner />

// Con tamaño y variante
<LoadingSpinner size="lg" variant="primary" text="Cargando datos..." />

// Fullscreen
<LoadingSpinner size="xl" variant="primary" text="Procesando..." fullscreen />
```

**Props**:
- `size`: `'sm' | 'md' | 'lg' | 'xl'` (default: `'md'`)
- `variant`: `'default' | 'primary' | 'secondary'` (default: `'default'`)
- `text`: Texto opcional debajo del spinner
- `fullscreen`: Mostrar en pantalla completa con backdrop
- `className`: Clases CSS adicionales

#### Variantes Predefinidas

```tsx
import { PageLoader, InlineLoader, FullPageLoader, ButtonLoader } from '@/components/common'

// Para páginas completas
<PageLoader text="Cargando expedientes..." />

// Inline (dentro de texto o componentes)
<InlineLoader text="Procesando..." />

// Fullscreen overlay
<FullPageLoader text="Extrayendo expediente del PJN..." />

// Dentro de botones
<Button disabled>
  <ButtonLoader />
  Guardando...
</Button>
```

#### `LoadingDots`

Alternativa animada con puntos.

```tsx
import { LoadingDots } from '@/components/common'

<LoadingDots />
```

#### `LoadingBar`

Barra de progreso lineal.

```tsx
import { LoadingBar } from '@/components/common'

// Sin progreso específico (animación continua)
<LoadingBar />

// Con progreso
<LoadingBar progress={75} />
```

### Skeleton Loaders

Componente para mostrar placeholders mientras carga contenido.

```tsx
import { Skeleton, SkeletonCard, SkeletonExpediente, SkeletonWorkspace, SkeletonTable, SkeletonStats, SkeletonList } from '@/components/ui/skeleton'

// Básico
<Skeleton className="h-4 w-full" />

// Cards predefinidos
<SkeletonExpediente />
<SkeletonWorkspace />
<SkeletonTable />
<SkeletonStats />
<SkeletonList count={5} />
```

**Skeletons disponibles**:
- `Skeleton` - Base genérico
- `SkeletonCard` - Card genérico
- `SkeletonExpediente` - Para ExpedienteCard
- `SkeletonWorkspace` - Para WorkspaceCard
- `SkeletonTable` - Para tablas
- `SkeletonStats` - Grid de 4 estadísticas
- `SkeletonList` - Lista de items

---

## 🛡️ Error Handling

### ErrorBoundary

Componente de clase para capturar errores de React y mostrar UI amigable.

```tsx
import { ErrorBoundary } from '@/components/common'

// Envolver componentes que puedan fallar
<ErrorBoundary>
  <MyComponent />
</ErrorBoundary>

// Con fallback personalizado
<ErrorBoundary fallback={<CustomErrorUI />}>
  <MyComponent />
</ErrorBoundary>

// HOC wrapper
import { withErrorBoundary } from '@/components/common'

const SafeComponent = withErrorBoundary(MyComponent)
```

**Características**:
- Captura errores de React en componentes hijos
- Muestra UI amigable con opciones de recuperación
- En desarrollo, muestra detalles del error
- Permite reintentar o volver al inicio
- Preparado para integración con servicios de logging (Sentry, LogRocket)

**Implementación**:
- Ya está envolviendo toda la app en `App.tsx`
- Los errores se loguean en consola en desarrollo
- En producción muestra mensaje genérico sin detalles técnicos

---

## 📭 Empty States

### EmptyState

Componente versátil para mostrar estados vacíos.

```tsx
import { EmptyState } from '@/components/common'

<EmptyState
  icon={FileText}
  title="No hay datos"
  description="No se encontraron registros en el sistema"
  action={{
    label: 'Agregar nuevo',
    onClick: handleAdd,
    icon: Plus,
  }}
  secondaryAction={{
    label: 'Limpiar filtros',
    onClick: handleClear,
  }}
  variant="card" // o "default"
/>
```

**Props**:
- `icon`: Componente de icono (Lucide)
- `emoji`: Emoji alternativo al icono
- `title`: Título del mensaje
- `description`: Descripción detallada
- `action`: Acción principal con label, onClick, icon (opcional)
- `secondaryAction`: Acción secundaria
- `variant`: `'default' | 'card'`

### Variantes Predefinidas

```tsx
import {
  EmptyExpedientes,
  EmptyWorkspaces,
  EmptyMonitoreo,
  EmptyCambios,
  EmptySearch,
} from '@/components/common'

// Expedientes vacíos
<EmptyExpedientes onExtraer={() => setShowDialog(true)} />

// Workspaces vacíos
<EmptyWorkspaces onCreate={() => setShowCreateDialog(true)} />

// Monitoreo vacío
<EmptyMonitoreo onAgregar={() => navigate('/expedientes')} />

// Sin cambios detectados
<EmptyCambios />

// Sin resultados de búsqueda
<EmptySearch query="ABC123" onClear={clearFilters} />
```

---

## ✨ Animaciones

### Clases CSS Personalizadas

Animaciones predefinidas disponibles vía Tailwind:

```tsx
// Fade in con slide up
<div className="animate-fade-in-up">Contenido</div>

// Slide desde la izquierda
<div className="animate-slide-in-left">Contenido</div>

// Slide desde la derecha
<div className="animate-slide-in-right">Contenido</div>

// Scale in
<div className="animate-scale-in">Contenido</div>

// Shimmer effect (para skeletons)
<div className="animate-shimmer">Cargando...</div>

// Bounce suave
<div className="animate-soft-bounce">Indicador</div>

// Scale pulse
<div className="animate-scale-pulse">Pulsante</div>

// Transición suave
<button className="transition-smooth hover:scale-105">Botón</button>
```

### Utilidades Adicionales

```tsx
// Gradiente de texto
<h1 className="text-gradient">Título con gradiente</h1>

// Sombras suaves
<div className="shadow-soft dark:shadow-soft-dark">Card</div>

// Backdrop blur
<div className="backdrop-blur-custom">Overlay</div>
```

### Accesibilidad

Las animaciones respetan `prefers-reduced-motion`:

```css
@media (prefers-reduced-motion: reduce) {
  /* Las animaciones se reducen a 0.01ms */
}
```

---

## 🔔 Toast Notifications

### Toast Utility

Wrapper mejorado alrededor de `sonner` para mensajes consistentes.

```tsx
import { toast } from '@/lib/toast'

// Mensajes genéricos
toast.success('Operación exitosa', 'Todo salió bien')
toast.error('Error al procesar', 'Intenta nuevamente')
toast.warning('Advertencia', 'Revisa los datos')
toast.info('Información', 'Dato relevante')
toast.loading('Procesando...') // retorna ID

// CRUD operations
toast.created('Expediente', 'ABC123/2024')
toast.updated('Workspace', 'Mi Workspace')
toast.deleted('Monitoreo', 'XYZ456/2024')

// Autenticación
toast.auth.loginSuccess('admin')
toast.auth.logoutSuccess()
toast.auth.registerSuccess()
toast.auth.passwordChanged()
toast.auth.credentialsUpdated()
toast.auth.credentialsDeleted()

// Expedientes
const loadingId = toast.expediente.extracting('ABC123/2024')
toast.dismiss(loadingId)
toast.expediente.extracted('ABC123/2024')
toast.expediente.notFound('ABC123/2024')

// Workspaces
toast.workspace.created('Mi Workspace')
toast.workspace.updated('Mi Workspace')
toast.workspace.deleted('Mi Workspace')
toast.workspace.expedienteAdded('ABC123/2024', 'Mi Workspace')
toast.workspace.expedienteRemoved('ABC123/2024')

// Monitoreo
toast.monitoreo.started('ABC123/2024')
toast.monitoreo.stopped('ABC123/2024')
toast.monitoreo.paused('ABC123/2024')
toast.monitoreo.resumed('ABC123/2024')
toast.monitoreo.cambioDetectado('ABC123/2024', 'Nueva actuación')
toast.monitoreo.verified('ABC123/2024')
toast.monitoreo.configUpdated()

// Promise-based
await toast.promise(
  fetchData(),
  {
    loading: 'Cargando datos...',
    success: 'Datos cargados correctamente',
    error: 'Error al cargar datos',
  }
)

// Dismiss
toast.dismiss() // todos
toast.dismiss(toastId) // específico
```

---

## 📖 Guía de Uso

### Cuándo usar cada componente

#### Loading States

| Situación | Componente |
|-----------|-----------|
| Cargando página completa | `<PageLoader />` |
| Operación fullscreen (extracción PJN) | `<FullPageLoader />` |
| Cargando lista/grid | `<SkeletonExpediente />` / `<SkeletonList />` |
| Botón en estado loading | `<ButtonLoader />` |
| Inline text loading | `<InlineLoader />` |
| Progreso de upload/download | `<LoadingBar progress={X} />` |

#### Error Handling

| Situación | Solución |
|-----------|----------|
| Error de componente React | Envuelto automático con `<ErrorBoundary>` |
| Error de API | `toast.error()` + estado de error en UI |
| Error de validación | Mostrar en formulario + `toast.error()` |

#### Empty States

| Situación | Componente |
|-----------|-----------|
| Sin expedientes | `<EmptyExpedientes />` |
| Sin workspaces | `<EmptyWorkspaces />` |
| Sin monitoreo | `<EmptyMonitoreo />` |
| Sin cambios detectados | `<EmptyCambios />` |
| Búsqueda sin resultados | `<EmptySearch />` |
| Otro caso | `<EmptyState />` personalizado |

#### Animaciones

| Situación | Clase CSS |
|-----------|-----------|
| Entrada de página/modal | `animate-fade-in-up` |
| Entrada de sidebar | `animate-slide-in-left` |
| Entrada de panel lateral | `animate-slide-in-right` |
| Entrada de modal/dialog | `animate-scale-in` |
| Card/botón hover | `transition-smooth hover:scale-105` |
| Skeleton loading | `animate-pulse` + `animate-shimmer` |

### Ejemplos Completos

#### Página con Loading y Empty States

```tsx
function ExpedientesPage() {
  const { expedientes, isLoading } = useExpedientesStore()

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {[...Array(6)].map((_, i) => (
          <SkeletonExpediente key={i} />
        ))}
      </div>
    )
  }

  if (expedientes.length === 0) {
    return <EmptyExpedientes onExtraer={() => setShowDialog(true)} />
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 animate-fade-in-up">
      {expedientes.map((exp) => (
        <ExpedienteCard key={exp.numero} expediente={exp} />
      ))}
    </div>
  )
}
```

#### Formulario con Toast

```tsx
async function handleSubmit(data: FormData) {
  const loadingId = toast.loading('Guardando cambios...')

  try {
    await updateProfile(data)
    toast.dismiss(loadingId)
    toast.success('Perfil actualizado', 'Tus cambios se guardaron correctamente')
  } catch (error) {
    toast.dismiss(loadingId)
    toast.error('Error al actualizar', error.message)
  }
}
```

#### Botón con Loading State

```tsx
<Button
  onClick={handleExtract}
  disabled={isExtracting}
>
  {isExtracting ? (
    <>
      <ButtonLoader />
      Extrayendo...
    </>
  ) : (
    <>
      <Download className="h-4 w-4 mr-2" />
      Extraer Expediente
    </>
  )}
</Button>
```

---

## 🎨 Mejores Prácticas

1. **Siempre mostrar feedback visual** para operaciones asíncronas
2. **Usar skeleton loaders** en lugar de spinners cuando sea posible (mejor UX)
3. **Toast para confirmaciones** de acciones importantes
4. **Empty states con CTAs claros** para guiar al usuario
5. **Animaciones sutiles** - no abusar para evitar mareos
6. **Respetar prefers-reduced-motion** para accesibilidad
7. **Error boundaries** para evitar que la app se rompa completamente
8. **Mensajes de error claros** que expliquen qué pasó y qué hacer

---

## 📝 Próximas Mejoras

- [ ] Progress indicators para operaciones largas
- [ ] Optimistic UI updates
- [ ] Offline mode indicators
- [ ] Undo/Redo para acciones destructivas
- [ ] Keyboard shortcuts hints
- [ ] Tour guiado para nuevos usuarios

---

**Última actualización**: 2025-11-05
**Mantenedor**: Sistema PJN v6 Team
