# Plan de Mejoras: Filtrado, Visualización y Paginación de Expedientes

**Fecha**: 2025-11-11
**Archivo objetivo**: `Sistema_v6/frontend/src/components/expedientes/ExtraccionMasivaDialog.tsx`
**Contexto**: Mejoras al sistema de extracción masiva de expedientes del PJN

---

## 📋 Contexto y Objetivo

Después de completar la funcionalidad de extracción masiva, se identificaron las siguientes necesidades:

1. **Falta información visible**: La columna "Última Actuación" no se muestra en la tabla
2. **Filtros estáticos**: Los filtros de "Fuero" y "Situación" están hardcodeados y no reflejan los datos reales
3. **Sin ordenamiento por fecha**: No se puede ordenar por fecha de última actuación
4. **Sin filtro de rango de fechas**: No se puede filtrar por rangos temporales
5. **Sin paginación**: Con miles de expedientes, la lista se vuelve difícil de manejar

---

## 🔍 Investigación: Estructura de Datos

### Campos Disponibles

```typescript
interface ExpedienteListado {
  numero: string              // Ej: "FPA 001949/2018"
  caratula: string           // Carátula completa del caso
  dependencia: string        // Juzgado o dependencia
  situacion: string          // Estado procesal (EN LETRA, EN DESPACHO, GIRO, etc.)
  fecha_inicio: string       // ⚠️ Generalmente VACÍO, NO usar
  ultima_actuacion: string   // Formato: YYYY-MM-DD
}
```

### Valores Dinámicos Encontrados

**Situación** (ejemplos de valores reales):
- EN LETRA
- EN DESPACHO
- GIRO
- CONFRONTE
- REMISIÓN
- SENTENCIA
- PRÉSTAMO

**Dependencia** (27+ valores únicos, ejemplos):
- CAMARA FEDERAL DE PARANÁ - SECRETARIA CIVIL
- JUZGADO FEDERAL DE PARANÁ 2 - SECRETARIA CIVIL Y COMERCIAL 1
- JUZGADO CONTENCIOSO ADMINISTRATIVO FEDERAL 2- SECRETARIA Nº 3
- etc.

### Formato de Fechas

- **Almacenamiento**: `YYYY-MM-DD` (Ej: `"2025-11-11"`)
- **Visualización**: `dd/mm/yyyy` (Ej: `"11/11/2025"`)

---

## ✅ Tareas de Implementación

### Fase 1: Preparación y Utilidades

#### [✓] Tarea 1: Actualizar interface Filtros

**Ubicación**: Inicio del componente `ExtraccionMasivaDialog`

```typescript
interface Filtros {
  texto: string
  dependencias: string[]  // ← Cambio: era 'fuero: string'
  situacion: string[]     // ← Se mantiene array pero ahora dinámico
  ordenFecha: 'desc' | 'asc' | 'ninguno'  // ← Nuevo
  fechaActuacionDesde: string             // ← Nuevo (YYYY-MM-DD)
  fechaActuacionHasta: string             // ← Nuevo (YYYY-MM-DD)
  usarFiltroFechaActuacion: boolean       // ← Nuevo
  minActuaciones: number
  usarMinActuaciones: boolean
}
```

**Actualizar estado inicial**:
```typescript
const [filtros, setFiltros] = useState<Filtros>({
  texto: '',
  dependencias: [],  // ← Cambio
  situacion: [],
  ordenFecha: 'ninguno',  // ← Nuevo
  fechaActuacionDesde: '',  // ← Nuevo
  fechaActuacionHasta: '',  // ← Nuevo
  usarFiltroFechaActuacion: false,  // ← Nuevo
  minActuaciones: 5,
  usarMinActuaciones: false
})
```

---

#### [✓] Tarea 2: Agregar estados de paginación

**Ubicación**: Después de los estados existentes

```typescript
const [paginaActual, setPaginaActual] = useState(1)
const ITEMS_POR_PAGINA = 50
```

---

#### [✓] Tarea 3: Crear funciones auxiliares de fechas

**Ubicación**: Antes de la función `aplicarFiltros()`

```typescript
// Parsear fecha YYYY-MM-DD a Date
const parsearFecha = (fechaStr: string): Date | null => {
  if (!fechaStr || fechaStr === '') return null
  const [year, month, day] = fechaStr.split('-').map(Number)
  if (!year || !month || !day) return null
  return new Date(year, month - 1, day)
}

// Formatear fecha YYYY-MM-DD a dd/mm/yyyy
const formatearFecha = (fechaStr: string): string => {
  const fecha = parsearFecha(fechaStr)
  if (!fecha) return ''
  const dia = fecha.getDate().toString().padStart(2, '0')
  const mes = (fecha.getMonth() + 1).toString().padStart(2, '0')
  return `${dia}/${mes}/${fecha.getFullYear()}`
}
```

---

#### [✓] Tarea 4: Crear funciones para opciones dinámicas con useMemo

**Ubicación**: Después de los estados, antes de aplicarFiltros

```typescript
// Calcular opciones de Dependencia con conteo
const opcionesDependencia = useMemo(() => {
  const counts = new Map<string, number>()
  expedientesExtraidos.forEach(exp => {
    const dep = exp.dependencia || 'Sin dependencia'
    counts.set(dep, (counts.get(dep) || 0) + 1)
  })
  return Array.from(counts.entries())
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([valor, count]) => ({ valor, count }))
}, [expedientesExtraidos])

// Calcular opciones de Situación con conteo
const opcionesSituacion = useMemo(() => {
  const counts = new Map<string, number>()
  expedientesExtraidos.forEach(exp => {
    const sit = exp.situacion || 'Sin situación'
    counts.set(sit, (counts.get(sit) || 0) + 1)
  })
  return Array.from(counts.entries())
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([valor, count]) => ({ valor, count }))
}, [expedientesExtraidos])
```

---

### Fase 2: Actualizar Lógica de Filtrado

#### [✓] Tarea 5: Actualizar función aplicarFiltros()

**Ubicación**: Reemplazar función existente

```typescript
const aplicarFiltros = () => {
  let filtered = [...expedientesExtraidos]

  // Función auxiliar para normalizar texto (quitar tildes, minúsculas)
  const normalizar = (texto: string) => {
    return texto
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
  }

  // Filtro por texto
  if (filtros.texto) {
    const textoNormalizado = normalizar(filtros.texto)
    filtered = filtered.filter(exp =>
      normalizar(exp.numero).includes(textoNormalizado) ||
      normalizar(exp.caratula).includes(textoNormalizado)
    )
  }

  // Filtro por Dependencias (múltiple)
  if (filtros.dependencias.length > 0) {
    filtered = filtered.filter(exp =>
      filtros.dependencias.includes(exp.dependencia)
    )
  }

  // Filtro por Situación (múltiple)
  if (filtros.situacion.length > 0) {
    filtered = filtered.filter(exp =>
      filtros.situacion.includes(exp.situacion)
    )
  }

  // Filtro por Rango de Fechas
  if (filtros.usarFiltroFechaActuacion) {
    filtered = filtered.filter(exp => {
      const fecha = parsearFecha(exp.ultima_actuacion)
      if (!fecha) return false

      const desde = filtros.fechaActuacionDesde
        ? parsearFecha(filtros.fechaActuacionDesde)
        : null
      const hasta = filtros.fechaActuacionHasta
        ? parsearFecha(filtros.fechaActuacionHasta)
        : null

      if (desde && fecha < desde) return false
      if (hasta && fecha > hasta) return false

      return true
    })
  }

  // Ordenamiento por fecha
  if (filtros.ordenFecha !== 'ninguno') {
    filtered.sort((a, b) => {
      const fechaA = parsearFecha(a.ultima_actuacion)
      const fechaB = parsearFecha(b.ultima_actuacion)

      if (!fechaA && !fechaB) return 0
      if (!fechaA) return 1
      if (!fechaB) return -1

      const diff = fechaA.getTime() - fechaB.getTime()
      return filtros.ordenFecha === 'asc' ? diff : -diff
    })
  }

  setExpedientesFiltrados(filtered)

  // Seleccionar todos los filtrados por defecto
  const nuevosSeleccionados = new Set(filtered.map(exp => exp.numero))
  setExpedientesSeleccionados(nuevosSeleccionados)

  // Resetear a página 1 cuando cambian filtros
  setPaginaActual(1)
}
```

---

#### [✓] Tarea 6: Agregar useEffect para resetear página al cambiar filtros

**Ubicación**: Después del useEffect existente que aplica filtros

```typescript
// Resetear página cuando cambian los filtros
useEffect(() => {
  setPaginaActual(1)
}, [filtros])
```

---

#### [✓] Tarea 7: Actualizar handleLimpiarFiltros()

**Ubicación**: Reemplazar función existente

```typescript
const handleLimpiarFiltros = () => {
  setFiltros({
    texto: '',
    dependencias: [],  // ← Cambio
    situacion: [],
    ordenFecha: 'ninguno',  // ← Nuevo
    fechaActuacionDesde: '',  // ← Nuevo
    fechaActuacionHasta: '',  // ← Nuevo
    usarFiltroFechaActuacion: false,  // ← Nuevo
    minActuaciones: 5,
    usarMinActuaciones: false
  })
  setPaginaActual(1)  // ← Nuevo
}
```

---

### Fase 3: Actualizar UI - Tabla

#### [✓] Tarea 8: Agregar columna "Última Actuación" en la tabla

**Ubicación**: En el `<thead>` y `<tbody>` de la tabla

**En thead** (después de la columna "Situación"):
```tsx
<th className="p-3 text-left text-sm font-medium">Última Actuación</th>
```

**En tbody** (después de la celda de situación):
```tsx
<td className="p-3 text-sm text-gray-600 dark:text-gray-400">
  {formatearFecha(expediente.ultima_actuacion)}
</td>
```

---

#### [✓] Tarea 9: Implementar paginación en la tabla

**Ubicación**:
1. Calcular expedientes paginados antes del return
2. Usar `expedientesPaginados` en el map de la tabla
3. Agregar controles de paginación debajo de la tabla

**Cálculo de paginación** (antes del return):
```typescript
// Calcular paginación
const totalPaginas = Math.ceil(expedientesFiltrados.length / ITEMS_POR_PAGINA)
const indiceInicio = (paginaActual - 1) * ITEMS_POR_PAGINA
const indiceFin = Math.min(indiceInicio + ITEMS_POR_PAGINA, expedientesFiltrados.length)
const expedientesPaginados = expedientesFiltrados.slice(indiceInicio, indiceFin)
```

**Cambiar el map** (línea ~950):
```tsx
{expedientesPaginados.map((expediente) => (
  // ... contenido de la fila
))}
```

**Agregar controles de paginación** (después del cierre de `</table>`):
```tsx
{/* Controles de Paginación */}
{expedientesFiltrados.length > ITEMS_POR_PAGINA && (
  <div className="flex items-center justify-between px-4 py-3 border-t">
    <div className="text-sm text-gray-600 dark:text-gray-400">
      Mostrando {indiceInicio + 1}-{indiceFin} de {expedientesFiltrados.length} expedientes
    </div>
    <div className="flex gap-2">
      <Button
        variant="outline"
        size="sm"
        disabled={paginaActual === 1}
        onClick={() => setPaginaActual(1)}
      >
        Primera
      </Button>
      <Button
        variant="outline"
        size="sm"
        disabled={paginaActual === 1}
        onClick={() => setPaginaActual(paginaActual - 1)}
      >
        Anterior
      </Button>
      <span className="px-3 py-1 text-sm">
        Página {paginaActual} de {totalPaginas}
      </span>
      <Button
        variant="outline"
        size="sm"
        disabled={paginaActual >= totalPaginas}
        onClick={() => setPaginaActual(paginaActual + 1)}
      >
        Siguiente
      </Button>
      <Button
        variant="outline"
        size="sm"
        disabled={paginaActual >= totalPaginas}
        onClick={() => setPaginaActual(totalPaginas)}
      >
        Última
      </Button>
    </div>
  </div>
)}
```

---

### Fase 4: Actualizar UI - Panel de Filtros

#### [✓] Tarea 10: Reemplazar filtro "Fuero" por "Dependencia" dinámica

**Ubicación**: En el panel de filtros (sección izquierda), reemplazar el Select de Fuero

```tsx
{/* Dependencia (múltiple con checkboxes) */}
<div className="space-y-2">
  <div className="flex items-center justify-between">
    <label className="text-sm font-medium">Dependencia</label>
    <div className="flex gap-1">
      <Button
        variant="ghost"
        size="sm"
        className="h-6 text-xs"
        onClick={() => setFiltros({
          ...filtros,
          dependencias: opcionesDependencia.map(o => o.valor)
        })}
      >
        Todas
      </Button>
      <Button
        variant="ghost"
        size="sm"
        className="h-6 text-xs"
        onClick={() => setFiltros({ ...filtros, dependencias: [] })}
      >
        Ninguna
      </Button>
    </div>
  </div>
  <div className="space-y-1 max-h-48 overflow-y-auto border rounded p-2">
    {opcionesDependencia.map(({ valor, count }) => (
      <div key={valor} className="flex items-center space-x-2">
        <Checkbox
          id={`dep-${valor}`}
          checked={filtros.dependencias.includes(valor)}
          onCheckedChange={(checked) => {
            if (checked) {
              setFiltros({
                ...filtros,
                dependencias: [...filtros.dependencias, valor]
              })
            } else {
              setFiltros({
                ...filtros,
                dependencias: filtros.dependencias.filter(d => d !== valor)
              })
            }
          }}
        />
        <label
          htmlFor={`dep-${valor}`}
          className="text-xs flex-1 cursor-pointer"
        >
          {valor} ({count})
        </label>
      </div>
    ))}
  </div>
</div>
```

---

#### [✓] Tarea 11: Actualizar filtro "Situación" a dinámico

**Ubicación**: Reemplazar la sección de Situación Procesal

```tsx
{/* Situación Procesal (dinámico con checkboxes) */}
<div className="space-y-2">
  <div className="flex items-center justify-between">
    <label className="text-sm font-medium">Situación Procesal</label>
    <div className="flex gap-1">
      <Button
        variant="ghost"
        size="sm"
        className="h-6 text-xs"
        onClick={() => setFiltros({
          ...filtros,
          situacion: opcionesSituacion.map(o => o.valor)
        })}
      >
        Todas
      </Button>
      <Button
        variant="ghost"
        size="sm"
        className="h-6 text-xs"
        onClick={() => setFiltros({ ...filtros, situacion: [] })}
      >
        Ninguna
      </Button>
    </div>
  </div>
  <div className="space-y-1">
    {opcionesSituacion.map(({ valor, count }) => (
      <div key={valor} className="flex items-center space-x-2">
        <Checkbox
          id={`sit-${valor}`}
          checked={filtros.situacion.includes(valor)}
          onCheckedChange={(checked) => {
            if (checked) {
              setFiltros({
                ...filtros,
                situacion: [...filtros.situacion, valor]
              })
            } else {
              setFiltros({
                ...filtros,
                situacion: filtros.situacion.filter(s => s !== valor)
              })
            }
          }}
        />
        <label
          htmlFor={`sit-${valor}`}
          className="text-sm cursor-pointer"
        >
          {valor} ({count})
        </label>
      </div>
    ))}
  </div>
</div>
```

---

#### [✓] Tarea 12: Agregar controles de ordenamiento por fecha

**Ubicación**: Después del filtro de Situación, antes del separador

```tsx
{/* Separador */}
<div className="border-t my-4" />

{/* Ordenamiento por Fecha */}
<div className="space-y-2">
  <label className="text-sm font-medium">Ordenar por Última Actuación</label>
  <Select
    value={filtros.ordenFecha}
    onValueChange={(value) => setFiltros({
      ...filtros,
      ordenFecha: value as 'desc' | 'asc' | 'ninguno'
    })}
  >
    <SelectTrigger>
      <SelectValue />
    </SelectTrigger>
    <SelectContent>
      <SelectItem value="ninguno">Sin ordenar</SelectItem>
      <SelectItem value="desc">Más recientes primero</SelectItem>
      <SelectItem value="asc">Más antiguos primero</SelectItem>
    </SelectContent>
  </Select>
</div>
```

---

#### [✓] Tarea 13: Agregar filtro de rango de fechas

**Ubicación**: Después del control de ordenamiento

```tsx
{/* Filtro por Rango de Fechas */}
<div className="space-y-2">
  <div className="flex items-center space-x-2">
    <Checkbox
      id="usar-filtro-fecha"
      checked={filtros.usarFiltroFechaActuacion}
      onCheckedChange={(checked) => setFiltros({
        ...filtros,
        usarFiltroFechaActuacion: checked as boolean
      })}
    />
    <label
      htmlFor="usar-filtro-fecha"
      className="text-sm font-medium cursor-pointer"
    >
      Filtrar por rango de fechas
    </label>
  </div>

  {filtros.usarFiltroFechaActuacion && (
    <div className="space-y-3 pl-6">
      <DateInputArgentino
        label="Desde"
        value={filtros.fechaActuacionDesde}
        onChange={(value) => setFiltros({
          ...filtros,
          fechaActuacionDesde: value || ''
        })}
        placeholder="dd/mm/aaaa"
      />
      <DateInputArgentino
        label="Hasta"
        value={filtros.fechaActuacionHasta}
        onChange={(value) => setFiltros({
          ...filtros,
          fechaActuacionHasta: value || ''
        })}
        placeholder="dd/mm/aaaa"
      />
    </div>
  )}
</div>
```

---

#### [✓] Tarea 14: Mejorar botones de selección masiva

**Ubicación**: Actualizar los botones sobre la tabla

```tsx
<div className="flex gap-2">
  <Button
    variant="outline"
    size="sm"
    onClick={handleSeleccionarTodos}
  >
    <CheckSquare className="h-4 w-4 mr-1" />
    Todos los filtrados ({expedientesFiltrados.length})
  </Button>
  <Button
    variant="outline"
    size="sm"
    onClick={() => {
      const nuevosSeleccionados = new Set(expedientesSeleccionados)
      expedientesPaginados.forEach(exp => nuevosSeleccionados.add(exp.numero))
      setExpedientesSeleccionados(nuevosSeleccionados)
    }}
  >
    <CheckSquare className="h-4 w-4 mr-1" />
    Página actual ({expedientesPaginados.length})
  </Button>
  <Button
    variant="outline"
    size="sm"
    onClick={handleDeseleccionarTodos}
  >
    <Square className="h-4 w-4 mr-1" />
    Ninguno
  </Button>
  <Button
    variant="outline"
    size="sm"
    onClick={handleInvertirSeleccion}
  >
    Invertir
  </Button>
</div>
```

---

## 🧪 Checklist de Verificación

Una vez completadas todas las tareas, verificar:

### Visualización
- [ ] La columna "Última Actuación" aparece en la tabla
- [ ] Las fechas se muestran en formato dd/mm/yyyy
- [ ] La tabla es responsiva y scrolleable

### Filtros Dinámicos
- [ ] Las opciones de Dependencia se cargan dinámicamente
- [ ] Las opciones de Situación se cargan dinámicamente
- [ ] Los contadores (N) muestran la cantidad correcta
- [ ] Los botones "Todas/Ninguna" funcionan correctamente

### Ordenamiento
- [ ] El ordenamiento "Más recientes primero" funciona
- [ ] El ordenamiento "Más antiguos primero" funciona
- [ ] El ordenamiento "Sin ordenar" mantiene el orden original
- [ ] El ordenamiento se aplica después de filtrar

### Filtro de Fechas
- [ ] El checkbox activa/desactiva el filtro de rango
- [ ] Los DateInputArgentino permiten ingresar fechas dd/mm/yyyy
- [ ] El filtro "Desde" funciona correctamente
- [ ] El filtro "Hasta" funciona correctamente
- [ ] El filtro maneja fechas vacías sin errores

### Paginación
- [ ] Se muestran 50 expedientes por página
- [ ] Los botones Primera/Anterior/Siguiente/Última funcionan
- [ ] El contador "Mostrando X-Y de Z" es correcto
- [ ] Al cambiar filtros, vuelve a la página 1
- [ ] La selección se mantiene al cambiar de página

### Selección Masiva
- [ ] "Todos los filtrados" selecciona todos (no solo página actual)
- [ ] "Página actual" selecciona solo los 50 visibles
- [ ] "Ninguno" deselecciona todos
- [ ] "Invertir" invierte la selección correctamente
- [ ] El contador de seleccionados es correcto

### Performance
- [ ] Con 2000+ expedientes, la interfaz es fluida
- [ ] Los filtros se aplican sin delay perceptible
- [ ] El cambio de página es instantáneo
- [ ] useMemo optimiza los cálculos de opciones

### UX General
- [ ] El botón "Limpiar" resetea todos los filtros
- [ ] Los separadores visuales organizan bien el panel
- [ ] Los hints y labels son claros
- [ ] No hay errores en consola

---

## 📝 Notas Importantes

1. **NO usar el campo `fecha_inicio`** - Está vacío en la mayoría de datos reales
2. **Formato de fechas**: Siempre `YYYY-MM-DD` internamente, `dd/mm/yyyy` para visualización
3. **Performance**: useMemo es crucial para opciones dinámicas con miles de expedientes
4. **Selección persistente**: Usar Set<string> con números de expediente
5. **Resetear página**: Al cambiar cualquier filtro, volver a página 1
6. **Ordenamiento**: Aplicar DESPUÉS de filtrar, ANTES de paginar

---

## 🚀 Orden de Ejecución Recomendado

1. **Preparación** (Tareas 1-4): Actualizar tipos, estados y crear utilidades
2. **Lógica** (Tareas 5-7): Actualizar filtrado, ordenamiento y limpieza
3. **Tabla** (Tareas 8-9): Agregar columna y paginación
4. **Filtros** (Tareas 10-13): Actualizar panel de filtros
5. **Pulir** (Tarea 14): Mejorar botones de selección
6. **Verificar**: Ejecutar checklist completo

---

**Fin del Plan** ✅
