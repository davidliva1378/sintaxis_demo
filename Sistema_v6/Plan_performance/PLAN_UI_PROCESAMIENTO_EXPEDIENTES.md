# Plan: UI de Procesamiento en Detalle de Expedientes

## Objetivo

Mejorar la visualización del procesamiento de expedientes integrando la información de clasificación, utilidad y vencimientos directamente en la página de detalle de cada expediente, utilizando un sistema de pestañas.

## Análisis Actual

### Estado Actual de ExpedienteDetallePage.tsx
- Layout lineal sin pestañas
- Secciones: Header, Info card, ActuacionesList
- No muestra información de procesamiento
- No indica si el expediente ha sido procesado

### Endpoints de Procesamiento Disponibles
```typescript
POST /api/v1/procesamiento/expediente          // Procesar expediente completo
GET  /api/v1/procesamiento/expediente/{numero}/estadisticas  // Estadísticas
GET  /api/v1/procesamiento/vencimientos/urgentes  // Vencimientos urgentes
GET  /api/v1/procesamiento/actuaciones/utilidad/{nivel}  // Por nivel utilidad
```

### Componentes Existentes
- `procesamientoApi.ts` - Cliente API con funciones de procesamiento
- `procesamiento.ts` - Tipos y utilidades (UtilidadJuridica, getColorUtilidad)
- No existe componente de visualización en detalle de expediente

---

## Fases de Implementación

### Fase 1: Sistema de Pestañas

**Objetivo**: Agregar sistema de tabs a ExpedienteDetallePage

**Tareas**:
1. Instalar dependencia @radix-ui/react-tabs
2. Crear componente tabs.tsx en /components/ui/
3. Modificar ExpedienteDetallePage para usar tabs con 3 pestañas:
   - "Información" (contenido actual)
   - "Procesamiento" (nuevo)
   - "Actuaciones" (mover ActuacionesList)

**Archivos a crear**:
- `frontend/src/components/ui/tabs.tsx`

**Archivos a modificar**:
- `frontend/src/pages/expedientes/ExpedienteDetallePage.tsx`

**Complejidad**: Media

---

### Fase 2: Pestaña de Procesamiento

**Objetivo**: Mostrar resultados del procesamiento con clasificación y utilidad

**Tareas**:
1. Crear panel de estadísticas del expediente
2. Crear lista de actuaciones clasificadas con indicadores visuales
3. Crear panel de vencimientos del expediente
4. Integrar componentes en la pestaña "Procesamiento"

**Archivos a crear**:
- `frontend/src/components/expedientes/EstadisticasExpedientePanel.tsx`
- `frontend/src/components/expedientes/ActuacionesClasificadasList.tsx`
- `frontend/src/components/expedientes/VencimientosExpedientePanel.tsx`

**Estructura de EstadisticasExpedientePanel**:
```typescript
// Muestra:
// - Total actuaciones
// - Desglose por utilidad (ALTA/MEDIA/BAJA/NULA) con barras de progreso
// - Porcentaje de reducción
// - Total vencimientos detectados
// - Vencimientos urgentes/próximos
// - Fecha último procesamiento
```

**Estructura de ActuacionesClasificadasList**:
```typescript
// Lista de actuaciones con:
// - Badge de utilidad coloreado (ALTA=verde, MEDIA=amarillo, BAJA=naranja, NULA=gris)
// - Indicador de vencimiento (si aplica)
// - Detalle expandible
// - Filtros por nivel de utilidad
// - Ordenamiento por utilidad/fecha
```

**Estructura de VencimientosExpedientePanel**:
```typescript
// Panel con:
// - Lista de vencimientos del expediente
// - Indicador de urgencia (colores rojo/amarillo/verde)
// - Fecha límite y días restantes
// - Tipo de actuación asociada
```

**Complejidad**: Alta

---

### Fase 3: Indicadores de Estado de Procesamiento

**Objetivo**: Mostrar claramente si el expediente/actuación está procesado

**Tareas**:
1. Agregar indicador en header del expediente (Procesado/No procesado)
2. Mostrar mensaje cuando no hay procesamiento disponible
3. Botón para procesar/reprocesar desde la UI
4. Indicador de fecha de último procesamiento

**Indicadores visuales**:
```typescript
// Badge en header:
// - Verde: "Procesado" (con fecha)
// - Gris: "Sin procesar" (con botón para procesar)
// - Amarillo: "Desactualizado" (si hay actuaciones nuevas)
```

**Archivos a crear**:
- `frontend/src/components/expedientes/ProcesamientoStatusBadge.tsx`

**Archivos a modificar**:
- `frontend/src/pages/expedientes/ExpedienteDetallePage.tsx`

**Complejidad**: Media

---

### Fase 4: Integración con API

**Objetivo**: Conectar componentes con endpoints de procesamiento

**Tareas**:
1. Agregar función para obtener estadísticas de expediente específico
2. Agregar función para procesar expediente desde UI
3. Manejar estados de carga y errores
4. Implementar polling o refresh manual para actualizar datos

**Funciones API a agregar/modificar** (procesamientoApi.ts):
```typescript
// Existentes:
obtenerEstadisticasExpediente(numero: string)
procesarExpediente(request: ProcesarExpedienteRequest)

// A agregar:
obtenerActuacionesClasificadas(numero: string)
obtenerVencimientosExpediente(numero: string)
```

**Complejidad**: Media

---

## Sugerencias Adicionales

### Mejora 1: Acceso Rápido desde Lista de Expedientes
- Agregar badge pequeño en la tarjeta de expediente mostrando:
  - Cantidad de actuaciones de alta utilidad
  - Vencimientos próximos
  - Estado de procesamiento

### Mejora 2: Mejoras a Página Global de Procesamiento
- Filtrar por expediente específico
- Agrupar vencimientos por expediente
- Dashboard con métricas agregadas de todos los expedientes

### Mejora 3: Sistema de Notificaciones
- Alertas cuando hay vencimientos próximos
- Notificación cuando un expediente necesita reprocesamiento

### Mejora 4: Exportación de Datos
- Exportar actuaciones de alta utilidad a PDF
- Exportar calendario de vencimientos

### Mejora 5: Historial de Cambios
- Mostrar cuando se detectan nuevas actuaciones vs último procesamiento
- Comparativa antes/después del procesamiento

---

## Archivos Involucrados

### A Crear
1. `frontend/src/components/ui/tabs.tsx` - Componente de pestañas
2. `frontend/src/components/expedientes/EstadisticasExpedientePanel.tsx` - Panel de estadísticas
3. `frontend/src/components/expedientes/ActuacionesClasificadasList.tsx` - Lista clasificada
4. `frontend/src/components/expedientes/VencimientosExpedientePanel.tsx` - Panel vencimientos
5. `frontend/src/components/expedientes/ProcesamientoStatusBadge.tsx` - Badge de estado

### A Modificar
1. `frontend/src/pages/expedientes/ExpedienteDetallePage.tsx` - Agregar tabs y componentes
2. `frontend/src/api/procesamientoApi.ts` - Nuevas funciones API
3. `frontend/src/types/procesamiento.ts` - Tipos adicionales si necesario
4. `frontend/package.json` - Agregar @radix-ui/react-tabs

---

## Estimación de Complejidad

| Fase | Descripción | Complejidad | Dependencias |
|------|-------------|-------------|--------------|
| 1 | Sistema de Pestañas | Media | npm install |
| 2 | Pestaña de Procesamiento | Alta | Fase 1 |
| 3 | Indicadores de Estado | Media | Fase 1, 2 |
| 4 | Integración API | Media | Fase 2, 3 |

**Orden recomendado**: Fase 1 → Fase 2 → Fase 3 → Fase 4

---

## Dependencias Técnicas

### NPM Packages a Instalar
```bash
npm install @radix-ui/react-tabs
```

### Componentes UI Existentes Utilizados
- Card, CardContent, CardHeader
- Badge
- Button
- Progress (para barras de estadísticas)
- Skeleton (para estados de carga)

### Librerías Ya Instaladas
- recharts (para gráficos si se requieren)
- lucide-react (para íconos)

---

## Criterios de Éxito

1. Usuario puede ver pestañas en detalle de expediente
2. Pestaña "Procesamiento" muestra:
   - Estadísticas de clasificación por utilidad
   - Lista de actuaciones con indicadores visuales
   - Vencimientos con fechas y urgencia
3. Indicador claro de estado de procesamiento en header
4. Botón funcional para procesar/reprocesar
5. Manejo correcto de estados de carga y errores
6. Mensaje informativo cuando expediente no está procesado

---

## Datos de Prueba

Expedientes disponibles para testing:
- **CARERI (21002877-2011)**: 216 actuaciones, 6 vencimientos, 39.4% reducción
- **GENERCH (FPA-004791-2020)**: 49 actuaciones, 2 vencimientos, 14.3% reducción

---

## Notas Adicionales

- Los endpoints de procesamiento requieren que el expediente tenga actuaciones cargadas
- El procesamiento guarda resultados en BD (`guardar_en_bd: true`)
- Los colores de utilidad están definidos en `getColorUtilidad()` en procesamiento.ts
- La clasificación usa heurísticas basadas en tipo y detalle de actuación
