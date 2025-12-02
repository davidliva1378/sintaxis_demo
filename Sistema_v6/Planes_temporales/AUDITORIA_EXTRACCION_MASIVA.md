# Auditoría: Sistema de Extracción Masiva

**Fecha:** 2024-12-02
**Tipo:** Auditoría Completa / Review de Flujo
**Alcance:** Frontend, Backend, Persistencia y Ciclo de Vida de Archivos

---

## Resumen Ejecutivo

El sistema de Extracción Masiva permite extraer actuaciones de múltiples expedientes desde el MEV (portal web del poder judicial) en un proceso batch. La auditoría revela **problemas significativos**, siendo los más críticos la **falta de endpoint de descarga**, los **formatos de exportación no implementados** y la **pérdida de sesiones en memoria tras reinicio del servidor**.

### Calificación por Área

| Área | Estado | Calificación |
|------|--------|--------------|
| Inicio de extracción | Funcional | ⭐⭐⭐⭐ |
| Progreso en tiempo real | Funcional (WebSocket + Polling) | ⭐⭐⭐⭐ |
| Listado de expedientes | Funcional | ⭐⭐⭐⭐ |
| Cargar Última Extracción | Funcional | ⭐⭐⭐⭐ |
| Configuración (timeout, reintentos) | **Frontend solo** | ⭐⭐ |
| Controles paginación | **Frontend solo** | ⭐⭐ |
| Formatos exportación (excel,csv,html) | **NO IMPLEMENTADO** | ⭐ |
| Descarga de resultados | **NO FUNCIONA** | ⭐ |
| Persistencia de sesiones | **NO PERSISTE** | ⭐ |
| Pause/Resume | **NO IMPLEMENTADO** | ⭐ |

---

## 0. OPCIONES DE CONFIGURACIÓN (Panel Inicial)

### Opciones Básicas (siempre visibles)
- **Modo invisible (headless)**: Ejecutar sin interfaz gráfica
- **Umbral de errores**: Detener tras N errores consecutivos (1-100)

### Opciones Avanzadas (colapsables)
| Opción | Frontend | Backend | Estado |
|--------|----------|---------|--------|
| **Timeout de página** (5000-60000ms) | ✅ `config.timeout_pagina` | ✅ Recibe en `ConfigExtraccionRequest` | ⚠️ Verificar uso real |
| **Máximo reintentos** (1-10) | ✅ `config.max_reintentos` | ✅ Recibe en `ConfigExtraccionRequest` | ⚠️ Verificar uso real |
| **Formatos exportación** (json/excel/csv/html) | ✅ `config.exportar_formatos` | ❌ **NO existe en backend** | ❌ No implementado |
| **Detener en duplicados** | ✅ `config.detener_en_duplicado` | ✅ Recibe | ⚠️ Verificar uso |
| **Omitir duplicados** | ✅ `config.omitir_duplicados` | ✅ Recibe | ⚠️ Verificar uso |
| **Límite de páginas** | ✅ `config.max_paginas` | ✅ Recibe | ⚠️ Verificar uso |
| **Fecha de corte** | ✅ `config.fecha_corte` | ✅ Recibe | ✅ Se usa |
| **Procesar con PDF** | ✅ `procesarConPDF` | ✅ `procesar_con_pdf` | ✅ Funcional |

### Botones Principales
1. **Cargar Última Extracción**: `GET /api/v1/extraccion-masiva/base` → Carga `listado_base.json`
2. **Iniciar Extracción Masiva Avanzada**: `POST /api/v1/extraccion-masiva/listado`

---

## 1. FLUJO COMPLETO DEL SISTEMA

### 1.1 Diagrama de Flujo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FLUJO DE EXTRACCIÓN MASIVA                            │
└─────────────────────────────────────────────────────────────────────────────┘

FRONTEND (ExtraccionMasivaDialog.tsx)          BACKEND (extraccion_masiva.py)
─────────────────────────────────────          ────────────────────────────────

1. Usuario abre ExtraccionMasivaDialog
   │
   ├─► Configura opciones básicas y avanzadas
   │   (timeout, reintentos, formatos, paginación)
   │
   ├─────────────────────────────────────┐
   │                                     │
   ▼                                     ▼
┌─────────────────────────┐    ┌─────────────────────────────────┐
│ "Cargar Última          │    │ "Iniciar Extracción Masiva      │
│  Extracción"            │    │  Avanzada"                      │
└─────────────────────────┘    └─────────────────────────────────┘
   │                                     │
   └──► GET /base ◄───────────┐          └──► POST /listado
            │                  │                   │
            ▼                  │                   ▼
   Carga listado_base.json    │          ┌────────────────────────────────────┐
   (última extracción)        │          │  ExtraccionMasivaRouter            │
            │                  │          │  - Crea sessionId (UUID)           │
            │                  │          │  - Guarda en _sesiones {}          │
            │                  │          │  - Lanza asyncio.create_task       │
            │                  │          └────────────────────────────────────┘
            │                  │                   │
            │                  │                   ▼
            │                  │          ┌────────────────────────────────────┐
            │                  │          │  ExtractorMasivo (background)      │
            │                  │          │  - Login PJN con credenciales      │
            │                  │          │  - Navega páginas del MEV          │
            │                  │          │  - Extrae listado expedientes      │
            │                  │          │  - Guarda en listado_base.json     │
            │                  │          │  - Compara con BASE anterior       │
            │                  │          └────────────────────────────────────┘
            │                  │                   │
            │                  │◄──────────────────┘
            │                  │     (guarda listado)
            ▼                  │
   ┌─────────────────────────────────────────────────────────────┐
   │  MUESTRA LISTA DE EXPEDIENTES                                │
   │  - ExtraccionReporte (resumen)                               │
   │  - ExtraccionFiltros (filtrar por dependencia, situación)    │
   │  - ExtraccionListado (seleccionar expedientes)               │
   └─────────────────────────────────────────────────────────────┘
            │
            ▼
   Usuario selecciona expedientes y click "Procesar Seleccionados"
            │
            └──► POST /procesar-seleccionados
                       │
                       ▼
                 ┌────────────────────────────────────┐
                 │  GestorBatch (background)          │
                 │  - Por cada expediente:            │
                 │    - Login MEV                     │
                 │    - Descarga actuaciones          │
                 │    - Guarda JSON en data/          │
                 │    - Extrae PDFs si configurado    │
                 │  - Actualiza progreso en sesión    │
                 └────────────────────────────────────┘
            │
            ▼
   Frontend polling cada 1s + WebSocket disponible
   GET /sesion/{id} o WS /sesion/{id}/ws
            │
            ▼
   Cuando estado="completado":
            │
            └──► Frontend llama descargarReporte(formato)
                       │
                       └──► GET /descargar/{sessionId}/{formato}
                                   │
                                   ▼
                            ❌ 404 NOT FOUND
                            (Endpoint NO existe en backend)

   [ARCHIVOS REALES]
   data/actuaciones/{expediente_numero}/json/actuaciones-{numero}.json
   data/extraccion_masiva/listados/listado_base.json
```

---

## 2. PROBLEMAS CRÍTICOS (P0)

### 2.1 Formatos de Exportación No Implementados

**Ubicación:** Frontend muestra opciones, pero backend las ignora

**Frontend (ExtraccionConfiguracion.tsx líneas 131-160):**
```typescript
// Usuario puede seleccionar: json, excel, csv, html
config.exportar_formatos = ['json', 'excel', 'csv']
```

**Backend (ConfigExtraccionRequest):**
```python
class ConfigExtraccionRequest(BaseModel):
    headless: bool = True
    timeout_pagina: int = 30000
    max_reintentos: int = 3
    # ... etc
    # ❌ NO EXISTE: exportar_formatos
```

**Impacto:** Las opciones excel, csv, html que el usuario selecciona se ignoran completamente.

**Solución:**
1. Agregar `exportar_formatos: List[str]` a `ConfigExtraccionRequest`
2. Implementar generadores de exportación (Excel con openpyxl, CSV con csv, HTML con jinja2)
3. Guardar archivos en formatos seleccionados al finalizar extracción

---

### 2.2 Endpoint de Descarga No Existe

**Ubicación:** `extraccion_masiva.py` - El endpoint `/descargar/{sessionId}/{formato}` no está implementado

**Frontend (extraccionStore.ts líneas 413-440):**
```typescript
descargarReporte: async (formato: 'json' | 'excel' | 'csv' | 'html') => {
    const response = await apiClient.get(
        `/api/v1/extraccion-masiva/descargar/${sessionId}/${formato}`,
        { responseType: 'blob' }
    )
    // Crea link de descarga...
}
```

**Backend actual - Endpoints existentes:**
```python
POST /listado                    # ✓ Iniciar extracción listado
POST /procesar-seleccionados     # ✓ Procesar expedientes
GET  /sesion/{id}                # ✓ Obtener estado
GET  /sesiones                   # ✓ Listar sesiones
GET  /base                       # ✓ Cargar última extracción
GET  /listado/{id}/expedientes   # ✓ Obtener expedientes de sesión
WS   /sesion/{id}/ws             # ✓ WebSocket progreso
POST /pausar/{id}                # ⚠️ Retorna 501
POST /reanudar/{id}              # ⚠️ Retorna 501
POST /cancelar/{id}              # ✓ Cancela tarea
GET  /descargar/{id}/{formato}   # ❌ NO EXISTE
```

**Impacto:** Usuario no puede descargar los resultados de la extracción.

**Solución:** Implementar endpoint que:
- Localice archivos de la sesión
- Comprima según formato solicitado
- Retorne como descarga (StreamingResponse)

---

### 2.3 Sesiones Almacenadas en Memoria

**Ubicación:** `extraccion_masiva.py:32`

```python
SESIONES_ACTIVAS: Dict[str, Dict[str, Any]] = {}
```

**Problema:** Las sesiones se pierden al reiniciar el servidor.

**Impacto:**
- Si el servidor reinicia durante extracción, se pierde todo el progreso
- No hay forma de recuperar sesiones anteriores
- Usuario no puede ver historial de extracciones

**Solución:**
- Persistir sesiones en base de datos (tabla `extraccion_masiva_sesiones`)
- O en Redis si se prefiere persistencia temporal
- Guardar: sessionId, estado, progreso, expedientes, timestamps

---

### 2.4 Pause/Resume No Implementados

**Ubicación:** `extraccion_masiva.py:166-186`

```python
@router.post("/pausar/{session_id}")
async def pausar_extraccion(session_id: str):
    # Solo cambia estado a "pausado"
    # Pero GestorBatch NO respeta este flag
    return HTTPException(status_code=501, detail="Pause no implementado")
```

**Problema:** Los botones Pausar/Reanudar en frontend no funcionan.

**Impacto:** Usuario no puede pausar una extracción larga.

**Solución:**
- GestorBatch debe verificar flag `pausado` en cada iteración
- Implementar mecanismo de señalización (Event o similar)
- Guardar checkpoint para resume

---

## 3. PROBLEMAS IMPORTANTES (P1)

### 3.1 Sin Control de Concurrencia

**Problema:** No hay límite de sesiones simultáneas ni mutex para recursos compartidos.

```python
# Cualquier usuario puede iniciar múltiples extracciones
SESIONES_ACTIVAS[session_id] = {...}  # Sin límite
```

**Impacto:**
- Múltiples extracciones pueden sobrecargar el servidor
- Posibles race conditions en acceso a archivos
- Sin límite de requests al MEV (riesgo de ban)

**Solución:**
- Semáforo global para limitar extracciones concurrentes (ej: max 3)
- Rate limiting por usuario
- Queue de extracciones pendientes

---

### 3.2 Usuario ID Hardcodeado

**Ubicación:** `extraccion_masiva.py:74`

```python
usuario_id=1,  # TODO: Obtener del token JWT
```

**Problema:** Todas las extracciones se atribuyen al usuario 1.

**Impacto:**
- Sin trazabilidad de quién inició cada extracción
- Problemas de auditoría
- Monitoreo incorrecto

**Solución:**
- Obtener usuario del token JWT: `current_user: User = Depends(get_current_user)`
- Pasar usuario_id al GestorBatch

---

### 3.3 WebSocket No Implementado

**Ubicación:** Frontend hace polling, no hay WebSocket

```typescript
// ExtraccionMasivaDialog.tsx
useEffect(() => {
  const interval = setInterval(async () => {
    const response = await fetch(`/api/v1/extraccion-masiva/sesion/${sessionId}`);
    // ...
  }, 2000);  // Polling cada 2 segundos
}, [sessionId]);
```

**Problema:** Polling es ineficiente y puede causar lag en UI.

**Impacto:**
- Delay de hasta 2s en actualizaciones
- Carga innecesaria al servidor
- No es tiempo real

**Solución:**
- Implementar WebSocket endpoint `/ws/extraccion-masiva/{session_id}`
- Push de actualizaciones en tiempo real
- Fallback a polling si WS falla

---

### 3.4 Sin Validación de Credenciales MEV Previo

**Problema:** La extracción inicia sin verificar que las credenciales MEV son válidas.

**Flujo actual:**
1. Usuario inicia extracción
2. Gestor intenta login al MEV
3. Si falla, error se registra pero ya se creó sesión

**Solución:**
- Endpoint `/validar-credenciales` que testea login antes de iniciar
- O validar en `/iniciar` antes de crear BackgroundTask

---

### 3.5 Archivos Huérfanos

**Problema:** Si una extracción falla a mitad, quedan archivos parciales sin cleanup.

**Ubicación de archivos:**
```
data/actuaciones/{expediente_numero}/
├── json/
│   └── actuaciones-{numero}.json
├── pdf/
│   └── *.pdf
└── metadata.json
```

**Solución:**
- Marcar archivos de sesión con sessionId
- Cleanup automático de sesiones fallidas (cron job)
- O transaccionalidad: todo o nada

---

## 4. PROBLEMAS MENORES (P2)

### 4.1 Botones Duplicados en UI

**Ubicación:** `ExpedientesPage.tsx:100-114`

**Problema:** Dos botones abren el mismo diálogo de Extracción Masiva.

**Solución:** Eliminar duplicado.

---

### 4.2 Línea Duplicada en Dialog

**Ubicación:** `ExtraccionMasivaDialog.tsx:220-221`

```typescript
setMostrarReporte(true);
setMostrarReporte(true);  // Duplicado
```

**Solución:** Eliminar línea duplicada.

---

### 4.3 Sin Límite de Expedientes por Extracción

**Problema:** Usuario puede intentar extraer miles de expedientes a la vez.

**Solución:**
- Límite configurable (ej: 100 expedientes por sesión)
- Warning si selecciona muchos
- Paginación del procesamiento

---

### 4.4 Logs No Persistentes

**Problema:** Los logs de extracción solo van a consola/archivo de log general.

**Solución:**
- Guardar logs específicos de cada sesión
- Endpoint para ver logs de sesión específica
- Útil para debugging

---

## 5. ARCHIVOS CRÍTICOS A MODIFICAR

### Backend

| Archivo | Problema | Acción |
|---------|----------|--------|
| `presentation/api/rest/routers/extraccion_masiva.py` | Endpoint descarga no existe, sesiones en memoria | Agregar endpoint, migrar a BD |
| `extraccion_masiva/gestor_batch.py` | No respeta pause, sin checkpoints | Implementar pause/resume |
| `infrastructure/persistence/` | Sin tabla de sesiones | Crear `extraccion_sesiones_mysql.py` |

### Frontend

| Archivo | Problema | Acción |
|---------|----------|--------|
| `components/expedientes/ExtraccionMasivaDialog.tsx` | Llama endpoint inexistente, línea duplicada | Corregir URL, eliminar duplicado |
| `pages/expedientes/ExpedientesPage.tsx` | Botones duplicados | Eliminar duplicado |

---

## 6. PLAN DE CORRECCIÓN RECOMENDADO

### Fase 1: Correcciones Críticas (Funcionalidad Básica)

1. **Implementar endpoint de descarga**
   - Crear `GET /descargar/{session_id}/{formato}`
   - Soportar: `json` (ZIP), `csv` (resumen), `xlsx`
   - Comprimir archivos de expedientes procesados

2. **Persistir sesiones en BD**
   - Crear tabla `extraccion_masiva_sesiones`
   - Migrar de `SESIONES_ACTIVAS` dict a MySQL
   - Mantener historial de extracciones

3. **Implementar Pause/Resume real**
   - Flag `should_pause` verificado en cada iteración del gestor
   - Guardar checkpoint (último expediente procesado)
   - Resume desde checkpoint

### Fase 2: Mejoras de Robustez

4. **Control de concurrencia**
   - Semáforo para máx 3 extracciones simultáneas
   - Queue de extracciones pendientes
   - Estado "en_cola" para sesiones

5. **Autenticación correcta**
   - Obtener usuario de JWT
   - Auditoría de quién inició cada extracción

6. **Validación previa de credenciales**
   - Test de login MEV antes de iniciar
   - Error temprano si credenciales inválidas

### Fase 3: Mejoras de UX

7. **WebSocket para progreso real-time**
   - Endpoint `/ws/extraccion-masiva/{session_id}`
   - Push de actualizaciones inmediatas

8. **Cleanup de archivos huérfanos**
   - Job periódico para limpiar extracciones fallidas
   - Marcar archivos con sessionId

9. **Fixes menores de UI**
   - Eliminar botones duplicados
   - Eliminar línea duplicada

---

## 7. ESQUEMA DE BD PROPUESTO

```sql
CREATE TABLE extraccion_masiva_sesiones (
    id VARCHAR(36) PRIMARY KEY,  -- UUID
    usuario_id INT NOT NULL,
    estado ENUM('listando', 'pausado', 'procesando', 'completado', 'error', 'cancelado') DEFAULT 'listando',
    fase VARCHAR(50),
    progreso INT DEFAULT 0,
    total_expedientes INT DEFAULT 0,
    expedientes_procesados INT DEFAULT 0,
    filtros JSON,  -- Criterios de búsqueda usados
    expedientes_data JSON,  -- Lista de expedientes encontrados
    resultados JSON,  -- Resultados del procesamiento
    checkpoint JSON,  -- Para resume: último procesado
    error_mensaje TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

CREATE INDEX idx_sesiones_usuario ON extraccion_masiva_sesiones(usuario_id);
CREATE INDEX idx_sesiones_estado ON extraccion_masiva_sesiones(estado);
```

---

## 8. ENDPOINT DE DESCARGA PROPUESTO

```python
@router.get("/descargar/{session_id}/{formato}")
async def descargar_resultados(
    session_id: str,
    formato: str = Path(..., regex="^(json|csv|xlsx)$"),
    current_user: User = Depends(get_current_user)
):
    """
    Descarga los resultados de una extracción completada.

    Formatos:
    - json: ZIP con todos los JSONs de actuaciones
    - csv: CSV con resumen de expedientes procesados
    - xlsx: Excel con múltiples hojas (resumen + detalles)
    """
    sesion = await get_sesion(session_id)

    if not sesion:
        raise HTTPException(404, "Sesión no encontrada")

    if sesion.estado != "completado":
        raise HTTPException(400, "Extracción no completada")

    if formato == "json":
        # Comprimir JSONs de expedientes procesados
        zip_buffer = crear_zip_actuaciones(sesion.expedientes_data)
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=extraccion_{session_id}.zip"}
        )

    elif formato == "csv":
        csv_content = generar_csv_resumen(sesion)
        return Response(
            csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=resumen_{session_id}.csv"}
        )

    # ... xlsx similar
```

---

## 9. RESUMEN DE HALLAZGOS

### Funciona Correctamente
- Inicio de extracción y creación de sesión
- Obtención de listado de expedientes del MEV
- "Cargar Última Extracción" (`GET /base`)
- Procesamiento de expedientes seleccionados
- Polling de estado desde frontend (cada 1s)
- WebSocket disponible (`/sesion/{id}/ws`)
- Cancelación de extracción (`asyncio.Task.cancel()`)
- Almacenamiento local de JSONs
- Configuración de timeout y reintentos (llega al backend)
- Controles de paginación (llegan al backend)

### No Funciona / No Existe
| Problema | Ubicación | Estado |
|----------|-----------|--------|
| **Formatos exportación (excel/csv/html)** | Frontend lo envía, backend lo ignora | ❌ No implementado |
| **Descarga de resultados** | `GET /descargar/{id}/{formato}` | ❌ Endpoint no existe |
| **Persistencia de sesiones** | `_sesiones: dict` en memoria | ❌ Se pierden al reiniciar |
| **Pause/Resume** | Retornan HTTP 501 | ❌ No implementado |

### Verificar Implementación Real
| Opción | Llega al Backend | ¿Se Usa en GestorBatch/Extractor? |
|--------|------------------|-----------------------------------|
| `timeout_pagina` | ✅ | ⚠️ Verificar |
| `max_reintentos` | ✅ | ⚠️ Verificar |
| `detener_en_duplicado` | ✅ | ⚠️ Verificar |
| `omitir_duplicados` | ✅ | ⚠️ Verificar |
| `max_paginas` | ✅ | ⚠️ Verificar |

### Bugs Menores
- Botones duplicados en ExpedientesPage
- Línea duplicada `setMostrarReporte(true)` en ExtraccionMasivaDialog

### Bug Corregido: Fechas Mostraban Día Anterior (2024-12-02)

**Síntoma:** El frontend mostraba `01/12/2025` cuando el backend devolvía `2025-12-02`

**Causa raíz:** Bug de timezone en JavaScript. La función `formatearFecha` usaba:
```javascript
new Date(fecha).toLocaleDateString('es-AR', {...})
```

Cuando JavaScript parsea `"2025-12-02"` (formato ISO sin hora), lo interpreta como UTC medianoche (`2025-12-02T00:00:00Z`). En Argentina (UTC-3), esto se convierte a `2025-12-01T21:00:00` del día anterior.

**Ubicación:** `ExtraccionMasivaDialog.tsx:365-379`

**Fix aplicado:**
```javascript
const formatearFecha = (fecha: string) => {
  if (!fecha) return '-'
  try {
    // Agregar hora del mediodía para evitar problemas de timezone
    const fechaConHora = fecha.includes('T') ? fecha : `${fecha}T12:00:00`
    return new Date(fechaConHora).toLocaleDateString('es-AR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    })
  } catch (e) {
    return fecha
  }
}
```

**Estado:** ✅ CORREGIDO

---

## 10. PRÓXIMOS PASOS RECOMENDADOS

1. **Implementar endpoint de descarga** - Crítico para que el flujo sea usable
2. **Agregar `exportar_formatos` al backend** - Para que las opciones tengan efecto
3. **Persistir sesiones en BD/Redis** - Para sobrevivir reinicios
4. **Verificar uso real de opciones avanzadas** - Auditar GestorBatch y ExtractorMasivo
5. **Implementar Pause/Resume** - Opcional pero útil para extracciones largas

---

**Fin de Auditoría**