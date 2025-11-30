# Plan de Implementación: Integración de Búsqueda por Carátula en Extracción Masiva

**Fecha**: 2025-11-12
**Versión**: v6.0.0
**Estado**: En Implementación
**Prioridad**: Alta

---

## 📋 Índice

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Contexto e Investigación](#contexto-e-investigación)
3. [Alcance y Objetivos](#alcance-y-objetivos)
4. [Plan de Implementación Detallado](#plan-de-implementación-detallado)
5. [Tests y Verificación](#tests-y-verificación)
6. [Criterios de Éxito](#criterios-de-éxito)
7. [Referencias](#referencias)

---

## 🎯 Resumen Ejecutivo

### Problema
El sistema v6 tiene implementada una función mejorada de búsqueda con filtrado por carátula (`buscar_expedientes()`) pero **no se está usando** en el flujo de extracción masiva batch (`GestorBatch`). Esto causa:
- Posible extracción incorrecta cuando hay múltiples expedientes con el mismo número/año
- Selección del expediente incorrecto (por ejemplo, un incidente en lugar del principal)
- Pérdida de funcionalidad que existía en v5.1.1

### Solución
Integrar `buscar_expedientes()` con filtrado por carátula en `GestorBatch`, implementando:
1. Búsqueda con carátula como filtro primario
2. Fallback automático sin carátula si no hay coincidencias
3. Logging de selecciones ambiguas
4. Configuración formal del parámetro

### Beneficios
- ✅ Mayor precisión en extracción masiva
- ✅ Restauración completa de funcionalidad v5.1.1
- ✅ Base para manejo futuro de incidentes
- ✅ Mejor observabilidad (logging de ambigüedades)

---

## 📚 Contexto e Investigación

### Investigación Previa

**Documentos de Referencia**:
- Análisis completo de búsqueda por carátula en v5.1.1 vs v6
- Análisis de manejo de expedientes principales e incidentes
- Comparación de implementaciones v4/v5 vs v6

### Estado Actual

#### ✅ Funcionalidad EXISTENTE en v6 (Mejorada)

**Archivo**: `pjn/scraping/expedientes.py`
**Función**: `buscar_expedientes()` (Líneas 946-1085)

**Características**:
- Normalización avanzada de texto (sin acentos, ASCII)
- Coincidencia parcial configurable (default: True)
- Logging detallado de coincidencias y descartes
- Manejo robusto de edge cases

**Código clave** (líneas 1045-1082):
```python
if caratula:
    caratula_normalizada = normalizar_texto(caratula)
    coincidencia_parcial = getattr(_config.scraping, "caratula_coincidencia_parcial", True)

    filas_filtradas: list[ElementHandle] = []
    for fila in filas:
        columnas = await fila.query_selector_all(SEL_EXPEDIENTES.COLUMNAS_FILA)
        if len(columnas) >= 3:
            caratula_original = (await columnas[2].inner_text()).strip()
            caratula_normalizada_fila = normalizar_texto(caratula_original)

            coincide = caratula_normalizada_fila == caratula_normalizada

            if not coincide and coincidencia_parcial and caratula_normalizada:
                if caratula_normalizada in caratula_normalizada_fila:
                    coincide = True

            if coincide:
                filas_filtradas.append(fila)

    return filas_filtradas
```

#### ⚠️ Funcionalidad NO INTEGRADA

**Archivo**: `extraccion_masiva/gestor_batch.py`
**Método**: `_procesar_expediente()` (Línea 247)

**Problema actual**:
```python
# ❌ Solo busca por número y año, NO usa carátula
exito, motivo = await buscar_expediente_por_numero(page, numero_limpio, anio_limpio)
```

**Debería ser**:
```python
# ✅ Buscar con carátula + fallback
filas = await buscar_expedientes(page, numero_limpio, anio_limpio, caratula_esperada)

if not filas and caratula_esperada:
    logger.warning("⚠️ Sin coincidencia exacta. Reintentando sin carátula...")
    filas = await buscar_expedientes(page, numero_limpio, anio_limpio, None)
```

### Comparación v5.1.1 vs v6

| Aspecto | v5.1.1 | v6 Actual | v6 Objetivo |
|---------|--------|-----------|-------------|
| Filtrado por carátula | ✅ Case-insensitive | ✅ Normalizado + parcial | ✅ Igual |
| Integración en batch | ✅ Usada en tests | ❌ No integrada | ✅ Totalmente integrada |
| Fallback sin carátula | ✅ Manual | ❌ No existe | ✅ Automático |
| Configuración | ❌ Hardcoded | ⚠️ getattr con default | ✅ Configuración formal |
| Logging | ⚠️ Básico (print) | ✅ Logger con niveles | ✅ Mejorado |

---

## 🎯 Alcance y Objetivos

### Fase 1: Integración de Carátula en Batch (ESTE PLAN)

**Objetivos**:
1. ✅ Agregar configuración formal en `ScrapingSettings`
2. ✅ Modificar `GestorBatch._procesar_expediente()` para usar carátula
3. ✅ Implementar fallback automático sin carátula
4. ✅ Agregar logging de selecciones ambiguas
5. ✅ Verificar funcionamiento con tests

**Archivos a Modificar**:
- `infrastructure/config/settings.py`
- `extraccion_masiva/gestor_batch.py`
- `presentation/api/rest/routers/extraccion_masiva.py` (opcional)

### Fase 2: Detección de Incidentes (FUTURO)

**Objetivos** (no incluidos en este plan):
- Agregar campos `es_incidente` y `numero_principal` al modelo
- Función de detección automática de incidentes
- Enriquecer listado con información de incidentes

---

## 🛠️ Plan de Implementación Detallado

### PASO 1: Agregar Configuración Formal

**Archivo**: `infrastructure/config/settings.py`
**Línea**: Después de línea 85 (dentro de clase `ScrapingSettings`)

**Acción**: Agregar nuevo campo de configuración

**Código a agregar**:
```python
class ScrapingSettings(BaseSettings):
    """Configuración de scraping (compatibilidad v5.1.1).

    Attributes:
        timeout_default: Timeout por defecto en ms para operaciones de scraping
        timeout_login: Timeout para operaciones de login en ms
        timeout_descarga: Timeout para descarga de archivos en ms
        max_paginas_expedientes: Máximo de páginas a extraer (None = sin límite)
        max_reintentos_descarga: Máximo de reintentos para descargas
        caratula_coincidencia_parcial: Si True, permite coincidencia parcial en carátulas  # 🆕 NUEVA LÍNEA
    """

    model_config = SettingsConfigDict(env_prefix="SCRAPING_", case_sensitive=False)

    timeout_default: int = 8000
    timeout_login: int = 60000
    timeout_descarga: int = 30000
    max_paginas_expedientes: int | None = 200
    max_reintentos_descarga: int = 3
    caratula_coincidencia_parcial: bool = True  # 🆕 NUEVA LÍNEA
```

**Verificación**:
```python
# En consola Python:
from infrastructure.config import get_settings
settings = get_settings()
assert hasattr(settings.scraping, 'caratula_coincidencia_parcial')
assert settings.scraping.caratula_coincidencia_parcial == True
print("✅ Configuración agregada correctamente")
```

---

### PASO 2: Modificar GestorBatch para Usar Búsqueda con Carátula

**Archivo**: `extraccion_masiva/gestor_batch.py`

#### 2.1. Agregar Import

**Línea**: ~20 (con otros imports de pjn.scraping)

**Código a agregar**:
```python
from pjn.scraping.expedientes import buscar_expedientes  # 🆕 AGREGAR
```

#### 2.2. Modificar Firma del Método `_procesar_expediente`

**Línea**: ~215

**ANTES**:
```python
async def _procesar_expediente(
    self,
    page: Page,
    numero_expediente: str,
    context: BrowserContext,
    browser: Browser,
) -> Dict:
```

**DESPUÉS**:
```python
async def _procesar_expediente(
    self,
    page: Page,
    numero_expediente: str,
    caratula_esperada: str | None,  # 🆕 NUEVO PARÁMETRO
    context: BrowserContext,
    browser: Browser,
) -> Dict:
```

#### 2.3. Modificar Lógica de Búsqueda

**Línea**: ~240-260 (buscar_expediente_por_numero)

**ANTES** (líneas ~247-253):
```python
# Buscar el expediente
logger.info(f"🔍 Buscando expediente: {numero_limpio}/{anio_limpio}")
exito, motivo = await buscar_expediente_por_numero(page, numero_limpio, anio_limpio)

if not exito:
    logger.error(f"❌ No se encontró expediente {numero_expediente}: {motivo}")
    return {"success": False, "error": motivo, "expediente": numero_expediente}
```

**DESPUÉS**:
```python
# Buscar el expediente con filtrado por carátula
logger.info(f"🔍 Buscando expediente: {numero_limpio}/{anio_limpio}" +
            (f" con carátula: '{caratula_esperada}'" if caratula_esperada else ""))

# 🆕 USAR buscar_expedientes con carátula
filas = await buscar_expedientes(
    page,
    numero=numero_limpio,
    anio=anio_limpio,
    caratula=caratula_esperada
)

# 🆕 FALLBACK: Reintentar sin carátula si no hay coincidencias
if not filas and caratula_esperada:
    logger.warning(
        f"⚠️ No se hallaron coincidencias para carátula '{caratula_esperada}'. "
        f"Reintentando sin filtro para expediente {numero_expediente}..."
    )
    filas = await buscar_expedientes(
        page,
        numero=numero_limpio,
        anio=anio_limpio,
        caratula=None
    )

# Verificar si se encontró el expediente
if not filas:
    logger.error(f"❌ No se encontró expediente {numero_expediente}")
    return {
        "success": False,
        "error": "Expediente no encontrado",
        "expediente": numero_expediente
    }

# 🆕 SELECCIÓN de expediente cuando hay múltiples resultados
if len(filas) > 1:
    logger.warning(
        f"⚠️ Múltiples expedientes encontrados ({len(filas)}) para {numero_expediente}. "
        f"Usando el primero de la lista."
    )

# 🆕 NAVEGAR al expediente seleccionado
try:
    enlace_expediente = await filas[0].query_selector("a")
    if not enlace_expediente:
        logger.error(f"❌ No se encontró enlace en fila del expediente {numero_expediente}")
        return {
            "success": False,
            "error": "Enlace de expediente no encontrado",
            "expediente": numero_expediente
        }

    await enlace_expediente.click()
    await page.wait_for_load_state("domcontentloaded")
    logger.info(f"✅ Navegado a expediente {numero_expediente}")

except Exception as e:
    logger.error(f"❌ Error al navegar a expediente {numero_expediente}: {str(e)}")
    return {
        "success": False,
        "error": f"Error al navegar: {str(e)}",
        "expediente": numero_expediente
    }
```

#### 2.4. Actualizar Llamadas a `_procesar_expediente`

**Línea**: ~169 (dentro de `procesar_seleccionados`)

**ANTES**:
```python
resultado = await self._procesar_expediente(
    page_expediente,
    numero_expediente,
    context,
    browser,
)
```

**DESPUÉS**:
```python
# 🆕 Obtener carátula del expediente desde el listado (si existe)
caratula_expediente = None
# TODO: Implementar búsqueda de carátula en listado previo si está disponible

resultado = await self._procesar_expediente(
    page_expediente,
    numero_expediente,
    caratula_expediente,  # 🆕 NUEVO PARÁMETRO
    context,
    browser,
)
```

**NOTA**: La carátula puede obtenerse del listado masivo previo si está disponible. Por ahora se pasa `None` para mantener compatibilidad.

---

### PASO 3: (Opcional) Actualizar API para Pasar Carátula

**Archivo**: `presentation/api/rest/routers/extraccion_masiva.py`

**Contexto**: Este paso es opcional y depende de si se quiere integrar completamente con el listado previo.

#### 3.1. Modificar `_ejecutar_procesamiento_background`

**Línea**: ~232-288

**Idea**: Cargar el listado previo y obtener la carátula de cada expediente antes de procesarlo.

**Pseudocódigo**:
```python
async def _ejecutar_procesamiento_background(
    session_id: str,
    numeros_expedientes: List[str],
    username: str,
    password: str,
    config: ConfigExtraccionMasiva,
    expediente_repo,
):
    try:
        # 🆕 Cargar listado BASE para obtener carátulas
        listado_base_path = Path(config.directorio_base) / "expedientes_base.json"
        listado_base = {}

        if listado_base_path.exists():
            with open(listado_base_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Crear diccionario numero -> caratula
                listado_base = {
                    exp.get("numero"): exp.get("caratula")
                    for exp in data.get("expedientes", [])
                }

        # 🆕 Crear diccionario de carátulas para expedientes seleccionados
        caratulas_expedientes = {
            num: listado_base.get(num)
            for num in numeros_expedientes
        }

        # Callback para actualizar progreso
        def callback_progreso(actual: int, total: int, mensaje: str):
            if session_id in _sesiones:
                _sesiones[session_id].progreso_actual = actual
                _sesiones[session_id].mensaje = mensaje

        # Crear gestor con caratulas
        gestor = GestorBatch(
            config=config,
            on_progress=callback_progreso,
            expediente_repository=expediente_repo,
            caratulas=caratulas_expedientes  # 🆕 PASAR CARÁTULAS
        )

        # ... resto del código
```

**NOTA**: Este paso requiere también modificar `GestorBatch.__init__` para aceptar el parámetro `caratulas`. Se puede dejar para una iteración futura.

---

### PASO 4: Verificar Imports y Dependencias

**Archivos a verificar**:

1. `extraccion_masiva/gestor_batch.py`:
   ```python
   from pjn.scraping.expedientes import buscar_expedientes
   from pjn.scraping.base import descomponer_numero_expediente
   ```

2. `pjn/scraping/expedientes.py` (ya existe):
   ```python
   async def buscar_expedientes(
       page: Page,
       numero: str | None = None,
       anio: str | None = None,
       caratula: str | None = None,
   ) -> list[ElementHandle]:
   ```

---

## 🧪 Tests y Verificación

### Test Manual 1: Extracción con Carátula

**Objetivo**: Verificar que la búsqueda con carátula funciona correctamente.

**Pasos**:
1. Crear script de test:
   ```python
   # Sistema_v6/test_busqueda_caratula.py

   import asyncio
   from playwright.async_api import async_playwright
   from pjn.scraping.expedientes import buscar_expedientes
   from infrastructure.config import get_settings

   async def test_busqueda_con_caratula():
       settings = get_settings()

       async with async_playwright() as p:
           browser = await p.chromium.launch(headless=False)
           page = await browser.new_page()

           # Login (usar credenciales reales)
           await page.goto("https://scw.pjn.gov.ar/scw/consultaListaRelacionados.seam")
           # ... login ...

           # Test: Buscar con carátula
           numero = "123"
           anio = "2020"
           caratula = "RECURSO DE AMPARO"

           print(f"🔍 Buscando: {numero}/{anio} con carátula: '{caratula}'")
           filas = await buscar_expedientes(page, numero, anio, caratula)

           print(f"✅ Encontradas {len(filas)} coincidencias")

           # Test: Fallback sin carátula
           if not filas:
               print(f"⚠️ Sin coincidencias. Reintentando sin carátula...")
               filas = await buscar_expedientes(page, numero, anio, None)
               print(f"✅ Encontradas {len(filas)} coincidencias sin filtro")

           await browser.close()

   if __name__ == "__main__":
       asyncio.run(test_busqueda_con_caratula())
   ```

2. Ejecutar:
   ```bash
   cd Sistema_v6
   PYTHONPATH=/Users/davidalejandroliva/PycharmProjects/sintaXis:$PYTHONPATH \
   python test_busqueda_caratula.py
   ```

3. Verificar:
   - ✅ Se filtra correctamente por carátula
   - ✅ Fallback funciona cuando no hay coincidencias
   - ✅ Logging muestra mensajes apropiados

### Test Manual 2: Extracción Masiva con GestorBatch

**Objetivo**: Verificar integración completa en flujo batch.

**Pasos**:
1. Usar interfaz web para iniciar extracción de expedientes seleccionados
2. Monitorear logs del backend
3. Verificar que aparecen mensajes de búsqueda con/sin carátula

**Logging esperado**:
```
🔍 Buscando expediente: 123/2020 con carátula: 'RECURSO DE AMPARO'
✅ Navegado a expediente FPA 123/2020
```

O con fallback:
```
🔍 Buscando expediente: 123/2020 con carátula: 'CAUSA S/ DENUNCIA'
⚠️ No se hallaron coincidencias para carátula 'CAUSA S/ DENUNCIA'. Reintentando sin filtro...
⚠️ Múltiples expedientes encontrados (2) para FPA 123/2020. Usando el primero.
✅ Navegado a expediente FPA 123/2020
```

### Test Manual 3: Configuración

**Objetivo**: Verificar que la configuración se carga correctamente.

**Pasos**:
```python
# En consola Python:
from infrastructure.config import get_settings

settings = get_settings()
print(f"caratula_coincidencia_parcial: {settings.scraping.caratula_coincidencia_parcial}")
# Esperado: True

# Test de cambio por variable de entorno:
import os
os.environ['SCRAPING_CARATULA_COINCIDENCIA_PARCIAL'] = 'false'

from infrastructure.config import reload_settings
settings = reload_settings()
print(f"caratula_coincidencia_parcial: {settings.scraping.caratula_coincidencia_parcial}")
# Esperado: False
```

---

## ✅ Criterios de Éxito

### Funcionales

1. ✅ **Búsqueda con carátula funciona**:
   - Filtra correctamente expedientes por carátula normalizada
   - Soporta coincidencia parcial (configurable)

2. ✅ **Fallback automático funciona**:
   - Si no hay coincidencias con carátula, reintenta sin carátula
   - Logging adecuado de fallback

3. ✅ **Selección múltiple manejada**:
   - Cuando hay múltiples resultados, usa el primero
   - Logging advierte de ambigüedad

4. ✅ **Configuración formal**:
   - Parámetro `caratula_coincidencia_parcial` en `ScrapingSettings`
   - Se puede configurar por variable de entorno

### No Regresión

5. ✅ **Extracción masiva sigue funcionando**:
   - Listado completo se extrae correctamente
   - Procesamiento de seleccionados funciona

6. ✅ **Compatibilidad hacia atrás**:
   - Si no se proporciona carátula, funciona igual que antes
   - No rompe tests existentes

### Calidad

7. ✅ **Logging apropiado**:
   - Mensajes claros de búsqueda, fallback y selección
   - Niveles de log correctos (INFO, WARNING, ERROR)

8. ✅ **Código limpio**:
   - Sin código comentado
   - Docstrings actualizados
   - Type hints correctos

---

## 📖 Referencias

### Archivos Principales

**Sistema v6 (Actual)**:
- `pjn/scraping/expedientes.py` (líneas 946-1085): Función `buscar_expedientes()` mejorada
- `pjn/scraping/base.py` (líneas 64-72): Función `normalizar_texto()`
- `extraccion_masiva/gestor_batch.py` (líneas 215-308): Método `_procesar_expediente()`
- `infrastructure/config/settings.py` (líneas 67-85): Clase `ScrapingSettings`

**Sistema v4/v5 (Referencia)**:
- `Sistema_v4/operaciones/expedientes/expedientes_v4.py` (líneas 667-729): `buscar_expedientes()` v5.1.1
- `Sistema_v4/operaciones/rf_test_actualizacion_actuaciones.py` (líneas 190-208): Patrón de uso con fallback

### Documentación Relacionada

- Análisis completo de búsqueda por carátula (investigación previa)
- Análisis de manejo de expedientes principales e incidentes
- Configuración de Pydantic Settings

---

## 📝 Notas de Implementación

### Decisiones de Diseño

1. **Uso de `buscar_expedientes()` existente**:
   - ✅ Función ya probada y mejorada respecto a v5
   - ✅ No duplicar código
   - ✅ Aprovechar normalización y coincidencia parcial

2. **Fallback automático**:
   - ✅ Evita fallos cuando la carátula no coincide exactamente
   - ✅ Mantiene robustez del sistema
   - ⚠️ Puede enmascarar problemas de datos (mitigado con logging)

3. **Selección del primer resultado**:
   - ✅ Simple y determinista
   - ⚠️ No garantiza selección óptima (futuro: estrategia más sofisticada)

4. **Configuración de coincidencia parcial**:
   - ✅ Default `True` para mayor tolerancia
   - ✅ Configurable por variable de entorno si se necesita mayor precisión

### Limitaciones Conocidas

1. **Carátula no disponible en primera iteración**:
   - `GestorBatch` no tiene acceso al listado BASE por defecto
   - Solución temporal: Pasar `None` como carátula
   - Solución futura: Cargar listado BASE y pasar carátulas (Paso 3 opcional)

2. **Selección simple de múltiples resultados**:
   - Solo usa el primer resultado cuando hay múltiples coincidencias
   - No implementa estrategia de selección interactiva
   - Futuro: Agregar opciones de selección automática más sofisticadas

3. **Sin detección de incidentes**:
   - Este plan NO incluye detección automática de incidentes
   - Eso queda para Fase 2 (futuro)

### Trabajo Futuro

**Fase 2 - Detección de Incidentes**:
- Agregar `es_incidente` y `numero_principal` al modelo
- Función `detectar_incidente()` con regex
- Enriquecer listado con información de relaciones

**Fase 3 - Selección Avanzada**:
- Estrategia de selección cuando hay múltiples resultados
- Opción de selección manual en UI
- Métricas de ambigüedad en extracciones

**Fase 4 - Extracción Completa con Incidentes**:
- Endpoint `/expedientes/{numero}/completo`
- Extracción automática de incidentes relacionados
- Vista jerárquica en frontend

---

## 🤖 Instrucciones para Agente IA

### Orden de Ejecución

1. **Leer y entender el contexto completo**
2. **Ejecutar PASO 1**: Agregar configuración
3. **Ejecutar PASO 2**: Modificar GestorBatch (2.1, 2.2, 2.3, 2.4)
4. **Ejecutar PASO 4**: Verificar imports
5. **Omitir PASO 3** por ahora (opcional/futuro)
6. **Ejecutar Tests**: Test Manual 1, 2 y 3
7. **Verificar Criterios de Éxito**
8. **Reportar resultados**

### Formato de Reporte

Al completar, generar reporte con:
```markdown
## Reporte de Implementación

**Fecha**: [fecha]
**Archivos modificados**: [lista]

### Cambios Realizados
- [x] Paso 1: Configuración agregada
- [x] Paso 2.1: Import agregado
- [x] Paso 2.2: Firma modificada
- [x] Paso 2.3: Lógica de búsqueda modificada
- [x] Paso 2.4: Llamadas actualizadas
- [x] Paso 4: Imports verificados

### Tests Ejecutados
- [x] Test 1: Búsqueda con carátula ✅
- [x] Test 2: Extracción masiva ✅
- [x] Test 3: Configuración ✅

### Problemas Encontrados
[Descripción de problemas si los hubo]

### Estado Final
✅ Implementación completada exitosamente
```

---

**Fin del Documento**

---

**Notas**:
- Este es un documento vivo que puede actualizarse según avance la implementación
- Mantener sincronizado con el código actual
- Agregar lecciones aprendidas durante la implementación
