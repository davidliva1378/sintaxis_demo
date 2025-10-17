# Sprint 1, Tarea 1.3: Validación de Recursos I/O

**Estado:** ✅ Completada
**Fecha:** 2025-10-16
**Estimación:** 4 horas
**Tiempo real:** ~4 horas
**Branch:** `refactor/validacion-recursos-io`
**Commits:** 3ad4c3d

---

## 📋 Objetivo

Agregar validaciones explícitas para operaciones de I/O (lectura/escritura de archivos) antes de ejecutarlas, mejorando el manejo de errores y los mensajes descriptivos para facilitar el debugging.

**Funciones identificadas para mejora:**
- `descargar_archivos_de_json()` - Lee y escribe archivos JSON
- `obtener_actuaciones_todas_paginas_async()` - Guarda archivos JSON
- `actualizar_actuaciones_desde_json()` - Lee y actualiza archivos JSON

---

## ✅ Cambios Implementados

### 1. Función: `descargar_archivos_de_json()`

**Ubicación:** `pjn/scraping/actuaciones.py:1205`

#### ANTES (sin validaciones adecuadas)

```python
async def descargar_archivos_de_json(page, carpeta_destino: str):
    if not carpeta_destino:
        logger.warning("⚠️ Carpeta destino no proporcionada.")
        return

    os.makedirs(carpeta_destino, exist_ok=True)

    archivos_json = [f for f in os.listdir(carpeta_destino)
                     if f.startswith("actuaciones-") and f.endswith(".json")]

    if archivos_json:
        ruta_json = os.path.join(carpeta_destino, archivos_json[0])
        with open(ruta_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        # ... resto del código
```

**Problemas:**
- ❌ No valida si la ruta es un directorio válido
- ❌ No maneja errores al listar archivos
- ❌ No valida permisos de lectura
- ❌ No valida que el JSON sea válido
- ❌ No valida permisos de escritura antes de guardar

#### DESPUÉS (con validaciones completas)

```python
async def descargar_archivos_de_json(page, carpeta_destino: str):
    if not carpeta_destino:
        logger.warning("⚠️ Carpeta destino no proporcionada.")
        return

    # Validar que la carpeta destino existe
    if not os.path.exists(carpeta_destino):
        try:
            os.makedirs(carpeta_destino, exist_ok=True)
            logger.debug("📁 Carpeta creada: %s", carpeta_destino)
        except OSError as e:
            logger.error("❌ Error al crear carpeta %s: %s", carpeta_destino, e)
            return

    # Validar que es un directorio
    if not os.path.isdir(carpeta_destino):
        logger.error("❌ La ruta no es un directorio: %s", carpeta_destino)
        return

    # Buscar archivos JSON de actuaciones
    try:
        archivos_json = [f for f in os.listdir(carpeta_destino)
                         if f.startswith("actuaciones-") and f.endswith(".json")]
    except OSError as e:
        logger.error("❌ Error al listar archivos en %s: %s", carpeta_destino, e)
        return

    if archivos_json:
        ruta_json = os.path.join(carpeta_destino, archivos_json[0])

        # Validar que el archivo existe
        if not os.path.exists(ruta_json):
            logger.error("❌ Archivo JSON no encontrado: %s", ruta_json)
            return

        # Validar que el archivo es legible
        if not os.access(ruta_json, os.R_OK):
            logger.error("❌ Sin permisos de lectura para: %s", ruta_json)
            return

        try:
            with open(ruta_json, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error("❌ El archivo no contiene JSON válido (%s): %s", ruta_json, e)
            return
        except OSError as e:
            logger.error("❌ Error al leer archivo %s: %s", ruta_json, e)
            return

        # ... procesamiento ...

        # Validar permisos de escritura antes de guardar
        if not os.access(carpeta_destino, os.W_OK):
            logger.error("❌ Sin permisos de escritura en: %s", carpeta_destino)
            return

        try:
            with open(ruta_json, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("📝 JSON actualizado con estado de descarga.")
        except OSError as e:
            logger.error("❌ Error al guardar archivo %s: %s", ruta_json, e)
            return
```

**Mejoras:**
- ✅ Valida existencia de carpeta y la crea con manejo de errores
- ✅ Valida que la ruta es un directorio
- ✅ Maneja errores al listar archivos con try/except
- ✅ Valida permisos de lectura con `os.access()`
- ✅ Valida formato JSON con `json.JSONDecodeError`
- ✅ Valida permisos de escritura antes de guardar
- ✅ Logging descriptivo con emojis para cada error

---

### 2. Función: `obtener_actuaciones_todas_paginas_async()`

**Ubicación:** `pjn/scraping/actuaciones.py:509-534`

#### ANTES

```python
carpeta_actuaciones = os.path.abspath(carpeta_destino)
os.makedirs(carpeta_actuaciones, exist_ok=True)
json_path = os.path.join(carpeta_actuaciones, f"actuaciones-{expediente_numero}.json")

with open(json_path, "w", encoding="utf-8") as f:
    json.dump({"Expediente": encabezado, "Actuaciones": todas}, f, indent=2, ensure_ascii=False)

logger.info("✅ Archivo JSON guardado: %s", json_path)
```

#### DESPUÉS

```python
carpeta_actuaciones = os.path.abspath(carpeta_destino)

# Validar y crear carpeta si no existe
try:
    os.makedirs(carpeta_actuaciones, exist_ok=True)
except OSError as e:
    logger.error("❌ Error al crear carpeta %s: %s", carpeta_actuaciones, e)
    return todas, f"Error al crear carpeta: {e}", None

# Validar permisos de escritura
if not os.access(carpeta_actuaciones, os.W_OK):
    error_msg = f"Sin permisos de escritura en: {carpeta_actuaciones}"
    logger.error("❌ %s", error_msg)
    return todas, error_msg, None

json_path = os.path.join(carpeta_actuaciones, f"actuaciones-{expediente_numero}.json")

# Guardar archivo JSON con manejo de errores
try:
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"Expediente": encabezado, "Actuaciones": todas}, f, indent=2, ensure_ascii=False)
    logger.info("✅ Archivo JSON guardado: %s", json_path)
except OSError as e:
    error_msg = f"Error al guardar archivo {json_path}: {e}"
    logger.error("❌ %s", error_msg)
    return todas, error_msg, None
```

**Mejoras:**
- ✅ Manejo de errores al crear carpeta
- ✅ Validación de permisos de escritura
- ✅ Manejo de errores al guardar archivo
- ✅ Retorna mensajes de error descriptivos

---

### 3. Función: `actualizar_actuaciones_desde_json()`

**Ubicación:** `pjn/scraping/actuaciones.py:569-735`

#### ANTES

```python
if not ruta_json_existente or not os.path.exists(ruta_json_existente):
    return 0, None, "El archivo de actuaciones especificado no existe."

try:
    with open(ruta_json_existente, "r", encoding="utf-8") as f:
        data = json.load(f)
except Exception as e:  # noqa: BLE001
    return 0, None, f"No se pudo leer el JSON existente: {type(e).__name__}: {str(e)}"

# ... procesamiento ...

try:
    with open(ruta_json_existente, "w", encoding="utf-8") as f:
        json.dump(nuevo_payload, f, indent=2, ensure_ascii=False)
except Exception as e:  # noqa: BLE001
    return 0, None, f"No se pudo actualizar el JSON: {type(e).__name__}: {str(e)}"
```

#### DESPUÉS

```python
# Validar que la ruta fue proporcionada
if not ruta_json_existente:
    return 0, None, "No se proporcionó ruta al archivo de actuaciones."

# Validar que el archivo existe
if not os.path.exists(ruta_json_existente):
    return 0, None, f"El archivo de actuaciones no existe: {ruta_json_existente}"

# Validar que es un archivo regular
if not os.path.isfile(ruta_json_existente):
    return 0, None, f"La ruta no es un archivo válido: {ruta_json_existente}"

# Validar permisos de lectura
if not os.access(ruta_json_existente, os.R_OK):
    return 0, None, f"Sin permisos de lectura para: {ruta_json_existente}"

try:
    with open(ruta_json_existente, "r", encoding="utf-8") as f:
        data = json.load(f)
except json.JSONDecodeError as e:
    return 0, None, f"El archivo no contiene JSON válido: {e}"
except OSError as e:
    return 0, None, f"Error al leer el archivo: {e}"

# ... procesamiento ...

# Validar permisos de escritura antes de guardar
carpeta_json = os.path.dirname(ruta_json_existente)
if not os.access(carpeta_json, os.W_OK):
    return 0, None, f"Sin permisos de escritura en: {carpeta_json}"

try:
    with open(ruta_json_existente, "w", encoding="utf-8") as f:
        json.dump(nuevo_payload, f, indent=2, ensure_ascii=False)
except OSError as e:
    return 0, None, f"Error al guardar el archivo: {e}"
```

**Mejoras:**
- ✅ Validaciones separadas para cada condición
- ✅ Diferencia entre archivo inexistente vs no es archivo
- ✅ Validación explícita de permisos de lectura
- ✅ Excepción específica `json.JSONDecodeError` en lugar de `Exception`
- ✅ Validación de permisos de escritura antes de guardar
- ✅ Excepción específica `OSError` en lugar de `Exception`
- ✅ Mensajes de error más descriptivos con la ruta incluida

---

## 🧪 Tests Creados

**Archivo:** `Sistema_v5/tests/test_io_validations.py`
**Tamaño:** 313 líneas

### Suite de Tests

#### TestValidacionesLectura (5 tests)

| Test | Descripción | Estado |
|------|-------------|--------|
| `test_actualizar_actuaciones_sin_ruta` | Valida error si no se proporciona ruta | ✅ PASS |
| `test_actualizar_actuaciones_archivo_no_existe` | Valida error si archivo no existe | ✅ PASS |
| `test_actualizar_actuaciones_no_es_archivo` | Valida error si ruta es directorio | ✅ PASS |
| `test_actualizar_actuaciones_json_invalido` | Valida error si JSON es inválido | ✅ PASS |
| `test_actualizar_actuaciones_sin_permisos_lectura` | Valida error si no hay permisos | ✅ PASS |

#### TestValidacionesEscritura (1 test)

| Test | Descripción | Estado |
|------|-------------|--------|
| `test_escribir_sin_permisos_reporta_error` | Valida manejo de errores de escritura | ✅ PASS |

#### TestValidacionesDescargarArchivos (6 tests)

| Test | Descripción | Estado |
|------|-------------|--------|
| `test_descargar_sin_carpeta` | Maneja correctamente carpeta vacía | ✅ PASS |
| `test_descargar_crea_carpeta_si_no_existe` | Crea carpeta si no existe | ✅ PASS |
| `test_descargar_ruta_no_es_directorio` | Maneja error si ruta es archivo | ✅ PASS |
| `test_descargar_json_no_encontrado` | Maneja cuando no hay JSONs | ✅ PASS |
| `test_descargar_json_invalido` | Maneja JSON inválido | ✅ PASS |
| `test_descargar_json_valido_procesa_correctamente` | Procesa JSON válido correctamente | ✅ PASS |

#### TestMensajesError (2 tests)

| Test | Descripción | Estado |
|------|-------------|--------|
| `test_mensaje_error_archivo_no_existe_incluye_ruta` | Error incluye ruta del archivo | ✅ PASS |
| `test_mensaje_error_json_invalido_es_claro` | Error de JSON es claro | ✅ PASS |

#### TestIntegracionValidaciones (1 test)

| Test | Descripción | Estado |
|------|-------------|--------|
| `test_flujo_completo_con_archivo_valido` | Flujo completo funciona | ✅ PASS |

**Resultado:**
```
============================
15 passed in 0.04s
============================
```

---

## 📊 Métricas

### Código

| Métrica | Antes | Después | Mejora |
|---------|-------|---------|--------|
| Validaciones de existencia | 1 | 5 | +400% |
| Validaciones de permisos | 0 | 5 | +∞ |
| Validaciones de formato | 0 | 2 | +∞ |
| Manejo de errores específicos | 2 | 10 | +400% |
| Logging con emojis | 5 | 15 | +200% |
| Líneas de código (neto) | - | +115 | - |

### Tests

| Métrica | Valor |
|---------|-------|
| Tests nuevos | 15 |
| Tests pasando | 15 (100%) |
| Categorías cubiertas | 5 |
| Tiempo ejecución | 0.04s |

### Calidad de Mensajes

| Aspecto | Antes | Después |
|---------|-------|---------|
| Incluye ruta en error | A veces | Siempre ✅ |
| Diferencia tipo de error | No | Sí ✅ |
| Mensajes descriptivos | Básicos | Detallados ✅ |
| Emojis para visibilidad | Pocos | Muchos ✅ |

---

## 🎯 Validaciones Implementadas

### Resumen por Tipo

| Tipo de Validación | Cantidad | Funciones |
|-------------------|----------|-----------|
| **Existencia de archivos** | 3 | descargar_archivos_de_json, actualizar_actuaciones_desde_json |
| **Existencia de carpetas** | 2 | descargar_archivos_de_json, obtener_actuaciones_todas_paginas_async |
| **Tipo de recurso** | 2 | descargar_archivos_de_json, actualizar_actuaciones_desde_json |
| **Permisos de lectura** | 2 | descargar_archivos_de_json, actualizar_actuaciones_desde_json |
| **Permisos de escritura** | 3 | Todas las funciones |
| **Formato JSON válido** | 2 | descargar_archivos_de_json, actualizar_actuaciones_desde_json |
| **Manejo OSError** | 6 | Todas las funciones |

**Total:** 20+ validaciones explícitas agregadas

---

## 🎯 Objetivos Alcanzados

- [x] Identificar funciones de I/O sin validación
- [x] Agregar validaciones de existencia de archivos/carpetas
- [x] Agregar validaciones de permisos (lectura/escritura)
- [x] Validar formato JSON antes de procesar
- [x] Mejorar mensajes de error con información descriptiva
- [x] Crear suite de tests comprehensiva
- [x] Verificar que todos los tests pasen
- [x] Actualizar tracking de sprints
- [x] Mergear a v5.6

---

## 📝 Lecciones Aprendidas

### ✅ Lo que funcionó bien

1. **Validaciones en capas**
   - Validar primero existencia, luego tipo, luego permisos, luego formato
   - Cada validación retorna mensaje de error específico

2. **os.access() para permisos**
   - Mejor que try/except para validar permisos
   - Permite verificar antes de intentar la operación

3. **Excepciones específicas**
   - `json.JSONDecodeError` en lugar de `Exception`
   - `OSError` en lugar de `Exception`
   - Facilita debugging

4. **Logging con emojis**
   - ❌ para errores
   - ✅ para éxitos
   - 📁 para operaciones de carpetas
   - 📝 para operaciones de archivos
   - Mejora la visibilidad en logs

5. **Tests con tmp_path**
   - Fixture de pytest perfecto para tests de I/O
   - Cleanup automático después de tests

### 🔍 Áreas de mejora para próximas tareas

1. **Validaciones en más funciones**
   - Hay otras funciones de I/O que podrían beneficiarse
   - Considerar crear helper functions para validaciones comunes

2. **Retry logic**
   - Para errores transitorios (ej: permisos temporalmente bloqueados)
   - Agregar exponential backoff

3. **Telemetría**
   - Registrar cuántas veces fallan validaciones
   - Ayudaría a identificar problemas comunes

---

## 🚀 Próximos Pasos

Este cierra las **3 tareas críticas del Sprint 1**. El Sprint 1 está completado al 100%.

### Sprint 1: Estado Final
```
████████████████████████ 100%

✅ Tarea 1.1: Consolidar código duplicado
✅ Tarea 1.2: Deprecar side effects
✅ Tarea 1.3: Validación de recursos I/O

Estado: COMPLETADO
```

### Próximo: Sprint 2 - Refactorización

**Tareas estimadas:**
- Tarea 2.1: Refactorizar `extraer_actuaciones_datos()` (8h)
- Tarea 2.2: Refactorizar `extraer_expedientes_completos()` (10h)
- Tarea 2.3: Crear objetos de configuración (6h)

---

## 📎 Referencias

- **Commits:**
  - `3ad4c3d` - Implementación de validaciones I/O

- **Archivos modificados:**
  - `Sistema_v5/pjn/scraping/actuaciones.py` (+115 líneas netas)
  - `Sistema_v5/tests/test_io_validations.py` (313 líneas nuevas)
  - `Sistema_v5/documentacion/TRACKING_SPRINTS.md` (actualizado)

- **Documentación:**
  - [Hoja de Ruta Completa](./HOJA_DE_RUTA_MEJORAS.md)
  - [Tracking de Sprints](./TRACKING_SPRINTS.md)
  - [Reporte Final Sprint 1](./SPRINT_1_REPORTE_FINAL.md)

---

**Completado por:** Claude
**Fecha:** 2025-10-16
**Tiempo:** ~4 horas
**Sprint 1 Progreso:** 100% (3/3 tareas completadas)
