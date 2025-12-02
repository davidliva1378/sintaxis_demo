# Plan de Implementación: Funcionalidades IA en Frontend

> **Fecha**: 2025-11-26
> **Ubicación**: `Sistema_v6/Plan_ia/PLAN_IMPLEMENTACION_FRONTEND_IA.md`

---

## PARTE 1: AUDITORÍA - Estado Actual

### 1.1 Funcionalidades YA Expuestas

| Ubicación | Endpoint | Estado |
|-----------|----------|--------|
| `/ia` - Tab RAG | `POST /api/v1/rag/query` | ✅ Funcional |
| `/ia` - Tab Búsqueda | `POST /api/v1/rag/search` | ✅ Funcional |
| `/ia` - Tab Chat | `POST /api/v1/ia/chat/stream` | ✅ SSE |
| `/expedientes/:n` - Tab Inteligencia | `GET /api/v1/expedientes/{n}/inteligencia` | ✅ Funcional |
| `/expedientes/:n` - Tab Mi Análisis | `GET/POST /api/v1/analisis/...` | ✅ Funcional |
| `/expedientes/:n` - Tab Vencimientos | `GET /api/v1/procesamiento/.../vencimientos` | ✅ Funcional |
| `/expedientes/:n` - Tab Procesamiento | `GET /api/v1/procesamiento/.../estadisticas` | ✅ Funcional |

### 1.2 Funcionalidades Backend SIN Frontend

| Feature | Endpoint | Estado Backend |
|---------|----------|----------------|
| **Resumen Ejecutivo LLM** | `GET /api/v1/ia/rag/resumir/{expediente_id}` | ✅ Implementado |
| **Vencimientos Globales** | `GET /api/v1/procesamiento/vencimientos/urgentes` | ✅ Implementado |
| **Estadísticas Globales** | `GET /api/v1/procesamiento/estadisticas/globales` | ✅ Implementado |
| **Destacados Globales** | `GET /api/v1/analisis/destacados` | ✅ Implementado |
| **Exportar Análisis** | `GET /api/v1/analisis/expediente/{n}/exportar` | ✅ Implementado |
| **Relaciones Entidades** | `POST /api/v1/ia/relaciones/extraer` | ✅ Implementado |
| **Hardware Profile** | `GET/POST /api/v1/ia/hardware/profile` | ✅ Implementado |

---

## PARTE 2: PLAN DE IMPLEMENTACIÓN

### FASE 1: Quick Wins (Prioridad Alta)

#### 1.1 Activar Resumen Ejecutivo en InteligenciaPanel
**Ubicación**: `frontend/src/components/expedientes/InteligenciaPanel.tsx`
**Esfuerzo**: Bajo

**Cambios necesarios**:
1. Agregar botón "Generar Resumen" en el panel
2. Llamar a `GET /api/v1/ia/rag/resumir/{expediente_id}`
3. Mostrar resumen en card colapsable al inicio del panel
4. Guardar en caché para no regenerar

**Nuevo código en `expedientesApi.ts`**:
```typescript
export async function generarResumenExpediente(numero: string): Promise<{resumen: string}> {
  const response = await fetch(`${API_BASE_URL}/api/v1/ia/rag/resumir/${encodeURIComponent(numero)}`)
  return response.json()
}
```

#### 1.2 Exportar Análisis desde MiAnalisisList
**Ubicación**: `frontend/src/components/expedientes/MiAnalisisList.tsx`
**Esfuerzo**: Bajo

**Cambios necesarios**:
1. Agregar botón "Exportar" en header del componente
2. Llamar a `GET /api/v1/analisis/expediente/{n}/exportar?formato=csv`
3. Descargar archivo directamente

---

### FASE 2: Nuevas Páginas (Prioridad Media)

#### 2.1 Dashboard de Vencimientos Globales
**Nueva página**: `frontend/src/pages/vencimientos/VencimientosPage.tsx`
**Nueva ruta**: `/vencimientos`

**Componentes a crear**:
```
frontend/src/
├── pages/vencimientos/
│   └── VencimientosPage.tsx          # Página principal
├── components/vencimientos/
│   ├── VencimientosGlobalesPanel.tsx # Lista de vencimientos urgentes
│   ├── VencimientoCard.tsx           # Card individual
│   └── TimelineVencimientos.tsx      # Vista timeline visual
└── api/
    └── vencimientosApi.ts            # Cliente API
```

**Diseño UI**:
- Header con filtros (días adelante, nivel urgencia)
- Cards con código de colores por urgencia:
  - 🔴 Vencido (rojo)
  - 🟠 Crítico (naranja) - 1 día
  - 🟡 Urgente (amarillo) - 2-3 días
  - 🟢 Próximo (verde) - 4-7 días
- Click en card navega al expediente
- Badge en sidebar con contador de urgentes

**Endpoint**: `GET /api/v1/procesamiento/vencimientos/urgentes?dias_adelante=7`

#### 2.2 Dashboard de Estadísticas Globales
**Nueva página**: `frontend/src/pages/estadisticas/EstadisticasPage.tsx`
**Nueva ruta**: `/estadisticas`

**Componentes**:
```
frontend/src/
├── pages/estadisticas/
│   └── EstadisticasPage.tsx
└── components/estadisticas/
    ├── EstadisticasGlobalesCard.tsx
    ├── GraficoUtilidad.tsx           # Pie chart utilidad
    └── GraficoTendencias.tsx         # Line chart temporal
```

**Datos a mostrar** (de `GET /api/v1/procesamiento/estadisticas/globales`):
- Total expedientes procesados
- Total actuaciones procesadas
- Vencimientos detectados vs urgentes
- Reducción promedio (%)
- Distribución por utilidad (alta/media/baja/nula)

#### 2.3 Página de Destacados Globales
**Nueva página**: `frontend/src/pages/destacados/DestacadosPage.tsx`
**Ruta existente**: `/destacados` (ya existe pero puede mejorarse)

**Mejoras**:
- Agrupar por expediente
- Filtrar por tags
- Exportar selección
- Vista cards vs lista

**Endpoint**: `GET /api/v1/analisis/destacados`

---

### FASE 3: Features Avanzados (Prioridad Baja)

#### 3.1 Visualización de Relaciones entre Entidades
**Ubicación sugerida**: Nuevo tab en `ExpedienteDetallePage` o modal desde InteligenciaPanel
**Librería**: `react-force-graph` o `vis-network`

**Componentes**:
```
frontend/src/components/expedientes/
└── RelacionesGraph.tsx
```

**Datos**: Combinar respuesta de `/inteligencia` con `/ia/relaciones/extraer`

#### 3.2 Panel de Configuración de Hardware/Modelos
**Ubicación**: Nueva sección en `/settings`

**Componentes**:
```
frontend/src/components/settings/
└── ConfiguracionIA.tsx
```

**Endpoints**:
- `GET /api/v1/ia/hardware/profile`
- `POST /api/v1/ia/hardware/profile`
- `GET /api/v1/ia/models`
- `POST /api/v1/ia/models/set`

---

## PARTE 3: ESTRUCTURA DE ARCHIVOS FINAL

```
frontend/src/
├── api/
│   ├── expedientesApi.ts      # (modificar) agregar generarResumen
│   ├── analisisApi.ts         # (existente) agregar exportar
│   ├── vencimientosApi.ts     # (nuevo)
│   └── estadisticasApi.ts     # (nuevo)
│
├── pages/
│   ├── vencimientos/
│   │   └── VencimientosPage.tsx    # (nuevo)
│   ├── estadisticas/
│   │   └── EstadisticasPage.tsx    # (nuevo)
│   └── expedientes/
│       └── ExpedienteDetallePage.tsx # (existente - ya tiene todos los tabs)
│
├── components/
│   ├── expedientes/
│   │   ├── InteligenciaPanel.tsx   # (modificar) agregar resumen
│   │   └── MiAnalisisList.tsx      # (modificar) agregar exportar
│   ├── vencimientos/
│   │   ├── VencimientosGlobalesPanel.tsx  # (nuevo)
│   │   ├── VencimientoCard.tsx            # (nuevo)
│   │   └── TimelineVencimientos.tsx       # (nuevo)
│   └── estadisticas/
│       ├── EstadisticasGlobalesCard.tsx   # (nuevo)
│       └── GraficoUtilidad.tsx            # (nuevo)
│
└── App.tsx                    # (modificar) agregar rutas
```

---

## PARTE 4: ORDEN DE IMPLEMENTACIÓN

| # | Tarea | Archivos | Esfuerzo |
|---|-------|----------|----------|
| 1 | Botón "Generar Resumen" en InteligenciaPanel | `InteligenciaPanel.tsx`, `expedientesApi.ts` | 1h |
| 2 | Botón "Exportar" en MiAnalisisList | `MiAnalisisList.tsx`, `analisisApi.ts` | 30min |
| 3 | Nueva página `/vencimientos` | 4 archivos nuevos + `App.tsx` | 3h |
| 4 | Badge vencimientos en sidebar | `MainLayout.tsx` o similar | 30min |
| 5 | Nueva página `/estadisticas` | 3 archivos nuevos + `App.tsx` | 2h |
| 6 | Mejorar `/destacados` | `DestacadosPage.tsx` | 1h |
| 7 | Grafo de relaciones (opcional) | `RelacionesGraph.tsx` | 4h |
| 8 | Config IA en settings (opcional) | `ConfiguracionIA.tsx` | 2h |

**Total estimado Fases 1-2**: ~8 horas
**Total con Fase 3**: ~14 horas

---

## PARTE 5: ARCHIVOS CLAVE PARA REFERENCIA

| Feature | Frontend | Backend |
|---------|----------|---------|
| Resumen | `InteligenciaPanel.tsx:140+` | `presentation/api/rest/routers/ia.py` |
| Exportar | `MiAnalisisList.tsx` | `presentation/api/rest/routers/analisis.py` |
| Vencimientos | (nuevo) | `presentation/api/rest/routers/procesamiento.py` |
| Estadísticas | (nuevo) | `presentation/api/rest/routers/procesamiento.py` |
| Relaciones | (nuevo) | `presentation/api/rest/routers/ia.py` |

---

## NOTAS IMPORTANTES

1. **MiAnalisisList YA está integrado** como tab "Mi Análisis" en ExpedienteDetallePage
2. **VencimientosExpedientePanel YA existe** como tab "Vencimientos" en ExpedienteDetallePage
3. **EstadisticasExpedientePanel YA existe** como tab "Procesamiento" en ExpedienteDetallePage
4. Lo que FALTA son las **vistas globales** (todos los expedientes) en páginas dedicadas

---

## PARTE 6: DASHBOARD COMO HUB CENTRAL

### Estado Actual del Dashboard
**Ubicación**: `frontend/src/pages/dashboard/DashboardPage.tsx`
**Estado**: Tiene datos de muestra estáticos (hardcoded), no conectado a backend

**Componentes existentes** (con datos falsos):
- `ActivityChart` - Gráfico de actividad últimos 30 días
- `StatsChart` - Gráfico de estadísticas mensuales
- `RecentActivity` - Lista de actividad reciente
- Cards de stats (Expedientes, Workspaces, Activos, Actualizaciones)
- Quick Actions (Extraer, Monitoreo, Workspace, Config PJN)
- System Info (Backend, BD, PJN, Versión)

### Propuesta: Dashboard Funcional con Datos Reales

#### Sección 1: Header con Bienvenida + Hora
```
┌─────────────────────────────────────────────────────────────┐
│ 👋 Bienvenido, {usuario}              📅 Mié 27 Nov - 14:35 │
│ Panel de control - Sistema PJN v6                           │
└─────────────────────────────────────────────────────────────┘
```

#### Sección 2: KPIs Principales (4 cards con datos reales)
```
┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
│ 📁 45      │ │ 🔴 3       │ │ 👁️ 12      │ │ 📊 89%     │
│ Expedients │ │ Vencidos   │ │ Monitoreado│ │ Procesado  │
│ +5 esta sem│ │ ⚠️ URGENTE │ │ activos    │ │ IA         │
└────────────┘ └────────────┘ └────────────┘ └────────────┘
```

**Endpoints a consumir**:
- `GET /api/v1/expedientes/count` (o similar)
- `GET /api/v1/procesamiento/vencimientos/urgentes?dias_adelante=0` (vencidos)
- `GET /api/v1/monitoreo/activos/count`
- `GET /api/v1/procesamiento/estadisticas/globales`

#### Sección 3: Alertas y Vencimientos Urgentes
```
┌─────────────────────────────────────────────────────────────┐
│ ⚠️ VENCIMIENTOS PRÓXIMOS                      [Ver todos →] │
├─────────────────────────────────────────────────────────────┤
│ 🔴 VENCIDO  │ FRE 4542/2021 │ Contestar demanda │ -2 días  │
│ 🟠 CRÍTICO  │ FRE 5087/2021 │ Apelación         │ 1 día    │
│ 🟡 URGENTE  │ CAF 1234/2023 │ Ofrecer prueba    │ 3 días   │
└─────────────────────────────────────────────────────────────┘
```

**Endpoint**: `GET /api/v1/procesamiento/vencimientos/urgentes?dias_adelante=7`

#### Sección 4: Últimos Movimientos (Actividad Real)
```
┌─────────────────────────────────────────────────────────────┐
│ 📋 ÚLTIMOS MOVIMIENTOS                                      │
├─────────────────────────────────────────────────────────────┤
│ 🔔 FRE 4542/2021 - Nueva actuación detectada    │ hace 2h  │
│ ✅ FRE 5087/2021 - Procesamiento IA completado  │ hace 5h  │
│ 📥 CAF 1234/2023 - Expediente extraído          │ ayer     │
│ 🔄 Monitoreo - 12 expedientes revisados         │ 6:00 AM  │
└─────────────────────────────────────────────────────────────┘
```

**Endpoint**: `GET /api/v1/monitoreo/logs?limite=10` (necesita crear/adaptar)

#### Sección 5: Estado del Sistema
```
┌─────────────────────────────────────────────────────────────┐
│ 🖥️ ESTADO DEL SISTEMA                                       │
├─────────────────────────────────────────────────────────────┤
│ ✅ Backend API    │ ✅ MySQL      │ ✅ Qdrant (RAG)        │
│ ✅ Ollama (LLM)   │ ⚠️ PJN (lento)│ ✅ Monitoreo activo    │
└─────────────────────────────────────────────────────────────┘
```

**Endpoints**:
- `GET /api/v1/health` - Estado general
- `GET /api/v1/rag/health` - Estado RAG/Qdrant
- `GET /api/v1/ia/models/current` - Estado Ollama
- `GET /api/v1/monitoreo/estado` - Estado monitoreo

#### Sección 6: Gráficos con Datos Reales
- **Gráfico Actividad**: Actuaciones procesadas por día (últimos 30 días)
- **Gráfico Distribución**: % utilidad (alta/media/baja/nula)

**Endpoint**: `GET /api/v1/procesamiento/estadisticas/globales`

#### Sección 7: Acciones Rápidas (Mejoradas)
```
┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
│ 📥 Extraer │ │ 🔍 Buscar  │ │ 💬 Chat IA │ │ ⚙️ Config  │
│ expediente │ │ RAG        │ │            │ │            │
└────────────┘ └────────────┘ └────────────┘ └────────────┘
```

### Componentes Nuevos para Dashboard

```
frontend/src/components/dashboard/
├── WelcomeHeader.tsx          # Header con hora y fecha
├── KPICards.tsx               # 4 KPIs principales con datos reales
├── VencimientosWidget.tsx     # Mini-lista de vencimientos urgentes
├── UltimosMovimientos.tsx     # Actividad real del sistema
├── SystemHealthPanel.tsx      # Estado de servicios
├── ActivityChart.tsx          # (modificar) datos reales
└── StatsChart.tsx             # (modificar) datos reales
```

### Nueva API para Dashboard

```typescript
// frontend/src/api/dashboardApi.ts (NUEVO)

export interface DashboardStats {
  total_expedientes: number
  expedientes_semana: number
  vencimientos_urgentes: number
  vencimientos_vencidos: number
  expedientes_monitoreados: number
  porcentaje_procesado_ia: number
}

export interface VencimientoUrgente {
  id: number
  expediente_numero: string
  tipo: string
  dias_restantes: number
  nivel_urgencia: 'vencido' | 'critico' | 'urgente' | 'proximo'
  descripcion: string
}

export interface SystemHealth {
  backend: boolean
  database: boolean
  rag: boolean
  ollama: boolean
  monitoreo: boolean
  pjn_last_check?: string
}

export async function getDashboardStats(): Promise<DashboardStats>
export async function getVencimientosUrgentes(limite?: number): Promise<VencimientoUrgente[]>
export async function getSystemHealth(): Promise<SystemHealth>
export async function getUltimosMovimientos(limite?: number): Promise<MovimientoReciente[]>
```

### Backend: Endpoints a Crear/Adaptar

| Endpoint | Estado | Acción |
|----------|--------|--------|
| `GET /api/v1/dashboard/stats` | ❌ No existe | **CREAR** - Consolidar KPIs |
| `GET /api/v1/dashboard/health` | ❌ No existe | **CREAR** - Health completo |
| `GET /api/v1/monitoreo/logs` | ✅ Existe | Adaptar para movimientos |
| `GET /api/v1/procesamiento/vencimientos/urgentes` | ✅ Existe | OK |
| `GET /api/v1/procesamiento/estadisticas/globales` | ✅ Existe | OK |

---

## PARTE 7: ORDEN DE IMPLEMENTACIÓN ACTUALIZADO

### Prioridad 1: Dashboard Funcional (HUB) ✅ COMPLETADO
| # | Tarea | Archivos | Estado |
|---|-------|----------|--------|
| 1 | Crear endpoint `GET /api/v1/dashboard/stats` | `routers/dashboard.py` | ✅ HECHO |
| 2 | Crear endpoint `GET /api/v1/dashboard/health` | `routers/dashboard.py` | ✅ HECHO |
| 3 | Crear `dashboardApi.ts` frontend | `api/dashboardApi.ts` | ✅ HECHO |
| 4 | Implementar `KPICards.tsx` con datos reales | `components/dashboard/` | ✅ HECHO |
| 5 | Implementar `VencimientosWidget.tsx` | `components/dashboard/` | ✅ HECHO |
| 6 | Implementar `SystemHealthPanel.tsx` | `components/dashboard/` | ✅ HECHO |
| 7 | Refactorizar `DashboardPage.tsx` | `pages/dashboard/` | ✅ HECHO |

### Prioridad 2: Quick Wins ✅ COMPLETADO
| # | Tarea | Esfuerzo | Estado |
|---|-------|----------|--------|
| 8 | Botón "Generar Resumen" en InteligenciaPanel | 1h | ✅ YA EXISTÍA |
| 9 | Botón "Exportar" en MiAnalisisList | 30min | ✅ YA EXISTÍA |

### Prioridad 2.5: Páginas Nuevas ✅ COMPLETADO
| # | Tarea | Esfuerzo | Estado |
|---|-------|----------|--------|
| A | VencimientosPage con filtros temporales | 2h | ✅ COMPLETADO (2025-11-26) |
| B | EstadisticasPage (dashboard global) | 2h | ✅ COMPLETADO (2025-11-26) |
| C | DestacadosPage mejorado (edición, tags, colores) | 1.5h | ✅ COMPLETADO (2025-11-26) |
| D | Limpieza badges obsoletos en Sidebar | 15min | ✅ COMPLETADO (2025-11-26) |

### Prioridad 3: Features Opcionales ✅ COMPLETADO
| # | Tarea | Esfuerzo | Estado |
|---|-------|----------|--------|
| 10 | Grafo de relaciones | 4h | ✅ COMPLETADO (2025-11-26) |
| 11 | Config IA en settings | 2h | ✅ COMPLETADO (2025-11-26) |

### Prioridad 4: Splash Screen ✅ COMPLETADO
| # | Tarea | Esfuerzo | Estado |
|---|-------|----------|--------|
| 12 | Crear `launcher.py` con integración splash | 1h | ✅ COMPLETADO |
| 13 | Crear `start.sh` script alternativo | 30min | ✅ COMPLETADO |

**Dashboard**: ~7h ✅ COMPLETADO (2025-11-26)
**Quick Wins pendientes**: ~1.5h
**Opcionales pendientes**: ~6h
**Splash pendiente**: ~1.5h

---

## PARTE 8: SPLASH SCREEN DE INICIO (splash.py)

### Descripción
Animación de bienvenida estilo "matrix" usando PySide6 que:
1. Muestra grilla de caracteres aleatorios (50x30)
2. Caracteres cambian aleatoriamente (efecto ruido)
3. Desaparecen gradualmente dejando pantalla vacía
4. Forma la palabra "sintaXis" letra por letra en la esquina inferior derecha
5. Cierra automáticamente después de ~6 segundos

**Ubicación**: `Sistema_v6/Plan_ia/splash.py`
**Dependencia**: `PySide6`

### Opciones de Integración

#### Opción A: Launcher Desktop (Recomendada)
Crear un launcher que muestre splash antes de abrir el navegador:

```python
# Sistema_v6/launcher.py
import subprocess
import webbrowser
import time
from Plan_ia.splash import AnimatedSplashScreen
from PySide6.QtWidgets import QApplication

def main():
    # 1. Mostrar splash
    app = QApplication([])
    splash = AnimatedSplashScreen()
    splash.show()

    # 2. Mientras splash corre, iniciar backend en background
    backend = subprocess.Popen([
        "uvicorn", "presentation.api.rest.main:app",
        "--port", "8000"
    ])

    # 3. Al terminar splash, abrir navegador
    splash.animation_complete.connect(lambda: webbrowser.open("http://localhost:3000"))

    app.exec()

if __name__ == "__main__":
    main()
```

#### Opción B: Solo Splash + Script de Inicio
Integrar en script `start_system.sh` o `start_system.py`:

```bash
#!/bin/bash
# start_system.sh

# Mostrar splash mientras inicia
python Sistema_v6/Plan_ia/splash.py &
SPLASH_PID=$!

# Iniciar backend
cd Sistema_v6
uvicorn presentation.api.rest.main:app --port 8000 &
BACKEND_PID=$!

# Iniciar frontend
cd frontend && npm run dev &
FRONTEND_PID=$!

# Esperar a que splash termine
wait $SPLASH_PID

# Abrir navegador
open http://localhost:3000
```

#### Opción C: Versión Web (Alternativa)
Crear versión JavaScript/CSS del efecto para el frontend React:

```typescript
// frontend/src/components/SplashScreen.tsx
// Recrear el efecto con CSS animations + React
// Mostrar al cargar la app por primera vez
```

### Dependencias Adicionales
```bash
pip install PySide6  # ~200MB, solo para launcher desktop
```

### Integración en requirements.txt
```
# Opcional - solo para launcher desktop
PySide6>=6.5.0
```

### Archivos a Crear/Modificar

| Archivo | Acción | Descripción |
|---------|--------|-------------|
| `Sistema_v6/launcher.py` | CREAR | Script principal que lanza todo |
| `Sistema_v6/Plan_ia/splash.py` | YA EXISTE | Animación splash |
| `Sistema_v6/requirements.txt` | MODIFICAR | Agregar PySide6 opcional |
| `Sistema_v6/start.sh` | CREAR | Script bash alternativo |

### Orden de Implementación (Fase Opcional)

| # | Tarea | Esfuerzo |
|---|-------|----------|
| 12 | Crear `launcher.py` con integración splash | 1h |
| 13 | Crear `start.sh` script alternativo | 30min |
| 14 | (Opcional) Versión web del splash | 3h |

**Total Splash**: ~1.5h (sin versión web)

---

## RESUMEN FINAL DE TIEMPOS

| Fase | Descripción | Esfuerzo |
|------|-------------|----------|
| **Dashboard** | Hub central funcional | ~7h |
| **Quick Wins** | Resumen + Exportar | ~1.5h |
| **Opcionales** | Grafo + Config IA | ~6h |
| **Splash** | Launcher desktop | ~1.5h |
| **TOTAL** | | **~16h** |
