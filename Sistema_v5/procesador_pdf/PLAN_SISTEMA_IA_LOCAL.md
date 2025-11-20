# Plan: Sistema de IA Local para Análisis de Actuaciones Judiciales

> **Fecha**: 2025-10-31
> **Objetivo**: Implementar un sistema de IA local que mejore el análisis, clasificación y procesamiento de actuaciones judiciales sin depender de APIs externas.
> **Base**: Módulo `procesador_pdf` v1.0 (reglas heurísticas)

---

## 📋 Índice

1. [Visión General](#visión-general)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Stack Tecnológico](#stack-tecnológico)
4. [Componentes del Sistema](#componentes-del-sistema)
5. [Plan de Implementación](#plan-de-implementación)
6. [Requerimientos de Hardware](#requerimientos-de-hardware)
7. [Casos de Uso](#casos-de-uso)
8. [Métricas de Éxito](#métricas-de-éxito)
9. [Riesgos y Mitigaciones](#riesgos-y-mitigaciones)

---

## 1. Visión General

### Objetivos Principales

1. **Independencia de APIs externas**: Sistema 100% local, sin costos por token ni límites de rate
2. **Privacidad de datos**: Información sensible nunca sale del servidor
3. **Análisis avanzado**: Ir más allá de reglas heurísticas con ML/DL
4. **Generación de texto**: Borradores de escritos jurídicos (apelaciones, agravios, etc.)
5. **RAG jurídico**: Búsqueda semántica y generación contextual

### Estado Actual (v1.0)

✅ **Implementado**:
- Clasificador por reglas heurísticas
- Detector de duplicados exactos
- Extractor de texto (PyPDF2 + OCR)
- Analizador de vencimientos por regex

🚀 **A mejorar con IA**:
- Clasificación más precisa (reglas → ML/DL)
- Extracción de entidades (NER jurídico)
- Resumen automático de actuaciones
- Generación de texto jurídico
- Búsqueda semántica (embeddings)

---

## 2. Arquitectura del Sistema

### 2.1 Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE APLICACIÓN                           │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────┐ │
│  │ Web UI     │  │ CLI        │  │ MCP Server │  │ API REST │ │
│  └────────────┘  └────────────┘  └────────────┘  └──────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MÓDULO PROCESADOR_PDF                        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │               CAPA DE IA LOCAL (NUEVA)                     │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │ │
│  │  │Clasif ML │  │NER Juríd │  │Resumen   │  │Gen Texto │  │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              SERVICIOS DE IA BASE                          │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │ │
│  │  │LLM Local │  │Embeddings│  │  Cache   │  │  Queue   │  │ │
│  │  │(Llama 3) │  │(BGE-M3)  │  │ (Redis)  │  │(Celery)  │  │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │           CAPA DE REGLAS HEURÍSTICAS (v1.0)                │ │
│  │  [Clasificador] [Duplicados] [Extractor] [Vencimientos]   │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE PERSISTENCIA                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  MySQL   │  │FAISS/    │  │  Redis   │  │Files/    │       │
│  │(Metadata)│  │ChromaDB  │  │ (Cache)  │  │PDFs      │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Flujo de Procesamiento

```
1. Ingesta de Actuación
   ├─> Extracción de texto (PyPDF2/OCR)
   ├─> Clasificación híbrida (Reglas + ML)
   ├─> NER jurídico (Extracción de entidades)
   ├─> Generación de embeddings
   └─> Almacenamiento (MySQL + Vector Store)

2. Análisis Avanzado
   ├─> RAG: Búsqueda semántica en expediente
   ├─> Resumen automático
   ├─> Detección de duplicados semánticos
   └─> Análisis de vencimientos mejorado

3. Generación de Texto
   ├─> Recuperación de contexto (RAG)
   ├─> Generación con LLM local
   ├─> Post-procesamiento (formato, citas)
   └─> Revisión y aprobación humana
```

---

## 3. Stack Tecnológico

### 3.1 Modelos de IA Local

#### LLMs (Generación de Texto)

**Opción A: Llama 3.1 (8B) - RECOMENDADO**
```yaml
Modelo: meta-llama/Meta-Llama-3.1-8B-Instruct
Tamaño: 8B parámetros (~5GB cuantizado)
Ventajas:
  - Excelente relación calidad/recursos
  - Soporte nativo español
  - Instrucciones bien seguidas
  - Comunidad activa
RAM mínima: 8GB
GPU recomendada: 8GB VRAM (RTX 3060/4060)
Alternativa CPU: Posible con cuantización Q4
```

**Opción B: Mistral 7B Instruct**
```yaml
Modelo: mistralai/Mistral-7B-Instruct-v0.3
Tamaño: 7B parámetros (~4.5GB cuantizado)
Ventajas:
  - Más rápido que Llama 3
  - Menor consumo de memoria
  - Buen seguimiento de instrucciones
Desventajas:
  - Menos robusto en español jurídico
```

**Opción C: Phi-3 Medium (14B)**
```yaml
Modelo: microsoft/Phi-3-medium-128k-instruct
Tamaño: 14B parámetros (~9GB cuantizado)
Ventajas:
  - Contexto extendido (128k tokens)
  - Excelente razonamiento
  - Optimizado para eficiencia
Desventajas:
  - Requiere más recursos
```

#### Embeddings (RAG y Búsqueda Semántica)

**Opción A: BGE-M3 - RECOMENDADO**
```yaml
Modelo: BAAI/bge-m3
Dimensiones: 1024
Ventajas:
  - Multilingüe (excelente español)
  - Estado del arte en retrieval
  - Eficiente (pequeño: 568MB)
  - Soporta textos largos (8192 tokens)
Uso: Embeddings para RAG
```

**Opción B: Multilingual E5**
```yaml
Modelo: intfloat/multilingual-e5-large
Dimensiones: 1024
Ventajas:
  - Muy buen rendimiento multilingüe
  - Menor tamaño que BGE-M3
```

#### NER Jurídico (Extracción de Entidades)

**Opción A: spaCy + Modelo Custom**
```yaml
Base: es_core_news_lg (español)
Custom training:
  - Entidades: PARTE, JUEZ, FECHA, MONTO, NORMA, PLAZO
  - Dataset: Anotaciones de actuaciones reales
  - Transfer learning desde modelo base
```

**Opción B: GLiNER (Zero-shot NER)**
```yaml
Modelo: urchade/gliner_medium-v2.1
Ventajas:
  - No requiere entrenamiento
  - Flexible (define entidades en runtime)
  - Multilingüe
```

### 3.2 Infraestructura de Inferencia

#### Backend LLM

**Opción A: Ollama - RECOMENDADO**
```yaml
Tecnología: llama.cpp wrapper
Ventajas:
  - Instalación simple (1 comando)
  - API REST compatible OpenAI
  - Gestión automática de modelos
  - Cuantización automática
  - Soporte GPU/CPU
Instalación:
  curl -fsSL https://ollama.com/install.sh | sh
  ollama pull llama3.1:8b
```

**Opción B: vLLM**
```yaml
Tecnología: Servidor optimizado para throughput
Ventajas:
  - Mejor performance con GPU
  - Batching inteligente
  - Continuous batching
Desventajas:
  - Más complejo de configurar
  - Solo GPU
```

**Opción C: llama.cpp (Directo)**
```yaml
Tecnología: Inferencia C++
Ventajas:
  - Máximo control
  - Excelente performance CPU
  - Cuantización avanzada
Desventajas:
  - Requiere compilación
  - Sin API REST built-in
```

#### Vector Store

**Opción A: ChromaDB - RECOMENDADO**
```yaml
Tipo: Vector database embebido
Ventajas:
  - Instalación simple (pip install)
  - Persistencia automática
  - API Python amigable
  - Metadatos y filtros
  - Cliente/servidor opcional
```

**Opción B: FAISS + SQLite**
```yaml
Tipo: Librería de Facebook + metadata DB
Ventajas:
  - Extremadamente rápido
  - Menor overhead
Desventajas:
  - Requiere gestión manual de metadata
```

#### Cache y Queue

**Cache: Redis**
```yaml
Uso:
  - Cache de embeddings
  - Cache de respuestas LLM
  - Rate limiting
Configuración:
  maxmemory: 2GB
  eviction-policy: allkeys-lru
```

**Queue: Celery + Redis**
```yaml
Uso:
  - Procesamiento batch de PDFs
  - Generación asíncrona de embeddings
  - Resúmenes en background
Workers: 2-4 (según cores disponibles)
```

### 3.3 Librerías Python

```python
# LLM y Embeddings
ollama==0.1.7              # Cliente Ollama
sentence-transformers==2.3.1  # Embeddings (BGE-M3)
transformers==4.36.0       # HuggingFace (si no usamos Ollama)
torch==2.1.2               # PyTorch

# NER y NLP
spacy==3.7.2
es-core-news-lg            # Modelo español spaCy
gliner==0.1.10             # Zero-shot NER (opcional)

# Vector Store y RAG
chromadb==0.4.22           # Vector database
langchain==0.1.4           # Framework RAG
llama-index==0.9.48        # Alternativa a LangChain

# Cache y Queue
redis==5.0.1
celery==5.3.4

# Utilidades
tenacity==8.2.3            # Retry logic
pydantic==2.5.3            # Validación
tiktoken==0.5.2            # Token counting

# Monitoreo
prometheus-client==0.19.0  # Métricas
```

---

## 4. Componentes del Sistema

### 4.1 Clasificador ML (Mejora del heurístico)

**Enfoque Híbrido: Reglas + ML**

```python
# Arquitectura
class ClasificadorML:
    def __init__(self):
        # Etapa 1: Reglas (rápido, 0ms)
        self.clasificador_reglas = ClasificadorActuaciones()

        # Etapa 2: ML (si score < umbral de confianza)
        self.modelo_ml = self._cargar_modelo()

        # Etapa 3: LLM (casos complejos, opcional)
        self.llm = OllamaClient()

    def clasificar(self, actuacion):
        # 1. Clasificación rápida con reglas
        resultado_reglas = self.clasificador_reglas.clasificar(
            actuacion.tipo, actuacion.detalle
        )

        # 2. Si confianza baja, usar ML
        if resultado_reglas.score < 70:
            features = self._extraer_features(actuacion)
            resultado_ml = self.modelo_ml.predict(features)
            return self._combinar_resultados(resultado_reglas, resultado_ml)

        return resultado_reglas
```

**Modelo ML Propuesto**:
- **Baseline**: Logistic Regression con TF-IDF
- **Avanzado**: BERT jurídico fine-tuned (dccuchile/bert-base-spanish-wwm-cased)
- **Features**: Tipo, detalle, longitud, keywords, estructura

**Dataset de entrenamiento**:
- Anotación manual de 500-1000 actuaciones
- Etiquetas: nula, baja, media, alta
- Validación cruzada 5-fold

### 4.2 NER Jurídico (Extracción de Entidades)

**Entidades a detectar**:
```python
ENTIDADES_JURIDICAS = {
    "PARTE_ACTORA": "Juan Pérez",
    "PARTE_DEMANDADA": "Empresa XYZ S.A.",
    "JUEZ": "Dr. García",
    "FECHA": "15/03/2024",
    "MONTO": "$1.500.000",
    "NORMA": "Art. 242 CPCCN",
    "PLAZO": "5 días hábiles",
    "TIPO_ACTO": "Sentencia definitiva",
    "TRIBUNAL": "Juzgado Civil N° 45",
}
```

**Implementación con GLiNER (Zero-shot)**:
```python
from gliner import GLiNER

class ExtractorEntidadesJuridicas:
    def __init__(self):
        self.model = GLiNER.from_pretrained("urchade/gliner_medium-v2.1")
        self.labels = [
            "parte actora", "parte demandada", "juez", "jueza",
            "fecha", "monto", "norma legal", "plazo",
            "tipo de acto procesal", "tribunal"
        ]

    def extraer(self, texto: str) -> dict:
        entities = self.model.predict_entities(
            texto,
            self.labels,
            threshold=0.5
        )
        return self._estructurar_entidades(entities)
```

### 4.3 Generador de Resúmenes

**Pipeline de resumen**:
```python
class ResumidorActuaciones:
    def __init__(self):
        self.llm = OllamaClient(model="llama3.1:8b")

    def resumir(self, actuacion: dict, max_palabras: int = 100) -> str:
        prompt = f"""
Eres un asistente legal. Resume la siguiente actuación en máximo {max_palabras} palabras,
manteniendo la información jurídica clave.

TIPO: {actuacion['tipo']}
DETALLE: {actuacion['detalle']}
CONTENIDO PDF: {actuacion['texto'][:2000]}

RESUMEN:
"""
        resumen = self.llm.generate(prompt, max_tokens=200)
        return resumen.strip()
```

### 4.4 Sistema RAG (Retrieval Augmented Generation)

**Arquitectura RAG**:
```python
class RAGJuridico:
    def __init__(self):
        # Vector store
        self.chroma = chromadb.PersistentClient(path="./vector_store")
        self.collection = self.chroma.get_or_create_collection(
            name="actuaciones",
            metadata={"hnsw:space": "cosine"}
        )

        # Embeddings
        self.embedder = SentenceTransformer("BAAI/bge-m3")

        # LLM
        self.llm = OllamaClient(model="llama3.1:8b")

    def indexar_actuacion(self, actuacion_id: int, texto: str, metadata: dict):
        # Segmentar texto en chunks
        chunks = self._segmentar_texto(texto, chunk_size=500, overlap=50)

        # Generar embeddings
        embeddings = self.embedder.encode(chunks)

        # Almacenar en ChromaDB
        self.collection.add(
            ids=[f"{actuacion_id}_{i}" for i in range(len(chunks))],
            embeddings=embeddings.tolist(),
            documents=chunks,
            metadatas=[{**metadata, "chunk_idx": i} for i in range(len(chunks))]
        )

    def consultar(self, pregunta: str, expediente_id: int, top_k: int = 5):
        # Embedding de la pregunta
        query_embedding = self.embedder.encode([pregunta])

        # Búsqueda en vector store
        resultados = self.collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=top_k,
            where={"expediente_id": expediente_id}
        )

        # Construir contexto
        contexto = "\n\n".join(resultados['documents'][0])

        # Generar respuesta
        prompt = f"""
Contexto de actuaciones del expediente:
{contexto}

Pregunta: {pregunta}

Responde basándote ÚNICAMENTE en el contexto proporcionado.
Si no puedes responder con la información disponible, dilo claramente.

Respuesta:
"""
        respuesta = self.llm.generate(prompt, max_tokens=500)
        return {
            "respuesta": respuesta,
            "fuentes": resultados['metadatas'][0]
        }
```

### 4.5 Generador de Texto Jurídico

**Plantillas por tipo de escrito**:
```python
PLANTILLAS = {
    "apelacion": {
        "sistema": """Eres un abogado experto en derecho procesal argentino.
Redacta apelaciones formales y bien fundamentadas.""",

        "estructura": [
            "Encabezado (Tribunal, carátula, partes)",
            "Objeto del recurso",
            "Antecedentes procesales",
            "Agravio invocado",
            "Fundamentos de derecho",
            "Doctrina y jurisprudencia aplicable",
            "Petitorio"
        ],

        "prompt": """
EXPEDIENTE: {expediente}
SENTENCIA A APELAR: {sentencia_texto}
MOTIVO DE APELACIÓN: {motivo}

Redacta un escrito de apelación formal contra la sentencia,
enfocándote en {motivo}.
Incluye citas a la normativa aplicable (CPCCN) y jurisprudencia relevante.

ESCRITO DE APELACIÓN:
"""
    },

    "expresion_agravios": {
        "estructura": [...],
        "prompt": "..."
    }
}

class GeneradorTextoJuridico:
    def __init__(self):
        self.llm = OllamaClient(model="llama3.1:8b")
        self.rag = RAGJuridico()

    def generar_apelacion(
        self,
        expediente_id: int,
        sentencia_texto: str,
        motivo: str
    ) -> str:
        # 1. Recuperar contexto vía RAG
        contexto = self.rag.consultar(
            f"Antecedentes relevantes para apelar por {motivo}",
            expediente_id
        )

        # 2. Construir prompt
        plantilla = PLANTILLAS["apelacion"]
        prompt = plantilla["prompt"].format(
            expediente=f"Expediente {expediente_id}",
            sentencia_texto=sentencia_texto[:3000],
            motivo=motivo
        )

        # 3. Generar con LLM
        escrito = self.llm.generate(
            prompt,
            system_prompt=plantilla["sistema"],
            max_tokens=2000,
            temperature=0.7
        )

        # 4. Post-procesar
        escrito_final = self._formatear_escrito(escrito, plantilla["estructura"])

        return escrito_final
```

---

## 5. Plan de Implementación

### Fase 1: Fundamentos (2 semanas)

**Semana 1: Infraestructura**
- [ ] Instalar y configurar Ollama
- [ ] Descargar modelo Llama 3.1 8B
- [ ] Configurar ChromaDB
- [ ] Configurar Redis
- [ ] Crear servicio de embeddings (BGE-M3)
- [ ] Tests de integración básicos

**Semana 2: NER y Clasificador ML**
- [ ] Implementar GLiNER para NER jurídico
- [ ] Crear dataset de entrenamiento para clasificador (100 actuaciones anotadas)
- [ ] Entrenar clasificador ML baseline (Logistic Regression)
- [ ] Integrar clasificador híbrido (reglas + ML)
- [ ] Tests y métricas de performance

**Entregables**:
- ✅ Ollama funcionando con Llama 3.1
- ✅ ChromaDB operativo
- ✅ NER jurídico extrayendo entidades
- ✅ Clasificador ML con >85% accuracy

### Fase 2: RAG y Resúmenes (2 semanas)

**Semana 3: Sistema RAG**
- [ ] Implementar pipeline de indexación
- [ ] Segmentación inteligente de textos
- [ ] Generación y almacenamiento de embeddings
- [ ] API de consulta RAG
- [ ] Interface de búsqueda semántica

**Semana 4: Generador de Resúmenes**
- [ ] Implementar resumidor de actuaciones
- [ ] Generador de timelines del expediente
- [ ] Extractor de hechos clave
- [ ] Tests con actuaciones reales
- [ ] Optimización de prompts

**Entregables**:
- ✅ RAG funcional con búsqueda semántica
- ✅ Resúmenes automáticos de actuaciones
- ✅ Timeline automático de expedientes

### Fase 3: Generación de Texto (2-3 semanas)

**Semana 5-6: Generador de Escritos**
- [ ] Plantillas de apelaciones
- [ ] Plantillas de expresión de agravios
- [ ] Plantillas de contestación de demanda
- [ ] Sistema de validación y review
- [ ] Generación de .docx formateados

**Semana 7: Integración y Optimización**
- [ ] Integrar con procesador_pdf v1.0
- [ ] Optimizar performance (cache, batching)
- [ ] Sistema de feedback para mejora continua
- [ ] Dashboard de métricas
- [ ] Documentación completa

**Entregables**:
- ✅ Generador de apelaciones funcional
- ✅ Generador de expresión de agravios
- ✅ Sistema de revisión humana
- ✅ Métricas de calidad

### Fase 4: Producción (1-2 semanas)

**Semana 8-9: Deploy y Monitoreo**
- [ ] Configuración de producción
- [ ] Sistema de monitoreo (Prometheus + Grafana)
- [ ] Alertas y logging
- [ ] Backups automáticos
- [ ] Documentación de operaciones
- [ ] Capacitación de usuarios

**Entregables**:
- ✅ Sistema en producción
- ✅ Monitoreo operativo
- ✅ Documentación completa

---

## 6. Requerimientos de Hardware

### Configuración Mínima (Para desarrollo y testing)

```yaml
CPU: 4 cores (Intel i5/Ryzen 5 o superior)
RAM: 16GB DDR4
GPU: Opcional (CPU funciona)
Disco: 100GB SSD
OS: Ubuntu 22.04 LTS / Windows 11 / macOS

Modelos:
  - Llama 3.1 8B cuantizado Q4: ~5GB RAM
  - BGE-M3 embeddings: ~2GB RAM
  - ChromaDB: ~2GB RAM
  - Redis cache: ~1GB RAM
  - OS y servicios: ~4GB RAM
  TOTAL: ~14GB RAM en uso

Performance esperada:
  - Clasificación: 50-100 actuaciones/seg
  - Generación texto: 15-25 tokens/seg (CPU)
  - Embeddings: 50-100 docs/seg
```

### Configuración Recomendada (Para producción)

```yaml
CPU: 8+ cores (Intel i7/Ryzen 7 o superior)
RAM: 32GB DDR4
GPU: NVIDIA RTX 3060 (8GB VRAM) o superior
Disco: 500GB NVMe SSD
OS: Ubuntu 22.04 LTS Server

Modelos:
  - Llama 3.1 8B con GPU: ~8GB VRAM
  - Alternativa: Llama 3.1 70B cuantizado (16GB VRAM)

Performance esperada (con GPU):
  - Clasificación: 200-500 actuaciones/seg
  - Generación texto: 50-80 tokens/seg
  - Embeddings: 200-300 docs/seg
```

### Configuración Óptima (Para alto volumen)

```yaml
CPU: 16+ cores (Threadripper/Xeon)
RAM: 64GB DDR4
GPU: NVIDIA RTX 4090 (24GB VRAM) o A100
Disco: 1TB+ NVMe RAID
OS: Ubuntu 22.04 LTS Server

Modelos:
  - Llama 3.1 70B: Calidad superior
  - Múltiples workers en paralelo

Performance esperada:
  - Clasificación: 500-1000 actuaciones/seg
  - Generación texto: 80-120 tokens/seg
  - Procesamiento batch: Miles de PDFs/día
```

---

## 7. Casos de Uso

### 7.1 Clasificación Mejorada

**Antes (v1.0 - Reglas)**:
```
Tipo: PROVIDENCIA
Detalle: "Atento el estado procesal y lo peticionado, provéase"
→ Score: 35 (MEDIA) - Requiere revisión PDF
```

**Después (v2.0 - ML + LLM)**:
```
Análisis híbrido:
1. Reglas: Score 35 (confianza baja)
2. ML: Detecta patrón "provéase" → Score 15 (BAJA)
3. NER: No extrae entidades relevantes
→ Score final: 10 (NULA) - Descartar

Ahorro: No requiere abrir PDF
```

### 7.2 Extracción de Información

**Input**: PDF de sentencia (10 páginas)

**Output**:
```json
{
  "resumen": "Sentencia definitiva que rechaza la demanda por falta de legitimación activa...",
  "partes": {
    "actora": "María González",
    "demandada": "Banco Nacional S.A."
  },
  "juez": "Dr. Roberto Fernández",
  "fecha": "2024-10-15",
  "tipo_resolucion": "Sentencia definitiva",
  "fallo": "Rechaza la demanda",
  "fundamento_principal": "Falta de legitimación activa (Art. 242 CPCCN)",
  "costas": "A cargo de la parte actora",
  "apelable": true,
  "plazo_apelacion": "5 días hábiles"
}
```

### 7.3 Generación de Apelación

**Input**:
```python
generar_apelacion(
    expediente_id=12345,
    sentencia="[Texto completo de la sentencia...]",
    motivo="Errónea valoración de la prueba documental"
)
```

**Output**: Escrito de 3-4 páginas con:
```
SEÑOR JUEZ:

    [Encabezado formal con carátula]

I. OBJETO

    Vengo por el presente a interponer recurso de apelación contra la
    sentencia de fecha [fecha] que rechazó la demanda...

II. ANTECEDENTES

    [Cronología del caso extraída vía RAG]

III. AGRAVIO

    La sentencia incurre en error al valorar la prueba documental
    obrante a fs. XX, específicamente...

    [Argumentación fundamentada con citas al CPCCN y jurisprudencia]

IV. DERECHO

    Conforme lo establece el Art. 242 del CPCCN...

    [Citas legales y jurisprudenciales relevantes]

V. PETITORIO

    Por todo lo expuesto, solicito:
    1. Se tenga por interpuesto el presente recurso...
    2. Se revoque la sentencia apelada...

Proveer de conformidad,
SERÁ JUSTICIA.
```

### 7.4 Búsqueda Semántica (RAG)

**Consulta**: "¿Cuál fue el monto reclamado en la demanda inicial?"

**Proceso**:
1. Embedding de la consulta
2. Búsqueda en vector store (top 5 chunks relevantes)
3. Generación de respuesta con LLM + contexto

**Respuesta**:
```
Según la demanda presentada el 15/03/2023 (fs. 1-12),
el monto reclamado es de $2.500.000 (pesos dos millones
quinientos mil) en concepto de daños y perjuicios.

Fuentes:
- Actuación #5 (Demanda inicial) - fs. 3
- Actuación #12 (Ampliación de demanda) - fs. 45
```

---

## 8. Métricas de Éxito

### KPIs Técnicos

```yaml
Clasificador ML:
  - Accuracy: >90% (vs 85% reglas)
  - Precision (ALTA): >92%
  - Recall (ALTA): >88%
  - F1-score: >90%
  - Tiempo promedio: <50ms

NER Jurídico:
  - Precision entidades: >85%
  - Recall entidades: >80%
  - Entidades/documento: 5-15

RAG:
  - Relevancia top-5: >80%
  - Tiempo de consulta: <2seg
  - Coherencia respuesta: >85% (evaluación humana)

Generación de Texto:
  - Aceptación humana: >75%
  - Requiere edición mínima: >60%
  - Tiempo generación: <30seg
  - Citas correctas: >90%

Performance:
  - Throughput clasificación: >100 docs/seg
  - Latencia P95 generación: <5seg
  - Uptime: >99%
```

### KPIs de Negocio

```yaml
Eficiencia:
  - Reducción tiempo análisis: 60%
  - Actuaciones procesadas/día: 10x
  - Costo/documento: $0 (vs API externa)

Calidad:
  - Satisfacción usuario: >80%
  - Errores críticos: <1%
  - Escritos aprobados sin cambios: >40%

ROI:
  - Ahorro en horas/abogado: 10-15 hrs/semana
  - Payback: <3 meses
```

---

## 9. Riesgos y Mitigaciones

### Riesgos Técnicos

| Riesgo | Impacto | Probabilidad | Mitigación |
|--------|---------|--------------|------------|
| Performance insuficiente con CPU | Alto | Media | Usar cuantización Q4, optimizar batch size, considerar GPU |
| Calidad LLM no suficiente | Alto | Media | Fine-tuning en dataset jurídico, mejores prompts, modelo más grande |
| Embeddings no capturan semántica jurídica | Medio | Media | Fine-tuning de BGE-M3, usar modelo jurídico específico |
| Consumo excesivo de RAM | Medio | Alta | Cuantización, streaming, procesamiento batch |
| Vector store crece demasiado | Bajo | Alta | Compresión, archivado de expedientes antiguos |

### Riesgos de Negocio

| Riesgo | Impacto | Probabilidad | Mitigación |
|--------|---------|--------------|------------|
| Resistencia de usuarios | Alto | Media | Capacitación, pruebas piloto, feedback continuo |
| Errores en documentos generados | Crítico | Baja | Revisión humana obligatoria, disclaimers claros |
| Tiempo de implementación excede | Medio | Alta | MVP primero, iteraciones rápidas, scope controlado |
| Hardware inadecuado | Alto | Media | Benchmarks previos, plan de upgrade, cloud backup |

---

## 10. Próximos Pasos

### Inmediato (Esta semana)

1. ✅ **Aprobar plan**: Revisar y aprobar este documento
2. 🔄 **Setup inicial**: Instalar Ollama y Llama 3.1
3. 🔄 **POC clasificador**: Probar clasificación con LLM vs reglas

### Corto plazo (Próximas 2 semanas)

1. Completar Fase 1 (Infraestructura + NER)
2. Crear dataset de entrenamiento (100 actuaciones)
3. Implementar clasificador híbrido
4. Benchmarks de performance

### Mediano plazo (1-2 meses)

1. Implementar RAG completo
2. Generador de resúmenes
3. Integración con sistema existente
4. Tests con usuarios reales

### Largo plazo (3-6 meses)

1. Generación de texto jurídico
2. Fine-tuning de modelos
3. Optimizaciones de producción
4. Expansión a otros tipos de escritos

---

## Conclusión

Este plan propone un sistema de IA local robusto y escalable que:

✅ **Mejora** el clasificador actual (reglas → ML/DL)
✅ **Añade** capacidades avanzadas (NER, RAG, generación)
✅ **Mantiene** privacidad (100% local)
✅ **Elimina** costos de APIs externas
✅ **Escala** con el volumen de trabajo

**Inversión estimada**:
- Tiempo desarrollo: 8-9 semanas
- Hardware: $1,500-$3,000 USD (GPU recomendada)
- Costo operativo: Electricidad (~$50/mes)

**Retorno esperado**:
- Ahorro tiempo: 60% en análisis de actuaciones
- Capacidad: 10x más documentos procesados
- Calidad: Escritos jurídicos en minutos vs horas
- Privacidad: Datos sensibles nunca salen del servidor

---

**¿Listo para comenzar?** 🚀

Próximo paso: Aprobar plan e iniciar Fase 1 (Infraestructura)
