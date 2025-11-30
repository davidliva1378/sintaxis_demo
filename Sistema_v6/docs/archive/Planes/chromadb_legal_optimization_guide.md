# Guía de Optimización ChromaDB para Sistemas Legales
## Estrategias Avanzadas para sintaXis y Procesamiento de Documentos Judiciales

---

## 📋 Tabla de Contenidos
1. [Diagnóstico de Problemas Comunes](#diagnóstico)
2. [Estrategias de Chunking Semántico](#chunking)
3. [Optimización de Embeddings](#embeddings)
4. [Búsqueda Híbrida y Multi-Stage](#búsqueda)
5. [Enriquecimiento de Metadatos](#metadatos)
6. [Arquitectura de Retrieval](#arquitectura)
7. [Prompt Engineering Legal](#prompts)
8. [Implementación Práctica](#implementación)
9. [Métricas y Evaluación](#métricas)
10. [Casos de Uso Específicos](#casos-uso)

---

## 🔍 Diagnóstico de Problemas Comunes {#diagnóstico}

### Síntomas de Respuestas Vagas
- **Chunks muy pequeños**: Pierden contexto legal importante
- **Embeddings genéricos**: No capturan terminología jurídica
- **Búsqueda simple**: Solo similaridad coseno sin reranking
- **Metadata pobre**: Sin información estructural del documento
- **Prompt básico**: No instruye al LLM sobre formato legal

### Checklist de Diagnóstico
```python
def diagnose_retrieval_issues(collection, test_queries):
    issues = []
    
    # Test 1: Tamaño de chunks
    avg_chunk_size = get_average_chunk_size(collection)
    if avg_chunk_size < 500:
        issues.append("Chunks demasiado pequeños para contexto legal")
    
    # Test 2: Calidad de embeddings
    similarity_scores = test_embedding_quality(test_queries)
    if np.mean(similarity_scores) < 0.7:
        issues.append("Embeddings no capturan bien la semántica legal")
    
    # Test 3: Cobertura de metadata
    metadata_fields = check_metadata_coverage(collection)
    if len(metadata_fields) < 5:
        issues.append("Metadata insuficiente para filtrado efectivo")
    
    return issues
```

---

## 🔄 Estrategias de Chunking Semántico {#chunking}

### 1. Chunking por Estructura Legal

```python
from typing import List, Dict
import re

class LegalDocumentChunker:
    """Chunking específico para documentos judiciales argentinos"""
    
    def __init__(self):
        self.section_patterns = {
            'vistos': r'(?i)(VISTOS?:.*?)(?=CONSIDERANDO|RESUELVE|$)',
            'considerandos': r'(?i)(CONSIDERANDOS?:.*?)(?=RESUELVE|POR ELLO|$)',
            'resuelve': r'(?i)(RESUELVE:|SE RESUELVE:.*?)(?=Regístrese|Notifíquese|$)',
            'hechos': r'(?i)(Y RESULTANDO:?.*?)(?=CONSIDERANDO|$)',
            'fundamentos': r'(?i)(FUNDAMENTOS?.*?)(?=POR ELLO|RESUELVE|$)'
        }
        
    def chunk_document(self, text: str, doc_type: str) -> List[Dict]:
        """Divide documento según su tipo y estructura"""
        
        if doc_type == "sentencia":
            return self._chunk_sentencia(text)
        elif doc_type == "cedula":
            return self._chunk_cedula(text)
        elif doc_type == "escrito":
            return self._chunk_escrito(text)
        else:
            return self._chunk_generic(text)
    
    def _chunk_sentencia(self, text: str) -> List[Dict]:
        chunks = []
        
        # Extraer secciones principales
        for section_name, pattern in self.section_patterns.items():
            matches = re.findall(pattern, text, re.DOTALL)
            if matches:
                chunk_text = matches[0]
                chunks.append({
                    'text': chunk_text,
                    'section': section_name,
                    'type': 'sentencia',
                    'importance': self._calculate_importance(section_name),
                    'char_start': text.find(chunk_text),
                    'char_end': text.find(chunk_text) + len(chunk_text)
                })
        
        # Si las secciones son muy largas, sub-dividir
        final_chunks = []
        for chunk in chunks:
            if len(chunk['text']) > 2000:
                sub_chunks = self._split_by_paragraph(chunk['text'])
                for i, sub in enumerate(sub_chunks):
                    final_chunks.append({
                        **chunk,
                        'text': sub,
                        'sub_index': i
                    })
            else:
                final_chunks.append(chunk)
        
        return final_chunks
    
    def _calculate_importance(self, section: str) -> float:
        """Asigna importancia según la sección"""
        importance_map = {
            'resuelve': 1.0,
            'considerandos': 0.9,
            'fundamentos': 0.8,
            'vistos': 0.6,
            'hechos': 0.7
        }
        return importance_map.get(section, 0.5)
```

### 2. Overlapping Contextual

```python
class ContextualOverlapChunker:
    """Chunking con overlap inteligente para mantener contexto"""
    
    def __init__(self, chunk_size=1200, overlap_size=200):
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        
    def create_chunks_with_context(self, text: str) -> List[Dict]:
        sentences = self._split_sentences(text)
        chunks = []
        
        i = 0
        while i < len(sentences):
            # Chunk principal
            chunk_sentences = []
            chunk_length = 0
            
            while i < len(sentences) and chunk_length < self.chunk_size:
                chunk_sentences.append(sentences[i])
                chunk_length += len(sentences[i])
                i += 1
            
            # Agregar contexto previo y siguiente
            prev_context = sentences[max(0, i-self.overlap_size//100):i-len(chunk_sentences)]
            next_context = sentences[i:min(len(sentences), i+self.overlap_size//100)]
            
            chunks.append({
                'text': ' '.join(chunk_sentences),
                'prev_context': ' '.join(prev_context),
                'next_context': ' '.join(next_context),
                'full_text': ' '.join(prev_context + chunk_sentences + next_context),
                'position': f"{i-len(chunk_sentences)}/{len(sentences)}"
            })
            
            # Retroceder para overlap
            i -= self.overlap_size // 100
        
        return chunks
```

### 3. Chunking Jerárquico

```python
class HierarchicalChunker:
    """Sistema de chunks anidados para diferentes niveles de detalle"""
    
    def create_hierarchy(self, document: str) -> Dict:
        return {
            'document_level': {
                'summary': self._create_summary(document),
                'embedding': self._embed_full_doc(document[:4000])
            },
            'section_level': [
                {
                    'section': section,
                    'text': text,
                    'embedding': self._embed_text(text)
                }
                for section, text in self._extract_sections(document).items()
            ],
            'paragraph_level': [
                {
                    'paragraph': para,
                    'section_parent': self._find_section(para, document),
                    'embedding': self._embed_text(para)
                }
                for para in self._extract_paragraphs(document)
            ]
        }
```

---

## 🧠 Optimización de Embeddings {#embeddings}

### 1. Modelos Especializados

```python
from sentence_transformers import SentenceTransformer
from transformers import AutoModel, AutoTokenizer

class LegalEmbeddingOptimizer:
    """Optimizador de embeddings para dominio legal"""
    
    def __init__(self):
        # Modelos recomendados para español legal
        self.models = {
            'multilingual': 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2',
            'spanish': 'hiiamsid/sentence_similarity_spanish_es',
            'legal_spanish': 'PlanTL-GOB-ES/RoBERTalex',
            'cross_encoder': 'cross-encoder/ms-marco-MiniLM-L-12-v2'
        }
        
    def create_hybrid_embedding(self, text: str) -> np.ndarray:
        """Combina múltiples modelos para mejor representación"""
        
        # Embedding principal (semántico)
        semantic_model = SentenceTransformer(self.models['spanish'])
        semantic_emb = semantic_model.encode(text)
        
        # Embedding legal (dominio específico)
        legal_emb = self._get_legal_embedding(text)
        
        # TF-IDF para términos importantes
        tfidf_emb = self._get_tfidf_embedding(text)
        
        # Concatenar y normalizar
        combined = np.concatenate([
            semantic_emb * 0.5,
            legal_emb * 0.3,
            tfidf_emb * 0.2
        ])
        
        return combined / np.linalg.norm(combined)
```

### 2. Fine-tuning Domain-Specific

```python
class LegalEmbeddingFineTuner:
    """Fine-tuning de modelos para dominio legal"""
    
    def prepare_training_data(self, actuaciones: List[str]) -> Dataset:
        """Prepara pares de documentos similares"""
        
        pairs = []
        
        # Generar pares positivos (misma causa/tema)
        for i, doc1 in enumerate(actuaciones):
            for doc2 in actuaciones[i+1:]:
                if self._are_related(doc1, doc2):
                    pairs.append({
                        'text1': doc1,
                        'text2': doc2,
                        'label': 1.0
                    })
        
        # Generar pares negativos (diferentes temas)
        for _ in range(len(pairs)):
            doc1, doc2 = random.sample(actuaciones, 2)
            if not self._are_related(doc1, doc2):
                pairs.append({
                    'text1': doc1,
                    'text2': doc2,
                    'label': 0.0
                })
        
        return Dataset.from_list(pairs)
    
    def fine_tune_model(self, base_model: str, training_data: Dataset):
        """Fine-tuning con contrastive learning"""
        
        model = SentenceTransformer(base_model)
        
        train_loss = losses.CosineSimilarityLoss(model)
        
        model.fit(
            train_objectives=[(train_dataloader, train_loss)],
            epochs=10,
            warmup_steps=100,
            output_path='./legal_embeddings_model'
        )
        
        return model
```

---

## 🔍 Búsqueda Híbrida y Multi-Stage {#búsqueda}

### 1. Implementación de Búsqueda Híbrida

```python
class HybridSearch:
    """Sistema de búsqueda combinando múltiples estrategias"""
    
    def __init__(self, collection, bm25_index):
        self.collection = collection
        self.bm25_index = bm25_index
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-12-v2')
        
    def search(self, query: str, n_results: int = 10) -> List[Dict]:
        """Búsqueda híbrida con reranking"""
        
        # Stage 1: Expansión de query
        expanded_query = self._expand_query(query)
        
        # Stage 2: Búsqueda múltiple
        # 2a. Búsqueda semántica (ChromaDB)
        semantic_results = self.collection.query(
            query_texts=[expanded_query],
            n_results=n_results * 2
        )
        
        # 2b. Búsqueda keyword (BM25)
        keyword_results = self.bm25_index.search(
            expanded_query,
            k=n_results * 2
        )
        
        # 2c. Búsqueda por metadata
        metadata_results = self._metadata_search(query, n_results)
        
        # Stage 3: Fusión de resultados
        fused_results = self._reciprocal_rank_fusion([
            semantic_results,
            keyword_results,
            metadata_results
        ])
        
        # Stage 4: Reranking con cross-encoder
        reranked = self._rerank_results(query, fused_results)
        
        # Stage 5: Diversificación
        diverse_results = self._mmr_diversify(reranked, lambda_param=0.7)
        
        return diverse_results[:n_results]
    
    def _expand_query(self, query: str) -> str:
        """Expande query con sinónimos legales"""
        
        legal_synonyms = {
            'sentencia': ['fallo', 'resolución', 'pronunciamiento', 'decisorio'],
            'demanda': ['acción', 'pretensión', 'reclamo'],
            'actor': ['demandante', 'accionante', 'peticionante', 'requirente'],
            'demandado': ['accionado', 'requerido', 'demandada'],
            'prueba': ['evidencia', 'elemento probatorio', 'medio de prueba'],
            'nulidad': ['invalidez', 'anulación', 'ineficacia'],
            'apelación': ['recurso', 'alzada', 'impugnación']
        }
        
        expanded = query
        for term, synonyms in legal_synonyms.items():
            if term in query.lower():
                expanded += ' ' + ' '.join(synonyms)
        
        return expanded
    
    def _reciprocal_rank_fusion(self, result_lists: List[List], k: int = 60) -> List:
        """Fusiona rankings usando RRF"""
        
        scores = {}
        
        for results in result_lists:
            for rank, result in enumerate(results):
                doc_id = result['id']
                if doc_id not in scores:
                    scores[doc_id] = 0
                scores[doc_id] += 1 / (k + rank + 1)
        
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    def _mmr_diversify(self, results: List, lambda_param: float = 0.5) -> List:
        """Maximum Marginal Relevance para diversificar"""
        
        if not results:
            return []
        
        selected = [results[0]]
        remaining = results[1:]
        
        while remaining and len(selected) < len(results):
            mmr_scores = []
            
            for doc in remaining:
                # Relevancia con query
                relevance = doc['score']
                
                # Máxima similaridad con documentos ya seleccionados
                max_sim = max([
                    self._compute_similarity(doc, sel) 
                    for sel in selected
                ])
                
                # MMR score
                mmr = lambda_param * relevance - (1 - lambda_param) * max_sim
                mmr_scores.append((doc, mmr))
            
            # Seleccionar documento con mayor MMR
            best_doc = max(mmr_scores, key=lambda x: x[1])[0]
            selected.append(best_doc)
            remaining.remove(best_doc)
        
        return selected
```

### 2. Query Processing Pipeline

```python
class QueryProcessor:
    """Pipeline avanzado de procesamiento de queries"""
    
    def __init__(self):
        self.ner_model = self._load_ner_model()
        self.intent_classifier = self._load_intent_classifier()
        
    def process_query(self, query: str) -> Dict:
        """Analiza y enriquece la query"""
        
        # Detectar intención
        intent = self.intent_classifier.predict(query)
        
        # Extraer entidades
        entities = self.ner_model.extract_entities(query)
        
        # Clasificar tipo de búsqueda
        search_type = self._classify_search_type(query)
        
        # Extraer filtros temporales
        date_filters = self._extract_date_filters(query)
        
        # Detectar referencias normativas
        legal_refs = self._extract_legal_references(query)
        
        return {
            'original_query': query,
            'intent': intent,
            'entities': entities,
            'search_type': search_type,
            'date_filters': date_filters,
            'legal_references': legal_refs,
            'suggested_filters': self._suggest_filters(entities, intent)
        }
    
    def _extract_legal_references(self, query: str) -> List[Dict]:
        """Extrae referencias a leyes y artículos"""
        
        patterns = [
            r'(?:ley|Ley)\s+(?:N°|Nº|n°|nº)?\s*(\d+(?:\.\d+)?)',
            r'(?:art(?:ículo)?|Art(?:ículo)?)\s+(\d+)',
            r'(?:decreto|Decreto)\s+(?:N°|Nº|n°|nº)?\s*(\d+/\d+)',
            r'(?:CCyCN?|Código Civil)',
            r'(?:CP|Código Penal)',
            r'(?:CPCCN|Código Procesal)'
        ]
        
        references = []
        for pattern in patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            if matches:
                references.extend(matches)
        
        return references
```

---

## 📊 Enriquecimiento de Metadatos {#metadatos}

### 1. Schema de Metadata Completo

```python
class LegalMetadataEnricher:
    """Enriquece documentos con metadata estructurada"""
    
    def enrich_document(self, text: str, doc_info: Dict) -> Dict:
        """Genera metadata completa para un documento"""
        
        return {
            # Identificadores
            'doc_id': doc_info['id'],
            'expediente_id': doc_info['expediente_id'],
            'actuacion_numero': doc_info.get('numero'),
            
            # Clasificación
            'doc_type': self._classify_document_type(text),
            'doc_subtype': self._classify_subtype(text),
            'legal_area': self._detect_legal_area(text),
            
            # Temporal
            'fecha_documento': doc_info.get('fecha'),
            'fecha_ingreso': doc_info.get('fecha_ingreso'),
            'plazo_vencimiento': self._extract_deadline(text),
            
            # Entidades
            'actor': self._extract_actor(text),
            'demandado': self._extract_demandado(text),
            'juzgado': doc_info.get('juzgado'),
            'juez': self._extract_judge(text),
            'secretario': self._extract_secretary(text),
            
            # Contenido
            'monto_reclamado': self._extract_amounts(text),
            'articulos_citados': self._extract_legal_articles(text),
            'normativa_aplicable': self._extract_applicable_laws(text),
            
            # Procesal
            'estado_procesal': self._infer_procedural_state(text),
            'requiere_respuesta': self._requires_response(text),
            'urgencia': self._calculate_urgency(text, doc_info),
            
            # Análisis
            'sentiment': self._analyze_sentiment(text),
            'complejidad': self._calculate_complexity(text),
            'relevancia_score': self._calculate_relevance(text, doc_info),
            
            # Relaciones
            'referencias_otras_actuaciones': self._extract_references(text),
            'documentos_relacionados': doc_info.get('related_docs', [])
        }
    
    def _extract_amounts(self, text: str) -> List[Dict]:
        """Extrae montos mencionados"""
        
        patterns = [
            r'\$\s*([\d.,]+)',
            r'pesos\s+([\d.,]+)',
            r'suma de\s+([\d.,]+)',
            r'monto de\s+([\d.,]+)'
        ]
        
        amounts = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                amount = match.replace(',', '').replace('.', '')
                amounts.append({
                    'value': float(amount),
                    'currency': 'ARS',
                    'context': self._get_context_around(match, text)
                })
        
        return amounts
```

### 2. Indexación Facetada

```python
class FacetedIndexer:
    """Sistema de indexación con facetas para búsqueda avanzada"""
    
    def create_faceted_index(self, documents: List[Dict]) -> ChromaCollection:
        """Crea índices con múltiples facetas"""
        
        collection = chromadb.create_collection(
            name="legal_docs_faceted",
            metadata={"hnsw:space": "cosine"}
        )
        
        for doc in documents:
            # Embedding principal del contenido
            content_embedding = self.embed_text(doc['text'])
            
            # Crear facetas
            facets = {
                'temporal': self._create_temporal_facet(doc),
                'entities': self._create_entity_facet(doc),
                'legal': self._create_legal_facet(doc),
                'procedural': self._create_procedural_facet(doc)
            }
            
            # Agregar documento con facetas
            collection.add(
                embeddings=[content_embedding],
                documents=[doc['text']],
                metadatas=[{
                    **doc['metadata'],
                    'facets': json.dumps(facets)
                }],
                ids=[doc['id']]
            )
        
        return collection
    
    def faceted_search(self, query: str, facet_filters: Dict) -> List:
        """Búsqueda con filtros de facetas"""
        
        where_clause = {}
        
        # Aplicar filtros de facetas
        if 'date_range' in facet_filters:
            where_clause['fecha'] = {
                '$gte': facet_filters['date_range']['start'],
                '$lte': facet_filters['date_range']['end']
            }
        
        if 'doc_types' in facet_filters:
            where_clause['doc_type'] = {'$in': facet_filters['doc_types']}
        
        if 'entities' in facet_filters:
            where_clause['$or'] = [
                {'actor': {'$in': facet_filters['entities']}},
                {'demandado': {'$in': facet_filters['entities']}}
            ]
        
        return self.collection.query(
            query_texts=[query],
            where=where_clause,
            n_results=20
        )
```

---

## 🏗️ Arquitectura de Retrieval {#arquitectura}

### 1. Multi-Index Strategy

```python
class MultiIndexRetrieval:
    """Sistema con múltiples índices especializados"""
    
    def __init__(self):
        self.indexes = {
            'sentencias': self._create_sentencias_index(),
            'escritos': self._create_escritos_index(),
            'cedulas': self._create_cedulas_index(),
            'providencias': self._create_providencias_index()
        }
        
        self.router = self._create_query_router()
    
    def retrieve(self, query: str, doc_types: List[str] = None) -> List:
        """Retrieval inteligente según tipo de documento"""
        
        # Determinar qué índices usar
        if doc_types:
            relevant_indexes = [self.indexes[dt] for dt in doc_types]
        else:
            # Router decide basándose en la query
            relevant_indexes = self.router.route_query(query)
        
        # Búsqueda paralela en índices relevantes
        results = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(idx.search, query): idx 
                for idx in relevant_indexes
            }
            
            for future in concurrent.futures.as_completed(futures):
                results.extend(future.result())
        
        # Consolidar y rankear
        return self._consolidate_results(results)
    
    def _create_sentencias_index(self) -> ChromaCollection:
        """Índice optimizado para sentencias"""
        
        return chromadb.create_collection(
            name="sentencias",
            embedding_function=LegalEmbeddingFunction(
                model='legal_spanish',
                chunk_size=2000  # Chunks más grandes para sentencias
            ),
            metadata={
                "hnsw:M": 32,  # Más conexiones para mejor recall
                "hnsw:ef_construction": 200
            }
        )
```

### 2. Caching Strategy

```python
class CachedRetrieval:
    """Sistema de caché para queries frecuentes"""
    
    def __init__(self, base_retriever):
        self.retriever = base_retriever
        self.cache = {}
        self.embedding_cache = {}
        self.query_history = deque(maxlen=1000)
        
    def retrieve_with_cache(self, query: str) -> List:
        """Retrieval con sistema de caché"""
        
        # Cache de queries exactas
        cache_key = self._get_cache_key(query)
        if cache_key in self.cache:
            self._update_cache_stats(cache_key, hit=True)
            return self.cache[cache_key]
        
        # Cache de embeddings similares
        query_embedding = self._get_or_compute_embedding(query)
        similar_cached = self._find_similar_cached_queries(query_embedding)
        
        if similar_cached:
            # Usar resultados de query similar y reranquear
            base_results = self.cache[similar_cached]
            reranked = self._rerank_for_new_query(query, base_results)
            return reranked
        
        # Búsqueda nueva
        results = self.retriever.retrieve(query)
        
        # Actualizar caché
        self.cache[cache_key] = results
        self.query_history.append({
            'query': query,
            'timestamp': datetime.now(),
            'results_count': len(results)
        })
        
        # Limpiar caché si es necesario
        if len(self.cache) > 1000:
            self._evict_least_used()
        
        return results
```

---

## 💬 Prompt Engineering Legal {#prompts}

### 1. Sistema de Prompts Estructurado

```python
class LegalPromptSystem:
    """Sistema de prompts optimizado para respuestas legales"""
    
    def __init__(self):
        self.base_prompt = """Sos un asistente legal especializado en derecho argentino.
        Tu tarea es analizar documentos judiciales y proporcionar respuestas precisas y fundamentadas.
        
        INSTRUCCIONES CRÍTICAS:
        1. SIEMPRE citar número de actuación, fecha y carátula
        2. Mencionar artículos específicos y normativa aplicable
        3. Identificar partes involucradas con sus roles exactos
        4. Incluir montos, plazos y fechas relevantes
        5. Referenciar precedentes si los hay
        6. Usar terminología legal precisa
        """
        
    def create_answer_prompt(self, query: str, context: List[Dict]) -> str:
        """Genera prompt para responder queries"""
        
        prompt = self.base_prompt + "\n\n"
        
        # Agregar contexto estructurado
        prompt += "DOCUMENTOS RELEVANTES:\n"
        for i, doc in enumerate(context):
            prompt += f"\n[Documento {i+1}]\n"
            prompt += f"- Tipo: {doc['metadata']['doc_type']}\n"
            prompt += f"- Fecha: {doc['metadata']['fecha']}\n"
            prompt += f"- Expediente: {doc['metadata']['expediente']}\n"
            prompt += f"- Contenido: {doc['text'][:1000]}\n"
        
        # Query específica
        prompt += f"\n\nCONSULTA: {query}\n"
        
        # Formato de respuesta
        prompt += "\nRESPONDER incluyendo:\n"
        prompt += "1. Respuesta directa a la consulta\n"
        prompt += "2. Fundamentos legales\n"
        prompt += "3. Referencias a los documentos citados\n"
        prompt += "4. Próximos pasos recomendados (si aplica)\n"
        
        return prompt
    
    def create_summary_prompt(self, documents: List[Dict]) -> str:
        """Prompt para generar resúmenes"""
        
        return f"""{self.base_prompt}
        
        TAREA: Generar resumen ejecutivo del expediente
        
        DOCUMENTOS: {len(documents)} actuaciones
        
        ESTRUCTURA DEL RESUMEN:
        1. CARÁTULA Y DATOS BÁSICOS
        2. OBJETO DE LA DEMANDA
        3. CRONOLOGÍA PROCESAL (hitos principales)
        4. ESTADO ACTUAL
        5. VENCIMIENTOS PRÓXIMOS
        6. RECOMENDACIONES
        
        Contenido a resumir:
        {self._format_documents_for_summary(documents)}
        """
```

### 2. Chain of Thought para Análisis Legal

```python
class LegalChainOfThought:
    """Sistema de razonamiento paso a paso"""
    
    def analyze_legal_question(self, question: str, context: str) -> str:
        """Análisis estructurado de cuestiones legales"""
        
        cot_prompt = f"""
        Vamos a analizar esta cuestión legal paso a paso.
        
        PREGUNTA: {question}
        
        CONTEXTO: {context}
        
        ANÁLISIS PASO A PASO:
        
        Paso 1: IDENTIFICACIÓN DE LA CUESTIÓN JURÍDICA
        - ¿Cuál es el problema legal central?
        - ¿Qué derechos están en juego?
        - ¿Qué pretensiones se discuten?
        
        Paso 2: MARCO NORMATIVO APLICABLE
        - Leyes relevantes:
        - Artículos específicos:
        - Jurisprudencia aplicable:
        
        Paso 3: HECHOS RELEVANTES
        - Hechos probados:
        - Hechos controvertidos:
        - Pruebas disponibles:
        
        Paso 4: ANÁLISIS JURÍDICO
        - Aplicación de la norma a los hechos:
        - Interpretación legal:
        - Precedentes similares:
        
        Paso 5: CONCLUSIÓN
        - Respuesta a la pregunta:
        - Fundamentos:
        - Recomendaciones:
        
        Desarrollar cada paso con el contexto proporcionado.
        """
        
        return cot_prompt
```

---

## 🛠️ Implementación Práctica {#implementación}

### 1. Pipeline Completo

```python
class OptimizedLegalRAG:
    """Sistema RAG optimizado para sintaXis"""
    
    def __init__(self, db_path: str):
        # Inicializar componentes
        self.chunker = LegalDocumentChunker()
        self.embedder = LegalEmbeddingOptimizer()
        self.metadata_enricher = LegalMetadataEnricher()
        self.searcher = HybridSearch()
        self.prompt_system = LegalPromptSystem()
        
        # Inicializar ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        self.collection = self._setup_collection()
    
    def process_new_document(self, document: Dict) -> None:
        """Pipeline completo para procesar nuevo documento"""
        
        # 1. Chunking semántico
        chunks = self.chunker.chunk_document(
            document['text'],
            document['type']
        )
        
        # 2. Enriquecimiento de metadata
        for chunk in chunks:
            chunk['metadata'] = self.metadata_enricher.enrich_document(
                chunk['text'],
                document
            )
        
        # 3. Generación de embeddings
        embeddings = []
        for chunk in chunks:
            embedding = self.embedder.create_hybrid_embedding(chunk['text'])
            embeddings.append(embedding)
        
        # 4. Almacenamiento en ChromaDB
        self.collection.add(
            embeddings=embeddings,
            documents=[c['text'] for c in chunks],
            metadatas=[c['metadata'] for c in chunks],
            ids=[f"{document['id']}_{i}" for i in range(len(chunks))]
        )
        
        print(f"Procesado: {document['id']} - {len(chunks)} chunks")
    
    def query(self, question: str, filters: Dict = None) -> Dict:
        """Query optimizada con respuesta enriquecida"""
        
        # 1. Procesar query
        processed = QueryProcessor().process_query(question)
        
        # 2. Búsqueda híbrida
        results = self.searcher.search(
            processed['original_query'],
            n_results=10
        )
        
        # 3. Aplicar filtros adicionales
        if filters:
            results = self._apply_filters(results, filters)
        
        # 4. Generar respuesta
        prompt = self.prompt_system.create_answer_prompt(
            question,
            results[:5]  # Top 5 resultados
        )
        
        # 5. LLM response (aquí conectar con tu LLM)
        response = self._generate_response(prompt)
        
        # 6. Post-procesamiento
        enriched_response = self._enrich_response(
            response,
            results,
            processed
        )
        
        return enriched_response
    
    def _enrich_response(self, response: str, sources: List, query_info: Dict) -> Dict:
        """Enriquece respuesta con citas y metadata"""
        
        return {
            'answer': response,
            'sources': [
                {
                    'text': src['text'][:200] + '...',
                    'metadata': src['metadata'],
                    'relevance_score': src['score']
                }
                for src in sources[:3]
            ],
            'query_analysis': query_info,
            'citations': self._extract_citations(response, sources),
            'confidence_score': self._calculate_confidence(sources),
            'suggested_followups': self._generate_followup_questions(response, query_info)
        }
```

### 2. Configuración Óptima

```python
# config.py
OPTIMAL_CONFIG = {
    'chunking': {
        'strategy': 'semantic',  # 'semantic', 'fixed', 'hierarchical'
        'chunk_size': 1500,      # Óptimo para contexto legal
        'chunk_overlap': 300,    # 20% overlap
        'min_chunk_size': 500,
        'max_chunk_size': 3000,
        'respect_sentence_boundary': True,
        'respect_paragraph_boundary': True
    },
    
    'embeddings': {
        'model': 'PlanTL-GOB-ES/RoBERTalex',
        'secondary_model': 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2',
        'dimension': 768,
        'normalize': True,
        'batch_size': 32
    },
    
    'retrieval': {
        'search_type': 'hybrid',  # 'hybrid', 'semantic', 'keyword'
        'top_k_initial': 20,      # Candidatos iniciales
        'top_k_rerank': 10,       # Después de reranking
        'top_k_final': 5,         # Resultados finales
        'use_mmr': True,          # Maximum Marginal Relevance
        'mmr_lambda': 0.7,        # Balance relevancia/diversidad
        'use_reranking': True,
        'reranker_model': 'cross-encoder/ms-marco-MiniLM-L-12-v2'
    },
    
    'metadata': {
        'extract_entities': True,
        'extract_dates': True,
        'extract_amounts': True,
        'extract_legal_refs': True,
        'calculate_importance': True,
        'detect_urgency': True
    },
    
    'chromadb': {
        'collection_name': 'legal_docs_optimized',
        'distance_metric': 'cosine',
        'hnsw_m': 16,
        'hnsw_ef_construction': 100,
        'hnsw_ef_search': 50
    },
    
    'caching': {
        'enabled': True,
        'cache_size': 1000,
        'ttl_seconds': 3600,
        'similarity_threshold': 0.95
    }
}
```

---

## 📈 Métricas y Evaluación {#métricas}

### 1. Sistema de Métricas

```python
class RAGEvaluator:
    """Evaluador de calidad del sistema RAG"""
    
    def __init__(self, test_set: List[Dict]):
        self.test_set = test_set  # Preguntas con respuestas esperadas
        
    def evaluate_system(self, rag_system: OptimizedLegalRAG) -> Dict:
        """Evaluación completa del sistema"""
        
        metrics = {
            'retrieval_metrics': {},
            'answer_quality': {},
            'performance': {}
        }
        
        for test_case in self.test_set:
            # Evaluar retrieval
            retrieval_score = self._evaluate_retrieval(
                rag_system,
                test_case['question'],
                test_case['relevant_docs']
            )
            
            # Evaluar calidad de respuesta
            answer_score = self._evaluate_answer(
                rag_system,
                test_case['question'],
                test_case['expected_answer']
            )
            
            # Métricas de performance
            perf = self._measure_performance(
                rag_system,
                test_case['question']
            )
            
            # Agregar a métricas
            self._update_metrics(metrics, retrieval_score, answer_score, perf)
        
        return self._calculate_final_metrics(metrics)
    
    def _evaluate_retrieval(self, system, question, relevant_docs):
        """Evalúa precisión y recall del retrieval"""
        
        results = system.search(question)
        retrieved_ids = [r['id'] for r in results]
        
        # Precision@K
        precision_at_5 = len(set(retrieved_ids[:5]) & set(relevant_docs)) / 5
        precision_at_10 = len(set(retrieved_ids[:10]) & set(relevant_docs)) / 10
        
        # Recall
        recall = len(set(retrieved_ids) & set(relevant_docs)) / len(relevant_docs)
        
        # MRR (Mean Reciprocal Rank)
        mrr = 0
        for i, doc_id in enumerate(retrieved_ids):
            if doc_id in relevant_docs:
                mrr = 1 / (i + 1)
                break
        
        return {
            'precision@5': precision_at_5,
            'precision@10': precision_at_10,
            'recall': recall,
            'mrr': mrr
        }
```

### 2. A/B Testing

```python
class ABTestingFramework:
    """Framework para A/B testing de configuraciones"""
    
    def run_ab_test(self, config_a: Dict, config_b: Dict, test_queries: List[str]):
        """Compara dos configuraciones"""
        
        # Crear sistemas con diferentes configs
        system_a = OptimizedLegalRAG(config_a)
        system_b = OptimizedLegalRAG(config_b)
        
        results = {
            'config_a': [],
            'config_b': [],
            'preferences': []
        }
        
        for query in test_queries:
            # Obtener respuestas de ambos sistemas
            response_a = system_a.query(query)
            response_b = system_b.query(query)
            
            # Evaluar calidad
            quality_a = self._evaluate_response_quality(response_a)
            quality_b = self._evaluate_response_quality(response_b)
            
            results['config_a'].append(quality_a)
            results['config_b'].append(quality_b)
            
            # Determinar preferencia
            if quality_a > quality_b:
                results['preferences'].append('A')
            elif quality_b > quality_a:
                results['preferences'].append('B')
            else:
                results['preferences'].append('tie')
        
        return self._calculate_statistics(results)
```

---

## 📚 Casos de Uso Específicos {#casos-uso}

### 1. Búsqueda de Jurisprudencia

```python
class JurisprudenceSearch:
    """Búsqueda especializada de jurisprudencia"""
    
    def find_similar_cases(self, case_summary: str, filters: Dict = None):
        """Encuentra casos similares"""
        
        # Extraer elementos clave del caso
        key_elements = {
            'legal_issue': self._extract_legal_issue(case_summary),
            'parties_type': self._classify_parties(case_summary),
            'claimed_rights': self._extract_rights(case_summary),
            'applicable_law': self._extract_laws(case_summary)
        }
        
        # Búsqueda por cada elemento
        results = []
        
        # Búsqueda por tema legal
        theme_results = self.collection.query(
            query_texts=[key_elements['legal_issue']],
            where={'doc_type': 'sentencia'},
            n_results=20
        )
        
        # Filtrar por similitud estructural
        filtered = []
        for result in theme_results:
            similarity_score = self._calculate_case_similarity(
                key_elements,
                result['metadata']
            )
            if similarity_score > 0.7:
                filtered.append({
                    **result,
                    'similarity_score': similarity_score
                })
        
        return sorted(filtered, key=lambda x: x['similarity_score'], reverse=True)
```

### 2. Análisis de Tendencias

```python
class TrendAnalyzer:
    """Análisis de tendencias en resoluciones"""
    
    def analyze_resolution_trends(self, topic: str, time_period: tuple):
        """Analiza tendencias en las resoluciones sobre un tema"""
        
        # Obtener todas las sentencias del período
        sentences = self.get_sentences_in_period(topic, time_period)
        
        # Agrupar por resultado
        trends = {
            'favorable': [],
            'desfavorable': [],
            'parcial': []
        }
        
        for sentence in sentences:
            # Clasificar resultado
            result_type = self._classify_sentence_result(sentence)
            trends[result_type].append({
                'date': sentence['fecha'],
                'expediente': sentence['expediente'],
                'key_points': self._extract_key_points(sentence)
            })
        
        # Calcular estadísticas
        statistics = {
            'total_casos': len(sentences),
            'tasa_favorable': len(trends['favorable']) / len(sentences),
            'evolucion_temporal': self._calculate_temporal_evolution(trends),
            'argumentos_frecuentes': self._extract_common_arguments(sentences)
        }
        
        return {
            'trends': trends,
            'statistics': statistics,
            'insights': self._generate_insights(trends, statistics)
        }
```

### 3. Alertas Inteligentes

```python
class SmartAlertSystem:
    """Sistema de alertas basado en RAG"""
    
    def setup_alerts(self, expediente_id: str, alert_rules: List[Dict]):
        """Configura alertas inteligentes para un expediente"""
        
        alerts = []
        
        for rule in alert_rules:
            if rule['type'] == 'similar_resolution':
                # Alerta cuando hay resolución similar en otro caso
                alert = self._create_similarity_alert(expediente_id, rule)
                
            elif rule['type'] == 'deadline_approaching':
                # Alerta de vencimientos con contexto
                alert = self._create_deadline_alert(expediente_id, rule)
                
            elif rule['type'] == 'relevant_jurisprudence':
                # Nueva jurisprudencia relevante
                alert = self._create_jurisprudence_alert(expediente_id, rule)
            
            alerts.append(alert)
        
        return alerts
    
    def check_alerts(self, expediente_id: str) -> List[Dict]:
        """Verifica alertas activas"""
        
        triggered_alerts = []
        alerts = self.get_alerts(expediente_id)
        
        for alert in alerts:
            if self._should_trigger(alert):
                # Enriquecer con contexto usando RAG
                context = self.rag_system.query(
                    f"Contexto para alerta: {alert['description']}",
                    filters={'expediente_id': expediente_id}
                )
                
                triggered_alerts.append({
                    'alert': alert,
                    'context': context,
                    'recommended_action': self._suggest_action(alert, context)
                })
        
        return triggered_alerts
```

---

## 🚀 Próximos Pasos y Recomendaciones

### Implementación Gradual

1. **Fase 1**: Optimizar chunking y embeddings
2. **Fase 2**: Implementar búsqueda híbrida
3. **Fase 3**: Enriquecer metadata
4. **Fase 4**: Agregar reranking y MMR
5. **Fase 5**: Implementar caché y optimizaciones

### Monitoreo Continuo

```python
class MonitoringDashboard:
    """Dashboard de monitoreo para el sistema RAG"""
    
    def get_system_metrics(self) -> Dict:
        return {
            'retrieval_performance': {
                'avg_query_time': self.get_avg_query_time(),
                'cache_hit_rate': self.get_cache_hit_rate(),
                'avg_relevance_score': self.get_avg_relevance_score()
            },
            'quality_metrics': {
                'user_satisfaction': self.get_user_satisfaction_score(),
                'answer_completeness': self.get_completeness_score(),
                'citation_accuracy': self.get_citation_accuracy()
            },
            'system_health': {
                'index_size': self.get_index_size(),
                'query_volume': self.get_query_volume(),
                'error_rate': self.get_error_rate()
            }
        }
```

### Recursos Adicionales

- [Documentación ChromaDB](https://docs.trychroma.com/)
- [Sentence Transformers](https://www.sbert.net/)
- [LangChain RAG](https://python.langchain.com/docs/use_cases/question_answering/)
- [Modelos para español legal](https://huggingface.co/PlanTL-GOB-ES)

---

## 💡 Tips Finales

1. **Itera constantemente**: La optimización es un proceso continuo
2. **Mide todo**: Sin métricas no hay mejora
3. **Escucha a los usuarios**: El feedback es oro
4. **Mantén la calidad de datos**: Garbage in, garbage out
5. **Documenta los cambios**: Para poder revertir si algo falla

---

*Esta guía está diseñada específicamente para sistemas legales en español. Adaptá las estrategias según tus necesidades específicas en sintaXis.*
