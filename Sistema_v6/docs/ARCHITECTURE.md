# Arquitectura del Sistema: Pipeline de IA y Workflow

## Resumen del Workflow: Expedientes → Ver Detalle → Procesar

### 1. Lista de Expedientes (ExpedientesPage)
- Se cargan los expedientes desde `GET /api/v1/expedientes`
- Se muestran en tarjetas (`ExpedienteCard`)

### 2. Ver Detalle
- Clic en "Ver detalle" navega a `/expedientes/{numero}`
- `ExpedienteDetallePage` llama a:
  - `GET /api/v1/expedientes/{numero}` → datos básicos
  - `GET /api/v1/expedientes/{numero}/actuaciones` → lista de actuaciones

### 3. Procesar (handleProcesar)
Al hacer clic en el botón "Procesar":

1. **Prepara los datos**: Convierte las actuaciones al formato `ActuacionInput[]` con sus rutas PDF
2. **Llama al backend**:
   ```http
   POST /api/v1/procesamiento/expediente
   {
     "numero_expediente": "...",
     "actuaciones": [...],
     "rutas_pdf": {...},
     "guardar_en_bd": true
   }
   ```
3. **Recibe respuesta** con:
   - Estadísticas (total, alta/media/baja/nula utilidad, vencimientos)
   - Vencimientos urgentes
   - Tiempo de procesamiento
4. **Carga datos adicionales**:
   - `GET .../estadisticas`
   - `GET .../actuaciones-clasificadas`
   - `GET .../vencimientos`
5. **Actualiza la UI**: Muestra panel de estadísticas y lista de actuaciones clasificadas por utilidad

#### Componentes clave
| Componente | Función |
|------------|---------|
| `ProcesamientoStatusBadge` | Botón "Procesar" + estado |
| `EstadisticasExpedientePanel` | Gráficos de resultados |
| `ActuacionesClasificadasList` | Actuaciones ordenadas por utilidad |

---

## Resumen del Pipeline de IA (Backend)

Cuando se hace clic en "Procesar", el backend ejecuta este pipeline:

### 1. Endpoint
`POST /api/v1/procesamiento/expediente` → `procesamiento.py`

### 2. Clasificación de Utilidad (`clasificador.py`)
Clasifica cada actuación usando heurísticas:

| Utilidad | Score | Ejemplos |
|----------|-------|----------|
| **ALTA** | 80-95 | Sentencias, resoluciones, demandas, apelaciones |
| **MEDIA** | 45-65 | Solicitudes, informes, traslados, certificados |
| **BAJA** | 15-35 | Cargos, constancias, devoluciones |
| **NULA** | 5-15 | Providencias simples ("agréguese", "téngase presente") |

### 3. Extracción de Texto (`extractor_texto.py`)
- Extrae texto embebido de PDFs (`PyPDF2`)
- Fallback a OCR (`Tesseract`) si es necesario
- Calcula hash MD5 para detectar duplicados

### 4. Detección de Vencimientos (`analizador_vencimientos.py`)
- Detecta plazos mediante regex (cédulas, traslados, alegatos)
- Calcula fecha de vencimiento considerando:
  - Días hábiles
  - Feriados nacionales
  - Feria judicial

### 5. Detección de Duplicados (`detector_duplicados.py`)
- Duplicados exactos (hash MD5)
- Duplicados semánticos (similitud coseno)

### 6. Servicios IA Avanzados (`ia_integration_service.py`)

| Servicio | Modelo | Función |
|----------|--------|---------|
| **Clasificación IA** | LLM (Ollama/Claude) | Mejora clasificación con justificación |
| **NER** | GLiNER | Extrae 18 tipos de entidades (personas, tribunales, montos, fechas...) |
| **Normalización** | Reglas | Estandariza entidades extraídas |
| **RAG** | Qdrant + BM25 | Indexa para búsqueda semántica |

### 7. Persistencia en BD
Se guardan en MySQL:
- `actuaciones` → clasificación, texto extraído, campos IA
- `vencimientos` → plazos detectados
- `duplicados_detectados` → duplicados encontrados
- `procesamiento_estadisticas` → métricas globales
- `entidades_extraidas` → entidades NER

### 8. Respuesta al Frontend
```json
{
  "estadisticas": {
    "total_actuaciones": 150,
    "actuaciones_alta/media/baja/nula": "...",
    "reduccion_estimada_pct": 42.5,
    "vencimientos_urgentes": 2
  },
  "vencimientos_urgentes": [...],
  "entidades_por_actuacion": {...}
}
```

---

## Archivos Clave del Sistema IA

```
Sistema_v6/
├── core/procesador_pdf/
│   ├── clasificador.py            # Clasificación heurística
│   ├── analizador_vencimientos.py # Detección de plazos
│   ├── extractor_texto.py         # Extracción PDF/OCR
│   └── detector_duplicados.py     # Duplicados
├── application/services/ia/
│   ├── ia_integration_service.py  # Orquestador IA
│   ├── ner_service.py             # GLiNER (entidades)
│   ├── rag_service.py             # Búsqueda semántica
│   └── entity_normalizer.py       # Normalización
└── presentation/api/rest/routers/
    └── procesamiento.py           # Endpoint principal
```
