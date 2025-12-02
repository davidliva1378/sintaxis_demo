# Plan: Mejorar Feedback Durante Procesamiento de Expedientes en Extracción Masiva

**Fecha:** 2024-12-01
**Estado:** Aprobado para implementación
**Problema:** Durante `procesar_expediente_completo()` en extracción masiva, la UI parece congelada - no hay feedback del proceso de extracción de texto, clasificación, NER, embeddings, etc.

---

## Diagnóstico del Problema

### Síntoma
- La extracción masiva muestra progreso durante descarga de expedientes/PDFs
- Cuando pasa a `procesar_expediente_completo()`, la ventana no ofrece información
- El sistema parece "congelado" aunque está procesando internamente

### Causa Raíz

**Diferencia crítica entre flujos:**

| Aspecto | Extracción Masiva | Ver Detalle → Procesar |
|---------|-------------------|------------------------|
| Comunicación | POLLING cada 1s | STREAMING (NDJSON) tiempo real |
| Granularidad | Nivel página PJN | Nivel actuación individual |
| Fases visibles | Solo "Extrayendo" | extracción→clasificación→IA→entidades→guardado |
| Estado IA | Invisible | Visible (eventos `analyzing`) |

**El flujo de detalle emite eventos detallados:**
- `start` - Inicio
- `progress` - Por cada actuación (extracción texto, clasificación)
- `analyzing` - Duplicados, NER, RAG
- `saving` - Guardado en BD
- `complete` - Resultado final

**El flujo masivo NO emite estos eventos durante `procesar_expediente_completo()`**

---

## Decisiones del Usuario

- **Granularidad:** Ambos (fase actual + progreso por actuación)
- **Arquitectura:** Polling (mantener sistema existente, agregar datos)

---

## Solución Propuesta

### Enfoque: Agregar callback de progreso a `procesar_expediente_completo()`

Mantener el polling cada 1s existente pero agregar datos detallados:
1. `GestorBatch` pasa callback al llamar `procesar_expediente_completo()`
2. El callback actualiza el estado de la sesión con fase + actuación actual
3. El frontend recibe los updates via el polling existente

### Implementación

#### Paso 1: Modificar `procesar_expediente_completo()` para aceptar callback

**Archivo:** `application/services/procesador_actuaciones_service.py`

```python
async def procesar_expediente_completo(
    self,
    numero_expediente: str,
    actuaciones: List[Dict],
    rutas_pdf: Dict[str, str] = None,
    guardar_en_bd: bool = True,
    progress_callback: Callable[[str, int, int, str], None] = None  # NUEVO
) -> Dict[str, Any]:
    """
    Args:
        progress_callback: Función(fase, actual, total, mensaje) para reportar progreso
    """
    total = len(actuaciones)

    # Al iniciar
    if progress_callback:
        progress_callback("procesando", 0, total, f"Iniciando procesamiento de {total} actuaciones...")

    # Durante extracción de texto/clasificación (loop principal)
    for i, actuacion in enumerate(actuaciones):
        if progress_callback:
            progress_callback("procesando", i+1, total, f"Actuación {i+1}/{total}: Extrayendo texto...")
        # ... proceso existente

    # Durante análisis IA
    if progress_callback:
        progress_callback("ia", 0, total, "Procesando con IA (clasificación, entidades, embeddings)...")

    # Durante guardado
    if progress_callback:
        progress_callback("guardando", 0, total, "Guardando resultados en base de datos...")
```

#### Paso 2: Modificar `GestorBatch` para pasar callback

**Archivo:** `extraccion_masiva/gestor_batch.py`

```python
# En procesar_seleccionados(), cuando llama a procesar_expediente_completo():

def _crear_callback_procesamiento(self, expediente_num: str):
    """Crea callback que actualiza el estado de la sesión."""
    def callback(fase: str, actual: int, total: int, mensaje: str):
        if self.callback_progreso:
            self.callback_progreso({
                "fase": f"procesando_{fase}",
                "expediente_actual": expediente_num,
                "actuacion_actual": actual,
                "actuaciones_total": total,
                "mensaje": mensaje
            })
    return callback

# Uso:
await procesador.procesar_expediente_completo(
    numero_expediente=numero_expediente,
    actuaciones=actuaciones,
    progress_callback=self._crear_callback_procesamiento(numero_expediente)
)
```

#### Paso 3: Actualizar modelo de sesión

**Archivo:** `extraccion_masiva/modelos.py`

```python
@dataclass
class SesionExtraccion:
    # ... campos existentes ...

    # NUEVOS campos para procesamiento:
    expediente_procesando: Optional[str] = None
    actuacion_actual: int = 0
    actuaciones_total: int = 0
    fase_procesamiento: str = ""  # "extrayendo_texto", "clasificando", "ia", "guardando"
    mensaje_procesamiento: str = ""
```

#### Paso 4: Actualizar endpoint de sesión

**Archivo:** `presentation/api/rest/routers/extraccion_masiva.py`

```python
@router.get("/sesion/{session_id}")
async def obtener_sesion(session_id: str):
    sesion = _sesiones.get(session_id)
    return {
        # ... campos existentes ...

        # NUEVOS campos:
        "expediente_procesando": sesion.expediente_procesando,
        "actuacion_actual": sesion.actuacion_actual,
        "actuaciones_total": sesion.actuaciones_total,
        "fase_procesamiento": sesion.fase_procesamiento,
        "mensaje_procesamiento": sesion.mensaje_procesamiento
    }
```

#### Paso 5: Actualizar UI de progreso

**Archivo:** `frontend/src/components/expedientes/extraccion/ExtraccionProgreso.tsx`

Agregar sección que muestre:
```tsx
{progreso.fase_procesamiento && (
  <div className="mt-4 p-3 bg-blue-50 rounded">
    <div className="font-medium">
      Procesando: {progreso.expediente_procesando}
    </div>
    <Progress
      value={(progreso.actuacion_actual / progreso.actuaciones_total) * 100}
    />
    <div className="text-sm text-gray-600">
      {progreso.mensaje_procesamiento}
    </div>
    <div className="text-xs">
      Actuación {progreso.actuacion_actual} de {progreso.actuaciones_total}
    </div>
  </div>
)}
```

---

## Archivos a Modificar

| Archivo | Cambio | Prioridad |
|---------|--------|-----------|
| `application/services/procesador_actuaciones_service.py` | Agregar `progress_callback` param | P0 |
| `extraccion_masiva/gestor_batch.py` | Crear y pasar callback | P0 |
| `extraccion_masiva/modelos.py` | Agregar campos de procesamiento | P0 |
| `presentation/api/rest/routers/extraccion_masiva.py` | Retornar nuevos campos | P0 |
| `frontend/src/stores/extraccionStore.ts` | Mapear nuevos campos | P1 |
| `frontend/src/components/expedientes/extraccion/ExtraccionProgreso.tsx` | Mostrar progreso detallado | P1 |

---

## Beneficios de este enfoque

1. **Mínimo cambio arquitectónico** - Mantiene polling existente, solo agrega datos
2. **Reutilizable** - El callback puede usarse en otros contextos
3. **Backwards compatible** - El callback es opcional
4. **Granularidad configurable** - Puede emitir con más o menos frecuencia
