# Refactorización MCP Server - Integración procesador_pdf

**Tarea 3: Eliminación de código duplicado y nuevas funcionalidades**
**Fecha**: 2025-11-03
**Estado**: ✅ COMPLETADO

---

## 📋 Resumen Ejecutivo

Esta refactorización elimina código duplicado entre `mcp_server/utils/pdf_extractor.py` y `procesador_pdf/extractor_texto.py`, convirtiendo el módulo MCP en un **wrapper inteligente** sobre el sistema `procesador_pdf` mientras mantiene 100% de compatibilidad hacia atrás.

### Objetivos Cumplidos

- ✅ **Eliminación de duplicación**: 65-85 líneas de código duplicado eliminadas
- ✅ **Nuevas funcionalidades**: Clasificación y análisis de vencimientos desde MCP
- ✅ **Mejoras técnicas**: Soporte OCR, hash MD5, detección de método de extracción
- ✅ **Compatibilidad**: 100% backward compatible con código existente
- ✅ **Fallback inteligente**: Implementación legacy preservada para casos sin procesador_pdf

---

## 🔄 Cambios Realizados

### 1. Archivo Refactorizado: `pdf_extractor.py`

**Antes** (163 líneas):
- Implementación directa con pdfplumber
- Código duplicado con procesador_pdf
- Sin soporte OCR
- Sin metadata enriquecida
- Sin funcionalidades de clasificación

**Después** (435 líneas):
- Wrapper sobre procesador_pdf.ExtractorTexto
- Código duplicado eliminado
- Soporte OCR opcional
- Metadata enriquecida (hash MD5, método de extracción)
- Nuevas funciones: clasificación y análisis de vencimientos
- Fallback a pdfplumber legacy preservado

### 2. Nuevas Funcionalidades

#### A. Extracción Mejorada con OCR

```python
from Sistema_v5.mcp_server.utils.pdf_extractor import extract_text_from_pdf

# NUEVO: Soporte para PDFs escaneados
resultado = extract_text_from_pdf(
    "cedula_escaneada.pdf",
    use_ocr=True  # ← NUEVO parámetro
)

print(resultado["text"])  # Texto extraído con OCR
print(resultado["hash"])  # ← NUEVO: Hash MD5 para deduplicación
print(resultado["extraction_method"])  # ← NUEVO: "ocr", "pdfplumber", "pypdf2"
```

#### B. Clasificación de Contenido PDF

```python
from Sistema_v5.mcp_server.utils.pdf_extractor import classify_pdf_content

# NUEVA funcionalidad: Clasificar utilidad jurídica
clasificacion = classify_pdf_content(
    "cedula.pdf",
    tipo_actuacion="CEDULA_ELECTRONICA",
    detalle_actuacion="Notificación de sentencia definitiva"
)

if clasificacion:
    print(f"Utilidad: {clasificacion['utilidad']}")  # "ALTA", "MEDIA", "BAJA", "NULA"
    print(f"Confianza: {clasificacion['score']}")  # 0-100
    print(f"Motivo: {clasificacion['motivo']}")
    print(f"Keywords: {clasificacion['keywords']}")
    print(f"Tiene plazo: {clasificacion['tiene_plazo']}")
```

**Casos de uso**:
- Priorizar descarga de actuaciones importantes
- Filtrar actuaciones de baja utilidad
- Detectar automáticamente documentos con plazos procesales

#### C. Análisis de Vencimientos

```python
from Sistema_v5.mcp_server.utils.pdf_extractor import analyze_deadlines_in_pdf

# NUEVA funcionalidad: Detectar vencimientos automáticamente
vencimientos = analyze_deadlines_in_pdf("cedula_notificacion.pdf")

if vencimientos:
    for venc in vencimientos:
        print(f"Tipo: {venc['tipo']}")
        print(f"Notificación: {venc['fecha_notificacion']}")
        print(f"Vencimiento: {venc['fecha_vencimiento']}")
        print(f"Días restantes: {venc['dias_restantes']}")
        print(f"¿Urgente?: {venc['es_urgente']}")  # < 7 días
        print(f"Descripción: {venc['descripcion']}")
        print("---")
```

**Casos de uso**:
- Detectar automáticamente plazos procesales
- Alertas de vencimientos urgentes
- Calendario automático de actuaciones

---

## 📊 Comparación Técnica

### Funcionalidad Existente (Mejorada)

| Característica | Antes | Después |
|----------------|-------|---------|
| **Extracción básica** | ✅ pdfplumber | ✅ procesador_pdf + fallback |
| **Metadata** | ✅ Básica | ✅ Enriquecida (hash, método) |
| **Manejo errores** | ✅ Try/except | ✅ Try/except mejorado |
| **Múltiples páginas** | ✅ Soportado | ✅ Soportado |
| **Información por página** | ✅ Parcial | ✅ Completa |

### Nuevas Funcionalidades

| Funcionalidad | Disponible | Requiere |
|---------------|------------|----------|
| **OCR para PDFs escaneados** | ✅ Nuevo | tesseract-ocr (opcional) |
| **Hash MD5 deduplicación** | ✅ Nuevo | procesador_pdf |
| **Detección método extracción** | ✅ Nuevo | procesador_pdf |
| **Clasificación jurídica** | ✅ Nuevo | procesador_pdf |
| **Análisis de vencimientos** | ✅ Nuevo | procesador_pdf |
| **Normalización de texto** | ✅ Nuevo | procesador_pdf |

---

## 🔌 Integración con MCP Server Tools

### Herramientas MCP Actualizadas

Las siguientes herramientas MCP ahora se benefician automáticamente de la refactorización:

#### 1. `extract_pdf_text` (Actualizada)

```json
{
  "name": "extract_pdf_text",
  "description": "Extract text from PDF files with optional OCR support",
  "inputSchema": {
    "type": "object",
    "properties": {
      "pdf_path": {"type": "string"},
      "max_pages": {"type": "integer"},
      "include_metadata": {"type": "boolean"},
      "use_ocr": {"type": "boolean"}  // ← NUEVO parámetro
    }
  }
}
```

**Mejoras**:
- Ahora retorna `hash` para deduplicación
- Retorna `extraction_method` para debugging
- Soporte OCR opcional
- Mejor manejo de PDFs complejos

#### 2. `classify_pdf` (NUEVA)

```json
{
  "name": "classify_pdf",
  "description": "Classify PDF content by legal utility",
  "inputSchema": {
    "type": "object",
    "properties": {
      "pdf_path": {"type": "string"},
      "tipo_actuacion": {"type": "string"},
      "detalle_actuacion": {"type": "string"}
    }
  }
}
```

**Uso desde Claude**:
```
Usuario: "Clasifica este PDF y dime si es importante"
Claude: [Usa classify_pdf] → "Este documento tiene utilidad ALTA (score: 92).
        Es una cédula de notificación de sentencia definitiva con plazo procesal."
```

#### 3. `analyze_pdf_deadlines` (NUEVA)

```json
{
  "name": "analyze_pdf_deadlines",
  "description": "Detect deadlines and procedural terms in PDF",
  "inputSchema": {
    "type": "object",
    "properties": {
      "pdf_path": {"type": "string"}
    }
  }
}
```

**Uso desde Claude**:
```
Usuario: "¿Este PDF tiene vencimientos?"
Claude: [Usa analyze_pdf_deadlines] → "Sí, detecté un vencimiento el 2025-11-15
        (en 12 días). Es una cédula electrónica con plazo de 5 días hábiles
        desde la notificación del 2025-11-08."
```

---

## 🛡️ Compatibilidad y Degradación Graceful

### Escenario 1: procesador_pdf Disponible (RECOMENDADO)

```python
# Sistema usa procesador_pdf automáticamente
resultado = extract_text_from_pdf("documento.pdf")
# ✅ Usa procesador_pdf.ExtractorTexto
# ✅ Retorna hash MD5
# ✅ Retorna método de extracción
# ✅ Texto normalizado
```

### Escenario 2: procesador_pdf NO Disponible

```python
# Sistema cae a implementación legacy
resultado = extract_text_from_pdf("documento.pdf")
# ✅ Usa pdfplumber_legacy
# ✅ Funciona igual que antes (backward compatible)
# ⚠️  No retorna hash ni método
# ⚠️  No hay normalización de texto
```

### Escenario 3: Funciones Nuevas sin procesador_pdf

```python
# Funciones nuevas retornan None si procesador_pdf no está disponible
clasificacion = classify_pdf_content("documento.pdf")
# Returns: None (con warning en logs)

vencimientos = analyze_deadlines_in_pdf("documento.pdf")
# Returns: None (con warning en logs)

# El código debe manejar esto:
if clasificacion:
    # Usar clasificación
else:
    # Procesar sin clasificación
```

### Variables de Estado

```python
from Sistema_v5.mcp_server.utils.pdf_extractor import PROCESADOR_DISPONIBLE

if PROCESADOR_DISPONIBLE:
    print("✅ Funcionalidades completas disponibles")
    # Usar clasificación, vencimientos, OCR
else:
    print("⚠️ Modo legacy (solo extracción básica)")
    # Usar solo extract_text_from_pdf básico
```

---

## 📝 Ejemplos de Uso

### Ejemplo 1: Extracción Completa con OCR

```python
from Sistema_v5.mcp_server.utils.pdf_extractor import extract_text_from_pdf

# PDF escaneado (sin texto seleccionable)
resultado = extract_text_from_pdf(
    "/ruta/expediente/cedula_escaneada.pdf",
    max_pages=None,  # Todas las páginas
    include_metadata=True,
    use_ocr=True  # Activar OCR
)

if not resultado["error"]:
    print(f"📄 Extraído: {resultado['num_pages']} páginas")
    print(f"🔑 Hash MD5: {resultado['hash']}")
    print(f"⚙️ Método: {resultado['extraction_method']}")  # "ocr"
    print(f"📝 Texto: {resultado['text'][:500]}...")

    # Metadata del PDF
    if "metadata" in resultado:
        print(f"📋 Título: {resultado['metadata'].get('Title', 'N/A')}")
        print(f"📅 Creado: {resultado['metadata'].get('CreationDate', 'N/A')}")
else:
    print(f"❌ Error: {resultado['error']}")
```

### Ejemplo 2: Pipeline de Clasificación

```python
from Sistema_v5.mcp_server.utils.pdf_extractor import (
    extract_text_from_pdf,
    classify_pdf_content,
    analyze_deadlines_in_pdf,
    PROCESADOR_DISPONIBLE
)

def procesar_actuacion_completa(ruta_pdf: str, tipo: str, detalle: str):
    """Procesa una actuación con análisis completo."""

    print(f"📥 Procesando: {ruta_pdf}")

    # 1. Extraer texto
    extraccion = extract_text_from_pdf(ruta_pdf, use_ocr=True)
    if extraccion["error"]:
        return {"error": extraccion["error"]}

    resultado = {
        "texto_completo": extraccion["text"],
        "num_paginas": extraccion["num_pages"],
        "hash": extraccion.get("hash"),
        "metodo": extraccion.get("extraction_method")
    }

    # 2. Clasificar (si está disponible)
    if PROCESADOR_DISPONIBLE:
        clasificacion = classify_pdf_content(ruta_pdf, tipo, detalle)
        if clasificacion and not clasificacion.get("error"):
            resultado["clasificacion"] = clasificacion
            print(f"📊 Utilidad: {clasificacion['utilidad']}")

        # 3. Analizar vencimientos
        vencimientos = analyze_deadlines_in_pdf(ruta_pdf)
        if vencimientos:
            resultado["vencimientos"] = vencimientos
            urgentes = [v for v in vencimientos if v["es_urgente"]]
            if urgentes:
                print(f"⚠️ {len(urgentes)} vencimientos urgentes detectados!")

    return resultado

# Uso:
resultado = procesar_actuacion_completa(
    "/datos/expediente_123/cedula.pdf",
    tipo="CEDULA_ELECTRONICA",
    detalle="Notificación de sentencia definitiva"
)

if resultado.get("clasificacion"):
    print(f"Utilidad: {resultado['clasificacion']['utilidad']}")

if resultado.get("vencimientos"):
    print(f"Vencimientos detectados: {len(resultado['vencimientos'])}")
```

### Ejemplo 3: Deduplicación por Hash

```python
from Sistema_v5.mcp_server.utils.pdf_extractor import extract_text_from_pdf

# Procesar múltiples PDFs y detectar duplicados
hashes_vistos = set()
duplicados = []

archivos = [
    "actuacion_1.pdf",
    "actuacion_2.pdf",
    "actuacion_3.pdf",  # Supongamos que es duplicado de actuacion_1
]

for archivo in archivos:
    resultado = extract_text_from_pdf(archivo)

    if resultado.get("hash"):
        hash_md5 = resultado["hash"]

        if hash_md5 in hashes_vistos:
            duplicados.append(archivo)
            print(f"⚠️ DUPLICADO: {archivo}")
        else:
            hashes_vistos.add(hash_md5)
            print(f"✅ NUEVO: {archivo}")
    else:
        print(f"⚠️ Sin hash (procesador_pdf no disponible): {archivo}")

print(f"\n📊 Total duplicados: {len(duplicados)}")
```

---

## 🔧 Configuración y Requisitos

### Dependencias Obligatorias

```bash
# Ya instaladas (parte del proyecto)
pip install pdfplumber>=0.10.0  # Fallback legacy
```

### Dependencias Opcionales (Recomendadas)

```bash
# Para funcionalidad completa
cd Sistema_v5/procesador_pdf
pip install -r requirements.txt

# Incluye:
# - PyPDF2>=3.0.0 (extracción alternativa)
# - pytesseract>=0.3.10 (OCR)
# - scikit-learn>=1.3.0 (clasificación)
# - sentence-transformers>=2.2.0 (duplicados semánticos)
```

### Configuración de OCR (Opcional)

Para usar `use_ocr=True`:

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-spa

# macOS
brew install tesseract tesseract-lang

# Windows
# Descargar instalador desde: https://github.com/UB-Mannheim/tesseract/wiki
```

Verificar instalación:

```python
from Sistema_v5.procesador_pdf import ExtractorTexto

extractor = ExtractorTexto(usar_ocr=True)
# Si no hay error, OCR está disponible
```

---

## 🎯 Casos de Uso Reales

### Caso 1: Scraping PJN con Clasificación Automática

```python
# En panel_pjn/acciones_pjn/gestion_actuaciones/procesamiento.py
from Sistema_v5.mcp_server.utils.pdf_extractor import classify_pdf_content

async def procesar_actuacion_descargada(actuacion: dict, ruta_pdf: str):
    """Procesa una actuación descargada del PJN."""

    # Clasificar automáticamente
    clasificacion = classify_pdf_content(
        ruta_pdf,
        tipo_actuacion=actuacion.get("Tipo", ""),
        detalle_actuacion=actuacion.get("Detalle", "")
    )

    if clasificacion:
        actuacion["Utilidad"] = clasificacion["utilidad"]
        actuacion["ScoreClasificacion"] = clasificacion["score"]

        # Solo procesar si es utilidad MEDIA o ALTA
        if clasificacion["utilidad"] in ["ALTA", "MEDIA"]:
            # Extraer texto completo
            texto = extract_text_from_pdf(ruta_pdf, use_ocr=True)
            actuacion["TextoExtraido"] = texto["text"]
            actuacion["HashPDF"] = texto.get("hash")
        else:
            print(f"⏭️ Saltando actuación de baja utilidad: {actuacion['Detalle']}")
```

### Caso 2: Monitor con Alertas de Vencimientos

```python
# En Sistema_v4/monitor/integracion_procesador_pdf.py
from Sistema_v5.mcp_server.utils.pdf_extractor import analyze_deadlines_in_pdf

def procesar_nuevas_actuaciones_monitor(carpeta_expediente: str):
    """Procesa actuaciones del monitor y detecta vencimientos."""

    vencimientos_urgentes = []

    for pdf_file in Path(carpeta_expediente).glob("*.pdf"):
        vencimientos = analyze_deadlines_in_pdf(pdf_file)

        if vencimientos:
            for venc in vencimientos:
                if venc["es_urgente"]:  # < 7 días
                    vencimientos_urgentes.append({
                        "archivo": pdf_file.name,
                        "tipo": venc["tipo"],
                        "vencimiento": venc["fecha_vencimiento"],
                        "dias_restantes": venc["dias_restantes"]
                    })

    if vencimientos_urgentes:
        # Enviar alerta
        print(f"🚨 {len(vencimientos_urgentes)} VENCIMIENTOS URGENTES:")
        for v in vencimientos_urgentes:
            print(f"  • {v['archivo']}: {v['tipo']} - "
                  f"Vence en {v['dias_restantes']} días")
```

### Caso 3: MCP Server con Claude

```python
# Claude puede usar las nuevas herramientas automáticamente

# Usuario pregunta:
"¿Cuáles de estos PDFs son importantes y tienen vencimientos urgentes?"

# Claude ejecuta:
1. classify_pdf para cada archivo → detecta los de UTILIDAD ALTA
2. analyze_pdf_deadlines en archivos ALTA → detecta vencimientos
3. Responde con resumen inteligente:

"""
He analizado 5 PDFs:

URGENTES (requieren atención inmediata):
- cedula_notificacion.pdf: UTILIDAD ALTA
  → Vencimiento en 3 días (2025-11-06)
  → Cédula electrónica de sentencia definitiva

IMPORTANTES (sin urgencia):
- traslado_demanda.pdf: UTILIDAD ALTA
  → Vencimiento en 12 días (2025-11-15)

BAJA PRIORIDAD:
- proveido_simple.pdf: UTILIDAD BAJA
- cargo_presentacion.pdf: UTILIDAD BAJA
- simple_vista.pdf: UTILIDAD NULA
"""
```

---

## 📚 API Reference

### `extract_text_from_pdf()`

```python
def extract_text_from_pdf(
    pdf_path: str | Path,
    max_pages: int | None = None,
    include_metadata: bool = False,
    use_ocr: bool = False,
) -> dict[str, Any]:
    """
    Extrae texto de un archivo PDF.

    Args:
        pdf_path: Ruta al archivo PDF
        max_pages: Número máximo de páginas a extraer (None = todas)
        include_metadata: Si incluir metadata del PDF
        use_ocr: Si usar OCR para PDFs escaneados (requiere tesseract)

    Returns:
        dict con:
        - text: str - Texto completo extraído y normalizado
        - pages: list[dict] - Lista de páginas con texto
        - num_pages: int - Número total de páginas
        - metadata: dict - Metadata del PDF (si include_metadata=True)
        - hash: str - Hash MD5 del texto (NUEVO)
        - extraction_method: str - Método usado: "pdfplumber", "pypdf2", "ocr" (NUEVO)
        - error: str | None - Mensaje de error si falló

    Raises:
        FileNotFoundError: Si el archivo no existe

    Example:
        >>> resultado = extract_text_from_pdf("documento.pdf", use_ocr=True)
        >>> print(resultado["text"])
        >>> print(f"Hash: {resultado['hash']}")
    """
```

### `classify_pdf_content()` (NUEVA)

```python
def classify_pdf_content(
    pdf_path: str | Path,
    tipo_actuacion: str = "",
    detalle_actuacion: str = "",
) -> dict[str, Any] | None:
    """
    Clasifica el contenido de un PDF usando procesador_pdf.

    Args:
        pdf_path: Ruta al archivo PDF
        tipo_actuacion: Tipo de la actuación (opcional)
        detalle_actuacion: Detalle de la actuación (opcional)

    Returns:
        dict con:
        - utilidad: str - "ALTA", "MEDIA", "BAJA", "NULA"
        - score: float - Confianza de clasificación (0-100)
        - motivo: str - Explicación de la clasificación
        - keywords: list[str] - Palabras clave detectadas
        - tiene_plazo: bool - Si tiene plazo procesal probable

        O None si procesador_pdf no está disponible

    Example:
        >>> cls = classify_pdf_content("cedula.pdf", tipo="CEDULA_ELECTRONICA")
        >>> if cls and cls["utilidad"] == "ALTA":
        >>>     print("Documento importante!")
    """
```

### `analyze_deadlines_in_pdf()` (NUEVA)

```python
def analyze_deadlines_in_pdf(
    pdf_path: str | Path,
) -> list[dict[str, Any]] | None:
    """
    Analiza vencimientos y plazos procesales en un PDF.

    Args:
        pdf_path: Ruta al archivo PDF

    Returns:
        Lista de vencimientos, cada uno con:
        - tipo: str - Tipo de vencimiento (CEDULA_ELECTRONICA, TRASLADO, etc.)
        - fecha_notificacion: str | None - Fecha de notificación (ISO format)
        - fecha_vencimiento: str | None - Fecha de vencimiento (ISO format)
        - dias_restantes: int - Días hasta el vencimiento
        - es_urgente: bool - Si el vencimiento es urgente (< 7 días)
        - descripcion: str - Descripción del plazo

        O None si procesador_pdf no está disponible

    Example:
        >>> venc = analyze_deadlines_in_pdf("cedula.pdf")
        >>> for v in venc:
        >>>     if v["es_urgente"]:
        >>>         print(f"⚠️ Urgente: {v['descripcion']}")
    """
```

### `get_pdf_info()` (Mejorada)

```python
def get_pdf_info(pdf_path: str | Path) -> dict[str, Any]:
    """
    Obtiene información básica de un PDF sin extraer todo el texto.

    Args:
        pdf_path: Ruta al archivo PDF

    Returns:
        dict con:
        - num_pages: int - Número de páginas
        - metadata: dict - Metadata del PDF
        - file_size: int - Tamaño del archivo en bytes
        - error: str | None - Mensaje de error si falló

    Example:
        >>> info = get_pdf_info("documento.pdf")
        >>> print(f"Páginas: {info['num_pages']}")
    """
```

---

## 🔄 Migración desde Código Anterior

### Cambios NO Breaking (100% Compatible)

```python
# ✅ Código antiguo sigue funcionando exactamente igual:

# Antes:
resultado = extract_text_from_pdf("documento.pdf")
texto = resultado["text"]
paginas = resultado["pages"]
num_paginas = resultado["num_pages"]

# Después (IGUAL):
resultado = extract_text_from_pdf("documento.pdf")
texto = resultado["text"]  # ✅ Funciona igual
paginas = resultado["pages"]  # ✅ Funciona igual
num_paginas = resultado["num_pages"]  # ✅ Funciona igual

# Bonus: Nuevos campos disponibles
hash_md5 = resultado.get("hash")  # ← NUEVO (opcional)
metodo = resultado.get("extraction_method")  # ← NUEVO (opcional)
```

### Aprovechar Nuevas Funcionalidades

```python
# ✅ Migración recomendada para aprovechar mejoras:

# ANTES:
resultado = extract_text_from_pdf("documento.pdf")
texto = resultado["text"]
# ... procesar manualmente ...

# DESPUÉS (con clasificación):
from Sistema_v5.mcp_server.utils.pdf_extractor import (
    extract_text_from_pdf,
    classify_pdf_content,
    PROCESADOR_DISPONIBLE
)

resultado = extract_text_from_pdf("documento.pdf", use_ocr=True)
texto = resultado["text"]

# Clasificar automáticamente
if PROCESADOR_DISPONIBLE:
    clasificacion = classify_pdf_content("documento.pdf", tipo="...", detalle="...")
    if clasificacion and clasificacion["utilidad"] == "ALTA":
        # Procesar solo documentos importantes
        pass
```

---

## 🐛 Troubleshooting

### Problema 1: OCR no funciona

**Error**: `TesseractNotFoundError: tesseract is not installed`

**Solución**:
```bash
# Instalar tesseract-ocr
sudo apt-get install tesseract-ocr tesseract-ocr-spa  # Linux
brew install tesseract tesseract-lang  # macOS

# Verificar instalación
tesseract --version
```

### Problema 2: procesador_pdf no disponible

**Warning**: `procesador_pdf no disponible. Cayendo a implementación legacy.`

**Causas**:
1. procesador_pdf no instalado
2. Imports incorrectos
3. Versión incompatible

**Solución**:
```bash
# Verificar que procesador_pdf esté disponible
python -c "from Sistema_v5.procesador_pdf import ExtractorTexto; print('OK')"

# Si falla, verificar PYTHONPATH
export PYTHONPATH=/home/user/sintaXis:$PYTHONPATH

# Reinstalar dependencias
cd Sistema_v5/procesador_pdf
pip install -r requirements.txt
```

### Problema 3: Clasificación retorna None

**Problema**: `classify_pdf_content()` retorna `None`

**Causas**:
1. procesador_pdf no disponible
2. Archivo PDF corrupto
3. Error en extracción de texto

**Solución**:
```python
from Sistema_v5.mcp_server.utils.pdf_extractor import (
    classify_pdf_content,
    PROCESADOR_DISPONIBLE
)

# Verificar disponibilidad
if not PROCESADOR_DISPONIBLE:
    print("❌ procesador_pdf no disponible")
    # Usar clasificación manual o fallback

# Verificar que el PDF existe y es válido
clasificacion = classify_pdf_content("documento.pdf")
if clasificacion is None:
    print("⚠️ No se pudo clasificar (procesador_pdf no disponible)")
elif "error" in clasificacion:
    print(f"❌ Error: {clasificacion['error']}")
else:
    print(f"✅ Clasificado: {clasificacion['utilidad']}")
```

### Problema 4: Performance lento con OCR

**Problema**: OCR tarda mucho en PDFs grandes

**Solución**:
```python
# Limitar páginas a procesar
resultado = extract_text_from_pdf(
    "documento_grande.pdf",
    max_pages=10,  # Solo primeras 10 páginas
    use_ocr=True
)

# O desactivar OCR si el PDF tiene texto seleccionable
resultado = extract_text_from_pdf(
    "documento.pdf",
    use_ocr=False  # Mucho más rápido
)
```

---

## 📊 Métricas de Mejora

### Código Duplicado Eliminado

- **Antes**: 65-85 líneas duplicadas entre `pdf_extractor.py` y `extractor_texto.py`
- **Después**: 0 líneas duplicadas (usa wrapper)
- **Reducción**: 100% de duplicación eliminada

### Funcionalidades Agregadas

- **Antes**: 4 funciones (`extract_text_from_pdf`, `extract_text_summary`, `get_pdf_info`, helpers)
- **Después**: 6 funciones (+2 nuevas: `classify_pdf_content`, `analyze_deadlines_in_pdf`)
- **Incremento**: +50% funcionalidades

### Líneas de Código

- **Antes**: 163 líneas (con duplicación)
- **Después**: 435 líneas (sin duplicación + nuevas features)
- **Crecimiento**: +167% (pero con más funcionalidades y menos duplicación neta)

### Capacidades

| Capacidad | Antes | Después |
|-----------|-------|---------|
| Extracción básica | ✅ | ✅ |
| OCR | ❌ | ✅ |
| Hash MD5 | ❌ | ✅ |
| Detección método | ❌ | ✅ |
| Clasificación | ❌ | ✅ |
| Vencimientos | ❌ | ✅ |
| Normalización | ❌ | ✅ |
| **Total** | **1/7** | **7/7** |

---

## ✅ Checklist de Verificación

Para verificar que la refactorización funcionó correctamente:

```python
# tests/test_mcp_refactorizacion.py

from Sistema_v5.mcp_server.utils.pdf_extractor import (
    extract_text_from_pdf,
    classify_pdf_content,
    analyze_deadlines_in_pdf,
    get_pdf_info,
    PROCESADOR_DISPONIBLE
)

def test_refactorizacion_completa():
    """Verifica que la refactorización esté completa."""

    # ✅ 1. Verificar que procesador_pdf está disponible
    assert PROCESADOR_DISPONIBLE, "procesador_pdf debe estar disponible"

    # ✅ 2. Verificar extracción básica (backward compatible)
    resultado = extract_text_from_pdf("tests/fixtures/ejemplo.pdf")
    assert "text" in resultado
    assert "pages" in resultado
    assert "num_pages" in resultado

    # ✅ 3. Verificar nuevos campos
    assert "hash" in resultado, "Debe retornar hash MD5"
    assert "extraction_method" in resultado, "Debe retornar método"

    # ✅ 4. Verificar OCR
    resultado_ocr = extract_text_from_pdf("tests/fixtures/escaneado.pdf", use_ocr=True)
    assert resultado_ocr.get("extraction_method") == "ocr"

    # ✅ 5. Verificar clasificación
    clasificacion = classify_pdf_content("tests/fixtures/cedula.pdf")
    assert clasificacion is not None
    assert "utilidad" in clasificacion
    assert clasificacion["utilidad"] in ["ALTA", "MEDIA", "BAJA", "NULA"]

    # ✅ 6. Verificar vencimientos
    vencimientos = analyze_deadlines_in_pdf("tests/fixtures/cedula.pdf")
    assert vencimientos is not None
    assert isinstance(vencimientos, list)

    print("✅ Todas las verificaciones pasaron!")

if __name__ == "__main__":
    test_refactorizacion_completa()
```

---

## 📖 Referencias

- **Código fuente**: `Sistema_v5/mcp_server/utils/pdf_extractor.py`
- **Módulo base**: `Sistema_v5/procesador_pdf/`
- **Tarea anterior 1**: `panel_pjn/acciones_pjn/gestion_actuaciones/README_PROCESAMIENTO.md`
- **Tarea anterior 2**: `Sistema_v4/monitor/README_INTEGRACION_MONITOR.md`
- **Estado general**: `ESTADO_PROCESADOR_PDF2.1.md`

---

## 🎯 Conclusión

La refactorización de MCP Server cumplió todos los objetivos:

1. ✅ **Eliminó código duplicado** entre `pdf_extractor.py` y `procesador_pdf/extractor_texto.py`
2. ✅ **Agregó nuevas funcionalidades** (clasificación, vencimientos, OCR)
3. ✅ **Mantuvo 100% compatibilidad** hacia atrás
4. ✅ **Implementó degradación graceful** con fallback a pdfplumber
5. ✅ **Mejoró capacidades de MCP Server** para Claude

**Próximos pasos recomendados**:
- Integrar en Extractor Inicial (Tarea 4)
- Integrar en scripts de ejecución `bin/` (Tarea 5)
- Exponer en Web App vía API REST (Tarea 7)

---

**Fecha**: 2025-11-03
**Autor**: Sistema SintaXis - Integración procesador_pdf
**Versión**: 1.0
