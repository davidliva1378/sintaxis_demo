perasdfasd# Plan de Implementación: Procesamiento Completo de Expedientes
## Migración de Sistema_v5.1.1 a Sistema_v6

**Fecha:** 2025-01-11
**Rama origen:** producción_v5.1.1
**Rama destino:** sintaxis_parcial2
**Autor:** Claude Code

---

## 📋 Tabla de Contenidos

1. [Contexto del Proyecto](#contexto-del-proyecto)
2. [Investigación Realizada](#investigación-realizada)
3. [Arquitectura de Solución](#arquitectura-de-solución)
4. [Tareas de Implementación](#tareas-de-implementación)
5. [Comandos Git Seguros](#comandos-git-seguros)
6. [Checklist de Verificación](#checklist-de-verificación)
7. [Estimaciones](#estimaciones)
8. [Riesgos y Mitigaciones](#riesgos-y-mitigaciones)
9. [Referencias](#referencias)

---

## 🎯 Contexto del Proyecto

### Estado Actual del Sistema de Extracción Masiva

**✅ Funcionalidades Implementadas:**
- Extracción del listado completo de expedientes desde el PJN
- Filtrado dinámico (Dependencia, Situación, Fecha, Texto)
- Paginación (50 expedientes por página)
- Selección de expedientes (individual, página, todos filtrados)
- Interfaz de usuario con maximizar/minimizar
- Progreso en tiempo real con polling

**❌ Funcionalidad Faltante (CRÍTICA):**
- Procesamiento individual de expedientes seleccionados
- Extracción de actuaciones (actuales + históricas)
- Descarga de documentos adjuntos (PDFs)
- Guardado en estructura de directorios
- Actualización incremental (solo nuevas actuaciones)
- Clasificación inteligente por utilidad jurídica

**🔧 Implementación Actual:**
El archivo `Sistema_v6/extraccion_masiva/gestor_batch.py` tiene un **PLACEHOLDER** en la función `_procesar_expediente()` (líneas 207-232) que solo simula el procesamiento con un `sleep` aleatorio.

### Objetivo de Este Plan

Implementar el procesamiento completo de expedientes reutilizando el código **probado y funcional** de la rama `producción_v5.1.1`, que tiene toda la funcionalidad operando en producción.

---

## 🔍 Investigación Realizada

### Archivos Encontrados en Sistema_v5/pjn/ (producción_v5.1.1)

#### Módulo de Scraping
```
Sistema_v5/pjn/scraping/
├── expedientes.py          # Extracción de listados de expedientes
├── actuaciones.py          # ⭐ Extracción de actuaciones completas
├── actuaciones_utils.py    # ⭐ Utilidades para actuaciones
├── entradas.py             # Extracción de entradas
├── base.py                 # Funciones base de scraping
├── pagination.py           # Estrategias de paginación
└── session_manager.py      # Gestión de sesiones
```

#### Módulo de Parsers
```
Sistema_v5/pjn/parsers/
├── expedientes_parser.py   # Parser de expedientes
├── actuaciones_parser.py   # ⭐ Parser de actuaciones
└── entradas_parser.py      # Parser de entradas
```

#### Módulo de Persistencia
```
Sistema_v5/pjn/persistence/
└── actuaciones.py          # ⭐ Carga/guardado de actuaciones
```

#### Módulo de Servicios
```
Sistema_v5/pjn/services/
├── actuaciones.py          # ⭐ Coordinador de alto nivel
└── gui_monitor_adapter.py  # Adaptador para GUI
```

#### Gestor de Directorios
```
Sistema_v5/gestor_directorios/
├── expedientes.py          # ⭐ Gestión de estructura de archivos
├── archivos_usuario.py     # ⭐ Archivos del usuario
└── directorios_externos.py # Asociación de directorios externos
```

### Funciones Clave Disponibles en v5.1.1

#### 1. `scraping/actuaciones.py`

```python
async def extraer_actuaciones_completas(
    page_expediente: Page,
    expediente_datos: dict,
    incluir_historicas: bool = True,
    directorio_base: str = "Actuaciones"
) -> tuple[list[Actuacion], list[Actuacion], str | None]
```
**Qué hace:**
- Extrae actuaciones actuales de todas las páginas
- Extrae actuaciones históricas si `incluir_historicas=True`
- Guarda JSON con estructura v1.1
- Detecta duplicados por hash
- Retorna: (actuaciones_actuales, actuaciones_historicas, error)

```python
async def actualizar_actuaciones_desde_json(
    page_expediente: Page,
    expediente_datos: dict,
    ruta_json_existente: str
) -> tuple[int, dict | None, str | None]
```
**Qué hace:**
- Carga JSON existente
- Extrae solo actuaciones nuevas (por hash)
- Actualiza JSON sin duplicar
- Retorna: (cantidad_agregadas, estructura_actualizada, error)

```python
async def descargar_archivos_de_json(
    page: Page,
    carpeta_json: str,
    carpeta_adjuntos: str
) -> dict
```
**Qué hace:**
- Lee JSON de actuaciones
- Descarga todos los archivos adjuntos
- Marca actuaciones como "Descargado" en JSON
- Retorna: estadísticas de descarga

#### 2. `services/actuaciones.py`

```python
async def procesar_actuaciones_expediente(
    datos_expediente: dict[str, Any],
    *,
    descargar_adjuntos: bool = False
) -> tuple[Path | None, ResultadoProcesamiento]
```
**Qué hace (COORDINADOR PRINCIPAL):**
1. Crea estructura de directorios con `GestorDirectoriosExpedientes`
2. Extrae actuaciones actuales + históricas
3. Guarda JSON en carpeta de actuaciones
4. Descarga adjuntos si `descargar_adjuntos=True`
5. Actualiza manifest.json con metadata
6. Retorna: (ruta_json, resultado_con_estadisticas)

**Campos de `ResultadoProcesamiento`:**
```python
@dataclass
class ResultadoProcesamiento:
    exito: bool
    total_actuaciones: int
    archivos_descargados: int
    errores: list[str]
    tiempo_procesamiento: float
```

#### 3. `persistence/actuaciones.py`

```python
def cargar_actuaciones_json(ruta_json: str) -> dict
def guardar_actuaciones_json(
    archivo: ActuacionesArchivo,
    directorio_base: str,
    numero_expediente: str
) -> str
def actualizar_descargados(
    ruta_json: str,
    actuaciones_actualizadas: list[Actuacion]
) -> None
```

#### 4. `gestor_directorios/expedientes.py`

```python
class GestorDirectoriosExpedientes:
    def __init__(self, directorio_base: str):
        """Inicializa gestor con directorio base de expedientes."""

    def crear_estructura_expediente(
        self, numero_expediente: str
    ) -> dict[str, Path]:
        """
        Crea estructura de directorios para un expediente.

        Returns:
            {
                "raiz": Path,
                "actuaciones": Path,
                "documentos": Path,
                "adjuntos": Path,
                "procesados": Path,
                "reportes": Path,
                "temporal": Path
            }
        """

    def obtener_ruta_expediente(self, numero: str) -> Path:
    def obtener_ruta_actuaciones(self, numero: str) -> Path:
    def obtener_ruta_adjuntos(self, numero: str) -> Path:
    def listar_expedientes(self) -> list[str]:
    def expediente_existe(self, numero: str) -> bool:
```

### Comparación: v5.1.1 vs v6 vs v4

| Funcionalidad | v5.1.1 | v6 | v4 |
|--------------|--------|----|----|
| Extracción de expedientes | ✅ Completo | ✅ Básico | ❌ |
| Extracción de actuaciones | ✅ Completo | ❌ | ❌ |
| Actualización incremental | ✅ | ❌ | ❌ |
| Descarga de adjuntos | ✅ | ❌ | ❌ |
| Gestión de directorios | ✅ Completo | ⚠️ Diferente | ❌ |
| Persistencia de actuaciones | ✅ | ❌ | ❌ |
| Servicio coordinador | ✅ | ⚠️ Parcial | ❌ |
| Clasificación inteligente | ✅ | ⚠️ Parcial | ❌ |

**Conclusión:** Sistema_v5.1.1 tiene funcionalidad crítica que NO existe en v6 ni v4.

---

## 🏗️ Arquitectura de Solución

### Flujo de Procesamiento Completo

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USUARIO SELECCIONA EXPEDIENTES                          │
│    - Filtra listado extraído                                │
│    - Marca checkboxes de expedientes deseados               │
│    - Activa/desactiva "Procesar con PDF"                    │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    v
┌─────────────────────────────────────────────────────────────┐
│ 2. FRONTEND ENVÍA REQUEST                                   │
│    POST /api/v1/extraccion-masiva/procesar-seleccionados   │
│    {                                                         │
│      "numeros_expedientes": ["FPA 001/2024", ...],         │
│      "config": {                                            │
│        "procesar_con_pdf": true                            │
│      }                                                       │
│    }                                                         │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    v
┌─────────────────────────────────────────────────────────────┐
│ 3. BACKEND CREA GESTOR BATCH                                │
│    - Recibe configuración con procesar_con_pdf              │
│    - Crea sesión de procesamiento                           │
│    - Inicializa GestorBatch con config y repositorio        │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    v
┌─────────────────────────────────────────────────────────────┐
│ 4. PROCESAMIENTO POR EXPEDIENTE (loop)                      │
│                                                              │
│  Para cada expediente:                                       │
│    ┌──────────────────────────────────────────────────┐    │
│    │ 4.1 Buscar en PJN                                 │    │
│    │     buscar_expediente_por_numero()                │    │
│    └────────────────┬─────────────────────────────────┘    │
│                     │                                        │
│                     v                                        │
│    ┌──────────────────────────────────────────────────┐    │
│    │ 4.2 Extraer Metadata                             │    │
│    │     extraer_datos_expediente()                    │    │
│    └────────────────┬─────────────────────────────────┘    │
│                     │                                        │
│                     v                                        │
│    ┌──────────────────────────────────────────────────┐    │
│    │ 4.3 Procesar Actuaciones                         │    │
│    │     procesar_actuaciones_expediente()            │    │
│    │     ├─ Crear directorios                         │    │
│    │     ├─ Extraer actuaciones actuales              │    │
│    │     ├─ Extraer actuaciones históricas            │    │
│    │     ├─ Guardar JSON                               │    │
│    │     └─ Descargar PDFs (si procesar_con_pdf)     │    │
│    └────────────────┬─────────────────────────────────┘    │
│                     │                                        │
│                     v                                        │
│    ┌──────────────────────────────────────────────────┐    │
│    │ 4.4 Clasificar (opcional)                        │    │
│    │     FiltroContenidoInteligente                    │    │
│    └────────────────┬─────────────────────────────────┘    │
│                     │                                        │
│                     v                                        │
│    ┌──────────────────────────────────────────────────┐    │
│    │ 4.5 Guardar en Repositorio                       │    │
│    │     expediente_repository.save()                  │    │
│    └──────────────────────────────────────────────────┘    │
│                                                              │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    v
┌─────────────────────────────────────────────────────────────┐
│ 5. RETORNAR RESUMEN                                         │
│    {                                                         │
│      "session_id": "...",                                   │
│      "resumen": {                                           │
│        "total": 10,                                         │
│        "exitosos": 8,                                       │
│        "errores": 2,                                        │
│        "tiempo_total": 125.3                                │
│      }                                                       │
│    }                                                         │
└─────────────────────────────────────────────────────────────┘
```

### Estructura de Directorios Resultante

```
Sistema_v6/data/expedientes/
└── FPA_001234_2024/                    # Número sanitizado
    ├── manifest.json                   # Metadata del expediente
    ├── actuaciones/
    │   └── actuaciones-FPA_001234_2024.json  # Actuaciones completas
    ├── documentos/                     # Documentos principales (futuro)
    ├── adjuntos/                       # Solo si procesar_con_pdf=True
    │   └── adjuntos/
    │       ├── 20250110_RESOLUCION_abc123.pdf
    │       ├── 20250109_SENTENCIA_def456.pdf
    │       └── ...
    ├── procesados/                     # Datos procesados (clasificación)
    ├── reportes/                       # Reportes generados
    └── temporal/                       # Archivos temporales
```

### Formato JSON de Actuaciones (v1.1)

```json
{
  "Expediente": {
    "numero": "FPA 001234/2024",
    "caratula": "EJEMPLO S/ ACCIÓN DE AMPARO",
    "dependencia": "JUZGADO FEDERAL DE PARANÁ 2",
    "jurisdiccion": "PARANA",
    "situacion": "EN LETRA",
    "version_formato": "1.1",
    "fecha_extraccion": "2025-01-11 14:30:00",
    "incluye_historicas": true,
    "total_actuales": 45,
    "total_historicas": 12,
    "total_actuaciones": 57,
    "total_archivos_con_enlace": 23,
    "Cantidad de Archivos Descargados": 23,
    "descargas_pendientes": 0,
    "ultimo_hash_actual": "abc123def456",
    "ultima_fecha_actual": "2025-01-10"
  },
  "Actuaciones": [
    {
      "Indice": 1,
      "Oficina": "JUZGADO",
      "OficinaCompleta": "JUZGADO FEDERAL DE PARANÁ 2 - SECRETARIA CIVIL Y COMERCIAL 1",
      "Fecha": "10/01/2025",
      "Tipo": "RESOLUCION",
      "Detalle": "PROVIDENCIA - SE HACE LUGAR A LO SOLICITADO",
      "Foja": "123",
      "Archivo": "https://scw.pjn.gov.ar/scw/...",
      "NombreArchivo": "20250110_RESOLUCION_abc123.pdf",
      "TieneArchivo": true,
      "TipoArchivo": "pdf",
      "Hash": "abc123def456",
      "ExtraidaEn": "2025-01-11 14:30:15",
      "EsHistorica": false,
      "Descargado": true
    },
    {
      "Indice": 2,
      "Oficina": "JUZGADO",
      "Fecha": "09/01/2025",
      "Tipo": "ESCRITO",
      "Detalle": "PRESENTACIÓN DE DOCUMENTACIÓN",
      "Foja": "120",
      "Archivo": "",
      "NombreArchivo": "",
      "TieneArchivo": false,
      "TipoArchivo": "",
      "Hash": "def456ghi789",
      "ExtraidaEn": "2025-01-11 14:30:20",
      "EsHistorica": false,
      "Descargado": false
    }
  ]
}
```

---

## ✅ Tareas de Implementación

### FASE 1: MIGRACIÓN DE CÓDIGO CORE (1-2 horas)

#### Tarea 1.1: Crear directorios necesarios

```bash
mkdir -p Sistema_v6/pjn/scraping
mkdir -p Sistema_v6/pjn/parsers
mkdir -p Sistema_v6/pjn/persistence
mkdir -p Sistema_v6/pjn/services
mkdir -p Sistema_v6/gestor_directorios
```

**Verificación:** Los directorios existen y son escribibles.

---

#### Tarea 1.2: Portar módulo de actuaciones (scraping)

**Archivos a portar:**
```bash
git show producción_v5.1.1:Sistema_v5/pjn/scraping/actuaciones.py > Sistema_v6/pjn/scraping/actuaciones.py
git show producción_v5.1.1:Sistema_v5/pjn/scraping/actuaciones_utils.py > Sistema_v6/pjn/scraping/actuaciones_utils.py
```

**Funciones que obtenemos:**
- `extraer_actuaciones_completas()` - Extracción completa
- `actualizar_actuaciones_desde_json()` - Actualización incremental
- `descargar_archivos_de_json()` - Descarga de adjuntos
- Funciones auxiliares en `actuaciones_utils.py`

**Verificación:**
```bash
ls -lh Sistema_v6/pjn/scraping/actuaciones.py
ls -lh Sistema_v6/pjn/scraping/actuaciones_utils.py
```

---

#### Tarea 1.3: Portar parser de actuaciones

**Archivo a portar:**
```bash
git show producción_v5.1.1:Sistema_v5/pjn/parsers/actuaciones_parser.py > Sistema_v6/pjn/parsers/actuaciones_parser.py
```

**Funciones que obtenemos:**
- Parseo de tabla de actuaciones
- Extracción de campos de cada fila
- Detección de enlaces a archivos

**Verificación:**
```bash
ls -lh Sistema_v6/pjn/parsers/actuaciones_parser.py
```

---

#### Tarea 1.4: Portar módulo de persistencia

**Archivo a portar:**
```bash
git show producción_v5.1.1:Sistema_v5/pjn/persistence/actuaciones.py > Sistema_v6/pjn/persistence/actuaciones.py
```

**Funciones que obtenemos:**
- `cargar_actuaciones_json()`
- `guardar_actuaciones_json()`
- `actualizar_descargados()`
- `listar_archivos_actuaciones()`

**Verificación:**
```bash
ls -lh Sistema_v6/pjn/persistence/actuaciones.py
```

---

#### Tarea 1.5: Portar servicio coordinador

**Archivo a portar:**
```bash
git show producción_v5.1.1:Sistema_v5/pjn/services/actuaciones.py > Sistema_v6/pjn/services/actuaciones.py
```

**Función principal:**
- `procesar_actuaciones_expediente()` - Coordinador de alto nivel

**Verificación:**
```bash
ls -lh Sistema_v6/pjn/services/actuaciones.py
```

---

#### Tarea 1.6: Portar gestor de directorios

**Archivos a portar:**
```bash
git show producción_v5.1.1:Sistema_v5/gestor_directorios/expedientes.py > Sistema_v6/gestor_directorios/expedientes.py
git show producción_v5.1.1:Sistema_v5/gestor_directorios/archivos_usuario.py > Sistema_v6/gestor_directorios/archivos_usuario.py
```

**Clases que obtenemos:**
- `GestorDirectoriosExpedientes` - Creación de estructura
- `GestorArchivosUsuario` - Gestión de archivos del usuario

**Verificación:**
```bash
ls -lh Sistema_v6/gestor_directorios/expedientes.py
ls -lh Sistema_v6/gestor_directorios/archivos_usuario.py
```

---

#### Tarea 1.7: Verificar modelos de datos

**Archivo a revisar:**
```bash
git show producción_v5.1.1:Sistema_v5/pjn/models/__init__.py
```

**Verificar que existan en Sistema_v6/pjn/models/__init__.py:**
- `Actuacion` (dataclass o Pydantic model)
- `ActuacionesArchivo` (estructura del JSON)
- `ResultadoProcesamiento` (resultado de procesamiento)
- `ExpedienteResumen` (ya existe)

**Si faltan, portar:**
```bash
git show producción_v5.1.1:Sistema_v5/pjn/models/__init__.py >> Sistema_v6/pjn/models/__init__.py
```

**Verificación:** Revisar archivo y verificar que los modelos estén definidos.

---

### FASE 2: ADAPTACIÓN A SISTEMA_V6 (30-45 min)

#### Tarea 2.1: Actualizar imports en archivos portados

**Para cada archivo portado en Fase 1:**

1. `Sistema_v6/pjn/scraping/actuaciones.py`
2. `Sistema_v6/pjn/scraping/actuaciones_utils.py`
3. `Sistema_v6/pjn/parsers/actuaciones_parser.py`
4. `Sistema_v6/pjn/persistence/actuaciones.py`
5. `Sistema_v6/pjn/services/actuaciones.py`
6. `Sistema_v6/gestor_directorios/expedientes.py`
7. `Sistema_v6/gestor_directorios/archivos_usuario.py`

**Buscar y reemplazar:**
```
from Sistema_v5.pjn        → from Sistema_v6.pjn
from Sistema_v5.gestor_directorios  → from Sistema_v6.gestor_directorios
```

**Comando útil (por archivo):**
```bash
sed -i '' 's/from Sistema_v5/from Sistema_v6/g' Sistema_v6/pjn/scraping/actuaciones.py
```

**Verificación:** Buscar que no quede ningún `Sistema_v5`:
```bash
grep -r "Sistema_v5" Sistema_v6/pjn/scraping/actuaciones.py
```

---

#### Tarea 2.2: Verificar compatibilidad de Playwright

**Verificar versión en v5.1.1:**
```bash
git show producción_v5.1.1:requirements.txt | grep playwright
```

**Verificar versión en v6:**
```bash
grep playwright Sistema_v6/requirements.txt
```

**Si hay diferencia significativa:** Actualizar requirements.txt de v6 o adaptar código.

---

#### Tarea 2.3: Adaptar configuración

**Archivo de configuración v5:**
```bash
git show producción_v5.1.1:Sistema_v5/pjn/config.py
```

**Archivo de configuración v6:**
```
Sistema_v6/pjn/config.py
```

**Verificar compatibilidad de:**
- Timeouts
- Selectores CSS
- URLs del PJN
- Paths de directorios

**Adaptar si es necesario.**

---

#### Tarea 2.4: Verificar sistema de logging

**Buscar en archivos portados:**
```bash
grep -n "logger\." Sistema_v6/pjn/scraping/actuaciones.py
```

**Si usa logging diferente a v6:** Adaptar a sistema de logging de v6.

---

### FASE 3: IMPLEMENTACIÓN EN GESTOR_BATCH (1 hora)

#### Tarea 3.1: Actualizar ConfigExtraccionMasiva

**Archivo:** `Sistema_v6/extraccion_masiva/models.py`

**Agregar campos nuevos:**

```python
@dataclass
class ConfigExtraccionMasiva:
    """Configuración para la extracción masiva."""
    headless: bool = True
    umbral_errores: int = 10
    timeout_pagina: int = 30000
    max_reintentos: int = 3
    procesar_con_pdf: bool = False      # ← NUEVO
    incluir_historicas: bool = True     # ← NUEVO
    min_utilidad: str = "MEDIA"         # ← NUEVO (para clasificador)
    directorio_base: str = "./Sistema_v6/data/expedientes"  # ← NUEVO

    def to_dict(self) -> Dict:
        return {
            "headless": self.headless,
            "umbral_errores": self.umbral_errores,
            "timeout_pagina": self.timeout_pagina,
            "max_reintentos": self.max_reintentos,
            "procesar_con_pdf": self.procesar_con_pdf,           # ← NUEVO
            "incluir_historicas": self.incluir_historicas,       # ← NUEVO
            "min_utilidad": self.min_utilidad,                   # ← NUEVO
            "directorio_base": self.directorio_base              # ← NUEVO
        }
```

**Verificación:** Verificar que el modelo se serializa correctamente.

---

#### Tarea 3.2: Implementar _procesar_expediente() completo

**Archivo:** `Sistema_v6/extraccion_masiva/gestor_batch.py`

**Ubicación:** Reemplazar función existente (líneas 207-232)

**Código completo:**

```python
async def _procesar_expediente(
    self, page: Page, numero: str
) -> Optional[Dict]:
    """
    Procesa un expediente individual.

    Flujo:
    1. Buscar expediente por número en PJN
    2. Extraer datos del expediente (metadata)
    3. Procesar actuaciones usando servicio coordinador de v5
    4. Descargar adjuntos si procesar_con_pdf=True
    5. Clasificar actuaciones (opcional)
    6. Guardar en repositorio

    Args:
        page: Página de Playwright
        numero: Número de expediente (ej: "FPA 001234/2024")

    Returns:
        Dict con información del procesamiento o None si falla
    """
    from Sistema_v6.pjn.scraping.expedientes import (
        buscar_expediente_por_numero,
        extraer_datos_expediente
    )
    from Sistema_v6.pjn.services.actuaciones import procesar_actuaciones_expediente

    try:
        # ==================================================================
        # PASO 1: Buscar expediente en PJN
        # ==================================================================
        print(f"🔍 Buscando expediente: {numero}")

        # Parsear número para extraer año
        # Formatos soportados: "FPA 001234/2024", "001234/2024", "001234/2024/I"
        partes = numero.replace("FPA", "").strip().split('/')
        anio = partes[-1] if len(partes) > 1 else None

        # Normalizar año (tomar primeros 4 dígitos)
        if anio and len(anio) > 4:
            anio = anio[:4]

        exito, motivo = await buscar_expediente_por_numero(page, numero, anio)

        if not exito:
            print(f"❌ Expediente no encontrado: {numero} - {motivo}")
            return None

        print(f"✅ Expediente encontrado: {numero}")

        # ==================================================================
        # PASO 2: Extraer metadata del expediente
        # ==================================================================
        datos_expediente = await extraer_datos_expediente(page)

        if not datos_expediente:
            print(f"❌ No se pudieron extraer datos: {numero}")
            return None

        print(f"📋 Metadata extraída: {datos_expediente.get('caratula', '')[:50]}...")

        # ==================================================================
        # PASO 3: Procesar actuaciones con servicio coordinador
        # ==================================================================
        print(f"📥 Extrayendo actuaciones de {numero}...")

        # Agregar directorio_base a datos_expediente si no existe
        datos_expediente["directorio_base"] = self.config.directorio_base

        ruta_json, resultado = await procesar_actuaciones_expediente(
            datos_expediente,
            descargar_adjuntos=self.config.procesar_con_pdf
        )

        if not resultado.exito:
            print(f"❌ Error procesando actuaciones: {', '.join(resultado.errores)}")
            return None

        print(f"✅ Actuaciones extraídas: {resultado.total_actuaciones}")

        if self.config.procesar_con_pdf:
            print(f"📎 Archivos descargados: {resultado.archivos_descargados}")

        # ==================================================================
        # PASO 4: Clasificación inteligente (opcional)
        # ==================================================================
        actuaciones_clasificadas = None
        if self.config.procesar_con_pdf and ruta_json:
            try:
                from Sistema_v5.generador_documentos.integracion_procesador import (
                    FiltroContenidoInteligente
                )
                from Sistema_v6.pjn.persistence.actuaciones import cargar_actuaciones_json

                print(f"🧠 Clasificando actuaciones por utilidad jurídica...")

                # Cargar actuaciones desde JSON
                datos_actuaciones = cargar_actuaciones_json(str(ruta_json))
                actuaciones = datos_actuaciones.get("Actuaciones", [])

                # Aplicar filtro
                filtro = FiltroContenidoInteligente(
                    min_utilidad=self.config.min_utilidad,
                    incluir_vencimientos=True,
                    ordenar_por_prioridad=True
                )

                actuaciones_clasificadas = filtro.filtrar_actuaciones(
                    actuaciones,
                    incluir_estadisticas=True
                )

                print(f"📊 Clasificación completada: {len(actuaciones_clasificadas)} actuaciones relevantes")

            except Exception as e:
                print(f"⚠️ Error en clasificación (no crítico): {e}")

        # ==================================================================
        # PASO 5: Guardar en repositorio (si está disponible)
        # ==================================================================
        if self.expediente_repository:
            try:
                # TODO: Convertir a modelo de dominio y guardar
                # expediente_dominio = ExpedienteDominio(...)
                # self.expediente_repository.save(expediente_dominio)
                pass
            except Exception as e:
                print(f"⚠️ Error guardando en repositorio (no crítico): {e}")

        # ==================================================================
        # RETORNAR RESULTADO
        # ==================================================================
        return {
            "numero": numero,
            "caratula": datos_expediente.get("caratula", ""),
            "ruta_json": str(ruta_json) if ruta_json else None,
            "total_actuaciones": resultado.total_actuaciones,
            "archivos_descargados": resultado.archivos_descargados,
            "tiempo_procesamiento": resultado.tiempo_procesamiento,
            "actuaciones_clasificadas": len(actuaciones_clasificadas) if actuaciones_clasificadas else 0
        }

    except Exception as e:
        print(f"❌ Error procesando expediente {numero}: {e}")
        import traceback
        traceback.print_exc()
        return None
```

**Verificación:** El código compila sin errores de sintaxis.

---

#### Tarea 3.3: Agregar imports necesarios al inicio del archivo

**Archivo:** `Sistema_v6/extraccion_masiva/gestor_batch.py`

**Agregar al inicio (después de imports existentes):**

```python
from pathlib import Path
from typing import Optional, Dict, List
from playwright.async_api import Page

# Imports de módulos portados
from Sistema_v6.pjn.scraping.expedientes import (
    buscar_expediente_por_numero,
    extraer_datos_expediente
)
from Sistema_v6.pjn.services.actuaciones import procesar_actuaciones_expediente
from Sistema_v6.pjn.persistence.actuaciones import cargar_actuaciones_json
```

---

### FASE 4: CONEXIÓN FRONTEND-BACKEND (15 min)

#### Tarea 4.1: Enviar procesarConPDF desde frontend

**Archivo:** `Sistema_v6/frontend/src/components/expedientes/ExtraccionMasivaDialog.tsx`

**Ubicación:** En función `handleConfirmar()` (buscar por "handleConfirmar")

**Modificar para incluir config:**

```typescript
const handleConfirmar = async () => {
  const numeros = Array.from(expedientesSeleccionados)

  // Crear configuración que incluya procesarConPDF
  const configProcesamiento = {
    procesar_con_pdf: procesarConPDF,
    incluir_historicas: true,
    min_utilidad: "MEDIA"
  }

  try {
    await procesarExpedientesSeleccionados(numeros, configProcesamiento)
    onClose()
    if (onSuccess) {
      onSuccess(expedientesFiltrados)
    }
  } catch (error) {
    console.error('Error procesando expedientes:', error)
  }
}
```

**Verificación:** Frontend compila sin errores TypeScript.

---

#### Tarea 4.2: Actualizar store para enviar config

**Archivo:** `Sistema_v6/frontend/src/stores/expedientesStore.ts`

**Buscar función:** `procesarExpedientesSeleccionados`

**Actualizar firma:**

```typescript
procesarExpedientesSeleccionados: async (
  numeros: string[],
  config?: {
    procesar_con_pdf?: boolean
    incluir_historicas?: boolean
    min_utilidad?: string
  }
) => {
  // ... código existente ...

  const response = await fetch('/api/v1/extraccion-masiva/procesar-seleccionados', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      numeros_expedientes: numeros,
      config: config || {}  // ← Agregar config
    })
  })

  // ... resto del código ...
}
```

---

#### Tarea 4.3: Actualizar modelo de request en backend

**Archivo:** `Sistema_v6/presentation/api/rest/routers/extraccion_masiva.py`

**Buscar:** `class ConfigExtraccionRequest`

**Actualizar modelo:**

```python
class ConfigExtraccionRequest(BaseModel):
    """Configuración para extracción."""
    headless: bool = True
    umbral_errores: int = 10
    timeout_pagina: int = 30000
    max_reintentos: int = 3
    procesar_con_pdf: bool = False           # ← NUEVO
    incluir_historicas: bool = True          # ← NUEVO
    min_utilidad: str = "MEDIA"              # ← NUEVO
```

**Verificación:** Backend arranca sin errores.

---

### FASE 5: TESTING Y VALIDACIÓN (30 min)

#### Tarea 5.1: Test manual con expediente real

**Pasos:**

1. Iniciar backend y frontend
2. Navegar a página de Expedientes
3. Hacer clic en "Extracción Masiva de Expedientes"
4. Configurar extracción y ejecutar
5. Esperar a que complete (ver reporte)
6. Filtrar y seleccionar 2-3 expedientes conocidos
7. **DESACTIVAR** checkbox "Procesar con PDF"
8. Confirmar procesamiento
9. Monitorear logs del backend

**Verificación (sin PDF):**
```bash
# Verificar que se creó estructura de directorios
ls -la Sistema_v6/data/expedientes/

# Verificar que se guardó JSON de actuaciones
find Sistema_v6/data/expedientes -name "*.json" -type f

# Verificar que NO hay carpeta de adjuntos
find Sistema_v6/data/expedientes -name "adjuntos" -type d
```

---

#### Tarea 5.2: Test con descarga de PDFs

**Pasos:**

1. Repetir proceso de selección
2. **ACTIVAR** checkbox "Procesar con PDF"
3. Confirmar procesamiento
4. Esperar a que complete

**Verificación (con PDF):**
```bash
# Verificar que se descargaron PDFs
find Sistema_v6/data/expedientes -name "*.pdf" -type f

# Verificar carpeta de adjuntos existe
find Sistema_v6/data/expedientes -name "adjuntos" -type d

# Contar archivos descargados
find Sistema_v6/data/expedientes -name "*.pdf" -type f | wc -l
```

---

#### Tarea 5.3: Verificar formato del JSON

**Archivo de ejemplo:**
```bash
# Listar JSONs generados
find Sistema_v6/data/expedientes -name "actuaciones-*.json"

# Ver contenido de uno
cat Sistema_v6/data/expedientes/FPA_001234_2024/actuaciones/actuaciones-FPA_001234_2024.json | jq .
```

**Verificar campos obligatorios:**
- `Expediente.version_formato` = "1.1"
- `Expediente.total_actuaciones` > 0
- `Actuaciones` es array
- Cada actuación tiene `Hash`, `Fecha`, `Tipo`, `Detalle`

---

#### Tarea 5.4: Test de actualización incremental

**Pasos:**

1. Procesar un expediente que ya fue procesado anteriormente
2. Verificar que se ejecuta `actualizar_actuaciones_desde_json()`
3. Verificar que no se duplican actuaciones
4. Verificar que solo se agregan actuaciones nuevas

**Verificación:**
```bash
# Ver logs del backend buscando "actualizando" o "incremental"
# Revisar JSON y verificar que no hay duplicados por Hash
```

---

## 📜 Comandos Git Seguros

### Extraer Archivos de Otra Rama Sin Checkout

**Sintaxis general:**
```bash
git show <rama>:<ruta_archivo> > <ruta_destino>
```

### Comandos Específicos para Este Plan

```bash
# Crear directorios
mkdir -p Sistema_v6/pjn/scraping
mkdir -p Sistema_v6/pjn/parsers
mkdir -p Sistema_v6/pjn/persistence
mkdir -p Sistema_v6/pjn/services
mkdir -p Sistema_v6/gestor_directorios

# Módulo de actuaciones (scraping)
git show producción_v5.1.1:Sistema_v5/pjn/scraping/actuaciones.py > Sistema_v6/pjn/scraping/actuaciones.py
git show producción_v5.1.1:Sistema_v5/pjn/scraping/actuaciones_utils.py > Sistema_v6/pjn/scraping/actuaciones_utils.py

# Parser de actuaciones
git show producción_v5.1.1:Sistema_v5/pjn/parsers/actuaciones_parser.py > Sistema_v6/pjn/parsers/actuaciones_parser.py

# Persistencia
git show producción_v5.1.1:Sistema_v5/pjn/persistence/actuaciones.py > Sistema_v6/pjn/persistence/actuaciones.py

# Servicio coordinador
git show producción_v5.1.1:Sistema_v5/pjn/services/actuaciones.py > Sistema_v6/pjn/services/actuaciones.py

# Gestor de directorios
git show producción_v5.1.1:Sistema_v5/gestor_directorios/expedientes.py > Sistema_v6/gestor_directorios/expedientes.py
git show producción_v5.1.1:Sistema_v5/gestor_directorios/archivos_usuario.py > Sistema_v6/gestor_directorios/archivos_usuario.py

# Modelos (opcional, solo si faltan)
git show producción_v5.1.1:Sistema_v5/pjn/models/__init__.py > /tmp/models_v5.py
# Revisar y copiar solo lo necesario a Sistema_v6/pjn/models/__init__.py
```

### Verificar Diferencias Entre Ramas

```bash
# Ver contenido de archivo en otra rama
git show producción_v5.1.1:Sistema_v5/pjn/scraping/actuaciones.py | head -50

# Comparar archivos entre ramas
git diff sintaxis_parcial2:Sistema_v6/pjn/scraping/actuaciones.py producción_v5.1.1:Sistema_v5/pjn/scraping/actuaciones.py
```

---

## ✓ Checklist de Verificación

### Migración de Código

- [ ] Directorio `Sistema_v6/pjn/scraping/` existe
- [ ] Directorio `Sistema_v6/pjn/parsers/` existe
- [ ] Directorio `Sistema_v6/pjn/persistence/` existe
- [ ] Directorio `Sistema_v6/pjn/services/` existe
- [ ] Directorio `Sistema_v6/gestor_directorios/` existe
- [ ] Archivo `actuaciones.py` portado a scraping
- [ ] Archivo `actuaciones_utils.py` portado a scraping
- [ ] Archivo `actuaciones_parser.py` portado a parsers
- [ ] Archivo `actuaciones.py` portado a persistence
- [ ] Archivo `actuaciones.py` portado a services
- [ ] Archivo `expedientes.py` portado a gestor_directorios
- [ ] Archivo `archivos_usuario.py` portado a gestor_directorios

### Adaptación a v6

- [ ] Todos los imports de `Sistema_v5` cambiados a `Sistema_v6`
- [ ] Modelos de datos verificados (Actuacion, ActuacionesArchivo, etc.)
- [ ] Compatibilidad de Playwright verificada
- [ ] Sistema de logging adaptado (si necesario)
- [ ] Configuración compatible

### Implementación Backend

- [ ] `ConfigExtraccionMasiva` actualizado con nuevos campos
- [ ] `_procesar_expediente()` implementado completamente
- [ ] Imports necesarios agregados a `gestor_batch.py`
- [ ] `ConfigExtraccionRequest` actualizado en router
- [ ] Backend arranca sin errores

### Implementación Frontend

- [ ] `handleConfirmar()` envía config con `procesarConPDF`
- [ ] Store `procesarExpedientesSeleccionados` actualizado
- [ ] Frontend compila sin errores TypeScript
- [ ] Checkbox "Procesar con PDF" funcional

### Testing

- [ ] Test sin PDF: estructura de directorios creada
- [ ] Test sin PDF: JSON de actuaciones guardado
- [ ] Test sin PDF: NO hay carpeta adjuntos
- [ ] Test con PDF: PDFs descargados en carpeta adjuntos
- [ ] Formato JSON v1.1 correcto
- [ ] Campos obligatorios presentes en JSON
- [ ] Actualización incremental funciona (no duplica)
- [ ] Clasificación inteligente ejecuta (si aplicable)
- [ ] Repositorio actualizado (si aplicable)

### Validación Final

- [ ] Backend logs sin errores críticos
- [ ] Frontend sin errores en consola
- [ ] Progreso se muestra en tiempo real
- [ ] Resumen final muestra estadísticas correctas
- [ ] Archivos organizados en estructura correcta
- [ ] No hay fugas de memoria (ejecutar 10+ expedientes)

---

## ⏱️ Estimaciones

### Por Fase

| Fase | Descripción | Tiempo Estimado |
|------|-------------|-----------------|
| 1 | Migración de código core | 1-2 horas |
| 2 | Adaptación a Sistema_v6 | 30-45 min |
| 3 | Implementación GestorBatch | 1 hora |
| 4 | Conexión Frontend-Backend | 15 min |
| 5 | Testing y validación | 30 min |
| **TOTAL** | | **3-4.5 horas** |

### Por Tipo de Tarea

| Tipo | Tiempo |
|------|--------|
| Copiar archivos (git show) | 30 min |
| Actualizar imports | 30 min |
| Verificar compatibilidad | 15 min |
| Implementar lógica procesamiento | 1 hora |
| Conectar frontend-backend | 15 min |
| Testing manual | 30 min |
| Debugging y ajustes | 30-60 min |

---

## ⚠️ Riesgos y Mitigaciones

### Riesgo 1: Incompatibilidad de versiones de Playwright

**Impacto:** Alto
**Probabilidad:** Medio

**Síntomas:**
- Funciones de Playwright no encontradas
- Selectores que no funcionan
- Timeouts inesperados

**Mitigación:**
```bash
# Verificar versión en ambas ramas
git show producción_v5.1.1:requirements.txt | grep playwright
cat Sistema_v6/requirements.txt | grep playwright

# Si hay diferencia, actualizar v6 o adaptar código
pip install playwright==<version_v5>
```

---

### Riesgo 2: Modelos de datos diferentes

**Impacto:** Medio
**Probabilidad:** Medio

**Síntomas:**
- Errores de serialización
- Campos faltantes en JSON
- Tipos incompatibles

**Mitigación:**
- Crear adaptadores/mappers entre modelos de v5 y v6
- Usar Pydantic para validación explícita
- Escribir tests unitarios para conversión de modelos

---

### Riesgo 3: Dependencias faltantes

**Impacto:** Alto
**Probabilidad:** Bajo

**Síntomas:**
- `ImportError` o `ModuleNotFoundError`
- Funciones no encontradas

**Mitigación:**
```bash
# Verificar requirements de v5
git show producción_v5.1.1:requirements.txt > /tmp/req_v5.txt

# Comparar con v6
diff /tmp/req_v5.txt Sistema_v6/requirements.txt

# Instalar dependencias faltantes
pip install -r /tmp/req_v5.txt
```

---

### Riesgo 4: Selectores CSS desactualizados

**Impacto:** Alto
**Probabilidad:** Medio

**Síntomas:**
- No encuentra elementos en página del PJN
- Timeout esperando selectores
- Datos extraídos incorrectos

**Mitigación:**
- Verificar selectores con navegador en modo headless=False
- Actualizar selectores en `Sistema_v6/pjn/selectores.py` si cambió el portal PJN
- Agregar logging detallado para debuggear

---

### Riesgo 5: Errores de permisos en directorios

**Impacto:** Medio
**Probabilidad:** Bajo

**Síntomas:**
- `PermissionError` al crear directorios
- No se guardan archivos

**Mitigación:**
```bash
# Verificar permisos del directorio base
ls -la Sistema_v6/data/

# Crear si no existe
mkdir -p Sistema_v6/data/expedientes

# Asegurar permisos de escritura
chmod -R 755 Sistema_v6/data/
```

---

### Riesgo 6: Timeout en descargas de PDFs grandes

**Impacto:** Bajo
**Probabilidad:** Medio

**Síntomas:**
- Descarga se interrumpe
- Error de timeout en playwright

**Mitigación:**
- Aumentar timeout en configuración: `timeout_pagina: 60000`
- Implementar reintentos con backoff exponencial
- Agregar logging de progreso de descarga

---

## 📚 Referencias

### Archivos Clave del Proyecto

#### Backend

**Extracción Masiva:**
- `/Users/davidalejandroliva/PycharmProjects/sintaXis/Sistema_v6/extraccion_masiva/extractor_masivo.py`
- `/Users/davidalejandroliva/PycharmProjects/sintaXis/Sistema_v6/extraccion_masiva/gestor_batch.py`
- `/Users/davidalejandroliva/PycharmProjects/sintaXis/Sistema_v6/extraccion_masiva/models.py`

**API REST:**
- `/Users/davidalejandroliva/PycharmProjects/sintaXis/Sistema_v6/presentation/api/rest/routers/extraccion_masiva.py`

**PJN Scraping (v6 actual):**
- `/Users/davidalejandroliva/PycharmProjects/sintaXis/Sistema_v6/pjn/scraping/expedientes.py`
- `/Users/davidalejandroliva/PycharmProjects/sintaXis/Sistema_v6/pjn/parsers/expedientes_parser.py`

**Sistema v5 (producción):**
- `git show producción_v5.1.1:Sistema_v5/pjn/scraping/actuaciones.py`
- `git show producción_v5.1.1:Sistema_v5/pjn/services/actuaciones.py`
- `git show producción_v5.1.1:Sistema_v5/gestor_directorios/expedientes.py`

#### Frontend

**Componente Principal:**
- `/Users/davidalejandroliva/PycharmProjects/sintaXis/Sistema_v6/frontend/src/components/expedientes/ExtraccionMasivaDialog.tsx`

**Store:**
- `/Users/davidalejandroliva/PycharmProjects/sintaXis/Sistema_v6/frontend/src/stores/expedientesStore.ts`

### Funciones Principales y Firmas

#### Búsqueda de Expedientes

```python
async def buscar_expediente_por_numero(
    page: Page,
    numero: str,
    anio: str,
    timeout: int = 8_000
) -> tuple[bool, str]
```
**Ubicación:** `Sistema_v6/pjn/scraping/expedientes.py`

---

#### Extracción de Metadata

```python
async def extraer_datos_expediente(page: Page) -> dict[str, str] | None
```
**Ubicación:** `Sistema_v6/pjn/scraping/expedientes.py`

---

#### Extracción de Actuaciones Completas

```python
async def extraer_actuaciones_completas(
    page_expediente: Page,
    expediente_datos: dict,
    incluir_historicas: bool = True,
    directorio_base: str = "Actuaciones"
) -> tuple[list[Actuacion], list[Actuacion], str | None]
```
**Ubicación:** `Sistema_v5/pjn/scraping/actuaciones.py` (a portar)

---

#### Coordinador de Procesamiento

```python
async def procesar_actuaciones_expediente(
    datos_expediente: dict[str, Any],
    *,
    descargar_adjuntos: bool = False
) -> tuple[Path | None, ResultadoProcesamiento]
```
**Ubicación:** `Sistema_v5/pjn/services/actuaciones.py` (a portar)

---

#### Gestión de Directorios

```python
class GestorDirectoriosExpedientes:
    def __init__(self, directorio_base: str):
        """Inicializa gestor con directorio base."""

    def crear_estructura_expediente(
        self, numero_expediente: str
    ) -> dict[str, Path]:
        """Crea estructura completa de directorios."""
```
**Ubicación:** `Sistema_v5/gestor_directorios/expedientes.py` (a portar)

---

### Estructuras de Datos

#### ExpedienteResumen

```python
@dataclass
class ExpedienteResumen:
    numero: str
    dependencia: str
    caratula: str
    situacion: str | None
    ultima_actuacion: str | None  # YYYY-MM-DD
```

#### Actuacion

```python
@dataclass
class Actuacion:
    Indice: int
    Oficina: str
    OficinaCompleta: str
    Fecha: str  # DD/MM/YYYY
    Tipo: str
    Detalle: str
    Foja: str
    Archivo: str  # URL
    NombreArchivo: str
    TieneArchivo: bool
    TipoArchivo: str  # .pdf, .doc, etc
    Hash: str
    ExtraidaEn: str
    EsHistorica: bool
    Descargado: bool
```

#### ResultadoProcesamiento

```python
@dataclass
class ResultadoProcesamiento:
    exito: bool
    total_actuaciones: int
    archivos_descargados: int
    errores: list[str]
    tiempo_procesamiento: float
```

---

### Comandos Útiles

#### Verificar estructura creada

```bash
tree Sistema_v6/data/expedientes/
```

#### Buscar archivos JSON

```bash
find Sistema_v6/data/expedientes -name "*.json" -type f
```

#### Buscar PDFs descargados

```bash
find Sistema_v6/data/expedientes -name "*.pdf" -type f | wc -l
```

#### Ver logs del backend

```bash
tail -f logs/extraccion_masiva.log  # Si existe
# O ver output de uvicorn directamente
```

#### Verificar imports de Sistema_v5

```bash
grep -r "Sistema_v5" Sistema_v6/pjn/
```

#### Contar líneas portadas

```bash
wc -l Sistema_v6/pjn/scraping/actuaciones.py
wc -l Sistema_v6/pjn/services/actuaciones.py
```

---

## 🎯 Resumen Ejecutivo

### Lo que vamos a lograr

Al completar este plan, el sistema tendrá:

1. ✅ **Procesamiento completo de expedientes** usando código probado de v5.1.1
2. ✅ **Extracción de actuaciones** actuales + históricas con paginación automática
3. ✅ **Descarga opcional de PDFs** controlada por checkbox en UI
4. ✅ **Actualización incremental** - solo agregar actuaciones nuevas
5. ✅ **Gestión automática de directorios** por expediente
6. ✅ **Clasificación inteligente** opcional por utilidad jurídica
7. ✅ **Formato JSON estandarizado** (v1.1) compatible con procesador_pdf
8. ✅ **Detección de duplicados** por hash de actuaciones
9. ✅ **Progreso en tiempo real** visible en frontend
10. ✅ **Manejo robusto de errores** con umbral configurable

### Código portado de producción

Todo el código crítico viene de la rama `producción_v5.1.1` que está **operando en producción**, lo que garantiza:

- ✅ Código probado y depurado
- ✅ Manejo de casos edge conocidos
- ✅ Compatibilidad con portal PJN actual
- ✅ Formato de datos validado

### Tiempo total estimado

**3-4.5 horas** incluyendo testing.

### Próximos pasos después de implementar

1. Monitorear primeros procesamientos en producción
2. Ajustar timeouts si es necesario
3. Optimizar clasificador inteligente
4. Implementar caché de actuaciones ya descargadas
5. Agregar reportes de procesamiento

---

**FIN DEL PLAN DE IMPLEMENTACIÓN**

Para dudas o problemas durante la implementación, consultar:
- Este documento
- README del Sistema_v5: `Sistema_v6/REFERENCIA_SISTEMA_V5/README.md`
- Código fuente en rama: `producción_v5.1.1`
