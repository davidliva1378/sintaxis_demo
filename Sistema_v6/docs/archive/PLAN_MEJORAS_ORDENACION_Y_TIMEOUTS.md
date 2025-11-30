# Plan de Mejoras: Ordenación y Timeouts

## Contexto

**Problema reportado en pruebas:**
1. Sistema navega a página de expedientes pero **NO ordena por fecha** (antes sí ordenaba)
2. Extracción empieza en orden alfabético (predeterminado del sitio)
3. Después de varias páginas, sitio PJN se vuelve lento
4. Sistema muestra "Error: error_desconocido. Reintentando en 5s..."
5. En reintento, muestra "error timeout" y cierra
6. Frontend no carga después de cerrar ventana de extracción

## Análisis de Causas

### 1. Ordenación que falla silenciosamente
**Archivo:** `pjn/scraping/expedientes.py:316-356`

La función `_aplicar_ordenamiento_tabla()`:
- Captura `TimeoutError` en línea 350 y solo loguea warning
- NO lanza excepción cuando falla
- Sistema continúa extracción sin ordenar (orden alfabético predeterminado)
- Usuario NO recibe indicación clara de que ordenación falló

**Timeout actual:** 15 segundos (`timeout_tabla_expedientes`)

### 2. Timeout sin captura en espera inicial de tabla
**Archivo:** `pjn/scraping/expedientes.py:593`

```python
await tabla.wait_for(state=STATE_VISIBLE, timeout=_config.scraping.timeout_tabla_expedientes)
```

- NO tiene try/except
- Si tabla tarda >15s en aparecer, lanza `TimeoutError` sin captura
- Excepción se propaga hasta `extractor_masivo.py:268`
- Activa sistema de reintentos

### 3. Clasificación de errores mejorable
**Archivo:** `extraccion_masiva/extractor_masivo.py:268-282`

El bloque `except Exception` clasifica errores como:
- "navegador_cerrado" si contiene keywords específicos
- "timeout_conexion" si contiene "timeout"
- "error_desconocido" para todo lo demás

**Problema:** El string "timeout" puede no aparecer en todos los TimeoutError, dependiendo del mensaje exacto.

### 4. Frontend no carga
**Causa:** Cache del navegador retiene estado antiguo
**Solución:** Hard refresh (Cmd+Shift+R en Mac, Ctrl+Shift+F5 en Windows/Linux)

## Correcciones Propuestas

### CORRECCIÓN 1: Aumentar timeout de ordenación (PRIORIDAD: MEDIA)
**Archivo:** `infrastructure/config/settings.py:88`

**Antes:**
```python
timeout_tabla_expedientes: int = 15000  # 15 segundos
```

**Después:**
```python
timeout_tabla_expedientes: int = 30000  # 30 segundos para sitios lentos
```

**Justificación:** Cuando PJN está lento, 15s no es suficiente. Duplicar a 30s reduce falsos timeouts.

---

### CORRECCIÓN 2: Mejorar logging en ordenación (PRIORIDAD: ALTA)
**Archivo:** `pjn/scraping/expedientes.py:341-353`

**Antes:**
```python
try:
    await page.select_option(_SEL_ORDEN_SELECT, value=valor_orden)
    await page.locator(_SEL_ORDENAR_LINK).click()
    try:
        await tabla.wait_for(state=STATE_HIDDEN, timeout=_config.scraping.timeout_default)
    except TimeoutError:
        pass
    await tabla.wait_for(state=STATE_VISIBLE, timeout=_config.scraping.timeout_tabla_expedientes)
    logger.info("🔽 Tabla ordenada por %s", orden.upper())
except TimeoutError as exc:
    logger.warning(
        "⚠️ El reordenamiento por %s no se completó a tiempo: %s", orden, exc
    )
```

**Después:**
```python
try:
    logger.info("🔄 Iniciando ordenamiento por %s...", orden.upper())
    await page.select_option(_SEL_ORDEN_SELECT, value=valor_orden)
    await page.locator(_SEL_ORDENAR_LINK).click()

    # Esperar que tabla se oculte (máx 8s)
    try:
        await tabla.wait_for(state=STATE_HIDDEN, timeout=_config.scraping.timeout_default)
        logger.debug("   ✓ Tabla ocultada")
    except TimeoutError:
        logger.warning("   ⚠️ Tabla no se ocultó, continuando...")

    # Esperar que tabla reaparezca ordenada (máx 30s)
    await tabla.wait_for(state=STATE_VISIBLE, timeout=_config.scraping.timeout_tabla_expedientes)
    logger.info("✅ Tabla ordenada por %s", orden.upper())
except TimeoutError as exc:
    logger.error(
        "❌ FALLO ORDENAMIENTO: Timeout ordenando por %s después de %dms: %s",
        orden,
        _config.scraping.timeout_tabla_expedientes,
        exc
    )
    logger.error("   ⚠️ Continuando extracción con orden PREDETERMINADO (alfabético)")
```

**Justificación:** Logging más detallado permite diagnosticar dónde falla el ordenamiento.

---

### CORRECCIÓN 3: Capturar timeout en espera inicial de tabla (PRIORIDAD: ALTA)
**Archivo:** `pjn/scraping/expedientes.py:591-593`

**Antes:**
```python
# Aseguramos presencia de tabla
tabla = page.locator(sel_tabla_final)
await tabla.wait_for(state=STATE_VISIBLE, timeout=_config.scraping.timeout_tabla_expedientes)
```

**Después:**
```python
# Aseguramos presencia de tabla
tabla = page.locator(sel_tabla_final)
try:
    await tabla.wait_for(state=STATE_VISIBLE, timeout=_config.scraping.timeout_tabla_expedientes)
    logger.debug("✓ Tabla de expedientes visible")
except TimeoutError as exc:
    logger.error("❌ Timeout esperando tabla de expedientes (>%dms)", _config.scraping.timeout_tabla_expedientes)
    raise TimeoutError(f"Tabla de expedientes no apareció en {_config.scraping.timeout_tabla_expedientes}ms") from exc
```

**Justificación:** Captura explícita con mensaje claro para debugging.

---

### CORRECCIÓN 4: Mejorar clasificación de errores (PRIORIDAD: MEDIA)
**Archivo:** `extraccion_masiva/extractor_masivo.py:268-282`

**Antes:**
```python
except Exception as e_intento:
    # Restaurar stdout en caso de error
    sys.stdout = old_stdout

    # Determinar tipo de error
    error_str = str(e_intento).lower()
    if any(keyword in error_str for keyword in ['target closed', 'browser', 'context closed', 'connection closed']):
        motivo = "navegador_cerrado"
        print(f"\n❌ El navegador se cerró inesperadamente durante intento {sesion.intentos_realizados}")
    elif 'timeout' in error_str:
        motivo = "timeout_conexion"
        print(f"\n❌ Timeout de conexión durante intento {sesion.intentos_realizados}")
    else:
        motivo = "error_desconocido"
        print(f"\n❌ Error durante intento {sesion.intentos_realizados}: {e_intento}")
```

**Después:**
```python
except Exception as e_intento:
    # Restaurar stdout en caso de error
    sys.stdout = old_stdout

    # Determinar tipo de error con mejor precisión
    error_str = str(e_intento).lower()
    error_type = type(e_intento).__name__

    if any(keyword in error_str for keyword in ['target closed', 'browser', 'context closed', 'connection closed']):
        motivo = "navegador_cerrado"
        print(f"\n❌ El navegador se cerró inesperadamente durante intento {sesion.intentos_realizados}")
    elif error_type == 'TimeoutError' or 'timeout' in error_str:
        motivo = "timeout_conexion"
        print(f"\n❌ Timeout de conexión durante intento {sesion.intentos_realizados}")
        print(f"   Detalles: {e_intento}")
    else:
        motivo = "error_desconocido"
        print(f"\n❌ Error durante intento {sesion.intentos_realizados}")
        print(f"   Tipo: {error_type}")
        print(f"   Mensaje: {e_intento}")
```

**Justificación:** Detectar `TimeoutError` por tipo de clase, no solo por string. Mejor logging para debugging.

---

### CORRECCIÓN 5: Documentar comportamiento de ordenación
**Archivo:** `pjn/scraping/expedientes.py:321-330` (docstring)

**Actualizar docstring:**
```python
"""Aplica ordenamiento a la tabla de expedientes si se especifica.

Args:
    page: Página de Playwright.
    tabla: Locator de la tabla de expedientes.
    orden: Criterio de orden ('fecha', 'caratula', 'oficina', 'situacion').

Raises:
    No lanza excepciones. Si el ordenamiento falla por timeout:
    - Loguea ERROR con detalles
    - Continúa extracción con orden PREDETERMINADO del sitio (alfabético por carátula)

Note:
    Cuando el sitio PJN está lento, el ordenamiento puede tardar >30s y fallar.
    En ese caso, la extracción continúa pero los resultados estarán en orden
    alfabético en lugar del orden solicitado.
"""
```

## Plan de Implementación

### Fase 1: Correcciones Críticas (ALTA PRIORIDAD)
1. ✅ **CORRECCIÓN 2**: Mejorar logging en ordenación
2. ✅ **CORRECCIÓN 3**: Capturar timeout en espera inicial de tabla

### Fase 2: Mejoras de Robustez (MEDIA PRIORIDAD)
3. ✅ **CORRECCIÓN 1**: Aumentar timeout de ordenación a 30s
4. ✅ **CORRECCIÓN 4**: Mejorar clasificación de errores

### Fase 3: Documentación (BAJA PRIORIDAD)
5. ✅ **CORRECCIÓN 5**: Documentar comportamiento de ordenación

## Testing

### Prueba 1: Ordenación con sitio rápido
1. Ejecutar extracción masiva
2. Verificar logs muestran "🔄 Iniciando ordenamiento por FECHA..."
3. Verificar logs muestran "✅ Tabla ordenada por FECHA"
4. Verificar expedientes extraídos están en orden cronológico

### Prueba 2: Ordenación con sitio lento (simulado)
1. Reducir temporalmente `timeout_tabla_expedientes` a 3000ms (3s)
2. Ejecutar extracción masiva
3. Verificar logs muestran "❌ FALLO ORDENAMIENTO: Timeout..."
4. Verificar logs muestran "⚠️ Continuando extracción con orden PREDETERMINADO"
5. Verificar extracción continúa (no falla)
6. Verificar expedientes están en orden alfabético

### Prueba 3: Timeout en espera de tabla
1. Reducir temporalmente `timeout_tabla_expedientes` a 3000ms
2. Intentar extracción cuando sitio está muy lento
3. Verificar error muestra "Tabla de expedientes no apareció en 3000ms"
4. Verificar sistema reintenta correctamente

### Prueba 4: Clasificación de errores
1. Provocar TimeoutError intencionalmente
2. Verificar se clasifica como "timeout_conexion"
3. Verificar logs muestran tipo de error y detalles

## Impacto Esperado

### Antes de las correcciones:
- Ordenación falla silenciosamente
- Usuario no sabe que extracción está en orden incorrecto
- Errors "desconocidos" dificultan debugging
- Timeouts de 15s insuficientes para sitios lentos

### Después de las correcciones:
- Logging claro indica éxito/fallo de ordenación
- Usuario informado si extracción usa orden predeterminado
- Errores clasificados precisamente (timeout vs desconocido vs navegador cerrado)
- Timeout de 30s más robusto para sitios lentos
- Mensajes de error informativos para debugging

## Notas Adicionales

### Frontend no carga - Solución inmediata
**Problema:** Después de cerrar ventana de extracción, frontend no carga

**Solución:**
1. Hacer hard refresh en el navegador:
   - **Mac**: `Cmd + Shift + R`
   - **Windows/Linux**: `Ctrl + Shift + F5`
2. Esto borra caché y fuerza recarga de todos los assets

### Consideración: ¿Hacer ordenación obligatoria?
Actualmente, si ordenación falla, continúa con orden predeterminado. Alternativas:
- **Opción A (actual)**: Continuar con orden predeterminado, loguear warning
- **Opción B**: Hacer ordenación obligatoria, fallar si no se puede ordenar
- **Opción C**: Agregar parámetro `ordenacion_obligatoria: bool = False`

**Recomendación:** Mantener Opción A. Ordenación fallida no debería abortar extracción completa.

### Timeouts recomendados
```python
timeout_default: 8000ms (8s)          # Operaciones rápidas
timeout_loading_hidden: 12000ms (12s)  # Elementos aparecer/desaparecer
timeout_tabla_expedientes: 30000ms (30s)  # Tablas grandes/sitios lentos
timeout_login: 60000ms (60s)          # Login puede ser lento
```
