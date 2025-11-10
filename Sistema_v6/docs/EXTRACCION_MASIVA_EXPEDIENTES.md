# Extracción Masiva de Expedientes del PJN

## Descripción

Nueva funcionalidad del frontend (Sistema_v6) que permite extraer la totalidad de los expedientes del PJN y seleccionar cuáles serán monitoreados en el sistema mediante filtros avanzados.

## Ubicación

- **Branch**: `claude/v6-testing-frontend-expedient-011CUrB9GyTPg5JcaSxNjv1o`
- **Componente Principal**: `Sistema_v6/frontend/src/components/expedientes/ExtraccionMasivaDialog.tsx`
- **Integración**: `Sistema_v6/frontend/src/pages/expedientes/ExpedientesPage.tsx`

## Características Implementadas

### 1. Extracción Automática
- Interfaz en 2 etapas: Extracción y Filtrado/Selección
- Opción de procesamiento con `procesador_pdf` (clasificación y análisis)
- Log de actividad en tiempo real
- Manejo de errores y estados de carga

### 2. Filtros Avanzados

#### Filtros Disponibles:
- **Búsqueda por texto**: Número de expediente o carátula
- **Fuero**: Todos, Federal, Civil, Penal, Laboral, Contencioso Administrativo
- **Situación Procesal**:
  - En trámite
  - Archivado
  - Finalizado

#### Acciones de Selección:
- ✓ Seleccionar todos los expedientes filtrados
- ✗ Deseleccionar todos
- Invertir selección
- Selección individual por checkbox

### 3. Interfaz de Usuario

#### Acceso:
1. **Botón en Header**: "Extracción Masiva" (botón outline con icono de descarga)
2. Ubicado en la página de Expedientes (`/expedientes`)

#### Workflow:

**Etapa 1: Extracción**
1. Configurar opciones:
   - Checkbox para activar procesamiento con `procesador_pdf`
2. Hacer clic en "Iniciar Extracción"
3. Ver progreso en log en tiempo real
4. Esperar a que complete (auto-avanza a Etapa 2)

**Etapa 2: Filtrado y Selección**
1. **Panel Lateral (Filtros)**:
   - Campo de búsqueda
   - Selector de fuero
   - Checkboxes de situación procesal
   - Botón "Limpiar" para resetear filtros

2. **Panel Principal (Tabla)**:
   - Tabla con expedientes filtrados
   - Checkbox en cada fila
   - Botones de selección masiva
   - Stats: Total filtrados vs Seleccionados

3. Confirmar selección

#### Estados Visuales:
- Loading durante extracción
- Tabla responsive con scroll
- Estados hover en filas
- Badges de situación coloreados:
  - Verde: En trámite
  - Gris: Archivado/Finalizado

## Arquitectura Técnica

### Componentes Principales

#### 1. `ExtraccionMasivaDialog`
```typescript
interface ExtraccionMasivaDialogProps {
  onClose: () => void
  onSuccess?: (expedientes: ExpedienteResumen[]) => void
}
```

**Estados Internos**:
- `etapa`: 'extraccion' | 'filtrado'
- `expedientesExtraidos`: Array de todos los expedientes
- `expedientesFiltrados`: Array después de aplicar filtros
- `expedientesSeleccionados`: Set con números seleccionados
- `filtros`: Objeto con criterios de filtrado
- `logMensajes`: Array de mensajes del log

**Funciones Principales**:
- `handleIniciarExtraccion()`: Inicia el proceso de extracción
- `aplicarFiltros()`: Aplica filtros a los expedientes
- `handleToggleExpediente(numero)`: Toggle de selección individual
- `handleConfirmar()`: Confirma y emite expedientes seleccionados

#### 2. Componentes UI Nuevos

**`Checkbox` (shadcn/ui)**
- Ubicación: `Sistema_v6/frontend/src/components/ui/checkbox.tsx`
- Basado en Radix UI
- Soporta estados checked/unchecked
- Estilos dark mode

**`Select` (shadcn/ui)**
- Ubicación: `Sistema_v6/frontend/src/components/ui/select.tsx`
- Dropdown con search
- Múltiples variantes
- Portal rendering

### Tipos TypeScript

```typescript
interface ExpedienteResumen {
  numero: string
  dependencia: string
  caratula: string
  situacion: string | null
  ultima_actuacion: string | null
}

interface Filtros {
  texto: string
  fuero: string  // 'todos' | 'federal' | 'civil' | 'penal' | 'laboral' | 'contencioso'
  situacion: string[]  // ['en_tramite', 'archivado', 'finalizado']
  filtrarPorFecha: boolean
  fechaDesde: string
  fechaHasta: string
  minActuaciones: number
  usarMinActuaciones: boolean
}
```

### Integración con Backend

**Estado Actual**: ✅ **Completamente integrado con el backend**

**Implementación**:
```typescript
// En handleIniciarExtraccion():
const expedientes = await extraerExpedientesMasivamente(
  undefined, // usuario (opcional, se obtiene de sesión)
  undefined, // contraseña (opcional, se obtiene de sesión)
  procesarConPDF, // procesarConPDF
  agregarLog // callback de progreso
)
```

**Store (expedientesStore.ts)**:
```typescript
extraerExpedientesMasivamente: async (
  usuario?: string,
  contrasena?: string,
  procesarConPDF: boolean = false,
  onProgress?: (mensaje: string) => void
): Promise<ExpedienteResumen[]> => {
  // 1. POST /api/v1/expedientes/extraer
  const response = await apiClient.post('/api/v1/expedientes/extraer', {
    usuario,
    contrasena,
    headless: true,
  })

  // 2. GET /api/v1/expedientes
  const listResponse = await apiClient.get('/api/v1/expedientes')

  // 3. Actualizar store y retornar
  set({ expedientes: listResponse.data.expedientes })
  return listResponse.data.expedientes
}
```

**Backend (FastAPI)**:
- Router: `presentation/api/rest/routers/expedientes.py`
- Use Case: `application/use_cases/extraer_expedientes_use_case.py`
- Scraper: Playwright adapter (implementación en Sistema_v5)

**Notas**:
- La extracción usa playwright para scraping del PJN
- Los expedientes se guardan en el repositorio (base de datos/archivos)
- La función `procesarConPDF` está preparada pero pendiente de implementación en backend

## Casos de Uso

### Caso 1: Migración Inicial al Sistema
**Objetivo**: Importar todos los expedientes activos al sistema

1. Ir a `/expedientes`
2. Click en "Extracción Masiva"
3. Activar "Procesar con procesador_pdf"
4. Iniciar extracción
5. En filtros, seleccionar solo "En trámite"
6. Confirmar selección

### Caso 2: Expedientes de un Fuero Específico
**Objetivo**: Monitorear solo expedientes federales

1. Abrir "Extracción Masiva"
2. Iniciar extracción
3. Fuero: "Federal"
4. Situación: "En trámite"
5. Confirmar

### Caso 3: Búsqueda Específica
**Objetivo**: Encontrar expedientes por número o carátula

1. Extraer expedientes
2. Usar campo de búsqueda: "FPA-000632"
3. Verificar coincidencias
4. Confirmar

## Estilos y Diseño

### Paleta de Colores
- **Primary**: Blue-600 (#3b82f6)
- **Success**: Green-600 (#10b981)
- **Warning**: Yellow-600 (#f59e0b)
- **Error**: Red-600 (#ef4444)

### Layout
- Modal full-screen con max-width: 6xl (1152px)
- Grid responsive: 3 columnas (filtros) + 9 columnas (tabla)
- Altura máxima: 90vh con scroll interno

### Responsividad
- Desktop: Grid completo
- Tablet: Stack vertical
- Mobile: Filtros colapsables (pendiente)

## Testing

### Tests Unitarios (Pendiente)
```typescript
// ExtraccionMasivaDialog.test.tsx
describe('ExtraccionMasivaDialog', () => {
  it('debería mostrar etapa de extracción inicialmente')
  it('debería aplicar filtros correctamente')
  it('debería seleccionar/deseleccionar expedientes')
  it('debería emitir expedientes confirmados')
})
```

### Tests de Integración (Pendiente)
- Conectar con mock del backend
- Verificar flujo completo de extracción
- Validar filtros complejos

## Mejoras Futuras

### Planificadas
- [ ] Conectar con backend real para extracción
- [ ] Implementar filtros por fecha
- [ ] Implementar filtro por número mínimo de actuaciones
- [ ] Paginación en tabla de resultados
- [ ] Exportar selección a CSV/Excel
- [ ] Búsqueda avanzada con regex
- [ ] Filtros adicionales: por juzgado, por tipo de proceso
- [ ] Vista previa de expedientes
- [ ] Guardado de selecciones previas
- [ ] Modo responsive completo

### Posibles Mejoras
- [ ] Estadísticas visuales de la selección (gráficos)
- [ ] Comparación entre extracciones
- [ ] Tags y etiquetas personalizadas
- [ ] Notas en expedientes
- [ ] Integración con workspaces
- [ ] Programación de extracciones automáticas
- [ ] Notificaciones de progreso
- [ ] Modo oscuro optimizado

## Troubleshooting

### Problema: Componentes UI no se encuentran
**Solución**: Los componentes `Checkbox` y `Select` fueron agregados como parte de esta funcionalidad. Verificar que existan en `Sistema_v6/frontend/src/components/ui/`

### Problema: Errores de TypeScript
**Solución**: Ejecutar `npm install` para asegurar que todas las dependencias están instaladas:
```bash
npm install @radix-ui/react-checkbox @radix-ui/react-select lucide-react
```

### Problema: Modal no se cierra
**Solución**: Verificar que el prop `onClose` esté correctamente pasado y que no haya errores en la consola bloqueando el cierre

### Problema: Filtros no funcionan
**Solución**: Los filtros se aplican automáticamente al cambiar (efecto de React). Verificar que `useEffect` esté correctamente configurado

## Comandos de Desarrollo

### Iniciar desarrollo
```bash
cd Sistema_v6/frontend
npm run dev
```

### Build para producción
```bash
npm run build
```

### Tests
```bash
npm run test
```

### Linting
```bash
npm run lint
```

## Archivos Modificados/Creados

```
Sistema_v6/frontend/src/
├── components/
│   ├── expedientes/
│   │   └── ExtraccionMasivaDialog.tsx          (NUEVO)
│   └── ui/
│       ├── checkbox.tsx                         (NUEVO)
│       └── select.tsx                           (NUEVO)
├── pages/
│   └── expedientes/
│       └── ExpedientesPage.tsx                  (MODIFICADO)
└── types/
    └── expediente.ts                            (Ya existía)

Sistema_v6/docs/
└── EXTRACCION_MASIVA_EXPEDIENTES.md            (NUEVO - Este archivo)
```

## Dependencias Necesarias

```json
{
  "dependencies": {
    "@radix-ui/react-checkbox": "^1.0.4",
    "@radix-ui/react-select": "^2.0.0",
    "lucide-react": "^0.303.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  }
}
```

## API Reference

### ExtraccionMasivaDialog

**Props**:
```typescript
{
  onClose: () => void
  onSuccess?: (expedientes: ExpedienteResumen[]) => void
}
```

**Eventos**:
- `onClose`: Se ejecuta al cerrar el modal
- `onSuccess`: Se ejecuta al confirmar selección, recibe array de expedientes seleccionados

**Estados**:
- Etapa 1: Extracción en progreso
- Etapa 2: Filtrado y selección

### Filtros

**Métodos**:
- `aplicarFiltros()`: Aplica filtros a expedientes
- `handleLimpiarFiltros()`: Resetea todos los filtros
- `handleToggleSituacion(situacion)`: Toggle de situación específica

**Estados de Filtros**:
```typescript
{
  texto: string
  fuero: 'todos' | 'federal' | 'civil' | 'penal' | 'laboral' | 'contencioso'
  situacion: Array<'en_tramite' | 'archivado' | 'finalizado'>
  // ... más filtros
}
```

## Notas de Implementación

1. **Datos Mock**: Actualmente usa datos de demostración. Comentarios `TODO` indican dónde conectar backend.

2. **Performance**: Todos los expedientes se cargan en memoria. Para grandes volúmenes (>1000), considerar:
   - Paginación del lado del servidor
   - Virtualización de tabla
   - Lazy loading

3. **Accesibilidad**:
   - Todos los checkboxes tienen labels
   - Modal puede cerrarse con click fuera (cuando no está extrayendo)
   - Estados de loading bien indicados

4. **Dark Mode**: Componentes soportan dark mode mediante clases de Tailwind

5. **Iconos**: Usa `lucide-react` para todos los iconos

---

**Autor**: Sistema de Gestión Legal
**Versión**: 1.0
**Fecha**: Noviembre 2025
**Stack**: React + TypeScript + Tailwind CSS + shadcn/ui
