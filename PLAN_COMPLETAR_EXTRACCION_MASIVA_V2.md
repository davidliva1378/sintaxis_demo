# 🎯 PLAN COMPLETO V2: Finalizar Implementación de Extracción Masiva

**Fecha de actualización:** 2025-11-10
**Versión:** 2.1 (Con FASE 2 de Filtrado + FASE 4 de Monitoreo)
**Rama de trabajo:** `sintaxis_parcial2` → `claude/review-sintaxis-parcial2-011CUuHPSBCZ7juywst29TXV`
**Estado actual:** 30% completado (ajustado con nuevas fases)
**Tiempo estimado total:** 31-41 horas (MVP: 17-22 horas)

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

## 📋 PLAN DE IMPLEMENTACIÓN - 22 TAREAS (4 FASES)

---

### **FASE 1: BACKEND - ENDPOINTS DE LISTADO CON COMPARACIÓN** (3-4 horas)

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

#### **TAREA 1B: Agregar comparación automática con JSON BASE** 🆕

**Archivo:** `Sistema_v6/extraccion_masiva/extractor_masivo.py`

**Objetivo:** Al extraer el listado, compararlo automáticamente con JSON BASE si existe para mostrar cambios al usuario.

**Código:**
```python
# En extractor_masivo.py, método extraer_listado_completo()

async def extraer_listado_completo(self):
    """Extrae listado completo Y compara con JSON BASE si existe."""

    # 1. Extracción normal
    expedientes = await self._extraer_todas_paginas()

    # 2. Guardar como listado de esta sesión
    listado_path = self.listados_dir / f"listado_{self.session_id}.json"
    self._guardar_json(listado_path, expedientes)

    # 3. 🆕 COMPARACIÓN si existe JSON BASE
    json_base_path = self.listados_dir / "listado_base.json"

    comparacion = None
    if json_base_path.exists():
        logger.info("JSON BASE encontrado, ejecutando comparación...")

        base_anterior = self._cargar_json(json_base_path)

        # Usar ComparadorExpedientes (del sistema de monitoreo)
        from Sistema_v6.monitoring.comparador_expedientes import ComparadorExpedientes
        comparador = ComparadorExpedientes()

        cambios = comparador.detectar_cambios(expedientes, base_anterior)
        nuevos = comparador.detectar_nuevos(expedientes, base_anterior)

        comparacion = {
            "total_nuevos": len(nuevos),
            "total_cambios": len(cambios),
            "total_sin_cambios": len(expedientes) - len(nuevos) - len(cambios),
            "nuevos": nuevos[:10],  # Primeros 10 para preview
            "cambios": cambios[:10],  # Primeros 10 para preview
            "fecha_base_anterior": base_anterior.get("metadata", {}).get("fecha_extraccion")
        }

        logger.info(
            f"Comparación completada: "
            f"{len(nuevos)} nuevos, {len(cambios)} cambios"
        )

    # 4. Emitir resultado al frontend
    self._emit("fin_listado", {
        "total": len(expedientes),
        "archivo": str(listado_path),
        "listado_path": str(listado_path),
        "comparacion": comparacion,  # 🆕 NUEVO
        "paginas_procesadas": self.paginas_procesadas,
    })

    return expedientes
```

**Actualizar endpoint:**
```python
# En routers/extraccion_masiva.py, actualizar TAREA 1

@router.get("/{session_id}/listado", response_model=Dict)
async def obtener_listado_completo(session_id: str, ...):
    """Obtiene listado + comparación si existe."""

    # ... código existente ...

    return {
        "session_id": session_id,
        "total": len(expedientes),
        "expedientes": expedientes,
        "metadata": {
            "dependencias": dependencias,
            "situaciones": situaciones,
            "fecha_extraccion": sesion.get("tiempo_inicio"),
        },
        "comparacion": sesion.get("comparacion"),  # 🆕 NUEVO
    }
```

**UI de comparación (Frontend):**
```typescript
// En FiltradoExpedientesDialog.tsx

{comparacion && (
  <Alert severity="info" sx={{ mb: 2 }}>
    <AlertTitle>
      Comparación con extracción anterior ({new Date(comparacion.fecha_base_anterior).toLocaleDateString()})
    </AlertTitle>
    <Box sx={{ display: 'flex', gap: 2 }}>
      <Chip label={`🆕 ${comparacion.total_nuevos} nuevos`} color="success" />
      <Chip label={`📝 ${comparacion.total_cambios} con cambios`} color="warning" />
      <Chip label={`✅ ${comparacion.total_sin_cambios} sin cambios`} color="default" />
    </Box>
    <Box sx={{ mt: 1 }}>
      <Button size="small" onClick={() => setMostrarNuevos(true)}>Ver nuevos</Button>
      <Button size="small" onClick={() => setMostrarCambios(true)}>Ver cambios</Button>
    </Box>
  </Alert>
)}
```

**Beneficios:**
- ✅ Usuario ve cambios inmediatamente
- ✅ Identifica nuevos expedientes sin buscar manualmente
- ✅ Reutiliza lógica del sistema de monitoreo
- ✅ Mejora UX significativamente

**Tiempo:** 1 hora

**Criterios de éxito:**
- ✅ Comparación se ejecuta automáticamente si existe JSON BASE
- ✅ Frontend muestra resumen de cambios
- ✅ Usuario puede ver detalles de nuevos/cambios
- ✅ Funciona correctamente si NO existe JSON BASE (primera vez)

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

### **FASE 4: SISTEMA DE MONITOREO** (12-16 horas) 🆕

**Documentación completa:** Ver `ARQUITECTURA_SISTEMA_MONITOREO.md`

Esta fase implementa el sistema de monitoreo que mantiene sincronizado el sistema local con el PJN mediante extracciones periódicas y comparaciones inteligentes.

#### **TAREA 12: Implementar ComparadorExpedientes**

**Archivo NUEVO:** `Sistema_v6/monitoring/comparador_expedientes.py`

**Objetivo:** Servicio que realiza las 3 comparaciones críticas del sistema de monitoreo.

**Código:**
```python
from typing import List, Dict, Optional
from datetime import datetime

class Cambio:
    """Representa un cambio detectado en un expediente."""
    def __init__(self, numero: str, cambios: Dict, fecha_deteccion: str):
        self.numero = numero
        self.cambios = cambios
        self.fecha_deteccion = fecha_deteccion


class ComparadorExpedientes:
    """Comparador de expedientes entre JSONs."""

    def detectar_cambios(
        self,
        monitoreo: List[Dict],
        sistema: List[Dict]
    ) -> List[Cambio]:
        """
        Comparación 1: Detectar cambios en expedientes del sistema.

        Compara JSON_MONITOREO vs JSON_SISTEMA para encontrar
        expedientes con datos desactualizados.
        """
        cambios = []

        # Indexar por número para búsqueda rápida
        sistema_dict = {exp["numero"]: exp for exp in sistema}

        for exp_mon in monitoreo:
            numero = exp_mon["numero"]

            # Si está en el sistema, comparar
            if numero in sistema_dict:
                exp_sis = sistema_dict[numero]

                # Comparar campos críticos
                cambios_encontrados = {}

                if exp_mon.get("situacion") != exp_sis.get("situacion"):
                    cambios_encontrados["situacion"] = {
                        "anterior": exp_sis.get("situacion"),
                        "nuevo": exp_mon.get("situacion")
                    }

                if exp_mon.get("ultima_actuacion") != exp_sis.get("ultima_actuacion"):
                    cambios_encontrados["ultima_actuacion"] = {
                        "anterior": exp_sis.get("ultima_actuacion"),
                        "nuevo": exp_mon.get("ultima_actuacion")
                    }

                if exp_mon.get("dependencia") != exp_sis.get("dependencia"):
                    cambios_encontrados["dependencia"] = {
                        "anterior": exp_sis.get("dependencia"),
                        "nuevo": exp_mon.get("dependencia")
                    }

                if exp_mon.get("caratula") != exp_sis.get("caratula"):
                    cambios_encontrados["caratula"] = {
                        "anterior": exp_sis.get("caratula"),
                        "nuevo": exp_mon.get("caratula")
                    }

                if cambios_encontrados:
                    cambios.append(Cambio(
                        numero=numero,
                        cambios=cambios_encontrados,
                        fecha_deteccion=datetime.now().isoformat()
                    ))

        return cambios

    def detectar_nuevos(
        self,
        monitoreo: List[Dict],
        base: List[Dict]
    ) -> List[Dict]:
        """
        Comparación 2: Detectar nuevos expedientes.

        Compara JSON_MONITOREO vs JSON_BASE para encontrar
        expedientes completamente nuevos.
        """
        nuevos = []

        # Indexar números existentes en base
        numeros_base = {exp["numero"] for exp in base}

        for exp_mon in monitoreo:
            if exp_mon["numero"] not in numeros_base:
                nuevos.append({
                    "expediente": exp_mon,
                    "fecha_deteccion": datetime.now().isoformat(),
                    "origen": "monitor_extraccion"
                })

        return nuevos

    def detectar_faltantes(
        self,
        sistema: List[Dict],
        monitoreo: List[Dict],
        tipo_extraccion: str,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None
    ) -> List[Dict]:
        """
        Comparación 3: Detectar faltantes CON LÓGICA CONDICIONAL.

        Compara JSON_SISTEMA vs JSON_MONITOREO para encontrar
        expedientes que no aparecieron, pero solo los marca si
        DEBERÍAN haber aparecido según el tipo de extracción.
        """
        faltantes = []

        # Indexar números encontrados en monitoreo
        numeros_monitoreo = {exp["numero"] for exp in monitoreo}

        for exp_sis in sistema:
            numero = exp_sis["numero"]

            # Si NO está en monitoreo
            if numero not in numeros_monitoreo:

                # LÓGICA CONDICIONAL: Evaluar si DEBERÍA haber estado
                deberia_estar = self._evaluar_si_deberia_estar(
                    exp_sis,
                    tipo_extraccion,
                    fecha_desde,
                    fecha_hasta
                )

                if deberia_estar:
                    faltantes.append({
                        "numero": numero,
                        "caratula": exp_sis.get("caratula"),
                        "tipo_extraccion": tipo_extraccion,
                        "fecha_deteccion": datetime.now().isoformat(),
                        "accion_sugerida": "MARCAR_NO_ENCONTRADO"
                    })

        return faltantes

    def _evaluar_si_deberia_estar(
        self,
        expediente: Dict,
        tipo_extraccion: str,
        fecha_desde: Optional[str],
        fecha_hasta: Optional[str]
    ) -> bool:
        """
        Evalúa si un expediente DEBERÍA haber aparecido en la extracción.

        Reglas:
        1. TOTAL: Siempre debería estar
        2. PARCIAL: Solo si está en el rango de fechas
        3. DIRIGIDA: Solo si fue específicamente buscado
        """

        # Caso 1: Extracción TOTAL
        if tipo_extraccion == "TOTAL":
            return True

        # Caso 2: Extracción PARCIAL por fechas
        if tipo_extraccion == "PARCIAL":
            if not fecha_desde or not fecha_hasta:
                return True

            # Verificar si la última actuación está en el rango
            ultima_act = expediente.get("ultima_actuacion")
            if not ultima_act:
                return False

            try:
                from dateutil.parser import parse as parse_date
                ultima_act_date = parse_date(ultima_act)
                desde_date = parse_date(fecha_desde)
                hasta_date = parse_date(fecha_hasta)

                if desde_date <= ultima_act_date <= hasta_date:
                    return True  # SÍ debería estar
                else:
                    return False  # NO debería estar (fuera del rango)
            except:
                return True  # En caso de error, asumir que debería estar

        # Caso 3: Extracción DIRIGIDA
        if tipo_extraccion == "DIRIGIDA":
            # Por ahora, asumir que debería estar
            return True

        # Default: Asumir que debería estar
        return True
```

**Tiempo:** 2-3 horas

**Criterios de éxito:**
- ✅ Las 3 comparaciones funcionan correctamente
- ✅ Lógica condicional de faltantes implementada
- ✅ Performance optimizada con índices
- ✅ Tests unitarios pasan

---

#### **TAREA 13: Implementar ActualizadorJSONs**

**Archivo NUEVO:** `Sistema_v6/monitoring/actualizador_jsons.py`

**Objetivo:** Servicio que actualiza los archivos JSON después de las comparaciones.

**Código:**
```python
import json
import shutil
from pathlib import Path
from typing import List, Dict
from datetime import datetime


class ActualizadorJSONs:
    """Actualizador de archivos JSON del sistema."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.listados_dir = data_dir / "extraccion_masiva" / "listados"
        self.sistema_dir = data_dir / "sistema"

    def actualizar_json_base(
        self,
        base: List[Dict],
        monitoreo: List[Dict],
        nuevos: List[Dict]
    ) -> List[Dict]:
        """
        Actualizar JSON_BASE con nuevos expedientes y actualizaciones.

        Args:
            base: JSON BASE actual
            monitoreo: Expedientes extraídos en monitoreo
            nuevos: Expedientes nuevos detectados

        Returns:
            JSON BASE actualizado
        """
        # Indexar por número
        base_dict = {exp["numero"]: exp for exp in base}

        # 1. Actualizar existentes con datos del monitoreo
        for exp_mon in monitoreo:
            numero = exp_mon["numero"]
            if numero in base_dict:
                # Actualizar datos
                base_dict[numero].update({
                    "situacion": exp_mon.get("situacion"),
                    "ultima_actuacion": exp_mon.get("ultima_actuacion"),
                    "dependencia": exp_mon.get("dependencia"),
                    "caratula": exp_mon.get("caratula"),
                    "ultima_actualizacion": datetime.now().isoformat()
                })

        # 2. Agregar nuevos
        for nuevo in nuevos:
            exp = nuevo["expediente"]
            exp["fecha_agregado"] = datetime.now().isoformat()
            exp["ultima_actualizacion"] = datetime.now().isoformat()
            base_dict[exp["numero"]] = exp

        return list(base_dict.values())

    def actualizar_json_sistema(
        self,
        sistema: List[Dict],
        cambios: List,
        faltantes: List[Dict]
    ) -> List[Dict]:
        """
        Actualizar JSON_SISTEMA con cambios y expedientes faltantes.

        Args:
            sistema: JSON SISTEMA actual
            cambios: Cambios detectados
            faltantes: Expedientes no encontrados

        Returns:
            JSON SISTEMA actualizado
        """
        sistema_dict = {exp["numero"]: exp for exp in sistema}

        # 1. Aplicar cambios detectados
        for cambio in cambios:
            numero = cambio.numero
            if numero in sistema_dict:
                # Actualizar cada campo cambiado
                for campo, valores in cambio.cambios.items():
                    sistema_dict[numero][campo] = valores["nuevo"]

                sistema_dict[numero]["ultima_actualizacion_sistema"] = datetime.now().isoformat()

        # 2. Marcar faltantes
        for faltante in faltantes:
            numero = faltante["numero"]
            if numero in sistema_dict:
                sistema_dict[numero]["estado_sistema"] = "NO_ENCONTRADO"
                sistema_dict[numero]["fecha_no_encontrado"] = datetime.now().isoformat()

        return list(sistema_dict.values())

    def guardar_con_backup(
        self,
        archivo: Path,
        datos: Dict,
        crear_backup: bool = True
    ):
        """
        Guardar JSON con backup automático.

        Args:
            archivo: Ruta del archivo a guardar
            datos: Datos a guardar
            crear_backup: Si crear backup antes de sobrescribir
        """
        # Crear backup antes de sobrescribir
        if crear_backup and archivo.exists():
            backup_path = archivo.parent / f"{archivo.stem}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}{archivo.suffix}"
            shutil.copy(archivo, backup_path)

        # Guardar nuevo
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)

    def guardar_json_pendientes(self, nuevos: List[Dict]):
        """Guardar expedientes nuevos en JSON_PENDIENTES."""
        pendientes_path = self.sistema_dir / "pendientes_revision.json"

        # Cargar existentes si existen
        expedientes_existentes = []
        if pendientes_path.exists():
            with open(pendientes_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                expedientes_existentes = data.get("expedientes_nuevos", [])

        # Agregar nuevos
        expedientes_existentes.extend(nuevos)

        # Guardar
        data = {
            "metadata": {
                "total_pendientes": len(expedientes_existentes),
                "ultima_actualizacion": datetime.now().isoformat()
            },
            "expedientes_nuevos": expedientes_existentes
        }

        self.guardar_con_backup(pendientes_path, data, crear_backup=False)
```

**Tiempo:** 2-3 horas

**Criterios de éxito:**
- ✅ JSON BASE se actualiza correctamente
- ✅ JSON SISTEMA se actualiza correctamente
- ✅ JSON PENDIENTES se crea/actualiza
- ✅ Backups automáticos funcionan

---

#### **TAREA 14: Implementar GestorConflictos**

**Archivo NUEVO:** `Sistema_v6/monitoring/gestor_conflictos.py`

**Objetivo:** Detectar y gestionar conflictos que requieren intervención del usuario.

**Código:**
```python
import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime


class Conflicto:
    """Representa un conflicto detectado."""
    def __init__(
        self,
        id: str,
        tipo: str,
        expediente: str,
        datos: Dict,
        fecha_deteccion: str
    ):
        self.id = id
        self.tipo = tipo
        self.expediente = expediente
        self.datos = datos
        self.fecha_deteccion = fecha_deteccion
        self.estado = "PENDIENTE"


class GestorConflictos:
    """Gestor de conflictos de datos."""

    def __init__(self, sistema_dir: Path):
        self.sistema_dir = sistema_dir
        self.conflictos_path = sistema_dir / "conflictos.json"

    def detectar_conflictos(
        self,
        cambios: List,
        faltantes: List[Dict]
    ) -> List[Conflicto]:
        """
        Detectar conflictos que requieren decisión del usuario.

        Args:
            cambios: Lista de cambios detectados
            faltantes: Lista de expedientes faltantes

        Returns:
            Lista de conflictos
        """
        conflictos = []

        # Conflictos tipo 1: Cambios en situación (crítico)
        for cambio in cambios:
            if "situacion" in cambio.cambios:
                conflicto_id = f"conflict_{cambio.numero}_{int(datetime.now().timestamp())}"
                conflictos.append(Conflicto(
                    id=conflicto_id,
                    tipo="CAMBIO_SITUACION",
                    expediente=cambio.numero,
                    datos={
                        "campo": "situacion",
                        "valor_local": cambio.cambios["situacion"]["anterior"],
                        "valor_pjn": cambio.cambios["situacion"]["nuevo"]
                    },
                    fecha_deteccion=datetime.now().isoformat()
                ))

        # Conflictos tipo 2: Expedientes no encontrados
        for faltante in faltantes:
            conflicto_id = f"conflict_{faltante['numero']}_{int(datetime.now().timestamp())}"
            conflictos.append(Conflicto(
                id=conflicto_id,
                tipo="NO_ENCONTRADO",
                expediente=faltante["numero"],
                datos=faltante,
                fecha_deteccion=datetime.now().isoformat()
            ))

        return conflictos

    def guardar_conflictos(self, conflictos: List[Conflicto]):
        """Guardar conflictos en JSON."""
        # Cargar existentes
        conflictos_existentes = []
        if self.conflictos_path.exists():
            with open(self.conflictos_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                conflictos_existentes = data.get("conflictos", [])

        # Agregar nuevos
        for conflicto in conflictos:
            conflictos_existentes.append({
                "id": conflicto.id,
                "tipo": conflicto.tipo,
                "numero_expediente": conflicto.expediente,
                "datos": conflicto.datos,
                "fecha_deteccion": conflicto.fecha_deteccion,
                "estado": conflicto.estado,
                "accion_usuario": None
            })

        # Guardar
        data = {
            "metadata": {
                "total_conflictos": len(conflictos_existentes),
                "pendientes": len([c for c in conflictos_existentes if c["estado"] == "PENDIENTE"]),
                "ultima_actualizacion": datetime.now().isoformat()
            },
            "conflictos": conflictos_existentes
        }

        with open(self.conflictos_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def resolver_conflicto(
        self,
        conflicto_id: str,
        accion: str  # ACEPTAR_PJN | MANTENER_LOCAL | REVISAR_DESPUES
    ):
        """Resolver un conflicto con la acción del usuario."""
        if not self.conflictos_path.exists():
            return

        with open(self.conflictos_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Buscar y actualizar conflicto
        for conflicto in data["conflictos"]:
            if conflicto["id"] == conflicto_id:
                conflicto["estado"] = "RESUELTO" if accion != "REVISAR_DESPUES" else "PENDIENTE"
                conflicto["accion_usuario"] = accion
                conflicto["fecha_resolucion"] = datetime.now().isoformat()
                break

        # Guardar
        with open(self.conflictos_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
```

**Tiempo:** 2 horas

**Criterios de éxito:**
- ✅ Conflictos se detectan correctamente
- ✅ Se guardan en JSON
- ✅ Usuario puede resolverlos
- ✅ Estados se actualizan correctamente

---

#### **TAREA 15: Implementar ServicioMonitor**

**Archivo NUEVO:** `Sistema_v6/monitoring/servicio_monitor.py`

**Objetivo:** Servicio principal que coordina todo el sistema de monitoreo.

**Código simplificado:**
```python
import logging
from typing import Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)


class ServicioMonitor:
    """Servicio principal de monitoreo."""

    def __init__(
        self,
        extractor,
        comparador,
        actualizador,
        gestor_conflictos,
        config
    ):
        self.extractor = extractor
        self.comparador = comparador
        self.actualizador = actualizador
        self.gestor_conflictos = gestor_conflictos
        self.config = config
        self.is_running = False

    async def ejecutar_monitoreo(self, tipo: str = "PARCIAL"):
        """
        Ejecutar ciclo completo de monitoreo.

        Args:
            tipo: PARCIAL | TOTAL
        """
        logger.info(f"Iniciando monitoreo {tipo}")

        # 1. Extracción
        if tipo == "PARCIAL":
            criterio = self.config.criterio_parcial
            monitoreo = await self.extractor.extraer_con_criterio(criterio)
        else:
            monitoreo = await self.extractor.extraer_listado_completo()

        # 2. Cargar JSONs existentes
        base = self._cargar_json_base()
        sistema = self._cargar_json_sistema()

        # 3. Comparaciones
        cambios = self.comparador.detectar_cambios(monitoreo, sistema)
        nuevos = self.comparador.detectar_nuevos(monitoreo, base)
        faltantes = self.comparador.detectar_faltantes(
            sistema,
            monitoreo,
            tipo_extraccion=tipo,
            fecha_desde=criterio.get("fecha_desde") if tipo == "PARCIAL" else None,
            fecha_hasta=criterio.get("fecha_hasta") if tipo == "PARCIAL" else None
        )

        # 4. Detectar conflictos
        conflictos = self.gestor_conflictos.detectar_conflictos(cambios, faltantes)

        if conflictos:
            # Guardar conflictos
            self.gestor_conflictos.guardar_conflictos(conflictos)
            # Notificar al usuario
            await self._notificar_conflictos(conflictos)
            # Esperar decisión del usuario (no auto-actualizar)
            logger.info(f"{len(conflictos)} conflictos detectados. Esperando resolución del usuario.")
            return

        # 5. Actualizar JSONs (solo si no hay conflictos)
        base_actualizado = self.actualizador.actualizar_json_base(base, monitoreo, nuevos)
        sistema_actualizado = self.actualizador.actualizar_json_sistema(sistema, cambios, faltantes)

        # 6. Guardar
        self._guardar_json_base(base_actualizado)
        self._guardar_json_sistema(sistema_actualizado)

        if nuevos:
            self.actualizador.guardar_json_pendientes(nuevos)

        logger.info(
            f"Monitoreo completado: "
            f"{len(cambios)} cambios, "
            f"{len(nuevos)} nuevos, "
            f"{len(faltantes)} faltantes"
        )

    # ... métodos auxiliares ...
```

**Tiempo:** 3-4 horas

**Criterios de éxito:**
- ✅ Coordina todas las operaciones
- ✅ Maneja errores correctamente
- ✅ Logging completo
- ✅ Notificaciones funcionan

---

#### **TAREA 16: Crear endpoints REST para monitoreo**

**Archivo:** `Sistema_v6/presentation/api/rest/routers/monitoring.py`

**Objetivo:** Exponer API REST para controlar el monitoreo.

**Código:**
```python
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict
import json

router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])


@router.post("/start")
async def iniciar_monitoreo(
    config: Dict,
    monitor = Depends(get_monitor_service)
):
    """Iniciar servicio de monitoreo con configuración."""
    await monitor.iniciar(config)
    return {"status": "iniciado", "mensaje": "Monitoreo iniciado correctamente"}


@router.post("/stop")
async def detener_monitoreo(monitor = Depends(get_monitor_service)):
    """Detener servicio de monitoreo."""
    await monitor.detener()
    return {"status": "detenido"}


@router.post("/trigger/{tipo}")
async def forzar_extraccion(
    tipo: str,  # PARCIAL | TOTAL
    monitor = Depends(get_monitor_service)
):
    """Forzar extracción manual inmediata."""
    if tipo not in ["PARCIAL", "TOTAL"]:
        raise HTTPException(status_code=400, detail="Tipo debe ser PARCIAL o TOTAL")

    await monitor.ejecutar_monitoreo(tipo)
    return {"status": "completado", "tipo": tipo}


@router.get("/status")
async def estado_monitoreo(monitor = Depends(get_monitor_service)):
    """Obtener estado actual del monitoreo."""
    return {
        "activo": monitor.is_running,
        "ultima_extraccion": monitor.ultima_extraccion,
        "proxima_extraccion": monitor.proxima_extraccion,
        "tipo_ultima_extraccion": monitor.tipo_ultima_extraccion
    }


@router.get("/conflictos")
async def obtener_conflictos():
    """Obtener lista de conflictos pendientes."""
    conflictos_path = Path("data/sistema/conflictos.json")
    if not conflictos_path.exists():
        return {"conflictos": [], "total": 0}

    with open(conflictos_path, "r", encoding="utf-8") as f:
        return json.load(f)


@router.post("/conflictos/{conflicto_id}/resolver")
async def resolver_conflicto(
    conflicto_id: str,
    accion: str,  # ACEPTAR_PJN | MANTENER_LOCAL | REVISAR_DESPUES
    gestor = Depends(get_gestor_conflictos)
):
    """Resolver un conflicto específico."""
    if accion not in ["ACEPTAR_PJN", "MANTENER_LOCAL", "REVISAR_DESPUES"]:
        raise HTTPException(status_code=400, detail="Acción inválida")

    gestor.resolver_conflicto(conflicto_id, accion)
    return {"status": "resuelto", "conflicto_id": conflicto_id, "accion": accion}


@router.get("/pendientes")
async def obtener_pendientes():
    """Obtener expedientes nuevos pendientes de revisión."""
    pendientes_path = Path("data/sistema/pendientes_revision.json")
    if not pendientes_path.exists():
        return {"expedientes_nuevos": [], "total": 0}

    with open(pendientes_path, "r", encoding="utf-8") as f:
        return json.load(f)
```

**Tiempo:** 2 horas

**Criterios de éxito:**
- ✅ 7 endpoints funcionan correctamente
- ✅ Validación de parámetros
- ✅ Manejo de errores
- ✅ Documentación en /docs

---

#### **TAREA 17: Implementar scheduler con APScheduler**

**Archivo:** `Sistema_v6/monitoring/scheduler.py`

**Objetivo:** Programar extracciones automáticas según configuración.

**Código:**
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import logging

logger = logging.getLogger(__name__)


class MonitorScheduler:
    """Scheduler para extracciones automáticas."""

    def __init__(self, servicio_monitor):
        self.monitor = servicio_monitor
        self.scheduler = AsyncIOScheduler()

    def configurar(self, config: Dict):
        """
        Configurar scheduler según configuración del usuario.

        Args:
            config: Configuración de monitoreo
        """
        # Limpiar jobs existentes
        self.scheduler.remove_all_jobs()

        # Extracciones parciales (frecuentes)
        if config.get("extracciones_parciales", {}).get("habilitado"):
            frecuencia_horas = config["extracciones_parciales"].get("frecuencia_horas", 1)

            self.scheduler.add_job(
                self.monitor.ejecutar_monitoreo,
                trigger=IntervalTrigger(hours=frecuencia_horas),
                args=["PARCIAL"],
                id="monitoreo_parcial",
                replace_existing=True
            )
            logger.info(f"Programado: Extracción PARCIAL cada {frecuencia_horas} horas")

        # Extracciones totales (periódicas)
        if config.get("extracciones_totales", {}).get("habilitado"):
            frecuencia = config["extracciones_totales"].get("frecuencia", "SEMANAL")

            if frecuencia == "SEMANAL":
                dia = config["extracciones_totales"].get("dia_semana", "DOMINGO")
                hora = config["extracciones_totales"].get("hora", 3)

                dia_map = {
                    "LUNES": "mon", "MARTES": "tue", "MIERCOLES": "wed",
                    "JUEVES": "thu", "VIERNES": "fri", "SABADO": "sat", "DOMINGO": "sun"
                }

                self.scheduler.add_job(
                    self.monitor.ejecutar_monitoreo,
                    trigger=CronTrigger(day_of_week=dia_map[dia], hour=hora),
                    args=["TOTAL"],
                    id="monitoreo_total_semanal",
                    replace_existing=True
                )
                logger.info(f"Programado: Extracción TOTAL semanal ({dia} {hora}:00)")

            elif frecuencia == "DIARIO":
                hora = config["extracciones_totales"].get("hora", 3)

                self.scheduler.add_job(
                    self.monitor.ejecutar_monitoreo,
                    trigger=CronTrigger(hour=hora),
                    args=["TOTAL"],
                    id="monitoreo_total_diario",
                    replace_existing=True
                )
                logger.info(f"Programado: Extracción TOTAL diaria ({hora}:00)")

    def iniciar(self):
        """Iniciar scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler iniciado")

    def detener(self):
        """Detener scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler detenido")
```

**Tiempo:** 1-2 horas

**Criterios de éxito:**
- ✅ Scheduler se configura correctamente
- ✅ Jobs se ejecutan en horarios correctos
- ✅ Se puede iniciar/detener

---

#### **TAREA 18: Crear UI de configuración de monitoreo**

**Archivo NUEVO:** `Sistema_v6/frontend/src/components/monitoring/MonitorConfigDialog.tsx`

**Objetivo:** Interfaz para configurar el sistema de monitoreo.

**Estructura:**
```typescript
interface MonitorConfig {
  activado: boolean;
  extracciones_parciales: {
    habilitado: boolean;
    frecuencia_horas: number;
    dias_atras: number;
  };
  extracciones_totales: {
    habilitado: boolean;
    frecuencia: 'DIARIO' | 'SEMANAL';
    dia_semana?: string;
    hora: number;
  };
  notificaciones: {
    cambios_situacion: boolean;
    nuevos_expedientes: boolean;
    expedientes_faltantes: boolean;
    conflictos: boolean;
  };
}

export const MonitorConfigDialog: React.FC = () => {
  const [config, setConfig] = useState<MonitorConfig>(defaultConfig);

  const handleGuardar = async () => {
    await fetch('/api/v1/monitoring/start', {
      method: 'POST',
      body: JSON.stringify(config),
      headers: { 'Content-Type': 'application/json' }
    });
  };

  return (
    <Dialog open={open} maxWidth="md" fullWidth>
      <DialogTitle>⚙️ Configuración de Monitoreo</DialogTitle>
      <DialogContent>
        {/* UI de configuración */}
      </DialogContent>
    </Dialog>
  );
};
```

**Tiempo:** 3-4 horas

**Criterios de éxito:**
- ✅ UI intuitiva y clara
- ✅ Guarda configuración correctamente
- ✅ Valida inputs
- ✅ Muestra estado actual

---

#### **TAREA 19: Crear UI de dashboard de monitoreo**

**Archivo NUEVO:** `Sistema_v6/frontend/src/components/monitoring/MonitorDashboard.tsx`

**Objetivo:** Dashboard para ver estado y estadísticas del monitoreo.

**Tiempo:** 3-4 horas

---

#### **TAREA 20: Crear UI de gestión de conflictos**

**Archivo NUEVO:** `Sistema_v6/frontend/src/components/monitoring/ConflictosDialog.tsx`

**Objetivo:** Interfaz para revisar y resolver conflictos.

**Tiempo:** 2-3 horas

---

### **FASE 5: TESTING Y DOCUMENTACIÓN** (2-3 horas)

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

## 📊 RESUMEN DE TIEMPOS ACTUALIZADO

| Fase | Tareas | Tiempo | Prioridad |
|------|--------|--------|-----------|
| 1. Backend Listado + Comparación | 1, 1B, 2 | 3-4h | 🔴 ALTA |
| 2. Frontend Filtrado | 3-7 | 8-10h | 🔴 CRÍTICA |
| 3. Procesamiento Selectivo | 8-11 | 6-8h | 🔴 ALTA |
| 4. Sistema de Monitoreo 🆕 | 12-20 | 12-16h | 🟡 MEDIA |
| 5. Testing/Docs | 21-22 | 2-3h | 🟡 MEDIA |
| **TOTAL** | **22** | **31-41h** | |

### Desglose Detallado:

**FASE 1: Backend Listado con Comparación** (3-4h)
- Tarea 1: Endpoint `/listado` (2h)
- Tarea 1B: Comparación automática con JSON BASE 🆕 (1h)
- Tarea 2: Endpoint `/procesar-seleccionados` (1h)

**FASE 2: Frontend Filtrado** (8-10h) ⭐ CRÍTICA
- Tarea 3: FiltradoExpedientesDialog (5-6h)
- Tarea 4: Hook de filtros (1h)
- Tarea 5: Hook de selección masiva (1h)
- Tarea 6: Virtualización y paginación (2h)
- Tarea 7: Integración con flujo (1h)

**FASE 3: Procesamiento Selectivo** (6-8h)
- Tarea 8: `_procesar_expediente()` básico (2-3h)
- Tarea 9: Integrar guardado (1-2h)
- Tarea 10: Actualizar estados (1h)
- Tarea 11: DI Container (1h)

**FASE 4: Sistema de Monitoreo** (12-16h) 🆕
- Tarea 12: ComparadorExpedientes (2-3h)
- Tarea 13: ActualizadorJSONs (2-3h)
- Tarea 14: GestorConflictos (2h)
- Tarea 15: ServicioMonitor (3-4h)
- Tarea 16: Endpoints REST (2h)
- Tarea 17: Scheduler (1-2h)
- Tarea 18: UI Configuración (3-4h)
- Tarea 19: UI Dashboard (3-4h)
- Tarea 20: UI Conflictos (2-3h)

**FASE 5: Testing y Docs** (2-3h)
- Tarea 21: Tests completos (1-2h)
- Tarea 22: Documentación (1h)

### Estrategia de Implementación Recomendada:

**Opción A: MVP Rápido (Solo Fases 1-3)** ⭐ RECOMENDADO PARA EMPEZAR
- Tiempo: 17-22 horas
- Funcionalidad: Extracción → Filtrado → Procesamiento
- Sin monitoreo automático

**Opción B: Completo con Monitoreo (Fases 1-5)**
- Tiempo: 31-41 horas
- Funcionalidad: Todo + Monitoreo automático
- Producción ready

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

---

## 📚 DOCUMENTACIÓN RELACIONADA

1. **ARQUITECTURA_SISTEMA_MONITOREO.md** 🆕 - Documentación completa del sistema de monitoreo
2. **RESUMEN_DIAGNOSTICO_Y_PLAN_V2.md** - Resumen ejecutivo
3. **HOJA_RUTA_AGENTE_V2.md** - Guía práctica para agentes
4. **INDICE_DOCUMENTACION_EXTRACCION_MASIVA.md** - Índice de navegación

---

**FIN DEL PLAN V2.1**

**Última actualización:** 2025-11-10
**Versión:** 2.1 (Con Sistema de Monitoreo)
**Estado:** ✅ LISTO PARA IMPLEMENTACIÓN

**Cambios en V2.1:**
- ✅ Agregada Tarea 1B: Comparación automática en extracción masiva
- ✅ Agregada FASE 4 completa: Sistema de Monitoreo (Tareas 12-20)
- ✅ Documentada arquitectura de 3 capas JSON (BASE, SISTEMA, WORKSPACE)
- ✅ Documentada estrategia dual de extracción (parcial + total)
- ✅ Implementación de scheduler con APScheduler
- ✅ UI completa para configuración, dashboard y conflictos
- ✅ Total: 22 tareas, 31-41 horas (MVP: 17-22 horas)
