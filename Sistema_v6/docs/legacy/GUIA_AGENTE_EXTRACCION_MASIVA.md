# 🤖 GUÍA PARA AGENTE: Completar Extracción Masiva - Sistema_v6

**Fecha de creación:** 2025-11-10
**Última actualización:** 2025-11-10
**Estado del proyecto:** 30% completado - Componentes creados pero NO integrados
**Rama actual:** `sintaxis_parcial2`

---

## 📋 RESUMEN EJECUTIVO

### Situación Real Descubierta

**El problema:** Claude Code creó componentes el 2025-11-10 pero **NO los integró**. Los archivos existen pero no se usan.

**Componentes creados pero NO integrados:**
- ✅ `frontend/src/components/FiltradoExpedientesDialog.tsx` (320 líneas)
- ✅ `frontend/src/components/TablaVirtualizada.tsx` (172 líneas)
- ✅ `frontend/src/hooks/useFiltrosExpedientes.ts` (160 líneas)
- ✅ `frontend/src/hooks/useSeleccionMasiva.ts` (153 líneas)

**Verificación:**
```bash
# Buscar si FiltradoExpedientesDialog se importa en algún lado
grep -r "FiltradoExpedientesDialog" frontend/src --include="*.tsx" | grep -v "FiltradoExpedientesDialog.tsx"
# Resultado: NADA - No se usa en ningún lado
```

**ExtraccionMasivaDialog.tsx** tiene su propio filtrado básico (líneas 96-130) que ignora los componentes nuevos.

---

## 🎯 OBJETIVO FINAL

Implementar flujo completo:
```
1. Extraer listado → 2000+ expedientes ✅ (funciona)
2. Filtrar y seleccionar → Usuario elige 45 de 2000 ❌ (componentes no integrados)
3. Procesar seleccionados → Solo 45 ❌ (endpoint no existe)
4. Guardar en sistema → Solo los 45 ❌ (lógica placeholder)
```

---

## 📊 ESTADO ACTUAL DETALLADO

### ✅ FASE 1: Extracción del Listado (100% Completo)

**Backend:**
- `extraccion_masiva/extractor_masivo.py` - ✅ Funcional
- `extraccion_masiva/models.py` - ✅ Completo
- Extrae todas las páginas del PJN automáticamente
- Guarda en: `data/extraccion_masiva/listados/listado_YYYYMMDD_HHMMSS.json`

**Verificar:**
```bash
ls -la Sistema_v6/data/extraccion_masiva/listados/
# Debería mostrar JSONs con listados
```

### ❌ FASE 2: Filtrado y Selección (0% Integrado - Componentes Huérfanos)

**Componentes creados pero NO usados:**
```
frontend/src/components/
├── FiltradoExpedientesDialog.tsx    ← NO IMPORTADO
├── TablaVirtualizada.tsx            ← NO IMPORTADO
└── expedientes/
    └── ExtraccionMasivaDialog.tsx   ← USA SU PROPIO FILTRADO BÁSICO
```

**ExtraccionMasivaDialog.tsx actual:**
- Líneas 96-130: Filtrado básico inline (texto, fuero, situación)
- NO usa `FiltradoExpedientesDialog`
- NO usa `TablaVirtualizada`
- NO usa hooks `useFiltrosExpedientes` ni `useSeleccionMasiva`

### ❌ FASE 3: Procesamiento Selectivo (0% Implementado)

**Backend:**
- `extraccion_masiva/gestor_batch.py`
  - Líneas 172-230: `_procesar_expediente()` es **PLACEHOLDER**
  - Solo hace `await asyncio.sleep(0.5)` y retorna fake data

**API:**
- `presentation/api/rest/routers/extraccion_masiva.py`
  - ❌ NO existe endpoint `/procesar-seleccionados`
  - Solo existen endpoints para extracción, no para procesamiento

**Verificar:**
```bash
grep "procesar-seleccionados" Sistema_v6/presentation/api/rest/routers/extraccion_masiva.py
# Resultado: NADA
```

---

## 🚨 TAREAS PRIORITARIAS

### 🔴 CRÍTICO 1: Copiar Referencia desde Sistema_v5 (30 min)

**Por qué:** Sistema_v5 tiene la lógica REAL de procesamiento de expedientes que necesitamos copiar.

**Comandos:**
```bash
cd /Users/davidalejandroliva/PycharmProjects/sintaXis/Sistema_v6

# Crear estructura
mkdir -p REFERENCIA_SISTEMA_V5/{procesamiento,extraccion,documentacion,scripts}

# Copiar procesador inteligente
cp ../Sistema_v5/generador_documentos/integracion_procesador.py \
   REFERENCIA_SISTEMA_V5/procesamiento/

# Copiar scraping del PJN
cp -r ../Sistema_v5/pjn/scraping REFERENCIA_SISTEMA_V5/extraccion/
cp -r ../Sistema_v5/pjn/parsers REFERENCIA_SISTEMA_V5/extraccion/

# Copiar script completo de extracción
cp ../Sistema_v5/bin/ejecutar_extraccion.py \
   REFERENCIA_SISTEMA_V5/scripts/

# Copiar documentación
cp ../Sistema_v5/MEJORAS_REVISION_2025_01_30.md \
   REFERENCIA_SISTEMA_V5/documentacion/ 2>/dev/null || echo "Archivo no existe"

# Buscar y copiar procesador_pdf si existe
find ../Sistema_v5 -name "*procesador*pdf*" -type f -name "*.py" \
  -exec cp {} REFERENCIA_SISTEMA_V5/procesamiento/ \; 2>/dev/null

# Crear README
cat > REFERENCIA_SISTEMA_V5/README.md << 'EOF'
# Referencia Sistema v5 - Código Funcional

Esta carpeta contiene código del Sistema_v5 que sirve como referencia
para implementar el procesamiento real de expedientes en Sistema_v6.

## Archivos Clave:

### Procesamiento:
- `procesamiento/integracion_procesador.py` - Filtro inteligente de actuaciones
- `procesamiento/*procesador*.py` - Clasificadores y analizadores

### Extracción:
- `extraccion/scraping/` - Módulos de scraping del PJN
- `extraccion/parsers/` - Parsers de HTML del portal

### Scripts:
- `scripts/ejecutar_extraccion.py` - Flujo completo de extracción

## Uso:

**NO ejecutar directamente.** Usar como referencia para:

1. Implementar `_procesar_expediente()` en `extraccion_masiva/gestor_batch.py`
2. Ver cómo buscar expediente por número en el PJN
3. Ver cómo extraer actuaciones completas
4. Ver cómo descargar documentos adjuntos

## Notas:

- Sistema_v5 usa interfaz Tkinter (ignorar)
- Sistema_v6 usa React + FastAPI
- Adaptar la LÓGICA, no copiar literalmente
- Enfocarse en las funciones de scraping y parseo
EOF
```

**Verificar:**
```bash
ls -la REFERENCIA_SISTEMA_V5/
tree REFERENCIA_SISTEMA_V5/ -L 2
```

### 🔴 CRÍTICO 2: Habilitar Router de Extracción Masiva (15 min)

**Archivo:** `presentation/api/rest/main.py`

**Problema:** Router está deshabilitado (línea ~68)

**Solución:**
```python
# ANTES (línea ~68):
from .routers import (
    auth,
    config,
    expedientes,
    # extraccion_masiva,  # Temporalmente deshabilitado por problemas de importación
    health,
    monitoreo,
    workspaces,
)

# DESPUÉS:
from .routers import (
    auth,
    config,
    expedientes,
    extraccion_masiva,  # ← Descomentar
    health,
    monitoreo,
    workspaces,
)

# ANTES (línea ~188):
# app.include_router(
#     extraccion_masiva.router,
#     prefix="/api/v1/expedientes/extraer",
#     tags=["extraccion_masiva"],
# )  # Temporalmente deshabilitado

# DESPUÉS (añadir después de otros routers):
app.include_router(
    extraccion_masiva.router,
    prefix="/api/v1/extraccion-masiva",
    tags=["extraccion_masiva"]
)
```

**Verificar:**
```bash
# Reiniciar backend
# Luego:
curl http://localhost:8000/docs
# Buscar en Swagger UI la sección "extraccion_masiva"
```

### 🔴 CRÍTICO 3: Crear Endpoint de Procesamiento (1-2h)

**Archivo:** `presentation/api/rest/routers/extraccion_masiva.py`

**Añadir nuevo endpoint:**
```python
from typing import List
from pydantic import BaseModel

class ProcesarSeleccionadosRequest(BaseModel):
    """Request para procesar expedientes seleccionados."""
    numeros: List[str]
    opciones: Optional[Dict] = {}

@router.post("/{session_id}/procesar-seleccionados")
async def procesar_expedientes_seleccionados(
    session_id: str,
    request: ProcesarSeleccionadosRequest,
    container: Container = Depends(get_container)
) -> Dict:
    """
    Procesa solo los expedientes seleccionados por el usuario.

    Args:
        session_id: ID de sesión de extracción
        request: Lista de números de expedientes a procesar

    Returns:
        Estado de procesamiento y progreso
    """
    # 1. Obtener use case
    use_case = container.extraccion_masiva_use_case()

    # 2. Crear comando
    command = ProcesarSeleccionadosCommand(
        session_id=session_id,
        numeros_expedientes=request.numeros,
        opciones=request.opciones
    )

    # 3. Ejecutar en background
    background_tasks.add_task(
        use_case.procesar_seleccionados,
        command
    )

    # 4. Retornar inmediatamente
    return {
        "success": True,
        "message": f"Procesando {len(request.numeros)} expedientes",
        "session_id": session_id
    }
```

**Crear DTO del comando:**
```python
# En application/dtos/extraccion_masiva_commands.py
@dataclass
class ProcesarSeleccionadosCommand:
    session_id: str
    numeros_expedientes: List[str]
    opciones: Dict = field(default_factory=dict)
```

### 🔴 CRÍTICO 4: Implementar Procesamiento Real (3-4h)

**Archivo:** `extraccion_masiva/gestor_batch.py`
**Función:** `_procesar_expediente()` (líneas 172-230)

**Estado actual:**
```python
async def _procesar_expediente(self, page, numero_expediente, ...):
    # TODO: IMPLEMENTAR LÓGICA REAL
    await asyncio.sleep(0.5)  # FAKE
    return {"success": True}  # FAKE
```

**Implementar usando REFERENCIA_SISTEMA_V5:**

```python
async def _procesar_expediente(
    self,
    page: Page,
    numero_expediente: str,
    context: BrowserContext,
    browser: Browser,
) -> Dict:
    """
    Procesa un expediente individual extrayendo datos completos.

    Pasos:
    1. Buscar expediente en PJN por número
    2. Navegar a página del expediente
    3. Extraer datos completos (carátula, partes, actuaciones)
    4. Descargar documentos adjuntos
    5. Guardar en repositorio
    """
    try:
        # PASO 1: Buscar expediente
        # Ver: REFERENCIA_SISTEMA_V5/extraccion/scraping/
        await page.goto(URL_BUSQUEDA_PJN)
        await page.fill("#numero_expediente", numero_expediente)
        await page.click("button[type='submit']")
        await page.wait_for_load_state("networkidle")

        # PASO 2: Verificar que se encontró
        resultado = await page.query_selector(".expediente-encontrado")
        if not resultado:
            return {
                "success": False,
                "error": "Expediente no encontrado",
                "numero": numero_expediente
            }

        # PASO 3: Click en el expediente
        await resultado.click()
        await page.wait_for_load_state("networkidle")

        # PASO 4: Extraer datos completos
        # Ver: REFERENCIA_SISTEMA_V5/extraccion/parsers/
        datos = await self._extraer_datos_expediente(page)

        # PASO 5: Extraer actuaciones
        actuaciones = await self._extraer_actuaciones(page)

        # PASO 6: Descargar documentos (opcional)
        if self.config.descargar_documentos:
            documentos = await self._descargar_documentos(page, numero_expediente)

        # PASO 7: Guardar en repositorio
        expediente = Expediente(
            numero=numero_expediente,
            datos=datos,
            actuaciones=actuaciones,
            documentos=documentos if self.config.descargar_documentos else []
        )

        # Usar IExpedienteRepository
        await self.expediente_repository.guardar(expediente)

        return {
            "success": True,
            "numero": numero_expediente,
            "actuaciones_count": len(actuaciones),
            "documentos_count": len(documentos) if self.config.descargar_documentos else 0
        }

    except Exception as e:
        logger.error(f"Error procesando {numero_expediente}: {e}")
        return {
            "success": False,
            "error": str(e),
            "numero": numero_expediente
        }
```

**Métodos auxiliares a implementar:**
```python
async def _extraer_datos_expediente(self, page: Page) -> Dict:
    """Extrae carátula, partes, juzgado, fecha, etc."""
    # Ver REFERENCIA_SISTEMA_V5/extraccion/parsers/expedientes_parser.py
    pass

async def _extraer_actuaciones(self, page: Page) -> List[Dict]:
    """Extrae todas las actuaciones del expediente."""
    # Ver REFERENCIA_SISTEMA_V5/extraccion/parsers/actuaciones_parser.py
    pass

async def _descargar_documentos(self, page: Page, numero: str) -> List[Dict]:
    """Descarga PDFs adjuntos a actuaciones."""
    # Ver REFERENCIA_SISTEMA_V5/extraccion/scraping/
    pass
```

### 🟡 IMPORTANTE 5: Integrar Componentes de Filtrado (2-3h)

**Archivo:** `frontend/src/components/expedientes/ExtraccionMasivaDialog.tsx`

**Problema:** No usa los componentes creados

**Solución: Reemplazar filtrado inline con componente completo**

```tsx
// AÑADIR IMPORT al inicio:
import { FiltradoExpedientesDialog } from '../FiltradoExpedientesDialog'

// ELIMINAR: Filtrado inline (líneas 96-130)
// ELIMINAR: Estado de filtros inline (líneas 52-62)

// REEMPLAZAR etapa de 'filtrado' con:
{etapa === 'filtrado' && (
  <FiltradoExpedientesDialog
    expedientes={expedientesExtraidos}
    isOpen={true}
    onClose={() => {
      setEtapa('config')
      desconectarWebSocket()
    }}
    onConfirmar={handleProcesarSeleccionados}
  />
)}

// AÑADIR función de callback:
const handleProcesarSeleccionados = async (numerosSeleccionados: string[]) => {
  if (!extraccionMasiva.sessionId) {
    console.error('No hay session_id')
    return
  }

  // Llamar al nuevo endpoint
  await useExpedientesStore.getState().procesarExpedientesSeleccionados(
    extraccionMasiva.sessionId,
    numerosSeleccionados
  )

  // Cambiar a etapa de procesamiento
  setEtapa('procesando') // Nuevo estado
}
```

### 🟡 IMPORTANTE 6: Conectar Frontend con Backend (1h)

**Archivo:** `frontend/src/stores/expedientesStore.ts`

**Añadir nueva función:**
```typescript
// Añadir al store:
procesarExpedientesSeleccionados: async (
  sessionId: string,
  numeros: string[]
) => {
  try {
    set({ isProcessing: true, error: null })

    const response = await apiClient.post(
      `/extraccion-masiva/${sessionId}/procesar-seleccionados`,
      { numeros }
    )

    if (response.data.success) {
      // Conectar WebSocket para ver progreso de procesamiento
      const wsUrl = `ws://localhost:8000/api/v1/extraccion-masiva/${sessionId}/ws`
      const ws = new WebSocket(wsUrl)

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        set((state) => ({
          extraccionMasiva: {
            ...state.extraccionMasiva,
            progreso: data.progreso,
            expedientesProcesados: data.procesados,
            mensaje: data.mensaje
          }
        }))
      }

      set({ processingWebSocket: ws })
    }
  } catch (error) {
    set({ error: error.message, isProcessing: false })
  }
}
```

---

## 📁 ARCHIVOS CLAVE

### Backend

| Archivo | Estado | Acción Requerida |
|---------|--------|------------------|
| `presentation/api/rest/main.py` | ⚠️ Router comentado | Descomentar líneas 68 y 188 |
| `presentation/api/rest/routers/extraccion_masiva.py` | ⚠️ Falta endpoint | Añadir `/procesar-seleccionados` |
| `extraccion_masiva/gestor_batch.py` | ❌ Placeholder | Implementar `_procesar_expediente()` |
| `application/dtos/extraccion_masiva_commands.py` | ⚠️ Falta DTO | Crear `ProcesarSeleccionadosCommand` |
| `infrastructure/di_container.py` | ⚠️ Falta repo | Añadir `expediente_repository()` |

### Frontend

| Archivo | Estado | Acción Requerida |
|---------|--------|------------------|
| `frontend/src/components/FiltradoExpedientesDialog.tsx` | ✅ Creado | Integrar en ExtraccionMasivaDialog |
| `frontend/src/components/TablaVirtualizada.tsx` | ✅ Creado | Usado por FiltradoExpedientesDialog |
| `frontend/src/hooks/useFiltrosExpedientes.ts` | ✅ Creado | Usado por FiltradoExpedientesDialog |
| `frontend/src/hooks/useSeleccionMasiva.ts` | ✅ Creado | Usado por FiltradoExpedientesDialog |
| `frontend/src/components/expedientes/ExtraccionMasivaDialog.tsx` | ⚠️ No integrado | Importar y usar FiltradoExpedientesDialog |
| `frontend/src/stores/expedientesStore.ts` | ⚠️ Falta función | Añadir `procesarExpedientesSeleccionados()` |

---

## 🔍 COMANDOS ÚTILES

### Verificar Estado

```bash
# Ver si componentes se usan
cd /Users/davidalejandroliva/PycharmProjects/sintaXis/Sistema_v6
grep -r "FiltradoExpedientesDialog" frontend/src --include="*.tsx" --include="*.ts"

# Ver si endpoint existe
grep "procesar-seleccionados" presentation/api/rest/routers/extraccion_masiva.py

# Ver tamaño de placeholder
sed -n '172,230p' extraccion_masiva/gestor_batch.py

# Verificar router habilitado
grep -A 5 "extraccion_masiva" presentation/api/rest/main.py
```

### Testing

```bash
# Iniciar servidores
cd Sistema_v6
python scripts/iniciar_servidores.py

# O manualmente:
# Terminal 1 - Backend:
PYTHONPATH=/Users/davidalejandroliva/PycharmProjects/sintaXis:$PYTHONPATH \
  /Users/davidalejandroliva/PycharmProjects/sintaXis/.venv1/bin/python \
  -m uvicorn presentation.api.rest.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2 - Frontend:
cd frontend && npm run dev

# Terminal 3 - Test endpoint:
curl -X POST http://localhost:8000/api/v1/extraccion-masiva/test-session/procesar-seleccionados \
  -H "Content-Type: application/json" \
  -d '{"numeros": ["12345/2024", "12346/2024"]}'
```

---

## 📚 DOCUMENTACIÓN DE REFERENCIA

### Documentación Oficial del Proyecto

**Carpeta:** `/Users/davidalejandroliva/PycharmProjects/sintaXis/DOCUMENTACION_EXTRACCION_MASIVA/`

| Archivo | Contenido |
|---------|-----------|
| `RESUMEN_DIAGNOSTICO_Y_PLAN_V2.md` | Diagnóstico DESACTUALIZADO (2025-11-07) |
| `PLAN_COMPLETAR_EXTRACCION_MASIVA_V2.md` | Plan completo V2.1 con 18 tareas |
| `IMPLEMENTACION_EXTRACCION_MASIVA_UNIFICADA.md` | Implementación unificada |
| `ARQUITECTURA_SISTEMA_MONITOREO.md` | Sistema de monitoreo (Fase 4) |

### Documentación del Proyecto

**Carpeta:** `/Users/davidalejandroliva/PycharmProjects/sintaXis/Sistema_v6/`

| Archivo | Contenido |
|---------|-----------|
| `PLAN_EXTRACCION_MASIVA.md` | Plan original (desactualizado) |
| `IMPLEMENTACION_RESUMEN.md` | Resumen de implementación actual |
| `docs/EXTRACCION_MASIVA_EXPEDIENTES.md` | Documentación frontend |
| `VERIFICACION_FASE1.md` | Verificación backend |
| `VERIFICACION_FASE2.md` | Verificación API y frontend |

---

## ⚠️ NOTAS IMPORTANTES

### 1. Sobre el Commit del 2025-11-10

**Commit:** `3783f6e - feat: Implementar Sistema v6 - Extracción Masiva con Filtrado (MVP Fases 1-3)`

**Lo que dice que hace:**
- ✅ FASE 1: Backend API (100%)
- ⚠️ FASE 2: Frontend React/TypeScript (80%)
- ❌ FASE 3: Procesamiento (placeholder)

**Realidad:**
- ✅ Creó componentes de frontend
- ❌ NO los integró en ExtraccionMasivaDialog
- ❌ NO creó endpoint de procesamiento
- ❌ NO implementó `_procesar_expediente()`

### 2. Sobre el Router Deshabilitado

**Comentario en main.py (línea 68):**
```python
# extraccion_masiva,  # Temporalmente deshabilitado por problemas de importación
```

**Verificar qué problema de importación existe antes de habilitar:**
```bash
cd Sistema_v6
python -c "from presentation.api.rest.routers import extraccion_masiva"
# Si da error, resolver primero
```

### 3. Sobre Sistema_v5

**Sistema_v5 existe localmente en:**
```
/Users/davidalejandroliva/PycharmProjects/sintaXis/Sistema_v5/
```

**Tiene código FUNCIONAL de:**
- Procesamiento completo de expedientes
- Clasificación inteligente de actuaciones
- Análisis de vencimientos
- Sistema de monitoreo

**NO copiar todo Sistema_v5, solo lo necesario para FASE 3.**

### 4. Sobre los Hooks Personalizados

**Hooks creados:**
- `useFiltrosExpedientes.ts` - 7 tipos de filtros
- `useSeleccionMasiva.ts` - 5 funciones de selección

**Son reutilizables y bien implementados.** Solo falta integrarlos.

---

## 🎯 CRITERIOS DE ÉXITO

### Flujo Completo Funcional:

1. ✅ Usuario hace clic en "Extracción Masiva"
2. ✅ Backend extrae listado completo (2000+ expedientes)
3. ⭐ Aparece `FiltradoExpedientesDialog` con tabla virtualizada
4. ⭐ Usuario aplica filtros (dependencia, fecha, situación)
5. ⭐ Usuario selecciona 45 de 2000 expedientes
6. ⭐ Usuario hace clic en "Procesar 45 seleccionados"
7. ⭐ Backend procesa SOLO los 45 (no todos)
8. ⭐ Frontend muestra progreso en tiempo real
9. ⭐ Solo 45 expedientes se guardan en sistema
10. ⭐ Usuario puede descargar reportes

### Performance:

- Tabla renderiza 2000+ expedientes sin lag (<100ms)
- Filtros se aplican instantáneamente (<200ms)
- Procesamiento batch con control de errores
- WebSocket actualiza progreso en tiempo real

---

## 🚀 ORDEN DE IMPLEMENTACIÓN RECOMENDADO

**Día 1 (4-5h):**
1. ✅ Copiar REFERENCIA_SISTEMA_V5 (30 min)
2. ✅ Habilitar router en main.py (15 min)
3. ✅ Crear endpoint `/procesar-seleccionados` (2h)
4. ✅ Crear DTO `ProcesarSeleccionadosCommand` (30 min)
5. ✅ Testing básico con curl (30 min)

**Día 2 (6-8h):**
6. ✅ Implementar `_procesar_expediente()` real (4-6h)
7. ✅ Integrar con IExpedienteRepository (1h)
8. ✅ Testing con expedientes reales (1h)

**Día 3 (3-4h):**
9. ✅ Integrar FiltradoExpedientesDialog en ExtraccionMasivaDialog (2h)
10. ✅ Añadir función procesarExpedientesSeleccionados al store (1h)
11. ✅ Testing flujo completo (1h)

**Día 4 (2-3h):**
12. ✅ Pulir UI y UX (1h)
13. ✅ Documentar cambios (30 min)
14. ✅ Testing final y ajustes (1h)

**Total:** 15-20 horas

---

## 📞 CONTACTO Y CONTINUIDAD

### Si necesitas continuar desde donde otro agente dejó:

1. **Lee este archivo completo** (15 min)
2. **Verifica estado actual:**
   ```bash
   cd /Users/davidalejandroliva/PycharmProjects/sintaXis/Sistema_v6
   git status
   git log --oneline -5
   ```
3. **Revisa qué tareas ya se completaron:**
   ```bash
   # Ver si REFERENCIA_SISTEMA_V5 existe
   ls -la REFERENCIA_SISTEMA_V5/

   # Ver si router está habilitado
   grep "extraccion_masiva" presentation/api/rest/main.py

   # Ver si endpoint existe
   grep "procesar-seleccionados" presentation/api/rest/routers/extraccion_masiva.py
   ```
4. **Continúa desde la primera tarea NO completada**

### Si encuentras problemas:

1. **Lee la documentación en:**
   ```
   /DOCUMENTACION_EXTRACCION_MASIVA/
   ```
2. **Revisa el código de referencia en:**
   ```
   Sistema_v6/REFERENCIA_SISTEMA_V5/
   ```
3. **Consulta los logs del backend:**
   ```bash
   # En la terminal donde corre uvicorn
   # Los errores aparecerán ahí
   ```

---

**FIN DE LA GUÍA**

**Última actualización:** 2025-11-10
**Mantenida por:** Claude Code
**Proyecto:** Sistema PJN v6 - Extracción Masiva