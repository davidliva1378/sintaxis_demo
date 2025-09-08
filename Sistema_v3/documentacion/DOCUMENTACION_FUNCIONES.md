# Documentación de Funciones - Sistema_v3

## Información General

- **Total de archivos analizados**: 10 archivos Python
- **Total de funciones documentadas**: 34 funciones
- **Funciones asíncronas**: 24 (71%)
- **Funciones síncronas**: 10 (29%)
- **Framework principal**: Playwright para automatización web
- **Fecha de documentación**: 2025-09-08

---

## Índice de Módulos

1. [Actuaciones](#actuaciones)
   - [actuaciones.py](#actuacionespy)
   - [actuaciones_utils.py](#actuaciones_utilspy)
   - [rf_actuaciones.py](#rf_actuacionespy)
2. [Entradas](#entradas)
   - [entradas.py](#entradaspy)
   - [utils.py](#utilspy-entradas)
3. [Expedientes](#expedientes)
   - [expedientes.py](#expedientespy)
   - [expediente_detalle.py](#expediente_detallepy)
   - [ref_expedientes.py](#ref_expedientespy)
   - [utils.py](#utilspy-expedientes)
4. [Testing](#testing)
   - [rf_test_extraccion_completa.py](#rf_test_extraccion_completapy)

---

## Actuaciones

### actuaciones.py

**Ubicación**: `Sistema_v3/operaciones/actuaciones/actuaciones.py`

**Dependencias**:
- `os, re, json, asyncio`
- `datetime (datetime, date)`
- `urllib.parse (urlparse, parse_qs)`
- `playwright.async_api (TimeoutError, Page)`
- `Sistema_v3.operaciones.actuaciones.actuaciones_utils`

#### `aviso_si_tarda(idx, segundos)`
- **Línea**: 27
- **Tipo**: Función asíncrona
- **Parámetros**: 
  - `idx` (int): Índice de la actuación siendo descargada
  - `segundos` (int): Segundos a esperar antes de mostrar aviso
- **Retorna**: None
- **Descripción**: Muestra un aviso si la descarga tarda más de lo esperado
- **Docstring**: "Muestra un aviso si la descarga tarda más de lo esperado."

#### `descargar_archivos_actuaciones(page, actuaciones, carpeta_destino)`
- **Línea**: 33
- **Tipo**: Función asíncrona
- **Parámetros**:
  - `page: Page`: Objeto página de Playwright
  - `actuaciones: list`: Lista de diccionarios de actuaciones
  - `carpeta_destino: str`: Ruta de carpeta destino
- **Retorna**: None
- **Descripción**: Descarga los archivos adjuntos de las actuaciones usando automatización del navegador
- **Docstring**: "Descarga los archivos adjuntos de las actuaciones dadas."

#### `extraer_actuaciones_pagina(page_expediente, expediente_datos, indice_inicial=1)`
- **Línea**: 89
- **Tipo**: Función asíncrona
- **Parámetros**:
  - `page_expediente`: Objeto página de Playwright
  - `expediente_datos`: Diccionario con datos del expediente
  - `indice_inicial=1`: Índice inicial para las actuaciones
- **Retorna**: `tuple[list, str | None]`
- **Descripción**: Obtiene las actuaciones listadas en la página actual del expediente
- **Docstring**: "Obtiene las actuaciones listadas en la página actual del expediente."

#### `obtener_actuaciones_todas_paginas_async(page_expediente, expediente_datos, carpeta_destino="Actuaciones")`
- **Línea**: 157
- **Tipo**: Función asíncrona
- **Parámetros**:
  - `page_expediente`: Objeto página de Playwright
  - `expediente_datos`: Diccionario con datos del expediente
  - `carpeta_destino="Actuaciones"`: Carpeta destino
- **Retorna**: `tuple[list, str | None, str]`
- **Descripción**: Recorre todas las páginas del expediente y reúne sus actuaciones
- **Docstring**: "Recorre todas las páginas del expediente y reúne sus actuaciones."

#### `extraer_actuaciones_completas(page_expediente, expediente_datos, incluir_historicas=True, directorio_base="ActuacionesCompletas")`
- **Línea**: 215
- **Tipo**: Función asíncrona
- **Parámetros**:
  - `page_expediente`: Objeto página de Playwright
  - `expediente_datos: dict`: Diccionario de datos del expediente
  - `incluir_historicas: bool = True`: Incluir actuaciones históricas
  - `directorio_base: str = "ActuacionesCompletas"`: Directorio base
- **Retorna**: `tuple[list[dict], list[dict], str | None]`
- **Descripción**: Extrae actuaciones actuales e históricas del expediente y las guarda como JSON
- **Docstring**: Docstring completo explicando la extracción de actuaciones actuales e históricas

#### `descargar_archivos_de_json(page, carpeta_destino)`
- **Línea**: 294
- **Tipo**: Función asíncrona
- **Parámetros**:
  - `page`: Objeto página de Playwright
  - `carpeta_destino: str`: Ruta de carpeta destino
- **Retorna**: None
- **Descripción**: Lee el archivo unificado desde la carpeta del expediente y descarga archivos vinculados
- **Docstring**: Docstring completo explicando la lectura de JSON y descarga de archivos

#### `extraer_actuaciones_historicas(page_expediente, expediente_datos, indice_inicial=1)`
- **Línea**: 335
- **Tipo**: Función asíncrona
- **Parámetros**:
  - `page_expediente`: Objeto página de Playwright
  - `expediente_datos`: Diccionario con datos del expediente
  - `indice_inicial=1`: Índice inicial
- **Retorna**: `tuple[list, str | None]`
- **Descripción**: Recupera las actuaciones históricas del expediente indicado
- **Docstring**: "Recupera las actuaciones históricas del expediente indicado."

---

### actuaciones_utils.py

**Ubicación**: `Sistema_v3/operaciones/actuaciones/actuaciones_utils.py`

**Dependencias**:
- `re, hashlib`
- `datetime (datetime)`

#### `limpiar_texto(texto)`
- **Línea**: 5
- **Tipo**: Función síncrona
- **Parámetros**: `texto: str` - Texto a limpiar
- **Retorna**: `str`
- **Descripción**: Limpia texto removiendo prefijos y normalizando espacios en blanco
- **Docstring**: Sin docstring

#### `normalizar_fecha(texto)`
- **Línea**: 10
- **Tipo**: Función síncrona
- **Parámetros**: `texto: str` - Texto de fecha a normalizar
- **Retorna**: `str`
- **Descripción**: Normaliza formato de fecha de DD/MM/YYYY a YYYY-MM-DD
- **Docstring**: Sin docstring

#### `generar_hash_archivo(fecha, tipo, detalle, longitud=6)`
- **Línea**: 16
- **Tipo**: Función síncrona
- **Parámetros**:
  - `fecha: str`: Cadena de fecha
  - `tipo: str`: Cadena de tipo
  - `detalle: str`: Cadena de detalles
  - `longitud: int = 6`: Longitud del hash
- **Retorna**: `str`
- **Descripción**: Genera un hash SHA256 desde fecha, tipo y detalles para nombrado de archivos
- **Docstring**: Sin docstring

---

### rf_actuaciones.py

**Ubicación**: `Sistema_v3/operaciones/actuaciones/rf_actuaciones.py`

**Dependencias**:
- `os, re, json, asyncio, hashlib`
- `datetime (datetime, date)`
- `urllib.parse (urlparse, parse_qs)`
- `playwright.async_api (TimeoutError)`
- `.actuaciones_utils`
- Importaciones de panel_pjn

#### `extraer_actuaciones_historicas(page_expediente, expediente_datos, indice_inicial=1)`
- **Línea**: 7
- **Tipo**: Función asíncrona
- **Parámetros**:
  - `page_expediente`: Objeto página de Playwright
  - `expediente_datos`: Diccionario con datos del expediente
  - `indice_inicial=1`: Índice inicial
- **Retorna**: `tuple[list, str | None]`
- **Descripción**: Extrae actuaciones históricas de un expediente
- **Docstring**: Sin docstring

#### `extraer_actuaciones_pagina(page_expediente, expediente_datos, indice_inicial=1)`
- **Línea**: 127
- **Tipo**: Función asíncrona
- **Parámetros**:
  - `page_expediente`: Objeto página de Playwright
  - `expediente_datos`: Diccionario con datos del expediente
  - `indice_inicial=1`: Índice inicial
- **Retorna**: `tuple[list, str | None]`
- **Descripción**: Extrae actuaciones de la página actual de un expediente
- **Docstring**: Sin docstring

#### `obtener_actuaciones_todas_paginas_async(page_expediente, expediente_datos, carpeta_destino="Actuaciones")`
- **Línea**: 201
- **Tipo**: Función asíncrona
- **Parámetros**:
  - `page_expediente`: Objeto página de Playwright
  - `expediente_datos`: Diccionario con datos del expediente
  - `carpeta_destino="Actuaciones"`: Carpeta destino
- **Retorna**: `tuple[list, str | None, str]`
- **Descripción**: Obtiene actuaciones de todas las páginas de un expediente
- **Docstring**: Sin docstring

#### `extraer_actuaciones_completas(page_expediente, expediente_datos, incluir_historicas=True, directorio_base="ActuacionesCompletas")`
- **Línea**: 263
- **Tipo**: Función asíncrona
- **Parámetros**:
  - `page_expediente`: Objeto página de Playwright
  - `expediente_datos: dict`: Datos del expediente
  - `incluir_historicas: bool = True`: Incluir históricas
  - `directorio_base: str = "ActuacionesCompletas"`: Directorio base
- **Retorna**: `tuple[list[dict], list[dict], str | None]`
- **Descripción**: Extrae actuaciones actuales e históricas y las guarda como JSON
- **Docstring**: Docstring completo explicando la extracción de actuaciones

#### `aviso_si_tarda(idx, segundos)`
- **Línea**: 343
- **Tipo**: Función asíncrona
- **Parámetros**:
  - `idx`: Índice de la actuación
  - `segundos`: Segundos a esperar
- **Retorna**: None
- **Descripción**: Muestra aviso si la descarga tarda demasiado
- **Docstring**: Sin docstring

#### `descargar_archivos_actuaciones(page, actuaciones, carpeta_destino)`
- **Línea**: 347
- **Tipo**: Función asíncrona
- **Parámetros**:
  - `page: Page`: Página de Playwright
  - `actuaciones: list`: Lista de actuaciones
  - `carpeta_destino: str`: Carpeta destino
- **Retorna**: None
- **Descripción**: Descarga archivos de actuaciones
- **Docstring**: Sin docstring

#### `descargar_archivos_de_json(page, carpeta_destino)`
- **Línea**: 401
- **Tipo**: Función asíncrona
- **Parámetros**:
  - `page`: Objeto página de Playwright
  - `carpeta_destino: str`: Carpeta destino
- **Retorna**: None
- **Descripción**: Lee archivo JSON unificado y descarga archivos vinculados, actualizando el estado de descarga
- **Docstring**: Docstring completo explicando lectura de JSON y descarga de archivos

---

## Entradas

### entradas.py

**Ubicación**: `Sistema_v3/operaciones/entradas/entradas.py`

**Dependencias**:
- `os, json, asyncio, csv`
- `datetime (datetime, timedelta)`
- `typing (Optional)`
- `playwright.async_api (Page)`
- `.utils (limpiar_texto, normalizar_texto)`

#### `actualizar_notificaciones_nuevas(page, destino=None)`
- **Línea**: 16
- **Tipo**: Función asíncrona
- **Parámetros**:
  - `page: Page`: Objeto página de Playwright
  - `destino: Optional[str] = None`: Carpeta destino opcional
- **Retorna**: `int`
- **Descripción**: Actualiza notificaciones nuevas navegando por páginas y recolectando nuevas entradas
- **Docstring**: Sin docstring

#### `notificaciones_proximas_a_vencer(destino=None, horas=48)`
- **Línea**: 130
- **Tipo**: Función síncrona
- **Parámetros**:
  - `destino: Optional[str] = None`: Carpeta destino opcional
  - `horas: int = 48`: Horas por delante a verificar
- **Retorna**: `list[dict]`
- **Descripción**: Retorna notificaciones cuya expiración está dentro del marco temporal especificado
- **Docstring**: Docstring completo explicando la función retorna notificaciones próximas a vencer

---

### utils.py (Entradas)

**Ubicación**: `Sistema_v3/operaciones/entradas/utils.py`

**Dependencias**:
- `..expedientes.utils (limpiar_texto, normalizar_texto)`

Este archivo solo contiene importaciones y exportaciones, sin definiciones de funciones.

---

## Expedientes

### expedientes.py

**Ubicación**: `Sistema_v3/operaciones/expedientes/expedientes.py`

**Dependencias**:
- `os, json, time`
- `datetime (datetime)`
- `typing (Optional)`
- `pathlib (Path)`
- `asyncio`
- `playwright.async_api (Page, TimeoutError)`

#### `extraer_expedientes(page, carpeta_salida="datos_extraidos/monitoreo", delay=3000, nombre_archivo=None, detener_en_duplicado=True, guardar_json=True, fecha_corte=None, tiempo_maximo_segundos=None, orden=None)`
- **Línea**: 11
- **Tipo**: Función asíncrona
- **Parámetros**: Múltiples parámetros para configuración de extracción
- **Retorna**: `tuple[list[dict], Optional[str], str]`
- **Descripción**: Extrae expedientes del portal con paginación, filtrado y opciones de ordenamiento
- **Docstring**: Sin docstring

---

### expediente_detalle.py

**Ubicación**: `Sistema_v3/operaciones/expedientes/expediente_detalle.py`

**Dependencias**:
- `playwright.async_api (Page)`
- `typing (Optional, List)`
- `playwright.async_api (ElementHandle)`

#### `buscar_expediente_por_numero(page, numero)`
- **Línea**: 13
- **Tipo**: Función asíncrona
- **Parámetros**:
  - `page: Page`: Objeto página de Playwright
  - `numero: str`: Número de expediente a buscar
- **Retorna**: `bool`
- **Descripción**: Busca expediente por número usando el campo de búsqueda
- **Docstring**: Sin docstring

#### `abrir_expediente_desde_fila(page, indice=0)`
- **Línea**: 30
- **Tipo**: Función asíncrona
- **Parámetros**:
  - `page: Page`: Objeto página de Playwright
  - `indice: int = 0`: Índice de fila a abrir
- **Retorna**: `bool`
- **Descripción**: Abre expediente desde una fila de tabla por índice
- **Docstring**: Sin docstring

#### `extraer_datos_expediente(page)`
- **Línea**: 46
- **Tipo**: Función asíncrona
- **Parámetros**: `page: Page` - Objeto página de Playwright
- **Retorna**: `dict`
- **Descripción**: Extrae datos visibles de un expediente abierto
- **Docstring**: Sin docstring

#### `mostrar_y_elegir_expediente(lista)`
- **Línea**: 63
- **Tipo**: Función síncrona
- **Parámetros**: `lista: list[dict]` - Lista de diccionarios de expedientes
- **Retorna**: `dict`
- **Descripción**: Muestra lista de expedientes y permite al usuario seleccionar uno por índice
- **Docstring**: Sin docstring

#### `buscar_expedientes(page, numero=None, anio=None, caratula=None)`
- **Línea**: 81
- **Tipo**: Función asíncrona
- **Parámetros**:
  - `page: Page`: Objeto página de Playwright
  - `numero: Optional[str] = None`: Número de expediente opcional
  - `anio: Optional[str] = None`: Año opcional
  - `caratula: Optional[str] = None`: Filtro de carátula opcional
- **Retorna**: `List[ElementHandle]`
- **Descripción**: Función de búsqueda avanzada para expedientes por número, año y/o carátula
- **Docstring**: Docstring completo explicando la búsqueda en portal PJN

---

### ref_expedientes.py

**Ubicación**: `Sistema_v3/operaciones/expedientes/ref_expedientes.py`

**Dependencias**:
- `datetime, json, os, time`
- `typing (Optional, List, Dict)`
- `pathlib (Path)`
- `playwright.async_api (Page, TimeoutError)`
- `asyncio`

#### `extraer_expedientes(page, carpeta_salida="panel_pjn/acciones_pjn/Actuaciones", delay=3000, nombre_archivo=None, detener_en_duplicado=True, guardar_json=True, fecha_corte=None, tiempo_maximo_segundos=None, orden=None)`
- **Línea**: 12
- **Tipo**: Función asíncrona
- **Parámetros**: Múltiples parámetros para configuración de extracción
- **Retorna**: `tuple[list[dict], Optional[str], str]`
- **Descripción**: Extrae expedientes del portal con paginación y filtrado
- **Docstring**: Sin docstring

#### `extraer_datos_expediente(page)`
- **Línea**: 147
- **Tipo**: Función asíncrona
- **Parámetros**: `page` - Objeto página de Playwright
- **Retorna**: `dict`
- **Descripción**: Extrae datos del expediente, usado para validación y detección de cambios de jurisdicción
- **Docstring**: Sin docstring

#### `abrir_expediente_desde_fila(fila, page)`
- **Línea**: 173
- **Tipo**: Función asíncrona
- **Parámetros**:
  - `fila`: Handle del elemento fila
  - `page`: Objeto página de Playwright
- **Retorna**: `bool`
- **Descripción**: Abre expediente desde una fila específica
- **Docstring**: Sin docstring

#### `mostrar_y_elegir_expediente(page, filas)`
- **Línea**: 198
- **Tipo**: Función asíncrona
- **Parámetros**:
  - `page: Page`: Objeto página de Playwright
  - `filas: List`: Lista de filas encontradas
- **Retorna**: `Optional[Dict]`
- **Descripción**: Muestra expedientes encontrados y permite selección del usuario
- **Docstring**: Docstring completo explicando selección de expedientes

#### `buscar_expediente_por_numero(page, numero, anio, timeout=8000)`
- **Línea**: 254
- **Tipo**: Función asíncrona
- **Parámetros**:
  - `page: Page`: Objeto página de Playwright
  - `numero: str`: Número de expediente
  - `anio: str`: Año
  - `timeout: int = 8000`: Timeout en milisegundos
- **Retorna**: `tuple[bool, str]`
- **Descripción**: Busca expediente por número y año usando el formulario de búsqueda
- **Docstring**: Sin docstring

#### `buscar_expedientes(page, numero=None, anio=None, caratula=None)`
- **Línea**: 292
- **Tipo**: Función asíncrona
- **Parámetros**:
  - `page: Page`: Objeto página de Playwright
  - `numero: Optional[str] = None`: Número de expediente opcional
  - `anio: Optional[str] = None`: Año opcional
  - `caratula: Optional[str] = None`: Filtro de carátula opcional
- **Retorna**: `List`
- **Descripción**: Busca expedientes en portal PJN y retorna lista de filas encontradas
- **Docstring**: Docstring completo explicando búsqueda en portal PJN

---

### utils.py (Expedientes)

**Ubicación**: `Sistema_v3/operaciones/expedientes/utils.py`

**Dependencias**:
- `unicodedata` (importado dentro de la función)

#### `limpiar_texto(texto)`
- **Línea**: 3
- **Tipo**: Función síncrona
- **Parámetros**: `texto` - Texto a limpiar
- **Retorna**: `str` (implícito)
- **Descripción**: Limpia texto reemplazando saltos de línea y eliminando espacios
- **Docstring**: Sin docstring

#### `normalizar_texto(t)`
- **Línea**: 6
- **Tipo**: Función síncrona
- **Parámetros**: `t` - Texto a normalizar
- **Retorna**: `str` (implícito)
- **Descripción**: Normaliza texto usando normalización Unicode y codificación ASCII
- **Docstring**: Sin docstring

---

## Testing

### rf_test_extraccion_completa.py

**Ubicación**: `Sistema_v3/operaciones/rf_test_extraccion_completa.py`

**Dependencias**:
- `asyncio, os`
- `playwright.async_api (async_playwright)`
- `panel_pjn.acciones_pjn.urls_pjn (URL_LOGIN, URL_CONSULTAS)`
- `Sistema_v3.operaciones.expedientes.ref_expedientes`
- `Sistema_v3.operaciones.actuaciones.rf_actuaciones`

#### `login_portal(page)`
- **Línea**: 19
- **Tipo**: Función asíncrona
- **Parámetros**: `page` - Objeto página de Playwright
- **Retorna**: `bool`
- **Descripción**: Realiza login al portal usando credenciales hardcodeadas
- **Docstring**: Sin docstring

#### `main()`
- **Línea**: 37
- **Tipo**: Función asíncrona
- **Parámetros**: Ninguno
- **Retorna**: None
- **Descripción**: Función principal que orquesta el workflow completo de extracción
- **Docstring**: Sin docstring

---

## Resumen de Características Técnicas

### Dependencias Principales
- **Playwright**: Automatización web (`async_playwright`, `Page`, `TimeoutError`)
- **asyncio**: Programación asíncrona
- **datetime**: Manejo de fechas y tiempos
- **json/csv**: Persistencia de datos
- **pathlib**: Manejo de rutas
- **typing**: Type hints

### Patrones de Diseño Implementados
- **Async/Await**: 71% de funciones asíncronas para operaciones no bloqueantes
- **Error Handling**: Manejo de `TimeoutError` y validaciones
- **Modularidad**: Separación clara de responsabilidades por módulos
- **Utils**: Funciones auxiliares reutilizables para normalización y limpieza

### Funcionalidades Core del Sistema
1. **Extracción de Datos**: Web scraping judicial automatizado
2. **Gestión de Archivos**: Descarga y organización automática
3. **Paginación**: Manejo automático de múltiples páginas
4. **Filtrado**: Por fechas, tipos, y criterios específicos
5. **Persistencia**: JSON y CSV para datos estructurados
6. **Notificaciones**: Sistema de alertas y vencimientos
7. **Búsqueda Avanzada**: Múltiples criterios de búsqueda
8. **Validación**: Control de duplicados y cambios de jurisdicción

### Arquitectura del Sistema
- **Separación de Responsabilidades**: Módulos independientes para cada funcionalidad
- **Reutilización**: Funciones utilitarias compartidas entre módulos
- **Configurabilidad**: Parámetros opcionales en funciones principales
- **Robustez**: Manejo de errores y timeouts configurables

---

*Documentación generada automáticamente el 2025-09-08*