# Plan de Corrección: Sistema de Extracción Masiva

## Resumen del Problema

El sistema de extracción masiva presenta dos problemas principales:
1. **Congelamiento en formulario de búsqueda**: El navegador llega al formulario pero no carga datos
2. **Detención post-descarga**: Después de descargar archivos, el proceso queda detenido

---

## PARTE 1: DIAGNÓSTICO - Problemas Identificados

### 1.1 Bugs Críticos en `gestor_batch.py`

| Problema | Ubicación | Impacto |
|----------|-----------|---------|
| Login espera "Menú" con 60s timeout sin retries | Línea 549 | Congelamiento inicial |
| Parámetros `max_paginas` y `tiempo_maximo_segundos` NO SE USAN | Constructor | Bucle infinito potencial |
| Fallback a expediente incorrecto si no hay match exacto | Líneas 274-284 | Datos incorrectos |

### 1.2 Bugs Críticos en `actuaciones.py` (pjn/scraping)

| Problema | Ubicación | Impacto |
|----------|-----------|---------|
| `while True` sin límite de páginas | Línea 772 | **BUCLE INFINITO** |
| `_esperar_cambio_pagina()` timeout 8s muy corto | Línea ~850 | Falla en PJN lento |
| `download.save_as()` sin timeout | Línea 1184 | Congelamiento en descarga |
| Sin manejo de casos donde página no cambia | Múltiples | Bucle infinito |

### 1.3 Manejo de Expedientes sin Actuaciones

**Comportamiento Actual:**
1. Navega al expediente correctamente
2. En `_extraer_actuaciones_actuales()` espera 8 segundos buscando filas
3. Si no hay filas → lanza `ActuacionesNoDisponibles` (timeout)
4. `gestor_batch.py` captura como ERROR genérico
5. **Resultado**: Expediente marcado como ERROR, desperdicio de 8 segundos

**Comportamiento Deseado:**
1. Verificar primero si existe la tabla de actuaciones
2. Si existe pero está vacía → retornar lista vacía inmediatamente
3. Marcar como "sin actuaciones" (no como error)
4. Continuar normalmente con el siguiente expediente

### 1.4 Diferencias con v5.1.1 (que funciona mejor)

| Aspecto | v5.1.1 | v6 (actual) |
|---------|--------|-------------|
| Browser por retry | Reutiliza | Crea nuevo (~5-10s overhead) |
| Timeouts | Simples | Redundantes (asyncio + page.goto) |
| Arquitectura | Directa | Más capas de abstracción |
| Login | Con retries | Sin retries |

---

## PARTE 2: PLAN DE CORRECCIÓN

### Fase 1: Correcciones Críticas (Bugs que causan congelamiento)

#### 1.1 Limitar bucle de paginación en `actuaciones.py`

**Archivo**: `Sistema_v6/pjn/scraping/actuaciones.py`

```python
# ANTES (línea ~772):
while True:
    # procesar página
    if not hay_siguiente:
        break

# DESPUÉS:
MAX_PAGINAS = 500  # Límite de seguridad
pagina_actual = 0
while pagina_actual < MAX_PAGINAS:
    pagina_actual += 1
    # procesar página
    if not hay_siguiente:
        break
else:
    logger.warning(f"Límite de {MAX_PAGINAS} páginas alcanzado")
```

#### 1.2 Aumentar timeout de espera de página

**Archivo**: `Sistema_v6/pjn/scraping/actuaciones.py`

```python
# ANTES:
async def _esperar_cambio_pagina(self, pagina_esperada: int, timeout: float = 8.0):

# DESPUÉS:
async def _esperar_cambio_pagina(self, pagina_esperada: int, timeout: float = 30.0):
```

#### 1.3 Agregar timeout a descargas

**Archivo**: `Sistema_v6/pjn/scraping/actuaciones.py`

```python
# ANTES (línea ~1184):
await download.save_as(archivo_destino)

# DESPUÉS:
try:
    await asyncio.wait_for(
        download.save_as(archivo_destino),
        timeout=60.0  # 60 segundos por archivo
    )
except asyncio.TimeoutError:
    logger.error(f"Timeout descargando archivo: {archivo_destino}")
    raise
```

#### 1.4 Agregar retries al login en `gestor_batch.py`

**Archivo**: `Sistema_v6/extraccion_masiva/gestor_batch.py`

```python
# ANTES (línea ~549):
await page.wait_for_selector('text="Menú"', timeout=60000)

# DESPUÉS:
MAX_LOGIN_RETRIES = 3
for intento in range(MAX_LOGIN_RETRIES):
    try:
        await page.wait_for_selector('text="Menú"', timeout=60000)
        break
    except Exception as e:
        if intento < MAX_LOGIN_RETRIES - 1:
            logger.warning(f"Reintento login {intento + 1}/{MAX_LOGIN_RETRIES}")
            await asyncio.sleep(5)
        else:
            raise
```

#### 1.5 Manejar expedientes sin actuaciones

**Archivo**: `Sistema_v6/pjn/scraping/actuaciones.py`

```python
# ANTES (línea ~884-891):
async def _extraer_actuaciones_actuales(...):
    try:
        await page.wait_for_selector(
            r"#expediente\:action-table tbody tr", timeout=8000
        )
    except PlaywrightTimeout as exc:
        raise ActuacionesNoDisponibles(
            "No se encontró la tabla de actuaciones en el tiempo esperado"
        ) from exc

# DESPUÉS:
async def _extraer_actuaciones_actuales(...):
    # Primero verificar si la tabla existe
    tabla = await page.query_selector(r"#expediente\:action-table")
    if not tabla:
        raise ActuacionesNoDisponibles("No existe tabla de actuaciones")

    # Verificar si hay filas (sin timeout largo)
    filas = await page.query_selector_all(r"#expediente\:action-table tbody tr")
    if not filas:
        # Expediente sin actuaciones - retornar lista vacía
        logger.info("Expediente sin actuaciones")
        return []

    # Continuar con la extracción normal...
```

**Archivo**: `Sistema_v6/extraccion_masiva/gestor_batch.py`

```python
# En el manejo de resultados:
if not actuaciones and not error:
    # Expediente procesado correctamente pero sin actuaciones
    logger.info(f"Expediente {numero} sin actuaciones")
    return {
        "success": True,  # No es un error
        "numero": numero_expediente,
        "actuaciones": 0,
        "mensaje": "Expediente sin actuaciones"
    }
```

### Fase 2: Mejoras de Estabilidad

#### 2.1 Usar los parámetros max_paginas y tiempo_maximo

**Archivo**: `Sistema_v6/extraccion_masiva/gestor_batch.py`

El constructor recibe `max_paginas` y `tiempo_maximo_segundos` pero NO SE USAN en ninguna parte del código. Implementar:

```python
# En el método de extracción de actuaciones:
tiempo_inicio = time.time()
paginas_procesadas = 0

while True:
    # Verificar límites
    if self.max_paginas and paginas_procesadas >= self.max_paginas:
        logger.info(f"Límite de páginas alcanzado: {self.max_paginas}")
        break

    if self.tiempo_maximo_segundos:
        tiempo_transcurrido = time.time() - tiempo_inicio
        if tiempo_transcurrido >= self.tiempo_maximo_segundos:
            logger.info(f"Tiempo máximo alcanzado: {self.tiempo_maximo_segundos}s")
            break

    # ... procesar página ...
    paginas_procesadas += 1
```

#### 2.2 Coordinar timeouts

```python
# Valores sugeridos consistentes:
TIMEOUT_LOGIN = 60  # segundos
TIMEOUT_NAVEGACION = 30  # segundos
TIMEOUT_CAMBIO_PAGINA = 30  # segundos
TIMEOUT_DESCARGA = 60  # segundos por archivo
TIMEOUT_OPERACION_TOTAL = 3600  # 1 hora máximo por expediente
```

### Fase 3: Simplificación (como v5.1.1)

#### 3.1 Reutilizar browser en reintentos

**Archivo**: `Sistema_v6/extraccion_masiva/extractor_masivo.py`

```python
# ANTES: Crea nuevo browser en cada retry
for intento in range(max_reintentos):
    browser = await playwright.chromium.launch()  # Lento: 5-10s

# DESPUÉS: Reutilizar browser, solo nueva página
browser = await playwright.chromium.launch()
for intento in range(max_reintentos):
    page = await browser.new_page()  # Rápido: <1s
    try:
        # ... operación ...
    finally:
        await page.close()
```

#### 3.2 Simplificar timeouts redundantes

```python
# ANTES (redundante):
await asyncio.wait_for(
    page.goto(url, timeout=30000),  # Timeout interno Playwright
    timeout=35.0  # Timeout externo asyncio
)

# DESPUÉS (simple):
await page.goto(url, timeout=30000)  # Solo usar timeout de Playwright
```

---

## PARTE 3: ORDEN DE IMPLEMENTACIÓN

### Prioridad 1: Crítico (Resolver congelamientos)

| # | Tarea | Archivo | Riesgo |
|---|-------|---------|--------|
| 1 | Limitar `while True` con MAX_PAGINAS | `actuaciones.py` | Alto |
| 2 | Aumentar timeout cambio página (8s → 30s) | `actuaciones.py` | Medio |
| 3 | Agregar timeout a `download.save_as()` | `actuaciones.py` | Alto |
| 4 | Agregar retries a login | `gestor_batch.py` | Medio |
| 5 | Manejar expedientes sin actuaciones | `actuaciones.py`, `gestor_batch.py` | Medio |

### Prioridad 2: Estabilidad

| # | Tarea | Archivo | Riesgo |
|---|-------|---------|--------|
| 6 | Implementar uso de max_paginas/tiempo_maximo | `gestor_batch.py` | Bajo |
| 7 | Unificar constantes de timeout | Múltiples | Bajo |

### Prioridad 3: Optimización

| # | Tarea | Archivo | Riesgo |
|---|-------|---------|--------|
| 8 | Reutilizar browser en reintentos | `extractor_masivo.py` | Medio |
| 9 | Eliminar timeouts redundantes | Múltiples | Bajo |

---

## PARTE 4: ARCHIVOS A MODIFICAR

| Archivo | Cambios | Líneas Aprox. |
|---------|---------|---------------|
| `Sistema_v6/pjn/scraping/actuaciones.py` | Límite páginas, timeouts, 0-actuaciones | 772, 850, 884, 1184 |
| `Sistema_v6/extraccion_masiva/gestor_batch.py` | Login retries, usar parámetros, 0-actuaciones | 549, 274-284 |
| `Sistema_v6/extraccion_masiva/extractor_masivo.py` | Reutilizar browser | ~200-300 |

---

## PARTE 5: VERIFICACIÓN

### Tests a ejecutar después de cada cambio:

1. **Test básico**: Extraer 1 expediente con pocas actuaciones
2. **Test paginación**: Extraer expediente con >10 páginas de actuaciones
3. **Test timeout**: Verificar que no se congela en PJN lento
4. **Test sin actuaciones**: Extraer expediente sin actuaciones (verificar que no marca como error)

### Métricas de éxito:

- [ ] No hay congelamientos en formulario de búsqueda
- [ ] Proceso termina después de descargar archivos
- [ ] Expedientes sin actuaciones se marcan correctamente (no como error)
- [ ] Tiempo por expediente < 10 minutos (promedio)

---

## NOTAS ADICIONALES

### Comparación rama produccion_v5.1.1

La rama `produccion_v5.1.1` funciona mejor porque:
1. Arquitectura más directa, menos capas de abstracción
2. Reutiliza conexiones de browser
3. Timeouts más simples y generosos
4. Manejo de errores más robusto en puntos críticos

### Riesgos a considerar

1. **Cambios en actuaciones.py**: Este archivo es crítico para toda la extracción
2. **Timeouts**: Valores muy altos pueden causar esperas largas en errores reales

### Recomendación

Implementar cambios de Prioridad 1 primero y probar exhaustivamente antes de continuar con Prioridad 2 y 3.
