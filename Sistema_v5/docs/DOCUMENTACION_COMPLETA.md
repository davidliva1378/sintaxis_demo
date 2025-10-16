# 📚 Documentación Completa - Sistema_v5

**Versión:** 5.5
**Última actualización:** 2025-10-15
**Líneas de código:** ~5,776 líneas Python
**Estado:** Producción Ready ✅

---

## 📖 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Módulos y Componentes](#módulos-y-componentes)
4. [API Reference](#api-reference)
5. [Modelos de Datos](#modelos-de-datos)
6. [Configuración](#configuración)
7. [Excepciones](#excepciones)
8. [Guías de Uso](#guías-de-uso)
9. [Ejemplos Completos](#ejemplos-completos)
10. [Testing](#testing)

---

## Introducción

Sistema_v5 es un framework completo de web scraping para el Portal Judicial Nacional (PJN) de Argentina, diseñado con arquitectura modular, altamente reutilizable y fácilmente extensible a otros portales.

### Características Principales

- ✅ **Arquitectura Modular**: Separación clara de responsabilidades
- ✅ **Funciones Puras**: Extracción sin side effects, ideal para composición
- ✅ **Manejo de Errores Estandarizado**: Excepciones jerárquicas con stack traces
- ✅ **Configuración Centralizada**: Un solo punto de configuración
- ✅ **Estrategias de Paginación**: Adaptable a diferentes frameworks web
- ✅ **Persistencia Separada**: Funciones de I/O independientes
- ✅ **Type Hints**: Completamente tipado para mejor IDE support
- ✅ **Logging Estructurado**: Sistema de logging configurable
- ✅ **Retrocompatible**: Código legacy sigue funcionando

### Mejoras Implementadas (60% completado)

**CRÍTICAS** (100%):
- Separación extracción/persistencia
- Manejo de errores estandarizado
- Eliminación de side effects
- Configuración centralizada

**ALTAS** (100%):
- Módulo de persistencia
- Estrategias de paginación
- Refactorización de funciones gigantes

---

## Arquitectura del Sistema

```
Sistema_v5/
├── pjn/                          # Paquete principal
│   ├── __init__.py              # Exports públicos
│   ├── config.py                # ⚙️ Configuración centralizada
│   ├── exceptions.py            # 🚨 Excepciones personalizadas
│   ├── selectores.py            # 🎯 Selectores CSS
│   │
│   ├── models/                  # 📦 Modelos de datos
│   │   ├── __init__.py
│   │   ├── actuacion.py        # Modelo Actuacion
│   │   ├── entrada.py          # Modelo Entrada
│   │   ├── expediente.py       # Modelo ExpedienteResumen
│   │   └── _utils.py           # Utilidades de modelos
│   │
│   ├── parsers/                 # 🔍 Parsers de HTML
│   │   ├── __init__.py
│   │   ├── actuaciones_parser.py
│   │   ├── entradas_parser.py
│   │   └── expedientes_parser.py
│   │
│   ├── scraping/                # 🌐 Módulo de scraping
│   │   ├── __init__.py
│   │   ├── base.py             # Funciones base
│   │   ├── actuaciones.py      # Extracción de actuaciones
│   │   ├── actuaciones_utils.py
│   │   ├── entradas.py         # Extracción de entradas
│   │   ├── expedientes.py      # Extracción de expedientes
│   │   └── pagination.py       # 🔄 Estrategias de paginación
│   │
│   ├── persistence/             # 💾 Capa de persistencia
│   │   ├── __init__.py
│   │   └── actuaciones.py      # I/O de actuaciones
│   │
│   ├── utils/                   # 🛠️ Utilidades
│   │   ├── __init__.py
│   │   └── logging.py          # Sistema de logging
│   │
│   └── scripts/                 # 📜 Scripts de ejemplo
│       ├── __init__.py
│       ├── rf_test_extraccion_completa.py
│       ├── diagnostico_entradas.py
│       └── prueba_extractor_entradas.py
│
├── ROADMAP.md                   # Roadmap de mejoras
├── MEJORAS_IMPLEMENTADAS.md     # Documentación de mejoras
├── MEJORA_6_EJEMPLO.md         # Ejemplos de paginación
└── DOCUMENTACION_COMPLETA.md   # Este documento
```

### Flujo de Datos

```
┌─────────────────┐
│   Configuración │
│   (config.py)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Selectores    │
│ (selectores.py) │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│           SCRAPING LAYER                │
│  ┌──────────────┐  ┌──────────────┐    │
│  │ Expedientes  │  │  Actuaciones │    │
│  └──────────────┘  └──────────────┘    │
│  ┌──────────────┐  ┌──────────────┐    │
│  │   Entradas   │  │  Pagination  │    │
│  └──────────────┘  └──────────────┘    │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│    PARSERS      │
│  HTML → Models  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     MODELS      │
│   Dataclasses   │
└────────┬────────┘
         │
         ├──────────────────────┐
         │                      │
         ▼                      ▼
┌─────────────────┐    ┌─────────────────┐
│   PERSISTENCE   │    │  Return to User │
│   JSON/CSV I/O  │    │   (in-memory)   │
└─────────────────┘    └─────────────────┘
```

---

## Módulos y Componentes

### 1. Módulo de Configuración (`pjn.config`)

Centraliza toda la configuración del sistema.

**Clases:**
- `ScrapingConfig`: Configuración de scraping
- `BrowserConfig`: Configuración de navegador
- `AuthConfig`: Configuración de autenticación
- `ArchivosConfig`: Configuración de archivos
- `Config`: Clase principal que agrupa todas

**Funciones:**
- `get_config() -> Config`: Obtiene configuración global
- `set_config(config: Config) -> None`: Establece configuración

**Ejemplo:**
```python
from pjn.config import get_config, Config

# Obtener configuración
config = get_config()
timeout = config.scraping.timeout_default

# Configuración personalizada
custom_config = Config(
    scraping=ScrapingConfig(
        timeout_default=30_000,
        max_paginas_expedientes=50,
    )
)
set_config(custom_config)
```

### 2. Módulo de Excepciones (`pjn.exceptions`)

Sistema jerárquico de excepciones.

**Jerarquía:**
```
Exception
└── PJNError (base)
    ├── ExtraccionError
    │   ├── TimeoutExtraccion
    │   └── ActuacionesNoDisponibles
    └── (futuras excepciones)
```

**Uso:**
```python
from pjn.exceptions import ExtraccionError, TimeoutExtraccion

try:
    datos = await extraer_actuaciones_datos(page, expediente)
except TimeoutExtraccion as e:
    # Manejo específico de timeout
    logger.error(f"Timeout: {e}")
except ExtraccionError as e:
    # Manejo genérico
    logger.error(f"Error: {e}")
```

### 3. Módulo de Modelos (`pjn.models`)

Dataclasses que representan las entidades del sistema.

#### 3.1 `Actuacion`

Representa una actuación judicial.

**Atributos:**
```python
@dataclass
class Actuacion:
    indice: int                  # Índice secuencial
    numero: str                  # Número de expediente
    fecha: str                   # Fecha en formato YYYY-MM-DD
    tipo: str                    # Tipo de actuación
    detalle: str                 # Detalle de la actuación
    archivos: List[Archivo]      # Lista de archivos adjuntos
```

**Métodos:**
- `to_dict() -> dict`: Convierte a diccionario
- `from_dict(data: dict) -> Actuacion`: Crea desde diccionario

#### 3.2 `ActuacionesArchivo`

Contenedor para actuaciones de un expediente.

**Atributos:**
```python
@dataclass
class ActuacionesArchivo:
    numero_expediente: str
    caratula: str
    actuaciones: List[Actuacion]
    metadata: dict
```

#### 3.3 `Entrada`

Representa una entrada/notificación.

**Atributos:**
```python
@dataclass
class Entrada:
    numero: str                  # Número de expediente
    caratula: str               # Carátula del expediente
    fecha: str                  # Fecha YYYY-MM-DD
    evento: str                 # Tipo: 'N' (notificación) o 'D' (despacho)
    tipo_evento: str            # 'NOTIFICACION' o 'DESPACHO'
    leida: bool                 # Si fue leída
    extraida_en: str            # Timestamp de extracción
```

#### 3.4 `ExpedienteResumen`

Resumen de expediente del listado.

**Atributos:**
```python
@dataclass
class ExpedienteResumen:
    numero: str
    dependencia: str
    caratula: str
    situacion: str
    ultima_actuacion: str       # YYYY-MM-DD
```

### 4. Módulo de Scraping (`pjn.scraping`)

El corazón del sistema, contiene toda la lógica de extracción.

#### 4.1 Scraping de Expedientes (`pjn.scraping.expedientes`)

**Funciones Principales:**

##### `extraer_expedientes_completos()`

Extrae expedientes paginados con filtros y configuraciones avanzadas.

```python
async def extraer_expedientes_completos(
    page: Page,
    sel_tabla: str = SEL_TABLA,
    sel_tbody: str = SEL_TBODY,
    sel_siguiente: str = SEL_SIGUIENTE,
    max_paginas: int | None = None,
    omitir_duplicados: bool = True,
    detener_en_duplicado: bool = True,
    *,
    fecha_corte: str | None = None,
    tiempo_maximo_segundos: int | None = None,
    orden: str | None = None,
    mapper: Callable[[ExpedienteResumen], TResumen] | None = None,
    pagination_strategy: PaginationStrategy | None = None,
) -> tuple[list[TResumen], str, dict[str, object]]:
```

**Parámetros:**
- `page`: Página de Playwright con el listado abierto
- `sel_tabla`: Selector CSS de la tabla (default: tabla PJN)
- `sel_tbody`: Selector del tbody
- `sel_siguiente`: Selector del botón "Siguiente"
- `max_paginas`: Límite de páginas a extraer (default: config)
- `omitir_duplicados`: Si omitir expedientes duplicados
- `detener_en_duplicado`: Si detener al encontrar duplicado
- `fecha_corte`: Fecha mínima (YYYY-MM-DD o DD/MM/YYYY)
- `tiempo_maximo_segundos`: Timeout de extracción completa
- `orden`: Criterio de ordenamiento ('fecha', 'caratula', 'oficina', 'situacion')
- `mapper`: Función para transformar ExpedienteResumen
- `pagination_strategy`: Estrategia de paginación personalizada

**Retorna:**
```python
tuple[
    list[dict | ExpedienteResumen],  # Expedientes extraídos
    str,                              # Motivo de finalización
    dict[str, object]                 # Metadata
]
```

**Motivos de finalización:**
- `"fin_listado"`: Final natural del paginado
- `"limite_paginas"`: Alcanzó max_paginas
- `"limite_fecha"`: Superó fecha_corte
- `"limite_tiempo"`: Superó tiempo_maximo_segundos
- `"sin_siguiente"`: No existe botón siguiente
- `"sin_siguiente_habilitado"`: Botón deshabilitado
- `"siguiente_timeout"`: Timeout esperando botón
- `"error_click"`: Error al hacer clic
- `"duplicado_encontrado"`: Expediente duplicado encontrado

**Ejemplo básico:**
```python
from playwright.async_api import async_playwright
from pjn.scraping.expedientes import extraer_expedientes_completos

async with async_playwright() as p:
    browser = await p.chromium.launch()
    page = await browser.new_page()

    # Navegar al listado de expedientes
    await page.goto("URL_DEL_PORTAL")

    # Extraer con configuración simple
    expedientes, motivo, metadata = await extraer_expedientes_completos(
        page,
        max_paginas=10,
    )

    print(f"Extraídos: {len(expedientes)} expedientes")
    print(f"Motivo: {motivo}")
    print(f"Metadata: {metadata}")
```

**Ejemplo avanzado:**
```python
from pjn.scraping.expedientes import extraer_expedientes_completos
from pjn.scraping.pagination import PrimeFacesPaginationStrategy

# Estrategia de paginación personalizada
strategy = PrimeFacesPaginationStrategy(
    timeout_ms=15_000,
    max_wait_content_ms=20_000,
)

# Extraer con filtros
expedientes, motivo, metadata = await extraer_expedientes_completos(
    page,
    max_paginas=50,
    fecha_corte="2024-01-01",           # Solo desde esta fecha
    tiempo_maximo_segundos=300,         # Máximo 5 minutos
    orden="fecha",                      # Ordenar por fecha
    omitir_duplicados=True,
    detener_en_duplicado=True,          # Detener en duplicado
    pagination_strategy=strategy,       # Usar estrategia custom
)
```

##### `extraer_expedientes_completos_modelos()`

Versión que retorna modelos `ExpedienteResumen` en lugar de dicts.

```python
async def extraer_expedientes_completos_modelos(
    page: Page,
    # ... mismos parámetros que extraer_expedientes_completos
) -> tuple[list[ExpedienteResumen], str, dict[str, object]]:
```

**Ejemplo:**
```python
from pjn.scraping.expedientes import extraer_expedientes_completos_modelos

expedientes, motivo, metadata = await extraer_expedientes_completos_modelos(
    page,
    max_paginas=10,
)

for exp in expedientes:
    print(f"{exp.numero}: {exp.caratula}")
    print(f"  Última actuación: {exp.ultima_actuacion}")
```

**Funciones Auxiliares (públicas):**

##### `extraer_datos_expediente()`

Extrae datos del expediente actualmente abierto.

```python
async def extraer_datos_expediente(page: Page) -> dict[str, str] | None:
```

**Retorna:**
```python
{
    "numero": "...",
    "caratula": "...",
    "dependencia": "...",
    "jurisdiccion": "...",
    "situacion": "..."
}
```

#### 4.2 Scraping de Actuaciones (`pjn.scraping.actuaciones`)

**Funciones Principales (Puras - Recomendadas):**

##### `extraer_actuaciones_datos()`

Extrae actuaciones de un expediente y retorna modelo (sin guardar archivos).

```python
async def extraer_actuaciones_datos(
    page: Page,
    expediente_datos: dict[str, str],
) -> ActuacionesArchivo:
```

**Parámetros:**
- `page`: Página de Playwright con el expediente abierto
- `expediente_datos`: Dict con datos del expediente (numero, caratula, etc.)

**Retorna:**
- `ActuacionesArchivo`: Modelo con actuaciones extraídas

**Raises:**
- `ExtraccionError`: Si hay error en la extracción
- `TimeoutExtraccion`: Si timeout esperando elementos
- `ActuacionesNoDisponibles`: Si no hay actuaciones

**Ejemplo:**
```python
from pjn.scraping.actuaciones import extraer_actuaciones_datos
from pjn.exceptions import ExtraccionError

try:
    # Datos del expediente
    expediente = {
        "numero": "EXP-123/2024",
        "caratula": "CASO DE PRUEBA",
        "dependencia": "JUZGADO NACIONAL",
    }

    # Extraer actuaciones (sin guardar)
    archivo = await extraer_actuaciones_datos(page, expediente)

    print(f"Actuaciones extraídas: {len(archivo.actuaciones)}")
    for act in archivo.actuaciones:
        print(f"{act.fecha}: {act.tipo} - {act.detalle}")
        print(f"  Archivos: {len(act.archivos)}")

except ExtraccionError as e:
    print(f"Error: {e}")
```

##### `extraer_actuaciones_pagina_modelos()`

Extrae actuaciones de una sola página.

```python
async def extraer_actuaciones_pagina_modelos(
    page_expediente: Page,
    expediente_datos: dict[str, str],
    indice_inicial: int = 1,
) -> list[Actuacion]:
```

**Ejemplo:**
```python
# Extraer solo primera página
actuaciones = await extraer_actuaciones_pagina_modelos(
    page,
    expediente_datos,
    indice_inicial=1,
)
```

##### `descargar_archivos_actuaciones_modelos()`

Descarga archivos de actuaciones (función pura).

```python
async def descargar_archivos_actuaciones_modelos(
    page: Page,
    actuaciones: list[Actuacion],
    carpeta_destino: str,
) -> list[Actuacion]:
```

**Parámetros:**
- `page`: Página de Playwright
- `actuaciones`: Lista de actuaciones (con archivos pendientes)
- `carpeta_destino`: Carpeta donde guardar archivos

**Retorna:**
- `list[Actuacion]`: Nueva lista con estado actualizado (no modifica original)

**Ejemplo:**
```python
from pjn.scraping.actuaciones import (
    extraer_actuaciones_datos,
    descargar_archivos_actuaciones_modelos,
)

# Extraer actuaciones
archivo = await extraer_actuaciones_datos(page, expediente)

# Filtrar solo actuaciones con archivos
con_archivos = [
    act for act in archivo.actuaciones
    if act.archivos and any(not a.descargado for a in act.archivos)
]

# Descargar archivos
actuaciones_actualizadas = await descargar_archivos_actuaciones_modelos(
    page,
    con_archivos,
    "datos/expediente-123",
)

print(f"Archivos descargados: {sum(len(a.archivos) for a in actuaciones_actualizadas)}")
```

**Funciones Utilitarias:**

##### `calcular_metricas_descargas_json()`

Calcula métricas de descargas.

```python
def calcular_metricas_descargas_json(
    payload: dict[str, Any]
) -> dict[str, Any]:
```

**Funciones Legacy (Deprecated pero compatibles):**

##### `extraer_actuaciones_completas()` ⚠️ Deprecated

Versión antigua que guarda archivos automáticamente.

```python
async def extraer_actuaciones_completas(
    page: Page,
    expediente_datos: dict[str, str],
    directorio_destino: str,
) -> tuple[ActuacionesArchivo | None, str | None]:
```

**Nota:** Se recomienda usar `extraer_actuaciones_datos()` + funciones de persistencia.

#### 4.3 Scraping de Entradas (`pjn.scraping.entradas`)

**Función Principal:**

##### `extraer_entradas_datos()`

Extrae entradas/notificaciones del PJN (función pura).

```python
async def extraer_entradas_datos(
    page: Page,
    duplicados: bool = False,
    incluir_tipos: tuple[str, ...] = ("N", "D"),
    fechas: Optional[Iterable[str]] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    historial_existente: Optional[List[Entrada]] = None,
) -> List[Entrada]:
```

**Parámetros:**
- `page`: Página con la lista de entradas abierta
- `duplicados`: Si False, deduplica por (numero, fecha, caratula, evento)
- `incluir_tipos`: Tipos a incluir: `('N',)` notificaciones, `('D',)` despachos, `('N', 'D')` ambos
- `fechas`: Lista de fechas exactas (YYYY-MM-DD o DD/MM/YYYY)
- `fecha_desde`: Fecha inicio de rango
- `fecha_hasta`: Fecha fin de rango
- `historial_existente`: Lista de entradas previas para deduplicación

**Retorna:**
- `List[Entrada]`: Lista de modelos de entrada

**Raises:**
- `ExtraccionError`: Si no se puede acceder al contenedor

**Ejemplo básico:**
```python
from pjn.scraping.entradas import extraer_entradas_datos

# Extraer todas las notificaciones y despachos
entradas = await extraer_entradas_datos(page)

print(f"Entradas extraídas: {len(entradas)}")
for entrada in entradas:
    print(f"{entrada.fecha} - {entrada.tipo_evento}: {entrada.numero}")
```

**Ejemplo con filtros:**
```python
# Solo notificaciones
notificaciones = await extraer_entradas_datos(
    page,
    incluir_tipos=("N",),  # Solo 'N'
)

# Solo despachos
despachos = await extraer_entradas_datos(
    page,
    incluir_tipos=("D",),  # Solo 'D'
)

# Fechas específicas
entradas_enero = await extraer_entradas_datos(
    page,
    fechas=["2024-01-15", "2024-01-16"],  # Solo estos días
)

# Rango de fechas
entradas_mes = await extraer_entradas_datos(
    page,
    fecha_desde="2024-01-01",
    fecha_hasta="2024-01-31",
)
```

**Ejemplo con deduplicación:**
```python
# Primera extracción
entradas_ayer = await extraer_entradas_datos(page)

# Segunda extracción (hoy) - deduplicar contra ayer
entradas_hoy = await extraer_entradas_datos(
    page,
    historial_existente=entradas_ayer,  # Deduplica contra estas
)

print(f"Nuevas entradas: {len(entradas_hoy)}")
```

##### `extraer_entradas_pjn()` ⚠️ Deprecated

Versión antigua que guarda JSON/CSV automáticamente.

```python
async def extraer_entradas_pjn(
    page: Page,
    destino: Optional[str] = None,
    # ... otros parámetros
) -> int:
```

#### 4.4 Estrategias de Paginación (`pjn.scraping.pagination`)

**Protocol:**

##### `PaginationStrategy`

Define interfaz para estrategias de paginación.

```python
class PaginationStrategy(Protocol):
    async def navegar_siguiente(
        self,
        page: Page,
        tbody_locator: Locator,
        fingerprint_actual: str,
    ) -> tuple[bool, str | None]:
        ...
```

**Implementaciones:**

##### `PrimeFacesPaginationStrategy`

Estrategia para portales con PrimeFaces.

```python
class PrimeFacesPaginationStrategy:
    def __init__(
        self,
        selector_siguiente: str | None = None,
        timeout_ms: int = 10_000,
        max_wait_content_ms: int = 12_000,
        poll_interval_ms: int = 400,
    ):
```

**Parámetros:**
- `selector_siguiente`: Selector del botón (None = selectores por defecto)
- `timeout_ms`: Timeout para esperar botón
- `max_wait_content_ms`: Timeout para cambio de contenido
- `poll_interval_ms`: Intervalo de polling

**Ejemplo:**
```python
from pjn.scraping.pagination import PrimeFacesPaginationStrategy
from pjn.scraping.expedientes import extraer_expedientes_completos

# Crear estrategia personalizada
strategy = PrimeFacesPaginationStrategy(
    timeout_ms=15_000,        # 15 segundos para botón
    max_wait_content_ms=20_000,  # 20 segundos para contenido
)

# Usar en extracción
expedientes, motivo, metadata = await extraer_expedientes_completos(
    page,
    pagination_strategy=strategy,
)
```

**Crear Estrategia Personalizada:**

```python
class MyCustomPaginationStrategy:
    async def navegar_siguiente(self, page, tbody_locator, fingerprint_actual):
        # Implementar lógica de navegación
        # ...
        return (True, None)  # (exito, motivo_fallo)

# Usar
custom = MyCustomPaginationStrategy()
expedientes, motivo, metadata = await extraer_expedientes_completos(
    page,
    pagination_strategy=custom,
)
```

### 5. Módulo de Persistencia (`pjn.persistence`)

Funciones para I/O de archivos JSON/CSV.

#### 5.1 Persistencia de Actuaciones (`pjn.persistence.actuaciones`)

##### `cargar_actuaciones_json()`

Carga JSON raw de actuaciones.

```python
def cargar_actuaciones_json(ruta: str | Path) -> dict[str, Any]:
```

##### `cargar_actuaciones_archivo()`

Carga JSON y convierte a modelo.

```python
def cargar_actuaciones_archivo(ruta: str | Path) -> ActuacionesArchivo:
```

##### `guardar_actuaciones_json()`

Guarda modelo como JSON.

```python
def guardar_actuaciones_json(
    archivo: ActuacionesArchivo,
    directorio: str | Path,
) -> str:
```

**Retorna:**
- `str`: Ruta del archivo guardado

##### `listar_archivos_actuaciones()`

Lista archivos JSON de actuaciones en un directorio.

```python
def listar_archivos_actuaciones(directorio: str | Path) -> list[Path]:
```

##### `extraer_actuaciones_con_archivos()`

Filtra actuaciones que tienen archivos pendientes.

```python
def extraer_actuaciones_con_archivos(
    archivo: ActuacionesArchivo
) -> list[Actuacion]:
```

##### `actualizar_descargados()`

Actualiza el estado de archivos descargados en JSON.

```python
def actualizar_descargados(
    ruta_json: str | Path,
    actuaciones_actualizadas: list[Actuacion],
) -> None:
```

**Ejemplo Completo:**

```python
from pjn.persistence.actuaciones import (
    cargar_actuaciones_archivo,
    guardar_actuaciones_json,
    extraer_actuaciones_con_archivos,
)
from pjn.scraping.actuaciones import (
    extraer_actuaciones_datos,
    descargar_archivos_actuaciones_modelos,
)

# 1. Extraer actuaciones
archivo = await extraer_actuaciones_datos(page, expediente)

# 2. Guardar JSON
ruta = guardar_actuaciones_json(archivo, "datos/exp-123")
print(f"Guardado en: {ruta}")

# 3. Más tarde: cargar y procesar
archivo_cargado = cargar_actuaciones_archivo(ruta)

# 4. Filtrar con archivos pendientes
con_archivos = extraer_actuaciones_con_archivos(archivo_cargado)

# 5. Descargar archivos
actuaciones_actualizadas = await descargar_archivos_actuaciones_modelos(
    page,
    con_archivos,
    "datos/exp-123",
)

# 6. Actualizar JSON
actualizar_descargados(ruta, actuaciones_actualizadas)
```

### 6. Módulo de Parsers (`pjn.parsers`)

Convierten HTML a modelos de datos.

#### 6.1 Parser de Actuaciones (`pjn.parsers.actuaciones_parser`)

##### `parse_actuacion()`

Parsea una fila de actuación.

```python
def parse_actuacion(
    fila_html: ElementHandle,
    expediente_numero: str,
    indice: int,
) -> Actuacion:
```

#### 6.2 Parser de Entradas (`pjn.parsers.entradas_parser`)

##### `parse_entrada()`

Crea modelo Entrada desde datos.

```python
def parse_entrada(
    numero: str,
    caratula: str,
    fecha: str,
    evento: str,
    tipo_evento: str,
    leida: bool,
    extraida_en: str,
) -> Entrada:
```

#### 6.3 Parser de Expedientes (`pjn.parsers.expedientes_parser`)

##### `parse_expediente_resumen()`

Parsea una fila del listado de expedientes.

```python
def parse_expediente_resumen(
    fila_html: ElementHandle
) -> ExpedienteResumen:
```

### 7. Módulo de Utilidades (`pjn.utils`)

#### 7.1 Logging (`pjn.utils.logging`)

##### `get_logger()`

Obtiene logger configurado.

```python
def get_logger(name: str) -> logging.Logger:
```

**Ejemplo:**
```python
from pjn.utils.logging import get_logger

logger = get_logger(__name__)
logger.info("Iniciando extracción")
logger.warning("Timeout detectado")
logger.error("Error crítico")
```

### 8. Selectores CSS (`pjn.selectores`)

Constantes con selectores CSS para el PJN.

**Clases:**
- `SEL_EXPEDIENTES`: Selectores para expedientes
- `SEL_ACTUACIONES`: Selectores para actuaciones
- `SEL_ENTRADAS`: Selectores para entradas

**Ejemplo:**
```python
from pjn.selectores import SEL_EXPEDIENTES

# Usar selectores
await page.wait_for_selector(SEL_EXPEDIENTES.TABLA_RESULTADOS)
numero = await page.query_selector(SEL_EXPEDIENTES.NUMERO_DETALLE)
```

---

## Configuración

### Estructura de Configuración

```python
@dataclass
class ScrapingConfig:
    timeout_default: int = 15_000          # ms
    timeout_navegacion: int = 30_000       # ms
    timeout_descarga: int = 120_000        # ms
    max_paginas_expedientes: int = 200
    expedientes_por_pagina: int = 25

@dataclass
class BrowserConfig:
    headless: bool = True
    slow_mo: int = 0
    download_path: str = "./descargas"

@dataclass
class AuthConfig:
    cuil: str = ""
    password: str = ""

@dataclass
class ArchivosConfig:
    directorio_base: str = "./datos_extraidos"

@dataclass
class Config:
    scraping: ScrapingConfig
    browser: BrowserConfig
    auth: AuthConfig
    archivos: ArchivosConfig
```

### Configuración por Variables de Entorno

```bash
# .env
PJN_TIMEOUT_DEFAULT=20000
PJN_MAX_PAGINAS=100
PJN_HEADLESS=false
PJN_CUIL=20123456789
PJN_PASSWORD=mi_password_seguro
```

### Ejemplo de Configuración Personalizada

```python
from pjn.config import Config, ScrapingConfig, BrowserConfig, set_config

# Configuración para testing
test_config = Config(
    scraping=ScrapingConfig(
        timeout_default=5_000,      # Timeouts cortos
        max_paginas_expedientes=2,  # Solo 2 páginas
    ),
    browser=BrowserConfig(
        headless=False,              # Visible para debug
        slow_mo=500,                 # Slow motion
    ),
)

set_config(test_config)
```

---

## Excepciones

### Jerarquía Completa

```python
Exception
└── PJNError                      # Base para todas las excepciones del sistema
    └── ExtraccionError          # Error general de extracción
        ├── TimeoutExtraccion    # Timeout esperando elementos
        └── ActuacionesNoDisponibles  # No hay actuaciones disponibles
```

### Uso de Excepciones

```python
from pjn.exceptions import (
    PJNError,
    ExtraccionError,
    TimeoutExtraccion,
    ActuacionesNoDisponibles,
)

# Captura específica
try:
    archivo = await extraer_actuaciones_datos(page, expediente)
except TimeoutExtraccion:
    logger.warning("Timeout - reintentando con más tiempo...")
    # Reintentar
except ActuacionesNoDisponibles:
    logger.info("Este expediente no tiene actuaciones")
    # OK, continuar
except ExtraccionError as e:
    logger.error(f"Error inesperado: {e}")
    raise

# Captura genérica
try:
    resultado = await alguna_operacion()
except PJNError as e:
    # Cualquier error del sistema PJN
    logger.exception("Error del sistema PJN")
```

---

*Continúa en siguiente mensaje...*
