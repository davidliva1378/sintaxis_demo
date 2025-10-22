# Documentación Completa - Sistema Expedientes v4

## Tabla de Contenidos
1. [Introducción](#introducción)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Componentes Principales](#componentes-principales)
4. [Módulo expedientes_v4.py](#módulo-expedientes_v4py)
5. [Monitor de Expedientes](#monitor-de-expedientes)
6. [Configuración y Parámetros](#configuración-y-parámetros)
7. [Funcionalidades Principales](#funcionalidades-principales)
8. [Ejemplos de Uso](#ejemplos-de-uso)
9. [Manejo de Errores](#manejo-de-errores)
10. [Migración desde v3](#migración-desde-v3)
11. [Estructura de Datos](#estructura-de-datos)
12. [API Reference](#api-reference)

---

## Introducción

El Sistema Expedientes v4 es una evolución del sistema de extracción y monitoreo de expedientes del Poder Judicial de la Nación (PJN). Esta versión introduce mejoras significativas en:

- **Arquitectura modular**: Organización mejorada con separación clara de responsabilidades
- **Compatibilidad con versiones anteriores**: Soporte temporal para Sistema_v3 durante la migración
- **Monitoreo automatizado**: Sistema de bandeja con verificación periódica
- **Extracción robusta**: Manejo avanzado de errores y detección de duplicados
- **Configuración flexible**: Parámetros ajustables para diferentes escenarios de uso

---

## Arquitectura del Sistema

### Estructura de Directorios

```
Sistema_v4/
├── __init__.py
├── config/
│   └── __init__.py
├── monitor/
│   ├── __init__.py
│   └── monitor_entradas_expedientes_v4.py
├── operaciones/
│   ├── __init__.py
│   └── expedientes/
│       ├── __init__.py
│       ├── README.md
│       └── expedientes_v4.py
├── utils/
│   └── __init__.py
└── web/
    └── __init__.py
```

### Árbol de archivos generado para cada expediente

La utilidad de gestión de directorios crea un árbol base para cada expediente que almacena los datos descargados. La estructura actual incluye una carpeta dedicada para documentos cargados manualmente por el equipo:

```
<expediente>/
├── actuaciones/
│   └── adjuntos/
├── json/
├── documentos_usuario/
└── reportes/
```

La carpeta `documentos_usuario` queda disponible para almacenar escritos o archivos complementarios agregados por la mesa de trabajo que no provienen del portal del PJN, manteniéndolos separados de las actuaciones oficiales.

> 💡 Además del árbol base anterior, suele resultar útil preparar directorios opcionales como `documentos_firmados/` (para versiones selladas o con firma digital) o `tmp/` (para insumos intermedios compartidos con procesos externos). El módulo `Sistema_v5.gestor_directorios` permite incorporarlos dinámicamente usando `GestorDirectoriosExpedientes.actualizar_estructura` o pasando un diccionario personalizado en `generar_arbol`.

### Principios de Diseño

1. **Separación de Responsabilidades**: Cada módulo tiene una función específica
2. **Compatibilidad hacia atrás**: Importaciones condicionales para mantener compatibilidad con v3
3. **Modularidad**: Componentes independientes que pueden ser utilizados por separado
4. **Robustez**: Manejo exhaustivo de errores y casos edge

---

## Componentes Principales

### 1. Extractor de Expedientes (`expedientes_v4.py`)
- **Ubicación**: `Sistema_v4/operaciones/expedientes/expedientes_v4.py`
- **Función**: Extracción completa de expedientes con paginación automática
- **Tecnología**: Playwright para automatización web

### 2. Monitor de Sistema (`monitor_entradas_expedientes_v4.py`)
- **Ubicación**: `Sistema_v4/monitor/monitor_entradas_expedientes_v4.py`
- **Función**: Aplicación de bandeja del sistema para monitoreo automático
- **Tecnología**: PySide6 para interfaz gráfica

---

## Módulo expedientes_v4.py

### Función Principal

#### `extraer_expedientes_completos()`

**Ubicación**: `Sistema_v4/operaciones/expedientes/expedientes_v4.py:121`

```python
async def extraer_expedientes_completos(
    page: Page,
    sel_tabla: str = SEL_TABLA,
    sel_tbody: str = SEL_TBODY,
    sel_siguiente: str = SEL_SIGUIENTE,
    max_paginas: int = 200,
    omitir_duplicados: bool = True,
    detener_en_duplicado: bool = True,
    *,
    fecha_corte: str | None = None,
    tiempo_maximo_segundos: int | None = None,
    orden: str | None = None,
) -> tuple[list[dict], str, dict[str, object]]:
```

### Parámetros de Entrada

| Parámetro | Tipo | Descripción | Valor por defecto |
|-----------|------|-------------|-------------------|
| `page` | `Page` | Instancia de página de Playwright | **Requerido** |
| `sel_tabla` | `str` | Selector CSS de la tabla de expedientes | `"table.table-striped"` |
| `sel_tbody` | `str` | Selector CSS del contenedor de filas (usado como `${sel_tbody} tr`) | `SEL_TBODY` |
| `sel_siguiente` | `str` | Selector del botón "Siguiente" | Múltiples selectores |
| `max_paginas` | `int` | Máximo número de páginas a procesar | `200` |
| `omitir_duplicados` | `bool` | Evitar agregar expedientes duplicados | `True` |
| `detener_en_duplicado` | `bool` | Parar extracción al encontrar duplicado | `True` |
| `fecha_corte` | `str \| None` | Fecha mínima en formato YYYY-MM-DD o DD/MM/AAAA | `None` |
| `tiempo_maximo_segundos` | `int \| None` | Límite de tiempo de ejecución | `None` |
| `orden` | `str \| None` | Criterio de ordenamiento | `None` |

### Valores de Retorno

La función retorna una tupla `(expedientes, motivo, metadata)`:

- **expedientes**: Lista de diccionarios con datos de expedientes.
- **motivo**: Código que indica por qué se detuvo la extracción.
- **metadata**: Diccionario con metadatos adicionales. Incluye la clave opcional `"total_esperado"` cuando el portal anuncia la cantidad total de expedientes publicados.

#### Códigos de Motivo

| Código | Descripción |
|--------|-------------|
| `"fin_listado"` | Se alcanzó el final natural del paginado |
| `"limite_paginas"` | Se alcanzó el límite de páginas configurado |
| `"limite_fecha"` | Se superó la fecha de corte especificada |
| `"limite_tiempo"` | Se superó el tiempo máximo de ejecución |
| `"sin_siguiente"` | No existe control para pasar de página |
| `"sin_siguiente_habilitado"` | No hay botón "Siguiente" habilitado |
| `"siguiente_timeout"` | El botón "Siguiente" no apareció a tiempo |
| `"siguiente_deshabilitado"` | El botón se deshabilitó al intentar usarlo |
| `"error_click"` | Falló el clic en "Siguiente" |
| `"duplicado_encontrado"` | Se detectó un expediente repetido |

### Funciones Auxiliares

#### `_norm_fecha(s: str) -> str`
**Ubicación**: `Sistema_v4/operaciones/expedientes/expedientes_v4.py:45`

Convierte fechas en formato DD/MM/YYYY a YYYY-MM-DD.

#### `_build_fingerprint(html: str, max_len: int | None = 4096) -> str`
**Ubicación**: `Sistema_v4/operaciones/expedientes/expedientes_v4.py:62`

Crea una huella digital del contenido HTML para detectar cambios de página.

#### `_is_locator_enabled(locator: Locator) -> bool`
**Ubicación**: `Sistema_v4/operaciones/expedientes/expedientes_v4.py:79`

Determina si un elemento está habilitado para interacción.

#### `_resolver_valor_orden(orden: str | None) -> str | None`
**Ubicación**: `Sistema_v4/operaciones/expedientes/expedientes_v4.py:40`

Convierte valores de ordenamiento legibles a códigos del sistema.

### Selectores Configurables

```python
# Selector principal de tabla
SEL_TABLA = "table.table-striped"

# Selector del contenedor de filas dentro de la tabla
SEL_TBODY = f"{SEL_TABLA} tbody"

# Múltiples selectores para botón "Siguiente"
SEL_SIGUIENTE = ", ".join([
    "a[aria-label='Siguiente']",
    "button[aria-label='Siguiente']",
    "a:has(span[title='Siguiente'])",
    "button:has(span[title='Siguiente'])",
    ".pagination li.next:not(.disabled) a",
    ".pagination a:has-text('Siguiente')",
    ".rf-ds-btn-next",
])
```

---

## Monitor de Expedientes

### Clase Principal: `MonitorExpedientesTray`

**Ubicación**: `Sistema_v4/monitor/monitor_entradas_expedientes_v4.py:134`

Aplicación de bandeja del sistema que proporciona monitoreo automatizado de expedientes.

### Características

- **Icono en bandeja del sistema**: Interfaz no intrusiva
- **Verificación automática**: Basada en horarios configurables
- **Notificaciones**: Alertas cuando se detectan cambios
- **Configuración flexible**: Modos automático, laboral y no laboral

### Configuración por Defecto

```python
DEFAULT_CONFIG = {
    "modo": "automatico",
    "horario_laboral": {
        "dias": ["lunes", "martes", "miércoles", "jueves", "viernes"],
        "hora_inicio": "07:00",
        "hora_fin": "20:00",
        "intervalo_minutos": 30,
    },
    "fuera_horario": {"intervalo_minutos": 240},
}
```

### Modos de Operación

1. **Automático**: Ajusta el intervalo según el horario laboral
2. **Laboral**: Usa siempre el intervalo de horario laboral
3. **No laboral**: Usa siempre el intervalo fuera de horario

### Clase `VerificadorExpedientesV4`

**Ubicación**: `Sistema_v4/monitor/monitor_entradas_expedientes_v4.py:76`

Hilo separado que ejecuta la extracción de expedientes sin bloquear la interfaz.

#### Características:

- **Ejecución asíncrona**: No bloquea la interfaz de usuario
- **Guardado automático**: Resultados en formato JSON
- **Manejo de errores**: Captura y reporta excepciones
- **Señales Qt**: Comunicación thread-safe con la interfaz
- **Omisión de duplicados**: Invoca al scraper con `detener_en_duplicado=False` para continuar paginando aunque aparezcan expedientes repetidos.

---

## Configuración y Parámetros

### Archivo de Configuración

**Ubicación**: `config/config_monitor.json`

```json
{
  "modo": "automatico",
  "horario_laboral": {
    "dias": ["lunes", "martes", "miércoles", "jueves", "viernes"],
    "hora_inicio": "07:00",
    "hora_fin": "20:00",
    "intervalo_minutos": 30
  },
  "fuera_horario": {
    "intervalo_minutos": 240
  }
}
```

### Parámetros de Ordenamiento

| Valor | Código Sistema | Descripción |
|-------|----------------|-------------|
| `"fecha"` | `"FECHA"` | Ordenar por fecha de última actuación |
| `"caratula"` | `"CARATULA"` | Ordenar por carátula del expediente |
| `"oficina"` | `"OFICINA"` | Ordenar por oficina/dependencia |
| `"situacion"` | `"SITUACION"` | Ordenar por situación del expediente |

---

## Funcionalidades Principales

### 1. Extracción Completa de Expedientes

- **Paginación automática**: Navega por todas las páginas disponibles
- **Detección de duplicados**: Evita procesar expedientes repetidos
- **Filtrado por fecha**: Permite establecer una fecha de corte
- **Ordenamiento**: Reorganiza los resultados según criterios específicos
- **Timeout configurable**: Límites de tiempo para evitar ejecuciones indefinidas

### 2. Monitoreo Automático

- **Verificación periódica**: Ejecuta extracciones según horarios configurados
- **Notificaciones del sistema**: Informa sobre nuevos expedientes
- **Persistencia de datos**: Guarda resultados en archivos JSON
- **Reintentos automáticos**: Reintenta operaciones fallidas hasta 5 veces

### 3. Gestión de Sesiones

- **Reutilización de sesiones**: Mantiene sesiones activas para eficiencia
- **Login automático**: Maneja autenticación de forma transparente
- **Manejo de errores de conexión**: Recuperación automática de fallos

---

## Ejemplos de Uso

### Extracción Básica

```python
from Sistema_v4.operaciones.expedientes.expedientes_v4 import extraer_expedientes_completos
from Sistema_v4.web.auto_login import reutilizar_sesion_async
from Sistema_v4.config.urls_pjn import URL_CONSULTAS

async def ejemplo_basico():
    async with reutilizar_sesion_async() as (page, context, browser):
        await page.goto(URL_CONSULTAS)
        expedientes, motivo, metadata = await extraer_expedientes_completos(page)
        print(f"Extraídos {len(expedientes)} expedientes. Motivo: {motivo}")
        return expedientes
```

### Extracción con Parámetros Avanzados

```python
async def ejemplo_avanzado():
    async with reutilizar_sesion_async() as (page, context, browser):
        await page.goto(URL_CONSULTAS)

        expedientes, motivo, metadata = await extraer_expedientes_completos(
            page,
            max_paginas=50,
            fecha_corte="2024-01-01",
            tiempo_maximo_segundos=300,
            orden="fecha",
            omitir_duplicados=True,
            detener_en_duplicado=False
        )

        print(f"Extraídos {len(expedientes)} expedientes. Motivo: {motivo}")
        return expedientes
```

### Uso del Monitor

```python
from Sistema_v4.monitor.monitor_entradas_expedientes_v4 import MonitorExpedientesTray

# Inicia el monitor (ejecuta hasta que se cierre)
if __name__ == "__main__":
    MonitorExpedientesTray()
```

### Verificación Manual

```python
from Sistema_v4.monitor.monitor_entradas_expedientes_v4 import VerificadorExpedientesV4
from pathlib import Path

verificador = VerificadorExpedientesV4(
    carpeta_salida=Path("mi_carpeta/expedientes"),
    nombre_archivo="expedientes_hoy.json",
    guardar_json=True
)

# Conectar señal para procesar resultados
verificador.resultado.connect(lambda resultado: print(f"Estado: {resultado.estado}"))
verificador.start()
```

---

## Manejo de Errores

### Estrategias de Recuperación

1. **Reintentos automáticos**: Hasta 5 intentos en el monitor
2. **Timeouts configurables**: Evita ejecuciones indefinidas
3. **Validación de elementos**: Verifica disponibilidad antes de interactuar
4. **Logging detallado**: Registra todos los eventos para debugging

### Tipos de Errores Comunes

#### Errores de Navegación
- **Timeout de página**: El sitio no responde en el tiempo esperado
- **Elementos no encontrados**: Cambios en la estructura de la página
- **Botón deshabilitado**: Paginación no disponible

#### Errores de Datos
- **Formato de fecha inválido**: Fechas que no coinciden con el formato esperado
- **Duplicados detectados**: Expedientes repetidos en la extracción
- **Datos incompletos**: Filas con menos de 5 columnas

#### Errores del Sistema
- **Memoria insuficiente**: Demasiados expedientes en memoria
- **Permisos de archivo**: No se puede escribir en el directorio de salida
- **Conexión perdida**: Problemas de red durante la extracción

---

## Migración desde v3

### Compatibilidad

El sistema v4 mantiene compatibilidad con v3 mediante importaciones condicionales:

```python
try:
    from Sistema_v4.operaciones.expedientes.expedientes_v4 import extraer_expedientes_completos
except ImportError:
    from Sistema_v3.operaciones.expedientes.expedientes_v4 import extraer_expedientes_completos
```

### Diferencias Principales

| Aspecto | Sistema_v3 | Sistema_v4 |
|---------|------------|------------|
| **Estructura** | Monolítica | Modular |
| **Imports** | Rutas fijas | Condicionales |
| **Config** | Hardcoded | Archivo JSON |
| **Monitor** | Básico | Interfaz completa |
| **Logging** | Limitado | Exhaustivo |

### Pasos de Migración

1. **Instalar dependencias v4**
2. **Actualizar imports** a rutas v4
3. **Migrar configuración** a formato JSON
4. **Probar funcionalidad** con ambas versiones
5. **Deprecar v3** gradualmente

---

## Estructura de Datos

### Formato de Expediente

```python
{
    "numero": "ABC-123/2024",
    "dependencia": "Juzgado Civil N° 1",
    "caratula": "PEREZ, Juan c/ LOPEZ, Maria s/ DAÑOS Y PERJUICIOS",
    "situacion": "En trámite",
    "ultima_actuacion": "2024-03-15"
}
```

### Resultado de Verificación

```python
@dataclass
class ResultadoExpedientes:
    estado: str                    # Código de finalización
    cantidad: int | None = None    # Número de expedientes extraídos
    ruta: str | None = None        # Ruta del archivo guardado
    error: str | None = None       # Mensaje de error si aplica
```

### Configuración del Monitor

```python
{
    "modo": "automatico" | "laboral" | "no_laboral",
    "horario_laboral": {
        "dias": ["lunes", "martes", ...],
        "hora_inicio": "HH:MM",
        "hora_fin": "HH:MM",
        "intervalo_minutos": int
    },
    "fuera_horario": {
        "intervalo_minutos": int
    }
}
```

---

## API Reference

### Funciones Públicas

#### `extraer_expedientes_completos(page, **kwargs)`
Función principal de extracción de expedientes.

**Parámetros:**
- `page: Page` - Página de Playwright
- `sel_tabla: str` - Selector de tabla
- `sel_tbody: str` - Selector del cuerpo de la tabla (se usa como `${sel_tbody} tr`).
  Si el DOM no posee un `<tbody>` estándar, pasá aquí el nodo contenedor de las filas.
- `sel_siguiente: str` - Selector botón siguiente
- `max_paginas: int` - Límite de páginas
- `omitir_duplicados: bool` - Evitar duplicados
- `detener_en_duplicado: bool` - Parar en duplicado
- `fecha_corte: str | None` - Fecha límite
- `tiempo_maximo_segundos: int | None` - Timeout
- `orden: str | None` - Criterio de orden

**Retorna:**
- `tuple[list[dict], str, dict[str, object]]` - (expedientes, motivo, metadata)

### Clases Principales

#### `MonitorExpedientesTray`
Aplicación de bandeja del sistema.

**Métodos:**
- `__init__()` - Inicializa la aplicación
- `verificar_expedientes()` - Ejecuta verificación manual
- `salir()` - Cierra la aplicación

#### `VerificadorExpedientesV4(QThread)`
Hilo de verificación de expedientes.

**Métodos:**
- `__init__(carpeta_salida, nombre_archivo, guardar_json)`
- `run()` - Ejecuta verificación asíncrona

**Señales:**
- `resultado: Signal(object)` - Emite ResultadoExpedientes

### Constantes

```python
# Selectores por defecto
SEL_TABLA = "table.table-striped"
SEL_TBODY = f"{SEL_TABLA} tbody"  # Valor por defecto para el parámetro sel_tbody
SEL_SIGUIENTE = "..." # Múltiples selectores

# Para portales sin `<tbody>` clásico podés redefinir sel_tbody, por ejemplo:
# sel_tbody = ".tabla-resultados .filas"

# Mapeo de ordenamiento
_ORDEN_MAP = {
    "fecha": "FECHA",
    "caratula": "CARATULA",
    "oficina": "OFICINA",
    "situacion": "SITUACION",
}

# Configuración
CONFIG_PATH = Path("config/config_monitor.json")
DEFAULT_CONFIG = {...}
```

---

## Conclusión

El Sistema Expedientes v4 representa una evolución significativa en la arquitectura y funcionalidades del sistema de extracción de expedientes. Sus principales fortalezas incluyen:

- **Robustez**: Manejo exhaustivo de errores y casos edge
- **Flexibilidad**: Parámetros configurables para diferentes escenarios
- **Usabilidad**: Interfaz de bandeja del sistema intuitiva
- **Mantenibilidad**: Código modular y bien documentado
- **Compatibilidad**: Transición suave desde versiones anteriores

Esta documentación debe mantenerse actualizada conforme evolucione el sistema, especialmente durante la migración completa desde Sistema_v3.