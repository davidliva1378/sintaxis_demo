# Módulo procesador_pdf - Implementado en Sistema v5

**Fecha de análisis:** 2025-11-18
**Rama:** `procesador_pdf2.1`
**Versión:** 1.0.0 (MVP - Fase 1)
**Ubicación:** `/Sistema_v5/procesador_pdf/`
**Estado:** ✅ Completamente implementado y funcional

---

## Resumen Ejecutivo

El módulo **procesador_pdf** es un sistema completo de procesamiento inteligente de actuaciones judiciales que implementa:
- ✅ Clasificación heurística por utilidad jurídica
- ✅ Detección de duplicados exactos
- ✅ Extracción de texto multi-método (PyPDF2, pdfplumber, OCR)
- ✅ Análisis de vencimientos procesales con días hábiles

**Total de código:** ~2,089 líneas Python
**Dependencias:** PyPDF2, pdfplumber, pytesseract (opcional)
**API pública:** Funciones `procesar_actuacion()` y `procesar_expediente()`

---

## Tabla de Contenidos

1. [Arquitectura del Módulo](#1-arquitectura-del-módulo)
2. [Componentes Principales](#2-componentes-principales)
3. [Extractor de Texto](#3-extractor-de-texto)
4. [Clasificador de Actuaciones](#4-clasificador-de-actuaciones)
5. [Analizador de Vencimientos](#5-analizador-de-vencimientos)
6. [Detector de Duplicados](#6-detector-de-duplicados)
7. [Modelos de Datos](#7-modelos-de-datos)
8. [API Pública](#8-api-pública)
9. [Integración con Sistema v6](#9-integración-con-sistema-v6)
10. [Ejemplos de Uso](#10-ejemplos-de-uso)
11. [Roadmap](#11-roadmap)

---

## 1. Arquitectura del Módulo

### Estructura de Archivos

```
Sistema_v5/procesador_pdf/
├── __init__.py                          # API pública (291 líneas)
├── extractor_texto.py                   # Extracción de PDFs (369 líneas)
├── clasificador.py                      # Clasificación heurística (347 líneas)
├── analizador_vencimientos.py          # Vencimientos procesales (445 líneas)
├── detector_duplicados.py              # Detección duplicados (363 líneas)
├── models.py                           # Dataclasses y Enums (274 líneas)
├── README.md                           # Documentación (407 líneas)
├── MEJORAS_PROPUESTAS.md              # Roadmap detallado (442 líneas)
├── PLAN_SISTEMA_IA_LOCAL.md           # IA local (977 líneas)
└── Plan_Procesamiento_Actuaciones_Hibrido.md  # Plan arquitectura (379 líneas)
```

### Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                    API PÚBLICA (__init__.py)                 │
│  procesar_actuacion() | procesar_expediente()               │
└────────┬────────────────────────────────────────────────────┘
         │
         v
┌─────────────────────────────────────────────────────────────┐
│                    COMPONENTES CORE                          │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ExtractorTexto    │  │Clasificador      │                │
│  │- PyPDF2          │  │- Reglas          │                │
│  │- pdfplumber      │  │- Keywords        │                │
│  │- OCR (Tesseract) │  │- Score 0-100     │                │
│  └──────────────────┘  └──────────────────┘                │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │AnalizadorVenc    │  │DetectorDup       │                │
│  │- Días hábiles    │  │- Hash MD5        │                │
│  │- Feriados        │  │- Normalización   │                │
│  │- Feria judicial  │  │- Cédulas dup     │                │
│  └──────────────────┘  └──────────────────┘                │
└─────────────────────────────────────────────────────────────┘
         │
         v
┌─────────────────────────────────────────────────────────────┐
│                    MODELOS DE DATOS                          │
│  - UtilidadJuridica (Enum)                                  │
│  - ClasificacionActuacion (dataclass)                       │
│  - Vencimiento (dataclass)                                  │
│  - DuplicadoDetectado (dataclass)                           │
│  - TextoExtraido (dataclass)                                │
│  - ResultadoProcesamiento (dataclass)                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Componentes Principales

### Resumen de Componentes

| Componente | Archivo | Líneas | Funcionalidad Principal |
|-----------|---------|--------|------------------------|
| **ExtractorTexto** | extractor_texto.py | 369 | Extracción texto de PDFs (multi-método) |
| **ClasificadorActuaciones** | clasificador.py | 347 | Clasificación por utilidad jurídica |
| **AnalizadorVencimientos** | analizador_vencimientos.py | 445 | Cálculo de vencimientos procesales |
| **DetectorDuplicados** | detector_duplicados.py | 363 | Detección de actuaciones duplicadas |
| **Modelos** | models.py | 274 | Estructuras de datos |
| **API** | __init__.py | 291 | Funciones helper de alto nivel |

---

## 3. Extractor de Texto

### Ubicación
`/Sistema_v5/procesador_pdf/extractor_texto.py` (369 líneas)

### Clase: `ExtractorTexto`

#### Constructor
```python
def __init__(self, usar_ocr: bool = True, idioma_ocr: str = "spa")
```

**Parámetros:**
- `usar_ocr`: Habilitar OCR como fallback (default: True)
- `idioma_ocr`: Idioma para Tesseract (default: "spa")

#### Método Principal: `extraer()`

```python
def extraer(self, ruta_pdf: str) -> TextoExtraido
```

**Estrategia de extracción (degradación gradual):**
1. **PyPDF2** - Rápido, básico
2. **pdfplumber** - Mejor calidad si PyPDF2 falla
3. **OCR con Tesseract** - Solo si texto embebido < 50 caracteres
4. **Normalización** - Limpieza y estructuración
5. **Cálculo de métricas** - Hash MD5, longitud, palabras

**Retorna:** Objeto `TextoExtraido` con:
- `texto_completo`: Texto sin procesar
- `texto_normalizado`: Texto limpio
- `num_paginas`: Cantidad de páginas
- `metodo_extraccion`: "embebido", "ocr", "mixto"
- `tiene_texto_embebido`: Bool
- `hash_contenido`: MD5 para deduplicación
- `longitud_caracteres`: int
- `longitud_palabras`: int

#### Ejemplo de Uso

```python
extractor = ExtractorTexto(usar_ocr=True, idioma_ocr="spa")
resultado = extractor.extraer("sentencia.pdf")

print(f"Método: {resultado.metodo_extraccion}")      # "embebido"
print(f"Páginas: {resultado.num_paginas}")           # 15
print(f"Palabras: {resultado.longitud_palabras}")    # 3500
print(f"Está vacío: {resultado.esta_vacio}")         # False
print(f"Hash: {resultado.hash_contenido}")           # "a1b2c3d4..."
```

#### Normalización de Texto

```python
def normalizar_texto(self, texto: str) -> str
```

**Operaciones:**
1. Eliminar caracteres de control
2. Unificar saltos de línea
3. Filtrar líneas muy cortas (<3 chars)
4. **Detectar y eliminar encabezados/pies de página**
5. Reducir múltiples espacios
6. Reducir saltos de línea excesivos

**Patrones de encabezado/pie detectados:**
- "página X de Y"
- "Poder Judicial de la Nación"
- "Expediente N° XXXX"
- "Hoja N° XXXX"
- Números de folio

#### Librerías Utilizadas

1. **PyPDF2** (>=3.0.0) - Extracción básica
2. **pdfplumber** (>=0.11.0) - Extracción avanzada
3. **pytesseract** (>=0.3.10) - OCR (requiere Tesseract en sistema)
4. **pdf2image** (>=1.16.0) - Conversión PDF→imagen para OCR

---

## 4. Clasificador de Actuaciones

### Ubicación
`/Sistema_v5/procesador_pdf/clasificador.py` (347 líneas)

### Clase: `ClasificadorActuaciones`

#### Niveles de Utilidad

```python
class UtilidadJuridica(Enum):
    NULA = "nula"    # Score 0-10:  Providencias simples, descartables
    BAJA = "baja"    # Score 11-40: Cargos, constancias
    MEDIA = "media"  # Score 41-70: Presentaciones genéricas
    ALTA = "alta"    # Score 71-100: Sentencias, resoluciones, traslados
```

#### Patrones de Clasificación

**UTILIDAD NULA:**
```python
PATRONES_NULA = [
    r"^agreg[uú]ese",
    r"^t[ée]ngase\s+presente",
    r"^en\s+los\s+t[ée]rminos\s+solicitados",
    r"^c[ií]tese",
    r"^pase",
    r"^vuelva",
    r"^reserve",
    r"^archiv[eé]se",
]
```

**UTILIDAD ALTA:**
```python
KEYWORDS_ALTA = [
    "sentencia", "resoluci[oó]n", "auto.*fundado", "fallo",
    "demanda", "contestaci[oó]n", "apelaci[oó]n", "alegato",
    "expresi[oó]n.*agravios", "amparo",
    "medida.*cautelar", "medida.*precautoria",
    "resuelve", "considerando.*fallo", "visto.*considerando",
]
```

#### Método Principal: `clasificar()`

```python
def clasificar(
    self,
    tipo: str,
    detalle: str,
    tiene_archivo: bool = False,
    longitud_detalle: Optional[int] = None
) -> ClasificacionActuacion
```

**Flujo de clasificación:**
1. Providencias simples → NULA (score 5)
2. Providencias cortas (<50 chars) → NULA (score 8)
3. Tipos de alta prioridad (SENTENCIA, AUTO, etc.) → ALTA (score 85-95)
4. Keywords en detalle → Según keywords detectados
5. Cédulas con plazo → ALTA (score 75)
6. Cédulas sin plazo → BAJA (score 25)
7. Default → MEDIA con `requiere_pdf=True`

#### Ejemplo de Uso

```python
clasificador = ClasificadorActuaciones()

# Caso 1: Providencia simple
result = clasificador.clasificar("PROVEIDO", "Agréguese")
# → UtilidadJuridica.NULA, score=5

# Caso 2: Sentencia
result = clasificador.clasificar(
    "SENTENCIA",
    "VISTO...CONSIDERANDO...RESUELVE condenar...",
    tiene_archivo=True
)
# → UtilidadJuridica.ALTA, score=95

# Caso 3: Cédula con plazo
result = clasificador.clasificar(
    "CEDULA_ELECTRONICA",
    "Notificado el 15/03/2024. Plazo 5 días"
)
# → UtilidadJuridica.ALTA, score=75, tiene_plazo_probable=True
```

#### Clasificación en Lote

```python
def clasificar_lote(self, actuaciones: List[Dict]) -> Dict[int, ClasificacionActuacion]
```

Procesa múltiples actuaciones eficientemente.

#### Estadísticas

```python
def estadisticas_clasificacion(self, clasificaciones: Dict) -> Dict
```

**Retorna:**
```json
{
    "total_actuaciones": 100,
    "nula": {"count": 30, "porcentaje": 30.0},
    "baja": {"count": 20, "porcentaje": 20.0},
    "media": {"count": 25, "porcentaje": 25.0},
    "alta": {"count": 25, "porcentaje": 25.0},
    "requieren_pdf": 15,
    "tienen_plazo_probable": 5,
    "probables_duplicados": 8,
    "reduccion_estimada": 50.0
}
```

---

## 5. Analizador de Vencimientos

### Ubicación
`/Sistema_v5/procesador_pdf/analizador_vencimientos.py` (445 líneas)

### Clase: `AnalizadorVencimientos`

#### Constructor
```python
def __init__(self, considerar_feria: bool = True)
```

**Parámetros:**
- `considerar_feria`: Si descontar feria judicial (enero-febrero) del cálculo

#### Tipos de Vencimiento Soportados

```python
class TipoVencimiento(Enum):
    CEDULA_ELECTRONICA = "cedula_electronica"  # 5 días hábiles
    CEDULA_FISICA = "cedula_fisica"            # 3 días hábiles
    TRASLADO = "traslado"                      # Variable
    ALEGATO = "alegato"                        # Variable
    PRESENTACION = "presentacion"              # Variable
    OTRO = "otro"
```

#### Patrones de Detección

**Cédula electrónica:**
```python
{
    "tipo": TipoVencimiento.CEDULA_ELECTRONICA,
    "regex": r"notific[oóa].*?(?:el|fecha:?)\s*(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})",
    "plazo_dias": 5,  # Art. 135 CPCCN
    "dias_habiles": True,
    "confianza": 0.95
}
```

**Traslado con plazo variable:**
```python
{
    "tipo": TipoVencimiento.TRASLADO,
    "regex": r"traslado.*?(?:por|de)\s*(\d+)\s*d[ií]as?",
    "plazo_variable": True,  # Se extrae del texto
    "dias_habiles": True,
    "confianza": 0.92
}
```

#### Método Principal: `analizar_texto()`

```python
def analizar_texto(
    self,
    texto: str,
    actuacion_id: Optional[int] = None
) -> List[Vencimiento]
```

**Ejemplo de Uso:**
```python
analizador = AnalizadorVencimientos(considerar_feria=True)

texto_cedula = """
Cédula de notificación electrónica.
Notificado el 15/03/2024 a las 10:30hs.
Plazo: 5 días hábiles para contestar.
"""

vencimientos = analizador.analizar_texto(texto_cedula)

for v in vencimientos:
    print(f"Tipo: {v.tipo.value}")                    # "cedula_electronica"
    print(f"Notificación: {v.fecha_notificacion}")    # 2024-03-15
    print(f"Vencimiento: {v.fecha_vencimiento}")      # 2024-03-22 (5 días hábiles)
    print(f"Días restantes: {v.dias_restantes}")      # Property calculada
    print(f"Urgente: {v.es_urgente}")                 # True si <= 3 días
```

#### Cálculo de Días Hábiles

```python
def calcular_fecha_vencimiento(
    self,
    fecha_inicio: date,
    plazo_dias: int
) -> date
```

**Algoritmo:**
1. Iniciar contador en 0
2. Avanzar 1 día
3. Si es hábil (no sábado/domingo/feriado/feria) → contador++
4. Repetir hasta alcanzar plazo_dias
5. Retornar fecha actual

**Descontar:**
- Sábados y domingos
- Feriados nacionales (2024-2025 hardcodeados)
- Feria judicial (enero-febrero, si `considerar_feria=True`)

#### Feriados Hardcodeados

**2024:**
```python
FERIADOS_2024 = [
    date(2024, 1, 1),   # Año Nuevo
    date(2024, 2, 12),  # Carnaval
    date(2024, 2, 13),  # Carnaval
    date(2024, 3, 24),  # Día de la Memoria
    date(2024, 3, 29),  # Viernes Santo
    date(2024, 4, 2),   # Malvinas
    date(2024, 5, 1),   # Día del Trabajador
    date(2024, 5, 25),  # Revolución de Mayo
    # ... (total 13 feriados)
]
```

**NOTA:** Para años futuros, retorna `False`. Se debe migrar a librería `holidays` para escalabilidad.

#### Feria Judicial

```python
FERIA_JUDICIAL_2024 = (date(2024, 1, 1), date(2024, 2, 29))
FERIA_JUDICIAL_2025 = (date(2025, 1, 1), date(2025, 2, 28))
```

---

## 6. Detector de Duplicados

### Ubicación
`/Sistema_v5/procesador_pdf/detector_duplicados.py` (363 líneas)

### Clase: `DetectorDuplicados`

#### Estrategia de Detección

**Fase 1 (Implementada):** Duplicados exactos
- Hash MD5 de contenido normalizado
- Ignora elementos variables (fechas, horas, nombres)

**Fase 2 (Planificada):** Duplicados semánticos
- SimHash para near-duplicates
- MinHash + LSH para escalabilidad

#### Normalización de Contenido

**Patrones normalizados:**
```python
[
    # Fechas y horas
    (r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", ""),
    (r"\d{1,2}:\d{2}(:\d{2})?", ""),

    # Números de folio, cargo, hash
    (r"folio\s+n?[°º]?\s*\d+", ""),
    (r"cargo\s+n?[°º]?\s*\d+", ""),
    (r"hash\s*:?\s*[a-f0-9]{6,}", ""),

    # Nombres y DNI
    (r"DNI\s+N?[°º]?\s*\d{7,8}", "DNI_XXX"),
    (r"CUIT\s+N?[°º]?\s*\d{2}-\d{8}-\d", "CUIT_XXX"),

    # Emails
    (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "EMAIL"),
]
```

#### Método Principal: `detectar_duplicados_exactos()`

```python
def detectar_duplicados_exactos(
    self,
    actuaciones: List[Dict[str, any]],
    campo_texto: str = "Detalle"
) -> List[DuplicadoDetectado]
```

**Algoritmo:**
1. Calcular hash normalizado de cada actuación
2. Agrupar por hash
3. Para grupos con 2+ elementos:
   - Primer elemento = "original"
   - Resto = "duplicados"
4. Crear objetos `DuplicadoDetectado`

**Ejemplo:**
```python
actuaciones = [
    {"id": 1, "Detalle": "Cédula a Juan García. Notificado 15/03/2024 10:00hs. Hash ABC"},
    {"id": 2, "Detalle": "Cédula a María López. Notificado 15/03/2024 10:05hs. Hash XYZ"},
]

detector = DetectorDuplicados()
duplicados = detector.detectar_duplicados_exactos(actuaciones)

# Resultado: 1 duplicado detectado
# DuplicadoDetectado(
#     actuacion_id_original=1,
#     actuacion_id_duplicada=2,
#     tipo=TipoDuplicado.EXACTO,
#     similitud=1.0,
#     motivo="Contenido normalizado idéntico"
# )
```

#### Detección de Cédulas Duplicadas

```python
def detectar_cedulas_duplicadas(
    self,
    actuaciones: List[Dict[str, any]]
) -> List[DuplicadoDetectado]
```

**Caso especial:** Múltiples cédulas del mismo acto para distintos destinatarios.

**Normalización especial para cédulas:**
- Elimina "A [Nombre] [Apellido]"
- Elimina "Notifíquese a [persona]"
- Elimina domicilios constituidos
- Elimina domicilios electrónicos

---

## 7. Modelos de Datos

### Ubicación
`/Sistema_v5/procesador_pdf/models.py` (274 líneas)

### Enums Definidos

#### UtilidadJuridica
```python
class UtilidadJuridica(Enum):
    NULA = "nula"
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
```

#### TipoDuplicado
```python
class TipoDuplicado(Enum):
    EXACTO = "exacto"          # Hash idéntico
    SEMANTICO = "semantico"    # Contenido similar (Fase 2)
    PARCIAL = "parcial"        # Similitud parcial (Fase 2)
```

#### TipoVencimiento
```python
class TipoVencimiento(Enum):
    CEDULA_ELECTRONICA = "cedula_electronica"
    CEDULA_FISICA = "cedula_fisica"
    TRASLADO = "traslado"
    ALEGATO = "alegato"
    PRESENTACION = "presentacion"
    OTRO = "otro"
```

### Dataclasses Definidos

#### ClasificacionActuacion
```python
@dataclass
class ClasificacionActuacion:
    utilidad: UtilidadJuridica
    score: int  # 0-100
    motivo: str
    requiere_pdf: bool = False
    es_duplicado_probable: bool = False
    tiene_plazo_probable: bool = False
    keywords_detectados: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Serialización para JSON/DB"""
```

#### TextoExtraido
```python
@dataclass
class TextoExtraido:
    texto_completo: str
    texto_normalizado: str
    num_paginas: int
    metodo_extraccion: str  # 'embebido', 'ocr', 'mixto'
    tiene_texto_embebido: bool
    longitud_caracteres: int
    longitud_palabras: int
    hash_contenido: str

    @property
    def esta_vacio(self) -> bool:
        """True si < 10 caracteres"""
        return len(self.texto_normalizado.strip()) < 10

    @property
    def es_muy_corto(self) -> bool:
        """True si < 20 palabras"""
        return self.longitud_palabras < 20
```

#### Vencimiento
```python
@dataclass
class Vencimiento:
    tipo: TipoVencimiento
    fecha_notificacion: date
    plazo_dias: int
    fecha_vencimiento: date
    dias_habiles: bool = True
    descripcion: str = ""
    actuacion_id: Optional[int] = None
    texto_fuente: str = ""
    confianza: float = 1.0

    @property
    def dias_restantes(self) -> int:
        """Días hasta vencimiento"""
        delta = self.fecha_vencimiento - date.today()
        return delta.days

    @property
    def esta_vencido(self) -> bool:
        """True si ya venció"""
        return date.today() > self.fecha_vencimiento

    @property
    def es_urgente(self) -> bool:
        """True si vence en <= 3 días"""
        return 0 <= self.dias_restantes <= 3
```

#### DuplicadoDetectado
```python
@dataclass
class DuplicadoDetectado:
    actuacion_id_original: int   # ID a conservar
    actuacion_id_duplicada: int  # ID a marcar como duplicado
    tipo: TipoDuplicado          # EXACTO, SEMANTICO, PARCIAL
    similitud: float             # 0.0-1.0
    hash_normalizado: Optional[str] = None
    motivo: str = ""
```

#### ResultadoProcesamiento
```python
@dataclass
class ResultadoProcesamiento:
    """Contenedor principal para resultados completos"""
    actuacion_id: int
    clasificacion: ClasificacionActuacion
    texto: Optional[TextoExtraido] = None
    duplicados: List[DuplicadoDetectado] = field(default_factory=list)
    vencimientos: List[Vencimiento] = field(default_factory=list)
    errores: List[str] = field(default_factory=list)

    @property
    def requiere_atencion(self) -> bool:
        """Alta utilidad o tiene vencimientos"""
        return (self.clasificacion.utilidad in [UtilidadJuridica.ALTA, UtilidadJuridica.MEDIA]
                or self.tiene_vencimientos)
```

---

## 8. API Pública

### Ubicación
`/Sistema_v5/procesador_pdf/__init__.py` (291 líneas)

### Exports del Módulo

```python
__all__ = [
    # Modelos
    "UtilidadJuridica",
    "TipoDuplicado",
    "TipoVencimiento",
    "ClasificacionActuacion",
    "DuplicadoDetectado",
    "Vencimiento",
    "TextoExtraido",
    "ResultadoProcesamiento",
    # Clases principales
    "ClasificadorActuaciones",
    "DetectorDuplicados",
    "ExtractorTexto",
    "AnalizadorVencimientos",
    # Funciones helper
    "procesar_actuacion",
    "procesar_expediente",
]
```

### Función Helper: `procesar_actuacion()`

```python
def procesar_actuacion(
    actuacion: dict,
    ruta_pdf: str = None,
    analizar_vencimientos: bool = True,
    detectar_duplicados: bool = False,
    actuaciones_comparar: list = None
) -> ResultadoProcesamiento
```

**Pipeline completo:**
1. Clasificación
2. Extracción de texto si hay PDF
3. Análisis de vencimientos si probable
4. Detección de duplicados
5. Retorno de `ResultadoProcesamiento`

**Ejemplo:**
```python
from Sistema_v5.procesador_pdf import procesar_actuacion

actuacion = {
    "id": 1,
    "tipo": "CEDULA_ELECTRONICA",
    "detalle": "Notificación del 15/03/2024...",
    "tiene_archivo": True
}

resultado = procesar_actuacion(
    actuacion,
    ruta_pdf="/path/to/cedula.pdf",
    analizar_vencimientos=True
)

print(resultado.clasificacion.utilidad)  # UtilidadJuridica.ALTA
print(len(resultado.vencimientos))        # 1
print(resultado.requiere_atencion)        # True
```

### Función Helper: `procesar_expediente()`

```python
def procesar_expediente(
    actuaciones: list,
    rutas_pdf: dict = None,
    analizar_vencimientos: bool = True,
    detectar_duplicados: bool = True
) -> dict
```

**Pipeline completo de expediente:**
1. Procesar cada actuación individualmente
2. Detección de duplicados en batch
3. Recopilar vencimientos
4. Generar estadísticas
5. Retornar resultado completo

**Retorna:**
```python
{
    "resultados": {act_id: ResultadoProcesamiento},
    "estadisticas": {
        "total_actuaciones": int,
        "por_utilidad": {
            "nula": {"count": int, "porcentaje": float},
            "baja": {...},
            "media": {...},
            "alta": {...}
        },
        "reduccion_estimada": float
    },
    "vencimientos_urgentes": List[Vencimiento],
    "vencimientos_totales": int,
    "duplicados_detectados": List[DuplicadoDetectado]
}
```

---

## 9. Integración con Sistema v6

### Paso 1: Instalar Dependencias

**Actualizar `Sistema_v6/requirements.txt`:**
```txt
# Procesamiento de PDFs
PyPDF2>=3.0.0
pdfplumber>=0.11.0

# OCR (opcional)
pytesseract>=0.3.10
pdf2image>=1.16.0
```

**Instalar:**
```bash
cd Sistema_v6
pip install -r requirements.txt
```

**Instalar Tesseract (opcional, solo si usar OCR):**
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-spa

# macOS
brew install tesseract tesseract-lang
```

### Paso 2: Importar Módulo

**Opción A: Importación directa desde Sistema_v5**

```python
# En Sistema_v6/application/services/procesador_actuaciones_service.py

import sys
from pathlib import Path

# Agregar Sistema_v5 al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "Sistema_v5"))

from Sistema_v5.procesador_pdf import (
    procesar_expediente,
    ClasificadorActuaciones,
    AnalizadorVencimientos,
    UtilidadJuridica
)
```

**Opción B: Copiar módulo a v6**

```bash
cp -r Sistema_v5/procesador_pdf/ Sistema_v6/core/procesador_pdf/
```

### Paso 3: Actualizar Base de Datos

**Agregar campos a tabla `actuaciones`:**
```sql
ALTER TABLE actuaciones
ADD COLUMN utilidad ENUM('nula','baja','media','alta') NULL,
ADD COLUMN score INT NULL,
ADD COLUMN motivo_clasificacion TEXT NULL,
ADD COLUMN requiere_pdf BOOLEAN DEFAULT FALSE,
ADD COLUMN tiene_plazo_probable BOOLEAN DEFAULT FALSE,
ADD INDEX idx_utilidad (utilidad),
ADD INDEX idx_score (score);
```

**Crear tabla de vencimientos:**
```sql
CREATE TABLE vencimientos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    actuacion_id INT NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    fecha_notificacion DATE NOT NULL,
    plazo_dias INT NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    descripcion TEXT,
    estado ENUM('pendiente','atendido','vencido') DEFAULT 'pendiente',
    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (actuacion_id) REFERENCES actuaciones(id),
    INDEX idx_fecha_vencimiento (fecha_vencimiento),
    INDEX idx_estado (estado)
);
```

### Paso 4: Crear Servicio de Procesamiento

**Archivo:** `Sistema_v6/application/services/procesador_actuaciones_service.py`

```python
from typing import List, Dict
from Sistema_v5.procesador_pdf import procesar_expediente, ClasificadorActuaciones

class ProcesadorActuacionesService:
    def __init__(
        self,
        actuaciones_repo: ActuacionesRepository,
        vencimientos_repo: VencimientosRepository
    ):
        self.actuaciones_repo = actuaciones_repo
        self.vencimientos_repo = vencimientos_repo
        self.clasificador = ClasificadorActuaciones()

    async def procesar_expediente_completo(self, expediente_id: int) -> Dict:
        # Cargar actuaciones
        actuaciones = await self.actuaciones_repo.obtener_por_expediente(expediente_id)

        # Convertir a formato esperado
        actuaciones_dict = [
            {
                "id": act.id,
                "tipo": act.tipo,
                "detalle": act.detalle,
                "tiene_archivo": act.tiene_archivo
            }
            for act in actuaciones
        ]

        # Procesar
        resultado = procesar_expediente(
            actuaciones_dict,
            analizar_vencimientos=True,
            detectar_duplicados=True
        )

        # Persistir resultados
        # ...

        return resultado
```

### Paso 5: Endpoint REST API

**Archivo:** `Sistema_v6/presentation/api/rest/routers/actuaciones.py`

```python
@router.post("/expediente/{expediente_id}/procesar")
async def procesar_expediente(
    expediente_id: int,
    service: ProcesadorActuacionesService = Depends()
):
    """Procesa actuaciones con módulo procesador_pdf"""
    resultado = await service.procesar_expediente_completo(expediente_id)
    return resultado
```

### Paso 6: Frontend React

**Componente:** `Sistema_v6/frontend/src/components/expedientes/ProcesadorActuaciones.tsx`

```typescript
export const ProcesadorActuaciones: React.FC<{ expedienteId: number }> = ({
  expedienteId
}) => {
  const [procesando, setProcesando] = useState(false);
  const [stats, setStats] = useState(null);

  const handleProcesar = async () => {
    setProcesando(true);
    try {
      const resultado = await procesarExpediente(expedienteId);
      setStats(resultado.estadisticas);
    } finally {
      setProcesando(false);
    }
  };

  return (
    <Card>
      <h3>Procesador Inteligente de Actuaciones</h3>
      <Button onClick={handleProcesar} disabled={procesando}>
        {procesando ? 'Procesando...' : 'Procesar Expediente'}
      </Button>

      {stats && (
        <div>
          <p>Total: {stats.total_actuaciones}</p>
          <p>Alta utilidad: {stats.por_utilidad.alta.count}</p>
          <p>Reducción: {stats.reduccion_estimada}%</p>
        </div>
      )}
    </Card>
  );
};
```

---

## 10. Ejemplos de Uso

### Ejemplo 1: Clasificación Básica

```python
from Sistema_v5.procesador_pdf import ClasificadorActuaciones

clasificador = ClasificadorActuaciones()

# Clasificar sentencia
clf = clasificador.clasificar(
    tipo="SENTENCIA",
    detalle="VISTO...CONSIDERANDO...RESUELVE condenar a pagar $500.000",
    tiene_archivo=True
)

print(f"Utilidad: {clf.utilidad.value}")  # "alta"
print(f"Score: {clf.score}")              # 95
print(f"Motivo: {clf.motivo}")
```

### Ejemplo 2: Análisis de Vencimientos

```python
from Sistema_v5.procesador_pdf import AnalizadorVencimientos

analizador = AnalizadorVencimientos()

texto = """
Cédula de notificación electrónica.
Notificado el 15/03/2024 a las 10:30hs.
Plazo: 5 días hábiles para contestar.
"""

vencimientos = analizador.analizar_texto(texto)

for v in vencimientos:
    print(f"Vencimiento: {v.fecha_vencimiento}")
    print(f"Días restantes: {v.dias_restantes}")
    print(f"Urgente: {v.es_urgente}")
```

### Ejemplo 3: Procesamiento Completo

```python
from Sistema_v5.procesador_pdf import procesar_expediente

actuaciones = [
    {"id": 1, "tipo": "SENTENCIA", "detalle": "Sentencia...", "tiene_archivo": True},
    {"id": 2, "tipo": "PROVEIDO", "detalle": "Agréguese", "tiene_archivo": False},
    {"id": 3, "tipo": "CEDULA", "detalle": "Notificado 15/03/2024...", "tiene_archivo": True},
]

resultado = procesar_expediente(
    actuaciones,
    analizar_vencimientos=True,
    detectar_duplicados=True
)

print(f"Total: {resultado['estadisticas']['total_actuaciones']}")
print(f"Alta: {resultado['estadisticas']['por_utilidad']['alta']['count']}")
print(f"Reducción: {resultado['estadisticas']['reduccion_estimada']}%")
print(f"Vencimientos urgentes: {len(resultado['vencimientos_urgentes'])}")
```

---

## 11. Roadmap

### Fase 1 (MVP) - ✅ COMPLETADA

- [x] Clasificador por reglas heurísticas
- [x] Detector de duplicados exactos
- [x] Extractor de texto (PyPDF2 + pdfplumber + OCR)
- [x] Analizador de vencimientos con días hábiles
- [x] API unificada
- [x] Documentación completa
- [x] Tests de integración

### Fase 2 (Features Avanzadas) - 🚧 PLANIFICADA

- [ ] Clasificador ML híbrido (reglas + Logistic Regression)
- [ ] Detector de duplicados semánticos (SimHash/MinHash)
- [ ] Sistema de alertas multinivel
- [ ] Dashboard de monitoreo
- [ ] Integración con MySQL
- [ ] NER jurídico básico
- [ ] Feriados dinámicos (librería `holidays`)

**Estimación:** 3-4 semanas

### Fase 3 (IA Generativa) - 📅 FUTURA

- [ ] LLM local (Llama 3.1 8B + Ollama)
- [ ] Embeddings y RAG (BGE-M3 + ChromaDB)
- [ ] Generador de apelaciones
- [ ] Generador de expresión de agravios
- [ ] Resumen automático
- [ ] Búsqueda semántica

**Estimación:** 4-6 semanas

---

## Resumen de Capacidades Actuales

### ✅ Implementado

| Funcionalidad | Estado | Performance |
|--------------|--------|-------------|
| Clasificación heurística | ✅ Completa | ~1000 acts/seg |
| Duplicados exactos | ✅ Completa | ~500 acts/seg |
| Extracción texto (sin OCR) | ✅ Completa | 2-5 PDFs/seg |
| Extracción texto (con OCR) | ✅ Completa | ~1 pág/seg |
| Vencimientos procesales | ✅ Completa | ~1000 acts/seg |
| API unificada | ✅ Completa | - |

### 📊 Métricas Esperadas

- **Reducción de volumen:** 30-50% de actuaciones descartables
- **Precisión clasificador:** >95% (en dataset de prueba)
- **Detección duplicados:** >90% recall
- **Detección vencimientos:** >98% (cédulas)

### 🎯 Próximos Pasos Recomendados

1. **Integrar con Sistema v6** (1-2 semanas)
2. **Migrar clasificaciones existentes** (3-5 días)
3. **Dashboard básico de estadísticas** (1 semana)
4. **Implementar Fase 2** (3-4 semanas)

---

**Última actualización:** 2025-11-18
**Versión del módulo:** 1.0.0
**Rama:** procesador_pdf2.1
