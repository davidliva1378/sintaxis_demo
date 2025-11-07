# Settings Components - Frontend Documentation

> **Guía técnica para desarrolladores sobre los componentes de configuración**

---

## 📋 Tabla de Contenidos

1. [Arquitectura](#arquitectura)
2. [Componentes](#componentes)
3. [Patrones de Desarrollo](#patrones-de-desarrollo)
4. [Agregar Nuevos Componentes](#agregar-nuevos-componentes)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)

---

## Arquitectura

### Estructura de Archivos

```
frontend/src/components/settings/
├── CambiarPassword.tsx              # Cambio de contraseña usuario
├── ConfiguracionAvanzada.tsx        # MCP + Storage (avanzado)
├── ConfiguracionBrowser.tsx         # Configuración del navegador
├── ConfiguracionEnDesarrollo.tsx    # Placeholder futuras configs
├── ConfiguracionMonitoreo.tsx       # Monitoreo (simple/avanzado)
├── ConfiguracionScraping.tsx        # Scraping timeouts y límites
├── CredencialesPJN.tsx              # Credenciales Portal Judicial
├── PerfilUsuario.tsx                # Información personal
├── PreferenciasUsuario.tsx          # Tema, notificaciones, idioma
└── __tests__/                       # Tests de componentes
    ├── ConfiguracionBrowser.test.tsx
    ├── ConfiguracionEnDesarrollo.test.tsx
    └── ConfiguracionMonitoreo.test.tsx
```

---

### Stack Tecnológico

| Tecnología | Propósito |
|------------|-----------|
| **React** | Framework UI |
| **TypeScript** | Type safety |
| **react-hook-form** | Gestión de formularios |
| **zod** | Validación de schemas |
| **Tailwind CSS** | Estilos |
| **lucide-react** | Iconos |
| **sonner** | Toast notifications |
| **vitest** | Testing framework |

---

## Componentes

### 1. ConfiguracionMonitoreo.tsx

Configuración de monitoreo automático con **modo simple/avanzado**.

#### Características

- ✅ Toggle entre modo simple y avanzado
- ✅ Configuración básica: intervalo, días actividad, reintentos
- ✅ Configuración avanzada: horarios laborales, intervalos diferenciados
- ✅ Deshabilita intervalo básico cuando está en modo avanzado
- ✅ Validación completa con zod

#### Schema de Validación

```typescript
const monitoreoSchema = z.object({
  // Modo simple
  intervalo_segundos: z.number().min(0).max(86400),
  dias_actividad: z.number().min(1).max(365),
  max_reintentos: z.number().min(1).max(10),
  notificar_cambios: z.boolean(),
  descargar_archivos: z.boolean(),

  // Modo avanzado (opcional)
  modo_avanzado: z.boolean(),
  intervalos_laboral_expedientes: z.number().min(1).max(1440).optional().nullable(),
  intervalos_laboral_entradas: z.number().min(1).max(1440).optional().nullable(),
  intervalos_no_laboral_expedientes: z.number().min(1).max(1440).optional().nullable(),
  intervalos_no_laboral_entradas: z.number().min(1).max(1440).optional().nullable(),
  dias_laborales: z.array(z.string()).min(1),
  hora_inicio: z.string().regex(/^\d{2}:\d{2}$/),
  hora_fin: z.string().regex(/^\d{2}:\d{2}$/),
})
```

#### Estado

- `isSubmitting`: Loading del submit
- `modoAvanzado`: Estado del toggle modo avanzado
- `isLoading`: Loading inicial de datos

#### API Calls

- **GET** `/api/v1/config/sistema` - Carga configuración actual
- **PUT** `/api/v1/config/sistema` - Guarda cambios

---

### 2. ConfiguracionBrowser.tsx

Configuración del navegador Playwright.

#### Características

- ✅ Toggle modo headless (con/sin interfaz gráfica)
- ✅ Timeouts configurables (general y navegación)
- ✅ User Agent personalizado
- ✅ Información contextual sobre timeouts

#### Schema de Validación

```typescript
const browserSchema = z.object({
  headless: z.boolean(),
  timeout_ms: z.number().min(1000).max(300000),
  navigation_timeout_ms: z.number().min(1000).max(300000),
  user_agent: z.string().nullable().optional(),
})
```

---

### 3. ConfiguracionScraping.tsx

Configuración de extracción de datos.

#### Características

- ✅ 3 tipos de timeouts (default, login, descarga)
- ✅ Límite de páginas con toggle "sin límite"
- ✅ Reintentos de descarga
- ✅ Warning cuando se selecciona "sin límite"

#### Schema de Validación

```typescript
const scrapingSchema = z.object({
  timeout_default: z.number().min(1000).max(300000),
  timeout_login: z.number().min(1000).max(300000),
  timeout_descarga: z.number().min(1000).max(300000),
  max_paginas_expedientes: z.number().min(1).max(10000).nullable().optional(),
  max_reintentos_descarga: z.number().min(1).max(10),
})
```

#### Toggle "Sin Límite"

```typescript
const handleToggleLimite = () => {
  const currentValue = watch('max_paginas_expedientes')
  setValue('max_paginas_expedientes', currentValue === null ? 200 : null, {
    shouldDirty: true,
  })
}
```

---

### 4. ConfiguracionAvanzada.tsx

Configuración de MCP Server y Storage con **secciones colapsables**.

#### Características

- ✅ Sección MCP colapsable
- ✅ Sección Storage colapsable
- ✅ 16 variables de configuración
- ✅ Deshabilita campos cuando MCP está desactivado

#### Secciones

**MCP Server (9 variables):**
- Puerto, mode, workspace, server name
- Features: PDF extraction, full-text search, statistics
- Límites: max_pdf_pages, max_pdf_size_mb

**Storage (7 variables):**
- Paths: base, workspaces, downloads
- Archivos JSON: base, sistema
- Formato: pretty_json, ensure_ascii

---

### 5. ConfiguracionEnDesarrollo.tsx

Placeholder para futuras configuraciones.

#### Características

- ✅ Banner "Sección en construcción"
- ✅ Lista de próximas configuraciones planificadas
- ✅ Información para sugerencias
- ✅ No tiene formulario (solo presentación)

---

## Patrones de Desarrollo

### Patrón de Componente Estándar

Todos los componentes de configuración siguen este patrón:

```typescript
import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Icon, Save } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { toast } from 'sonner'

// 1. Schema de validación con zod
const configSchema = z.object({
  // ... campos
})

type ConfigForm = z.infer<typeof configSchema>

export default function ConfiguracionComponente() {
  // 2. Estados
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  // 3. React Hook Form con zod resolver
  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
    reset,
    setValue,
    watch,
  } = useForm<ConfigForm>({
    resolver: zodResolver(configSchema),
    defaultValues: {
      // ... valores por defecto
    },
  })

  // 4. Cargar configuración al montar
  useEffect(() => {
    const cargarConfiguracion = async () => {
      try {
        const response = await fetch('/api/v1/config/sistema')
        const data = await response.json()

        // Setear valores
        setValue('campo', data.seccion.campo)
        // ...

        setIsLoading(false)
      } catch (error) {
        toast.error('Error al cargar configuración')
        setIsLoading(false)
      }
    }

    cargarConfiguracion()
  }, [setValue])

  // 5. Submit handler
  const onSubmit = async (data: ConfigForm) => {
    setIsSubmitting(true)

    try {
      const response = await fetch('/api/v1/config/sistema', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          seccion: data
        }),
      })

      if (!response.ok) throw new Error('Error al actualizar')

      const result = await response.json()
      toast.success('Configuración actualizada', {
        description: result.message,
      })

      reset(data)
    } catch (error: any) {
      toast.error('Error al actualizar', {
        description: error.message,
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  // 6. Loading state
  if (isLoading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
        </div>
      </Card>
    )
  }

  // 7. Render
  return (
    <Card className="p-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-color-100 dark:bg-color-900/20 rounded-lg">
          <Icon className="h-5 w-5 text-color-600 dark:text-color-400" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Título
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Descripción
          </p>
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Campos del formulario */}

        {/* Botón Submit */}
        <div className="flex justify-end pt-4 border-t">
          <Button type="submit" disabled={!isDirty || isSubmitting}>
            <Save className="h-4 w-4 mr-2" />
            {isSubmitting ? 'Guardando...' : 'Guardar configuración'}
          </Button>
        </div>
      </form>
    </Card>
  )
}
```

---

### Patrón de Campo de Input

```typescript
<div>
  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
    Label del Campo
  </label>
  <input
    {...register('nombre_campo', { valueAsNumber: true })} // Si es number
    type="number"
    min="1"
    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
  />
  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
    Texto de ayuda contextual
  </p>
  {errors.nombre_campo && (
    <p className="mt-1 text-xs text-red-600">{errors.nombre_campo.message}</p>
  )}
</div>
```

---

### Patrón de Checkbox

```typescript
<label className="flex items-center justify-between p-4 rounded-lg border cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800">
  <div>
    <div className="text-sm font-medium text-gray-900 dark:text-white">
      Label
    </div>
    <div className="text-xs text-gray-600 dark:text-gray-400">
      Descripción
    </div>
  </div>
  <input
    {...register('campo')}
    type="checkbox"
    className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
  />
</label>
```

---

## Agregar Nuevos Componentes

### Paso 1: Crear el componente

```bash
cd frontend/src/components/settings/
touch ConfiguracionNueva.tsx
```

### Paso 2: Seguir el patrón estándar

1. Importar dependencias
2. Definir schema de validación con zod
3. Crear tipo desde schema
4. Implementar estados (isSubmitting, isLoading)
5. Configurar react-hook-form
6. useEffect para cargar datos
7. onSubmit handler
8. Render con loading state
9. Form con campos

### Paso 3: Registrar en SettingsPage

```typescript
// pages/settings/SettingsPage.tsx

// 1. Importar componente
import ConfiguracionNueva from '@/components/settings/ConfiguracionNueva'

// 2. Agregar al tipo TabId
type TabId = 'perfil' | 'credenciales' | 'password' | 'preferencias' |
             'monitoreo' | 'browser' | 'scraping' | 'avanzado' | 'desarrollo' |
             'nueva'  // ← NUEVO

// 3. Agregar al array de tabs
const tabs: Tab[] = [
  // ... tabs existentes
  {
    id: 'nueva',
    label: 'Nueva Config',
    icon: IconoNuevo,
    description: 'Descripción breve',
  },
]

// 4. Agregar al render
{tabActiva === 'nueva' && <ConfiguracionNueva />}
```

### Paso 4: Actualizar el backend

Si el componente requiere nuevas variables de configuración:

1. Actualizar `infrastructure/config/settings.py`
2. Agregar nuevos campos a los Settings
3. Actualizar schemas en `presentation/api/rest/schemas/config_schemas.py`
4. Modificar router si es necesario

### Paso 5: Crear tests

```typescript
// __tests__/ConfiguracionNueva.test.tsx

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import ConfiguracionNueva from '../ConfiguracionNueva'

// Mock de fetch
global.fetch = vi.fn()

// Mock de toast
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

describe('ConfiguracionNueva', () => {
  // Tests aquí
})
```

---

## Testing

### Ejecutar Tests

```bash
# Todos los tests de settings
npm test settings

# Test específico
npm test ConfiguracionMonitoreo

# Con UI
npm run test:ui

# Con cobertura
npm run test:coverage
```

### Estructura de Test Típica

```typescript
describe('ConfiguracionComponente', () => {
  const mockConfigData = {
    // ... mock data
  }

  beforeEach(() => {
    vi.clearAllMocks()
    ;(global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockConfigData,
    })
  })

  it('renderiza el componente correctamente', async () => {
    render(<ConfiguracionComponente />)
    await waitFor(() => {
      expect(screen.getByText('Título')).toBeInTheDocument()
    })
  })

  it('carga la configuración actual al montar', async () => {
    render(<ConfiguracionComponente />)
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/v1/config/sistema')
    })
  })

  // ... más tests
})
```

---

## Troubleshooting

### Problema: El formulario no se marca como "dirty"

**Solución:** Usa `setValue` con opción `shouldDirty`:

```typescript
setValue('campo', valor, { shouldDirty: true })
```

---

### Problema: Los checkboxes no funcionan correctamente

**Solución:** No uses `valueAsNumber` en checkboxes:

```typescript
// ❌ Incorrecto
{...register('campo', { valueAsNumber: true })}

// ✅ Correcto
{...register('campo')}
```

---

### Problema: El watch no detecta cambios

**Solución:** Asegúrate de usar `watch` antes del render:

```typescript
const modoAvanzado = watch('modo_avanzado')

// Luego en el render:
{modoAvanzado && <ConfigAvanzada />}
```

---

### Problema: Loading infinito

**Solución:** Siempre llama `setIsLoading(false)` en el finally:

```typescript
useEffect(() => {
  const cargar = async () => {
    try {
      // ...
      setIsLoading(false)
    } catch (error) {
      toast.error('Error')
      setIsLoading(false)  // ← Importante
    }
  }
  cargar()
}, [])
```

---

### Problema: Dark mode no funciona

**Solución:** Siempre incluye clases dark:

```typescript
className="text-gray-900 dark:text-white bg-white dark:bg-gray-800"
```

---

## Convenciones de Código

### Naming

- Componentes: `PascalCase` (ConfiguracionMonitoreo)
- Variables: `camelCase` (isSubmitting, modoAvanzado)
- Constantes: `UPPER_SNAKE_CASE` (API_URL)
- Props: `camelCase`

### Colores

Usa las clases de Tailwind con variantes dark:

```typescript
// Fondos
"bg-gray-50 dark:bg-gray-800"

// Textos
"text-gray-900 dark:text-white"
"text-gray-600 dark:text-gray-400"

// Bordes
"border-gray-200 dark:border-gray-700"

// Acentos
"bg-blue-100 dark:bg-blue-900/20"
"text-blue-600 dark:text-blue-400"
```

---

## Performance

### Optimizaciones Implementadas

1. **Lazy Loading**: Los componentes solo se cargan cuando se accede al tab
2. **Debounce**: No implementado aún, pero considerar para inputs frecuentes
3. **Memoization**: No implementado aún, considerar para cálculos pesados

### Recomendaciones

- No llamar a `setValue` en bucles
- Usar `watch` con cuidado (puede causar re-renders)
- Considerar `useCallback` para handlers complejos

---

## Referencias

- [react-hook-form docs](https://react-hook-form.com/)
- [zod docs](https://zod.dev/)
- [Tailwind CSS docs](https://tailwindcss.com/)
- [lucide-react icons](https://lucide.dev/)
- [vitest docs](https://vitest.dev/)

---

**Versión:** 6.0.0
**Última actualización:** 2025-11-06
**Mantenedor:** Sistema sintaXis
