# Guía de Migración - Funciones Deprecated

**Fecha:** 2025-10-16
**Sprint:** 1, Tarea 1.2
**Versión Deprecation:** 5.6
**Versión Eliminación:** 6.0

---

## 🎯 Resumen

Esta guía documenta las funciones marcadas como **deprecated** en la versión 5.6 del sistema y proporciona instrucciones claras para migrar a las alternativas recomendadas.

**Funciones Deprecated:**
1. `actualizar_metricas_descargas_en_json()` → Use `calcular_metricas_descargas_json()`
2. `descargar_archivos_actuaciones()` → Use `descargar_archivos_actuaciones_modelos()`

**Timeline:**
- ✅ **v5.6 (actual)**: Funciones marcadas como deprecated, warnings emitidos
- ⚠️ **v5.7-5.9**: Período de migración (warnings activos)
- ❌ **v6.0**: Funciones eliminadas completamente

---

## 📋 Índice

1. [Función 1: actualizar_metricas_descargas_en_json()](#función-1-actualizar_metricas_descargas_en_json)
2. [Función 2: descargar_archivos_actuaciones()](#función-2-descargar_archivos_actuaciones)
3. [FAQ - Preguntas Frecuentes](#faq---preguntas-frecuentes)
4. [Testing](#testing)
5. [Checklist de Migración](#checklist-de-migración)

---

## Función 1: actualizar_metricas_descargas_en_json()

### ❌ Problema

Esta función **muta** el diccionario `payload` in-place, lo que puede causar efectos secundarios inesperados en el código que llama a la función.

```python
# ❌ DEPRECATED - NO USAR EN CÓDIGO NUEVO
def actualizar_metricas_descargas_en_json(payload: dict) -> None:
    """Modifica payload in-place (SIDE EFFECT)."""
    encabezado = payload.get("Expediente")
    # ... calcula métricas ...
    encabezado["Cantidad de Archivos Descargados"] = total_descargados  # ⚠️ MUTA EL ORIGINAL
```

**Por qué es problemático:**
- 🐛 Difícil de testear (necesita copiar datos antes de cada test)
- 🔀 Puede causar bugs sutiles si múltiples funciones modifican el mismo objeto
- 📖 No es obvio desde la firma de la función que muta el argumento

### ✅ Solución

Use `calcular_metricas_descargas_json()` que retorna una **copia modificada** sin alterar el original.

```python
# ✅ RECOMENDADO - USAR ESTA VERSIÓN
def calcular_metricas_descargas_json(payload: dict) -> dict:
    """Retorna copia modificada sin mutar el original."""
    nuevo_payload = copy.deepcopy(payload)
    # ... calcula métricas ...
    # Modifica la COPIA, no el original
    return nuevo_payload
```

### 🔄 Pasos de Migración

#### Paso 1: Identificar Usos

Busque todos los lugares donde se usa la función deprecated:

```bash
# Buscar en el código
grep -r "actualizar_metricas_descargas_en_json" Sistema_v5/pjn/
```

**Ubicaciones encontradas (al 2025-10-16):**
- `Sistema_v5/pjn/scraping/actuaciones.py:668` - función `extraer_actuaciones_datos()`
- `Sistema_v5/pjn/scraping/actuaciones.py:1199` - función `descargar_archivos_de_json()`

#### Paso 2: Reemplazar el Código

**ANTES (deprecated):**
```python
def extraer_actuaciones_datos(...):
    # ... código que genera payload ...

    # ❌ Muta el payload original
    actualizar_metricas_descargas_en_json(nuevo_payload)

    return nuevo_payload
```

**DESPUÉS (recomendado):**
```python
def extraer_actuaciones_datos(...):
    # ... código que genera payload ...

    # ✅ Retorna copia modificada
    nuevo_payload = calcular_metricas_descargas_json(nuevo_payload)

    return nuevo_payload
```

#### Paso 3: Ejecutar Tests

```bash
# Ejecutar tests unitarios
python -m pytest Sistema_v5/tests/ -v

# Verificar que no hay warnings de deprecación
python -m pytest Sistema_v5/tests/ -W error::DeprecationWarning
```

### 📊 Tabla Comparativa

| Aspecto | `actualizar_metricas_descargas_en_json()` (deprecated) | `calcular_metricas_descargas_json()` (recomendado) |
|---------|-------------------------------------------------------|---------------------------------------------------|
| **Retorno** | `None` | `dict` (nueva copia) |
| **Side Effects** | ⚠️ SÍ - Muta el argumento | ✅ NO - Retorna copia |
| **Testeable** | ❌ Difícil | ✅ Fácil |
| **Thread-safe** | ❌ NO | ✅ Potencialmente sí |
| **Claridad** | ❌ No obvio que muta | ✅ Claro que retorna copia |

---

## Función 2: descargar_archivos_actuaciones()

### ❌ Problema

Esta función **muta** los diccionarios dentro de la lista `actuaciones` in-place.

```python
# ❌ DEPRECATED - NO USAR EN CÓDIGO NUEVO
async def descargar_archivos_actuaciones(
    page: Page,
    actuaciones: list,  # ⚠️ Lista de DICTS que serán mutados
    carpeta_destino: str
):
    for idx, act in enumerate(actuaciones):
        # ... descarga archivo ...
        act["NombreArchivo"] = nombre_archivo      # ⚠️ MUTA EL DICT
        act["TipoArchivo"] = tipo_archivo          # ⚠️ MUTA EL DICT
        act["Descargado"] = True                   # ⚠️ MUTA EL DICT
```

**Por qué es problemático:**
- 🐛 Los diccionarios originales son modificados sin que sea obvio
- 📖 Mezcla lógica de descarga con mutación de datos
- 🔀 Imposible usar con objetos inmutables (frozen dataclasses, Pydantic con frozen=True)

### ✅ Solución

Use `descargar_archivos_actuaciones_modelos()` que trabaja con objetos **Pydantic inmutables**.

```python
# ✅ RECOMENDADO - USAR ESTA VERSIÓN
async def descargar_archivos_actuaciones_modelos(
    page: Page,
    actuaciones: list[Actuacion],  # ✅ Lista de objetos Pydantic
    carpeta_destino: str
) -> list[Actuacion]:  # ✅ Retorna lista con objetos actualizados
    """Descarga archivos sin mutar objetos originales."""
    actuaciones_actualizadas = []

    for actuacion in actuaciones:
        # ... descarga archivo ...
        # Crea NUEVO objeto con campos actualizados
        actuacion_actualizada = actuacion.model_copy(update={
            "nombre_archivo": nombre_archivo,
            "tipo_archivo": tipo_archivo,
            "descargado": True
        })
        actuaciones_actualizadas.append(actuacion_actualizada)

    return actuaciones_actualizadas
```

### 🔄 Pasos de Migración

#### Paso 1: Identificar Usos

```bash
# Buscar en el código
grep -r "descargar_archivos_actuaciones(" Sistema_v5/pjn/
```

**Ubicaciones encontradas (al 2025-10-16):**
- `Sistema_v5/pjn/scraping/actuaciones.py:1192` - función `descargar_archivos_de_json()`

#### Paso 2: Convertir Datos a Modelos

**ANTES (deprecated):**
```python
async def descargar_archivos_de_json(page, carpeta_destino: str):
    with open(ruta_json, "r", encoding="utf-8") as f:
        data = json.load(f)
        actuaciones = data.get("Actuaciones", [])  # ← Lista de DICTS

        # ... filtrar actuaciones ...

        # ❌ Muta los dicts originales
        await descargar_archivos_actuaciones(page, actuaciones_filtradas, carpeta_destino)
```

**DESPUÉS (recomendado):**
```python
async def descargar_archivos_de_json(page, carpeta_destino: str):
    with open(ruta_json, "r", encoding="utf-8") as f:
        data = json.load(f)
        actuaciones_dicts = data.get("Actuaciones", [])

        # ✅ Convertir a modelos Pydantic
        actuaciones_modelos = [Actuacion.from_dict(act) for act in actuaciones_dicts]

        # ... filtrar actuaciones ...

        # ✅ Trabaja con objetos inmutables
        actuaciones_actualizadas = await descargar_archivos_actuaciones_modelos(
            page, actuaciones_filtradas, carpeta_destino
        )

        # ✅ Si necesita actualizar el JSON, convertir de vuelta
        data["Actuaciones"] = [act.to_dict() for act in actuaciones_actualizadas]
```

#### Paso 3: Actualizar Código Dependiente

Si el código que llama espera que la lista original sea mutada, necesita ajustes:

```python
# ❌ ANTES - Asume mutación in-place
actuaciones = [{"Archivo": "url1", ...}, {"Archivo": "url2", ...}]
await descargar_archivos_actuaciones(page, actuaciones, carpeta)
# actuaciones ahora está mutada con "Descargado": True

# ✅ DESPUÉS - Recibe lista actualizada
actuaciones = [Actuacion(...), Actuacion(...)]
actuaciones = await descargar_archivos_actuaciones_modelos(page, actuaciones, carpeta)
# actuaciones ahora contiene NUEVOS objetos con descargado=True
```

### 📊 Tabla Comparativa

| Aspecto | `descargar_archivos_actuaciones()` (deprecated) | `descargar_archivos_actuaciones_modelos()` (recomendado) |
|---------|------------------------------------------------|--------------------------------------------------------|
| **Input** | `list[dict]` | `list[Actuacion]` (Pydantic) |
| **Retorno** | `None` | `list[Actuacion]` |
| **Side Effects** | ⚠️ SÍ - Muta dicts | ✅ NO - Retorna nuevos objetos |
| **Type Safety** | ❌ Dicts sin validación | ✅ Pydantic con validación |
| **Inmutabilidad** | ❌ NO | ✅ Soporta objetos frozen |

---

## FAQ - Preguntas Frecuentes

### ¿Por qué deprecar estas funciones ahora?

**Respuesta:** Estas funciones tienen **side effects** (mutación de argumentos) que dificultan el testing, razonamiento sobre el código, y pueden causar bugs sutiles. La refactorización a funciones puras o con objetos inmutables mejora la calidad del código.

### ¿Tengo que migrar TODO mi código inmediatamente?

**Respuesta:** No. Las funciones deprecated seguirán funcionando hasta la versión 6.0. Sin embargo:
- ✅ **Código NUEVO**: Use las funciones recomendadas desde ahora
- ⚠️ **Código EXISTENTE**: Migre progresivamente, empezando por código crítico
- ❌ **No espere hasta v6.0**: Migre durante el período de gracia (v5.6-5.9)

### ¿Los warnings de deprecación rompen mis tests?

**Respuesta:** Por defecto, NO. Los `DeprecationWarning` son capturados silenciosamente en Python. Sin embargo:

```python
# Para VER los warnings durante desarrollo:
python -W default::DeprecationWarning script.py

# Para FALLAR tests si hay warnings (recomendado en CI):
pytest -W error::DeprecationWarning
```

### ¿Puedo suprimir los warnings temporalmente?

**Respuesta:** Sí, pero NO es recomendado excepto para código legacy en proceso de migración:

```python
import warnings

# ⚠️ Suprime warnings temporalmente (solo para legacy)
with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    actualizar_metricas_descargas_en_json(payload)  # No emite warning
```

### ¿Hay algún script de migración automática?

**Respuesta:** No actualmente. La migración requiere cambios en la lógica (ej: asignar el valor de retorno) que son difíciles de automatizar. Use esta guía y los ejemplos proporcionados.

### ¿Qué pasa si no migro antes de v6.0?

**Respuesta:** Su código **se romperá** con un `ImportError` o `AttributeError` al intentar usar las funciones eliminadas. Por eso es crítico migrar durante v5.6-5.9.

---

## Testing

### Test de Migración Exitosa

Use este test para verificar que ha migrado correctamente:

```python
"""tests/test_deprecacion_migracion.py"""

import warnings
import pytest
from pjn.scraping.actuaciones import (
    actualizar_metricas_descargas_en_json,
    calcular_metricas_descargas_json,
)

class TestMigracionFunciones:
    """Tests para verificar migración de funciones deprecated."""

    def test_actualizar_metricas_emite_warning(self):
        """Función deprecated debe emitir DeprecationWarning."""
        payload = {
            "Expediente": {"Cantidad de Archivos Descargados": 0},
            "Actuaciones": [
                {"TieneArchivo": True, "Descargado": True}
            ]
        }

        # ✅ Debe emitir warning
        with pytest.warns(DeprecationWarning, match="deprecated"):
            actualizar_metricas_descargas_en_json(payload)

    def test_calcular_metricas_sin_warning(self):
        """Función nueva NO debe emitir warning."""
        payload = {
            "Expediente": {"Cantidad de Archivos Descargados": 0},
            "Actuaciones": [
                {"TieneArchivo": True, "Descargado": True}
            ]
        }

        # ✅ No debe emitir warning
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # Falla si hay warning
            resultado = calcular_metricas_descargas_json(payload)

        # ✅ Debe retornar copia modificada
        assert resultado is not payload  # Diferente objeto
        assert resultado["Expediente"]["Cantidad de Archivos Descargados"] == 1
```

### Test de Side Effects

Verifique que las funciones nuevas NO mutan el original:

```python
def test_calcular_metricas_no_muta_original(self):
    """Función nueva NO debe mutar el payload original."""
    payload_original = {
        "Expediente": {"Cantidad de Archivos Descargados": 0},
        "Actuaciones": [{"TieneArchivo": True, "Descargado": True}]
    }

    # Guardar valor original
    valor_original = payload_original["Expediente"]["Cantidad de Archivos Descargados"]

    # Calcular con función nueva
    payload_nuevo = calcular_metricas_descargas_json(payload_original)

    # ✅ El original NO debe cambiar
    assert payload_original["Expediente"]["Cantidad de Archivos Descargados"] == valor_original

    # ✅ El nuevo SÍ debe tener el valor actualizado
    assert payload_nuevo["Expediente"]["Cantidad de Archivos Descargados"] == 1
```

---

## Checklist de Migración

Use esta checklist para cada archivo que necesite migrar:

### Para `actualizar_metricas_descargas_en_json()`

- [ ] Identificar todos los usos de la función deprecated
- [ ] Reemplazar `actualizar_metricas_descargas_en_json(payload)` por `payload = calcular_metricas_descargas_json(payload)`
- [ ] Asegurarse de **asignar el valor de retorno** a la variable
- [ ] Ejecutar tests unitarios para verificar comportamiento
- [ ] Ejecutar con `-W error::DeprecationWarning` para confirmar cero warnings
- [ ] Code review para verificar que no hay side effects no intencionados

### Para `descargar_archivos_actuaciones()`

- [ ] Identificar todos los usos de la función deprecated
- [ ] Convertir listas de dicts a listas de objetos `Actuacion`
- [ ] Reemplazar llamada con `actuaciones = await descargar_archivos_actuaciones_modelos(...)`
- [ ] Asegurarse de **asignar el valor de retorno** a la variable
- [ ] Actualizar código que espera mutación in-place
- [ ] Ejecutar tests unitarios y de integración
- [ ] Ejecutar con `-W error::DeprecationWarning` para confirmar cero warnings
- [ ] Verificar que descargas funcionan correctamente

### General

- [ ] Todos los tests pasan sin warnings de deprecación
- [ ] Documentación actualizada si corresponde
- [ ] Code review completado
- [ ] Merge a rama principal

---

## 📞 Soporte

**¿Necesita ayuda con la migración?**

- 📖 Consulte la documentación completa en `Sistema_v5/documentacion/`
- 🐛 Reporte issues en el repositorio
- 💬 Pregunte al equipo en Slack/Discord

---

## 📚 Referencias

- [HOJA_DE_RUTA_MEJORAS.md](./HOJA_DE_RUTA_MEJORAS.md) - Plan completo de mejoras
- [SPRINT_1_TAREA_1.1_RESUMEN.md](./SPRINT_1_TAREA_1.1_RESUMEN.md) - Tarea anterior completada
- [TRACKING_SPRINTS.md](./TRACKING_SPRINTS.md) - Estado actual de sprints
- [Python Deprecation Best Practices](https://docs.python.org/3/library/warnings.html)

---

**Documento creado:** 2025-10-16
**Sprint 1, Tarea 1.2:** Deprecar funciones con side effects
**Versión del sistema:** 5.6
**Autor:** Claude
