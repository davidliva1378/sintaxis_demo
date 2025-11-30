# INVESTIGACIÓN COMPLETA: Flujo "Expedientes - Ver detalle - Procesar"

**Fecha:** 2025-11-25
**Sistema:** SintaXis v6
**Módulo:** Procesamiento de Expedientes

---

## Tabla de Contenidos

1. [Frontend - Interfaz de Usuario](#1-frontend---interfaz-de-usuario)
2. [API - Capa de Comunicación](#2-api---capa-de-comunicación)
3. [Backend - Lógica de Negocio](#3-backend---lógica-de-negocio)
4. [Integraciones](#4-integraciones)
5. [Base de Datos](#5-base-de-datos)
6. [Flujo Completo Paso a Paso](#6-flujo-completo-paso-a-paso)
7. [Configuración y Dependencias](#7-configuración-y-dependencias)
8. [Resumen de Archivos Clave](#8-resumen-de-archivos-clave)
9. [Posibles Puntos de Falla o Mejora](#9-posibles-puntos-de-falla-o-mejora)

---

## 1. FRONTEND - Interfaz de Usuario

### 1.1. Componente Principal de Detalle

**Ubicación:** `/frontend/src/pages/expedientes/ExpedienteDetallePage.tsx`

**Funcionalidad:**
- **Líneas 46-73:** Inicialización y carga del expediente usando el hook `useExpedientesStore()`
- **Líneas 107-154:** Función `handleProcesar()` - El corazón del procesamiento

### 1.2. Botón "Procesar" - Ubicación y Activación

El botón se encuentra en dos ubicaciones:

1. **En el Header (Líneas 212-217):**
   - Componente `ProcesamientoStatusBadge` que muestra el estado y botón
   - Se pasa `onProcesar={handleProcesar}` como prop

2. **En Tab de Procesamiento (Líneas 363-375):**
   - Botón grande cuando el expediente NO está procesado
   - Muestra spinner durante procesamiento

**Estados del Botón:**
- **Sin Procesar:** Badge gris con X + Botón "Procesar"
- **Procesando:** Badge con spinner + texto "Procesando..."
- **Procesado:** Badge verde con checkmark + fecha
- **Desactualizado:** Badge amarillo + Botón "Reprocesar"

### 1.3. Flujo de Navegación

**Ruta:** `/expedientes` → `/expedientes/:numero`

1. **ExpedientesPage.tsx (línea 50-54):**
   ```typescript
   const handleVerDetalle = (numero: string) => {
     const numeroNormalizado = numero.replace(/\s+/g, '-').replace(/\//g, '-')
     navigate(`/expedientes/${numeroNormalizado}`)
   }
   ```

2. **ExpedienteDetallePage.tsx (líneas 65-73):**
   - useEffect carga el expediente al montar
   - useEffect limpia al desmontar
   - Segundo useEffect (líneas 76-80) carga datos de procesamiento

### 1.4. Gestión de Estado (Zustand Store)

**Store:** `/frontend/src/stores/expedientesStore.ts`

**Estados Relevantes:**
- `expedienteActual: ExpedienteDetalle | null` - Expediente en vista
- `isLoading: boolean` - Estado de carga
- `filtros: ExpedienteFiltros` - Filtros aplicados
- `paginacion` - Info de paginación

**Métodos:**
- `obtenerExpediente(numero: string)` (líneas 198-235) - Obtiene detalle del expediente
- `limpiarExpedienteActual()` - Limpia estado al salir

### 1.5. Llamadas API Durante el Procesamiento

**Función `handleProcesar` (líneas 107-154):**

1. **Preparación de Datos (líneas 113-128):**
   - Convierte actuaciones al formato `ActuacionInput[]`
   - Construye diccionario de rutas PDF `rutas_pdf: Record<number, string>`

2. **Llamada Principal (línea 130):**
   ```typescript
   const resultado = await procesarExpediente({
     numero_expediente: expedienteActual.numero,
     actuaciones: actuacionesInput,
     rutas_pdf: Object.keys(rutas_pdf).length > 0 ? rutas_pdf : undefined,
     guardar_en_bd: true
   })
   ```

3. **Recarga de Datos (línea 146):**
   ```typescript
   await cargarDatosProcesamiento(expedienteActual.numero)
   ```

**Función `cargarDatosProcesamiento` (líneas 82-105):**
Carga 3 endpoints en paralelo:
```typescript
const [stats, actuaciones, venc] = await Promise.all([
  obtenerEstadisticasExpediente(numeroExp),
  obtenerActuacionesClasificadasExpediente(numeroExp),
  obtenerVencimientosExpediente(numeroExp)
])
```

### 1.6. UX - Modales, Confirmaciones y Feedback

**Feedback Visual:**
- **Spinner durante procesamiento** (líneas 366-368)
- **Toast de éxito** (líneas 141-143):
  ```typescript
  toast.success('Expediente procesado', {
    description: `${resultado.estadisticas.total_actuaciones} actuaciones clasificadas`
  })
  ```
- **Toast de error** (líneas 148-150)

**Estados Visuales:**
- Loader mientras carga (líneas 167-174)
- Mensaje de "no encontrado" (líneas 176-196)
- Tabs con badges indicando cantidad (líneas 313-326)

### 1.7. Tipos TypeScript

**Archivo:** `/frontend/src/types/procesamiento.ts`

**Tipos Clave:**
```typescript
export interface ActuacionInput {
  id: number
  tipo: string
  detalle: string
  tiene_archivo?: boolean
  expediente_numero?: string
}

export interface ResultadoExpediente {
  expediente_numero: string
  estadisticas: EstadisticasExpediente
  vencimientos_urgentes: VencimientoUrgente[]
  con_errores: number
}

export interface EstadisticasExpediente {
  total_actuaciones: number
  actuaciones_alta: number
  actuaciones_media: number
  actuaciones_baja: number
  actuaciones_nula: number
  reduccion_estimada_pct: number
  vencimientos_detectados: number
  vencimientos_urgentes: number
  duplicados_detectados: number
  tiempo_procesamiento_seg: number
}
```

---

## 2. API - Capa de Comunicación

### 2.1. Cliente API

**Archivo:** `/frontend/src/api/procesamientoApi.ts`

### 2.2. Endpoint Principal: Procesar Expediente

**Función:** `procesarExpediente(request: ProcesarExpedienteRequest)` (líneas 67-82)

```typescript
POST /api/v1/procesamiento/expediente
```

**Request:**
```typescript
{
  numero_expediente: string,
  actuaciones: ActuacionInput[],
  rutas_pdf?: Record<number, string>,
  guardar_en_bd?: boolean
}
```

**Response:**
```typescript
{
  expediente_numero: string,
  estadisticas: EstadisticasExpediente,
  vencimientos_urgentes: VencimientoUrgente[],
  con_errores: number
}
```

### 2.3. Endpoints Relacionados

1. **Obtener Estadísticas** (líneas 111-128):
   ```
   GET /api/v1/procesamiento/expediente/{numero}/estadisticas
   ```

2. **Obtener Vencimientos** (líneas 133-150):
   ```
   GET /api/v1/procesamiento/expediente/{numero}/vencimientos
   ```

3. **Obtener Actuaciones Clasificadas** (líneas 155-172):
   ```
   GET /api/v1/procesamiento/expediente/{numero}/actuaciones-clasificadas
   ```

### 2.4. Manejo de Errores

**En procesamientoApi.ts (líneas 76-78):**
```typescript
if (!response.ok) {
  const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
  throw new Error(error.detail || `HTTP ${response.status}`)
}
```

**En ExpedienteDetallePage.tsx (líneas 147-153):**
```typescript
catch (error) {
  toast.error('Error al procesar', {
    description: error instanceof Error ? error.message : 'Error desconocido'
  })
}
```

### 2.5. Rate Limiting

**Archivo Router:** `/presentation/api/rest/routers/procesamiento.py`

```python
@router.post("/expediente", response_model=ResultadoExpedienteResponse)
@limiter.limit("5/minute")  # Línea 258
```

---

## 3. BACKEND - Lógica de Negocio

### 3.1. Router FastAPI

**Archivo:** `/presentation/api/rest/routers/procesamiento.py`

**Endpoint Principal:** `procesar_expediente` (líneas 257-386)

**Flujo:**
1. **Conversión de datos** (línea 283)
2. **Llamada al servicio** (líneas 285-290)
3. **Conversión de estadísticas** (líneas 293-305)
4. **Conversión de vencimientos** (líneas 308-372)
5. **Retorno de resultado** (líneas 374-379)

### 3.2. Service - ProcesadorActuacionesService

**Archivo:** `/application/services/procesador_actuaciones_service.py`

**Método Principal:** `procesar_expediente_completo` (líneas 671-773)

#### ¿Qué hace exactamente "Procesar"?

1. **PROCESAMIENTO CON procesador_pdf** (líneas 695-701):
   ```python
   resultado_procesamiento = procesar_expediente(
       actuaciones=actuaciones,
       rutas_pdf=rutas_pdf,
       analizar_vencimientos=True,
       detectar_duplicados=True
   )
   ```

2. **GUARDAR EN BASE DE DATOS** (líneas 706-765):

   **a) Obtener expediente_id de MySQL** (líneas 708-719)

   **b) Guardar clasificaciones individuales** (líneas 720-741):
   - Utilidad jurídica (nula, baja, media, alta)
   - Score de clasificación (0-100)
   - Motivo de clasificación
   - Keywords detectados
   - Texto extraído del PDF
   - Hash del contenido
   - Metadata de clasificación

   **c) Guardar vencimientos** (líneas 733-740)

   **d) Guardar duplicados detectados** (líneas 743-747)

   **e) Guardar estadísticas del expediente** (líneas 749-765)

### 3.3. Use Case del Procesador (core/procesador_pdf)

**Archivo:** `/core/procesador_pdf/__init__.py`

**Función `procesar_expediente`** (líneas 192-291):

#### Qué hace paso a paso:

1. **Procesar cada actuación individualmente** (líneas 228-240):
   ```python
   for actuacion in actuaciones:
       resultado = procesar_actuacion(
           actuacion=actuacion,
           ruta_pdf=ruta_pdf,
           analizar_vencimientos=analizar_vencimientos,
           detectar_duplicados=False
       )
       resultados[act_id] = resultado
   ```

2. **Detectar duplicados en batch** (líneas 244-258):
   - Duplicados exactos (por hash MD5)
   - Duplicados de cédulas (por contenido)

3. **Recopilar vencimientos** (líneas 261-267):
   - Filtrar vencimientos urgentes (próximos 7 días)

4. **Generar estadísticas** (líneas 269-281):
   - Conteo por utilidad (alta, media, baja, nula)
   - Reducción estimada de volumen
   - Estadísticas de duplicados

### 3.4. Función `procesar_actuacion` (líneas 83-189)

#### Operaciones realizadas:

1. **CLASIFICACIÓN** (líneas 128-142):
   - Analiza tipo y detalle de la actuación
   - Asigna utilidad jurídica (ALTA, MEDIA, BAJA, NULA)
   - Calcula score (0-100)
   - Detecta keywords relevantes
   - Determina si requiere revisión de PDF
   - Detecta si probablemente tiene plazo procesal

2. **EXTRACCIÓN DE TEXTO DE PDF** (líneas 144-151):
   ```python
   if ruta_pdf:
       extractor = ExtractorTexto(usar_ocr=False)
       texto_extraido = extractor.extraer(ruta_pdf)
   ```

3. **ANÁLISIS DE VENCIMIENTOS** (líneas 154-164):
   ```python
   if analizar_vencimientos and clasificacion.tiene_plazo_probable:
       analizador = AnalizadorVencimientos()
       vencimientos = analizador.analizar_actuacion(
           actuacion,
           extraer_de_pdf=bool(ruta_pdf),
           ruta_pdf=ruta_pdf
       )
   ```

4. **DETECCIÓN DE DUPLICADOS** (líneas 167-180):
   - Compara con actuaciones previas
   - Detecta duplicados exactos y semánticos
   - Calcula similitud

---

## 4. INTEGRACIONES

### 4.1. ExtractorMasivo

**NO se usa ExtractorMasivo para procesar**. El procesamiento usa:
- PDFs ya descargados previamente
- Rutas a archivos locales en el sistema

### 4.2. Scraping Directo del PJN

**NO se hace scraping durante el procesamiento**. El procesamiento trabaja con datos ya extraídos.

### 4.3. LLM/Embeddings - Integración IA

**Archivo:** `/application/services/procesador_actuaciones_service.py`

**Integración automática** (líneas 266-336):

Cuando hay texto extraído:

```python
if texto_extraido and _ia_integration_available:
    ia_service = get_ia_integration_service(
        habilitar_clasificacion=True,
        habilitar_rag=True,
        habilitar_ner=True
    )
    resultado_ia = ia_service.procesar_actuacion(
        actuacion_id=str(actuacion_id),
        texto=texto_extraido,
        metadata={...},
        clasificar=True,
        indexar=True,
        extraer_entidades=True
    )
```

#### Qué hace la integración IA:
1. **Clasificación IA:** tipo_ia, confianza_ia, justificacion_ia
2. **Indexación RAG:** Agrega a ChromaDB/vector store
3. **NER:** Extrae entidades (nombres, lugares, fechas, etc.)

### 4.4. Actualización de Índices

**BM25 Index:**
- Se actualiza automáticamente al guardar texto en BD
- Ubicación: `/data/bm25_index/actuaciones/`

**Vector Store (ChromaDB):**
- Se actualiza si `indexar=True` en integración IA
- Ubicación: `/data/vector_store/`

---

## 5. BASE DE DATOS

### 5.1. Tablas Involucradas

**Archivo Schema:** `/database/migrations/001_add_procesador_pdf_fields.sql`

#### Tabla `actuaciones`

**Campos agregados para procesamiento:**
- `utilidad` ENUM('nula', 'baja', 'media', 'alta')
- `score` INT (0-100)
- `motivo_clasificacion` TEXT
- `requiere_pdf` BOOLEAN
- `tiene_plazo_probable` BOOLEAN
- `es_duplicado_probable` BOOLEAN
- `keywords_detectados` JSON
- `fecha_clasificacion` DATETIME
- `texto_extraido` LONGTEXT
- `hash_contenido` VARCHAR(64)
- `texto_json` JSON (texto estructurado)
- `tiene_texto_extraido` BOOLEAN
- `metodo_extraccion` VARCHAR(50)

**Campos de IA:**
- `tipo_ia` VARCHAR(100)
- `confianza_ia` DECIMAL(3,2)
- `justificacion_ia` TEXT
- `metodo_ia` VARCHAR(50)
- `fecha_clasificacion_ia` DATETIME
- `indexado_rag` BOOLEAN

**Índices:**
```sql
INDEX idx_utilidad (utilidad)
INDEX idx_score (score)
INDEX idx_requiere_pdf (requiere_pdf)
INDEX idx_tiene_plazo (tiene_plazo_probable)
```

#### Tabla `vencimientos`

**Estructura (líneas 29-55):**
```sql
CREATE TABLE vencimientos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    actuacion_id INT NOT NULL,
    expediente_numero VARCHAR(100),
    tipo VARCHAR(50),  -- cedula_electronica, cedula_fisica, traslado, etc.
    fecha_notificacion DATE NOT NULL,
    plazo_dias INT NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    dias_habiles BOOLEAN DEFAULT TRUE,
    descripcion TEXT,
    texto_fuente TEXT,
    confianza DECIMAL(3,2) DEFAULT 1.00,
    estado ENUM('pendiente', 'atendido', 'vencido'),
    fecha_atencion DATETIME,
    usuario_atencion VARCHAR(100),
    notas TEXT,
    creado_en DATETIME,
    actualizado_en DATETIME,
    FOREIGN KEY (actuacion_id) REFERENCES actuaciones(id) ON DELETE CASCADE
)
```

**Índices:**
- `idx_fecha_vencimiento`
- `idx_estado`
- `idx_tipo`
- `idx_expediente_numero`

#### Tabla `duplicados_detectados`

**Estructura (líneas 61-82):**
```sql
CREATE TABLE duplicados_detectados (
    id INT PRIMARY KEY AUTO_INCREMENT,
    actuacion_original_id INT NOT NULL,
    actuacion_duplicada_id INT NOT NULL,
    tipo ENUM('exacto', 'semantico', 'parcial'),
    similitud DECIMAL(5,4),  -- 0.0000 a 1.0000
    hash_normalizado VARCHAR(64),
    motivo TEXT,
    revisado BOOLEAN DEFAULT FALSE,
    confirmado BOOLEAN,
    creado_en DATETIME,
    revisado_en DATETIME,
    revisado_por VARCHAR(100),
    UNIQUE KEY unique_duplicado (actuacion_original_id, actuacion_duplicada_id)
)
```

#### Tabla `procesamiento_estadisticas`

**Estructura (líneas 88-106):**
```sql
CREATE TABLE procesamiento_estadisticas (
    id INT PRIMARY KEY AUTO_INCREMENT,
    expediente_numero VARCHAR(100) NOT NULL,
    fecha_procesamiento DATETIME NOT NULL,
    total_actuaciones INT NOT NULL,
    actuaciones_alta INT DEFAULT 0,
    actuaciones_media INT DEFAULT 0,
    actuaciones_baja INT DEFAULT 0,
    actuaciones_nula INT DEFAULT 0,
    reduccion_estimada_pct DECIMAL(5,2),
    vencimientos_detectados INT DEFAULT 0,
    vencimientos_urgentes INT DEFAULT 0,
    duplicados_detectados INT DEFAULT 0,
    tiempo_procesamiento_seg DECIMAL(10,2),
    version_procesador VARCHAR(20) DEFAULT '1.0.0'
)
```

### 5.2. Vistas

**1. `vencimientos_urgentes`** (líneas 113-130):
```sql
CREATE OR REPLACE VIEW vencimientos_urgentes AS
SELECT
    v.*,
    a.tipo AS actuacion_tipo,
    a.detalle AS actuacion_detalle,
    DATEDIFF(v.fecha_vencimiento, CURDATE()) AS dias_restantes,
    CASE
        WHEN DATEDIFF(...) <= 0 THEN 'vencido'
        WHEN DATEDIFF(...) <= 1 THEN 'critico'
        WHEN DATEDIFF(...) <= 3 THEN 'urgente'
        WHEN DATEDIFF(...) <= 7 THEN 'proximo'
        ELSE 'normal'
    END AS nivel_urgencia
FROM vencimientos v
JOIN actuaciones a ON v.actuacion_id = a.id
WHERE v.estado = 'pendiente'
  AND DATEDIFF(v.fecha_vencimiento, CURDATE()) <= 7
```

**2. `actuaciones_alta_utilidad`** (líneas 133-153):
Vista optimizada para actuaciones de alta y media utilidad con vencimientos.

### 5.3. Relaciones

```
expedientes (1) ----< actuaciones (N)
                          |
                          |--< vencimientos (N)
                          |
                          |--< duplicados_detectados (N)

expedientes (1) ----< procesamiento_estadisticas (N)
```

---

## 6. FLUJO COMPLETO PASO A PASO

### 6.1. Diagrama de Flujo

```
[Usuario hace clic en "Procesar"]
         |
         v
[1. FRONTEND - ExpedienteDetallePage.tsx]
    |
    |-- handleProcesar() ejecutado
    |-- setIsProcessing(true)
    |-- Convierte actuaciones a ActuacionInput[]
    |-- Construye rutas_pdf: Record<number, string>
    |
    v
[2. API CALL - procesamientoApi.ts]
    |
    |-- POST /api/v1/procesamiento/expediente
    |-- Payload: { numero_expediente, actuaciones, rutas_pdf, guardar_en_bd }
    |
    v
[3. BACKEND ROUTER - procesamiento.py]
    |
    |-- @limiter.limit("5/minute")
    |-- Valida request
    |-- servicio.procesar_expediente_completo()
    |
    v
[4. SERVICE - ProcesadorActuacionesService]
    |
    |-- procesar_expediente_completo()
    |-- Llama a core.procesador_pdf.procesar_expediente()
    |
    v
[5. CORE PROCESSOR - procesador_pdf/__init__.py]
    |
    |-- Para cada actuación:
    |   |
    |   |-- [5.1] CLASIFICACIÓN
    |   |   |-- ClasificadorActuaciones.clasificar()
    |   |   |-- Analiza tipo + detalle
    |   |   |-- Asigna utilidad (ALTA/MEDIA/BAJA/NULA)
    |   |   |-- Calcula score (0-100)
    |   |   |-- Detecta keywords jurídicos
    |   |   |-- Determina requiere_pdf
    |   |   |-- Detecta tiene_plazo_probable
    |   |
    |   |-- [5.2] EXTRACCIÓN DE TEXTO (si tiene PDF)
    |   |   |-- ExtractorTexto.extraer(ruta_pdf)
    |   |   |-- Intenta texto embebido primero
    |   |   |-- OCR si es necesario (Tesseract)
    |   |   |-- Normaliza y limpia texto
    |   |   |-- Calcula hash MD5 del contenido
    |   |
    |   |-- [5.3] ANÁLISIS DE VENCIMIENTOS (si tiene_plazo_probable)
    |   |   |-- AnalizadorVencimientos.analizar_actuacion()
    |   |   |-- Busca patrones de fechas en texto
    |   |   |-- Detecta plazos (días hábiles/corridos)
    |   |   |-- Calcula fecha_vencimiento
    |   |   |-- Asigna confianza (0.0-1.0)
    |   |
    |   v
    |
    |-- [5.4] DETECCIÓN DE DUPLICADOS (en batch)
    |   |-- DetectorDuplicados.detectar_duplicados_exactos()
    |   |-- Compara hashes MD5
    |   |-- DetectorDuplicados.detectar_cedulas_duplicadas()
    |   |-- Compara contenido normalizado
    |   |-- Calcula similitud semántica
    |
    |-- [5.5] RECOPILACIÓN Y FILTRADO
    |   |-- Recopila todos los vencimientos
    |   |-- Filtra vencimientos urgentes (≤ 7 días)
    |   |-- Genera estadísticas globales
    |
    v
[6. PERSISTENCIA - ActuacionesRepository]
    |
    |-- Para cada actuación:
    |   |
    |   |-- [6.1] guardar_clasificacion()
    |   |   |-- INSERT ... ON DUPLICATE KEY UPDATE actuaciones
    |   |   |-- Actualiza: utilidad, score, motivo, keywords
    |   |   |-- Guarda: texto_extraido, hash_contenido, texto_json
    |   |   |
    |   |   |-- [6.1.1] INTEGRACIÓN IA (si hay texto)
    |   |       |-- get_ia_integration_service()
    |   |       |-- procesar_actuacion(clasificar=True, indexar=True, extraer_entidades=True)
    |   |       |
    |   |       |-- [IA CLASIFICACIÓN]
    |   |       |   |-- LLM clasifica tipo de actuación
    |   |       |   |-- Guarda: tipo_ia, confianza_ia, justificacion_ia
    |   |       |
    |   |       |-- [IA INDEXACIÓN RAG]
    |   |       |   |-- Genera embeddings con SentenceTransformer
    |   |       |   |-- Almacena en ChromaDB
    |   |       |   |-- Marca indexado_rag = TRUE
    |   |       |
    |   |       |-- [IA NER - Named Entity Recognition]
    |   |           |-- Extrae entidades: personas, lugares, fechas
    |   |           |-- Guarda en tabla entidades_extraidas
    |   |
    |   |-- [6.2] guardar_vencimientos()
    |   |   |-- INSERT ... ON DUPLICATE KEY UPDATE vencimientos
    |   |   |-- Para cada vencimiento detectado
    |   |   |-- Guarda: tipo, fechas, plazo, confianza
    |   |
    |   v
    |
    |-- [6.3] guardar_duplicados()
    |   |-- INSERT ... ON DUPLICATE KEY UPDATE duplicados_detectados
    |   |-- Para cada duplicado encontrado
    |
    |-- [6.4] guardar_estadisticas()
        |-- INSERT ... ON DUPLICATE KEY UPDATE procesamiento_estadisticas
        |-- Guarda resumen del procesamiento
        |-- Incluye: conteos, reducción estimada, tiempo
    |
    v
[7. RESPONSE AL FRONTEND]
    |
    |-- Construye ResultadoExpedienteResponse
    |-- Incluye: estadisticas, vencimientos_urgentes, con_errores
    |-- Retorna JSON
    |
    v
[8. FRONTEND - Actualización UI]
    |
    |-- setEstadisticas(resultado.estadisticas)
    |-- setVencimientos(resultado.vencimientos_urgentes)
    |-- setIsProcesado(true)
    |-- setIsProcessing(false)
    |
    |-- toast.success('Expediente procesado')
    |
    |-- [8.1] RECARGA DATOS COMPLETOS
    |   |-- cargarDatosProcesamiento()
    |   |-- Promise.all([
    |   |     obtenerEstadisticasExpediente(),
    |   |     obtenerActuacionesClasificadasExpediente(),
    |   |     obtenerVencimientosExpediente()
    |   |   ])
    |
    v
[9. USUARIO VE RESULTADO]
    |
    |-- Badge verde "Procesado"
    |-- Tab "Procesamiento" con estadísticas
    |-- Tab "Vencimientos" con alertas urgentes
    |-- Tab "Análisis IA" con clasificaciones
    |-- Tab "Entidades" con entidades extraídas
```

### 6.2. Tiempo Estimado de Procesamiento

**Estimación por número de actuaciones:**

```typescript
// procesamientoApi.ts líneas 315-321
export function calcularTiempoEstimado(cantidadActuaciones: number): number {
  // Clasificación: ~1000 acts/seg
  // Extracción PDF: ~2-5 PDFs/seg
  // Promedio conservador: 100 acts/seg
  return Math.ceil(cantidadActuaciones / 100)
}
```

**Ejemplos:**
- 10 actuaciones: < 1 segundo
- 50 actuaciones: ~0.5 segundos
- 100 actuaciones: ~1 segundo
- 500 actuaciones: ~5 segundos

**NOTA:** El tiempo real depende de:
- Cantidad de PDFs a procesar
- Tamaño de los PDFs
- Si requiere OCR
- Velocidad de la base de datos
- Disponibilidad del servicio IA

### 6.3. Qué se Muestra al Usuario Durante el Proceso

1. **Inicio:**
   - Badge cambia a "Procesando..." con spinner
   - Botón se deshabilita
   - Estado `isProcessing = true`

2. **Durante:**
   - No hay feedback intermedio (proceso rápido)
   - UI permanece responsive

3. **Finalización Exitosa:**
   - Toast verde: "Expediente procesado - X actuaciones clasificadas"
   - Badge cambia a verde "Procesado"
   - Tabs se actualizan con datos

4. **Error:**
   - Toast rojo con mensaje de error
   - Badge vuelve a estado "Sin procesar"
   - Botón se habilita para reintentar

### 6.4. Qué Sucede en Caso de Error

**Niveles de Manejo:**

1. **Frontend (ExpedienteDetallePage.tsx líneas 147-153):**
   ```typescript
   catch (error) {
     toast.error('Error al procesar', {
       description: error instanceof Error ? error.message : 'Error desconocido'
     })
   } finally {
     setIsProcessing(false)
   }
   ```

2. **API Router (procesamiento.py líneas 381-386):**
   ```python
   except Exception as e:
       logger.error(f"Error procesando expediente {data.numero_expediente}: {e}")
       raise HTTPException(
           status_code=500,
           detail=f"Error al procesar expediente: {str(e)}"
       )
   ```

3. **Core Processor:**
   - Errores se capturan por actuación
   - Se agregan a `errores: List[str]`
   - El procesamiento continúa con las demás
   - `con_errores` cuenta actuaciones con problemas

**Comportamiento ante Errores:**
- **Error en 1 actuación:** Continúa con las demás, marca el error
- **Error en clasificación:** Usa clasificación por defecto (MEDIA, score 50)
- **Error en PDF:** Continúa sin texto extraído
- **Error en vencimientos:** Continúa sin vencimientos para esa actuación
- **Error en BD:** Falla todo el procesamiento (transaccional)

---

## 7. CONFIGURACIÓN Y DEPENDENCIAS

### 7.1. Variables de Entorno Relevantes

**Archivo:** `/.env.example`

**Base de Datos:**
```bash
DATABASE_URL=sqlite:///./data/sistema.db
# O MySQL:
# MYSQL_HOST=localhost
# MYSQL_PORT=3306
# MYSQL_DATABASE=sintaxis
# MYSQL_USER=root
# MYSQL_PASSWORD=password
```

**IA/RAG:**
```bash
IA_OLLAMA_ENABLED=false
IA_OLLAMA_HOST=http://localhost:11434
IA_OLLAMA_MODEL=llama3.1
IA_CHROMADB_PATH=./data/chromadb
```

**PDF Processing:**
```bash
PDF_TESSERACT_CMD=/usr/bin/tesseract  # Linux/Mac
# PDF_TESSERACT_CMD=C:\\Program Files\\Tesseract-OCR\\tesseract.exe  # Windows
```

**Logging:**
```bash
LOG_LEVEL=INFO
LOG_DIR=./data/logs
```

### 7.2. Servicios que Deben Estar Activos

**OBLIGATORIOS:**
1. **Base de Datos MySQL**
   - Puerto: 3306
   - Tablas creadas (migración 001)
   - Conexión pool disponible

2. **Backend FastAPI**
   - Puerto: 8000
   - Servidor corriendo
   - Rate limiter activo

3. **Frontend React**
   - Puerto: 3000 (dev) o compilado
   - Proxy configurado a backend

**OPCIONALES (mejoran funcionalidad):**
1. **Ollama** (para clasificación IA)
   - Puerto: 11434
   - Modelo descargado (llama3.1)

2. **ChromaDB** (para RAG)
   - Path: ./data/chromadb
   - Accesible para escritura

3. **Tesseract OCR** (para PDFs escaneados)
   - Instalado en sistema
   - PATH configurado

### 7.3. Credenciales Necesarias

**NO se requieren credenciales para procesar**. El procesamiento trabaja con:
- Expedientes ya descargados
- PDFs ya en el sistema de archivos
- Base de datos local

**Credenciales PJN solo para:**
- Extracción inicial de expedientes
- Monitoreo de cambios
- Descarga de nuevos PDFs

---

## 8. RESUMEN DE ARCHIVOS CLAVE

### 8.1. Frontend

| Archivo | Descripción | Líneas Clave |
|---------|-------------|--------------|
| `ExpedienteDetallePage.tsx` | Componente principal de detalle | 107-154 (handleProcesar) |
| `procesamientoApi.ts` | Cliente API de procesamiento | 67-82 (procesarExpediente) |
| `procesamiento.ts` | Tipos TypeScript | Toda |
| `expedientesStore.ts` | Estado global Zustand | 198-235 (obtenerExpediente) |
| `ProcesamientoStatusBadge.tsx` | Badge de estado visual | Toda |

### 8.2. Backend

| Archivo | Descripción | Líneas Clave |
|---------|-------------|--------------|
| `routers/procesamiento.py` | Router FastAPI | 257-386 (procesar_expediente) |
| `procesador_actuaciones_service.py` | Service principal | 671-773 (procesar_expediente_completo) |
| `core/procesador_pdf/__init__.py` | Core processor | 83-291 (procesar_actuacion, procesar_expediente) |
| `clasificador.py` | Clasificador de utilidad | Toda |
| `extractor_texto.py` | Extractor de PDFs | Toda |
| `analizador_vencimientos.py` | Detector de plazos | Toda |
| `detector_duplicados.py` | Detector de duplicados | Toda |

### 8.3. Base de Datos

| Archivo | Descripción |
|---------|-------------|
| `001_add_procesador_pdf_fields.sql` | Schema completo del sistema de procesamiento |

### 8.4. Configuración

| Archivo | Descripción |
|---------|-------------|
| `.env.example` | Variables de entorno necesarias |
| `infrastructure/config/settings.py` | Configuración centralizada |

---

## 9. POSIBLES PUNTOS DE FALLA O MEJORA

### 9.1. Puntos de Falla

#### 1. Base de Datos
**Problemas:**
- Conexión perdida durante procesamiento
- Tabla llena (disk space)
- Violación de constraints

**Mitigación:**
- Connection pooling
- Retry logic
- Monitoreo de espacio

#### 2. PDFs Corruptos
**Problemas:**
- Archivo no legible
- PDF protegido con contraseña
- Formato no estándar

**Mitigación:**
- Try-catch individual
- Skip con error log
- Validación previa

#### 3. OCR Failures
**Problemas:**
- Tesseract no instalado
- Imagen de baja calidad
- Idioma no soportado

**Mitigación:**
- Fallback a texto embebido
- Error graceful
- Configuración de idioma

#### 4. IA Service Down
**Problemas:**
- Ollama no disponible
- ChromaDB lock
- Timeout en embeddings

**Mitigación:**
- Continúa sin IA
- Marca `indexado_rag = FALSE`
- Retry con backoff

#### 5. Memory Issues
**Problemas:**
- PDFs muy grandes (>100MB)
- Muchas actuaciones (>1000)

**Mitigación:**
- Streaming de PDFs
- Procesamiento en lotes
- Límites de tamaño

### 9.2. Mejoras Sugeridas

#### Performance

1. **Procesamiento en background**
   - Usar BackgroundTasks de FastAPI
   - Retornar inmediatamente al usuario
   - Notificar por WebSocket al completar

2. **Batch processing**
   - Procesar múltiples expedientes en paralelo
   - Queue system (Celery/RQ)
   - Priorización de trabajos

3. **Caché**
   - Cachear clasificaciones comunes
   - Redis para resultados recientes
   - Invalidación inteligente

4. **Índices optimizados**
   - Agregar índices compuestos
   - Analizar queries lentas
   - Particionamiento de tablas grandes

#### UX

1. **Progress bar**
   - Mostrar progreso en tiempo real
   - WebSocket para updates
   - Porcentaje completado

2. **Estimación de tiempo**
   - Calcular tiempo restante
   - Basado en histórico
   - Actualización dinámica

3. **Cancelación**
   - Permitir cancelar procesamiento
   - Rollback parcial
   - Estado "cancelado"

4. **Historial**
   - Ver procesamiento anteriores
   - Comparar resultados
   - Exportar reportes

#### Robustez

1. **Retry logic**
   - Reintentos automáticos
   - Exponential backoff
   - Límite de intentos

2. **Validation**
   - Validar datos antes de procesar
   - Schema validation (Pydantic)
   - Sanitización de inputs

3. **Logging mejorado**
   - Más contexto en logs
   - Correlation IDs
   - Structured logging (JSON)

4. **Health checks**
   - Verificar servicios antes de procesar
   - Endpoint `/health`
   - Dependency checks

#### Funcionalidad

1. **Reprocesamiento selectivo**
   - Solo reprocesar actuaciones modificadas
   - Diff con versión anterior
   - Cambios incrementales

2. **Configuración por usuario**
   - Ajustar umbrales de clasificación
   - Preferencias de procesamiento
   - Templates personalizados

3. **Export**
   - Exportar resultados a Excel
   - Generación de PDF reports
   - API para integraciones

4. **Comparación**
   - Comparar procesamiento antes/después
   - Visualización de cambios
   - Análisis de mejoras

#### Monitoreo

1. **Métricas**
   - Tiempo promedio de procesamiento
   - Tasa de éxito/fallo
   - Recursos utilizados
   - Prometheus/Grafana

2. **Alertas**
   - Notificar si procesamiento falla consistentemente
   - Umbrales de performance
   - Integración con PagerDuty/Slack

3. **Dashboard**
   - Panel de control de procesamiento
   - KPIs en tiempo real
   - Tendencias históricas

---

## 10. CONCLUSIONES

### Fortalezas del Sistema Actual

1. **Arquitectura modular:** Separación clara entre frontend, API y backend
2. **Procesamiento robusto:** Manejo de errores por actuación individual
3. **Integración IA opcional:** Sistema funciona sin dependencias de IA
4. **Base de datos bien diseñada:** Vistas, índices y relaciones optimizadas
5. **UX clara:** Feedback visual claro en cada etapa

### Áreas de Oportunidad

1. **Procesamiento asíncrono:** Para expedientes grandes
2. **Monitoreo y observabilidad:** Métricas y alertas
3. **Optimización de performance:** Caché y batch processing
4. **Testing:** Más cobertura de tests unitarios e integración
5. **Documentación:** Mantener actualizada con cambios

---

**Última actualización:** 2025-11-25
**Versión del documento:** 1.0
**Autor:** Sistema de Documentación Automática
