# 📋 Inventario Completo de Funciones - Sistema_v5

**Versión:** 5.5
**Última actualización:** 2025-10-15

---

## Índice

1. [Módulo de Scraping](#módulo-de-scraping)
2. [Módulo de Persistencia](#módulo-de-persistencia)
3. [Módulo de Parsers](#módulo-de-parsers)
4. [Módulo de Modelos](#módulo-de-modelos)
5. [Módulo de Configuración](#módulo-de-configuración)
6. [Módulo de Excepciones](#módulo-de-excepciones)
7. [Módulo de Utilidades](#módulo-de-utilidades)
8. [Funciones Internas (Private)](#funciones-internas-private)

---

## Módulo de Scraping

### `pjn.scraping.expedientes`

#### Funciones Públicas

##### `extraer_expedientes_completos()`

**Signatura:**
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
) -> tuple[list[TResumen], str, dict[str, object]]
```

**Descripción:** Extrae todas las páginas del listado de expedientes con filtros avanzados.

**Parámetros:**
- `page` (Page): Página de Playwright con el listado
- `sel_tabla` (str): Selector CSS de la tabla
- `sel_tbody` (str): Selector del tbody
- `sel_siguiente` (str): Selector del botón "Siguiente"
- `max_paginas` (int | None): Límite de páginas
- `omitir_duplicados` (bool): Si omitir duplicados
- `detener_en_duplicado` (bool): Si detener en duplicado
- `fecha_corte` (str | None): Fecha mínima YYYY-MM-DD
- `tiempo_maximo_segundos` (int | None): Timeout de extracción
- `orden` (str | None): Criterio de ordenamiento
- `mapper` (Callable): Función de transformación
- `pagination_strategy` (PaginationStrategy | None): Estrategia de paginación

**Retorna:**
- `tuple[list, str, dict]`: (expedientes, motivo, metadata)

**Raises:**
- Ninguna (maneja errores internamente)

**Tipo:** Asíncrona

---

##### `extraer_expedientes_completos_modelos()`

**Signatura:**
```python
async def extraer_expedientes_completos_modelos(
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
    pagination_strategy: PaginationStrategy | None = None,
) -> tuple[list[ExpedienteResumen], str, dict[str, object]]
```

**Descripción:** Versión que retorna modelos ExpedienteResumen.

**Parámetros:** Mismos que `extraer_expedientes_completos()`

**Retorna:**
- `tuple[list[ExpedienteResumen], str, dict]`: (expedientes, motivo, metadata)

**Tipo:** Asíncrona

---

##### `extraer_datos_expediente()`

**Signatura:**
```python
async def extraer_datos_expediente(page: Page) -> dict[str, str] | None
```

**Descripción:** Extrae datos del expediente actualmente abierto.

**Parámetros:**
- `page` (Page): Página con el expediente abierto

**Retorna:**
- `dict[str, str] | None`: Diccionario con datos o None si error

**Tipo:** Asíncrona

---

#### Funciones Internas (Documentadas para referencia)

##### `_parsear_fecha_corte()`

**Signatura:**
```python
def _parsear_fecha_corte(fecha_corte: str | None) -> datetime | None
```

**Descripción:** Parsea y valida la fecha de corte.

**Raises:** ValueError si formato inválido

---

##### `_aplicar_ordenamiento_tabla()`

**Signatura:**
```python
async def _aplicar_ordenamiento_tabla(
    page: Page,
    tabla: Locator,
    orden: str | None,
) -> None
```

**Descripción:** Aplica ordenamiento a la tabla.

---

##### `_procesar_expediente_resumen()`

**Signatura:**
```python
def _procesar_expediente_resumen(
    resumen: ExpedienteResumen,
    fecha_corte_dt: datetime | None,
    huellas: set[tuple[str, str, str]],
    omitir_duplicados: bool,
    detener_en_duplicado: bool,
) -> tuple[bool, bool, bool]
```

**Descripción:** Procesa un resumen y determina si agregarlo.

**Retorna:** (agregar, detener, es_duplicado)

---

##### `_navegar_siguiente_pagina()`

**Signatura:**
```python
async def _navegar_siguiente_pagina(
    page: Page,
    tbody_locator: Locator,
    sel_siguiente: str,
    fingerprint_actual: str,
    estrategia: PaginationStrategy | None = None,
) -> tuple[bool, str | None]
```

**Descripción:** Navega a siguiente página.

**Retorna:** (exito, motivo_fallo)

---

### `pjn.scraping.actuaciones`

#### Funciones Públicas (Recomendadas)

##### `extraer_actuaciones_datos()`

**Signatura:**
```python
async def extraer_actuaciones_datos(
    page: Page,
    expediente_datos: dict[str, str],
) -> ActuacionesArchivo
```

**Descripción:** Extrae actuaciones y retorna modelo (sin guardar archivos).

**Parámetros:**
- `page` (Page): Página con expediente abierto
- `expediente_datos` (dict): Datos del expediente

**Retorna:**
- `ActuacionesArchivo`: Modelo con actuaciones

**Raises:**
- `ExtraccionError`: Error en extracción
- `TimeoutExtraccion`: Timeout esperando elementos
- `ActuacionesNoDisponibles`: No hay actuaciones

**Tipo:** Asíncrona, Pura (sin side effects)

---

##### `extraer_actuaciones_pagina_modelos()`

**Signatura:**
```python
async def extraer_actuaciones_pagina_modelos(
    page_expediente: Page,
    expediente_datos: dict[str, str],
    indice_inicial: int = 1,
) -> list[Actuacion]
```

**Descripción:** Extrae actuaciones de una sola página.

**Parámetros:**
- `page_expediente` (Page): Página del expediente
- `expediente_datos` (dict): Datos del expediente
- `indice_inicial` (int): Índice inicial

**Retorna:**
- `list[Actuacion]`: Lista de actuaciones

**Raises:**
- `TimeoutExtraccion`: Timeout
- `ExtraccionError`: Error de extracción

**Tipo:** Asíncrona, Pura

---

##### `descargar_archivos_actuaciones_modelos()`

**Signatura:**
```python
async def descargar_archivos_actuaciones_modelos(
    page: Page,
    actuaciones: list[Actuacion],
    carpeta_destino: str,
) -> list[Actuacion]
```

**Descripción:** Descarga archivos de actuaciones (función pura).

**Parámetros:**
- `page` (Page): Página de Playwright
- `actuaciones` (list[Actuacion]): Lista de actuaciones
- `carpeta_destino` (str): Carpeta destino

**Retorna:**
- `list[Actuacion]`: Nueva lista con estado actualizado

**Tipo:** Asíncrona, Pura (retorna nueva lista)

---

##### `calcular_metricas_descargas_json()`

**Signatura:**
```python
def calcular_metricas_descargas_json(
    payload: dict[str, Any]
) -> dict[str, Any]
```

**Descripción:** Calcula métricas de descargas.

**Parámetros:**
- `payload` (dict): Payload con actuaciones

**Retorna:**
- `dict[str, Any]`: Payload actualizado con métricas

**Tipo:** Síncrona, Pura

---

#### Funciones Deprecated (Compatibilidad)

##### `extraer_actuaciones_completas()` ⚠️

**Signatura:**
```python
async def extraer_actuaciones_completas(
    page: Page,
    expediente_datos: dict[str, str],
    directorio_destino: str,
) -> tuple[ActuacionesArchivo | None, str | None]
```

**Descripción:** Versión antigua que guarda archivos automáticamente.

**Tipo:** Asíncrona, **Deprecated**

**Nota:** Usar `extraer_actuaciones_datos()` + persistencia

---

##### `extraer_actuaciones_pagina()` ⚠️

**Signatura:**
```python
async def extraer_actuaciones_pagina(
    page_expediente: Page,
    expediente_datos: dict[str, str],
    indice_inicial: int = 1,
) -> tuple[list[dict], str | None]
```

**Descripción:** Versión deprecated que retorna tuple.

**Tipo:** Asíncrona, **Deprecated**

---

### `pjn.scraping.entradas`

#### Funciones Públicas

##### `extraer_entradas_datos()`

**Signatura:**
```python
async def extraer_entradas_datos(
    page: Page,
    duplicados: bool = False,
    incluir_tipos: tuple[str, ...] = ("N", "D"),
    fechas: Optional[Iterable[str]] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    historial_existente: Optional[List[Entrada]] = None,
) -> List[Entrada]
```

**Descripción:** Extrae entradas del PJN (función pura).

**Parámetros:**
- `page` (Page): Página con lista de entradas
- `duplicados` (bool): Si permitir duplicados
- `incluir_tipos` (tuple): Tipos a incluir ('N', 'D')
- `fechas` (Optional[Iterable[str]]): Fechas exactas
- `fecha_desde` (str | None): Fecha inicio
- `fecha_hasta` (str | None): Fecha fin
- `historial_existente` (List[Entrada] | None): Historial para deduplicar

**Retorna:**
- `List[Entrada]`: Lista de modelos de entrada

**Raises:**
- `ExtraccionError`: Si no se puede acceder al contenedor

**Tipo:** Asíncrona, Pura

---

##### `extraer_entradas_pjn()` ⚠️

**Signatura:**
```python
async def extraer_entradas_pjn(
    page: Page,
    destino: Optional[str] = None,
    duplicados: bool = False,
    incluir_tipos: tuple[str, ...] = ("N", "D"),
    fechas: Optional[Iterable[str]] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    coleccion_modelos: Optional[List[Entrada]] = None,
) -> int
```

**Descripción:** Versión deprecated que guarda JSON/CSV.

**Tipo:** Asíncrona, **Deprecated**

---

#### Funciones Auxiliares Internas

##### `_preparar_filtros_y_historial()`

**Signatura:**
```python
def _preparar_filtros_y_historial(
    fechas: Optional[Iterable[str]],
    fecha_desde: Optional[str],
    fecha_hasta: Optional[str],
    historial_existente: Optional[List[Entrada]],
) -> tuple[set[str], Optional[date], Optional[date], list[Dict], set[tuple], set[tuple]]
```

**Descripción:** Prepara filtros y estructuras de deduplicación.

---

##### `_configurar_pagina_scroll()`

**Signatura:**
```python
async def _configurar_pagina_scroll(page: Page) -> tuple
```

**Descripción:** Configura página para scroll infinito.

**Retorna:** (cont, fin_loc, loading_loc)

---

##### `_procesar_fila_entrada()`

**Signatura:**
```python
async def _procesar_fila_entrada(
    fila,
    incluir_tipos: tuple[str, ...],
    fechas_exactas: set[str],
    rango_desde: Optional[date],
    rango_hasta: Optional[date],
    contadores: ContadoresDiagnostico,
) -> Optional[Entrada]
```

**Descripción:** Procesa una fila y retorna Entrada si pasa filtros.

---

##### `_aplicar_deduplicacion()`

**Signatura:**
```python
def _aplicar_deduplicacion(
    entrada_modelo: Entrada,
    historial_dicts: list[Dict[str, Any]],
    claves_hist_base: set[tuple],
    claves_hist_event: set[tuple],
    vistos_run_event: set[tuple],
) -> bool
```

**Descripción:** Aplica deduplicación.

**Retorna:** True si debe agregarse

---

##### `_ejecutar_scroll_y_esperar()`

**Signatura:**
```python
async def _ejecutar_scroll_y_esperar(
    page: Page,
    cont_locator,
    loading_loc,
    ultima_fila_prev: str,
    _ultima_fila_texto_fn,
) -> tuple[str, bool]
```

**Descripción:** Ejecuta scroll y espera carga.

---

##### `_loguear_diagnostico()`

**Signatura:**
```python
def _loguear_diagnostico(
    nuevas_entradas: List[Entrada],
    contadores: ContadoresDiagnostico
) -> None
```

**Descripción:** Loguea resumen de diagnóstico.

---

##### `ContadoresDiagnostico` (Clase)

**Descripción:** Clase para mantener contadores de diagnóstico.

**Atributos:**
```python
filas_procesadas: int
filas_sin_numero: int
filas_sin_caratula: int
filas_sin_celdas: int
filas_sin_fecha: int
filas_sin_evento: int
filas_filtradas_tipo: int
filas_filtradas_fecha: int
```

---

### `pjn.scraping.pagination`

#### Protocol

##### `PaginationStrategy`

**Signatura:**
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

**Descripción:** Protocol para estrategias de paginación.

---

#### Clases

##### `PrimeFacesPaginationStrategy`

**Constructor:**
```python
def __init__(
    self,
    selector_siguiente: str | None = None,
    timeout_ms: int = 10_000,
    max_wait_content_ms: int = 12_000,
    poll_interval_ms: int = 400,
)
```

**Método:**
```python
async def navegar_siguiente(
    self,
    page: Page,
    tbody_locator: Locator,
    fingerprint_actual: str,
) -> tuple[bool, str | None]
```

**Descripción:** Estrategia de paginación para PrimeFaces.

---

### `pjn.scraping.base`

#### Funciones Públicas

##### `limpiar_texto()`

**Signatura:**
```python
def limpiar_texto(texto: str) -> str
```

**Descripción:** Limpia texto removiendo espacios extra.

---

##### `normalizar_texto()`

**Signatura:**
```python
def normalizar_texto(texto: str) -> str
```

**Descripción:** Normaliza texto para comparaciones.

---

## Módulo de Persistencia

### `pjn.persistence.actuaciones`

#### Funciones Públicas

##### `cargar_actuaciones_json()`

**Signatura:**
```python
def cargar_actuaciones_json(ruta: str | Path) -> dict[str, Any]
```

**Descripción:** Carga JSON raw de actuaciones.

**Tipo:** Síncrona

---

##### `cargar_actuaciones_archivo()`

**Signatura:**
```python
def cargar_actuaciones_archivo(ruta: str | Path) -> ActuacionesArchivo
```

**Descripción:** Carga JSON y convierte a modelo.

**Tipo:** Síncrona

---

##### `guardar_actuaciones_json()`

**Signatura:**
```python
def guardar_actuaciones_json(
    archivo: ActuacionesArchivo,
    directorio: str | Path,
) -> str
```

**Descripción:** Guarda modelo como JSON.

**Retorna:** Ruta del archivo guardado

**Tipo:** Síncrona

---

##### `listar_archivos_actuaciones()`

**Signatura:**
```python
def listar_archivos_actuaciones(directorio: str | Path) -> list[Path]
```

**Descripción:** Lista archivos JSON de actuaciones.

**Tipo:** Síncrona

---

##### `extraer_actuaciones_con_archivos()`

**Signatura:**
```python
def extraer_actuaciones_con_archivos(
    archivo: ActuacionesArchivo
) -> list[Actuacion]
```

**Descripción:** Filtra actuaciones con archivos pendientes.

**Tipo:** Síncrona, Pura

---

##### `actualizar_descargados()`

**Signatura:**
```python
def actualizar_descargados(
    ruta_json: str | Path,
    actuaciones_actualizadas: list[Actuacion],
) -> None
```

**Descripción:** Actualiza estado de archivos descargados.

**Tipo:** Síncrona

---

## Módulo de Parsers

### `pjn.parsers.actuaciones_parser`

##### `parse_actuacion()`

**Signatura:**
```python
def parse_actuacion(
    fila_html: ElementHandle,
    expediente_numero: str,
    indice: int,
) -> Actuacion
```

**Descripción:** Parsea fila HTML a modelo Actuacion.

---

### `pjn.parsers.entradas_parser`

##### `parse_entrada()`

**Signatura:**
```python
def parse_entrada(
    numero: str,
    caratula: str,
    fecha: str,
    evento: str,
    tipo_evento: str,
    leida: bool,
    extraida_en: str,
) -> Entrada
```

**Descripción:** Crea modelo Entrada desde datos.

---

### `pjn.parsers.expedientes_parser`

##### `parse_expediente_resumen()`

**Signatura:**
```python
def parse_expediente_resumen(fila_html: ElementHandle) -> ExpedienteResumen
```

**Descripción:** Parsea fila de listado a modelo ExpedienteResumen.

---

## Módulo de Modelos

### `pjn.models.actuacion`

#### Clases

##### `Archivo`

**Atributos:**
```python
nombre: str
url: str
descargado: bool
ruta_local: str | None
```

**Métodos:**
```python
to_dict() -> dict
from_dict(data: dict) -> Archivo
```

---

##### `Actuacion`

**Atributos:**
```python
indice: int
numero: str
fecha: str
tipo: str
detalle: str
archivos: List[Archivo]
```

**Métodos:**
```python
to_dict() -> dict
from_dict(data: dict) -> Actuacion
```

---

##### `ActuacionesArchivo`

**Atributos:**
```python
numero_expediente: str
caratula: str
actuaciones: List[Actuacion]
metadata: dict
```

**Métodos:**
```python
to_dict() -> dict
from_dict(data: dict) -> ActuacionesArchivo
```

---

### `pjn.models.entrada`

##### `Entrada`

**Atributos:**
```python
numero: str
caratula: str
fecha: str
evento: str
tipo_evento: str
leida: bool
extraida_en: str
```

**Métodos:**
```python
to_dict() -> dict
from_dict(data: dict) -> Entrada
```

---

### `pjn.models.expediente`

##### `ExpedienteResumen`

**Atributos:**
```python
numero: str
dependencia: str
caratula: str
situacion: str
ultima_actuacion: str
```

**Métodos:**
```python
to_dict() -> dict
from_dict(data: dict) -> ExpedienteResumen
```

---

## Módulo de Configuración

### `pjn.config`

#### Clases

##### `ScrapingConfig`

**Atributos:**
```python
timeout_default: int
timeout_navegacion: int
timeout_descarga: int
max_paginas_expedientes: int
expedientes_por_pagina: int
```

---

##### `BrowserConfig`

**Atributos:**
```python
headless: bool
slow_mo: int
download_path: str
```

---

##### `AuthConfig`

**Atributos:**
```python
cuil: str
password: str
```

---

##### `ArchivosConfig`

**Atributos:**
```python
directorio_base: str
```

---

##### `Config`

**Atributos:**
```python
scraping: ScrapingConfig
browser: BrowserConfig
auth: AuthConfig
archivos: ArchivosConfig
```

**Métodos estáticos:**
```python
@staticmethod
def for_testing() -> Config
```

---

#### Funciones

##### `get_config()`

**Signatura:**
```python
def get_config() -> Config
```

**Descripción:** Obtiene configuración global.

---

##### `set_config()`

**Signatura:**
```python
def set_config(config: Config) -> None
```

**Descripción:** Establece configuración global.

---

## Módulo de Excepciones

### `pjn.exceptions`

#### Clases

##### `PJNError`

**Descripción:** Excepción base del sistema.

**Hereda de:** Exception

---

##### `ExtraccionError`

**Descripción:** Error general de extracción.

**Hereda de:** PJNError

---

##### `TimeoutExtraccion`

**Descripción:** Timeout esperando elementos.

**Hereda de:** ExtraccionError

---

##### `ActuacionesNoDisponibles`

**Descripción:** No hay actuaciones disponibles.

**Hereda de:** ExtraccionError

---

## Módulo de Utilidades

### `pjn.utils.logging`

##### `get_logger()`

**Signatura:**
```python
def get_logger(name: str) -> logging.Logger
```

**Descripción:** Obtiene logger configurado para el módulo.

**Parámetros:**
- `name` (str): Nombre del logger (típicamente `__name__`)

**Retorna:**
- `logging.Logger`: Logger configurado

**Tipo:** Síncrona

---

## Resumen Estadístico

### Por Tipo de Función

- **Funciones Asíncronas:** 25
- **Funciones Síncronas:** 30
- **Funciones Puras (sin side effects):** 18
- **Funciones Deprecated:** 6
- **Clases:** 15
- **Protocols:** 1

### Por Módulo

| Módulo | Funciones Públicas | Funciones Internas | Total |
|--------|-------------------|-------------------|-------|
| scraping.expedientes | 3 | 8 | 11 |
| scraping.actuaciones | 4 + 3 deprecated | 5 | 12 |
| scraping.entradas | 1 + 1 deprecated | 6 | 8 |
| scraping.pagination | 1 Protocol + 1 Clase | 2 | 4 |
| scraping.base | 2 | 0 | 2 |
| persistence.actuaciones | 6 | 0 | 6 |
| parsers | 3 | 0 | 3 |
| models | 6 clases | 0 | 6 |
| config | 2 + 5 clases | 0 | 7 |
| exceptions | 4 clases | 0 | 4 |
| utils.logging | 1 | 0 | 1 |

### Por Estado

- **Producción (Recomendadas):** 42 funciones/clases
- **Deprecated (Compatibilidad):** 6 funciones
- **Internas (Documentadas):** 21 funciones

---

**Total de elementos documentados:** 69 funciones/métodos + 15 clases = **84 elementos**

---

**Fin de INVENTARIO_FUNCIONES.md**
