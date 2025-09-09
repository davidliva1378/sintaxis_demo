# Documentación Técnica - extractor_entradas.py

## Descripción General

`extractor_entradas.py` es un módulo especializado para la extracción automatizada de entradas (notificaciones y despachos) del Portal de Justicia Nacional (PJN). Utiliza Playwright para automatización web y proporciona una interfaz simple pero potente para recopilar, filtrar y persistir datos de seguimiento judicial.

## Características Principales

- **Scroll Robusto**: Implementa un sistema de desplazamiento inteligente con detección de elementos de carga
- **Filtrado Avanzado**: Soporte para filtros por tipo de evento (N/D) y rangos/fechas específicas
- **Gestión de Duplicados**: Sistema configurable para manejar entradas duplicadas con enriquecimiento de datos
- **Persistencia Dual**: Guarda datos en formato JSON y CSV para compatibilidad con versiones previas
- **Detección Determinística**: Utiliza múltiples estrategias para identificar el final del scroll

## Estructura del Código

### Constantes y Configuración

```python
# Selectores CSS para elementos del PJN
SELEC_TABLA = "div.MuiTableContainer-root tr"
SELEC_EXPEDIENTE_NUMERO = "p.MuiTypography-root.MuiTypography-body1.w-full.css-11dlpbt"
SELEC_EXPEDIENTE_CARATULA = "p.MuiTypography-root.MuiTypography-body1.w-full.italic.css-4icvzy"
SELEC_CONTENEDOR_SCROLL = "#LayoutScrollingContainer"

# Expresiones regulares para detección de estados
RE_FIN = re.compile(r"No hay m[aá]s eventos", re.I)
RE_LOADING = re.compile(r"Cargando m[aá]s eventos", re.I)
RE_EVENTO_NOTIF = re.compile(r"evento\s+notificaci[oó]n", re.I)
RE_EVENTO_DESP = re.compile(r"evento\s+despacho", re.I)
```

### Funciones Utilitarias

#### `limpiar_texto(texto: str) -> str`
Normaliza el texto removiendo saltos de línea múltiples y espacios extra.

#### `normalizar_texto(t: str) -> str`
Realiza normalización Unicode y conversión a ASCII para comparaciones consistentes.

#### `_to_iso(fecha_str: str) -> Optional[str]`
Convierte fechas en formato 'YYYY-MM-DD' o 'DD/MM/YYYY' al formato ISO estándar.

**Parámetros:**
- `fecha_str`: Cadena de fecha en cualquiera de los formatos soportados

**Retorna:**
- Fecha en formato 'YYYY-MM-DD' o None si el formato es inválido

#### `_parse_fechas_exactas(fechas: Optional[Iterable[str]]) -> set[str]`
Procesa una lista de fechas y las convierte al formato ISO.

#### `_parse_fecha_limite(f: Optional[str]) -> Optional[date]`
Convierte una fecha string a objeto `date` para comparaciones de rango.

### Funciones de Navegación Web

#### `_near_bottom(page: Page, tol: int = 24) -> bool`
Determina si el scroll está cerca del final del contenedor.

**Parámetros:**
- `page`: Instancia de página de Playwright
- `tol`: Tolerancia en píxeles (default: 24)

**Retorna:**
- True si está cerca del final, False en caso contrario

#### `_scroll_step(page: Page)`
Ejecuta un paso de desplazamiento controlado en el contenedor.

#### `_wheel(page: Page, cont_locator)`
Simula movimiento de rueda del mouse para activar carga lazy.

### Funciones de Detección de Eventos

#### `_detectar_indicador_evento(fila) -> Tuple[Optional[str], Optional[str]]`
Identifica el tipo de evento (Notificación/Despacho) usando múltiples estrategias:

1. **Estrategia Principal**: Análisis del atributo `aria-label`
2. **Fallback**: Extracción de letra del Avatar (N/D)

**Retorna:**
- Tupla `(evento, tipo_evento)` donde:
  - `evento`: 'N' para notificación, 'D' para despacho
  - `tipo_evento`: 'NOTIFICACION' o 'DESPACHO'

### Funciones de Gestión de Duplicados

#### `_base_key(e: Dict[str, Any]) -> tuple`
Genera clave única basada en número de expediente, fecha y carátula.

#### `_event_key(e: Dict[str, Any]) -> tuple`
Extiende la clave base incluyendo el tipo de evento para deduplicación completa.

## Función Principal

### `extraer_entradas_pjn()`

```python
async def extraer_entradas_pjn(
    page: Page,
    destino: Optional[str] = None,
    duplicados: bool = False,
    incluir_tipos: tuple[str, ...] = ("N", "D"),
    fechas: Optional[Iterable[str]] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
) -> int:
```

#### Parámetros

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `page` | `Page` | Requerido | Página de Playwright ya autenticada y navegada al listado |
| `destino` | `Optional[str]` | `./datos_extraidos/monitoreo` | Directorio base para almacenar archivos |
| `duplicados` | `bool` | `False` | Control de manejo de duplicados |
| `incluir_tipos` | `tuple[str, ...]` | `("N", "D")` | Tipos de eventos a incluir |
| `fechas` | `Optional[Iterable[str]]` | `None` | Fechas exactas a filtrar |
| `fecha_desde` | `Optional[str]` | `None` | Fecha inicial del rango |
| `fecha_hasta` | `Optional[str]` | `None` | Fecha final del rango |

#### Comportamiento del Parámetro `duplicados`

- **`False` (Recomendado)**: 
  - Evita duplicados usando clave compuesta (número + fecha + carátula + evento)
  - Enriquece registros históricos que no tenían tipo de evento
  - Mantiene integridad de datos a largo plazo

- **`True`**: 
  - Guarda todas las apariciones encontradas
  - Útil para auditorías o análisis de frecuencia

#### Algoritmo de Extracción

1. **Inicialización**:
   - Validación de selectores y contenedor
   - Carga del historial existente (JSON)
   - Configuración de filtros de fecha

2. **Bucle Principal** (máximo 500 iteraciones):
   - Procesamiento de filas visibles
   - Extracción de datos de expediente
   - Aplicación de filtros
   - Detección de tipo de evento
   - Gestión de duplicados

3. **Navegación Inteligente**:
   - Scroll por pasos controlados
   - Detección de indicadores de carga
   - Verificación de avance real
   - Condición de parada determinística

4. **Persistencia**:
   - Actualización del historial JSON
   - Regeneración completa del archivo CSV

#### Estructura de Datos de Salida

Cada entrada extraída contiene:

```python
{
    "numero": str,          # Número de expediente
    "caratula": str,        # Carátula del expediente
    "fecha": str,           # Fecha en formato YYYY-MM-DD
    "evento": str,          # 'N' o 'D'
    "tipo_evento": str,     # 'NOTIFICACION' o 'DESPACHO'
    "leida": bool,          # Estado de lectura (siempre False al extraer)
    "extraida_en": str      # Timestamp de extracción
}
```

#### Archivos Generados

1. **`historial_notificaciones.json`**: 
   - Formato principal para procesamiento programático
   - Mantiene estructura completa de datos
   - Utilizado para detección de duplicados

2. **`historial_notificaciones.csv`**: 
   - Formato compatible para análisis manual
   - Columnas: Fecha, Número, Carátula, Evento, TipoEvento, Leída, Extraída En

#### Valor de Retorno

Retorna el número de registros **nuevos** agregados en la ejecución actual:
- Con `duplicados=False`: Cantidad de entradas genuinamente nuevas
- Con `duplicados=True`: Cantidad total de entradas procesadas

## Manejo de Errores

El módulo implementa múltiples niveles de tolerancia a errores:

- **Errores de Selector**: Continúa con la siguiente fila si falla el parsing
- **Errores de Red**: Timeouts configurables para carga de elementos
- **Errores de Archivo**: Reporta pero no detiene la ejecución
- **Límites de Iteración**: Previene bucles infinitos con límite máximo

## Consideraciones de Rendimiento

- **Scrolling Adaptativo**: Ajusta el paso según el tamaño del viewport
- **Detección de Carga**: Espera sincronizada de elementos dinámicos
- **Procesamiento en Memoria**: Mantiene el historial cargado para comparaciones rápidas
- **Límite de Seguridad**: Máximo 500 iteraciones por ejecución

## Ejemplos de Uso

### Extracción Básica
```python
nuevas = await extraer_entradas_pjn(page)
print(f"Se extrajeron {nuevas} nuevas entradas")
```

### Filtrado por Fecha Específica
```python
nuevas = await extraer_entradas_pjn(
    page, 
    fechas=["2024-01-15", "15/01/2024"]
)
```

### Solo Notificaciones en Rango
```python
nuevas = await extraer_entradas_pjn(
    page,
    incluir_tipos=("N",),
    fecha_desde="2024-01-01",
    fecha_hasta="2024-01-31"
)
```

### Permitir Duplicados
```python
total = await extraer_entradas_pjn(
    page,
    duplicados=True
)
```

## Dependencias

- `playwright.async_api`: Automatización web
- `datetime`: Manejo de fechas
- `json`: Persistencia de datos estructurados
- `csv`: Compatibilidad con formatos tabulares
- `unicodedata`: Normalización de texto
- `re`: Procesamiento de expresiones regulares

## Notas de Mantenimiento

- **Selectores CSS**: Pueden requerir actualización si el PJN modifica su estructura
- **Expresiones Regulares**: Configuradas para múltiples variantes idiomáticas
- **Timeouts**: Ajustables según la latencia de red
- **Límites de Iteración**: Modificables según el volumen de datos esperado

## Compatibilidad

- **Versiones Previas**: Mantiene compatibilidad con formatos de archivo existentes
- **Encoding**: UTF-8 para soporte completo de caracteres especiales
- **Formatos de Fecha**: Flexible con entrada, consistente en salida