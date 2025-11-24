# Plan de Mejoras - Sistema PJN v6

**Fecha de creación:** 2025-11-22
**Última actualización:** 2025-11-22
**Estado:** En progreso

---

## Resumen Ejecutivo

Este documento contiene el plan de mejoras identificadas durante la revisión exhaustiva del Sistema PJN v6. Incluye problemas detectados, mejoras recomendadas y nuevas funcionalidades propuestas, organizadas por fases de implementación.

---

## Estado de Implementación

### Funcionalidades Completadas (de otros planes)

> **Nota:** Las siguientes fases fueron completadas según `PLAN_IMPLEMENTACION_FUNCIONALIDADES.md`:

| Fase | Nombre | Estado | Fecha |
|------|--------|--------|-------|
| 1 | Correcciones Críticas iniciales | ✅ Completada | 2025-11-21 |
| 2 | Visor PDF Modal | ✅ Completada | 2025-11-21 |
| 3 | Mi Análisis | ✅ Completada | 2025-11-21 |
| 4 | Debug PDF Buttons | ✅ Completada | 2025-11-21 |
| 5 | Módulo Agenda | ✅ Completada | 2025-11-21 |
| 6 | Sistema de Escritos | ✅ Completada | 2025-11-21 |
| 7 | Mejoras Mi Análisis | ✅ Completada | 2025-11-21 |
| 8 | Integración IA | ⏳ Pendiente | - |

---

### Fase 1: Correcciones Críticas (Revisión 2025-11-22)

| # | Tarea | Estado | Commit | Notas |
|---|-------|--------|--------|-------|
| 1.1 | Unificar normalización de expedientes | ✅ Completado | 228a830 | Formato único con guiones (FPA-012332-2019) |
| 1.2 | Implementar autenticación de admin | ✅ Completado | 228a830 | verify_superuser() valida is_superuser |
| 1.3 | Agregar token JWT al cliente API | ✅ Completado | 228a830 | Interceptor en client.ts |
| 1.4 | Eliminar dependencias de Sistema_v5 | ✅ Completado | ab407fc | Migrado a core/procesador_pdf y core/generador_documentos |

### Fase 1.5: Consolidación Sistema_v6 (Autosuficiencia)

> **Objetivo:** Hacer que Sistema_v6 sea completamente autosuficiente, eliminando todas las dependencias externas.

#### 1.5.1 Correcciones Críticas (Funcionalidad Rota)

| # | Tarea | Estado | Prioridad | Descripción |
|---|-------|--------|-----------|-------------|
| 1.5.1.1 | Migrar dependencia de Sistema_v4 | ✅ Completado | Crítica | `expedientes_v4.py` en Sistema_v6/core/operaciones/ |
| 1.5.1.2 | Actualizar config/sistema.json | ✅ Completado | Crítica | Rutas actualizadas a Sistema_v6/data/ |
| 1.5.1.3 | Migrar panel_pjn | ✅ Completado | Alta | Módulo completo en Sistema_v6/infrastructure/scrapers/gestion_actuaciones/ |
| 1.5.1.4 | Migrar módulo core/ | ⚠️ Parcial | Alta | gestion_expedientes/ migrado, faltan flujo_inicial/ y modulos_monitor/ |

#### 1.5.2 Consolidación de Documentación

| # | Tarea | Estado | Prioridad | Descripción |
|---|-------|--------|-----------|-------------|
| 1.5.2.1 | Mover archivos .md de raíz | ✅ Completado | Media | 51 archivos en Sistema_v6/docs/ |
| 1.5.2.2 | Consolidar directorios docs | ✅ Completado | Media | Consolidado en docs/ con subdirs extraccion_masiva/, legacy/ |
| 1.5.2.3 | Mover config/ a Sistema_v6 | ✅ Completado | Media | sistema.json, monitor.json, mcp_settings.json |

#### 1.5.3 Limpieza de Directorios Obsoletos

| # | Tarea | Estado | Prioridad | Descripción |
|---|-------|--------|-----------|-------------|
| 1.5.3.1 | Eliminar versiones antiguas | ✅ Completado | Baja | Sistema_v3/, Sistema_v4/ eliminados |
| 1.5.3.2 | Eliminar código no usado | ✅ Completado | Baja | tests/, notificaciones_v2/, ui/, V3/, data/ eliminados |
| 1.5.3.3 | Eliminar archivos de raíz | ✅ Completado | Baja | main.py, menu_main.py, urls_pjn.py eliminados |
| 1.5.3.4 | Manejar backup | ⏳ Pendiente | Baja | backup_reorganizacion.tar.gz (1 GB) |

#### Resumen de Impacto

- **Archivos Python fuera de Sistema_v6:** ~163 archivos
- **Documentación dispersa:** ~40 archivos .md
- **Imports rotos:** 8+ archivos con dependencias externas
- **Rutas hardcoded:** 11 rutas a Sistema_v5

### Fase 2: Seguridad y Estabilidad

| # | Tarea | Estado | Prioridad | Complejidad |
|---|-------|--------|-----------|-------------|
| 2.1 | Implementar Rate Limiting | ✅ Completado | Alta | Moderada |
| 2.2 | Connection Pooling de BD | ⏳ Pendiente | Media | Moderada |
| 2.3 | Mejorar manejo de errores | ⏳ Pendiente | Media | Moderada |
| 2.4 | Centralizar logging | ⏳ Pendiente | Media | Moderada |
| 2.5 | Health checks completos | ⏳ Pendiente | Media | Simple |

### Fase 2.5: Mejoras del Sistema de Monitoreo

> **Contexto:** El sistema de monitoreo actual usa ExtractorMasivo para verificar todos los expedientes (~80 segundos por extracción completa). Se identificaron mejoras para optimizar la UX y funcionalidad.

#### 2.5.1 Problema Actual

El botón "actualizar" en cada `MonitoreoCard` ejecuta `verificarManual()` que:
- Extrae **todos los 2,047 expedientes** del PJN (137 páginas)
- Tarda ~80 segundos
- Verifica los 15 expedientes monitoreados contra el listado completo
- El usuario espera verificación individual, no global

#### 2.5.2 Tareas de Implementación

| # | Tarea | Estado | Prioridad | Complejidad |
|---|-------|--------|-----------|-------------|
| 2.5.1 | Verificación individual por expediente | ⏳ Pendiente | Alta | Moderada |
| 2.5.2 | Endpoint con parámetro opcional `numero_expediente` | ⏳ Pendiente | Alta | Simple |
| 2.5.3 | Actualización inmediata de UI tras verificación | ⏳ Pendiente | Media | Simple |
| 2.5.4 | Badge de cambios sin leer en Header/Sidebar | ⏳ Pendiente | Media | Simple |
| 2.5.5 | Notificaciones en tiempo real (WebSockets) | ⏳ Pendiente | Baja | Compleja |

#### 2.5.3 Propuesta de Solución

**Backend - Endpoint modificado:**
```python
# presentation/api/rest/routers/monitoreo.py
@router.post("/verificar")
async def verificar_manual(
    headless: bool = True,
    numero_expediente: str | None = None,  # Nuevo parámetro opcional
):
    if numero_expediente:
        # Verificación individual usando scraper directo
        # Extrae solo actuaciones del expediente específico
        resultado = await verificar_expediente_individual(numero_expediente, headless)
    else:
        # Verificación global con ExtractorMasivo (actual)
        resultado = await verificar_todos_expedientes(headless)
```

**Frontend - API modificada:**
```typescript
// frontend/src/api/monitoreoApi.ts
verificarManual: (numeroExpediente?: string) => {
  const params = new URLSearchParams()
  if (numeroExpediente) params.append('numero_expediente', numeroExpediente)
  return api.post(`/api/v1/monitoreo/verificar?${params}`)
}

// frontend/src/stores/monitoreoStore.ts
verificarExpediente: async (numero: string) => {
  const response = await monitoreoApi.verificarManual(numero)  // Usa el número
  // ...
}
```

#### 2.5.4 Archivos Afectados

**Backend:**
- `presentation/api/rest/routers/monitoreo.py` - Añadir parámetro al endpoint
- `application/use_cases/monitorear_expedientes_use_case.py` - Lógica de verificación individual
- `presentation/api/rest/schemas/monitoreo_schemas.py` - Actualizar schemas si necesario

**Frontend:**
- `frontend/src/api/monitoreoApi.ts` - Pasar parámetro al endpoint
- `frontend/src/stores/monitoreoStore.ts` - Usar número de expediente en verificación
- `frontend/src/components/monitoreo/MonitoreoCard.tsx` - Pasar número al handler

#### 2.5.5 Mejoras Adicionales de UX

1. **Spinner en botón específico** - Mostrar loading solo en el card que se está verificando
2. **Toast con resultado específico** - "Expediente FPA-012332-2019: sin cambios"
3. **Actualización optimista** - Actualizar timestamp inmediatamente
4. **Badge en Header** - Mostrar contador de cambios sin leer globalmente

#### 2.5.6 Estimación de Impacto

| Mejora | Tiempo actual | Tiempo estimado | Mejora |
|--------|---------------|-----------------|--------|
| Verificación global | ~80s | ~80s | Sin cambio |
| Verificación individual | ~80s | ~5-10s | 8-16x más rápido |

### Fase 2.6: Mejoras Completas del Frontend de Monitoreo

> **Contexto:** Análisis profundo del módulo de Monitoreo reveló estado actual ~60% funcional con múltiples oportunidades de mejora en frontend, UX y funcionalidad.

#### 2.6.1 Arquitectura Actual del Módulo

**Frontend:**
```
Sistema_v6/frontend/src/
├── types/monitoreo.ts                    (Tipos TypeScript)
├── stores/monitoreoStore.ts              (State management con Zustand)
├── api/monitoreoApi.ts                   (Cliente API - 22+ funciones)
├── pages/monitoreo/
│   └── MonitoreoPage.tsx                 (Página principal)
├── components/monitoreo/
│   ├── MonitoreoCard.tsx                 (Card de expediente monitoreado)
│   └── LogsList.tsx                      (Lista de cambios detectados)
└── components/settings/
    └── ConfiguracionMonitoreo.tsx        (Configuración de monitoreo)
```

**Backend:**
```
Sistema_v6/
├── presentation/api/rest/routers/monitoreo.py
├── application/services/monitoreo_service.py
├── infrastructure/persistence/monitoreo_repository.py
└── presentation/api/rest/schemas/monitoreo_schemas.py
```

#### 2.6.2 Fixes Críticos (Prioridad Alta)

| # | Tarea | Estado | Complejidad | Descripción |
|---|-------|--------|-------------|-------------|
| FIX-MON-01 | Mapeo de tipos de cambio | ⏳ Pendiente | Baja | Frontend usa [nueva_actuacion, cambio_estado, nuevo_archivo, modificacion, otro], Backend usa [cambio_situacion, cambio_dependencia, cambio_caratula] |
| FIX-MON-02 | Sincronizar endpoints de configuración | ⏳ Pendiente | Media | ConfiguracionMonitoreo.tsx usa `/api/v1/config/sistema`, MonitoreoStore usa `/api/v1/monitoreo/configuracion` |
| FIX-MON-03 | usuario_id hardcodeado | ⏳ Pendiente | Media | Backend usa `usuario_id=1` para todos los usuarios (línea 310) |

**Detalle FIX-MON-01: Mapeo de tipos de cambio**

**Problema:** Mismatch entre tipos frontend/backend causa que cambios no se muestren correctamente.

**Archivos a modificar:**
- `frontend/src/types/monitoreo.ts` - Actualizar `TipoCambio`
- `frontend/src/stores/monitoreoStore.ts` - Mapear tipos del backend

**Implementación:**
```typescript
// types/monitoreo.ts
export type TipoCambio =
  | 'nueva_actuacion'
  | 'cambio_situacion'    // Antes: cambio_estado
  | 'cambio_dependencia'  // Nuevo
  | 'cambio_caratula'     // Nuevo
  | 'nuevo_archivo'
  | 'modificacion'
  | 'otro'
```

---

**Detalle FIX-MON-02: Sincronizar endpoints de configuración**

**Problema:** Dos fuentes de verdad para configuración de monitoreo.

**Archivos a modificar:**
- `frontend/src/components/settings/ConfiguracionMonitoreo.tsx` - Usar endpoint de monitoreo

**Implementación:**
```typescript
// ConfiguracionMonitoreo.tsx - Cambiar endpoint
const cargarConfiguracion = async () => {
  // Antes: fetch('/api/v1/config/sistema')
  const response = await fetch('/api/v1/monitoreo/configuracion')
  // ...
}
```

---

**Detalle FIX-MON-03: usuario_id hardcodeado**

**Problema:** Todos los usuarios ven los mismos expedientes monitoreados.

**Archivos a modificar:**
- `presentation/api/rest/routers/monitoreo.py` - Obtener usuario del JWT

**Implementación:**
```python
# routers/monitoreo.py
from presentation.api.rest.dependencies import get_current_user

@router.get("/expedientes")
async def listar_expedientes(
    current_user: Usuario = Depends(get_current_user)
):
    # Antes: usuario_id=1
    usuario_id = current_user.id
    return await monitoreo_service.listar_expedientes(usuario_id)
```

#### 2.6.3 Mejoras de UX (Prioridad Media)

| # | Tarea | Estado | Complejidad | Descripción |
|---|-------|--------|-------------|-------------|
| UX-MON-01 | Búsqueda y filtrado avanzado | ⏳ Pendiente | Media | Filtrar expedientes por estado, prioridad, fecha. Buscar en cambios |
| UX-MON-02 | Mejorar MonitoreoCard | ⏳ Pendiente | Baja | Mostrar prioridad, notas, tiempo estimado próxima verificación |
| UX-MON-03 | Historial completo con exportación | ⏳ Pendiente | Baja | Exportar historial a CSV, filtrar por rango de fechas |
| UX-MON-04 | Store con paginación | ⏳ Pendiente | Media | No cargar todo a memoria, paginar en store |
| UX-MON-05 | Agregar expedientes en bulk | ⏳ Pendiente | Media | Importar desde CSV o selección múltiple |

**Detalle UX-MON-01: Búsqueda y filtrado**

**Archivos a crear/modificar:**
- `frontend/src/components/monitoreo/MonitoreoFilters.tsx` - Nuevo componente de filtros
- `frontend/src/pages/monitoreo/MonitoreoPage.tsx` - Integrar filtros
- `frontend/src/stores/monitoreoStore.ts` - Estado de filtros

**Implementación UI:**
```typescript
// MonitoreoFilters.tsx
interface MonitoreoFiltersProps {
  onFilter: (filters: MonitoreoFilterState) => void
}

interface MonitoreoFilterState {
  busqueda: string
  estado: 'todos' | 'activo' | 'pausado' | 'error'
  prioridad: 'todos' | 'alta' | 'media' | 'baja'
  conCambios: boolean
  fechaDesde?: Date
  fechaHasta?: Date
}
```

---

**Detalle UX-MON-02: Mejorar MonitoreoCard**

**Archivos a modificar:**
- `frontend/src/components/monitoreo/MonitoreoCard.tsx`

**Campos adicionales a mostrar:**
- Prioridad (alta/media/baja) con color
- Notas del usuario
- Tiempo estimado próxima verificación
- Progreso si verificación en curso

---

**Detalle UX-MON-03: Historial con exportación**

**Archivos a crear/modificar:**
- `frontend/src/components/monitoreo/LogsList.tsx` - Agregar botón exportar
- `frontend/src/api/monitoreoApi.ts` - Endpoint de exportación
- `presentation/api/rest/routers/monitoreo.py` - Endpoint `/cambios/exportar`

**Implementación backend:**
```python
@router.get("/cambios/exportar")
async def exportar_cambios(
    formato: Literal["csv", "json"] = "csv",
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None
):
    cambios = await monitoreo_service.obtener_cambios(fecha_desde, fecha_hasta)
    if formato == "csv":
        return StreamingResponse(
            generar_csv(cambios),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=cambios.csv"}
        )
    return cambios
```

---

**Detalle UX-MON-05: Agregar expedientes en bulk**

**Archivos a crear/modificar:**
- `frontend/src/components/monitoreo/BulkImportDialog.tsx` - Modal de importación
- `presentation/api/rest/routers/monitoreo.py` - Endpoint `/expedientes/bulk`

**Implementación:**
```python
@router.post("/expedientes/bulk")
async def agregar_expedientes_bulk(
    expedientes: list[str]  # Lista de números de expediente
):
    resultados = []
    for numero in expedientes:
        try:
            exp = await monitoreo_service.agregar_expediente(numero)
            resultados.append({"numero": numero, "status": "ok", "id": exp.id})
        except Exception as e:
            resultados.append({"numero": numero, "status": "error", "error": str(e)})
    return {"total": len(expedientes), "resultados": resultados}
```

#### 2.6.4 Tiempo Real (Prioridad Media-Alta)

| # | Tarea | Estado | Complejidad | Descripción |
|---|-------|--------|-------------|-------------|
| RT-MON-01 | WebSocket para notificaciones | ⏳ Pendiente | Alta | Notificaciones inmediatas sin polling |
| RT-MON-02 | Reemplazar polling 10s | ⏳ Pendiente | Media | Reducir carga en servidor y mejorar UX |

**Detalle RT-MON-01: WebSocket**

**Archivos a crear:**
- `presentation/api/rest/websockets/monitoreo_ws.py` - WebSocket endpoint
- `frontend/src/hooks/useMonitoreoWebSocket.ts` - Hook de conexión WS
- `frontend/src/stores/monitoreoStore.ts` - Integrar WS con store

**Implementación backend:**
```python
# presentation/api/rest/websockets/monitoreo_ws.py
from fastapi import WebSocket, WebSocketDisconnect

class MonitoreoConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, usuario_id: int):
        await websocket.accept()
        if usuario_id not in self.active_connections:
            self.active_connections[usuario_id] = []
        self.active_connections[usuario_id].append(websocket)

    async def broadcast_cambio(self, usuario_id: int, cambio: dict):
        if usuario_id in self.active_connections:
            for ws in self.active_connections[usuario_id]:
                await ws.send_json(cambio)

manager = MonitoreoConnectionManager()

@router.websocket("/ws/{usuario_id}")
async def websocket_endpoint(websocket: WebSocket, usuario_id: int):
    await manager.connect(websocket, usuario_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Manejar mensajes del cliente (ej: ping)
    except WebSocketDisconnect:
        manager.disconnect(websocket, usuario_id)
```

**Implementación frontend:**
```typescript
// hooks/useMonitoreoWebSocket.ts
export function useMonitoreoWebSocket(usuarioId: number) {
  const { agregarCambio } = useMonitoreoStore()

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/api/v1/monitoreo/ws/${usuarioId}`)

    ws.onmessage = (event) => {
      const cambio = JSON.parse(event.data)
      agregarCambio(cambio)
      toast.success(`Nuevo cambio en ${cambio.expediente_numero}`)
    }

    return () => ws.close()
  }, [usuarioId])
}
```

#### 2.6.5 Integraciones (Prioridad Media)

| # | Tarea | Estado | Complejidad | Descripción |
|---|-------|--------|-------------|-------------|
| INT-MON-01 | Dashboard widget | ⏳ Pendiente | Media | Mostrar cambios recientes en página principal |
| INT-MON-02 | Botón "Monitorear" en Expediente | ⏳ Pendiente | Baja | Agregar botón en ExpedienteDetallePage |
| INT-MON-03 | Integración con IA | ⏳ Pendiente | Alta | Análisis automático de cambios detectados |
| INT-MON-04 | Reportes periódicos | ⏳ Pendiente | Media | Enviar resúmenes diarios/semanales |

**Detalle INT-MON-01: Dashboard widget**

**Archivos a crear/modificar:**
- `frontend/src/components/dashboard/CambiosRecientesWidget.tsx` - Nuevo widget
- `frontend/src/pages/DashboardPage.tsx` - Integrar widget

**Implementación:**
```typescript
// CambiosRecientesWidget.tsx
export function CambiosRecientesWidget() {
  const { cambiosRecientes, isLoading } = useMonitoreoStore()

  return (
    <Card>
      <CardHeader>
        <CardTitle>Cambios Recientes</CardTitle>
        <Link to="/monitoreo">Ver todos</Link>
      </CardHeader>
      <CardContent>
        {cambiosRecientes.slice(0, 5).map(cambio => (
          <CambioItem key={cambio.id} cambio={cambio} />
        ))}
      </CardContent>
    </Card>
  )
}
```

---

**Detalle INT-MON-02: Botón "Monitorear"**

**Archivos a modificar:**
- `frontend/src/pages/expedientes/ExpedienteDetallePage.tsx`

**Implementación:**
```typescript
// ExpedienteDetallePage.tsx
const handleAgregarMonitoreo = async () => {
  try {
    await monitoreoApi.agregarExpediente(expediente.numero)
    toast.success('Expediente agregado al monitoreo')
  } catch (error) {
    toast.error('Error al agregar al monitoreo')
  }
}

// En el header del expediente
<Button onClick={handleAgregarMonitoreo}>
  <Eye className="h-4 w-4 mr-2" />
  Monitorear
</Button>
```

---

**Detalle INT-MON-03: Integración con IA**

**Archivos a crear:**
- `application/services/ia/analizador_cambios.py` - Servicio de análisis
- `presentation/api/rest/routers/monitoreo.py` - Endpoint `/cambios/{id}/analizar`

**Funcionalidades:**
- Resumir cambios detectados con LLM
- Detectar patrones en cambios históricos
- Sugerir acciones basadas en tipo de cambio
- Clasificar urgencia del cambio

**Implementación:**
```python
# application/services/ia/analizador_cambios.py
class AnalizadorCambiosService:
    async def analizar_cambio(self, cambio: CambioDetectado) -> AnalisisCambio:
        prompt = f"""
        Analiza el siguiente cambio en un expediente judicial:
        - Tipo: {cambio.tipo_cambio}
        - Fecha: {cambio.fecha_deteccion}
        - Detalles: {json.dumps(cambio.detalles)}

        Proporciona:
        1. Resumen en una oración
        2. Nivel de urgencia (alta/media/baja)
        3. Acciones sugeridas
        """
        return await self.llm_service.generar(prompt)
```

#### 2.6.6 Resumen de Estimaciones

| Categoría | Tareas | Tiempo Total Estimado |
|-----------|--------|----------------------|
| Fixes Críticos | 3 | 4-6 horas |
| Mejoras UX | 5 | 12-16 horas |
| Tiempo Real | 2 | 8-12 horas |
| Integraciones | 4 | 10-14 horas |
| **Total** | **14** | **34-48 horas** |

#### 2.6.7 Orden de Implementación Recomendado

1. **Semana 1:** Fixes Críticos (FIX-MON-01, 02, 03)
2. **Semana 2:** Mejoras UX básicas (UX-MON-01, 02)
3. **Semana 3:** WebSocket y tiempo real (RT-MON-01, 02)
4. **Semana 4:** Integraciones (INT-MON-01, 02, 04)
5. **Semana 5:** Mejoras avanzadas (UX-MON-03, 04, 05, INT-MON-03)

---

### Fase 3: Nuevas Funcionalidades

| # | Tarea | Estado | Prioridad | Complejidad |
|---|-------|--------|-----------|-------------|
| 3.1 | Sistema de notificaciones push | ⏳ Pendiente | Alta | Compleja |
| 3.2 | Exportación de informes PDF/Excel | ⏳ Pendiente | Alta | Moderada |
| 3.3 | Panel de analytics | ⏳ Pendiente | Media | Moderada |
| 3.4 | Sistema de alertas configurables | ⏳ Pendiente | Media | Moderada |
| 3.5 | Búsqueda semántica con RAG | ⏳ Pendiente | Media | Compleja |

### Fase 4: Mejoras Adicionales

| # | Tarea | Estado | Prioridad | Complejidad |
|---|-------|--------|-----------|-------------|
| 4.1 | CI/CD Pipeline | ⏳ Pendiente | Media | Moderada |
| 4.2 | Chat con asistente IA | ⏳ Pendiente | Media | Compleja |
| 4.3 | Integración con calendario | ⏳ Pendiente | Media | Moderada |
| 4.4 | Modo offline / PWA | ⏳ Pendiente | Baja | Moderada |

---

## Problemas Críticos Detectados

### 1. Inconsistencia en Normalización de Expedientes
**Estado:** ✅ RESUELTO

- **Problema:** Diferentes formatos (`_` vs `-`) causaban fallas en JOINs
- **Solución:** Unificar a formato con guiones bajos (`FPA_015960_2018`) para compatibilidad con datos existentes en MySQL
- **Archivos modificados:**
  - `core/domain/expediente_utils.py` - Normalización usa `_` en lugar de `-`
  - `application/services/procesador_actuaciones_service.py`

### 2. Falta de Autenticación en Admin
**Estado:** ✅ RESUELTO

- **Problema:** `verify_superuser()` siempre retornaba `True`
- **Solución:** Implementar validación real de `is_superuser`
- **Archivo modificado:** `presentation/api/rest/routers/admin.py`

### 3. Token JWT no incluido en requests
**Estado:** ✅ RESUELTO

- **Problema:** Cliente API no enviaba Authorization header
- **Solución:** Agregar interceptor de Axios
- **Archivo modificado:** `frontend/src/api/client.ts`

### 4. Dependencia de Sistema_v5
**Estado:** ✅ RESUELTO

- **Problema:** Imports directos de `Sistema_v5.procesador_pdf` y `Sistema_v5.generador_documentos`
- **Solución:** Migrado módulos completos a `Sistema_v6/core/`
- **Archivos creados:**
  - `core/procesador_pdf/` (7 archivos, 82 KB)
  - `core/generador_documentos/` (4 archivos, 36 KB)
- **Archivos actualizados:** 5 archivos con imports actualizados
- **Sistema_v5 eliminado:** ~22 GB liberados

### 5. Falta de Rate Limiting
**Estado:** ✅ COMPLETADO

- **Problema:** API vulnerable a ataques de fuerza bruta
- **Solución:** Implementar slowapi con limiter centralizado
- **Implementado:**
  - `presentation/api/rest/rate_limiter.py` - Limiter centralizado
  - `presentation/api/rest/main.py` - Integración con app
  - `presentation/api/rest/routers/auth.py` - Login 10/min, Register 5/min
  - `presentation/api/rest/routers/expedientes.py` - Extraer 5/min, Filtrar 10/min
  - `presentation/api/rest/routers/procesamiento.py` - Actuación 10/min, Expediente 5/min
  - `presentation/api/rest/routers/escritos.py` - Plantillas 20/min, Escritos 20/min

### 6. Error en escritos.py - Database Settings
**Estado:** ✅ RESUELTO

- **Problema:** `AttributeError: 'Settings' object has no attribute 'database'`
- **Solución:** Usar `os.getenv()` para configuración MySQL
- **Archivo modificado:** `presentation/api/rest/routers/escritos.py`

### 7. Error en LoginPage.tsx - Validación
**Estado:** ✅ RESUELTO

- **Problema:** React intentaba renderizar objeto de error de FastAPI directamente
- **Solución:** Manejar tanto string como array de errores de validación
- **Archivo modificado:** `frontend/src/pages/auth/LoginPage.tsx`

---

## Mejoras Recomendadas - Detalle

### 2.1 Rate Limiting

**Descripción:** Proteger endpoints críticos contra abuso

**Implementación:**
```python
# requirements.txt
slowapi==0.1.9

# main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/v1/auth/login")
@limiter.limit("5/minute")
async def login(...):
    ...
```

**Archivos:**
- `presentation/api/rest/main.py`
- `requirements.txt`

---

### 2.2 Connection Pooling

**Descripción:** Usar pool de conexiones en lugar de crear conexión por request

**Implementación:**
```python
# Usar SQLAlchemy en lugar de mysql-connector directo
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800
)
```

**Archivos:**
- `infrastructure/persistence/expedientes_mysql.py`

---

### 2.3 Centralizar Logging

**Descripción:** Configuración estructurada de logging con JSON

**Implementación:**
```python
# infrastructure/config/logging_config.py
import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "formatters": {
        "json": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/sistema.log",
            "maxBytes": 10485760,
            "backupCount": 5,
            "formatter": "json"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"]
    }
}
```

---

## Nuevas Funcionalidades - Detalle

### 3.1 Sistema de Notificaciones Push

**Descripción:** Notificaciones en tiempo real para eventos críticos

**Componentes:**
1. Backend: WebSocket server
2. Frontend: Service Worker + Push API
3. Base de datos: Tabla de suscripciones

**Casos de uso:**
- Vencimientos próximos (24h, 48h)
- Nuevas actuaciones en expedientes monitoreados
- Cambios de estado en expedientes

**Archivos a crear:**
- `infrastructure/adapters/notifications/push_service.py`
- `presentation/api/rest/routers/notifications.py`
- `frontend/src/components/notifications/`

---

### 3.2 Exportación de Informes

**Descripción:** Generar informes PDF/Excel con estadísticas y línea de tiempo

**Formatos:**
- PDF: Usando ReportLab o WeasyPrint
- Excel: Usando openpyxl o pandas

**Contenido del informe:**
- Datos del expediente
- Línea de tiempo de actuaciones
- Estadísticas de procesamiento
- Vencimientos pendientes
- Entidades extraídas

**Archivos a crear:**
- `application/services/report_generator.py`
- `presentation/api/rest/routers/reports.py`

---

### 3.3 Panel de Analytics

**Descripción:** Dashboard con métricas y visualizaciones

**Métricas:**
- Expedientes por estado
- Actuaciones por tipo/utilidad
- Tendencias temporales
- Distribución de vencimientos

**Tecnologías:**
- Backend: Endpoints de agregación
- Frontend: Recharts o Chart.js

**Archivos a crear:**
- `presentation/api/rest/routers/analytics.py`
- `frontend/src/pages/analytics/AnalyticsPage.tsx`

---

## Configuración del Sistema

### Base de Datos

```
# SQLite (usuarios/autenticación)
data/sistema.db

# MySQL (expedientes/actuaciones)
Host: localhost
Port: 3306
Database: sintaxis
User: root
```

### Servidores

```
# Backend API
URL: http://localhost:8000
Docs: http://localhost:8000/docs

# Frontend
URL: http://localhost:3001

# MCP Server (opcional)
Puerto: 8765
```

### Credenciales de Prueba

```
Usuario: admin
Password: admin123
Email: admin@example.com
Superuser: Sí
```

---

## Instrucciones para Agente IA

### Contexto del Proyecto

Este es un sistema de gestión de expedientes judiciales del Portal Judicial Nacional de Argentina. Implementa:
- Clean Architecture (core, application, infrastructure, presentation)
- FastAPI para backend
- React + TypeScript para frontend
- MySQL para datos de expedientes
- SQLite para autenticación

### Prioridades de Implementación

1. **Alta prioridad:** Tareas marcadas como "Alta" en las tablas
2. **Siempre verificar:** Que los tests pasen y el sistema funcione
3. **Evitar:** Crear archivos innecesarios o documentación excesiva

### Archivos Clave

```
# Backend
Sistema_v6/presentation/api/rest/main.py
Sistema_v6/infrastructure/config/settings.py
Sistema_v6/application/services/

# Frontend
Sistema_v6/frontend/src/App.tsx
Sistema_v6/frontend/src/api/client.ts
Sistema_v6/frontend/src/stores/authStore.ts

# Base de datos
Sistema_v6/infrastructure/persistence/database/
Sistema_v6/infrastructure/persistence/expedientes_mysql.py
```

### Comandos Útiles

```bash
# Iniciar backend
PYTHONPATH=... uvicorn presentation.api.rest.main:app --reload

# Iniciar frontend
cd frontend && npm run dev

# Verificar MySQL
mysql -u root -pSulaco01 sintaxis -e "SELECT COUNT(*) FROM expedientes"

# Correr tests
pytest tests/
```

---

## Historial de Cambios

| Fecha | Versión | Cambios |
|-------|---------|---------|
| 2025-11-22 | 1.0 | Creación inicial del plan |
| 2025-11-22 | 1.1 | Completadas tareas 1.1, 1.2, 1.3 de Fase 1 |
| 2025-11-22 | 1.2 | Integración de 5 planes adicionales del directorio Plan_performance |
| 2025-11-22 | 1.3 | Integración de Plan_directorios (Gestión Directorios Externos) |
| 2025-11-22 | 1.4 | Integración de Plan_expedientes (Paginación y Filtros ~35%) |
| 2025-11-22 | 1.5 | Integración de Plan_ia (Sistema IA ~65%, 8 casos de uso) |
| 2025-11-22 | 1.6 | Integración de Plan_monitor (Monitor Universal ~49%, 5 fases) |
| 2025-11-22 | 1.7 | Fase 1 completada - Migración procesador_pdf/generador_documentos, eliminación Sistema_v5 (~22 GB liberados) |
| 2025-11-22 | 1.8 | Agregada Fase 1.5 - Plan de consolidación Sistema_v6 (autosuficiencia) |
| 2025-11-22 | 1.9 | Fase 2.1 Rate Limiting parcial (auth), fixes críticos: escritos.py, LoginPage.tsx, normalización expedientes |
| 2025-11-22 | 2.0 | Fase 2.1 Rate Limiting COMPLETADA - Todos endpoints críticos protegidos |
| 2025-11-22 | 2.1 | Auditoría completa del plan - Actualización de 25+ tareas con estado real del código |
| 2025-11-23 | 2.2 | Agregar APScheduler a requirements.txt, corregir estado SEC-003 (.env nunca commiteado) |
| 2025-11-23 | 2.3 | SEC-002/004: Implementación revertida - causó error "Field required" en login |
| 2025-11-23 | 2.4 | Fix login Python 3.13: remover future annotations, agregar has_pjn_credentials property |
| 2025-11-23 | 2.5 | Implementar paginación real en GET /expedientes: query params pagina, por_pagina |
| 2025-11-24 | 2.6 | Agregada Fase 2.6 - Mejoras Completas del Frontend de Monitoreo (14 tareas, ~34-48h estimadas) |

---

## Integración con Otros Planes

### Planes Relacionados

| Directorio | Archivo | Descripción | Estado |
|------------|---------|-------------|--------|
| Plan_performance/ | `PLAN_IMPLEMENTACION_FUNCIONALIDADES.md` | Fases 1-7 completadas, Fase 8 (IA) pendiente | Integrado |
| Plan_performance/ | `PLAN_OPTIMIZACION_SISTEMA.md` | 35+ issues de seguridad/rendimiento | Integrado |
| Plan_performance/ | `PLAN_UI_PROCESAMIENTO_EXPEDIENTES.md` | UI de pestañas para detalle expediente | Integrado |
| Plan_performance/ | `MODULO_PROCESADOR_PDF_IMPLEMENTADO.md` | Documentación procesador_pdf v5 | Integrado |
| Plan_performance/ | `MANEJO_SERVIDOR_CAIDO.md` | Health check y manejo de errores PJN | Integrado |
| Plan_directorios/ | `IMPLEMENTACION_GESTION_DIRECTORIOS.md` | Gestión de directorios externos (~5%) | Integrado |
| Plan_expedientes/ | 4 fases + README + ROADMAP | Paginación y filtros expedientes (~35%) | Integrado |
| Plan_ia/ | 6 archivos, 8 casos de uso | Sistema IA completo (~65%) | Integrado |
| Plan_monitor/ | 4 archivos, 5 fases | Monitor Universal (~49%) | Integrado |

---

### Items de PLAN_OPTIMIZACION_SISTEMA.md a Implementar

#### Seguridad Crítica (Prioridad Alta)

| ID | Tarea | Estado | Overlap |
|----|-------|--------|---------|
| SEC-001 | Configurar CORS con orígenes específicos | ✅ Completado | 11 orígenes en settings.py |
| SEC-002 | JWT Secret Key obligatorio en producción | ⏳ Pendiente | Revertido - model_validator causó error de login |
| SEC-003 | Proteger .env del repositorio | ✅ Completado | .env nunca fue commiteado (ya en .gitignore) |
| SEC-004 | Fernet Key obligatorio en producción | ⏳ Pendiente | Revertido - model_validator causó error de login |
| SEC-005 | Verificación permisos admin | ✅ Completado | Tarea 1.2 |
| SEC-006 | Eliminar prints de secretos | ✅ Completado | Solo prints informativos en scripts |
| SEC-007 | Rate Limiting | ✅ Completado | Tarea 2.1 |
| SEC-008 | Usar credenciales por usuario | ⏳ Pendiente | - |

#### Rendimiento (Prioridad Media)

| ID | Tarea | Estado |
|----|-------|--------|
| PERF-001 | Migrar sesiones a Redis | ⏳ Pendiente |
| PERF-002 | Implementar paginación | ⏳ Pendiente |
| PERF-003 | Agregar índices BD | ⏳ Pendiente |
| PERF-004 | Refactorizar ExtraccionMasivaDialog | ⏳ Pendiente |
| PERF-005 | Optimizar re-renders frontend | ⏳ Pendiente |

---

### UI Procesamiento (de PLAN_UI_PROCESAMIENTO_EXPEDIENTES.md)

**Objetivo:** Sistema de pestañas en ExpedienteDetallePage

| Fase | Descripción | Estado | Complejidad |
|------|-------------|--------|-------------|
| 1 | Sistema de Pestañas (@radix-ui/react-tabs) | ⏳ Pendiente | Media |
| 2 | Pestaña de Procesamiento (estadísticas, clasificación) | ⏳ Pendiente | Alta |
| 3 | Indicadores de Estado de Procesamiento | ⏳ Pendiente | Media |
| 4 | Integración con API de procesamiento | ⏳ Pendiente | Media |

**Componentes a crear:**
- `EstadisticasExpedientePanel.tsx`
- `ActuacionesClasificadasList.tsx`
- `VencimientosExpedientePanel.tsx`
- `ProcesamientoStatusBadge.tsx`

---

### Módulo procesador_pdf (Tarea 1.4)

> Ver `MODULO_PROCESADOR_PDF_IMPLEMENTADO.md` para documentación completa

**Estado actual:** Implementado en Sistema_v5 (~2089 líneas Python)

**Componentes:**
- `ExtractorTexto` - Extracción multi-método (PyPDF2, pdfplumber, OCR)
- `ClasificadorActuaciones` - Clasificación por utilidad jurídica
- `AnalizadorVencimientos` - Cálculo días hábiles y feriados
- `DetectorDuplicados` - Detección hash MD5

**Opciones de migración:**
1. **Importación directa:** Agregar Sistema_v5 al PYTHONPATH
2. **Copiar módulo:** `cp -r Sistema_v5/procesador_pdf/ Sistema_v6/core/`

**Archivos afectados en v6:**
- `application/services/procesador_actuaciones_service.py`
- `application/services/extraccion_texto_service.py`
- `extraccion_masiva/gestor_batch.py`

---

### Health Check PJN (de MANEJO_SERVIDOR_CAIDO.md)

**Problema:** Broken pipe cuando PJN está caído sin feedback claro

**Solución propuesta:**
1. Health check previo con reintentos
2. Clasificación de errores específicos
3. Backoff exponencial (30s → 60s → 120s → 240s → 300s)
4. Mensajes claros al usuario

**Archivos a crear:**
- `pjn/health/checker.py` - `PJNHealthChecker`
- `pjn/errors/classifier.py` - `clasificar_error()`
- `pjn/retry/strategy.py` - `RetryStrategy`

**Estado:** Documentado, pendiente implementación

---

### Gestión de Directorios Externos (de Plan_directorios/)

> Ver `Plan_directorios/IMPLEMENTACION_GESTION_DIRECTORIOS.md` para plan completo

**Estado:** PENDIENTE (~5% completado)
**Prioridad:** Media-Alta

**Descripción:** Sistema para asociar directorios externos a expedientes con 4 tipos de asociación (reference, symlink, copy, watch).

**Implementado:**
- Hashing utilities (`core/domain/utils/hashing.py`)
- Base de archivos (`gestor_directorios/archivos_usuario.py`)
- Estructura de directorios con `documentos_usuario/externos`

**Tareas Pendientes:**

| Fase | Tareas | Estimación |
|------|--------|------------|
| Backend | `tipos_externos.py`, `directorios_externos.py`, thumbnails, MIME | 6-8 horas |
| API REST | Router con 5 endpoints, registrar en main.py | 2-3 horas |
| Frontend | types, api, 4 componentes React | 4-5 horas |
| Testing | Tests unitarios y E2E | 2 horas |

**Archivos a crear:**
- `gestor_directorios/tipos_externos.py` - Dataclasses
- `gestor_directorios/directorios_externos.py` - GestorDirectoriosExternos
- `presentation/api/rest/routers/directorios.py` - API endpoints
- `frontend/src/types/directorios.ts`
- `frontend/src/api/directoriosApi.ts`
- `frontend/src/components/expedientes/DirectoriosPanel.tsx`

**Dependencias:** Pillow, python-magic

---

### Módulo Expedientes - Paginación y Filtros (de Plan_expedientes/)

> Ver `Plan_expedientes/` para plan completo (4 fases)

**Estado:** PARCIAL (~55% completado)
**Prioridad:** Alta (afecta rendimiento con 100+ expedientes)

**Problema Crítico:** ~~El backend ignora parámetros de paginación - siempre retorna todos los expedientes.~~ ✅ RESUELTO - Backend ahora soporta `pagina` y `por_pagina`.

**Progreso por Fase:**

| Fase | Descripción | Estado | Progreso |
|------|-------------|--------|----------|
| 1 | Backend Paginación | ✅ Completado | 100% |
| 2 | Frontend Conexión | Parcial | 70% |
| 3 | Filtros Avanzados | No iniciado | 10% |
| 4 | Performance & UX | Parcial | 25% |

**Implementado:**
- Schema `ListarExpedientesResponse` con campos de paginación
- **✅ Query params `pagina`, `por_pagina` en endpoint GET /expedientes**
- **✅ Paginación real con slicing en backend (máx 100 items/página)**
- Frontend conectado a API real
- Componente `ExpedientesFiltros.tsx` (UI)
- Hook `useSeleccionMasiva.ts` (no integrado)
- Componente `TablaVirtualizada.tsx` (no integrado)

**Tareas Pendientes - Alta Prioridad:**

| Tarea | Archivo | Estimación |
|-------|---------|------------|
| Params de filtro en backend | `routers/expedientes.py` | 3h |
| Hook `useDebounce` | `hooks/useDebounce.ts` | 1h |

**Tareas Pendientes - Media Prioridad:**

| Tarea | Archivo | Estimación |
|-------|---------|------------|
| Integrar virtualización | `ExpedientesPage.tsx` | 2h |
| Integrar selección masiva | `ExpedientesPage.tsx` | 3h |
| React Query caching | `expedientesStore.ts` | 3h |

**Archivos a modificar:**
- `presentation/api/rest/routers/expedientes.py`
- `frontend/src/stores/expedientesStore.ts`
- `frontend/src/pages/expedientes/ExpedientesPage.tsx`

---

### Sistema IA (de Plan_ia/)

> Ver `Plan_ia/` para plan completo (8 casos de uso, 29 tools MCP)

**Estado:** ~65% completado
**Prioridad:** Media-Alta

**Servicios Implementados (8):**
- ClasificadorService, NERService, RAGService, LLMService
- EmbeddingsService, HybridSearchService, IAIntegrationService, ToolsService

**Infraestructura Implementada:**
- Vector Store (ChromaDB + BM25)
- MCP Server con 29 herramientas
- 3 migraciones DB (006, 007, 008)
- Frontend: IAPage, AsistenteIAPage, AnalisisIAPanel

**Progreso por Caso de Uso:**

| # | Caso de Uso | Estado | Progreso |
|---|-------------|--------|----------|
| 1 | Clasificación Actuaciones | Implementado | 90% |
| 2 | Extracción NER | Parcial | 60% |
| 3 | Búsqueda RAG | Implementado | 95% |
| 4 | Resumen Documentos | Parcial | 40% |
| 5 | Generación Escritos | Pendiente | 10% |
| 6 | Análisis Sentencias | Pendiente | 5% |
| 7 | Detección Vencimientos | Parcial | 30% |
| 8 | Predicción Tiempos | Pendiente | 0% |

**Pendientes Críticos (Alta Prioridad):**

| Tarea | Archivo | Impacto |
|-------|---------|---------|
| Habilitar NER en producción | `ia_integration_service.py` | Extracción automática entidades |
| Integrar persistencia entidades | `EntidadesRepository` | Guardar NER en DB |
| Implementar cache Redis | Nuevo: `redis_client.py` | Performance embeddings/resúmenes |
| Tests unitarios servicios IA | `tests/unit/application/services/ia/` | Calidad código |

**Funcionalidades Nuevas (Media Prioridad):**

| Funcionalidad | Descripción | Estimación |
|---------------|-------------|------------|
| Generador de Escritos | Plantillas + variables + DOCX export | 2-3 semanas |
| Analizador Sentencias | Detectar + extraer estructura + similares | 1-2 semanas |
| Vencimientos mejorado | NER fechas + días hábiles + calendario | 1 semana |

**Optimizaciones (Baja Prioridad):**
- Dataset anotado (100+ actuaciones) para entrenar ML
- Clasificador ML (LogReg/BERT) vs solo reglas+LLM
- Predicción tiempos procesales (regresión/survival)

---

### Monitor Universal (de Plan_monitor/)

> Ver `Plan_monitor/` para plan completo (5 fases, 56 tests definidos)

**Estado:** ~49% completado
**Prioridad:** Alta (funcionalidad core)

**Implementado:**
- DetectorCambios (4 campos: ultima_actuacion, situacion, dependencia, caratula)
- GestorEstadosExpedientes (activo, pausado, omitido, archivado)
- MonitorSchedulerService con APScheduler
- 37 tests unitarios pasando
- monitoreoApi.ts completo

**Progreso por Fase:**

| Fase | Descripción | Estado | Progreso |
|------|-------------|--------|----------|
| 1 | Backend Completo | Implementado | 100% |
| 2 | Scheduler Continuo | Parcial | 85% |
| 3 | Conectar Frontend | Parcial | 60% |
| 4 | Sistema Reportes | No implementado | 0% |
| 5 | Resiliencia y Testing | No implementado | 0% |

**Correcciones Críticas (Alta Prioridad):**

| Tarea | Archivo | Impacto | Estado |
|-------|---------|---------|--------|
| Agregar APScheduler a requirements.txt | `requirements.txt` | Monitor scheduler funcionando | ✅ Completado |
| Integrar scheduler.stop() en lifespan | `main.py` | Shutdown incorrecto | ⏳ Pendiente |

**Completar Fase 3 - Frontend (8+ TODOs):**
- Reemplazar mock data con llamadas reales en `monitoreoStore.ts`
- Endpoints ya implementados en `monitoreoApi.ts`

**Fase 4 - Sistema de Reportes:**
- Crear `application/services/report_service.py`
- Formatters: JSON, Markdown, HTML
- Endpoints: `/reportes`, `/reportes/{id}`, `/reportes/{id}/descargar/{formato}`

**Fase 5 - Resiliencia y Testing:**
- Circuit breaker (`infrastructure/resilience/circuit_breaker.py`)
- Tests E2E (`tests/e2e/test_monitor_completo.py`)
- Documentación usuario (`docs/MONITOR_USUARIO.md`)

---

## Notas Adicionales

- El archivo `.env` contiene configuración sensible (no commitear)
- Los datos de expedientes están en MySQL, migrados a formato con guiones
- La autenticación usa JWT con tokens de 24 horas
- El usuario `admin` tiene `is_superuser=True`
- El módulo `procesador_pdf` ya está completo en Sistema_v5 (migrar, no reimplementar)

---

## Próximos Pasos Recomendados

### Fase 1 Completada ✅ | Fase 1.5 ~90% ✅ | Fase 2.1 Completada ✅

1. **Alta Prioridad (Seguridad):**
   - **SEC-008:** Implementar credenciales por usuario
   - **Recomendado:** Rotar contraseña MySQL periódicamente

2. **Corto plazo (Rendimiento):**
   - **Tarea 2.2:** Connection Pooling de BD (SQLAlchemy QueuePool)
   - **Tarea 2.3:** Mejorar manejo de errores (exception handlers centralizados)
   - **Paginación real:** Backend ignora query params en /expedientes

3. **Medio plazo (UI/UX):**
   - UI de procesamiento con pestañas
   - Completar paginación backend real
   - Integrar virtualización frontend (TablaVirtualizada.tsx)

4. **Largo plazo:**
   - Panel de analytics
   - Integración IA completa (Fase 8)
   - Sistema de notificaciones push

---

*Documento generado para seguimiento por agente IA - Sistema PJN v6*
*Actualizado: 2025-11-24 - v2.6 - Mejoras completas del Frontend de Monitoreo (14 tareas)*
