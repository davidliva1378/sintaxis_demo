# 📋 Inventario Completo de Funciones - Sistema_v5

**Generado automáticamente**
**Versión:** 5.6
**Última actualización:** 17 de octubre, 2025

---

## 📖 Índice de Módulos

- [pjn.config](#pjnconfig)
- [pjn.exceptions](#pjnexceptions)
- [pjn.models._utils](#pjnmodels-utils)
- [pjn.models.actuacion](#pjnmodelsactuacion)
- [pjn.models.entrada](#pjnmodelsentrada)
- [pjn.models.expediente](#pjnmodelsexpediente)
- [pjn.models.extraccion_config](#pjnmodelsextraccion-config)
- [pjn.monitor.config](#pjnmonitorconfig)
- [pjn.monitor.core](#pjnmonitorcore)
- [pjn.monitor.detector](#pjnmonitordetector)
- [pjn.monitor.notifier](#pjnmonitornotifier)
- [pjn.monitor.scheduler](#pjnmonitorscheduler)
- [pjn.monitor.storage](#pjnmonitorstorage)
- [pjn.parsers.actuaciones_parser](#pjnparsersactuaciones-parser)
- [pjn.parsers.entradas_parser](#pjnparsersentradas-parser)
- [pjn.parsers.expedientes_parser](#pjnparsersexpedientes-parser)
- [pjn.persistence.actuaciones](#pjnpersistenceactuaciones)
- [pjn.scraping.actuaciones](#pjnscrapingactuaciones)
- [pjn.scraping.actuaciones_utils](#pjnscrapingactuaciones-utils)
- [pjn.scraping.base](#pjnscrapingbase)
- [pjn.scraping.entradas](#pjnscrapingentradas)
- [pjn.scraping.expedientes](#pjnscrapingexpedientes)
- [pjn.scraping.pagination](#pjnscrapingpagination)
- [pjn.scripts.diagnostico_entradas](#pjnscriptsdiagnostico-entradas)
- [pjn.scripts.prueba_extractor_entradas](#pjnscriptsprueba-extractor-entradas)
- [pjn.scripts.rf_test_extraccion_completa](#pjnscriptsrf-test-extraccion-completa)
- [pjn.selectores](#pjnselectores)
- [pjn.utils.logging](#pjnutilslogging)

---

## `pjn.config`

### Clases

#### `ArchivosConfig`

**Decoradores:** `dataclass`

**Descripción:** Configuración para manejo de archivos descargados.

**Ubicación:** `pjn.config:187`

**Métodos públicos:**

##### `for_testing(cls) -> Config`

**Decoradores:** `classmethod`

**Documentación:**

```
Crea configuración optimizada para testing.

Returns:
    Config: Instancia con timeouts reducidos y límites bajos.
```

**Ubicación:** `pjn.config:261`

##### `from_env(cls) -> ScrapingConfig`

**Decoradores:** `classmethod`

**Documentación:**

```
Crea configuración desde variables de entorno.

Variables soportadas:
- PJN_MAX_PAGINAS: int
- PJN_TIMEOUT_DEFAULT: int (ms)
- PJN_TIMEOUT_LOGIN: int (ms)
- PJN_MAX_REINTENTOS_DESCARGA: int

Returns:
    ScrapingConfig: Instancia con valores desde env o defaults.
```

**Ubicación:** `pjn.config:87`

##### `from_env(cls) -> BrowserConfig`

**Decoradores:** `classmethod`

**Documentación:**

```
Crea configuración desde variables de entorno.

Variables soportadas:
- PJN_HEADLESS: 1/true/yes/y para True

Returns:
    BrowserConfig: Instancia con valores desde env o defaults.
```

**Ubicación:** `pjn.config:138`

##### `from_env(cls) -> AuthConfig`

**Decoradores:** `classmethod`

**Documentación:**

```
Crea configuración desde variables de entorno.

Variables soportadas:
- PJN_LOGIN_URL: str

Returns:
    AuthConfig: Instancia con valores desde env o defaults.
```

**Ubicación:** `pjn.config:168`

##### `from_env(cls) -> ArchivosConfig`

**Decoradores:** `classmethod`

**Documentación:**

```
Crea configuración desde variables de entorno.

Variables soportadas:
- PJN_DIR_ACTUACIONES: str
- PJN_DIR_ENTRADAS: str

Returns:
    ArchivosConfig: Instancia con valores desde env o defaults.
```

**Ubicación:** `pjn.config:211`

##### `from_env(cls) -> Config`

**Decoradores:** `classmethod`

**Documentación:**

```
Crea configuración completa desde variables de entorno.

Returns:
    Config: Instancia con todos los sub-configs desde env.
```

**Ubicación:** `pjn.config:247`


#### `AuthConfig`

**Decoradores:** `dataclass`

**Descripción:** Configuración de autenticación.

**Ubicación:** `pjn.config:158`

**Métodos públicos:**

##### `for_testing(cls) -> Config`

**Decoradores:** `classmethod`

**Documentación:**

```
Crea configuración optimizada para testing.

Returns:
    Config: Instancia con timeouts reducidos y límites bajos.
```

**Ubicación:** `pjn.config:261`

##### `from_env(cls) -> ScrapingConfig`

**Decoradores:** `classmethod`

**Documentación:**

```
Crea configuración desde variables de entorno.

Variables soportadas:
- PJN_MAX_PAGINAS: int
- PJN_TIMEOUT_DEFAULT: int (ms)
- PJN_TIMEOUT_LOGIN: int (ms)
- PJN_MAX_REINTENTOS_DESCARGA: int

Returns:
    ScrapingConfig: Instancia con valores desde env o defaults.
```

**Ubicación:** `pjn.config:87`

##### `from_env(cls) -> BrowserConfig`

**Decoradores:** `classmethod`

**Documentación:**

```
Crea configuración desde variables de entorno.

Variables soportadas:
- PJN_HEADLESS: 1/true/yes/y para True

Returns:
    BrowserConfig: Instancia con valores desde env o defaults.
```

**Ubicación:** `pjn.config:138`

##### `from_env(cls) -> AuthConfig`

**Decoradores:** `classmethod`

**Documentación:**

```
Crea configuración desde variables de entorno.

Variables soportadas:
- PJN_LOGIN_URL: str

Returns:
    AuthConfig: Instancia con valores desde env o defaults.
```

**Ubicación:** `pjn.config:168`

##### `from_env(cls) -> ArchivosConfig`

**Decoradores:** `classmethod`

**Documentación:**

```
Crea configuración desde variables de entorno.

Variables soportadas:
- PJN_DIR_ACTUACIONES: str
- PJN_DIR_ENTRADAS: str

Returns:
    ArchivosConfig: Instancia con valores desde env o defaults.
```

**Ubicación:** `pjn.config:211`

##### `from_env(cls) -> Config`

**Decoradores:** `classmethod`

**Documentación:**

```
Crea configuración completa desde variables de entorno.

Returns:
    Config: Instancia con todos los sub-configs desde env.
```

**Ubicación:** `pjn.config:247`


#### `BrowserConfig`

**Decoradores:** `dataclass`

**Descripción:** Configuración del browser Playwright.

**Ubicación:** `pjn.config:120`

**Métodos públicos:**

##### `for_testing(cls) -> Config`

**Decoradores:** `classmethod`

**Documentación:**

```
Crea configuración optimizada para testing.

Returns:
    Config: Instancia con timeouts reducidos y límites bajos.
```

**Ubicación:** `pjn.config:261`

##### `from_env(cls) -> ScrapingConfig`

**Decoradores:** `classmethod`

**Documentación:**

```
Crea configuración desde variables de entorno.

Variables soportadas:
- PJN_MAX_PAGINAS: int
- PJN_TIMEOUT_DEFAULT: int (ms)
- PJN_TIMEOUT_LOGIN: int (ms)
- PJN_MAX_REINTENTOS_DESCARGA: int

Returns:
    ScrapingConfig: Instancia con valores desde env o defaults.
```

**Ubicación:** `pjn.config:87`

##### `from_env(cls) -> BrowserConfig`

**Decoradores:** `classmethod`

**Documentación:**

```
Crea configuración desde variables de entorno.

Variables soportadas:
- PJN_HEADLESS: 1/true/yes/y para True

Returns:
    BrowserConfig: Instancia con valores desde env o defaults.
```

**Ubicación:** `pjn.config:138`

##### `from_env(cls) -> AuthConfig`

**Decoradores:** `classmethod`

**Documentación:**

```
Crea configuración desde variables de entorno.

Variables soportadas:
- PJN_LOGIN_URL: str

Returns:
    AuthConfig: Instancia con valores desde env o defaults.
```

**Ubicación:** `pjn.config:168`

##### `from_env(cls) -> ArchivosConfig`

**Decoradores:** `classmethod`

**Documentación:**

```
Crea configuración desde variables de entorno.

Variables soportadas:
- PJN_DIR_ACTUACIONES: str
- PJN_DIR_ENTRADAS: str

Returns:
    ArchivosConfig: Instancia con valores desde env o defaults.
```

**Ubicación:** `pjn.config:211`

##### `from_env(cls) -> Config`

**Decoradores:** `classmethod`

**Documentación:**

```
Crea configuración completa desde variables de entorno.

Returns:
    Config: Instancia con todos los sub-configs desde env.
```

**Ubicación:** `pjn.config:247`


#### `Config`

**Decoradores:** `dataclass`

**Descripción:** Configuración global del sistema.

**Ubicación:** `pjn.config:238`

**Métodos públicos:**

##### `for_testing(cls) -> Config`

**Decoradores:** `classmethod`

**Documentación:**

```
Crea configuración optimizada para testing.

Returns:
    Config: Instancia con timeouts reducidos y límites bajos.
```

**Ubicación:** `pjn.config:261`

##### `from_env(cls) -> ScrapingConfig`

**Decoradores:** `classmethod`

**Documentación:**

```
Crea configuración desde variables de entorno.

Variables soportadas:
- PJN_MAX_PAGINAS: int
- PJN_TIMEOUT_DEFAULT: int (ms)
- PJN_TIMEOUT_LOGIN: int (ms)
- PJN_MAX_REINTENTOS_DESCARGA: int

Returns:
    ScrapingConfig: Instancia con valores desde env o defaults.
```

**Ubicación:** `pjn.config:87`

##### `from_env(cls) -> BrowserConfig`

**Decoradores:** `classmethod`

**Documentación:**

```
Crea configuración desde variables de entorno.

Variables soportadas:
- PJN_HEADLESS: 1/true/yes/y para True

Returns:
    BrowserConfig: Instancia con valores desde env o defaults.
```

**Ubicación:** `pjn.config:138`

##### `from_env(cls) -> AuthConfig`

**Decoradores:** `classmethod`

**Documentación:**

```
Crea configuración desde variables de entorno.

Variables soportadas:
- PJN_LOGIN_URL: str

Returns:
    AuthConfig: Instancia con valores desde env o defaults.
```

**Ubicación:** `pjn.config:168`

##### `from_env(cls) -> ArchivosConfig`

**Decoradores:** `classmethod`

**Documentación:**

```
Crea configuración desde variables de entorno.

Variables soportadas:
- PJN_DIR_ACTUACIONES: str
- PJN_DIR_ENTRADAS: str

Returns:
    ArchivosConfig: Instancia con valores desde env o defaults.
```

**Ubicación:** `pjn.config:211`

##### `from_env(cls) -> Config`

**Decoradores:** `classmethod`

**Documentación:**

```
Crea configuración completa desde variables de entorno.

Returns:
    Config: Instancia con todos los sub-configs desde env.
```

**Ubicación:** `pjn.config:247`


#### `ScrapingConfig`

**Decoradores:** `dataclass`

**Descripción:** Configuraciones generales para scraping del portal PJN.

**Ubicación:** `pjn.config:24`

**Métodos públicos:**

##### `for_testing(cls) -> Config`

**Decoradores:** `classmethod`

**Documentación:**

```
Crea configuración optimizada para testing.

Returns:
    Config: Instancia con timeouts reducidos y límites bajos.
```

**Ubicación:** `pjn.config:261`

##### `from_env(cls) -> ScrapingConfig`

**Decoradores:** `classmethod`

**Documentación:**

```
Crea configuración desde variables de entorno.

Variables soportadas:
- PJN_MAX_PAGINAS: int
- PJN_TIMEOUT_DEFAULT: int (ms)
- PJN_TIMEOUT_LOGIN: int (ms)
- PJN_MAX_REINTENTOS_DESCARGA: int

Returns:
    ScrapingConfig: Instancia con valores desde env o defaults.
```

**Ubicación:** `pjn.config:87`

##### `from_env(cls) -> BrowserConfig`

**Decoradores:** `classmethod`

**Documentación:**

```
Crea configuración desde variables de entorno.

Variables soportadas:
- PJN_HEADLESS: 1/true/yes/y para True

Returns:
    BrowserConfig: Instancia con valores desde env o defaults.
```

**Ubicación:** `pjn.config:138`

##### `from_env(cls) -> AuthConfig`

**Decoradores:** `classmethod`

**Documentación:**

```
Crea configuración desde variables de entorno.

Variables soportadas:
- PJN_LOGIN_URL: str

Returns:
    AuthConfig: Instancia con valores desde env o defaults.
```

**Ubicación:** `pjn.config:168`

##### `from_env(cls) -> ArchivosConfig`

**Decoradores:** `classmethod`

**Documentación:**

```
Crea configuración desde variables de entorno.

Variables soportadas:
- PJN_DIR_ACTUACIONES: str
- PJN_DIR_ENTRADAS: str

Returns:
    ArchivosConfig: Instancia con valores desde env o defaults.
```

**Ubicación:** `pjn.config:211`

##### `from_env(cls) -> Config`

**Decoradores:** `classmethod`

**Documentación:**

```
Crea configuración completa desde variables de entorno.

Returns:
    Config: Instancia con todos los sub-configs desde env.
```

**Ubicación:** `pjn.config:247`


### Funciones Públicas

#### `get_config() -> Config`

**Documentación:**

```
Obtiene la instancia global de configuración (singleton lazy).

La primera llamada crea la instancia desde variables de entorno.
Llamadas subsecuentes retornan la misma instancia.

Returns:
    Config: Instancia global de configuración.

Example:
    >>> from pjn.config import get_config
    >>> config = get_config()
    >>> print(config.scraping.timeout_default)
    8000
```

**Ubicación:** `pjn.config:288`

#### `reset_config() -> None`

**Documentación:**

```
Resetea la configuración global (fuerza recarga en próxima llamada).

Útil principalmente para testing.
```

**Ubicación:** `pjn.config:325`

#### `set_config(config: Config) -> None`

**Documentación:**

```
Establece manualmente la configuración global.

Útil para testing o personalización avanzada.

Args:
    config: Instancia de Config a usar globalmente.

Example:
    >>> from pjn.config import set_config, Config
    >>> set_config(Config.for_testing())
```

**Ubicación:** `pjn.config:309`

---

## `pjn.exceptions`

### Clases

#### `ActuacionesNoDisponibles`

**Descripción:** No se pudieron extraer actuaciones del expediente.

**Ubicación:** `pjn.exceptions:48`

#### `ArchivoNoDisponible`

**Descripción:** El archivo solicitado no está disponible para descarga.

**Ubicación:** `pjn.exceptions:82`

#### `AutenticacionError`

**Descripción:** Error relacionado con autenticación en el portal PJN.

**Ubicación:** `pjn.exceptions:21`

#### `ConfiguracionError`

**Descripción:** Error en la configuración del sistema.

**Ubicación:** `pjn.exceptions:135`

#### `CredencialesFaltantes`

**Descripción:** Se lanza cuando no se encuentran credenciales para el portal.

**Ubicación:** `pjn.exceptions:26`

#### `DatosIncompletos`

**Descripción:** Faltan datos requeridos en la estructura.

**Ubicación:** `pjn.exceptions:70`

#### `DescargaError`

**Descripción:** Error durante la descarga de archivos.

**Ubicación:** `pjn.exceptions:77`

#### `DescargaFallida`

**Descripción:** La descarga del archivo falló después de todos los reintentos.

**Ubicación:** `pjn.exceptions:87`

#### `EstadoInvalido`

**Descripción:** El sistema está en un estado inválido para la operación solicitada.

**Ubicación:** `pjn.exceptions:140`

#### `ExpedienteNoEncontrado`

**Descripción:** El expediente solicitado no fue encontrado en el portal.

**Ubicación:** `pjn.exceptions:43`

#### `ExtraccionError`

**Descripción:** Error durante la extracción de datos del portal.

**Ubicación:** `pjn.exceptions:38`

#### `FormatoInvalido`

**Descripción:** Los datos no tienen el formato esperado.

**Ubicación:** `pjn.exceptions:65`

#### `PJNError`

**Descripción:** Excepción base para todos los errores del sistema PJN.

**Ubicación:** `pjn.exceptions:9`

#### `ParametroInvalido`

**Descripción:** Un parámetro recibido no es válido.

**Ubicación:** `pjn.exceptions:110`

#### `ParsingError`

**Descripción:** Error durante el procesamiento de datos extraídos.

**Ubicación:** `pjn.exceptions:60`

#### `SesionInvalida`

**Descripción:** Se lanza cuando no puede verificarse un login válido.

**Ubicación:** `pjn.exceptions:31`

#### `SistemaError`

**Descripción:** Error interno del sistema.

**Ubicación:** `pjn.exceptions:130`

#### `TimeoutExtraccion`

**Descripción:** Se agotó el tiempo de espera durante la extracción.

**Ubicación:** `pjn.exceptions:53`

#### `ValidacionError`

**Descripción:** Error de validación de datos de entrada.

**Ubicación:** `pjn.exceptions:105`

---

## `pjn.models._utils`

### Funciones Públicas

#### `coerce_bool(value: Any, default: bool = False) -> bool`

*Sin documentación*

**Ubicación:** `pjn.models._utils:39`

#### `coerce_int(value: Any, default: int | None = None) -> int | None`

*Sin documentación*

**Ubicación:** `pjn.models._utils:28`

#### `coerce_str(value: Any) -> str | None`

*Sin documentación*

**Ubicación:** `pjn.models._utils:17`

#### `get_first(mapping: Mapping[str, Any], *keys: str) -> Any`

**Documentación:**

```
Obtiene el primer valor disponible para las ``keys`` dadas.
```

**Ubicación:** `pjn.models._utils:8`

---

## `pjn.models.actuacion`

### Clases

#### `Actuacion`

**Decoradores:** `dataclass(slots=True)`

**Descripción:** Representa una actuación individual extraída del PJN.

**Ubicación:** `pjn.models.actuacion:11`

**Métodos públicos:**

##### `from_dict(cls, data: Mapping[str, Any]) -> 'Actuacion'`

**Decoradores:** `classmethod`

**Documentación:**

```
Construye una :class:`Actuacion` a partir de un diccionario.
```

**Ubicación:** `pjn.models.actuacion:31`

##### `to_dict(self) -> dict[str, Any]`

**Documentación:**

```
Serializa la actuación utilizando las claves históricas.
```

**Ubicación:** `pjn.models.actuacion:64`

##### `to_dict(self) -> dict[str, Any]`

**Documentación:**

```
Devuelve una estructura serializable compatible con versiones previas.
```

**Ubicación:** `pjn.models.actuacion:98`

##### `to_json_ready(self) -> dict[str, Any]`

**Documentación:**

```
Alias explícito de :meth:`to_dict` para compatibilidad con dumps.
```

**Ubicación:** `pjn.models.actuacion:85`


#### `ActuacionesArchivo`

**Decoradores:** `dataclass(slots=True)`

**Descripción:** Agrupa el encabezado y la colección de actuaciones para exportar JSON.

**Ubicación:** `pjn.models.actuacion:92`

**Métodos públicos:**

##### `from_dict(cls, data: Mapping[str, Any]) -> 'Actuacion'`

**Decoradores:** `classmethod`

**Documentación:**

```
Construye una :class:`Actuacion` a partir de un diccionario.
```

**Ubicación:** `pjn.models.actuacion:31`

##### `to_dict(self) -> dict[str, Any]`

**Documentación:**

```
Serializa la actuación utilizando las claves históricas.
```

**Ubicación:** `pjn.models.actuacion:64`

##### `to_dict(self) -> dict[str, Any]`

**Documentación:**

```
Devuelve una estructura serializable compatible con versiones previas.
```

**Ubicación:** `pjn.models.actuacion:98`

##### `to_json_ready(self) -> dict[str, Any]`

**Documentación:**

```
Alias explícito de :meth:`to_dict` para compatibilidad con dumps.
```

**Ubicación:** `pjn.models.actuacion:85`


---

## `pjn.models.entrada`

### Clases

#### `Entrada`

**Decoradores:** `dataclass(slots=True)`

**Descripción:** Evento de notificación o despacho registrado en el portal.

**Ubicación:** `pjn.models.entrada:11`

**Métodos públicos:**

##### `from_dict(cls, data: Mapping[str, Any]) -> 'Entrada'`

**Decoradores:** `classmethod`

*Sin documentación*

**Ubicación:** `pjn.models.entrada:23`

##### `to_dict(self) -> dict[str, Any]`

*Sin documentación*

**Ubicación:** `pjn.models.entrada:34`


---

## `pjn.models.expediente`

### Clases

#### `ExpedienteIdentificacion`

**Decoradores:** `dataclass(slots=True)`

**Descripción:** Datos mínimos para localizar un expediente puntual.

**Ubicación:** `pjn.models.expediente:44`

**Métodos públicos:**

##### `from_dict(cls, data: Mapping[str, Any]) -> 'ExpedienteResumen'`

**Decoradores:** `classmethod`

*Sin documentación*

**Ubicación:** `pjn.models.expediente:21`

##### `from_dict(cls, data: Mapping[str, Any]) -> 'ExpedienteIdentificacion'`

**Decoradores:** `classmethod`

*Sin documentación*

**Ubicación:** `pjn.models.expediente:51`

##### `to_dict(self) -> dict[str, Any]`

*Sin documentación*

**Ubicación:** `pjn.models.expediente:33`

##### `to_dict(self) -> dict[str, str]`

*Sin documentación*

**Ubicación:** `pjn.models.expediente:57`


#### `ExpedienteResumen`

**Decoradores:** `dataclass(slots=True)`

**Descripción:** Representa una fila del listado de expedientes.

**Ubicación:** `pjn.models.expediente:11`

**Métodos públicos:**

##### `from_dict(cls, data: Mapping[str, Any]) -> 'ExpedienteResumen'`

**Decoradores:** `classmethod`

*Sin documentación*

**Ubicación:** `pjn.models.expediente:21`

##### `from_dict(cls, data: Mapping[str, Any]) -> 'ExpedienteIdentificacion'`

**Decoradores:** `classmethod`

*Sin documentación*

**Ubicación:** `pjn.models.expediente:51`

##### `to_dict(self) -> dict[str, Any]`

*Sin documentación*

**Ubicación:** `pjn.models.expediente:33`

##### `to_dict(self) -> dict[str, str]`

*Sin documentación*

**Ubicación:** `pjn.models.expediente:57`


---

## `pjn.models.extraccion_config`

### Clases

#### `ExtraccionExpedientesConfig`

**Decoradores:** `dataclass`

**Descripción:** Configuración para extracción de expedientes.

**Ubicación:** `pjn.models.extraccion_config:20`

**Métodos públicos:**

##### `completo(cls) -> ExtraccionExpedientesConfig`

**Decoradores:** `classmethod`

**Documentación:**

```
Configuración para extracción completa (producción).

Returns:
    Configuración sin límites para extracción completa.

Example:
    >>> config = ExtraccionExpedientesConfig.completo()
    >>> config.max_paginas is None
    True
    >>> config.detener_en_duplicado
    False
```

**Ubicación:** `pjn.models.extraccion_config:128`

##### `con_fecha_corte(cls, fecha_corte: str, max_paginas: int = 100) -> ExtraccionExpedientesConfig`

**Decoradores:** `classmethod`

**Documentación:**

```
Configuración con fecha de corte específica.

Args:
    fecha_corte: Fecha de corte en formato YYYY-MM-DD o DD/MM/YYYY.
    max_paginas: Número máximo de páginas (default: 100).

Returns:
    Configuración con fecha de corte configurada.

Example:
    >>> config = ExtraccionExpedientesConfig.con_fecha_corte("2025-01-01")
    >>> config.fecha_corte
    '2025-01-01'
```

**Ubicación:** `pjn.models.extraccion_config:149`

##### `rapido(cls, max_paginas: int = 5) -> ExtraccionExpedientesConfig`

**Decoradores:** `classmethod`

**Documentación:**

```
Configuración para extracción rápida (testing/desarrollo).

Args:
    max_paginas: Número máximo de páginas (default: 5).

Returns:
    Configuración optimizada para extracción rápida.

Example:
    >>> config = ExtraccionExpedientesConfig.rapido()
    >>> config.max_paginas
    5
    >>> config.tiempo_maximo_segundos
    60
```

**Ubicación:** `pjn.models.extraccion_config:104`

##### `to_dict(self) -> dict`

**Documentación:**

```
Convierte la configuración a diccionario.

Returns:
    Diccionario con todos los parámetros de configuración.
```

**Ubicación:** `pjn.models.extraccion_config:171`


---

## `pjn.monitor.config`

### Clases

#### `MonitorConfig`

**Decoradores:** `dataclass`

**Descripción:** Configuración completa del monitor PJN.

**Ubicación:** `pjn.monitor.config:19`

**Métodos públicos:**

##### `from_env(cls) -> 'MonitorConfig'`

**Decoradores:** `classmethod`

**Documentación:**

```
Carga configuración desde variables de entorno.

Variables de entorno soportadas:
    MONITOR_MODO: Modo del monitor
    MONITOR_HEADLESS: Si ejecutar en modo headless (1/true/yes)
    MONITOR_INTERVALO_LAB_EXP: Intervalo laboral expedientes (minutos)
    MONITOR_INTERVALO_LAB_ENT: Intervalo laboral entradas (minutos)
    MONITOR_NOTIF_ENTRADAS: Notificar nuevas entradas (1/true/yes)
    MONITOR_NOTIF_EXPEDIENTES: Notificar cambios expedientes (1/true/yes)

Returns:
    MonitorConfig: Instancia con configuración desde env
```

**Ubicación:** `pjn.monitor.config:138`

##### `from_file(cls, path: str | Path = 'config/monitor.json') -> 'MonitorConfig'`

**Decoradores:** `classmethod`

**Documentación:**

```
Carga configuración desde archivo JSON.

Args:
    path: Ruta al archivo de configuración JSON

Returns:
    MonitorConfig: Instancia con configuración cargada

Raises:
    FileNotFoundError: Si el archivo no existe
    json.JSONDecodeError: Si el archivo JSON es inválido
```

**Ubicación:** `pjn.monitor.config:106`

##### `to_dict(self) -> dict`

**Documentación:**

```
Convierte la configuración a diccionario.

Returns:
    dict: Configuración como diccionario
```

**Ubicación:** `pjn.monitor.config:191`

##### `to_file(self, path: str | Path = 'config/monitor.json') -> None`

**Documentación:**

```
Guarda configuración a archivo JSON.

Args:
    path: Ruta donde guardar el archivo
```

**Ubicación:** `pjn.monitor.config:179`


---

## `pjn.monitor.core`

### Clases

#### `MonitorPJN`

**Descripción:** Motor principal del monitor de expedientes y entradas PJN.

**Ubicación:** `pjn.monitor.core:26`

**Métodos públicos:**

##### `detener(self) -> None`

**Documentación:**

```
Detiene el monitor.

Marca el flag running como False para que los loops se detengan.
```

**Ubicación:** `pjn.monitor.core:234`

##### `async verificar_entradas(self) -> list[Entrada]`

**Documentación:**

```
Verifica si hay nuevas entradas/notificaciones.

Este método:
1. Extrae las entradas actuales del portal
2. Las compara con las conocidas
3. Detecta las nuevas
4. Actualiza el historial
5. Envía notificación si corresponde

Returns:
    list[Entrada]: Lista de entradas nuevas detectadas

Raises:
    Exception: Si falla la extracción o hay error en la sesión
```

**Ubicación:** `pjn.monitor.core:49`

##### `async verificar_expedientes(self) -> list[ExpedienteResumen]`

**Documentación:**

```
Verifica si hay cambios en expedientes.

Este método:
1. Extrae los expedientes actuales
2. Los compara con los conocidos
3. Detecta expedientes con cambios en ultima_actuacion
4. Actualiza el historial
5. Envía notificación si corresponde

Returns:
    list[ExpedienteResumen]: Lista de expedientes con cambios

Raises:
    Exception: Si falla la extracción o hay error en la sesión
```

**Ubicación:** `pjn.monitor.core:134`


---

## `pjn.monitor.detector`

### Clases

#### `DetectorCambios`

**Descripción:** Detecta diferencias entre estados de entradas y expedientes.

**Ubicación:** `pjn.monitor.detector:14`

**Métodos públicos:**

##### `detectar_cambios_expedientes(self, actuales: list[ExpedienteResumen], anteriores: list[ExpedienteResumen]) -> list[ExpedienteResumen]`

**Documentación:**

```
Detecta expedientes con ultima_actuacion diferente.

Args:
    actuales: Expedientes actuales extraídos
    anteriores: Expedientes del estado anterior

Returns:
    list[ExpedienteResumen]: Expedientes con cambios en ultima_actuacion
```

**Ubicación:** `pjn.monitor.detector:49`

##### `detectar_nuevas_entradas(self, actuales: list[Entrada], conocidas: list[Entrada]) -> list[Entrada]`

**Documentación:**

```
Detecta entradas nuevas comparando con las conocidas.

Args:
    actuales: Entradas actuales extraídas
    conocidas: Entradas conocidas previamente

Returns:
    list[Entrada]: Entradas que no están en conocidas
```

**Ubicación:** `pjn.monitor.detector:17`


---

## `pjn.monitor.notifier`

### Clases

#### `NotificadorPlyer`

**Descripción:** Notificador multiplataforma usando plyer.

**Ubicación:** `pjn.monitor.notifier:14`

**Métodos públicos:**

##### `notificar(self, titulo: str, mensaje: str, timeout: int = 10) -> None`

**Documentación:**

```
Envía una notificación al sistema.

Args:
    titulo: Título de la notificación
    mensaje: Mensaje de la notificación
    timeout: Segundos que permanecerá visible (default: 10)
```

**Ubicación:** `pjn.monitor.notifier:37`


---

## `pjn.monitor.scheduler`

### Clases

#### `SchedulerMonitor`

**Descripción:** Gestiona scheduling inteligente del monitor.

**Ubicación:** `pjn.monitor.scheduler:36`

**Métodos públicos:**

##### `detener(self) -> None`

**Documentación:**

```
Detiene el scheduler y todos sus jobs.
```

**Ubicación:** `pjn.monitor.scheduler:273`

##### `async ejecutar_verificacion_inmediata(self) -> None`

**Documentación:**

```
Ejecuta una verificación inmediata de entradas y expedientes.

Útil para testing o para forzar una verificación manual.
```

**Ubicación:** `pjn.monitor.scheduler:282`

##### `iniciar(self) -> None`

**Documentación:**

```
Inicia el scheduler con los jobs programados.

Programa:
- Verificación de entradas con su intervalo correspondiente
- Verificación de expedientes con su intervalo correspondiente
```

**Ubicación:** `pjn.monitor.scheduler:189`


---

## `pjn.monitor.storage`

### Clases

#### `EstadoMonitor`

**Decoradores:** `dataclass`

**Descripción:** Estado persistente del monitor.

**Ubicación:** `pjn.monitor.storage:22`

**Métodos públicos:**

##### `cargar_entradas_conocidas(self) -> list[Entrada]`

**Documentación:**

```
Carga el historial de entradas conocidas.

Returns:
    list[Entrada]: Lista de entradas conocidas
```

**Ubicación:** `pjn.monitor.storage:120`

##### `cargar_estado(self) -> EstadoMonitor`

**Documentación:**

```
Carga el estado del monitor desde disco.

Returns:
    EstadoMonitor: Estado cargado o nuevo si no existe
```

**Ubicación:** `pjn.monitor.storage:87`

##### `cargar_expedientes_conocidos(self) -> list[ExpedienteResumen]`

**Documentación:**

```
Carga el historial de expedientes conocidos.

Returns:
    list[ExpedienteResumen]: Lista de expedientes conocidos
```

**Ubicación:** `pjn.monitor.storage:163`

##### `from_dict(cls, data: dict[str, Any]) -> 'EstadoMonitor'`

**Decoradores:** `classmethod`

**Documentación:**

```
Crea instancia desde diccionario.

Args:
    data: Diccionario con datos del estado

Returns:
    EstadoMonitor: Instancia creada
```

**Ubicación:** `pjn.monitor.storage:38`

##### `guardar_entradas(self, entradas: list[Entrada]) -> None`

**Documentación:**

```
Guarda el historial de entradas a disco.

Args:
    entradas: Lista de entradas a guardar
```

**Ubicación:** `pjn.monitor.storage:147`

##### `guardar_estado(self, estado: EstadoMonitor) -> None`

**Documentación:**

```
Guarda el estado del monitor a disco.

Args:
    estado: Estado a guardar
```

**Ubicación:** `pjn.monitor.storage:107`

##### `guardar_expedientes(self, expedientes: list[ExpedienteResumen]) -> None`

**Documentación:**

```
Guarda el historial de expedientes a disco.

Args:
    expedientes: Lista de expedientes a guardar
```

**Ubicación:** `pjn.monitor.storage:193`

##### `to_dict(self) -> dict[str, Any]`

**Documentación:**

```
Convierte a diccionario.

Returns:
    dict: Estado como diccionario
```

**Ubicación:** `pjn.monitor.storage:54`


#### `StorageManager`

**Descripción:** Gestiona la persistencia de datos del monitor.

**Ubicación:** `pjn.monitor.storage:63`

**Métodos públicos:**

##### `cargar_entradas_conocidas(self) -> list[Entrada]`

**Documentación:**

```
Carga el historial de entradas conocidas.

Returns:
    list[Entrada]: Lista de entradas conocidas
```

**Ubicación:** `pjn.monitor.storage:120`

##### `cargar_estado(self) -> EstadoMonitor`

**Documentación:**

```
Carga el estado del monitor desde disco.

Returns:
    EstadoMonitor: Estado cargado o nuevo si no existe
```

**Ubicación:** `pjn.monitor.storage:87`

##### `cargar_expedientes_conocidos(self) -> list[ExpedienteResumen]`

**Documentación:**

```
Carga el historial de expedientes conocidos.

Returns:
    list[ExpedienteResumen]: Lista de expedientes conocidos
```

**Ubicación:** `pjn.monitor.storage:163`

##### `from_dict(cls, data: dict[str, Any]) -> 'EstadoMonitor'`

**Decoradores:** `classmethod`

**Documentación:**

```
Crea instancia desde diccionario.

Args:
    data: Diccionario con datos del estado

Returns:
    EstadoMonitor: Instancia creada
```

**Ubicación:** `pjn.monitor.storage:38`

##### `guardar_entradas(self, entradas: list[Entrada]) -> None`

**Documentación:**

```
Guarda el historial de entradas a disco.

Args:
    entradas: Lista de entradas a guardar
```

**Ubicación:** `pjn.monitor.storage:147`

##### `guardar_estado(self, estado: EstadoMonitor) -> None`

**Documentación:**

```
Guarda el estado del monitor a disco.

Args:
    estado: Estado a guardar
```

**Ubicación:** `pjn.monitor.storage:107`

##### `guardar_expedientes(self, expedientes: list[ExpedienteResumen]) -> None`

**Documentación:**

```
Guarda el historial de expedientes a disco.

Args:
    expedientes: Lista de expedientes a guardar
```

**Ubicación:** `pjn.monitor.storage:193`

##### `to_dict(self) -> dict[str, Any]`

**Documentación:**

```
Convierte a diccionario.

Returns:
    dict: Estado como diccionario
```

**Ubicación:** `pjn.monitor.storage:54`


---

## `pjn.parsers.actuaciones_parser`

### Funciones Públicas

#### `construir_actuaciones_archivo(expediente_datos: Mapping[str, object], actuaciones_actuales: Sequence[Actuacion], actuaciones_historicas: Sequence[Actuacion]) -> ActuacionesArchivo`

*Sin documentación*

**Ubicación:** `pjn.parsers.actuaciones_parser:291`

#### `construir_encabezado_actuaciones(expediente_datos: Mapping[str, object], actuaciones_actuales: Sequence[Actuacion], actuaciones_historicas: Sequence[Actuacion]) -> dict[str, object]`

**Documentación:**

```
Compone el encabezado enriquecido para el archivo de actuaciones.
```

**Ubicación:** `pjn.parsers.actuaciones_parser:239`

#### `construir_nombre_archivo_normalizado(fecha: str | None, tipo: str | None, hash_val: str | None, archivo_url: str | None, nombre_descarga: str | None = None) -> tuple[str | None, str | None]`

**Documentación:**

```
Calcula el nombre de archivo y su extensión.
```

**Ubicación:** `pjn.parsers.actuaciones_parser:98`

#### `normalizar_nombre_expediente(expediente_datos: Mapping[str, object]) -> str`

*Sin documentación*

**Ubicación:** `pjn.parsers.actuaciones_parser:312`

#### `obtener_extension_valida(valor: str | None) -> str | None`

*Sin documentación*

**Ubicación:** `pjn.parsers.actuaciones_parser:83`

#### `async parse_actuacion_row(page_expediente: Page, fila: ElementHandle, indice: int, timestamp_extraccion: str) -> Actuacion | None`

**Documentación:**

```
Interpreta una fila HTML y devuelve una :class:`Actuacion`.
```

**Ubicación:** `pjn.parsers.actuaciones_parser:140`

### Funciones Privadas

- `_calcular_metricas_descargas(actuaciones: Iterable[Actuacion | Mapping[str, object]]) -> tuple[int, int, int]` (línea 203)

---

## `pjn.parsers.entradas_parser`

### Funciones Públicas

#### `deduplicar_historial(historial: Iterable[Entrada]) -> set[tuple[str, str, str, str | None]]`

**Documentación:**

```
Genera la clave base utilizada para detectar duplicados.
```

**Ubicación:** `pjn.parsers.entradas_parser:48`

#### `normalizar_fecha(valor: str | None) -> str | None`

*Sin documentación*

**Ubicación:** `pjn.parsers.entradas_parser:10`

#### `parse_entrada(numero: str, caratula: str, fecha: str, evento: str | None, tipo_evento: str | None) -> Entrada`

*Sin documentación*

**Ubicación:** `pjn.parsers.entradas_parser:26`

---

## `pjn.parsers.expedientes_parser`

### Funciones Públicas

#### `normalizar_fecha_actuacion(valor: str | None) -> str | None`

**Documentación:**

```
Normaliza fechas ``dd/mm/yyyy`` a ``YYYY-MM-DD`` si es posible.
```

**Ubicación:** `pjn.parsers.expedientes_parser:10`

#### `parse_expediente_resumen(valores: Sequence[str]) -> ExpedienteResumen | None`

**Documentación:**

```
Interpreta la fila plana del listado de expedientes.
```

**Ubicación:** `pjn.parsers.expedientes_parser:28`

---

## `pjn.persistence.actuaciones`

### Funciones Públicas

#### `actualizar_descargados(ruta_json: str | Path, actuaciones_actualizadas: list[Actuacion]) -> None`

**Documentación:**

```
Actualiza el estado de descarga de actuaciones en un JSON existente.

Args:
    ruta_json: Ruta al archivo JSON.
    actuaciones_actualizadas: Lista de actuaciones con estado actualizado.

Raises:
    FileNotFoundError: Si el archivo no existe.
```

**Ubicación:** `pjn.persistence.actuaciones:162`

#### `cargar_actuaciones_archivo(ruta_json: str | Path) -> ActuacionesArchivo`

**Documentación:**

```
Carga un archivo JSON y lo convierte a modelo ActuacionesArchivo.

Args:
    ruta_json: Ruta al archivo JSON.

Returns:
    ActuacionesArchivo: Modelo estructurado.

Raises:
    FileNotFoundError: Si el archivo no existe.
    json.JSONDecodeError: Si el archivo no es JSON válido.
```

**Ubicación:** `pjn.persistence.actuaciones:37`

#### `cargar_actuaciones_json(ruta_json: str | Path) -> dict[str, Any]`

**Documentación:**

```
Carga un archivo JSON de actuaciones desde disco.

Args:
    ruta_json: Ruta al archivo JSON.

Returns:
    dict: Estructura con "Expediente" y "Actuaciones".

Raises:
    FileNotFoundError: Si el archivo no existe.
    json.JSONDecodeError: Si el archivo no es JSON válido.
```

**Ubicación:** `pjn.persistence.actuaciones:20`

#### `extraer_actuaciones_con_archivos(archivo: ActuacionesArchivo) -> list[Actuacion]`

**Documentación:**

```
Filtra actuaciones que tienen archivos para descargar.

Args:
    archivo: Archivo de actuaciones.

Returns:
    list[Actuacion]: Lista de actuaciones con archivo != None.
```

**Ubicación:** `pjn.persistence.actuaciones:146`

#### `guardar_actuaciones_json(archivo: ActuacionesArchivo, directorio_base: str | Path | None = None, numero_expediente: str | None = None) -> str`

**Documentación:**

```
Guarda un ActuacionesArchivo como JSON en disco.

Args:
    archivo: Modelo de actuaciones a guardar.
    directorio_base: Carpeta base (default desde config).
    numero_expediente: Número de expediente para nombrar el archivo.
        Si no se proporciona, se extrae del encabezado.

Returns:
    str: Ruta absoluta al archivo guardado.

Raises:
    ValueError: Si no se puede determinar el número de expediente.
```

**Ubicación:** `pjn.persistence.actuaciones:73`

#### `listar_archivos_actuaciones(directorio_base: str | Path | None = None, patron: str = '*.json') -> list[Path]`

**Documentación:**

```
Lista todos los archivos de actuaciones en el directorio base.

Args:
    directorio_base: Carpeta base (default desde config).
    patron: Patrón glob para filtrar archivos.

Returns:
    list[Path]: Lista de rutas a archivos encontrados.
```

**Ubicación:** `pjn.persistence.actuaciones:122`

---

## `pjn.scraping.actuaciones`

### Funciones Públicas

#### `async actualizar_actuaciones_desde_json(page_expediente: Page, expediente_datos: dict, ruta_json_existente: str) -> tuple[int, dict | None, str | None]`

**Documentación:**

```
Actualiza un JSON existente incorporando solo las actuaciones nuevas.

Retorna una tupla con la cantidad de actuaciones agregadas, la estructura
actualizada (o ``None`` si hubo error) y un mensaje de error en caso de fallos.
```

**Ubicación:** `pjn.scraping.actuaciones:569`

#### `actualizar_metricas_descargas_en_json(payload: dict) -> None`

**Documentación:**

```
Recalcula los contadores de descargas dentro de la estructura JSON.

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
```

**Ubicación:** `pjn.scraping.actuaciones:84`

#### `async aviso_si_tarda(idx, segundos)`

*Sin documentación*

**Ubicación:** `pjn.scraping.actuaciones:1106`

#### `calcular_metricas_descargas_json(payload: dict) -> dict`

**Documentación:**

```
Recalcula los contadores de descargas y retorna una COPIA actualizada del payload.

Args:
    payload: Estructura JSON con Expediente y Actuaciones.

Returns:
    dict: Nueva copia del payload con métricas actualizadas.

Note:
    Esta función NO modifica el payload original (sin side effects).
```

**Ubicación:** `pjn.scraping.actuaciones:49`

#### `async construir_actuacion_desde_fila(page_expediente: Page, fila: ElementHandle, indice: int, timestamp_extraccion: str, es_historica: bool = False)`

*Sin documentación*

**Ubicación:** `pjn.scraping.actuaciones:239`

#### `async construir_actuacion_modelo_desde_fila(page_expediente: Page, fila: ElementHandle, indice: int, timestamp_extraccion: str) -> Actuacion | None`

**Documentación:**

```
Construye un modelo :class:`Actuacion` a partir de la fila HTML.
```

**Ubicación:** `pjn.scraping.actuaciones:220`

#### `construir_encabezado_actuaciones(expediente_datos: Mapping[str, object] | dict, actuaciones_actuales: Iterable[Actuacion | Mapping[str, object]], actuaciones_historicas: Iterable[Actuacion | Mapping[str, object]], incluye_historicas: bool, timestamp_generacion: str) -> dict[str, object]`

**Documentación:**

```
Genera los metadatos enriquecidos para el archivo JSON de actuaciones.
```

**Ubicación:** `pjn.scraping.actuaciones:131`

#### `async descargar_archivos_actuaciones(page: Page, actuaciones: list, carpeta_destino: str)`

**Documentación:**

```
Descarga archivos de actuaciones (versión con side effects).

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
```

**Ubicación:** `pjn.scraping.actuaciones:1220`

#### `async descargar_archivos_actuaciones_modelos(page: Page, actuaciones: list[Actuacion], carpeta_destino: str) -> list[Actuacion]`

**Documentación:**

```
Descarga archivos y retorna lista actualizada de actuaciones (sin side effects).

Args:
    page: Página de Playwright autenticada.
    actuaciones: Lista de modelos Actuacion.
    carpeta_destino: Carpeta donde guardar los archivos.

Returns:
    list[Actuacion]: Nueva lista con actuaciones actualizadas (marca descargado=True).

Note:
    Esta función NO modifica la lista original.
```

**Ubicación:** `pjn.scraping.actuaciones:1110`

#### `async descargar_archivos_de_json(page, carpeta_json: str, carpeta_adjuntos: str | None = None)`

**Documentación:**

```
Lee el archivo unificado desde la carpeta del expediente
y descarga los archivos vinculados usando Playwright.
Permite especificar una carpeta diferente para guardar los adjuntos;
si no se indica, reutiliza la carpeta de los JSON.
Marca las actuaciones descargadas como "Descargado": true.
```

**Ubicación:** `pjn.scraping.actuaciones:1362`

#### `async extraer_actuaciones_completas(page_expediente: Page, expediente_datos: dict, incluir_historicas: bool = True, directorio_base: str = 'ActuacionesCompletas') -> tuple[list[dict], list[dict], str | None]`

**Documentación:**

```
Extrae actuaciones y las guarda como JSON (versión con persistencia).

NOTA: Esta función mantiene compatibilidad con código existente.
Para uso desde otras rutinas, considere usar extraer_actuaciones_datos()
que no guarda archivos automáticamente.

Args:
    page_expediente: Página de Playwright con el expediente abierto.
    expediente_datos: Datos del expediente (número, carátula, etc.).
    incluir_historicas: Si True, incluye actuaciones históricas.
    directorio_base: Carpeta base donde guardar los archivos.

Returns:
    tuple: (actuaciones_actuales, actuaciones_historicas, error)
        - Si error es None, la extracción fue exitosa
        - Si error es str, contiene el mensaje de error

Deprecated:
    Esta función será deprecada en favor de extraer_actuaciones_datos()
    + guardar_actuaciones_json() por separado.
```

**Ubicación:** `pjn.scraping.actuaciones:1042`

#### `async extraer_actuaciones_datos(page_expediente: Page, expediente_datos: Mapping[str, object] | dict, incluir_historicas: bool = True) -> ActuacionesArchivo`

**Documentación:**

```
Extrae actuaciones actuales e históricas (opcional) y retorna modelo estructurado.

Esta versión refactorizada delega en funciones especializadas para mayor
claridad, testabilidad y mantenibilidad.

Esta es la versión "pura" que NO guarda archivos. Útil para:
- Procesamiento en memoria
- Integración con otras rutinas
- Testing

Args:
    page_expediente: Página de Playwright con el expediente abierto.
    expediente_datos: Datos del expediente (número, carátula, etc.).
    incluir_historicas: Si True, incluye actuaciones históricas.

Returns:
    ActuacionesArchivo: Modelo con encabezado y actuaciones.

Raises:
    ExtraccionError: Si falla la extracción de actuaciones.
    ActuacionesNoDisponibles: Si no hay actuaciones disponibles.
```

**Ubicación:** `pjn.scraping.actuaciones:968`

#### `async extraer_actuaciones_historicas(page_expediente, expediente_datos, indice_inicial = 1)`

*Sin documentación*

**Ubicación:** `pjn.scraping.actuaciones:256`

#### `async extraer_actuaciones_pagina(page_expediente, expediente_datos, indice_inicial = 1) -> tuple[list[dict], str | None]`

**Documentación:**

```
Extrae actuaciones de la página actual (versión deprecated con tuple).

DEPRECATED: Esta función mantiene el retorno tuple[result, error] por compatibilidad.
Para nuevo código, use extraer_actuaciones_pagina_modelos() que lanza excepciones.

Returns:
    tuple: (lista_actuaciones_dict, error_str_o_None)
```

**Ubicación:** `pjn.scraping.actuaciones:407`

#### `async extraer_actuaciones_pagina_modelos(page_expediente: Page, expediente_datos: Mapping[str, object] | dict, indice_inicial: int = 1) -> list[Actuacion]`

**Documentación:**

```
Extrae actuaciones de la página actual y retorna modelos Actuacion.

Args:
    page_expediente: Página de Playwright con el expediente abierto.
    expediente_datos: Datos del expediente.
    indice_inicial: Índice inicial para numerar actuaciones.

Returns:
    list[Actuacion]: Lista de modelos de actuaciones extraídas.

Raises:
    TimeoutExtraccion: Si no se encuentra la tabla en el tiempo esperado.
    ExtraccionError: Si hay errores durante la extracción.
```

**Ubicación:** `pjn.scraping.actuaciones:430`

#### `async obtener_actuaciones_todas_paginas_async(page_expediente, expediente_datos, carpeta_destino = 'Actuaciones')`

*Sin documentación*

**Ubicación:** `pjn.scraping.actuaciones:456`

#### `async obtener_actuaciones_todas_paginas_modelos_async(page_expediente: Page, expediente_datos: Mapping[str, object] | dict, carpeta_destino: str = 'Actuaciones') -> tuple[ActuacionesArchivo | None, str | None, str | None]`

**Documentación:**

```
Obtiene las actuaciones en formato de modelos dataclass.
```

**Ubicación:** `pjn.scraping.actuaciones:539`

### Funciones Privadas

- `async _esperar_cambio_pagina(page: Page, tabla_id: str, html_anterior: str, paginador_selector_js: str | None, pagina_anterior: str | None) -> None` (línea 179)
- `async _extraer_actuaciones_actuales(page: Page, expediente_datos: Mapping[str, object] | dict) -> list[Actuacion]` (línea 864)
- `async _extraer_actuaciones_historicas(page: Page, expediente_datos: Mapping[str, object] | dict, indice_base: int) -> list[Actuacion]` (línea 909)
- `async _extraer_actuaciones_pagina_generico(page_expediente: Page, expediente_datos: Mapping[str, object] | dict, indice_inicial: int, builder: ActuacionBuilder[TActuacion]) -> list[TActuacion]` (línea 343)
- `async _navegar_paginas_actuaciones(page: Page, tabla_id: str, expediente_datos: Mapping[str, object] | dict, indice_inicial: int = 1, es_historica: bool = False) -> list[Actuacion]` (línea 738)
- `async _obtener_paginador_activo(page: Page, tabla_id: str) -> tuple[str | None, str | None]` (línea 164)

---

## `pjn.scraping.actuaciones_utils`

### Funciones Públicas

#### `generar_hash_archivo(fecha: str | None, tipo: str | None, detalle: str | None, longitud: int = 6) -> str`

**Documentación:**

```
Genera un hash corto para identificar actuaciones con archivo adjunto.
```

**Ubicación:** `pjn.scraping.actuaciones_utils:38`

#### `limpiar_texto(texto: str | None) -> str`

**Documentación:**

```
Normaliza texto de celdas de actuaciones removiendo etiquetas iniciales.
```

**Ubicación:** `pjn.scraping.actuaciones_utils:14`

#### `normalizar_fecha(texto: str | None) -> str`

**Documentación:**

```
Adapta fechas dd/mm/YYYY al formato ISO, manteniendo valores originales.
```

**Ubicación:** `pjn.scraping.actuaciones_utils:23`

---

## `pjn.scraping.base`

### Funciones Públicas

#### `generar_hash_identificador(*componentes: object) -> str`

**Documentación:**

```
Genera un hash estable a partir de múltiples componentes.
```

**Ubicación:** `pjn.scraping.base:118`

#### `limpiar_texto(texto: str | None) -> str`

**Documentación:**

```
Elimina saltos de línea y espacios redundantes.

Devuelve una cadena vacía si ``texto`` es ``None``.
```

**Ubicación:** `pjn.scraping.base:52`

#### `normalizar_fecha(valor: str | date | datetime | None) -> str | None`

**Documentación:**

```
Convierte fechas comunes del PJN al formato deseado.

Si no puede interpretarse ``valor``, devuelve el texto original limpiado.
```

**Ubicación:** `pjn.scraping.base:76`

#### `normalizar_numero_expediente(valor: object) -> str`

**Documentación:**

```
Convierte un número de expediente en un nombre seguro para rutas.
```

**Ubicación:** `pjn.scraping.base:126`

#### `normalizar_texto(texto: str | None) -> str`

**Documentación:**

```
Normaliza el texto a minúsculas ASCII sin acentos.
```

**Ubicación:** `pjn.scraping.base:65`

#### `async obtener_pagina_autenticada() -> AsyncIterator[tuple[Page, BrowserContext, Browser]]`

**Decoradores:** `asynccontextmanager`

**Documentación:**

```
Devuelve una página autenticada reutilizando el *storage state* local.

Si el archivo de sesión no existe o resulta inválido se realiza un login
automático y se reintenta.
```

**Ubicación:** `pjn.scraping.base:258`

### Funciones Privadas

- `async _crear_contexto(playwright) -> tuple[Browser, BrowserContext]` (línea 162)
- `async _guardar_storage_state(context: BrowserContext, destino: Path) -> None` (línea 189)
- `_leer_storage_state(path: Path) -> dict | None` (línea 179)
- `_obtener_credenciales(usuario: str | None = None, contraseña: str | None = None) -> tuple[str, str]` (línea 145)
- `async _realizar_login(playwright) -> None` (línea 200)
- `async _verificar_sesion(page: Page) -> bool` (línea 236)

---

## `pjn.scraping.entradas`

### Clases

#### `ContadoresDiagnostico`

**Descripción:** Clase para mantener contadores de diagnóstico durante la extracción.

**Ubicación:** `pjn.scraping.entradas:211`

### Funciones Públicas

#### `async extraer_entradas_datos(page: Page, duplicados: bool = False, incluir_tipos: tuple[str, ...] = ('N', 'D'), fechas: Optional[Iterable[str]] = None, fecha_desde: Optional[str] = None, fecha_hasta: Optional[str] = None, historial_existente: Optional[List[Entrada]] = None) -> List[Entrada]`

**Documentación:**

```
Extrae entradas del PJN y retorna lista de modelos (NO guarda archivos).

Esta es la versión "pura" que NO persiste JSON/CSV. Útil para:
- Procesamiento en memoria
- Integración con otras rutinas
- Testing

Args:
    page: Playwright Page ya logueada y con la lista abierta.
    duplicados: False => dedup por (numero, fecha, caratula, evento).
                True => retorna todas las apariciones.
    incluir_tipos: ('N',), ('D',) o ('N','D') (default).
    fechas: fecha(s) exactas (YYYY-MM-DD o DD/MM/YYYY).
    fecha_desde / fecha_hasta: rango inclusivo (mismos formatos).
    historial_existente: Lista de entradas previas para deduplicación.

Returns:
    List[Entrada]: Lista de modelos de Entrada extraídos.

Raises:
    ExtraccionError: Si no se puede acceder al contenedor de entradas.
```

**Ubicación:** `pjn.scraping.entradas:433`

#### `async extraer_entradas_pjn(page: Page, destino: Optional[str] = None, duplicados: bool = False, incluir_tipos: tuple[str, ...] = ('N', 'D'), fechas: Optional[Iterable[str]] = None, fecha_desde: Optional[str] = None, fecha_hasta: Optional[str] = None, coleccion_modelos: Optional[List[Entrada]] = None) -> int`

**Documentación:**

```
Extrae entradas del PJN y persiste JSON/CSV (versión con persistencia).

NOTA: Esta función mantiene compatibilidad con código existente.
Para uso desde otras rutinas, considere usar extraer_entradas_datos()
que no guarda archivos automáticamente.

Args:
    page: Playwright Page ya logueada y con la lista abierta.
    destino: carpeta base (default ./datos_extraidos/monitoreo).
    duplicados: False => dedup por (numero, fecha, caratula, evento).
                True => guarda todas las apariciones.
    incluir_tipos: ('N',), ('D',) o ('N','D') (default).
    fechas: fecha(s) exactas (YYYY-MM-DD o DD/MM/YYYY).
    fecha_desde / fecha_hasta: rango inclusivo (mismos formatos).
    coleccion_modelos: Lista opcional para recibir modelos extraídos.

Returns:
    int: cantidad de registros NUEVOS agregados en esta corrida.

Deprecated:
    Esta función será deprecada en favor de extraer_entradas_datos()
    + funciones de persistencia separadas.
```

**Ubicación:** `pjn.scraping.entradas:596`

#### `async extraer_entradas_pjn_modelos(page: Page, destino: Optional[str] = None, duplicados: bool = False, incluir_tipos: tuple[str, ...] = ('N', 'D'), fechas: Optional[Iterable[str]] = None, fecha_desde: Optional[str] = None, fecha_hasta: Optional[str] = None) -> tuple[int, List[Entrada]]`

**Documentación:**

```
Extrae entradas con persistencia y devuelve modelos generados.

Deprecated:
    Usar extraer_entradas_datos() para obtener solo modelos sin persistencia.
```

**Ubicación:** `pjn.scraping.entradas:714`

### Funciones Privadas

- `_aplicar_deduplicacion(entrada_modelo: Entrada, historial_dicts: list[Dict[str, Any]], claves_hist_base: set[tuple], claves_hist_event: set[tuple], vistos_run_event: set[tuple]) -> bool` (línea 324)
- `_base_key(e: Dict[str, Any]) -> tuple` (línea 117)
- `async _configurar_pagina_scroll(page: Page) -> tuple` (línea 171)
- `async _detectar_indicador_evento(fila) -> Tuple[Optional[str], Optional[str]]` (línea 91)
- `async _ejecutar_scroll_y_esperar(page: Page, cont_locator, loading_loc, ultima_fila_prev: str, _ultima_fila_texto_fn) -> tuple[str, bool]` (línea 365)
- `_event_key(e: Dict[str, Any]) -> tuple` (línea 120)
- `_loguear_diagnostico(nuevas_entradas: List[Entrada], contadores: ContadoresDiagnostico) -> None` (línea 406)
- `async _near_bottom(page: Page, tol: int = 24) -> bool` (línea 59)
- `_parse_fecha_limite(f: Optional[str]) -> Optional[date]` (línea 55)
- `_parse_fechas_exactas(fechas: Optional[Iterable[str]]) -> set[str]` (línea 43)
- `_preparar_filtros_y_historial(fechas: Optional[Iterable[str]], fecha_desde: Optional[str], fecha_hasta: Optional[str], historial_existente: Optional[List[Entrada]]) -> tuple[set[str], Optional[date], Optional[date], list[Dict[str, Any]], set[tuple], set[tuple]]` (línea 126)
- `async _procesar_fila_entrada(fila, incluir_tipos: tuple[str, ...], fechas_exactas: set[str], rango_desde: Optional[date], rango_hasta: Optional[date], contadores: ContadoresDiagnostico) -> Optional[Entrada]` (línea 225)
- `async _scroll_step(page: Page)` (línea 71)
- `_to_iso(fecha_str: str) -> Optional[str]` (línea 31)
- `async _ultima_fila_texto() -> str` (línea 488)
- `async _wheel(page: Page, cont_locator)` (línea 79)

---

## `pjn.scraping.expedientes`

### Funciones Públicas

#### `async abrir_expediente_desde_fila(fila: ElementHandle | Locator | None, page: Page) -> dict[str, str] | None`

**Documentación:**

```
Abre el expediente asociado a ``fila`` y devuelve los datos extraídos.

Estas utilidades complementan a ``extraer_expedientes_completos`` y se
mantienen para compatibilidad con flujos que operan fila a fila.
```

**Ubicación:** `pjn.scraping.expedientes:733`

#### `async buscar_expediente_por_numero(page: Page, numero: str, anio: str, timeout: int = 8000) -> tuple[bool, str]`

*Sin documentación*

**Ubicación:** `pjn.scraping.expedientes:857`

#### `async buscar_expedientes(page: Page, numero: str | None = None, anio: str | None = None, caratula: str | None = None) -> list[ElementHandle]`

**Documentación:**

```
Busca expedientes en el portal PJN según los filtros indicados.
```

**Ubicación:** `pjn.scraping.expedientes:909`

#### `async buscar_expedientes_por_caratula(page: Page, caratula: str) -> list[ElementHandle]`

**Documentación:**

```
Realiza la búsqueda de expedientes utilizando sólo la carátula.
```

**Ubicación:** `pjn.scraping.expedientes:893`

#### `async extraer_datos_expediente(page: Page) -> dict[str, str] | None`

**Documentación:**

```
Extrae los campos principales del expediente actualmente abierto.
```

**Ubicación:** `pjn.scraping.expedientes:708`

#### `async extraer_expedientes_completos(page: Page, config: ExtraccionExpedientesConfig | None = None, sel_tabla: str | None = None, sel_tbody: str | None = None, sel_siguiente: str | None = None, max_paginas: int | None = None, omitir_duplicados: bool | None = None, detener_en_duplicado: bool | None = None) -> tuple[list[TResumen], str, dict[str, object]]`

**Documentación:**

```
Extrae TODAS las páginas del listado de expedientes.

Esta función soporta dos modos de uso:

1. **Modo moderno (recomendado)**: Usando objeto de configuración
    >>> config = ExtraccionExpedientesConfig.rapido()
    >>> expedientes, motivo, meta = await extraer_expedientes_completos(page, config)

2. **Modo legacy**: Pasando parámetros individuales (DEPRECATED)
    >>> expedientes, motivo, meta = await extraer_expedientes_completos(
    ...     page, max_paginas=10, omitir_duplicados=True
    ... )

Args:
    page: Página de Playwright ya posicionada sobre el listado.
    config: Objeto de configuración (recomendado). Si se proporciona, se ignoran
        los parámetros legacy.

    --- Parámetros legacy (DEPRECATED - usar config en su lugar) ---
    sel_tabla: Selector de la tabla principal (default: "table.table-striped").
    sel_tbody: Selector del tbody (default: "{sel_tabla} tbody").
    sel_siguiente: Selector del botón "Siguiente".
    max_paginas: Límite máximo de páginas a extraer.
    omitir_duplicados: Si omitir expedientes duplicados.
    detener_en_duplicado: Si detener al encontrar duplicado.
    tiempo_maximo_segundos: Límite máximo de duración del scraping.
    orden: Criterio de ordenamiento (fecha, caratula, oficina, situacion).
    mapper: Función para mapear ExpedienteResumen a otro tipo.
    pagination_strategy: Estrategia de paginación personalizada.

Returns:
    tuple[list[TResumen], str, dict[str, object]]: Tupla con:
        - expedientes: Lista de expedientes extraídos
        - motivo: Código de finalización ("fin_listado", "limite_paginas",
            "limite_fecha", "limite_tiempo", "duplicado_encontrado", etc.)
        - metadata: Información adicional (total_esperado, filas_descartadas, etc.)

Example:
    >>> # Modo moderno con config
    >>> config = ExtraccionExpedientesConfig.rapido()
    >>> expedientes, motivo, meta = await extraer_expedientes_completos(page, config)
    >>>
    >>> # Con fecha de corte
    >>> config = ExtraccionExpedientesConfig.con_fecha_corte("2025-01-01")
    >>> expedientes, motivo, meta = await extraer_expedientes_completos(page, config)
```

**Ubicación:** `pjn.scraping.expedientes:443`

#### `async extraer_expedientes_completos_modelos(page: Page, sel_tabla: str = SEL_TABLA, sel_tbody: str = SEL_TBODY, sel_siguiente: str = SEL_SIGUIENTE, max_paginas: int | None = None, omitir_duplicados: bool = True, detener_en_duplicado: bool = True) -> tuple[list[ExpedienteResumen], str, dict[str, object]]`

**Documentación:**

```
Versión que devuelve :class:`ExpedienteResumen` en lugar de dicts.

Args:
    Ver documentación de :func:`extraer_expedientes_completos`.

Returns:
    tuple[list[ExpedienteResumen], str, dict]: Lista de modelos ExpedienteResumen,
    motivo de finalización y metadata.
```

**Ubicación:** `pjn.scraping.expedientes:665`

#### `async mostrar_y_elegir_expediente(page: Page, filas: list[ElementHandle | Locator]) -> dict[str, str] | None`

**Documentación:**

```
Muestra las filas encontradas y abre la opción seleccionada.
```

**Ubicación:** `pjn.scraping.expedientes:772`

### Funciones Privadas

- `async _aplicar_ordenamiento_tabla(page: Page, tabla: Locator, orden: str | None) -> None` (línea 314)
- `_build_fingerprint(html: str, max_len: int | None = _FP_MAX_LEN) -> str` (línea 109)
- `_excedio_tiempo() -> bool` (línea 570)
- `async _extraer_total_esperado(page: Page) -> int | None` (línea 356)
- `_finalizar(motivo: str) -> tuple[list[dict], str, dict[str, object]]` (línea 557)
- `async _is_locator_enabled(locator: Locator) -> bool` (línea 129)
- `async _navegar_siguiente_pagina(page: Page, tbody_locator: Locator, sel_siguiente: str, fingerprint_actual: str, estrategia: PaginationStrategy | None = None) -> tuple[bool, str | None]` (línea 174)
- `_norm_fecha(s: str) -> str` (línea 92)
- `_parsear_fecha_corte(fecha_corte: str | None) -> datetime | None` (línea 63)
- `_procesar_expediente_resumen(resumen: ExpedienteResumen, fecha_corte_dt: datetime | None, huellas: set[tuple[str, str, str]], omitir_duplicados: bool, detener_en_duplicado: bool) -> tuple[bool, bool, bool]` (línea 260)
- `_procesar_filas_pagina(filas: list[list[str]], fecha_corte_dt: datetime | None, huellas: set[tuple[str, str, str]], omitir_duplicados: bool, detener_en_duplicado: bool, resumen_mapper: Callable[[ExpedienteResumen], TResumen]) -> tuple[list[TResumen], int, int, str | None]` (línea 384)
- `_resolver_valor_orden(orden: str | None) -> str | None` (línea 87)
- `_seleccionar_primera_opcion(opciones: list[dict[str, str]]) -> int | None` (línea 766)
- `async _tbody_fingerprint(tbody: Locator | ElementHandle) -> str` (línea 161)

---

## `pjn.scraping.pagination`

### Clases

#### `PaginationStrategy`

**Decoradores:** `runtime_checkable`

**Descripción:** Protocol para estrategias de paginación en portales web.

**Ubicación:** `pjn.scraping.pagination:17`

**Métodos públicos:**

##### `async navegar_siguiente(self, page: Page, tbody_locator: Locator, fingerprint_actual: str) -> tuple[bool, str | None]`

**Documentación:**

```
Navega a la siguiente página y verifica el cambio de contenido.

Args:
    page: Página de Playwright.
    tbody_locator: Locator del tbody para verificar cambios.
    fingerprint_actual: Fingerprint del contenido antes de la navegación.

Returns:
    tuple[exito, motivo_fallo]:
        - exito: True si navegó correctamente y cambió el contenido.
        - motivo_fallo: Código de error si falló, None si tuvo éxito.

Códigos de error comunes:
    - "sin_siguiente": No existe botón siguiente.
    - "sin_siguiente_habilitado": Botón siguiente deshabilitado.
    - "siguiente_timeout": Timeout esperando botón.
    - "siguiente_deshabilitado": Botón se deshabilitó al hacer clic.
    - "error_click": Error al hacer clic.
    - "fin_listado": No cambió contenido (fin natural).
```

**Ubicación:** `pjn.scraping.pagination:24`

##### `async navegar_siguiente(self, page: Page, tbody_locator: Locator, fingerprint_actual: str) -> tuple[bool, str | None]`

**Documentación:**

```
Navega a la siguiente página usando controles PrimeFaces.

Args:
    page: Página de Playwright.
    tbody_locator: Locator del tbody para verificar cambios.
    fingerprint_actual: Fingerprint del tbody antes de hacer clic.

Returns:
    tuple[exito, motivo_fallo]:
        - exito: True si navegó correctamente y cambió el contenido.
        - motivo_fallo: Código de error si falló, None si tuvo éxito.
```

**Ubicación:** `pjn.scraping.pagination:99`


#### `PrimeFacesPaginationStrategy`

**Descripción:** Estrategia de paginación para portales que usan PrimeFaces.

**Ubicación:** `pjn.scraping.pagination:53`

**Métodos públicos:**

##### `async navegar_siguiente(self, page: Page, tbody_locator: Locator, fingerprint_actual: str) -> tuple[bool, str | None]`

**Documentación:**

```
Navega a la siguiente página y verifica el cambio de contenido.

Args:
    page: Página de Playwright.
    tbody_locator: Locator del tbody para verificar cambios.
    fingerprint_actual: Fingerprint del contenido antes de la navegación.

Returns:
    tuple[exito, motivo_fallo]:
        - exito: True si navegó correctamente y cambió el contenido.
        - motivo_fallo: Código de error si falló, None si tuvo éxito.

Códigos de error comunes:
    - "sin_siguiente": No existe botón siguiente.
    - "sin_siguiente_habilitado": Botón siguiente deshabilitado.
    - "siguiente_timeout": Timeout esperando botón.
    - "siguiente_deshabilitado": Botón se deshabilitó al hacer clic.
    - "error_click": Error al hacer clic.
    - "fin_listado": No cambió contenido (fin natural).
```

**Ubicación:** `pjn.scraping.pagination:24`

##### `async navegar_siguiente(self, page: Page, tbody_locator: Locator, fingerprint_actual: str) -> tuple[bool, str | None]`

**Documentación:**

```
Navega a la siguiente página usando controles PrimeFaces.

Args:
    page: Página de Playwright.
    tbody_locator: Locator del tbody para verificar cambios.
    fingerprint_actual: Fingerprint del tbody antes de hacer clic.

Returns:
    tuple[exito, motivo_fallo]:
        - exito: True si navegó correctamente y cambió el contenido.
        - motivo_fallo: Código de error si falló, None si tuvo éxito.
```

**Ubicación:** `pjn.scraping.pagination:99`


---

## `pjn.scripts.diagnostico_entradas`

### Funciones Públicas

#### `async main() -> None`

**Documentación:**

```
Ejecutar diagnóstico de selectores.
```

**Ubicación:** `pjn.scripts.diagnostico_entradas:23`

---

## `pjn.scripts.prueba_extractor_entradas`

### Funciones Públicas

#### `async main() -> None`

**Documentación:**

```
Función principal de prueba del extractor de entradas.
```

**Ubicación:** `pjn.scripts.prueba_extractor_entradas:39`

---

## `pjn.scripts.rf_test_extraccion_completa`

### Funciones Públicas

#### `async main() -> None`

*Sin documentación*

**Ubicación:** `pjn.scripts.rf_test_extraccion_completa:121`

#### `seleccionar_por_consola(opciones: list[dict[str, str]]) -> int | None`

**Documentación:**

```
Estrategia interactiva basada en la entrada del usuario por consola.
```

**Ubicación:** `pjn.scripts.rf_test_extraccion_completa:39`

### Funciones Privadas

- `async _buscar_y_seleccionar_expediente(page: Page) -> dict[str, Any] | None` (línea 79)
- `async _extraer_actuaciones(page: Page, datos_expediente: dict[str, Any]) -> None` (línea 97)
- `_leer_dato(prompt: str) -> str` (línea 75)
- `async _mostrar_credenciales_vacias(page: Page) -> bool` (línea 63)

---

## `pjn.selectores`

### Clases

#### `ActuacionesSelectores`

**Decoradores:** `dataclass(frozen=True)`

**Descripción:** Selectores para actuaciones actuales e históricas (PrimeFaces).

**Ubicación:** `pjn.selectores:85`

#### `AutenticacionSelectores`

**Decoradores:** `dataclass(frozen=True)`

**Descripción:** Selectores para login en Keycloak.

**Ubicación:** `pjn.selectores:17`

#### `EntradasSelectores`

**Decoradores:** `dataclass(frozen=True)`

**Descripción:** Selectores para bandeja de entradas/notificaciones (Material UI).

**Ubicación:** `pjn.selectores:30`

#### `ExpedientesSelectores`

**Decoradores:** `dataclass(frozen=True)`

**Descripción:** Selectores para búsqueda y listado de expedientes.

**Ubicación:** `pjn.selectores:60`

### Funciones Públicas

#### `escapar_id_jsf_para_css(id_jsf: str) -> str`

**Documentación:**

```
Escapa dos puntos de IDs JSF para usar en CSS con querySelector.

Los IDs JSF usan el formato 'formulario:componente:subcomponente'.
Para usarlos en selectores CSS necesitan escaparse los dos puntos.

NOTA: Esta función NO agrega el prefijo '#'. Si necesitas un selector
completo con '#', agrégalo manualmente: f"#{escapar_id_jsf_para_css(id)}"

Args:
    id_jsf: ID JSF sin formato (ej: 'expediente:action-table')

Returns:
    ID escapado SIN '#' (ej: 'expediente\:action-table')

Example:
    >>> escapar_id_jsf_para_css("expediente:action-table")
    'expediente\:action-table'
    >>> f"#{escapar_id_jsf_para_css('expediente:action-table')}"
    '#expediente\:action-table'
```

**Ubicación:** `pjn.selectores:128`

#### `escapar_id_jsf_para_js(id_jsf: str) -> str`

**Documentación:**

```
Escapa dos puntos de IDs JSF para usar en JavaScript/evaluate.

Similar a escapar_id_jsf_para_css pero con escape doble para JS.

Args:
    id_jsf: ID JSF sin formato

Returns:
    ID escapado para JS (ej: 'expediente\\:action-table')

Example:
    >>> escapar_id_jsf_para_js("expediente:action-table")
    'expediente\\:action-table'
```

**Ubicación:** `pjn.selectores:152`

---

## `pjn.utils.logging`

### Clases

#### `ColoredFormatter`

**Descripción:** Formatter que agrega colores ANSI a los niveles de log.

**Ubicación:** `pjn.utils.logging:43`

**Métodos públicos:**

##### `emit(self, record)`

*Sin documentación*

**Ubicación:** `pjn.utils.logging:25`

##### `format(self, record: logging.LogRecord) -> str`

*Sin documentación*

**Ubicación:** `pjn.utils.logging:67`


#### `SafeStreamHandler`

**Descripción:** StreamHandler que maneja errores de encoding en Windows.

**Ubicación:** `pjn.utils.logging:22`

**Métodos públicos:**

##### `emit(self, record)`

*Sin documentación*

**Ubicación:** `pjn.utils.logging:25`

##### `format(self, record: logging.LogRecord) -> str`

*Sin documentación*

**Ubicación:** `pjn.utils.logging:67`


### Funciones Públicas

#### `configure_from_env() -> None`

**Documentación:**

```
Configura logging desde variables de entorno.

Variables soportadas:
    LOG_LEVEL: Nivel de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    LOG_FILE: Ruta al archivo de log
    LOG_COLORS: Si usar colores (true/false, 1/0)

Example:
    >>> export LOG_LEVEL=DEBUG
    >>> export LOG_FILE=logs/sistema_v5.log
    >>> python script.py
```

**Ubicación:** `pjn.utils.logging:173`

#### `get_logger(name: str | None = None) -> logging.Logger`

**Documentación:**

```
Obtiene un logger configurado para el módulo especificado.

Args:
    name: Nombre del módulo (usa __name__ del módulo que llama)

Returns:
    Logger configurado

Example:
    >>> logger = get_logger(__name__)
    >>> logger.info("📄 Iniciando proceso...")
    >>> logger.debug("Variable x = %s", x)
```

**Ubicación:** `pjn.utils.logging:148`

#### `setup_logging(level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] | int = 'INFO', log_file: str | Path | None = None, use_colors: bool = True, file_level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] | int = 'DEBUG') -> None`

**Documentación:**

```
Configura el sistema de logging global para toda la aplicación.

Args:
    level: Nivel de logging para consola (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    log_file: Ruta al archivo donde guardar logs (opcional)
    use_colors: Si usar colores en la consola
    file_level: Nivel de logging para archivo (por defecto DEBUG para guardar todo)

Example:
    >>> setup_logging("INFO")  # Solo INFO y superiores en consola
    >>> setup_logging("DEBUG", log_file="debug.log")  # DEBUG en archivo
    >>> setup_logging("ERROR")  # Solo errores en consola
```

**Ubicación:** `pjn.utils.logging:81`

---

## 📊 Estadísticas

- **Módulos totales:** 28
- **Clases:** 46
- **Funciones públicas:** 70
- **Funciones privadas:** 47
- **Funciones async:** 65
- **Total items:** 163
