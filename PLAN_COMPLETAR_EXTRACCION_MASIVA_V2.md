# 🎯 PLAN COMPLETO V2: Finalizar Implementación de Extracción Masiva

**Fecha de actualización:** 2025-11-07
**Versión:** 2.0 (Con FASE 2 de Filtrado y Selección)
**Rama de trabajo:** `sintaxis_parcial2` → `claude/review-sintaxis-parcial2-011CUuHPSBCZ7juywst29TXV`
**Estado actual:** 30% completado (ajustado con nueva fase)
**Tiempo estimado total:** 18-24 horas

---

## 🔴 CAMBIO CRÍTICO: FLUJO REAL IDENTIFICADO

### ❌ Lo que pensábamos (incorrecto):
```
1. Extracción masiva → Lista completa
2. Procesamiento automático → TODOS los expedientes  ← ERROR
3. Guardar todos en el sistema
```

### ✅ FLUJO REAL (correcto):
```
1. Extracción masiva → Lista completa (2000+ expedientes)
2. ⭐ FILTRADO Y SELECCIÓN → Usuario elige cuáles procesar  ← NUEVA FASE CRÍTICA
3. Procesamiento selectivo → Solo los seleccionados (ej: 45 de 2000)
4. Guardar solo los seleccionados en el sistema
```

**Impacto:** Esta nueva fase es FUNDAMENTAL para la usabilidad del sistema.

---

## 🗺️ ARQUITECTURA COMPLETA ACTUALIZADA

```
┌─────────────────────────────────────────────────────────────────┐
│  FASE 1: EXTRACCIÓN DEL LISTADO COMPLETO                        │
│  ✅ YA IMPLEMENTADO (100%)                                       │
│                                                                   │
│  ExtractorMasivo.extraer_listado_completo()                     │
│  ├─ Navega al PJN con Playwright                                │
│  ├─ Extrae todas las páginas automáticamente                    │
│  ├─ Guarda listado.json (2000+ expedientes)                     │
│  └─ Emite progreso por WebSocket                                │
└──────────────────┬────────────────────────────────────────────────┘
                   │
                   │ Output: data/extraccion_masiva/listados/listado_YYYYMMDD.json
                   │         [2,340 expedientes]
                   ↓
┌─────────────────────────────────────────────────────────────────┐
│  FASE 2: FILTRADO Y SELECCIÓN DE EXPEDIENTES                   │
│  ❌ NO EXISTE - DEBE IMPLEMENTARSE (0%)                         │
│  ⭐ CRÍTICA PARA USABILIDAD                                      │
│                                                                   │
│  Frontend: FiltradoExpedientesDialog.tsx                        │
│  Backend: GET /api/v1/expedientes/extraer/{id}/listado          │
│                                                                   │
│  FUNCIONALIDADES:                                                │
│  ├─ 📊 Visualización de tabla completa                          │
│  │   ├─ Paginación (50/100/200/500 por página)                 │
│  │   ├─ Virtualización para performance                         │
│  │   └─ Vista compacta/expandida                                │
│  │                                                                │
│  ├─ 🔍 Filtros temporales (no persisten)                        │
│  │   ├─ Por fecha (descendente, ascendente, rango)             │
│  │   ├─ Por última actuación (rango)                            │
│  │   ├─ Por dependencia (multi-select)                          │
│  │   ├─ Por situación (multi-select)                            │
│  │   ├─ Orden alfabético (A-Z, Z-A)                             │
│  │   └─ Búsqueda personalizada (texto libre)                    │
│  │                                                                │
│  ├─ ☑️ Selección masiva                                         │
│  │   ├─ Seleccionar todos visibles (página actual)             │
│  │   ├─ Seleccionar todos (todos los expedientes)              │
│  │   ├─ Deseleccionar todos                                     │
│  │   ├─ Invertir selección                                      │
│  │   └─ Seleccionar por condición (custom)                      │
│  │                                                                │
│  ├─ 📊 Agrupación (opcional)                                    │
│  │   ├─ Agrupar por dependencia                                 │
│  │   ├─ Agrupar por situación                                   │
│  │   └─ Agrupar por mes                                         │
│  │                                                                │
│  └─ 📈 Contador en tiempo real                                  │
│      └─ "45 de 2,340 expedientes seleccionados"                 │
│                                                                   │
│  [Botón: "Procesar 45 seleccionados"]                           │
└──────────────────┬────────────────────────────────────────────────┘
                   │
                   │ Output: expedientes_seleccionados: string[] (45 números)
                   ↓
┌─────────────────────────────────────────────────────────────────┐
│  FASE 3: PROCESAMIENTO SELECTIVO                               │
│  ❌ IMPLEMENTAR (0%)                                            │
│                                                                   │
│  Backend: POST /api/v1/expedientes/extraer/{id}/procesar-seleccionados
│  GestorBatch.procesar_lote(expedientes_seleccionados)          │
│                                                                   │
│  Para cada expediente seleccionado (45, no 2,340):              │
│  ├─ Navegar al expediente con Playwright                        │
│  ├─ Extraer actuaciones (metadata básica)                       │
│  ├─ ⚠️ Clasificar actuaciones (DESHABILITADO - sin procesador)  │
│  ├─ ⚠️ Detectar vencimientos (DESHABILITADO - sin analizador)   │
│  ├─ Guardar en repository                                       │
│  ├─ Actualizar estado (PROCESADO/ERROR)                         │
│  └─ Emitir progreso por WebSocket                               │
└──────────────────┬────────────────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────────────┐
│  RESULTADO FINAL                                                │
│                                                                   │
│  ✅ 45 expedientes procesados y guardados en el sistema         │
│  ✅ 2,295 expedientes NO procesados (quedan en listado)         │
│  ✅ Usuario puede repetir FASE 2 para procesar más             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 PLAN DE IMPLEMENTACIÓN - 18 TAREAS (3 FASES)

---

### **FASE 1: BACKEND - ENDPOINTS DE LISTADO** (2-3 horas)

#### **TAREA 1: Crear endpoint para obtener listado completo**

**Archivo:** `Sistema_v6/presentation/api/rest/routers/extraccion_masiva.py`

**Objetivo:** Endpoint para que el frontend obtenga el listado completo tras la extracción.

**Código:**
```python
@router.get("/{session_id}/listado", response_model=Dict)
async def obtener_listado_completo(
    session_id: str,
    use_case: ExtraccionMasivaUseCase = Depends(get_extraccion_use_case),
):
    """
    Obtiene el listado completo de expedientes extraídos.

    Returns:
        {
            "session_id": str,
            "total": int,
            "expedientes": List[Dict]
        }
    """
    try:
        # Obtener sesión
        sesion = await use_case.gestor_sesiones.obtener_sesion(session_id)

        if not sesion:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")

        # Leer listado desde archivo
        listado_path = sesion.get("listado_path")
        if not listado_path or not Path(listado_path).exists():
            raise HTTPException(status_code=404, detail="Listado no encontrado")

        with open(listado_path, "r", encoding="utf-8") as f:
            expedientes = json.load(f)

        # Obtener dependencias únicas para filtros
        dependencias = sorted(list(set(exp.get("dependencia", "") for exp in expedientes)))
        situaciones = sorted(list(set(exp.get("situacion", "") for exp in expedientes)))

        return {
            "session_id": session_id,
            "total": len(expedientes),
            "expedientes": expedientes,
            "metadata": {
                "dependencias": dependencias,
                "situaciones": situaciones,
                "fecha_extraccion": sesion.get("tiempo_inicio"),
            }
        }

    except Exception as e:
        logger.exception(f"Error obteniendo listado de sesión {session_id}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Actualizar ExtractorMasivo:**
```python
# En extractor_masivo.py, al finalizar extraer_listado_completo():

# Guardar listado completo
listado_path = self.listados_dir / f"listado_{self.session_id}.json"
logger.info(f"Guardando listado en {listado_path}")

with open(listado_path, "w", encoding="utf-8") as f:
    json.dump(expedientes, f, indent=2, ensure_ascii=False)

# Actualizar sesión con la ruta del listado
self._emit("fin_listado", {
    "total": len(expedientes),
    "archivo": str(listado_path),
    "listado_path": str(listado_path),  # 🆕 NUEVO
    "paginas_procesadas": paginas_procesadas,
})
```

**Criterios de éxito:**
- ✅ Endpoint retorna listado completo
- ✅ Incluye metadata (dependencias, situaciones)
- ✅ Maneja errores de sesión no encontrada

---

#### **TAREA 2: Crear endpoint para procesar seleccionados**

**Archivo:** `Sistema_v6/presentation/api/rest/routers/extraccion_masiva.py`

**Objetivo:** Endpoint para procesar SOLO los expedientes seleccionados por el usuario.

**Código:**
```python
from pydantic import BaseModel

class ProcesarSeleccionadosRequest(BaseModel):
    """Request para procesar expedientes seleccionados."""
    numeros_expedientes: List[str]  # Lista de números de expediente


@router.post("/{session_id}/procesar-seleccionados")
async def procesar_expedientes_seleccionados(
    session_id: str,
    request: ProcesarSeleccionadosRequest,
    background_tasks: BackgroundTasks,
    use_case: ExtraccionMasivaUseCase = Depends(get_extraccion_use_case),
):
    """
    Procesa SOLO los expedientes seleccionados por el usuario.

    Args:
        session_id: ID de la sesión de extracción
        request: Lista de números de expedientes a procesar

    Returns:
        {
            "session_id": str,
            "total_seleccionados": int,
            "mensaje": str
        }
    """
    try:
        # Validar sesión
        sesion = await use_case.gestor_sesiones.obtener_sesion(session_id)
        if not sesion:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")

        # Obtener listado completo
        listado_path = sesion.get("listado_path")
        if not listado_path or not Path(listado_path).exists():
            raise HTTPException(status_code=404, detail="Listado no encontrado")

        with open(listado_path, "r", encoding="utf-8") as f:
            listado_completo = json.load(f)

        # Filtrar solo los seleccionados
        numeros_set = set(request.numeros_expedientes)
        expedientes_seleccionados = [
            exp for exp in listado_completo
            if exp.get("numero") in numeros_set
        ]

        logger.info(f"Procesando {len(expedientes_seleccionados)} expedientes seleccionados de {len(listado_completo)}")

        # Actualizar sesión
        await use_case.gestor_sesiones.actualizar_progreso(
            session_id,
            estado="procesando_seleccionados",
            fase="procesamiento",
            progreso_total=len(expedientes_seleccionados),
            mensaje=f"Procesando {len(expedientes_seleccionados)} expedientes seleccionados..."
        )

        # Ejecutar procesamiento en background
        config_extractor = ConfigExtraccionMasiva(
            headless=sesion["config"].get("headless", True),
            umbral_errores=sesion["config"].get("umbral_errores", 10),
        )

        background_tasks.add_task(
            use_case.ejecutar_procesamiento_seleccionados,
            session_id=session_id,
            expedientes_seleccionados=expedientes_seleccionados,
            config_extractor=config_extractor,
        )

        return {
            "session_id": session_id,
            "total_seleccionados": len(expedientes_seleccionados),
            "mensaje": f"Iniciando procesamiento de {len(expedientes_seleccionados)} expedientes"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error procesando seleccionados en sesión {session_id}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Agregar método al Use Case:**
```python
# En application/use_cases/extraccion_masiva_use_case.py

async def ejecutar_procesamiento_seleccionados(
    self,
    session_id: str,
    expedientes_seleccionados: List[Dict],
    config_extractor: ConfigExtraccionMasiva,
):
    """
    Ejecutar procesamiento SOLO de expedientes seleccionados.

    Args:
        session_id: ID de la sesión
        expedientes_seleccionados: Lista de expedientes a procesar
        config_extractor: Configuración del extractor
    """
    try:
        logger.info(f"Procesando {len(expedientes_seleccionados)} expedientes seleccionados")

        # Crear callbacks
        callbacks = self.crear_callbacks(session_id)

        # Procesar lote seleccionado con GestorBatch
        from Sistema_v6.extraccion_masiva.gestor_batch import GestorBatch

        gestor = GestorBatch(
            umbral_errores=config_extractor.umbral_errores,
            callback_progreso=lambda data: self._emit_callback(session_id, "progreso_batch", data),
            repository=self.repository,
            gestor_estados=self.gestor_estados,
        )

        # Emitir inicio de batch
        await self.gestor_sesiones.actualizar_progreso(
            session_id,
            fase="procesamiento",
            mensaje=f"Iniciando procesamiento de {len(expedientes_seleccionados)} expedientes..."
        )

        # Procesar
        resumen = await gestor.procesar_lote(
            expedientes=expedientes_seleccionados,
            descargar_adjuntos=False,  # Deshabilitado por ahora
            headless=config_extractor.headless,
        )

        # Finalizar
        resumen_dict = resumen.to_dict()
        await self.gestor_sesiones.finalizar_sesion(session_id, {
            "resumen": resumen_dict,
            "total_seleccionados": len(expedientes_seleccionados),
        })

        logger.info(f"Procesamiento completado: {resumen.exitosos}/{resumen.total} exitosos")

    except Exception as e:
        logger.exception(f"Error en procesamiento seleccionados {session_id}")
        await self.gestor_sesiones.marcar_error(session_id, str(e))
```

**Criterios de éxito:**
- ✅ Solo procesa expedientes seleccionados
- ✅ Ejecuta en background
- ✅ Actualiza progreso por WebSocket
- ✅ Guarda solo los seleccionados

---

### **FASE 2: FRONTEND - FILTRADO Y SELECCIÓN** (8-10 horas) ⭐ CRÍTICA

#### **TAREA 3: Crear componente FiltradoExpedientesDialog**

**Archivo NUEVO:** `Sistema_v6/frontend/src/components/expedientes/FiltradoExpedientesDialog.tsx`

**Objetivo:** Componente principal para filtrado, selección y procesamiento de expedientes.

**Estructura completa:** (Ver código al final de esta tarea)

**Características:**
1. **Tabla con virtualización** (react-virtual) para performance
2. **7 tipos de filtros** temporales
3. **Selección masiva** con 5 funciones
4. **Paginación** con 4 tamaños
5. **Contador en tiempo real** de seleccionados
6. **Agrupación** opcional por dependencia/situación
7. **Búsqueda** con debounce

**Tiempo:** 5-6 horas

**Criterios de éxito:**
- ✅ Renderiza 2000+ expedientes sin lag
- ✅ Filtros funcionan correctamente
- ✅ Selección masiva responsive
- ✅ Paginación fluida

---

#### **TAREA 4: Implementar sistema de filtros**

**Archivo:** `Sistema_v6/frontend/src/hooks/useFiltrosExpedientes.ts`

**Objetivo:** Hook personalizado para manejar todos los filtros.

**Código:**
```typescript
import { useState, useMemo } from 'react';
import { Expediente } from '@/types';

interface Filtros {
  ordenFecha: 'desc' | 'asc' | 'ninguno';
  fechaDesde?: Date;
  fechaHasta?: Date;
  ultimaActuacionDesde?: Date;
  ultimaActuacionHasta?: Date;
  dependencias: string[];
  situaciones: string[];
  ordenAlfabetico: 'az' | 'za' | 'ninguno';
  busqueda: string;
}

export const useFiltrosExpedientes = (expedientes: Expediente[]) => {
  const [filtros, setFiltros] = useState<Filtros>({
    ordenFecha: 'desc',
    dependencias: [],
    situaciones: [],
    ordenAlfabetico: 'ninguno',
    busqueda: '',
  });

  const expedientesFiltrados = useMemo(() => {
    let resultado = [...expedientes];

    // Filtro por fecha de inicio
    if (filtros.fechaDesde || filtros.fechaHasta) {
      resultado = resultado.filter(exp => {
        const fecha = parseDate(exp.fecha_inicio);
        if (filtros.fechaDesde && fecha < filtros.fechaDesde) return false;
        if (filtros.fechaHasta && fecha > filtros.fechaHasta) return false;
        return true;
      });
    }

    // Filtro por última actuación
    if (filtros.ultimaActuacionDesde || filtros.ultimaActuacionHasta) {
      resultado = resultado.filter(exp => {
        const fecha = parseDate(exp.ultima_actuacion);
        if (filtros.ultimaActuacionDesde && fecha < filtros.ultimaActuacionDesde) return false;
        if (filtros.ultimaActuacionHasta && fecha > filtros.ultimaActuacionHasta) return false;
        return true;
      });
    }

    // Filtro por dependencias
    if (filtros.dependencias.length > 0) {
      resultado = resultado.filter(exp =>
        filtros.dependencias.includes(exp.dependencia)
      );
    }

    // Filtro por situaciones
    if (filtros.situaciones.length > 0) {
      resultado = resultado.filter(exp =>
        filtros.situaciones.includes(exp.situacion)
      );
    }

    // Búsqueda personalizada
    if (filtros.busqueda.trim()) {
      const busquedaLower = filtros.busqueda.toLowerCase();
      resultado = resultado.filter(exp =>
        exp.numero.toLowerCase().includes(busquedaLower) ||
        exp.caratula.toLowerCase().includes(busquedaLower) ||
        exp.dependencia.toLowerCase().includes(busquedaLower)
      );
    }

    // Ordenamiento por fecha
    if (filtros.ordenFecha !== 'ninguno') {
      resultado.sort((a, b) => {
        const fechaA = parseDate(a.fecha_inicio).getTime();
        const fechaB = parseDate(b.fecha_inicio).getTime();
        return filtros.ordenFecha === 'desc' ? fechaB - fechaA : fechaA - fechaB;
      });
    }

    // Ordenamiento alfabético
    if (filtros.ordenAlfabetico !== 'ninguno') {
      resultado.sort((a, b) => {
        const comp = a.caratula.localeCompare(b.caratula);
        return filtros.ordenAlfabetico === 'az' ? comp : -comp;
      });
    }

    return resultado;
  }, [expedientes, filtros]);

  return {
    filtros,
    setFiltros,
    expedientesFiltrados,
  };
};
```

**Criterios de éxito:**
- ✅ Filtros aplicados correctamente
- ✅ Performance optimizada con useMemo
- ✅ Filtros combinables

---

#### **TAREA 5: Implementar selección masiva**

**Archivo:** `Sistema_v6/frontend/src/hooks/useSeleccionMasiva.ts`

**Objetivo:** Hook para manejar selección de expedientes.

**Código:**
```typescript
import { useState, useCallback } from 'react';
import { Expediente } from '@/types';

export const useSeleccionMasiva = (expedientes: Expediente[]) => {
  const [seleccionados, setSeleccionados] = useState<Set<string>>(new Set());

  const toggleSeleccion = useCallback((numero: string) => {
    setSeleccionados(prev => {
      const nuevo = new Set(prev);
      if (nuevo.has(numero)) {
        nuevo.delete(numero);
      } else {
        nuevo.add(numero);
      }
      return nuevo;
    });
  }, []);

  const seleccionarTodos = useCallback(() => {
    const todos = new Set(expedientes.map(exp => exp.numero));
    setSeleccionados(todos);
  }, [expedientes]);

  const seleccionarVisibles = useCallback((expedientesVisibles: Expediente[]) => {
    setSeleccionados(prev => {
      const nuevo = new Set(prev);
      expedientesVisibles.forEach(exp => nuevo.add(exp.numero));
      return nuevo;
    });
  }, []);

  const deseleccionarTodos = useCallback(() => {
    setSeleccionados(new Set());
  }, []);

  const invertirSeleccion = useCallback((expedientesVisibles: Expediente[]) => {
    setSeleccionados(prev => {
      const nuevo = new Set(prev);
      expedientesVisibles.forEach(exp => {
        if (nuevo.has(exp.numero)) {
          nuevo.delete(exp.numero);
        } else {
          nuevo.add(exp.numero);
        }
      });
      return nuevo;
    });
  }, []);

  const estaSeleccionado = useCallback((numero: string) => {
    return seleccionados.has(numero);
  }, [seleccionados]);

  const obtenerSeleccionados = useCallback(() => {
    return Array.from(seleccionados);
  }, [seleccionados]);

  return {
    seleccionados,
    totalSeleccionados: seleccionados.size,
    toggleSeleccion,
    seleccionarTodos,
    seleccionarVisibles,
    deseleccionarTodos,
    invertirSeleccion,
    estaSeleccionado,
    obtenerSeleccionados,
  };
};
```

**Criterios de éxito:**
- ✅ Selección individual funciona
- ✅ Selección masiva responsive
- ✅ Performance optimizada

---

#### **TAREA 6: Implementar paginación y virtualización**

**Instalaciones necesarias:**
```bash
npm install @tanstack/react-virtual
npm install react-window react-window-infinite-loader
```

**Archivo:** `Sistema_v6/frontend/src/components/expedientes/TablaVirtualizada.tsx`

**Objetivo:** Tabla virtualizada para manejar miles de expedientes sin lag.

**Código básico:**
```typescript
import { useVirtual } from '@tanstack/react-virtual';
import { useRef } from 'react';

interface TablaVirtualizadaProps {
  expedientes: Expediente[];
  onSeleccionar: (numero: string) => void;
  estaSeleccionado: (numero: string) => boolean;
}

export const TablaVirtualizada: React.FC<TablaVirtualizadaProps> = ({
  expedientes,
  onSeleccionar,
  estaSeleccionado,
}) => {
  const parentRef = useRef<HTMLDivElement>(null);

  const rowVirtualizer = useVirtual({
    size: expedientes.length,
    parentRef,
    estimateSize: useCallback(() => 60, []), // Altura estimada por fila
    overscan: 10, // Renderizar 10 items extra arriba/abajo
  });

  return (
    <div
      ref={parentRef}
      style={{
        height: '600px',
        overflow: 'auto',
        border: '1px solid #ddd',
      }}
    >
      <div
        style={{
          height: `${rowVirtualizer.totalSize}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {rowVirtualizer.virtualItems.map(virtualRow => {
          const expediente = expedientes[virtualRow.index];

          return (
            <div
              key={expediente.numero}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: `${virtualRow.size}px`,
                transform: `translateY(${virtualRow.start}px)`,
              }}
            >
              <ExpedienteRow
                expediente={expediente}
                seleccionado={estaSeleccionado(expediente.numero)}
                onSeleccionar={() => onSeleccionar(expediente.numero)}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
};
```

**Criterios de éxito:**
- ✅ Renderiza 2000+ expedientes sin lag
- ✅ Scroll suave
- ✅ Solo renderiza lo visible

---

#### **TAREA 7: Integrar con el flujo de extracción masiva**

**Objetivo:** Conectar el nuevo componente con el flujo existente.

**Modificar:** `Sistema_v6/frontend/src/components/expedientes/ExtraccionMasivaDialog.tsx`

**Agregar etapa de filtrado:**
```typescript
type EtapaExtraccion = 'config' | 'extrayendo' | 'filtrado' | 'procesando' | 'completado';

const [etapa, setEtapa] = useState<EtapaExtraccion>('config');

// En el render:
{etapa === 'filtrado' && (
  <FiltradoExpedientesDialog
    sessionId={sessionId}
    onProcesar={(seleccionados) => {
      setEtapa('procesando');
      procesarSeleccionados(seleccionados);
    }}
    onVolver={() => setEtapa('config')}
  />
)}
```

**Flujo actualizado:**
```
Config → Iniciar → Extrayendo (WebSocket) →
→ [NUEVO] Filtrado y Selección →
→ Procesando seleccionados (WebSocket) → Completado
```

**Criterios de éxito:**
- ✅ Flujo completo funciona
- ✅ Transiciones suaves entre etapas
- ✅ Estado se mantiene correctamente

---

### **FASE 3: PROCESAMIENTO SELECTIVO** (6-8 horas)

#### **TAREA 8: Implementar extracción básica en GestorBatch** (SIMPLIFICADA)

**Archivo:** `Sistema_v6/extraccion_masiva/gestor_batch.py`
**Método:** `_procesar_expediente()` (líneas 234-275)

**Objetivo:** Implementar lógica real BÁSICA sin clasificación ni vencimientos.

**Código:** (Ver sección anterior con implementación simplificada)

**Tiempo:** 2-3 horas

**Criterios de éxito:**
- ✅ Extrae metadata de actuaciones
- ✅ NO intenta clasificar ni detectar vencimientos
- ✅ Guarda en repository
- ✅ Actualiza estados básicos

---

#### **TAREA 9: Integrar guardado en repository**

**Tiempo:** 1-2 horas

**Criterios de éxito:**
- ✅ Expedientes guardados correctamente
- ✅ Manejo de errores robusto

---

#### **TAREA 10: Actualizar estados básicos**

**Tiempo:** 30 minutos - 1 hora

**Criterios de éxito:**
- ✅ Estados PROCESADO/ERROR/OMITIDO
- ✅ Estados persistidos

---

#### **TAREA 11: Actualizar DI Container**

**Tiempo:** 30 minutos - 1 hora

**Criterios de éxito:**
- ✅ Dependencias inyectadas
- ✅ Sin errores de importación

---

### **FASE 4: TESTING Y DOCUMENTACIÓN** (2-3 horas)

#### **TAREA 12-15: Tests**

- Tests unitarios de filtros
- Tests de selección masiva
- Tests de integración del flujo completo
- Pruebas manuales desde frontend

#### **TAREA 16-18: Documentación y ajustes finales**

- Actualizar README
- Crear guía de usuario
- Changelog

---

## 📊 RESUMEN DE TIEMPOS

| Fase | Tareas | Tiempo | Prioridad |
|------|--------|--------|-----------|
| 1. Backend Listado | 1-2 | 2-3h | 🔴 ALTA |
| 2. Frontend Filtrado | 3-7 | 8-10h | 🔴 CRÍTICA |
| 3. Procesamiento | 8-11 | 6-8h | 🔴 ALTA |
| 4. Testing/Docs | 12-18 | 2-3h | 🟡 MEDIA |
| **TOTAL** | **18** | **18-24h** | |

---

## ✅ NUEVO CHECKLIST DE VERIFICACIÓN

### Backend
- [ ] Endpoint `/listado` retorna expedientes completos
- [ ] Endpoint `/procesar-seleccionados` funciona
- [ ] GestorBatch procesa solo seleccionados
- [ ] Repository guarda correctamente

### Frontend
- [ ] FiltradoExpedientesDialog renderiza sin lag
- [ ] 7 filtros funcionan correctamente
- [ ] Selección masiva responsive
- [ ] Paginación fluida
- [ ] Contador en tiempo real actualiza
- [ ] Integración con flujo de extracción

### Flujo Completo
- [ ] Usuario extrae listado (Fase 1)
- [ ] Ve tabla con filtros (Fase 2)
- [ ] Filtra y selecciona expedientes
- [ ] Procesa solo seleccionados (Fase 3)
- [ ] Ve progreso en tiempo real
- [ ] Expedientes guardados en sistema

---

## 🎯 PRÓXIMO PASO INMEDIATO

**EMPEZAR CON TAREA 1:** Crear endpoint `/listado`

Es la base para todo el frontend de filtrado.

---

**FIN DEL PLAN V2**

**Última actualización:** 2025-11-07
**Versión:** 2.0
**Estado:** ✅ LISTO PARA IMPLEMENTACIÓN
