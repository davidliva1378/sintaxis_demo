# Sprint 1, Tarea 1.2: Deprecar Funciones con Side Effects

**Estado:** ✅ Completada
**Fecha:** 2025-10-16
**Estimación:** 3 horas
**Tiempo real:** ~3 horas
**Branch:** `refactor/deprecar-side-effects`
**Commits:** 2dc0dbd
**Merge commit:** 559c572

---

## 📋 Objetivo

Marcar como deprecated las funciones que mutan argumentos in-place (side effects), agregar warnings informativos, y crear guía de migración completa para facilitar la transición a funciones puras.

**Funciones identificadas:**
- `actualizar_metricas_descargas_en_json()` - muta payload in-place
- `descargar_archivos_actuaciones()` - muta lista de actuaciones in-place

---

## ✅ Cambios Implementados

### 1. Warnings de Deprecación Agregados

#### Función 1: `actualizar_metricas_descargas_en_json()`

**ANTES (sin warning):**
```python
def actualizar_metricas_descargas_en_json(payload: dict) -> None:
    """Recalcula los contadores de descargas dentro de la estructura JSON.

    Deprecated:
        Esta función modifica el payload in-place (side effect).
        Usar calcular_metricas_descargas_json() que retorna una copia.

    Warning:
        Esta función MUTA el argumento payload.
    """
    # ... código de implementación sin warning
```

**DESPUÉS (con warning):**
```python
def actualizar_metricas_descargas_en_json(payload: dict) -> None:
    """Recalcula los contadores de descargas dentro de la estructura JSON.

    .. deprecated:: 5.6
        Esta función modifica el payload in-place (side effect).
        Usar :func:`calcular_metricas_descargas_json` que retorna una copia inmutable.
        Esta función será eliminada en la versión 6.0.

    Warning:
        Esta función MUTA el argumento payload. Para código nuevo, use
        ``calcular_metricas_descargas_json()`` que retorna una copia modificada
        sin alterar el original.

    Args:
        payload: Diccionario con estructura JSON de expediente.

    Example:
        >>> # ❌ MAL - Muta el original
        >>> actualizar_metricas_descargas_en_json(payload)
        >>>
        >>> # ✅ BIEN - Retorna copia
        >>> nuevo_payload = calcular_metricas_descargas_json(payload)
    """
    warnings.warn(
        "actualizar_metricas_descargas_en_json() está deprecated y será eliminada en v6.0. "
        "Use calcular_metricas_descargas_json() que retorna una copia sin mutar el original.",
        DeprecationWarning,
        stacklevel=2  # ← El warning apunta al código que llama
    )

    # ... código de implementación
```

#### Función 2: `descargar_archivos_actuaciones()`

**DESPUÉS (con warning):**
```python
async def descargar_archivos_actuaciones(page: Page, actuaciones: list, carpeta_destino: str):
    """Descarga archivos de actuaciones (versión con side effects).

    .. deprecated:: 5.6
        Esta función modifica la lista de actuaciones in-place (side effect).
        Usar :func:`descargar_archivos_actuaciones_modelos` que trabaja con objetos
        inmutables y retorna una copia. Esta función será eliminada en la versión 6.0.

    Warning:
        Esta función MUTA los elementos de la lista actuaciones. Para código nuevo,
        use ``descargar_archivos_actuaciones_modelos()`` que trabaja con modelos
        Pydantic inmutables.

    Args:
        page: Página de Playwright para realizar las descargas.
        actuaciones: Lista de diccionarios con datos de actuaciones (SERÁ MUTADA).
        carpeta_destino: Ruta donde guardar los archivos descargados.

    Example:
        >>> # ❌ MAL - Muta la lista original
        >>> await descargar_archivos_actuaciones(page, actuaciones, carpeta)
        >>>
        >>> # ✅ BIEN - Trabaja con modelos inmutables
        >>> modelos = [Actuacion.from_dict(a) for a in actuaciones]
        >>> await descargar_archivos_actuaciones_modelos(page, modelos, carpeta)
    """
    warnings.warn(
        "descargar_archivos_actuaciones() está deprecated y será eliminada en v6.0. "
        "Use descargar_archivos_actuaciones_modelos() que trabaja con objetos inmutables.",
        DeprecationWarning,
        stacklevel=2
    )

    # ... código de implementación
```

### 2. Import Agregado

**Archivo:** `Sistema_v5/pjn/scraping/actuaciones.py`

```python
import asyncio
import json
import os
import re
import warnings  # ← AGREGADO
from contextlib import suppress
from datetime import datetime
# ...
```

---

## 📖 Documentación Creada

### Guía de Migración (GUIA_MIGRACION_DEPRECACIONES.md)

**Tamaño:** 439 líneas
**Secciones principales:**

1. **Resumen Ejecutivo**
   - Timeline de deprecación (v5.6 → v6.0)
   - Lista de funciones affected

2. **Función 1: actualizar_metricas_descargas_en_json()**
   - Explicación del problema
   - Solución recomendada
   - Pasos de migración
   - Tabla comparativa
   - Ejemplos de código

3. **Función 2: descargar_archivos_actuaciones()**
   - Explicación del problema
   - Solución recomendada
   - Pasos de migración
   - Tabla comparativa
   - Ejemplos de código

4. **FAQ - Preguntas Frecuentes**
   - ¿Por qué deprecar estas funciones ahora?
   - ¿Tengo que migrar TODO mi código inmediatamente?
   - ¿Los warnings rompen mis tests?
   - ¿Puedo suprimir los warnings temporalmente?
   - ¿Hay algún script de migración automática?
   - ¿Qué pasa si no migro antes de v6.0?

5. **Testing**
   - Tests para verificar migración exitosa
   - Tests para verificar que no hay side effects

6. **Checklist de Migración**
   - Para `actualizar_metricas_descargas_en_json()`
   - Para `descargar_archivos_actuaciones()`
   - Verificaciones generales

**Ejemplo de contenido:**

```markdown
### ❌ Problema
Esta función muta el diccionario payload in-place

### ✅ Solución
Use calcular_metricas_descargas_json() que retorna copia

### 🔄 Pasos de Migración

**ANTES (deprecated):**
```python
actualizar_metricas_descargas_en_json(nuevo_payload)
return nuevo_payload
```

**DESPUÉS (recomendado):**
```python
nuevo_payload = calcular_metricas_descargas_json(nuevo_payload)
return nuevo_payload
```
```

---

## 🧪 Tests Creados

**Archivo:** `Sistema_v5/tests/test_deprecation_warnings.py`
**Tamaño:** 295 líneas

### Suite de Tests

#### TestDeprecationWarningsMetricas (6 tests)

| Test | Descripción | Estado |
|------|-------------|--------|
| `test_actualizar_metricas_emite_deprecation_warning` | Función deprecated emite warning | ✅ PASS |
| `test_actualizar_metricas_warning_mensaje_correcto` | Warning menciona función alternativa | ✅ PASS |
| `test_actualizar_metricas_stacklevel_correcto` | Warning apunta al código del usuario | ✅ PASS |
| `test_calcular_metricas_sin_warning` | Función nueva NO emite warning | ✅ PASS |
| `test_calcular_metricas_no_muta_original` | Función nueva NO muta original | ✅ PASS |
| `test_actualizar_metricas_muta_original` | Función deprecated SÍ muta (expected) | ✅ PASS |

#### TestDeprecationWarningsDescargas (2 tests)

| Test | Descripción | Estado |
|------|-------------|--------|
| `test_descargar_archivos_actuaciones_emite_warning` | Función deprecated emite warning | ✅ PASS |
| `test_descargar_archivos_actuaciones_warning_mensaje` | Warning menciona función alternativa | ✅ PASS |

#### TestMigracionComparativa (3 tests)

| Test | Descripción | Estado |
|------|-------------|--------|
| `test_ambas_funciones_metricas_calculan_igual` | Ambas funciones calculan mismos valores | ✅ PASS |
| `test_metricas_caso_vacio` | Ambas manejan listas vacías correctamente | ✅ PASS |
| `test_metricas_con_objetos_actuacion` | Función nueva funciona con objetos Actuacion | ✅ PASS |

#### TestIntegrationWarnings (2 tests)

| Test | Descripción | Estado |
|------|-------------|--------|
| `test_pipeline_sin_warnings_usando_nuevas_funciones` | Pipeline completo sin warnings | ✅ PASS |
| `test_warning_en_codigo_legacy` | Código legacy emite warnings | ✅ PASS |

**Resultado:**
```
============================
13 passed in 0.04s
============================
```

---

## 📊 Métricas

### Código
| Métrica | Valor |
|---------|-------|
| Archivos modificados | 4 |
| Líneas agregadas | 805 |
| Líneas eliminadas | 16 |
| Funciones deprecated | 2 |
| Warnings implementados | 2 |
| Docstrings mejorados | 2 |

### Tests
| Métrica | Valor |
|---------|-------|
| Tests nuevos | 13 |
| Tests pasando | 13 (100%) |
| Tests existentes | 7 (siguen pasando) |
| Cobertura warnings | 100% |
| Tiempo ejecución | 0.04s |

### Documentación
| Métrica | Valor |
|---------|-------|
| Guía de migración | 439 líneas |
| Secciones FAQ | 6 preguntas |
| Ejemplos de código | 12+ ejemplos |
| Tablas comparativas | 2 tablas |
| Checklists | 2 checklists completos |

### Calidad
| Aspecto | Antes | Después |
|---------|-------|---------|
| Warnings en funciones deprecated | ❌ No | ✅ Sí |
| Documentación Sphinx | ❌ No | ✅ Sí (`.. deprecated::`) |
| Ejemplos en docstrings | ❌ No | ✅ Sí (❌ vs ✅) |
| Guía de migración | ❌ No | ✅ Completa (439 líneas) |
| Tests para warnings | ❌ No | ✅ 13 tests |

---

## 🎯 Objetivos Alcanzados

- [x] Identificar funciones con side effects
- [x] Agregar warnings de deprecación
- [x] Mejorar documentación con formato Sphinx
- [x] Agregar ejemplos de uso correcto vs incorrecto
- [x] Crear guía de migración completa
- [x] Crear suite de tests para warnings
- [x] Verificar que todos los tests pasen
- [x] Actualizar tracking de sprints
- [x] Mergear a v5.6

---

## 📝 Lecciones Aprendidas

### ✅ Lo que funcionó bien

1. **stacklevel=2 en warnings**
   - Hace que el warning apunte al código del usuario, no a la función interna
   - Mejora la experiencia de debugging

2. **Documentación exhaustiva**
   - La guía de migración con FAQ y ejemplos facilita la transición
   - Ejemplos lado a lado (❌ vs ✅) son muy claros

3. **Tests comprehensivos**
   - 13 tests cubren warnings, mensajes, side effects, comparaciones
   - Tests verifican tanto comportamiento deprecated como nuevo

4. **Formato Sphinx en docstrings**
   - `.. deprecated:: 5.6` es estándar y parseable por herramientas
   - `:func:` references crean enlaces automáticos en documentación

### 🔍 Áreas de mejora para próximas tareas

1. **Automatización de migración**
   - Considerar crear script de migración automática para casos simples
   - Usar AST (Abstract Syntax Tree) para reemplazar llamadas

2. **Métricas de uso**
   - Sería útil saber cuántas veces se llaman las funciones deprecated
   - Considerar logging temporal para medir impacto

3. **Comunicación al equipo**
   - Crear changelog entry
   - Enviar notificación al equipo sobre deprecaciones

---

## 🚀 Próximos Pasos

### Tarea 1.3: Validación de Recursos I/O
**Estimación:** 4 horas
**Prioridad:** 🟡 Media

**Objetivos:**
- Validar que archivos/carpetas existen antes de operaciones I/O
- Agregar checks explícitos en funciones críticas
- Mejorar mensajes de error cuando recursos no existen

**Funciones a mejorar:**
```python
# Función 1: guardar_json_actuaciones()
def guardar_json_actuaciones(...):
    # ✅ Agregar: validar que carpeta_destino existe/es escribible
    # ✅ Agregar: validar permisos de escritura
    # ✅ Mejorar: mensajes de error descriptivos
    ...

# Función 2: descargar_archivos_de_json()
def descargar_archivos_de_json(...):
    # ✅ Agregar: validar que archivo JSON existe
    # ✅ Agregar: validar que archivo es válido JSON
    # ✅ Mejorar: manejo de errores de lectura
    ...
```

---

## 📎 Referencias

- **Commits:**
  - `2dc0dbd` - Implementación de warnings y documentación
  - `559c572` - Merge a v5.6

- **Archivos creados:**
  - `Sistema_v5/tests/test_deprecation_warnings.py`
  - `Sistema_v5/documentacion/GUIA_MIGRACION_DEPRECACIONES.md`
  - `Sistema_v5/documentacion/MERGE_SPRINT_1_TAREA_1.2.md`

- **Archivos modificados:**
  - `Sistema_v5/pjn/scraping/actuaciones.py`
  - `Sistema_v5/documentacion/TRACKING_SPRINTS.md`

- **Documentación:**
  - [Hoja de Ruta Completa](./HOJA_DE_RUTA_MEJORAS.md)
  - [Guía de Migración](./GUIA_MIGRACION_DEPRECACIONES.md)
  - [Tracking de Sprints](./TRACKING_SPRINTS.md)
  - [Merge Report Tarea 1.2](./MERGE_SPRINT_1_TAREA_1.2.md)

---

## 🎉 Conclusión

La Tarea 1.2 se completó exitosamente:

- ✅ 2 funciones deprecated con warnings informativos
- ✅ Guía de migración completa (439 líneas)
- ✅ 13 tests nuevos, todos pasan
- ✅ Sin regresiones (7 tests existentes siguen pasando)
- ✅ Documentación mejorada con formato Sphinx
- ✅ Mergeado exitosamente a v5.6

**Estado:** COMPLETADA
**Listo para:** Continuar con Tarea 1.3

---

**Completado por:** Claude
**Fecha:** 2025-10-16
**Tiempo:** ~3 horas
**Sprint 1 Progreso:** 67% (2/3 tareas críticas completadas)
