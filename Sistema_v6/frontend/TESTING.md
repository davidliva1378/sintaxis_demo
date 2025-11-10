# Testing - Sistema PJN v6 Frontend

**Fecha**: 2025-11-05
**Versión**: 1.0.0

Este documento describe la estrategia de testing, herramientas y cómo ejecutar los tests del frontend.

---

## 📋 Tabla de Contenidos

1. [Stack de Testing](#stack-de-testing)
2. [Estructura de Tests](#estructura-de-tests)
3. [Ejecutar Tests](#ejecutar-tests)
4. [Escribir Tests](#escribir-tests)
5. [Coverage](#coverage)
6. [Mejores Prácticas](#mejores-prácticas)

---

## 🛠️ Stack de Testing

### Herramientas

- **Vitest** - Test runner (compatible con Jest API)
- **React Testing Library** - Testing de componentes React
- **jsdom** - Simulación de DOM en Node.js
- **@testing-library/jest-dom** - Matchers personalizados
- **vi (Vitest)** - Mocking y spies

### ¿Por qué Vitest?

- ⚡ **Rápido** - Más rápido que Jest
- 🔄 **Hot Module Replacement** - Tests se re-ejecutan automáticamente
- 📦 **Compatible con Vite** - Usa la misma configuración
- ✅ **Compatible con Jest** - API similar, fácil migración
- 🎯 **ESM First** - Soporte nativo para ES Modules

---

## 📁 Estructura de Tests

```
frontend/src/
├── test/
│   ├── setup.ts           # Configuración global de tests
│   └── utils.tsx          # Utilidades de testing
├── components/
│   ├── ui/
│   │   └── __tests__/
│   │       └── button.test.tsx
│   ├── common/
│   │   └── __tests__/
│   │       ├── EmptyState.test.tsx
│   │       └── LoadingSpinner.test.tsx
│   └── layout/
│       └── __tests__/
│           └── ProtectedRoute.test.tsx
├── stores/
│   └── __tests__/
│       ├── authStore.test.ts
│       └── themeStore.test.ts
└── lib/
    └── __tests__/
        ├── encryption.test.ts
        └── toast.test.ts
```

### Convenciones de Naming

- Tests en carpeta `__tests__/` junto al código
- Archivos de test: `*.test.ts` o `*.test.tsx`
- Un archivo de test por componente/módulo
- Nombres descriptivos en español

---

## 🚀 Ejecutar Tests

### Comandos Básicos

```bash
# Ejecutar todos los tests
npm test

# Ejecutar tests en modo watch (recomendado para desarrollo)
npm test -- --watch

# Ejecutar tests con UI interactiva
npm test -- --ui

# Ejecutar tests de un archivo específico
npm test -- button.test.tsx

# Ejecutar tests que coincidan con un patrón
npm test -- EmptyState
```

### Coverage

```bash
# Generar reporte de coverage
npm run test:coverage

# Ver reporte en navegador
open coverage/index.html
```

### CI/CD

```bash
# Ejecutar tests en modo CI (sin watch, con coverage)
npm run test:ci
```

---

## ✍️ Escribir Tests

### Estructura Básica

```tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MyComponent } from '../MyComponent'

describe('MyComponent', () => {
  beforeEach(() => {
    // Setup antes de cada test
    vi.clearAllMocks()
  })

  it('renderiza correctamente', () => {
    render(<MyComponent />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })

  it('llama onClick cuando se hace click', () => {
    const handleClick = vi.fn()
    render(<MyComponent onClick={handleClick} />)

    fireEvent.click(screen.getByRole('button'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })
})
```

### Testing de Componentes

#### Renderizar componente simple

```tsx
import { render, screen } from '@testing-library/react'

it('renderiza texto', () => {
  render(<Button>Click me</Button>)
  expect(screen.getByText('Click me')).toBeInTheDocument()
})
```

#### Renderizar con Router

```tsx
import { renderWithRouter } from '@/test/utils'

it('renderiza con router', () => {
  renderWithRouter(<MyComponent />)
  // ...
})
```

#### Interacciones de usuario

```tsx
import { fireEvent } from '@testing-library/react'

it('maneja click', () => {
  const handleClick = vi.fn()
  render(<Button onClick={handleClick}>Click</Button>)

  fireEvent.click(screen.getByRole('button'))
  expect(handleClick).toHaveBeenCalled()
})
```

#### Queries comunes

```tsx
// Por texto
screen.getByText('Hello')

// Por rol
screen.getByRole('button')
screen.getByRole('textbox')

// Por label
screen.getByLabelText('Username')

// Por placeholder
screen.getByPlaceholderText('Enter username')

// Por test ID
screen.getByTestId('submit-button')

// Queries async
await screen.findByText('Loaded!')

// Query que no falla si no existe
screen.queryByText('Optional text')
```

### Testing de Stores (Zustand)

```tsx
import { useMyStore } from '../myStore'

describe('myStore', () => {
  beforeEach(() => {
    // Reset store
    useMyStore.setState({ count: 0 })
  })

  it('incrementa contador', () => {
    const { increment } = useMyStore.getState()

    increment()

    expect(useMyStore.getState().count).toBe(1)
  })
})
```

### Mocking

#### Mock de funciones

```tsx
const mockFn = vi.fn()
mockFn.mockReturnValue('value')
mockFn.mockResolvedValue(Promise.resolve('async value'))

expect(mockFn).toHaveBeenCalled()
expect(mockFn).toHaveBeenCalledWith('arg1', 'arg2')
expect(mockFn).toHaveBeenCalledTimes(2)
```

#### Mock de módulos

```tsx
vi.mock('@/lib/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))
```

#### Mock de toast

```tsx
import { mockToast } from '@/test/utils'

// En el test
expect(mockToast.success).toHaveBeenCalledWith(
  'Operación exitosa',
  expect.any(Object)
)
```

### Testing de Async

```tsx
import { waitFor } from '@testing-library/react'

it('carga datos async', async () => {
  render(<MyComponent />)

  // Esperar a que aparezca elemento
  await waitFor(() => {
    expect(screen.getByText('Loaded')).toBeInTheDocument()
  })
})
```

---

## 📊 Coverage

### Objetivos de Coverage

| Categoría | Objetivo |
|-----------|----------|
| Statements | > 80% |
| Branches | > 75% |
| Functions | > 80% |
| Lines | > 80% |

### Archivos Excluidos

- `node_modules/`
- `src/test/`
- `**/*.d.ts`
- `**/*.config.*`
- `**/mockData`
- `dist/`

### Generar Reporte

```bash
npm run test:coverage
```

El reporte se genera en `coverage/`:
- `coverage/index.html` - Reporte visual
- `coverage/lcov.info` - Para CI/CD

---

## ✅ Mejores Prácticas

### 1. Nombrar Tests Descriptivamente

```tsx
// ❌ Malo
it('works', () => {})

// ✅ Bueno
it('renderiza botón con texto correcto', () => {})
it('llama onClick cuando se hace click', () => {})
it('muestra mensaje de error cuando falla validación', () => {})
```

### 2. Arrange, Act, Assert (AAA)

```tsx
it('incrementa contador', () => {
  // Arrange - Preparar
  const { increment } = useCounterStore.getState()

  // Act - Ejecutar
  increment()

  // Assert - Verificar
  expect(useCounterStore.getState().count).toBe(1)
})
```

### 3. Un Assert por Test (cuando sea posible)

```tsx
// ❌ Malo - Múltiples asserts no relacionados
it('hace todo', () => {
  expect(user.name).toBe('John')
  expect(user.email).toBe('john@example.com')
  expect(user.age).toBe(30)
})

// ✅ Bueno - Un concepto por test
it('tiene nombre correcto', () => {
  expect(user.name).toBe('John')
})

it('tiene email correcto', () => {
  expect(user.email).toBe('john@example.com')
})
```

### 4. Cleanup Después de Cada Test

```tsx
beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
  useAuthStore.setState({ user: null, token: null })
})
```

### 5. Usar Queries Semánticas

```tsx
// ❌ Malo
screen.getByTestId('submit-btn')

// ✅ Bueno
screen.getByRole('button', { name: /submit/i })
```

### 6. Testing de Accesibilidad

```tsx
// Verificar roles ARIA
expect(screen.getByRole('button')).toBeInTheDocument()

// Verificar labels
expect(screen.getByLabelText('Username')).toBeInTheDocument()

// Verificar alt text en imágenes
expect(screen.getByAltText('User avatar')).toBeInTheDocument()
```

### 7. No Testear Detalles de Implementación

```tsx
// ❌ Malo - Testea implementación interna
expect(component.state.isOpen).toBe(true)

// ✅ Bueno - Testea comportamiento visible
expect(screen.getByText('Modal Content')).toBeVisible()
```

### 8. Mock Solo lo Necesario

```tsx
// ❌ Malo - Mock excesivo
vi.mock('entire-library')

// ✅ Bueno - Mock específico
vi.mock('@/lib/api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: [] }),
  },
}))
```

---

## 🎯 Estrategia de Testing

### Pirámide de Tests

```
        /\
       /E2E\       (Pocos) - Tests de extremo a extremo
      /------\
     /Integr.\    (Algunos) - Tests de integración
    /----------\
   /   Unit     \ (Muchos) - Tests unitarios
  /--------------\
```

### Qué Testear

#### ✅ SÍ Testear

- Componentes UI reutilizables
- Lógica de negocio (stores, utilities)
- Validaciones de formularios
- Flujos críticos (auth, CRUD)
- Edge cases y errores
- Accesibilidad básica

#### ❌ NO Testear

- Librerías de terceros
- Detalles de implementación (CSS, estructura interna)
- Código trivial (getters/setters simples)
- Configuración (vite.config, tailwind.config)

---

## 📚 Recursos

### Documentación

- [Vitest](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [Testing Library Queries](https://testing-library.com/docs/queries/about)
- [jest-dom Matchers](https://github.com/testing-library/jest-dom)

### Guías

- [Common mistakes with React Testing Library](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
- [Testing Implementation Details](https://kentcdodds.com/blog/testing-implementation-details)

---

## 🐛 Troubleshooting

### Error: "Cannot find module '@/...'"

Asegúrate de que `vitest.config.ts` tiene el alias configurado:

```ts
resolve: {
  alias: {
    '@': path.resolve(__dirname, './src'),
  },
}
```

### Tests pasan pero coverage es 0%

Ejecuta con flag de coverage explícito:

```bash
npm test -- --coverage
```

### Error: "window is not defined"

Asegúrate de que `vitest.config.ts` tiene:

```ts
test: {
  environment: 'jsdom',
}
```

### Mock no funciona

Verifica que el mock está antes del import:

```tsx
vi.mock('@/lib/api') // ANTES

import { myFunction } from '@/lib/api' // DESPUÉS
```

---

## 📝 Próximas Mejoras

- [ ] E2E tests con Playwright
- [ ] Visual regression testing
- [ ] Performance testing
- [ ] Aumentar coverage a > 90%
- [ ] Tests de accesibilidad automatizados (axe-core)
- [ ] Snapshot testing para componentes críticos

---

**Última actualización**: 2025-11-05
**Mantenedor**: Sistema PJN v6 Team
