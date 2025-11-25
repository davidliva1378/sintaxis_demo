# Plan: Mejorar RAG y NER con LLM

> **Fecha**: 2025-11-25
> **Prioridad**: RAG primero, luego NER
> **Complejidad**: Implementación completa
> **Estado**: EN PROGRESO (6/9 tareas completadas)

---

## Contexto del Sistema

### Perfiles de Hardware

| Perfil | CPU | RAM | GPU | Uso |
|--------|-----|-----|-----|-----|
| `development` | Apple Silicon / Intel | 24 GB | Integrada/CPU | Desarrollo local (Mac) |
| `production` | Intel i7-11700KF | 32 GB DDR4 | RTX 3060 12GB | **Servidor producción** |

### Configuración por Perfil

```python
# config/hardware_profiles.py

HARDWARE_PROFILES = {
    "development": {
        "llm_model": "llama3.1:8b",
        "llm_num_ctx": 4096,
        "embedding_device": "cpu",
        "rerank_device": "cpu",
        "ner_device": "cpu",
        "batch_size": 4,
        "max_concurrent_requests": 2,
    },
    "production": {
        "llm_model": "llama3.1:70b",  # Modelo grande con GPU
        "llm_num_ctx": 8192,           # Más contexto
        "embedding_device": "cuda",    # GPU para embeddings
        "rerank_device": "cuda",       # GPU para reranking
        "ner_device": "cuda",          # GPU para GLiNER
        "batch_size": 16,              # Batches más grandes
        "max_concurrent_requests": 8,  # Más concurrencia
    }
}
```

### Estado Actual del Sistema

| Componente | Desarrollo (Mac) | Producción (i7 + RTX 3060) |
|------------|------------------|---------------------------|
| Modelo LLM | llama3.1:8b | llama3.1:70b o mistral-nemo:12b |
| Contexto LLM | 4096 tokens | 8192-16384 tokens |
| Embeddings | CPU (~500ms) | CUDA (~50ms) |
| Reranking | CPU (~200ms) | CUDA (~20ms) |
| GLiNER NER | CPU (~100ms) | CUDA (~10ms) |
| Concurrencia | 2 requests | 8+ requests |

### Modelos Recomendados para Producción (RTX 3060 12GB)

| Modelo | VRAM | Calidad | Velocidad | Recomendado |
|--------|------|---------|-----------|-------------|
| llama3.1:8b | ~6GB | Buena | Rápido | Para pruebas |
| mistral-nemo:12b | ~8GB | Muy buena | Medio | **Balance ideal** |
| llama3.1:70b-q4 | ~10GB | Excelente | Lento | Máxima calidad |
| qwen2.5:14b | ~9GB | Muy buena | Medio | Alternativa |

> **Recomendación**: Usar `mistral-nemo:12b` en producción - excelente balance calidad/velocidad para 12GB VRAM.

---

## FASE 1: Mejoras RAG (Prioridad Alta)

### TAREA 1.1: Query Expansion con LLM ✅
- [x] **Estado**: COMPLETADA
- **Impacto**: ALTO
- **Archivo**: `infrastructure/rag/services/query_expansion_service.py` (NUEVO)

**Descripción**: LLM genera variaciones semánticas de la búsqueda para mejorar recall.

```python
class QueryExpansionService:
    def __init__(self, llm_service):
        self.llm = llm_service

    def expand(self, query: str, n_variations: int = 3) -> List[str]:
        prompt = f"""
        Genera {n_variations} variaciones semánticas de esta pregunta legal:
        "{query}"

        Incluye sinónimos jurídicos y reformulaciones.
        Retorna JSON: ["variación1", "variación2", ...]
        """
        variations = self.llm.generate(prompt, temperature=0.3)
        return json.loads(variations) + [query]  # Original + expansiones
```

**Integración**: Modificar `hybrid_search_service.py` línea ~80 para usar expansiones.

---

### TAREA 1.2: Cross-Encoder Reranking ✅
- [x] **Estado**: COMPLETADA
- **Impacto**: ALTO
- **Archivo**: `infrastructure/rag/services/reranker_service.py` (NUEVO)
- **Dependencia**: `pip install sentence-transformers`

**Descripción**: Re-ordena resultados usando modelo de relevancia contextual.

```python
class RerankerService:
    def __init__(self):
        from sentence_transformers import CrossEncoder
        self.model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        self._loaded = False

    def _lazy_load(self):
        if not self._loaded:
            # Cargar modelo solo cuando se necesita
            self._loaded = True

    def rerank(self, query: str, results: List[SearchResult], top_k: int) -> List[SearchResult]:
        self._lazy_load()
        pairs = [(query, r.texto) for r in results]
        scores = self.model.predict(pairs)

        # Actualizar scores y ordenar
        for i, score in enumerate(scores):
            results[i].rerank_score = float(score)

        ranked = sorted(results, key=lambda x: x.rerank_score, reverse=True)
        return ranked[:top_k]
```

**Integración**: Reemplazar línea 294 de `hybrid_search_service.py`:
```python
# ANTES: return results[:top_k]
# DESPUÉS: return self.reranker.rerank(query, results, top_k)
```

---

### TAREA 1.3: Prompts Dinámicos por Tipo de Pregunta
- [ ] **Estado**: PENDIENTE
- **Impacto**: MEDIO
- **Archivo**: `infrastructure/rag/services/llm_service.py` línea 100-138

**Descripción**: Detectar tipo de pregunta y adaptar prompt del sistema.

```python
PROMPT_TEMPLATES = {
    "factual": """Responde con hechos concretos del expediente.
                  Cita fechas, nombres y eventos específicos.""",

    "analisis": """Analiza el razonamiento jurídico.
                   Explica fundamentos legales y precedentes citados.""",

    "temporal": """Ordena cronológicamente los eventos.
                   Identifica plazos y vencimientos.""",

    "procesal": """Indica el estado procesal actual.
                   Sugiere próximos pasos según el procedimiento."""
}

def detect_question_type(query: str) -> str:
    query_lower = query.lower()
    if any(w in query_lower for w in ["qué pasó", "qué ocurrió", "cuáles son los hechos"]):
        return "factual"
    elif any(w in query_lower for w in ["por qué", "fundamento", "razón"]):
        return "analisis"
    elif any(w in query_lower for w in ["cuándo", "fecha", "plazo", "término"]):
        return "temporal"
    elif any(w in query_lower for w in ["qué sigue", "próximo paso", "estado"]):
        return "procesal"
    return "factual"  # default
```

---

### TAREA 1.4: Chain-of-Thought Reasoning
- [ ] **Estado**: PENDIENTE
- **Impacto**: MEDIO
- **Archivo**: `infrastructure/rag/services/llm_service.py`

**Descripción**: Modificar prompt para incluir razonamiento paso a paso con citas.

```python
SYSTEM_PROMPT_COT = """
Eres un asistente jurídico argentino experto en análisis de expedientes judiciales.

PROCESO DE RESPUESTA (sigue estos pasos):
1. ANÁLISIS: Identifica qué información relevante hay en los documentos proporcionados
2. CONEXIÓN: Relaciona la información con la pregunta del usuario
3. RESPUESTA: Formula una respuesta clara y estructurada
4. CITAS: Indica exactamente de qué documento obtuviste cada información

REGLAS:
- SOLO usa información de los documentos proporcionados
- Si no encuentras la información, indícalo claramente
- Cita siempre la fuente: [Doc X, párrafo Y]
- Usa terminología jurídica argentina apropiada
"""
```

---

### TAREA 1.5: Compresión de Contexto
- [ ] **Estado**: PENDIENTE
- **Impacto**: MEDIO
- **Archivo**: `infrastructure/rag/services/context_compressor.py` (NUEVO)

**Descripción**: Resume chunks manteniendo información relevante para la query.

```python
class ContextCompressor:
    def __init__(self, llm_service):
        self.llm = llm_service

    def compress(self, chunks: List[str], query: str, max_chars: int = 3000) -> str:
        if sum(len(c) for c in chunks) <= max_chars:
            return "\n---\n".join(chunks)

        compressed = []
        for i, chunk in enumerate(chunks):
            prompt = f"""
            Resume este fragmento de documento judicial,
            manteniendo SOLO información relevante para: "{query}"

            Fragmento:
            {chunk[:1500]}

            Resumen (máximo 200 palabras):
            """
            summary = self.llm.generate(prompt, temperature=0.1, max_tokens=300)
            compressed.append(f"[Doc {i+1}] {summary}")

        return "\n---\n".join(compressed)
```

---

## FASE 2: Mejoras NER (Prioridad Media)

### TAREA 2.1: LLM Fallback para Entidades de Baja Confianza ✅
- [x] **Estado**: COMPLETADA
- **Impacto**: ALTO
- **Archivo**: `application/services/ia/ner_service.py`

**Descripción**: Usar LLM cuando GLiNER tiene score bajo.

```python
def extract_with_llm_fallback(self, text: str, threshold: float = 0.5) -> List[Entity]:
    # GLiNER primero (rápido: ~50-100ms)
    entities = self.model.predict_entities(text[:1500], self.labels, threshold=0.3)

    # Separar por confianza
    high_confidence = [e for e in entities if e['score'] >= threshold]
    low_confidence = [e for e in entities if e['score'] < threshold]

    # LLM para casos dudosos (lento: ~2-5s, pero preciso)
    if low_confidence:
        labels_to_check = list(set(e['label'] for e in low_confidence))
        llm_entities = self._extract_with_llm(text, labels_to_check)
        high_confidence.extend(llm_entities)

    return self._deduplicate(high_confidence)

def _extract_with_llm(self, text: str, labels: List[str]) -> List[Entity]:
    prompt = f"""
    Extrae las siguientes entidades del texto judicial:
    Tipos a buscar: {', '.join(labels)}

    Texto:
    {text[:2000]}

    Retorna JSON:
    [
        {{"text": "valor encontrado", "label": "TIPO", "score": 0.9}},
        ...
    ]

    IMPORTANTE: Solo incluye entidades CLARAMENTE presentes en el texto.
    """
    response = self.llm.generate(prompt, temperature=0.1)
    return json.loads(response)
```

---

### TAREA 2.2: Extracción de Relaciones ✅
- [x] **Estado**: COMPLETADA
- **Impacto**: ALTO
- **Archivo**: `application/services/ia/relation_extraction_service.py` (NUEVO)

**Descripción**: Conectar entidades con sus relaciones (quién demanda a quién, etc.)

```python
class RelationExtractionService:
    def __init__(self, llm_service):
        self.llm = llm_service

    def extract_relations(self, text: str, entities: List[Entity]) -> Dict:
        entity_names = [e['text'] for e in entities]

        prompt = f"""
        Analiza este texto judicial y extrae relaciones entre las entidades mencionadas.

        Entidades encontradas: {entity_names}

        Texto:
        {text[:2000]}

        Retorna JSON con estructura:
        {{
            "demanda": {{
                "actor": "nombre completo del demandante",
                "demandado": "nombre completo del demandado",
                "objeto": "descripción breve de qué se demanda"
            }},
            "representacion": [
                {{"parte": "nombre de la parte", "abogado": "nombre del abogado"}}
            ],
            "tribunal": {{
                "juzgado": "nombre del juzgado",
                "juez": "nombre del juez",
                "secretario": "nombre del secretario"
            }},
            "montos": [
                {{"concepto": "qué es", "monto": "valor numérico", "moneda": "ARS/USD"}}
            ]
        }}

        IMPORTANTE: Solo incluye relaciones EXPLÍCITAS en el texto.
        """
        response = self.llm.generate(prompt, temperature=0.1)
        return json.loads(response)
```

---

### TAREA 2.3: Normalización Inteligente
- [ ] **Estado**: PENDIENTE
- **Impacto**: MEDIO
- **Archivo**: `application/services/ia/entity_normalizer.py` (NUEVO)

**Descripción**: Estandarizar formatos de entidades.

```python
class EntityNormalizer:
    def __init__(self, llm_service):
        self.llm = llm_service

    def normalize(self, entities: List[Entity]) -> List[Entity]:
        # Agrupar por tipo
        by_type = {}
        for e in entities:
            by_type.setdefault(e['label'], []).append(e['text'])

        prompt = f"""
        Normaliza estas entidades jurídicas:
        {json.dumps(by_type, ensure_ascii=False)}

        Reglas:
        - PERSONA: "Juan Carlos García" (capitalizado, sin títulos)
        - FECHA: "2025-01-15" (formato ISO)
        - MONTO: "1500000.00 ARS" (número + moneda)
        - TRIBUNAL: Nombre completo normalizado
        - Deduplica variaciones del mismo nombre

        Retorna JSON con mapeo:
        {{
            "original": "normalizado",
            "JUAN CARLOS": "Juan Carlos García",
            ...
        }}
        """
        mapping = json.loads(self.llm.generate(prompt, temperature=0.1))

        # Aplicar normalización
        for e in entities:
            if e['text'] in mapping:
                e['text_normalized'] = mapping[e['text']]
                e['text_original'] = e['text']
                e['text'] = mapping[e['text']]

        return entities
```

---

### TAREA 2.4: Chunking para Textos Largos
- [ ] **Estado**: PENDIENTE
- **Impacto**: MEDIO
- **Archivo**: `application/services/ia/ner_service.py`

**Descripción**: Dividir textos largos para no perder entidades.

```python
def extract_with_chunking(self, text: str, chunk_size: int = 1500, overlap: int = 200) -> List[Entity]:
    if len(text) <= chunk_size:
        return self.extract(text)

    # Dividir en chunks con overlap
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append((start, text[start:end]))
        start += chunk_size - overlap

    all_entities = []
    for chunk_start, chunk_text in chunks:
        entities = self.extract(chunk_text)
        # Ajustar posiciones al texto original
        for e in entities:
            e['start'] += chunk_start
            e['end'] += chunk_start
        all_entities.extend(entities)

    # Deduplicar entidades solapadas
    return self._deduplicate_by_position(all_entities)

def _deduplicate_by_position(self, entities: List[Entity]) -> List[Entity]:
    # Ordenar por posición
    entities.sort(key=lambda x: (x['start'], -x['score']))

    result = []
    last_end = -1
    for e in entities:
        if e['start'] >= last_end:
            result.append(e)
            last_end = e['end']
        elif e['score'] > result[-1]['score']:
            # Reemplazar si tiene mejor score
            result[-1] = e
            last_end = e['end']

    return result
```

---

## FASE 3: Integración y API

### TAREA 3.1: Nuevos Endpoints RAG ✅
- [x] **Estado**: COMPLETADA (endpoints agregados en ia.py)
- **Archivo**: `presentation/api/rest/routers/rag.py`

```python
@router.post("/query-enhanced", response_model=EnhancedQueryResponse)
async def query_enhanced(
    request: EnhancedQueryRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    RAG mejorado con:
    - Query expansion (genera variaciones)
    - Cross-encoder reranking
    - Chain-of-Thought reasoning
    - Citas explícitas
    """
    return await rag_service.query_enhanced(
        pregunta=request.pregunta,
        expediente_numero=request.expediente_numero,
        enable_expansion=request.enable_expansion,
        enable_reranking=request.enable_reranking,
        top_k=request.limite
    )
```

---

### TAREA 3.2: Nuevo Endpoint Relaciones ✅
- [x] **Estado**: COMPLETADA
- **Archivo**: `presentation/api/rest/routers/ia.py`

```python
@router.post("/ner/relaciones", response_model=RelacionesResponse)
async def extract_relations(
    request: RelacionesRequest,
    ner_service: NERService = Depends(get_ner_service),
    relation_service: RelationExtractionService = Depends(get_relation_service)
):
    """Extrae entidades y sus relaciones de un texto judicial."""
    # Primero extraer entidades
    entities = await ner_service.extract_with_llm_fallback(request.texto)

    # Luego extraer relaciones
    relations = await relation_service.extract_relations(request.texto, entities)

    return {
        "entidades": entities,
        "relaciones": relations
    }
```

---

### TAREA 3.3: Configuración Global
- [ ] **Estado**: PENDIENTE
- **Archivo**: `infrastructure/rag/config.py`

```python
@dataclass
class RAGEnhancedConfig:
    # Query Expansion
    enable_query_expansion: bool = True
    num_query_variations: int = 3

    # Reranking
    enable_reranking: bool = True
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    rerank_top_k: int = 10  # Rerank top 10, return top 5

    # Chain of Thought
    enable_cot_reasoning: bool = True

    # Context Compression
    enable_compression: bool = False  # Opcional, consume tokens
    max_context_chars: int = 4000

    # NER
    ner_llm_fallback_threshold: float = 0.5
    ner_enable_chunking: bool = True
    ner_chunk_size: int = 1500
```

---

## Archivos a Crear/Modificar

### Archivos NUEVOS (5)
| Archivo | Descripción |
|---------|-------------|
| `infrastructure/rag/services/query_expansion_service.py` | Expansión de queries |
| `infrastructure/rag/services/reranker_service.py` | Cross-encoder reranking |
| `infrastructure/rag/services/context_compressor.py` | Compresión de contexto |
| `application/services/ia/relation_extraction_service.py` | Extracción de relaciones |
| `application/services/ia/entity_normalizer.py` | Normalización de entidades |

### Archivos a MODIFICAR (6)
| Archivo | Cambios |
|---------|---------|
| `infrastructure/rag/services/hybrid_search_service.py` | Integrar expansion + reranking |
| `infrastructure/rag/services/llm_service.py` | Prompts dinámicos + CoT |
| `infrastructure/rag/config.py` | Nuevas opciones de config |
| `application/services/ia/ner_service.py` | LLM fallback + chunking |
| `presentation/api/rest/routers/rag.py` | Endpoint /query-enhanced |
| `presentation/api/rest/routers/ia.py` | Endpoint /ner/relaciones |

---

## Orden de Implementación Recomendado

| # | Tarea | Impacto | Dependencia |
|---|-------|---------|-------------|
| 1 | Query Expansion (1.1) | ALTO | - |
| 2 | Cross-Encoder Reranking (1.2) | ALTO | pip install sentence-transformers |
| 3 | LLM Fallback NER (2.1) | ALTO | - |
| 4 | Chain-of-Thought (1.4) | MEDIO | - |
| 5 | Extracción Relaciones (2.2) | ALTO | 2.1 |
| 6 | Prompts Dinámicos (1.3) | MEDIO | - |
| 7 | Compresión Contexto (1.5) | MEDIO | - |
| 8 | Normalización (2.3) | MEDIO | 2.1 |
| 9 | Chunking NER (2.4) | MEDIO | - |

---

## Dependencias Adicionales

```bash
# Cross-encoder para reranking
pip install sentence-transformers

# Ya instaladas:
# - ollama (LLM local)
# - gliner (NER zero-shot)
# - chromadb/qdrant (vector DB)
```

---

## Notas Técnicas

1. **Modelo LLM**: Configurable por perfil (development/production)
2. **GLiNER**: Se mantiene como primera línea de NER (rápido)
3. **LLM solo interviene**: En fallback, reasoning y relaciones
4. **GPU Acceleration**: Disponible en producción para embeddings, reranking y NER

---

## TAREA 0: Sistema de Configuración por Perfil (PREREQUISITO) ✅
- [x] **Estado**: COMPLETADA
- **Impacto**: CRÍTICO
- **Archivo**: `config/hardware_profiles.py` (NUEVO)

### Archivo de Configuración Principal

```python
# config/hardware_profiles.py
"""
Sistema de configuración por perfil de hardware.
Permite optimizar el sistema según el equipo destino.
"""

import os
from dataclasses import dataclass, field
from typing import Optional
import torch

@dataclass
class HardwareProfile:
    """Perfil de configuración de hardware."""
    name: str

    # LLM Configuration
    llm_model: str = "llama3.1:8b"
    llm_num_ctx: int = 4096
    llm_temperature: float = 0.1
    llm_max_tokens: int = 2048

    # Device Configuration
    embedding_device: str = "cpu"
    rerank_device: str = "cpu"
    ner_device: str = "cpu"

    # Performance
    batch_size: int = 4
    max_concurrent_requests: int = 2
    embedding_batch_size: int = 8

    # RAG Enhanced Features
    enable_query_expansion: bool = True
    num_query_variations: int = 3
    enable_reranking: bool = True
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    enable_cot_reasoning: bool = True
    enable_context_compression: bool = False

    # NER Configuration
    ner_llm_fallback_threshold: float = 0.5
    ner_enable_chunking: bool = True
    ner_chunk_size: int = 1500

    # Cache
    cache_ttl_seconds: int = 3600
    cache_max_entries: int = 100


# Perfiles predefinidos
PROFILES = {
    "development": HardwareProfile(
        name="development",
        llm_model="llama3.1:8b",
        llm_num_ctx=4096,
        embedding_device="cpu",
        rerank_device="cpu",
        ner_device="cpu",
        batch_size=4,
        max_concurrent_requests=2,
        enable_context_compression=False,  # Ahorra tiempo en dev
    ),

    "production": HardwareProfile(
        name="production",
        llm_model="mistral-nemo:12b",  # Mejor modelo para RTX 3060
        llm_num_ctx=8192,
        embedding_device="cuda",
        rerank_device="cuda",
        ner_device="cuda",
        batch_size=16,
        max_concurrent_requests=8,
        embedding_batch_size=32,
        enable_context_compression=True,
        cache_ttl_seconds=7200,
        cache_max_entries=500,
    ),

    "production_max": HardwareProfile(
        name="production_max",
        llm_model="llama3.1:70b-q4_K_M",  # Máxima calidad
        llm_num_ctx=16384,
        embedding_device="cuda",
        rerank_device="cuda",
        ner_device="cuda",
        batch_size=8,  # Menor por modelo grande
        max_concurrent_requests=4,
        num_query_variations=5,
    ),
}


def get_profile(profile_name: Optional[str] = None) -> HardwareProfile:
    """
    Obtiene el perfil de hardware.

    Prioridad:
    1. Parámetro profile_name
    2. Variable de entorno HARDWARE_PROFILE
    3. Auto-detección de GPU
    4. Default: development
    """
    if profile_name:
        return PROFILES.get(profile_name, PROFILES["development"])

    env_profile = os.environ.get("HARDWARE_PROFILE")
    if env_profile and env_profile in PROFILES:
        return PROFILES[env_profile]

    # Auto-detección
    if torch.cuda.is_available():
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        if gpu_memory >= 10:
            return PROFILES["production"]

    return PROFILES["development"]


def get_device(device_config: str) -> str:
    """Resuelve el dispositivo real disponible."""
    if device_config == "cuda" and torch.cuda.is_available():
        return "cuda"
    return "cpu"


# Singleton del perfil activo
_active_profile: Optional[HardwareProfile] = None

def get_active_profile() -> HardwareProfile:
    global _active_profile
    if _active_profile is None:
        _active_profile = get_profile()
    return _active_profile

def set_active_profile(profile_name: str) -> HardwareProfile:
    global _active_profile
    _active_profile = get_profile(profile_name)
    return _active_profile
```

### Variables de Entorno (.env)

```bash
# .env para desarrollo (Mac)
HARDWARE_PROFILE=development
OLLAMA_MODEL=llama3.1:8b

# .env para producción (i7 + RTX 3060)
HARDWARE_PROFILE=production
OLLAMA_MODEL=mistral-nemo:12b
CUDA_VISIBLE_DEVICES=0
```

### Integración con Servicios Existentes

```python
# Ejemplo de uso en llm_service.py
from config.hardware_profiles import get_active_profile, get_device

class LLMService:
    def __init__(self):
        profile = get_active_profile()
        self.model = profile.llm_model
        self.num_ctx = profile.llm_num_ctx
        self.temperature = profile.llm_temperature

# Ejemplo en embedding_service.py
class EmbeddingService:
    def __init__(self):
        profile = get_active_profile()
        self.device = get_device(profile.embedding_device)
        self.batch_size = profile.embedding_batch_size
```

---

## Setup de Producción (i7-11700KF + RTX 3060)

### Requisitos Previos

```bash
# 1. Instalar CUDA Toolkit 12.x
# Descargar de https://developer.nvidia.com/cuda-downloads

# 2. Instalar PyTorch con CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 3. Verificar CUDA
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}, GPU: {torch.cuda.get_device_name(0)}')"

# 4. Instalar Ollama (si no está)
curl -fsSL https://ollama.com/install.sh | sh

# 5. Descargar modelo recomendado
ollama pull mistral-nemo:12b

# 6. Instalar dependencias con GPU
pip install sentence-transformers accelerate
```

### Optimizaciones de Producción

```python
# config/production_optimizations.py

# 1. Embeddings en GPU con batching
EMBEDDING_CONFIG = {
    "model": "BAAI/bge-m3",
    "device": "cuda",
    "batch_size": 32,
    "normalize_embeddings": True,
    "max_length": 512,
}

# 2. Cross-Encoder en GPU
RERANK_CONFIG = {
    "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
    "device": "cuda",
    "batch_size": 16,
}

# 3. GLiNER NER en GPU
NER_CONFIG = {
    "model": "urchade/gliner_medium-v2.1",
    "device": "cuda",
    "threshold": 0.5,
}

# 4. Ollama con GPU
OLLAMA_CONFIG = {
    "model": "mistral-nemo:12b",
    "num_ctx": 8192,
    "num_gpu": 99,  # Usar toda la GPU disponible
    "num_thread": 8,  # Threads de CPU para procesamiento
}
```

### Script de Inicio Producción

```bash
#!/bin/bash
# start_production.sh

export HARDWARE_PROFILE=production
export CUDA_VISIBLE_DEVICES=0
export OLLAMA_NUM_GPU=99

# Iniciar Ollama con GPU
ollama serve &
sleep 5

# Verificar modelo cargado
ollama run mistral-nemo:12b --verbose "test" || ollama pull mistral-nemo:12b

# Iniciar backend
cd /ruta/a/Sistema_v6
source .venv/bin/activate
uvicorn presentation.api.rest.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## Comparativa de Rendimiento Esperado

| Operación | Desarrollo (Mac CPU) | Producción (i7 + RTX 3060) | Mejora |
|-----------|---------------------|---------------------------|--------|
| Embedding (1 doc) | ~500ms | ~50ms | **10x** |
| Embedding (batch 32) | ~16s | ~800ms | **20x** |
| Reranking (10 docs) | ~2s | ~200ms | **10x** |
| NER (1 actuación) | ~100ms | ~15ms | **7x** |
| LLM Query (4K ctx) | ~8s | ~3s | **2.5x** |
| LLM Query (8K ctx) | N/A | ~5s | - |
| RAG completo | ~15s | ~4s | **4x** |

---

## Métricas de Éxito

- [ ] Query Expansion mejora recall en búsquedas complejas
- [ ] Reranking mejora precisión del top-5 resultados
- [ ] NER con fallback detecta >90% de entidades relevantes
- [ ] Extracción de relaciones identifica partes del proceso correctamente
- [ ] Tiempo de respuesta RAG mejorado < 5 segundos

---

## Registro de Cambios

| Fecha | Cambio | Estado |
|-------|--------|--------|
| 2025-11-25 | Plan inicial creado | COMPLETADO |
| 2025-11-25 | TAREA 0: Sistema de Configuración por Perfil implementado | COMPLETADO |
| 2025-11-25 | TAREA 1.1: Query Expansion Service implementado | COMPLETADO |
| 2025-11-25 | TAREA 1.2: Cross-Encoder Reranking Service implementado | COMPLETADO |
| 2025-11-25 | TAREA 2.1: LLM Fallback para NER integrado en NERService | COMPLETADO |
| 2025-11-25 | TAREA 2.2: Relation Extraction Service creado | COMPLETADO |
| 2025-11-25 | TAREA 3.1/3.2: Endpoints API agregados en ia.py | COMPLETADO |
| | | |
