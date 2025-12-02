# Plan de Implementación: Qdrant RAG desde Cero
## Sistema SintaXis v6 - Fresh Start Implementation

**Documento:** Plan de implementación completo
**Fecha:** 2025-11-25
**Versión:** 1.0
**Autor:** David Alejandro Liva
**Estado:** READY TO EXECUTE
**Basado en:** `sintaxis_qdrant_from_scratch.md`

---

## 📋 Resumen Ejecutivo

### Objetivo
Implementar sistema RAG completo con Qdrant desde cero, con:
- ✅ **Fresh start**: Empezar con 0 documentos, eliminar ChromaDB
- ✅ **LLM integrado**: Ollama + Llama 3 desde el inicio
- ✅ **Full-time**: Dedicación completa 2-3 semanas
- ✅ **Reemplazo total**: No convivencia con ChromaDB

### Decisiones Clave
1. **Datos actuales**: Descartar ChromaDB, empezar limpio
2. **LLM**: Integrar Ollama + Llama 3 desde día 1
3. **Timeline**: 21 días (3 semanas full-time)
4. **Estrategia**: Reemplazo total de ChromaDB

### Stack Tecnológico
```yaml
Vector Database: Qdrant (local con Docker)
Embeddings: sentence-transformers/paraphrase-multilingual-mpnet-base-v2
Chunking: Semántico por secciones legales (VISTOS, CONSIDERANDOS, RESUELVE)
Enrichment: NER + Regex para entidades legales
Search: Híbrida (vectorial + filtros + keywords)
Reranking: cross-encoder/ms-marco-MiniLM-L-12-v2
LLM: Ollama con Llama 3.2 (local)
```

---

## 🗓️ Timeline: 21 Días (3 Semanas)

```
Semana 1: Setup + Core Services
├─ Días 1-3:  Infraestructura (Docker, deps, config)
└─ Días 4-7:  Core RAG Services (Qdrant, Embeddings, Chunker)

Semana 2: Advanced Features + Integration
├─ Días 8-10:  Enricher + Search + Reranking
├─ Días 11-12: LLM Service (Ollama)
└─ Días 13-15: Integración con SintaXis

Semana 3: Testing + Deployment
├─ Días 16-18: Testing completo
└─ Días 19-21: Deployment + Limpieza + Docs
```

---

## 📅 Fase 1: Setup Infraestructura (Días 1-3)

### Día 1: Docker Stack

#### Tareas
1. ✅ Crear `docker-compose.yml` con servicios:
   - Qdrant (vector database)
   - Ollama (LLM local)
   - MySQL (ya existente, verificar)

2. ✅ Iniciar servicios y verificar health checks

3. ✅ Descargar modelo Llama 3.2 en Ollama

4. ✅ Configurar volúmenes de persistencia

#### Archivo: docker-compose.yml

```yaml
version: '3.8'

services:
  qdrant:
    image: qdrant/qdrant:v1.7.4
    container_name: sintaxis_qdrant
    ports:
      - "6333:6333"
      - "6334:6334"  # gRPC port
    volumes:
      - ./data/qdrant:/qdrant/storage
    environment:
      - QDRANT__SERVICE__GRPC_PORT=6334
      - QDRANT__LOG_LEVEL=INFO
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  ollama:
    image: ollama/ollama:latest
    container_name: sintaxis_ollama
    ports:
      - "11434:11434"
    volumes:
      - ./data/models:/root/.ollama
    environment:
      - OLLAMA_MODELS=/root/.ollama
    restart: unless-stopped
    # GPU support (opcional)
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: 1
    #           capabilities: [gpu]

  mysql:
    image: mysql:8.0
    container_name: sintaxis_mysql
    ports:
      - "3306:3306"
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: sintaxis
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
    volumes:
      - ./data/mysql:/var/lib/mysql
    restart: unless-stopped
```

#### Comandos de Inicialización

```bash
# 1. Iniciar servicios
cd /Users/davidalejandroliva/PycharmProjects/sintaXis/Sistema_v6
docker-compose up -d

# 2. Verificar Qdrant
curl http://localhost:6333/health
# Expected: {"title":"qdrant - vector search engine","version":"1.7.4"}

# 3. Descargar Llama 3.2
docker exec sintaxis_ollama ollama pull llama3.2:latest

# 4. Verificar Ollama
curl http://localhost:11434/api/tags
```

#### Deliverables
- ✅ Docker services corriendo
- ✅ Health checks pasando
- ✅ Llama 3.2 descargado

---

### Día 2: Dependencias Python

#### Tareas
1. ✅ Actualizar `requirements.txt`
2. ✅ Instalar dependencias en venv
3. ✅ Descargar modelo spaCy
4. ✅ Configurar variables de entorno

#### Archivo: requirements.txt (agregar)

```txt
# Core (existentes)
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0

# Database (existentes)
pymysql==1.1.0
sqlalchemy==2.0.23

# Vector Store & AI (NUEVOS)
qdrant-client==1.7.0
sentence-transformers==2.2.2
transformers==4.36.0
torch==2.1.0
ollama==0.1.7

# Document Processing (existentes + nuevos)
pypdf==3.17.0
python-docx==1.1.0
pytesseract==0.3.10
Pillow==10.1.0

# NLP & Legal (NUEVOS)
spacy==3.7.0
# Instalar separadamente: python -m spacy download es_core_news_md

# Search & Ranking (NUEVOS)
rank-bm25==0.2.2
scikit-learn==1.3.2

# Utils (existentes)
python-multipart==0.0.6
python-dotenv==1.0.0
redis==5.0.1
```

#### Archivo: .env (actualizar)

```bash
# Database (existentes)
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=sintaxis
MYSQL_USER=sintaxis_user
MYSQL_PASSWORD=Sulaco01
MYSQL_ROOT_PASSWORD=RootPassword123!

# Qdrant (NUEVO)
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_GRPC_PORT=6334
QDRANT_API_KEY=
QDRANT_COLLECTION=actuaciones

# Ollama (NUEVO)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:latest
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# Embeddings (NUEVO)
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-mpnet-base-v2
EMBEDDING_DIMENSION=768
EMBEDDING_BATCH_SIZE=32
USE_GPU=false

# Chunking (NUEVO)
CHUNK_SIZE=1500
CHUNK_OVERLAP=300
MIN_CHUNK_SIZE=500
MAX_CHUNK_SIZE=3000

# Search (NUEVO)
SEARCH_TOP_K=20
RERANK_TOP_K=10
FINAL_TOP_K=5
USE_RERANKING=true
MMR_LAMBDA=0.7

# Cache (opcional)
REDIS_HOST=localhost
REDIS_PORT=6379
CACHE_TTL=3600
```

#### Comandos de Instalación

```bash
cd /Users/davidalejandroliva/PycharmProjects/sintaXis/Sistema_v6

# Activar venv
source /Users/davidalejandroliva/PycharmProjects/sintaXis/.venv1/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Descargar modelo spaCy
python -m spacy download es_core_news_md

# Verificar instalaciones
python -c "from qdrant_client import QdrantClient; print('✅ Qdrant OK')"
python -c "from sentence_transformers import SentenceTransformer; print('✅ SentenceTransformers OK')"
python -c "import spacy; nlp = spacy.load('es_core_news_md'); print('✅ spaCy OK')"
python -c "import ollama; print('✅ Ollama OK')"
```

#### Deliverables
- ✅ Todas las dependencias instaladas
- ✅ spaCy modelo descargado
- ✅ Variables de entorno configuradas

---

### Día 3: Estructura de Código

#### Tareas
1. ✅ Crear estructura de directorios `/infrastructure/rag/`
2. ✅ Implementar `config.py` base
3. ✅ Setup de logging
4. ✅ Tests básicos de conectividad

#### Estructura de Directorios

```
Sistema_v6/
├── infrastructure/
│   └── rag/                          # NUEVO
│       ├── __init__.py
│       ├── config.py                 # Configuración RAG
│       ├── services/
│       │   ├── __init__.py
│       │   ├── qdrant_service.py     # Servicio Qdrant
│       │   ├── embedding_service.py  # Servicio embeddings
│       │   └── llm_service.py        # Servicio LLM (Ollama)
│       ├── processors/
│       │   ├── __init__.py
│       │   ├── chunker.py            # Chunker legal
│       │   ├── enricher.py           # Enriquecedor metadata
│       │   └── classifier.py         # Clasificador opcional
│       └── search/
│           ├── __init__.py
│           ├── searcher.py           # Motor de búsqueda
│           └── reranker.py           # Reranker
├── data/
│   ├── qdrant/                       # Datos Qdrant
│   ├── models/                       # Modelos Ollama
│   └── cache/                        # Cache embeddings
└── scripts/
    ├── setup_qdrant.py               # Setup inicial
    └── test_rag_connectivity.py      # Tests conectividad
```

#### Comandos

```bash
cd /Users/davidalejandroliva/PycharmProjects/sintaXis/Sistema_v6

# Crear directorios
mkdir -p infrastructure/rag/services
mkdir -p infrastructure/rag/processors
mkdir -p infrastructure/rag/search
mkdir -p data/qdrant
mkdir -p data/models
mkdir -p data/cache
mkdir -p scripts

# Crear __init__.py
touch infrastructure/rag/__init__.py
touch infrastructure/rag/services/__init__.py
touch infrastructure/rag/processors/__init__.py
touch infrastructure/rag/search/__init__.py
```

#### Archivo: infrastructure/rag/config.py

```python
from pydantic_settings import BaseSettings
from typing import Optional
import os

class RAGSettings(BaseSettings):
    """Configuración centralizada del sistema RAG"""

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_grpc_port: int = 6334
    qdrant_api_key: Optional[str] = None
    qdrant_collection: str = "actuaciones"

    # Embeddings
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    embedding_dimension: int = 768
    embedding_batch_size: int = 32
    use_gpu: bool = False

    # Chunking
    chunk_size: int = 1500
    chunk_overlap: int = 300
    min_chunk_size: int = 500
    max_chunk_size: int = 3000

    # Search
    search_top_k: int = 20
    rerank_top_k: int = 10
    final_top_k: int = 5
    use_reranking: bool = True
    mmr_lambda: float = 0.7

    # Ollama
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:latest"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = RAGSettings()
```

#### Deliverables
- ✅ Estructura de directorios creada
- ✅ Config base implementada
- ✅ Tests de conectividad pasando

---

## 📅 Fase 2: Core RAG Services (Días 4-8)

### Día 4: QdrantService

#### Archivo: infrastructure/rag/services/qdrant_service.py

**Contenido completo:** Ver `sintaxis_qdrant_from_scratch.md` líneas 274-686

**Features clave:**
- ✅ Inicialización de colección con optimizaciones
- ✅ Cuantización para reducir memoria
- ✅ Índices de payload
- ✅ Batch indexing
- ✅ Búsqueda vectorial con filtros
- ✅ Búsqueda híbrida (dense + sparse)

#### Tests

```python
# scripts/test_qdrant_service.py
from infrastructure.rag.services.qdrant_service import QdrantService

def test_qdrant_connectivity():
    qdrant = QdrantService()
    info = qdrant.get_collection_info()
    print(f"✅ Qdrant conectado: {info['name']}")
    assert info['name'] == 'actuaciones'

def test_index_and_search():
    qdrant = QdrantService()

    # Index test
    success = qdrant.index_chunk(
        chunk_id="test_001",
        vector=[0.1] * 768,
        text="Test sentencia sobre prescripción",
        metadata={"tipo": "SENTENCIA", "expediente": "2024-001"}
    )
    assert success

    # Search test
    results = qdrant.search(
        query_vector=[0.1] * 768,
        filters={"tipo": "SENTENCIA"},
        limit=5
    )
    assert len(results) > 0
    print(f"✅ Búsqueda OK: {len(results)} resultados")

if __name__ == "__main__":
    test_qdrant_connectivity()
    test_index_and_search()
```

#### Deliverables
- ✅ QdrantService completo
- ✅ Colección creada con optimizaciones
- ✅ Tests pasando

---

### Día 5: EmbeddingService

#### Archivo: infrastructure/rag/services/embedding_service.py

```python
from sentence_transformers import SentenceTransformer
from typing import List, Union
import numpy as np
import logging
from ..config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Servicio para generar embeddings"""

    def __init__(self):
        logger.info(f"Cargando modelo: {settings.embedding_model}")
        self.model = SentenceTransformer(
            settings.embedding_model,
            device='cuda' if settings.use_gpu else 'cpu'
        )
        self.dimension = settings.embedding_dimension

    def embed_text(self, text: str) -> np.ndarray:
        """Genera embedding para un texto"""
        return self.model.encode(text, convert_to_numpy=True)

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Genera embeddings para múltiples textos"""
        return self.model.encode(
            texts,
            batch_size=settings.embedding_batch_size,
            show_progress_bar=True,
            convert_to_numpy=True
        )

    def get_dimension(self) -> int:
        """Retorna dimensión de embeddings"""
        return self.dimension
```

#### Deliverables
- ✅ EmbeddingService implementado
- ✅ Batch processing
- ✅ GPU support opcional

---

### Día 6-7: LegalChunker

#### Archivo: infrastructure/rag/processors/chunker.py

**Contenido completo:** Ver `sintaxis_qdrant_from_scratch.md` líneas 688-1120

**Features clave:**
- ✅ Chunking por secciones legales (VISTOS, CONSIDERANDOS, RESUELVE)
- ✅ Métodos específicos: `_chunk_sentencia`, `_chunk_cedula`, `_chunk_escrito`, `_chunk_providencia`
- ✅ Split con overlap inteligente por oraciones
- ✅ Protección de abreviaciones legales
- ✅ Importancia de secciones

#### Tests

```python
# tests/test_chunker.py
from infrastructure.rag.processors.chunker import LegalChunker

def test_chunk_sentencia():
    chunker = LegalChunker()

    texto = """
    VISTOS: Los autos caratulados "PEREZ, JUAN c/ EMPRESA S.A. s/ DESPIDO"...

    CONSIDERANDO: Que el actor reclama el pago de indemnización por despido...

    RESUELVE: 1) Hacer lugar a la demanda. 2) Condenar a pagar $500.000...
    """

    chunks = chunker.chunk_document(
        text=texto,
        doc_type="sentencia",
        doc_metadata={"expediente": "2024-001"}
    )

    assert len(chunks) >= 3
    assert any('vistos' in c['metadata'].get('section', '') for c in chunks)
    print(f"✅ Chunker: {len(chunks)} chunks generados")

if __name__ == "__main__":
    test_chunk_sentencia()
```

#### Deliverables
- ✅ LegalChunker completo
- ✅ Patrones para documentos argentinos
- ✅ Tests con casos reales

---

### Día 8: MetadataEnricher

#### Archivo: infrastructure/rag/processors/enricher.py

**Contenido completo:** Ver `sintaxis_qdrant_from_scratch.md` líneas 1122-1479

**Features clave:**
- ✅ Extracción de entidades (NER con spaCy)
- ✅ Extracción de partes (actor, demandado, juez)
- ✅ Extracción de referencias legales (leyes, artículos, códigos)
- ✅ Extracción de montos
- ✅ Extracción de fechas y plazos
- ✅ Clasificación de tipo de contenido
- ✅ Cálculo de complejidad
- ✅ Detección de temas legales

#### Tests

```python
# tests/test_enricher.py
from infrastructure.rag.processors.enricher import MetadataEnricher

def test_extract_metadata():
    enricher = MetadataEnricher()

    texto = """
    Actor: Juan Pérez c/ Demandado: Empresa XYZ S.A.
    Monto reclamado: $500.000
    Artículo 42 de la Ley 24.240
    Plazo de 10 días
    """

    chunk = {"text": texto, "metadata": {}}
    enriched = enricher.enrich_chunk(chunk)

    assert 'entities' in enriched['metadata']
    assert 'legal_references' in enriched['metadata']
    assert 'amounts' in enriched['metadata']
    assert enriched['metadata']['amounts'][0]['value'] == 500000
    print("✅ Enricher: metadata extraída correctamente")

if __name__ == "__main__":
    test_extract_metadata()
```

#### Deliverables
- ✅ MetadataEnricher completo
- ✅ NER integrado con spaCy
- ✅ Regex patterns para datos legales

---

## 📅 Fase 3: Search & LLM (Días 9-12)

### Día 9-10: Hybrid Search + Reranking

#### Archivo: infrastructure/rag/search/searcher.py

```python
from typing import List, Dict, Any, Optional
from ..services.qdrant_service import QdrantService
from ..services.embedding_service import EmbeddingService
import logging

logger = logging.getLogger(__name__)

class LegalSearcher:
    """Motor de búsqueda híbrido para documentos legales"""

    def __init__(self):
        self.qdrant = QdrantService()
        self.embedder = EmbeddingService()

    async def search(
        self,
        query: str,
        expediente: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        use_reranking: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Búsqueda híbrida con reranking opcional

        Args:
            query: Query de búsqueda
            expediente: Filtrar por expediente específico
            filters: Filtros adicionales
            limit: Cantidad de resultados
            use_reranking: Usar reranking con cross-encoder

        Returns:
            Lista de resultados rankeados
        """

        # Generar embedding del query
        query_embedding = self.embedder.embed_text(query)

        # Preparar filtros
        search_filters = filters or {}
        if expediente:
            search_filters['expediente_numero'] = expediente

        # Búsqueda híbrida en Qdrant
        results = self.qdrant.hybrid_search(
            query_vector=query_embedding.tolist(),
            query_text=query,
            filters=search_filters,
            limit=limit * 2 if use_reranking else limit
        )

        # Reranking opcional
        if use_reranking and results:
            from .reranker import Reranker
            reranker = Reranker()
            results = reranker.rerank(query, results, top_k=limit)

        return results[:limit]
```

#### Archivo: infrastructure/rag/search/reranker.py

```python
from sentence_transformers import CrossEncoder
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class Reranker:
    """Reranker con cross-encoder para mejorar precisión"""

    def __init__(self):
        logger.info("Cargando modelo de reranking...")
        self.model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-12-v2')

    def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Re-rankea resultados usando cross-encoder

        Args:
            query: Query original
            results: Resultados iniciales
            top_k: Top K a retornar

        Returns:
            Resultados re-rankeados
        """

        if not results:
            return []

        # Preparar pares (query, document)
        pairs = [[query, r['text']] for r in results]

        # Calcular scores con cross-encoder
        scores = self.model.predict(pairs)

        # Agregar scores a resultados
        for i, result in enumerate(results):
            result['rerank_score'] = float(scores[i])

        # Ordenar por score de reranking
        reranked = sorted(results, key=lambda x: x['rerank_score'], reverse=True)

        logger.info(f"Reranking: {len(results)} → top {top_k}")
        return reranked[:top_k]
```

#### Deliverables
- ✅ Searcher con búsqueda híbrida
- ✅ Reranker con cross-encoder
- ✅ Tests de relevancia

---

### Día 11-12: LLM Service

#### Archivo: infrastructure/rag/services/llm_service.py

```python
import ollama
from typing import List, Dict, Any, Optional
import logging
from ..config import settings

logger = logging.getLogger(__name__)

class LLMService:
    """Servicio para generación de respuestas con LLM"""

    def __init__(self):
        self.client = ollama.Client(host=settings.ollama_host)
        self.model = settings.ollama_model

        # Verificar que modelo está disponible
        try:
            models = self.client.list()
            available = [m['name'] for m in models['models']]
            if self.model not in available:
                logger.warning(f"Modelo {self.model} no disponible. Descargando...")
                self.client.pull(self.model)
        except Exception as e:
            logger.error(f"Error verificando modelo: {e}")

    def generate_response(
        self,
        query: str,
        contexts: List[Dict[str, Any]],
        max_tokens: int = 500
    ) -> Dict[str, Any]:
        """
        Genera respuesta usando LLM con contextos

        Args:
            query: Pregunta del usuario
            contexts: Contextos recuperados (chunks)
            max_tokens: Máximo de tokens a generar

        Returns:
            Dict con respuesta y metadata
        """

        # Construir prompt con contextos
        prompt = self._build_prompt(query, contexts)

        try:
            # Generar respuesta
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    'num_predict': max_tokens,
                    'temperature': 0.3,  # Más determinístico para legal
                    'top_p': 0.9
                }
            )

            return {
                'answer': response['response'],
                'model': self.model,
                'contexts_used': len(contexts),
                'prompt_tokens': response.get('prompt_eval_count', 0),
                'completion_tokens': response.get('eval_count', 0)
            }

        except Exception as e:
            logger.error(f"Error generando respuesta: {e}")
            return {
                'answer': self._fallback_response(contexts),
                'error': str(e)
            }

    def _build_prompt(self, query: str, contexts: List[Dict[str, Any]]) -> str:
        """Construye prompt con contextos"""

        # Formatear contextos
        context_texts = []
        for i, ctx in enumerate(contexts[:5], 1):  # Máximo 5 contextos
            metadata = ctx.get('metadata', {})
            expediente = metadata.get('expediente_numero', 'N/A')
            tipo = metadata.get('tipo_actuacion', 'N/A')
            section = metadata.get('section', 'general')

            context_texts.append(
                f"[Contexto {i}]\n"
                f"Expediente: {expediente}\n"
                f"Tipo: {tipo}\n"
                f"Sección: {section}\n"
                f"Contenido: {ctx['text']}\n"
            )

        contexts_str = "\n\n".join(context_texts)

        # Prompt estructurado
        prompt = f"""Sos un asistente legal especializado en documentos judiciales argentinos.

Basándote ÚNICAMENTE en los siguientes contextos de expedientes judiciales, respondé la pregunta del usuario.

CONTEXTOS:
{contexts_str}

PREGUNTA: {query}

INSTRUCCIONES:
- Respondé de forma clara y concisa
- Citá el expediente cuando sea relevante
- Si la información no está en los contextos, decí "No encuentro información sobre eso en los documentos proporcionados"
- Usá terminología legal argentina apropiada

RESPUESTA:"""

        return prompt

    def _fallback_response(self, contexts: List[Dict[str, Any]]) -> str:
        """Respuesta fallback si LLM falla"""
        if not contexts:
            return "No se encontraron documentos relevantes para tu consulta."

        # Respuesta simple con primer contexto
        first = contexts[0]
        metadata = first.get('metadata', {})
        expediente = metadata.get('expediente_numero', 'N/A')

        return (
            f"Encontré información en el expediente {expediente}:\n\n"
            f"{first['text'][:300]}..."
        )

    async def generate_streaming(
        self,
        query: str,
        contexts: List[Dict[str, Any]]
    ):
        """Genera respuesta con streaming (para UI reactiva)"""

        prompt = self._build_prompt(query, contexts)

        try:
            stream = self.client.generate(
                model=self.model,
                prompt=prompt,
                stream=True,
                options={'temperature': 0.3}
            )

            for chunk in stream:
                if 'response' in chunk:
                    yield chunk['response']

        except Exception as e:
            logger.error(f"Error en streaming: {e}")
            yield f"Error: {str(e)}"
```

#### Tests

```python
# tests/test_llm_service.py
from infrastructure.rag.services.llm_service import LLMService

def test_llm_generation():
    llm = LLMService()

    contexts = [
        {
            'text': 'El actor reclama indemnización por despido. Monto: $500.000',
            'metadata': {
                'expediente_numero': '2024-001',
                'tipo_actuacion': 'SENTENCIA'
            }
        }
    ]

    response = llm.generate_response(
        query="¿Cuál es el monto reclamado?",
        contexts=contexts
    )

    assert 'answer' in response
    assert '500' in response['answer']
    print(f"✅ LLM: {response['answer']}")

if __name__ == "__main__":
    test_llm_generation()
```

#### Deliverables
- ✅ LLMService completo
- ✅ Prompt engineering para legal
- ✅ Streaming support
- ✅ Fallback mechanism

---

## 📅 Fase 4: Integración con SintaXis (Días 13-15)

### Día 13: Modificar Procesador de Actuaciones

#### Archivo: core/procesador_pdf/__init__.py (modificar)

Agregar después del procesamiento existente:

```python
from infrastructure.rag.services.qdrant_service import QdrantService
from infrastructure.rag.services.embedding_service import EmbeddingService
from infrastructure.rag.processors.chunker import LegalChunker
from infrastructure.rag.processors.enricher import MetadataEnricher

def procesar_actuacion(
    actuacion: Actuacion,
    ruta_pdf: str = None,
    clasificador: Clasificador = None,
    analizador_vencimientos: AnalizadorVencimientos = None,
    detector_duplicados: DetectorDuplicados = None
) -> ResultadoProcesamientoActuacion:
    """Procesa una actuación individual"""

    # ... procesamiento existente ...

    # NUEVO: Indexación en Qdrant
    if resultado.texto_extraido:
        try:
            logger.info(f"Iniciando indexación RAG de actuación {actuacion.id}")

            # Inicializar servicios
            qdrant = QdrantService()
            embedder = EmbeddingService()
            chunker = LegalChunker()
            enricher = MetadataEnricher()

            # Metadata del documento
            doc_metadata = {
                "actuacion_id": actuacion.id,
                "expediente_numero": actuacion.expediente_numero,
                "tipo_actuacion": actuacion.tipo,
                "fecha_actuacion": actuacion.fecha.isoformat() if actuacion.fecha else None,
                "utilidad": resultado.clasificacion.utilidad.value if resultado.clasificacion else "media",
                "score_clasificacion": resultado.clasificacion.score if resultado.clasificacion else 0.5,
                "juzgado": actuacion.expediente.juzgado if actuacion.expediente else None,
            }

            # 1. Chunking semántico
            chunks = chunker.chunk_document(
                text=resultado.texto_extraido,
                doc_type=actuacion.tipo,
                doc_metadata=doc_metadata
            )

            logger.info(f"Documento dividido en {len(chunks)} chunks")

            # 2. Enriquecer chunks
            enriched_chunks = []
            for chunk in chunks:
                enriched = enricher.enrich_chunk(chunk, doc_metadata)
                enriched_chunks.append(enriched)

            # 3. Generar embeddings e indexar
            indexed_chunks = []
            for i, chunk in enumerate(enriched_chunks):
                chunk_id = f"actuacion_{actuacion.id}_chunk_{i}"

                # Generar embedding
                embedding = embedder.embed_text(chunk["text"])

                # Preparar para indexación
                indexed_chunks.append({
                    "id": chunk_id,
                    "vector": embedding.tolist(),
                    "text": chunk["text"],
                    "metadata": chunk["metadata"]
                })

            # 4. Indexar en batch
            result = qdrant.batch_index(indexed_chunks)

            # Marcar como indexado
            resultado.indexado_rag = result["success_rate"] > 0.8

            logger.info(
                f"✅ Actuación {actuacion.id} indexada en RAG: "
                f"{result['indexed']}/{result['total']} chunks "
                f"(success rate: {result['success_rate']:.2%})"
            )

        except Exception as e:
            logger.error(f"❌ Error indexando actuación {actuacion.id} en RAG: {str(e)}")
            resultado.indexado_rag = False

    return resultado
```

#### Deliverables
- ✅ Procesador actualizado con pipeline RAG
- ✅ ChromaDB eliminado
- ✅ Tests con actuaciones reales

---

### Día 14: API Endpoints

#### Archivo: presentation/api/rest/routers/rag.py (nuevo)

```python
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import time
import logging

from infrastructure.rag.services.qdrant_service import QdrantService
from infrastructure.rag.services.llm_service import LLMService
from infrastructure.rag.search.searcher import LegalSearcher

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/rag", tags=["RAG"])

# ============================================
# MODELS
# ============================================

class SearchRequest(BaseModel):
    query: str
    expediente_numero: Optional[str] = None
    tipo_actuacion: Optional[str] = None
    fecha_desde: Optional[str] = None
    fecha_hasta: Optional[str] = None
    max_resultados: int = 5
    usar_llm: bool = True
    usar_reranking: bool = True

class SearchResponse(BaseModel):
    query: str
    respuesta: str
    fuentes: List[Dict[str, Any]]
    confianza: float
    tiempo_ms: int
    model_info: Optional[Dict[str, Any]] = None

class StatsResponse(BaseModel):
    total_chunks: int
    total_documentos: int
    collection_status: str
    vector_dimension: int
    index_health: str

# ============================================
# ENDPOINTS
# ============================================

@router.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """
    Búsqueda inteligente en documentos procesados con respuesta LLM

    Args:
        request: Parámetros de búsqueda

    Returns:
        Respuesta generada por LLM con fuentes
    """

    start_time = time.time()

    try:
        # Inicializar servicios
        searcher = LegalSearcher()

        # Preparar filtros
        filters = {}
        if request.tipo_actuacion:
            filters['tipo_actuacion'] = request.tipo_actuacion
        if request.fecha_desde:
            filters['fecha_actuacion'] = {'gte': request.fecha_desde}
        if request.fecha_hasta:
            if 'fecha_actuacion' in filters:
                filters['fecha_actuacion']['lte'] = request.fecha_hasta
            else:
                filters['fecha_actuacion'] = {'lte': request.fecha_hasta}

        # Realizar búsqueda
        results = await searcher.search(
            query=request.query,
            expediente=request.expediente_numero,
            filters=filters,
            limit=request.max_resultados * 2,  # Más candidatos para reranking
            use_reranking=request.usar_reranking
        )

        # Generar respuesta con LLM si está habilitado
        if request.usar_llm and results:
            llm = LLMService()
            llm_response = llm.generate_response(
                query=request.query,
                contexts=results[:request.max_resultados]
            )
            respuesta = llm_response['answer']
            model_info = {
                'model': llm_response['model'],
                'tokens': llm_response.get('completion_tokens', 0)
            }
        else:
            respuesta = _format_simple_response(results[:request.max_resultados])
            model_info = None

        # Calcular confianza
        confianza = _calculate_confidence(results)

        # Calcular tiempo
        elapsed_ms = int((time.time() - start_time) * 1000)

        return SearchResponse(
            query=request.query,
            respuesta=respuesta,
            fuentes=_format_sources(results[:3]),
            confianza=confianza,
            tiempo_ms=elapsed_ms,
            model_info=model_info
        )

    except Exception as e:
        logger.error(f"Error en búsqueda RAG: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=StatsResponse)
async def get_rag_statistics():
    """
    Obtiene estadísticas del sistema RAG

    Returns:
        Estadísticas de la colección Qdrant
    """

    try:
        qdrant = QdrantService()
        info = qdrant.get_collection_info()

        # Estimar cantidad de documentos únicos
        # (asumiendo ~5 chunks por documento en promedio)
        total_documentos = info["points_count"] // 5

        # Health check
        health = "healthy" if info["status"] == "green" else "degraded"

        return StatsResponse(
            total_chunks=info["points_count"],
            total_documentos=total_documentos,
            collection_status=info["status"],
            vector_dimension=info["config"]["vector_size"],
            index_health=health
        )

    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/collection/reset")
async def reset_collection(background_tasks: BackgroundTasks):
    """
    Elimina todos los datos de la colección (usar con precaución)

    Returns:
        Confirmación de reset
    """

    try:
        qdrant = QdrantService()

        # Delete collection
        qdrant.client.delete_collection(collection_name=qdrant.collection_name)

        # Recreate collection en background
        background_tasks.add_task(qdrant._initialize_collection)

        return {
            "success": True,
            "message": "Colección eliminada. Re-creación en background."
        }

    except Exception as e:
        logger.error(f"Error reseteando colección: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# HELPERS
# ============================================

def _format_simple_response(results: List[Dict]) -> str:
    """Respuesta simple sin LLM"""
    if not results:
        return "No se encontraron documentos relevantes para tu consulta."

    lines = ["Encontré la siguiente información:\n"]

    for i, result in enumerate(results[:3], 1):
        metadata = result.get('metadata', {})
        expediente = metadata.get('expediente_numero', 'N/A')
        tipo = metadata.get('tipo_actuacion', 'N/A')

        lines.append(f"{i}. Expediente {expediente} ({tipo}):")
        lines.append(f"   {result['text'][:200]}...\n")

    return "\n".join(lines)

def _calculate_confidence(results: List[Dict]) -> float:
    """Calcula confianza basada en scores"""
    if not results:
        return 0.0

    # Usar score del mejor resultado
    best_score = results[0].get('score', 0.0)

    # Normalizar a 0-1
    confidence = min(1.0, best_score)

    # Ajustar si hay rerank_score
    if 'rerank_score' in results[0]:
        rerank = results[0]['rerank_score']
        confidence = (confidence + rerank) / 2

    return round(confidence, 2)

def _format_sources(results: List[Dict]) -> List[Dict[str, Any]]:
    """Formatea fuentes para respuesta"""
    sources = []

    for result in results:
        metadata = result.get('metadata', {})
        sources.append({
            'expediente': metadata.get('expediente_numero'),
            'tipo': metadata.get('tipo_actuacion'),
            'seccion': metadata.get('section'),
            'score': result.get('score', 0.0),
            'texto_preview': result['text'][:150] + "..."
        })

    return sources
```

#### Registrar Router en main.py

```python
# presentation/api/rest/main.py

from .routers import rag  # NUEVO

app.include_router(rag.router)
```

#### Deliverables
- ✅ Endpoint `/api/v1/rag/search` funcionando
- ✅ Endpoint `/api/v1/rag/stats` funcionando
- ✅ Swagger docs actualizados

---

### Día 15: Frontend Integration

#### Archivo: frontend/src/api/ragApi.ts (nuevo)

```typescript
import axios from 'axios';

const API_BASE = '/api/v1/rag';

export interface SearchRequest {
  query: string;
  expediente_numero?: string;
  tipo_actuacion?: string;
  fecha_desde?: string;
  fecha_hasta?: string;
  max_resultados?: number;
  usar_llm?: boolean;
  usar_reranking?: boolean;
}

export interface SearchResponse {
  query: string;
  respuesta: string;
  fuentes: Array<{
    expediente: string;
    tipo: string;
    seccion: string;
    score: number;
    texto_preview: string;
  }>;
  confianza: number;
  tiempo_ms: number;
  model_info?: {
    model: string;
    tokens: number;
  };
}

export interface StatsResponse {
  total_chunks: number;
  total_documentos: number;
  collection_status: string;
  vector_dimension: number;
  index_health: string;
}

export const searchRAG = async (request: SearchRequest): Promise<SearchResponse> => {
  const response = await axios.post(`${API_BASE}/search`, request);
  return response.data;
};

export const getRAGStats = async (): Promise<StatsResponse> => {
  const response = await axios.get(`${API_BASE}/stats`);
  return response.data;
};
```

#### Componente de Búsqueda (ejemplo básico)

```typescript
// frontend/src/components/rag/RAGSearch.tsx

import React, { useState } from 'react';
import { searchRAG, SearchResponse } from '@/api/ragApi';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2 } from 'lucide-react';

export const RAGSearch: React.FC = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<SearchResponse | null>(null);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    try {
      const result = await searchRAG({
        query,
        max_resultados: 5,
        usar_llm: true,
        usar_reranking: true
      });
      setResponse(result);
    } catch (error) {
      console.error('Error en búsqueda:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Input
          placeholder="Pregunta sobre tus expedientes..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
        />
        <Button onClick={handleSearch} disabled={loading}>
          {loading ? <Loader2 className="animate-spin" /> : 'Buscar'}
        </Button>
      </div>

      {response && (
        <Card>
          <CardHeader>
            <CardTitle>Respuesta</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="whitespace-pre-wrap">{response.respuesta}</p>

            <div className="mt-4 text-sm text-gray-600">
              <p>Confianza: {(response.confianza * 100).toFixed(0)}%</p>
              <p>Tiempo: {response.tiempo_ms}ms</p>
            </div>

            {response.fuentes.length > 0 && (
              <div className="mt-4">
                <h4 className="font-semibold mb-2">Fuentes:</h4>
                {response.fuentes.map((fuente, idx) => (
                  <div key={idx} className="text-sm border-l-2 pl-2 mb-2">
                    <p className="font-medium">
                      {fuente.expediente} - {fuente.tipo}
                    </p>
                    <p className="text-gray-600">{fuente.texto_preview}</p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};
```

#### Deliverables
- ✅ API client implementado
- ✅ Componente de búsqueda básico
- ✅ Integración con UI existente

---

## 📅 Fase 5: Testing & Validación (Días 16-18)

### Día 16: Unit Tests

#### Estructura de Tests

```bash
tests/
├── unit/
│   ├── test_qdrant_service.py
│   ├── test_embedding_service.py
│   ├── test_chunker.py
│   ├── test_enricher.py
│   ├── test_searcher.py
│   └── test_llm_service.py
├── integration/
│   ├── test_rag_pipeline.py
│   └── test_api_endpoints.py
└── e2e/
    └── test_full_flow.py
```

#### Ejecutar Tests

```bash
cd /Users/davidalejandroliva/PycharmProjects/sintaXis/Sistema_v6

# Unit tests
PYTHONPATH=... python -m pytest tests/unit/ -v

# Integration tests
PYTHONPATH=... python -m pytest tests/integration/ -v

# E2E tests
PYTHONPATH=... python -m pytest tests/e2e/ -v

# Coverage
PYTHONPATH=... python -m pytest --cov=infrastructure/rag tests/
```

#### Deliverables
- ✅ Tests unitarios > 80% coverage
- ✅ Todos los tests pasando

---

### Día 17: Integration & E2E Tests

#### Script de Validación de Calidad

```python
# scripts/validate_rag_quality.py

from infrastructure.rag.search.searcher import LegalSearcher
from infrastructure.rag.services.llm_service import LLMService
import asyncio

async def validate_rag_quality():
    """Valida la calidad del sistema RAG con casos reales"""

    test_cases = [
        {
            "query": "¿Cuál es el monto de la indemnización reclamada?",
            "expected_keywords": ["monto", "indemnización", "pesos", "$"],
            "expected_confidence": 0.7
        },
        {
            "query": "¿Quién es el actor en el expediente?",
            "expected_keywords": ["actor", "demandante"],
            "expected_confidence": 0.7
        },
        {
            "query": "¿Qué artículos legales se mencionan?",
            "expected_keywords": ["artículo", "ley"],
            "expected_confidence": 0.6
        },
        {
            "query": "¿Qué resolvió el juez?",
            "expected_keywords": ["resuelve", "fallo", "resolvió"],
            "expected_confidence": 0.8
        }
    ]

    searcher = LegalSearcher()
    llm = LLMService()

    results = []

    for test in test_cases:
        print(f"\n🔍 Testing: {test['query']}")

        # Búsqueda
        search_results = await searcher.search(
            query=test["query"],
            limit=5,
            use_reranking=True
        )

        if not search_results:
            print("  ❌ No results found")
            results.append({
                "query": test["query"],
                "passed": False,
                "reason": "No results"
            })
            continue

        # Generar respuesta LLM
        llm_response = llm.generate_response(
            query=test["query"],
            contexts=search_results
        )

        answer = llm_response['answer'].lower()

        # Verificar keywords esperados
        found_keywords = sum(
            1 for keyword in test["expected_keywords"]
            if keyword.lower() in answer
        )

        accuracy = found_keywords / len(test["expected_keywords"])
        confidence = search_results[0].get('score', 0.0)

        passed = accuracy >= 0.5 and confidence >= test['expected_confidence']

        print(f"  Accuracy: {accuracy:.2%}")
        print(f"  Confidence: {confidence:.2f}")
        print(f"  Answer: {answer[:150]}...")
        print(f"  {'✅ PASSED' if passed else '❌ FAILED'}")

        results.append({
            "query": test["query"],
            "accuracy": accuracy,
            "confidence": confidence,
            "passed": passed
        })

    # Resumen
    total_passed = sum(1 for r in results if r["passed"])
    print(f"\n{'='*60}")
    print(f"RESUMEN: {total_passed}/{len(results)} tests pasados")
    print(f"{'='*60}")

    return all(r["passed"] for r in results)

if __name__ == "__main__":
    success = asyncio.run(validate_rag_quality())
    exit(0 if success else 1)
```

#### Deliverables
- ✅ Integration tests pasando
- ✅ E2E test completo (PDF → respuesta LLM)
- ✅ Script de validación de calidad

---

### Día 18: Validación con Usuarios

#### Procedimiento
1. Procesar 50-100 actuaciones reales
2. Probar 20-30 queries típicos
3. Validar respuestas con usuarios
4. Ajustar prompts si es necesario
5. Documentar casos de uso y ejemplos

#### Deliverables
- ✅ 50+ actuaciones procesadas
- ✅ Validación de calidad con usuarios
- ✅ Ajustes de prompts realizados

---

## 📅 Fase 6: Deployment & Limpieza (Días 19-21)

### Día 19: Deployment

#### Docker Compose Producción

```yaml
# docker-compose.prod.yml

version: '3.8'

services:
  qdrant:
    image: qdrant/qdrant:v1.7.4
    container_name: sintaxis_qdrant_prod
    ports:
      - "6333:6333"
    volumes:
      - qdrant_storage:/qdrant/storage
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__LOG_LEVEL=INFO
      - QDRANT__STORAGE__SNAPSHOTS_PATH=/qdrant/snapshots
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G

  ollama:
    image: ollama/ollama:latest
    container_name: sintaxis_ollama_prod
    ports:
      - "11434:11434"
    volumes:
      - ollama_models:/root/.ollama
    restart: always

  sintaxis_api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: sintaxis_api_prod
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - QDRANT_HOST=qdrant
      - OLLAMA_HOST=http://ollama:11434
    depends_on:
      - qdrant
      - ollama
      - mysql
    restart: always

volumes:
  qdrant_storage:
    driver: local
  ollama_models:
    driver: local
  mysql_data:
    driver: local
```

#### Script de Inicialización

```bash
#!/bin/bash
# scripts/init_rag.sh

echo "🚀 Inicializando sistema RAG para sintaXis..."

# 1. Levantar servicios
echo "📦 Levantando servicios Docker..."
docker-compose -f docker-compose.prod.yml up -d

# 2. Esperar a Qdrant
echo "⏳ Esperando a Qdrant..."
until curl -f http://localhost:6333/health > /dev/null 2>&1; do
    sleep 2
done
echo "✅ Qdrant listo"

# 3. Descargar modelo Llama
echo "🤖 Descargando modelo Llama 3.2..."
docker exec sintaxis_ollama_prod ollama pull llama3.2:latest

# 4. Instalar dependencias
echo "📚 Instalando dependencias..."
pip install -r requirements.txt

# 5. Descargar spaCy
echo "🔤 Descargando modelo spaCy..."
python -m spacy download es_core_news_md

# 6. Inicializar colección
echo "🗄️ Inicializando colección Qdrant..."
python -c "
from infrastructure.rag.services.qdrant_service import QdrantService
qdrant = QdrantService()
info = qdrant.get_collection_info()
print(f'✅ Colección creada: {info[\"name\"]} con {info[\"points_count\"]} puntos')
"

echo "✅ Sistema RAG inicializado correctamente!"
```

#### Configurar Backups

```bash
#!/bin/bash
# scripts/backup_qdrant.sh

BACKUP_DIR="/backups/qdrant"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Crear snapshot
docker exec sintaxis_qdrant_prod curl -X POST \
  http://localhost:6333/collections/actuaciones/snapshots

# Copiar snapshot
docker cp sintaxis_qdrant_prod:/qdrant/snapshots \
  ${BACKUP_DIR}/snapshot_${TIMESTAMP}

echo "✅ Backup creado: ${BACKUP_DIR}/snapshot_${TIMESTAMP}"
```

#### Deliverables
- ✅ Docker Compose prod configurado
- ✅ Script de inicialización
- ✅ Backups configurados

---

### Día 20: Limpieza ChromaDB

#### Tareas

1. **Backup final de ChromaDB** (por las dudas)

```bash
cd /Users/davidalejandroliva/PycharmProjects/sintaXis/Sistema_v6

# Backup
tar -czf data/chromadb_backup_final_$(date +%Y%m%d).tar.gz data/vector_store/

# Mover a archivo
mkdir -p archives
mv data/chromadb_backup_final_*.tar.gz archives/
```

2. **Eliminar código legacy**

```bash
# Buscar referencias a ChromaDB
grep -r "chromadb" --include="*.py" .

# Eliminar imports
# Eliminar código legacy en archivos relevantes
```

3. **Actualizar requirements.txt**

```bash
# Remover chromadb de requirements.txt
sed -i '' '/chromadb/d' requirements.txt
```

4. **Eliminar datos de ChromaDB**

```bash
# Después de confirmar que todo funciona
rm -rf data/vector_store/
rm -rf data/bm25_index/
```

#### Deliverables
- ✅ Backup de ChromaDB guardado
- ✅ Código legacy eliminado
- ✅ requirements.txt actualizado

---

### Día 21: Documentación & Handoff

#### Actualizar README

```markdown
# SintaXis v6 - Sistema RAG

## Stack Tecnológico

- **Vector Database:** Qdrant v1.7.4
- **LLM:** Ollama + Llama 3.2
- **Embeddings:** sentence-transformers (multilingual)
- **Chunking:** Semántico por secciones legales
- **Search:** Híbrida + Reranking

## Iniciar Sistema

```bash
# 1. Iniciar servicios
docker-compose up -d

# 2. Inicializar RAG
./scripts/init_rag.sh

# 3. Iniciar API
uvicorn presentation.api.rest.main:app --reload
```

## Endpoints RAG

### POST /api/v1/rag/search
Búsqueda inteligente con respuesta LLM

### GET /api/v1/rag/stats
Estadísticas del sistema

## Procesamiento de Actuaciones

Las actuaciones se procesan automáticamente:
1. Extracción de texto (PDF)
2. Chunking semántico por secciones
3. Enriquecimiento de metadata (NER + regex)
4. Generación de embeddings
5. Indexación en Qdrant

## Mantenimiento

### Backups
```bash
./scripts/backup_qdrant.sh
```

### Reset Collection
```bash
curl -X DELETE http://localhost:8000/api/v1/rag/collection/reset
```
```

#### Documentación de API

Actualizar Swagger/OpenAPI docs con ejemplos de uso.

#### Guía de Troubleshooting

```markdown
# Troubleshooting

## Qdrant no inicia
- Verificar puertos: `lsof -i :6333`
- Ver logs: `docker logs sintaxis_qdrant`

## Ollama no responde
- Verificar modelo: `docker exec sintaxis_ollama ollama list`
- Descargar si falta: `docker exec sintaxis_ollama ollama pull llama3.2`

## Búsquedas lentas
- Verificar índices: Endpoint `/api/v1/rag/stats`
- Revisar logs de performance
- Considerar aumentar memoria de Qdrant
```

#### Deliverables
- ✅ README actualizado
- ✅ API docs completos
- ✅ Guía de troubleshooting
- ✅ Presentación de resultados

---

## 📊 Entregables Finales

### Código
- ✅ `/infrastructure/rag/` completo (services, processors, search)
- ✅ API endpoints funcionando
- ✅ Frontend integrado
- ✅ Tests > 80% coverage

### Infraestructura
- ✅ Docker Compose configurado
- ✅ Qdrant operativo
- ✅ Ollama + Llama 3 funcionando
- ✅ Backups automatizados

### Funcionalidades
- ✅ Chunking semántico por secciones legales
- ✅ Metadata automática (NER + regex)
- ✅ Búsqueda híbrida + reranking
- ✅ Respuestas generadas por LLM
- ✅ ChromaDB eliminado completamente

### Documentación
- ✅ README actualizado
- ✅ API docs (Swagger)
- ✅ Guía de troubleshooting
- ✅ Presentación de resultados

---

## 🎯 Métricas de Éxito

| Métrica | Target | Estado |
|---------|--------|--------|
| Performance búsqueda | < 2 segundos | ✅ |
| Calidad respuestas LLM | > 90% relevantes | ✅ |
| Test coverage | > 80% | ✅ |
| Uptime | Sin errores críticos | ✅ |
| Documentos procesados | 0 → N | ✅ |
| ChromaDB eliminado | 100% | ✅ |

---

## 📅 Timeline Resumen

**Total: 21 días (3 semanas full-time)**

- **Semana 1** (Días 1-7): Setup + Core Services
- **Semana 2** (Días 8-15): Advanced Features + Integration
- **Semana 3** (Días 16-21): Testing + Deployment + Docs

---

**Documento:** PLAN_IMPLEMENTACION_QDRANT_FROM_SCRATCH.md
**Última actualización:** 2025-11-25
**Estado:** ✅ READY TO EXECUTE
