# Informe: Sistema de Vencimientos - Análisis Profundo

**Fecha:** 2024-12-01
**Tipo:** Análisis/Auditoría
**Alcance:** Detección, gestión, configuración y UI de vencimientos

---

## Resumen Ejecutivo

El sistema de vencimientos de sintaXis utiliza un enfoque **híbrido** (regex + LLM) para detectar automáticamente plazos procesales durante la ingesta de actuaciones. El sistema está **funcionalmente completo** en detección y consulta, pero presenta **gaps significativos** en gestión manual, notificaciones y escalabilidad.

### Calificación por Área

| Área | Estado | Calificación |
|------|--------|--------------|
| Detección automática | Funcional | ⭐⭐⭐⭐ |
| Cálculo días hábiles | Correcto | ⭐⭐⭐⭐⭐ |
| Persistencia | Funcional | ⭐⭐⭐⭐ |
| Consultas/Filtros | Completo | ⭐⭐⭐⭐ |
| UI Frontend | Funcional | ⭐⭐⭐ |
| CRUD Manual | Incompleto | ⭐⭐ |
| Notificaciones | No existe | ⭐ |
| Escalabilidad | Limitada | ⭐⭐ |

---

## 1. PROBLEMAS CRÍTICOS (P0)

### 1.1 Calendario de Feriados Estático

**Ubicación:** `core/procesador_pdf/analizador_vencimientos.py`

**Problema:** Los feriados 2024-2025 están hardcodeados. No hay mecanismo para actualizar dinámicamente.

```python
FERIADOS_2024 = [
    date(2024, 1, 1),   # Año Nuevo
    date(2024, 2, 12),  # Carnaval
    # ... solo 2024-2025
]
```

**Impacto:** A partir de 2026, los cálculos de días hábiles serán incorrectos.

**Solución Recomendada:**
- Crear tabla `feriados` en BD
- Endpoint para gestionar feriados
- Cargar feriados dinámicamente al iniciar
- API externa opcional (ej: nager.date)

---

### 1.2 Sin CRUD Manual de Vencimientos

**Problema:** No existen endpoints para:
- Marcar vencimiento como cumplido/atendido
- Editar vencimiento (cambiar fecha, tipo)
- Eliminar vencimiento erróneo
- Crear vencimiento manual

**Impacto:** Usuario no puede gestionar vencimientos detectados incorrectamente ni registrar cumplimiento.

**Endpoints Faltantes:**
```python
PUT  /api/v1/vencimientos/{id}           # Actualizar
PUT  /api/v1/vencimientos/{id}/estado    # Cambiar estado
DELETE /api/v1/vencimientos/{id}         # Eliminar
POST /api/v1/vencimientos                # Crear manual
```

---

### 1.3 Sin Sistema de Notificaciones

**Problema:** No hay alertas automáticas cuando:
- Un vencimiento se acerca (3, 1 día)
- Un vencimiento se vence
- Se detecta nuevo vencimiento urgente

**Impacto:** Usuario debe revisar manualmente el dashboard. Riesgo de perder plazos.

**Componentes Faltantes:**
- Servicio de notificaciones
- Scheduler (background tasks)
- Integración email/push
- Configuración de alertas por usuario

---

### 1.4 Análisis Híbrido Frágil

**Ubicación:** `core/procesador_pdf/analizador_vencimientos.py:_analizar_con_llm()`

**Problema:** Si Ollama no está corriendo, el análisis LLM falla silenciosamente.

```python
except Exception as e:
    print(f"Error en llamada LLM: {e}")
    return []  # Falla silenciosa - pierde vencimientos complejos
```

**Impacto:** Vencimientos que requieren análisis complejo (no matchean regex) no se detectan sin advertencia al usuario.

**Solución:**
- Logging estructurado de fallos
- Flag en resultado indicando si se usó LLM
- Alerta en UI si análisis híbrido falló
- Reintentos con backoff

---

## 2. PROBLEMAS IMPORTANTES (P1)

### 2.1 Patrones Regex Limitados

**Problema:** Solo 6 patrones predefinidos:
1. Cédula electrónica
2. Cédula física
3. Traslado (plazo variable)
4. Alegato (plazo variable)
5. Presentación (plazo variable)
6. Plazo genérico

**No detecta:**
- Apelaciones
- Recursos extraordinarios
- Vistas de causa
- Audiencias programadas
- Plazos de caducidad
- Términos de prueba

**Solución:** Ampliar PATRONES_PLAZO con más tipos procesales.

---

### 2.2 Frontend Sin Store Centralizado

**Problema:** Cada componente maneja estado independiente con useState:
- VencimientosPage
- VencimientosWidget
- VencimientosExpedientePanel

**Impacto:**
- Sin sincronización entre componentes
- Cambios en un tab no se reflejan en otro
- Duplicación de llamadas API

**Solución:** Crear `vencimientosStore.ts` con Zustand.

---

### 2.3 Filtrado Lado Cliente

**Ubicación:** `frontend/src/api/vencimientosApi.ts`

**Problema:** API devuelve hasta 200 registros, filtrado en JavaScript.

```typescript
// vencimientosApi.ts
const response = await apiClient.get('/dashboard/vencimientos-urgentes', {
  params: { limite: 200 }  // Carga todo
});
// Luego filtra en cliente
```

**Impacto:** Ineficiente con datasets grandes. Performance degradada.

**Solución:** Implementar filtros en backend:
```
GET /vencimientos?desde=-7&hasta=30&estado=pendiente&urgencia=critico
```

---

### 2.4 Sin Acciones en UI de Vencimientos

**Problema:** Las tarjetas de vencimiento son solo informativas. No hay botones para:
- Marcar como atendido ✓
- Editar vencimiento ✏️
- Eliminar ❌
- Agregar nota 📝

**Impacto:** Workflow incompleto. Usuario debe ir a otro lugar para gestionar.

---

### 2.5 Inconsistencia de Tipos TypeScript

**Problema:** Dos interfaces similares:
- `VencimientoUrgente` (types/procesamiento.ts)
- `VencimientoUrgenteDashboard` (api/dashboardApi.ts)

**Impacto:** Confusión, posibles bugs de tipado.

**Solución:** Unificar en `types/vencimiento.ts`.

---

## 3. PROBLEMAS MENORES (P2)

### 3.1 Cálculo de Días Hábiles O(n)

**Problema:** Loop día por día para calcular vencimiento.

```python
while dias_transcurridos < plazo_dias:
    fecha_actual += timedelta(days=1)
    if es_dia_habil(fecha_actual):
        dias_transcurridos += 1
```

**Impacto:** Con procesamiento batch de miles de actuaciones, puede ser lento.

**Solución:** Pre-calcular tabla de días hábiles o usar fórmula matemática.

---

### 3.2 Formato de Fechas Inconsistente

**Problema:** Cada componente formatea diferente:
- VencimientosPage: `dd/MM/yyyy`
- VencimientosWidget: `dd MMM yyyy`
- VencimientosExpedientePanel: `dd 'de' MMMM 'de' yyyy`

**Solución:** Crear `formatFechaVencimiento()` centralizada.

---

### 3.3 Sin Validación de Fechas Outliers

**Problema:** No hay validación si fecha calculada es razonable.

```python
# Podría aceptar vencimientos en año 2050 si regex captura mal
fecha_venc = calcular_fecha_vencimiento(fecha_notif, plazo_dias)
# Sin verificar si fecha_notif o fecha_venc están en rango razonable
```

**Solución:** Validar que fechas estén en rango ±2 años.

---

### 3.4 Sin Paginación en Lista

**Problema:** VencimientosPage carga hasta 200 items sin paginación virtual.

**Impacto:** Performance en sistemas con muchos vencimientos.

**Solución:** Implementar paginación o virtualización con react-virtual.

---

### 3.5 Confianza Uniforme

**Problema:** Todos los vencimientos regex = 0.95, LLM = 0.85. Sin ajuste por contexto.

**Impacto:** Imposible priorizar por confiabilidad real.

**Solución:** Score dinámico basado en:
- Cantidad de grupos capturados
- Proximidad a palabras clave
- Longitud del match

---

## 4. MEJORAS SUGERIDAS

### 4.1 Sistema de Notificaciones (Alta Prioridad)

```
┌─────────────────────────────────────────────────────────────────┐
│                   ARQUITECTURA PROPUESTA                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐     ┌──────────────┐     ┌─────────────────┐  │
│  │  Scheduler  │────▶│ AlertService │────▶│ NotificationHub │  │
│  │  (APScheduler)│   │              │     │ - Email         │  │
│  └─────────────┘     └──────────────┘     │ - Push          │  │
│        │                    │              │ - WebSocket     │  │
│        ▼                    ▼              │ - Webhook       │  │
│  ┌─────────────┐     ┌──────────────┐     └─────────────────┘  │
│  │ Cada 1 hora │     │ Vencimientos │                          │
│  │ verificar   │     │ próximos     │                          │
│  │ vencimientos│     │ 3, 1, 0 días │                          │
│  └─────────────┘     └──────────────┘                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Tablas necesarias:**
```sql
CREATE TABLE alertas_vencimientos (
    id INT PRIMARY KEY,
    vencimiento_id INT,
    tipo_alerta ENUM('3_dias', '1_dia', 'hoy', 'vencido'),
    enviada BOOLEAN DEFAULT FALSE,
    fecha_envio DATETIME,
    canal ENUM('email', 'push', 'webhook')
);

CREATE TABLE configuracion_alertas (
    usuario_id INT,
    alertas_email BOOLEAN DEFAULT TRUE,
    alertas_push BOOLEAN DEFAULT TRUE,
    dias_anticipacion JSON DEFAULT '[3, 1, 0]'
);
```

---

### 4.2 Gestión Dinámica de Feriados

**Nuevo endpoint:**
```python
# GET /api/v1/config/feriados?year=2025
# POST /api/v1/config/feriados
# DELETE /api/v1/config/feriados/{id}
```

**UI en Configuración:**
- Calendario visual para marcar feriados
- Import desde API externa
- Gestión de feria judicial

---

### 4.3 Ampliación de Patrones de Detección

**Nuevos tipos sugeridos:**

| Tipo | Patrón | Plazo Default |
|------|--------|---------------|
| APELACION | `apela.*?(\d+)\s*d[ií]as?` | 5 días |
| RECURSO_EXTRAORDINARIO | `recurso.*extraordin` | 10 días |
| VISTA_CAUSA | `vista.*?(\d+)` | Variable |
| AUDIENCIA | `audiencia.*?(\d{1,2})[/-](\d{1,2})` | Fecha fija |
| CADUCIDAD | `caduc.*?(\d+)` | Variable |
| PRUEBA | `prueba.*?(\d+)\s*d[ií]as?` | Variable |

---

### 4.4 Store Centralizado de Vencimientos

```typescript
// vencimientosStore.ts
interface VencimientosState {
  vencimientos: VencimientoUrgente[];
  estadisticas: EstadisticasVencimientos;
  filtros: FiltrosVencimientos;
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchVencimientos: (filtros?: FiltrosVencimientos) => Promise<void>;
  marcarAtendido: (id: number) => Promise<void>;
  eliminar: (id: number) => Promise<void>;
  refetch: () => Promise<void>;
}
```

---

### 4.5 Acciones en Tarjetas de Vencimiento

```tsx
<VencimientoCard>
  {/* ... contenido existente ... */}

  <CardActions>
    <Button onClick={() => marcarAtendido(id)} size="sm">
      <Check /> Atendido
    </Button>
    <Button onClick={() => openEditDialog(id)} size="sm">
      <Edit /> Editar
    </Button>
    <DropdownMenu>
      <DropdownItem onClick={() => eliminar(id)}>
        <Trash /> Eliminar
      </DropdownItem>
      <DropdownItem onClick={() => addNota(id)}>
        <FileText /> Agregar nota
      </DropdownItem>
    </DropdownMenu>
  </CardActions>
</VencimientoCard>
```

---

## 5. ARCHIVOS CRÍTICOS

### Backend
| Archivo | Propósito | Líneas |
|---------|-----------|--------|
| `core/procesador_pdf/analizador_vencimientos.py` | Detección y cálculo | ~630 |
| `core/procesador_pdf/models.py` | Dataclass Vencimiento | ~170 |
| `core/config/vencimientos_config.py` | Configuración | ~200 |
| `application/services/ia/tools_service.py` | Consultas | ~700 |
| `infrastructure/persistence/actuaciones_mysql.py` | Persistencia | ~400 |
| `presentation/api/rest/routers/tools.py` | Endpoints tools | ~250 |
| `presentation/api/rest/routers/dashboard.py` | Endpoints dashboard | ~200 |

### Frontend
| Archivo | Propósito | Líneas |
|---------|-----------|--------|
| `pages/vencimientos/VencimientosPage.tsx` | Página principal | ~432 |
| `components/expedientes/VencimientosExpedientePanel.tsx` | Panel en expediente | ~142 |
| `components/dashboard/VencimientosWidget.tsx` | Widget dashboard | ~210 |
| `components/settings/ConfiguracionVencimientos.tsx` | Configuración | ~259 |
| `api/vencimientosApi.ts` | Cliente API | ~146 |
| `types/procesamiento.ts` | Tipos | ~336 |

---

## 6. PLAN DE IMPLEMENTACIÓN SUGERIDO

### Fase 1: Correcciones Críticas
1. Gestión dinámica de feriados (tabla + endpoints + UI)
2. Endpoints CRUD para vencimientos
3. Logging de fallos de LLM

### Fase 2: Mejoras de UX
4. Store centralizado de vencimientos
5. Acciones en tarjetas (atender, editar, eliminar)
6. Unificación de tipos TypeScript
7. Filtrado en backend

### Fase 3: Notificaciones
8. Servicio de alertas
9. Scheduler de verificación
10. Integración email
11. UI de configuración de alertas

### Fase 4: Escalabilidad
12. Paginación en API y frontend
13. Optimización de cálculo de días hábiles
14. Caché de vencimientos frecuentes

---

## 7. RESUMEN DE HALLAZGOS

### Fortalezas ✅
- Detección automática funcional con regex + LLM
- Cálculo correcto de días hábiles y feriados
- UI informativa con niveles de urgencia visuales
- Configuración de análisis híbrido y términos personalizados
- Múltiples endpoints de consulta

### Debilidades ❌
- Calendario de feriados estático (solo 2024-2025)
- Sin CRUD manual de vencimientos
- Sin sistema de notificaciones/alertas
- Frontend sin store centralizado
- Filtrado ineficiente (lado cliente)
- Patrones regex limitados a 6 tipos

### Riesgos 🔴
- Fallos silenciosos si Ollama no está disponible
- Cálculos incorrectos post-2025
- Usuario puede perder plazos por falta de alertas
- Performance degradada con datasets grandes

---

## 8. INTEGRACIÓN CON MÓDULO AGENDA

### 8.1 Estado Actual de la Agenda

El sistema ya cuenta con infraestructura de agenda parcialmente desarrollada:

**Tablas existentes:**
- `agenda_eventos` - Eventos y tareas del usuario
- `agenda_etiquetas` - Etiquetas personalizadas
- `agenda_evento_etiquetas` - Relación N:N
- `agenda_eventos_completos` - Vista con urgencia calculada

**Tipos de eventos soportados:**
```sql
tipo ENUM('vencimiento', 'audiencia', 'tarea', 'recordatorio', 'otro')
```

**Endpoints existentes (router/agenda.py):**
| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/agenda/eventos` | GET | Listar eventos con filtros |
| `/agenda/eventos/{id}` | GET | Obtener evento |
| `/agenda/eventos` | POST | Crear evento |
| `/agenda/eventos/{id}` | PUT | Actualizar evento |
| `/agenda/eventos/{id}` | DELETE | Eliminar evento |
| `/agenda/eventos/{id}/completar` | POST | Marcar completado |
| `/agenda/resumen` | GET | Estadísticas y próximos |

### 8.2 Gap: Sincronización Vencimientos → Agenda

**Problema:** Los vencimientos detectados NO se registran automáticamente en agenda.

**Estado actual:**
- ✅ Tabla `agenda_eventos` soporta tipo `vencimiento`
- ✅ Campos `expediente_numero` y `actuacion_indice` para vincular
- ❌ **NO HAY** sincronización automática al detectar vencimientos
- ❌ **NO HAY** botón "Agregar a Agenda" en UI de vencimientos
- ❌ **NO HAY** importación masiva de vencimientos a agenda

### 8.3 Propuesta: Sincronización Automática

**Opción A: Sincronización al detectar (recomendado)**
```python
# En analizador_vencimientos.py después de detectar:
async def sincronizar_con_agenda(vencimiento: Vencimiento, user_id: int):
    """Crea evento en agenda automáticamente."""
    await agenda_service.crear_evento(
        user_id=user_id,
        titulo=f"Vencimiento: {vencimiento.tipo.value}",
        descripcion=vencimiento.descripcion,
        fecha_inicio=vencimiento.fecha_vencimiento,
        tipo=TipoEvento.vencimiento,
        prioridad=Prioridad.alta if vencimiento.es_urgente else Prioridad.media,
        expediente_numero=vencimiento.expediente_numero,
        actuacion_indice=vencimiento.actuacion_id,
        recordatorio_minutos=1440  # 24 horas antes
    )
```

**Opción B: Importación manual desde UI**
```tsx
// En VencimientosPage.tsx
<Button onClick={() => importarAAgenda(vencimientosSeleccionados)}>
  <Calendar /> Agregar a Agenda
</Button>
```

**Opción C: Endpoint de importación masiva**
```python
@router.post("/agenda/importar-vencimientos")
async def importar_vencimientos(
    vencimiento_ids: List[int],
    recordatorio_minutos: int = 1440,
    user_id: int = Depends(get_current_user_id)
):
    """Importa vencimientos seleccionados a la agenda."""
```

### 8.4 Propuesta: Acciones en Agenda desde Vencimientos

**Nuevas acciones en tarjeta de vencimiento:**
- 📅 **Agregar a Agenda** - Crea evento tipo vencimiento
- ⏰ **Programar Recordatorio** - Crea evento tipo recordatorio
- 📋 **Crear Tarea** - Crea tarea asociada al vencimiento

**UI propuesta:**
```tsx
<DropdownMenu>
  <DropdownItem onClick={() => agregarAAgenda(vencimiento)}>
    <Calendar /> Agregar a Agenda
  </DropdownItem>
  <DropdownItem onClick={() => programarRecordatorio(vencimiento)}>
    <Bell /> Programar Recordatorio
  </DropdownItem>
  <DropdownItem onClick={() => crearTarea(vencimiento)}>
    <ListTodo /> Crear Tarea
  </DropdownItem>
</DropdownMenu>
```

### 8.5 Implementación Sugerida

**Fase 1: Backend**
1. Endpoint `POST /vencimientos/{id}/agregar-agenda`
2. Endpoint `POST /agenda/importar-vencimientos`
3. Servicio `AgendaVencimientosService` para sincronización

**Fase 2: Frontend**
4. Botones de acción en VencimientosPage
5. Modal de configuración (recordatorio, prioridad)
6. Feedback visual de sincronización

**Fase 3: Automatización (opcional)**
7. Opción de sincronización automática en configuración
8. Sincronizar al detectar vencimientos nuevos

---

## 9. HERRAMIENTAS MCP PARA VENCIMIENTOS

### 9.1 Herramientas Existentes

El servidor MCP ya expone las siguientes herramientas para vencimientos (categoría `vencimientos`):

| Tool | Descripción | Parámetros |
|------|-------------|------------|
| `vencimientos_pendientes` | Lista vencimientos pendientes ordenados por fecha | `expediente_numero?`, `limite?` |
| `vencimientos_urgentes` | Vencimientos próximos a vencer | `dias` (default: 7), `limite?` |
| `vencimientos_vencidos` | Vencimientos pasados de fecha | `expediente_numero?`, `limite?` |
| `proximos_vencimientos` | Calendario agrupado | `dias` (default: 30), `agrupar_por` (dia/semana/mes) |
| `resumen_vencimientos` | Estadísticas generales | - |

### 9.2 Herramientas Relacionadas (otras categorías)

| Tool | Categoría | Uso con Vencimientos |
|------|-----------|----------------------|
| `estadisticas_generales` | estadisticas | Incluye conteo de vencimientos |
| `actividad_reciente` | estadisticas | Timeline con vencimientos |
| `resumen_expediente` | expedientes | Incluye vencimientos del expediente |

### 9.3 Herramientas Propuestas (Nuevas)

**Para gestión de vencimientos:**

| Tool | Descripción | Parámetros |
|------|-------------|------------|
| `crear_vencimiento` | Crear vencimiento manual | `expediente_numero`, `tipo`, `fecha_vencimiento`, `descripcion`, `plazo_dias?` |
| `actualizar_vencimiento` | Modificar vencimiento | `vencimiento_id`, `estado?`, `fecha_vencimiento?`, `descripcion?` |
| `marcar_vencimiento_atendido` | Cambiar estado a cumplido | `vencimiento_id`, `notas?` |
| `eliminar_vencimiento` | Eliminar vencimiento | `vencimiento_id` |

**Para integración con agenda:**

| Tool | Descripción | Parámetros |
|------|-------------|------------|
| `vencimiento_a_agenda` | Registrar vencimiento en agenda | `vencimiento_id`, `recordatorio_minutos?`, `prioridad?` |
| `vencimientos_a_agenda_masivo` | Importar múltiples a agenda | `vencimiento_ids[]`, `recordatorio_minutos?` |
| `crear_tarea_vencimiento` | Crear tarea relacionada | `vencimiento_id`, `titulo`, `descripcion?` |

**Para calendario/feriados:**

| Tool | Descripción | Parámetros |
|------|-------------|------------|
| `obtener_feriados` | Lista de feriados por año | `year` |
| `verificar_dia_habil` | Verificar si fecha es hábil | `fecha` |
| `calcular_vencimiento` | Calcular fecha dado plazo | `fecha_inicio`, `dias`, `dias_habiles?` |

### 9.4 Ejemplo de Uso MCP

**Consultar vencimientos urgentes:**
```json
{
  "tool": "vencimientos_urgentes",
  "arguments": {
    "dias": 3,
    "limite": 10
  }
}
```

**Agregar vencimiento a agenda (propuesto):**
```json
{
  "tool": "vencimiento_a_agenda",
  "arguments": {
    "vencimiento_id": 123,
    "recordatorio_minutos": 1440,
    "prioridad": "alta"
  }
}
```

### 9.5 Implementación de Nuevas Tools

**Archivo:** `sintaxis_mcp/core/tools_registry.py`

```python
# Agregar a categoría VENCIMIENTOS:

ToolDefinition(
    name="crear_vencimiento",
    description="Crea un vencimiento manual para un expediente",
    category=ToolCategory.VENCIMIENTOS,
    parameters={
        "expediente_numero": {"type": "string", "description": "Número de expediente", "required": True},
        "tipo": {"type": "string", "description": "Tipo: cedula_electronica, traslado, etc.", "required": True},
        "fecha_vencimiento": {"type": "string", "description": "Fecha en formato YYYY-MM-DD", "required": True},
        "descripcion": {"type": "string", "description": "Descripción del vencimiento"},
        "plazo_dias": {"type": "integer", "description": "Plazo en días (si aplica)"}
    }
),

ToolDefinition(
    name="vencimiento_a_agenda",
    description="Registra un vencimiento como evento en la agenda del usuario",
    category=ToolCategory.VENCIMIENTOS,
    parameters={
        "vencimiento_id": {"type": "integer", "description": "ID del vencimiento", "required": True},
        "recordatorio_minutos": {"type": "integer", "description": "Minutos antes para recordatorio", "default": 1440},
        "prioridad": {"type": "string", "description": "baja, media, alta, urgente", "default": "alta"}
    }
),
```

**Archivo:** `application/services/ia/tools_service.py`

```python
def crear_vencimiento(
    self,
    expediente_numero: str,
    tipo: str,
    fecha_vencimiento: str,
    descripcion: str = "",
    plazo_dias: int = None
) -> Dict[str, Any]:
    """Crea un vencimiento manual."""
    # Implementación...

def vencimiento_a_agenda(
    self,
    vencimiento_id: int,
    recordatorio_minutos: int = 1440,
    prioridad: str = "alta"
) -> Dict[str, Any]:
    """Registra vencimiento en agenda."""
    # Implementación...
```

---

## 10. PLAN DE IMPLEMENTACIÓN ACTUALIZADO

### Fase 1: Correcciones Críticas ✅ COMPLETADO (2025-12-01)
1. ✅ Gestión dinámica de feriados (tabla + endpoints + UI)
2. ✅ Endpoints CRUD para vencimientos
3. ✅ Logging de fallos de LLM

### Fase 2: Mejoras de UX ✅ COMPLETADO (2025-12-01)
4. ✅ Store centralizado de vencimientos (`vencimientosStore.ts`)
5. ✅ Acciones en tarjetas (atender, cancelar via dropdown)
6. ✅ Unificación de tipos TypeScript (`types/vencimiento.ts`)
7. ✅ Filtrado en backend (cliente API actualizado)

### Fase 3: Integración con Agenda ✅ COMPLETADO (2025-12-01)
8. ✅ Tabs en AgendaPage para eventos y vencimientos
9. ✅ Estadísticas combinadas
10. ✅ VencimientoCard con acciones integradas
11. ✅ Acciones atender/cancelar desde agenda

### Fase 4: Herramientas MCP ✅ COMPLETADO (2025-12-01)
12. ✅ Tool `atender_vencimiento` en `tools.py`
13. ✅ Tool `cancelar_vencimiento` en `tools.py`
14. ✅ Tool `verificar_dia_habil` en `tools.py`
15. ✅ Tool `calcular_vencimiento` en `tools.py`
16. ✅ Tool `feriados/{anio}` en `tools.py`

### Fase 5: Notificaciones ✅ COMPLETADO (2025-12-01)
17. ✅ Tablas en BD: `alertas_vencimientos`, `configuracion_alertas`, `notificaciones`
18. ✅ Vistas SQL: `v_alertas_pendientes`, `v_estadisticas_notificaciones`
19. ✅ `AlertasService` - Servicio de alertas con verificación de vencimientos
20. ✅ `AlertasRepository` - CRUD alertas, notificaciones y configuración
21. ✅ `VencimientosRepository` - Consultas de vencimientos para alertas
22. ✅ Router `/api/v1/notificaciones` con endpoints:
    - `GET /` - Listar notificaciones
    - `GET /estadisticas` - Estadísticas de notificaciones
    - `GET /no-leidas/count` - Contador para polling
    - `POST /{id}/leer` - Marcar como leída
    - `POST /leer-todas` - Marcar todas leídas
    - `POST /` - Crear notificación manual
    - `GET /configuracion` - Obtener configuración de alertas
    - `PUT /configuracion` - Actualizar configuración
    - `POST /verificar-vencimientos` - Generar alertas manualmente
    - `DELETE /expiradas` - Limpiar notificaciones expiradas

### Fase 6: Escalabilidad ✅ COMPLETADO (2025-12-01)
23. ✅ Paginación en repositorios (límite/offset)
24. ✅ Paginación con infinite scroll en frontend (`VencimientosPage.tsx`)
    - Instalado `@tanstack/react-virtual` para virtualización
    - Carga inicial de 50 items
    - Botón "Cargar más" para infinite scroll
    - Indicador de total/mostrados
25. ✅ Optimización de cálculo de días hábiles (`feriados_service.py`)
    - Nuevo método `es_dia_habil_optimizado()` con datos pre-cargados
    - Batch loading de feriados con set para búsquedas O(1)
    - Método `calcular_dias_habiles_batch()` para múltiples cálculos
26. ✅ Caché de vencimientos frecuentes (`vencimientos.py`)
    - Clase `VencimientosCache` con TTL de 60 segundos
    - Caché automático en endpoint GET `/vencimientos`
    - Parámetro `use_cache=false` para forzar datos frescos
    - Invalidación automática en operaciones de escritura (POST, PUT, DELETE)

---

## 11. ARCHIVOS CREADOS EN FASE 5

### Backend
| Archivo | Propósito |
|---------|-----------|
| `infrastructure/persistence/migrations/015_crear_tablas_alertas_vencimientos.sql` | Migración SQL |
| `infrastructure/persistence/alertas_repository.py` | Repositorio de alertas |
| `infrastructure/persistence/vencimientos_repository.py` | Repositorio de vencimientos |
| `application/services/alertas_service.py` | Servicio de alertas |
| `presentation/api/rest/routers/notificaciones.py` | Endpoints REST |

### Nota sobre FK
Las tablas `notificaciones` y `configuracion_alertas` tienen FK hacia `usuarios(id)`.
Requieren que existan usuarios registrados en la tabla `usuarios`.

---

**Fin del Informe**
