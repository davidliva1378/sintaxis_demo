# Optimización de ChromaDB para sintaXis v6
## Integración con el Flujo de Procesamiento de Expedientes

**Fecha:** 2025-11-25  
**Sistema:** sintaXis v6 con ChromaDB  
**Objetivo:** Mejorar la calidad de respuestas del sistema RAG

---

## 📋 Tabla de Contenidos

1. [Análisis del Sistema Actual](#análisis-actual)
2. [Problemas Identificados](#problemas-identificados)
3. [Optimizaciones para ChromaDB](#optimizaciones-chromadb)
4. [Integración con el Flujo Existente](#integración-flujo)
5. [Implementación Paso a Paso](#implementación)
6. [Configuración Recomendada](#configuración)
7. [Métricas de Evaluación](#métricas)
8. [Plan de Migración](#migración)

---

## 🔍 1. Análisis del Sistema Actual {#análisis-actual}

### 1.1 Arquitectura RAG Actual

Según tu flujo de trabajo, el sistema RAG se integra en:

**Backend - Procesamiento de Actuaciones:**
- **Archivo:** `/core/procesador_pdf/__init__.py` (líneas 246-254)
- **Función:** Indexación en ChromaDB después de clasificar
- **Archivo:** `/infrastructure/rag/services/__init__.py` (línea 315)
- **Storage:** `./data/chromadb`

**Flujo Actual:**
```python
# En procesar_actuacion (líneas 131-143)
if rag_service and resultado.texto_extraido:
    # Preparar metadata
    metadata = {
        "actuacion_id": actuacion.id,
        "tipo": actuacion.tipo,
        "fecha": actuacion.fecha.isoformat(),
        "expediente": actuacion.expediente_numero,
        "utilidad": resultado.clasificacion.utilidad.value,
        # ... más metadata
    }
    
    # Indexar en ChromaDB
    rag_service.indexar_documento(
        contenido=resultado.texto_extraido,
        metadata=metadata,
        doc_id=f"actuacion_{actuacion.id}"
    )
```

### 1.2 Configuración Actual

**Variables de Entorno (`.env`):**
```bash
IA_OLLAMA_ENABLED=false
IA_OLLAMA_HOST=http://localhost:11434
IA_OLLAMA_MODEL=llama3.1
IA_CHROMADB_PATH=./data/chromadb
```

### 1.3 Puntos de Integración

1. **Durante Procesamiento** (`procesar_expediente_completo`):
   - Líneas 695-701: Procesamiento con `procesador_pdf`
   - Líneas 246-254: Indexación en ChromaDB

2. **Consulta RAG** (no visible en el flujo actual):
   - Necesita implementarse o mejorarse

---

## 🚨 2. Problemas Identificados {#problemas-identificados}

### 2.1 Problemas de Chunking

**Problema Actual:**
```python
# Indexación de texto completo sin chunking
rag_service.indexar_documento(
    contenido=resultado.texto_extraido,  # ← Texto completo
    metadata=metadata,
    doc_id=f"actuacion_{actuacion.id}"
)
```

**Consecuencias:**
- ❌ Chunks muy grandes (documentos completos)
- ❌ Pérdida de granularidad en búsquedas
- ❌ Embeddings poco precisos
- ❌ Respuestas vagas sin contexto específico

### 2.2 Metadata Insuficiente

**Metadata Actual:**
```python
metadata = {
    "actuacion_id": actuacion.id,
    "tipo": actuacion.tipo,
    "fecha": actuacion.fecha.isoformat(),
    "expediente": actuacion.expediente_numero,
    "utilidad": resultado.clasificacion.utilidad.value
}
```

**Falta:**
- Sección del documento (vistos, considerandos, resuelve)
- Entidades mencionadas
- Montos y fechas específicas
- Referencias normativas
- Posición en el documento

### 2.3 Embeddings Genéricos

- Usa modelo genérico (no optimizado para español legal)
- Sin fine-tuning para dominio jurídico
- Sin estrategia híbrida

---

## 🚀 3. Optimizaciones para ChromaDB {#optimizaciones-chromadb}

### 3.1 Nuevo Sistema de Chunking Legal

```python
# /infrastructure/rag/chunkers/legal_chunker.py

from typing import List, Dict
import re

class LegalDocumentChunker:
    """Chunker especializado para documentos judiciales argentinos"""
    
    def __init__(self, chunk_size=1500, overlap=300):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.section_patterns = {
            'vistos': r'(?i)(VISTOS?:.*?)(?=CONSIDERANDO|RESUELVE|$)',
            'considerandos': r'(?i)(CONSIDERANDOS?:.*?)(?=RESUELVE|POR ELLO|$)',
            'resuelve': r'(?i)(RESUELVE:|SE RESUELVE:.*?)(?=Regístrese|Notifíquese|$)',
            'hechos': r'(?i)(Y RESULTANDO:?.*?)(?=CONSIDERANDO|$)',
            'fundamentos': r'(?i)(FUNDAMENTOS?.*?)(?=POR ELLO|RESUELVE|$)'
        }
    
    def chunk_actuacion(self, texto: str, tipo_actuacion: str) -> List[Dict]:
        """
        Divide una actuación en chunks semánticamente coherentes
        """
        # Determinar estrategia según tipo
        if tipo_actuacion in ['SENTENCIA', 'SENTENCIA DEFINITIVA', 'RESOLUCION']:
            return self._chunk_sentencia(texto)
        elif tipo_actuacion in ['CEDULA', 'CEDULA DE NOTIFICACION']:
            return self._chunk_cedula(texto)
        elif tipo_actuacion in ['ESCRITO', 'DEMANDA', 'CONTESTACION']:
            return self._chunk_escrito(texto)
        else:
            return self._chunk_generico(texto)
    
    def _chunk_sentencia(self, texto: str) -> List[Dict]:
        """Chunking específico para sentencias"""
        chunks = []
        
        # 1. Extraer secciones principales
        for section_name, pattern in self.section_patterns.items():
            matches = re.findall(pattern, texto, re.DOTALL)
            if matches:
                section_text = matches[0]
                
                # 2. Si la sección es muy larga, subdividir
                if len(section_text) > self.chunk_size * 2:
                    sub_chunks = self._split_with_overlap(section_text)
                    for i, chunk_text in enumerate(sub_chunks):
                        chunks.append({
                            'text': chunk_text,
                            'metadata': {
                                'section': section_name,
                                'subsection_index': i,
                                'importance': self._calculate_importance(section_name),
                                'char_start': texto.find(chunk_text),
                                'char_end': texto.find(chunk_text) + len(chunk_text)
                            }
                        })
                else:
                    chunks.append({
                        'text': section_text,
                        'metadata': {
                            'section': section_name,
                            'subsection_index': 0,
                            'importance': self._calculate_importance(section_name)
                        }
                    })
        
        # 3. Si no encontró secciones, usar chunking genérico
        if not chunks:
            chunks = self._chunk_generico(texto)
        
        return chunks
    
    def _split_with_overlap(self, text: str) -> List[str]:
        """Divide texto con overlap para mantener contexto"""
        sentences = self._split_sentences(text)
        chunks = []
        
        i = 0
        while i < len(sentences):
            chunk_sentences = []
            chunk_length = 0
            
            # Construir chunk hasta alcanzar el tamaño deseado
            while i < len(sentences) and chunk_length < self.chunk_size:
                chunk_sentences.append(sentences[i])
                chunk_length += len(sentences[i])
                i += 1
            
            chunks.append(' '.join(chunk_sentences))
            
            # Retroceder para overlap
            overlap_chars = 0
            while i > 0 and overlap_chars < self.overlap:
                i -= 1
                overlap_chars += len(sentences[i])
        
        return chunks
    
    def _calculate_importance(self, section: str) -> float:
        """Asigna importancia según la sección"""
        importance_map = {
            'resuelve': 1.0,
            'considerandos': 0.9,
            'fundamentos': 0.8,
            'hechos': 0.7,
            'vistos': 0.6
        }
        return importance_map.get(section, 0.5)
    
    def _split_sentences(self, text: str) -> List[str]:
        """Divide texto en oraciones preservando estructura legal"""
        # Pattern para dividir por oraciones legales
        sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])|(?<=\d\.)\s+(?=[A-Z])'
        sentences = re.split(sentence_pattern, text)
        return [s.strip() for s in sentences if s.strip()]
```

### 3.2 Enriquecimiento de Metadata

```python
# /infrastructure/rag/enrichers/metadata_enricher.py

import re
from typing import Dict, List, Any
from datetime import datetime

class LegalMetadataEnricher:
    """Enriquece chunks con metadata legal específica"""
    
    def __init__(self):
        self.entity_patterns = {
            'actor': r'(?:actor|demandante|requirente)\s*:?\s*([A-Z][A-Za-z\s]+?)(?:\s*c/|,)',
            'demandado': r'(?:demandado|requerido)\s*:?\s*([A-Z][A-Za-z\s]+?)(?:\s*s/|,)',
            'juez': r'(?:Juez|Magistrado|Dr\.|Dra\.)\s+([A-Z][A-Za-z\s]+?)(?:\s*-|\s*,)',
            'abogado': r'(?:letrado|abogado|patrocinante)\s*:?\s*([A-Z][A-Za-z\s]+?)(?:\s*Mat\.|,)'
        }
        
        self.legal_refs_patterns = {
            'ley': r'(?:ley|Ley)\s+(?:N°|Nº|n°|nº)?\s*(\d+(?:\.\d+)?)',
            'articulo': r'(?:art(?:ículo)?|Art(?:ículo)?)\s+(\d+)',
            'decreto': r'(?:decreto|Decreto)\s+(?:N°|Nº)?\s*(\d+/\d+)',
            'codigo': r'(?:CCyCN?|Código Civil|CP|Código Penal|CPCCN)'
        }
    
    def enrich_chunk(self, chunk: Dict, actuacion_data: Dict) -> Dict:
        """
        Enriquece un chunk con metadata adicional
        
        Args:
            chunk: Chunk con 'text' y 'metadata' básica
            actuacion_data: Datos de la actuación completa
        """
        text = chunk['text']
        metadata = chunk['metadata']
        
        # Agregar datos de la actuación
        metadata.update({
            'actuacion_id': actuacion_data['id'],
            'expediente_numero': actuacion_data['expediente_numero'],
            'tipo_actuacion': actuacion_data['tipo'],
            'fecha_actuacion': actuacion_data['fecha'],
            'utilidad': actuacion_data.get('utilidad', 'media')
        })
        
        # Extraer entidades
        metadata['entities'] = self._extract_entities(text)
        
        # Extraer referencias legales
        metadata['legal_references'] = self._extract_legal_references(text)
        
        # Extraer montos
        metadata['amounts'] = self._extract_amounts(text)
        
        # Extraer fechas y plazos
        metadata['dates'] = self._extract_dates(text)
        metadata['deadlines'] = self._extract_deadlines(text)
        
        # Calcular complejidad
        metadata['complexity_score'] = self._calculate_complexity(text)
        
        # Detectar tipo de contenido
        metadata['content_type'] = self._classify_content_type(text)
        
        # Agregar keywords importantes
        metadata['keywords'] = self._extract_keywords(text)
        
        return chunk
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extrae entidades legales del texto"""
        entities = {}
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                entities[entity_type] = list(set(matches))
        
        return entities
    
    def _extract_legal_references(self, text: str) -> List[Dict]:
        """Extrae referencias a leyes y artículos"""
        references = []
        
        for ref_type, pattern in self.legal_refs_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                references.append({
                    'type': ref_type,
                    'value': match,
                    'context': self._get_context(text, match)
                })
        
        return references
    
    def _extract_amounts(self, text: str) -> List[Dict]:
        """Extrae montos mencionados"""
        amounts = []
        patterns = [
            r'\$\s*([\d.,]+)',
            r'pesos\s+([\d.,]+)',
            r'suma de\s+([\d.,]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                clean_amount = match.replace(',', '').replace('.', '')
                try:
                    value = float(clean_amount)
                    amounts.append({
                        'value': value,
                        'formatted': match,
                        'currency': 'ARS'
                    })
                except ValueError:
                    pass
        
        return amounts
    
    def _extract_dates(self, text: str) -> List[str]:
        """Extrae fechas mencionadas"""
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{2,4}',
            r'\d{1,2} de \w+ de \d{4}',
            r'\w+ \d{1,2}, \d{4}'
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        
        return dates
    
    def _extract_deadlines(self, text: str) -> List[Dict]:
        """Extrae plazos y vencimientos"""
        deadline_patterns = [
            r'plazo de (\d+) días',
            r'dentro de los (\d+) días',
            r'término de (\d+) días',
            r'vence.{0,20}(\d{1,2}/\d{1,2}/\d{4})'
        ]
        
        deadlines = []
        for pattern in deadline_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                deadlines.append({
                    'value': match,
                    'context': self._get_context(text, match, window=50)
                })
        
        return deadlines
    
    def _calculate_complexity(self, text: str) -> float:
        """Calcula complejidad del texto legal"""
        # Factores de complejidad
        words = text.split()
        avg_word_length = sum(len(w) for w in words) / len(words) if words else 0
        
        # Cantidad de referencias legales
        legal_refs = len(self._extract_legal_references(text))
        
        # Cantidad de entidades
        entities = self._extract_entities(text)
        entity_count = sum(len(v) for v in entities.values())
        
        # Score normalizado
        complexity = min(1.0, (avg_word_length / 10 + legal_refs / 5 + entity_count / 3) / 3)
        
        return round(complexity, 2)
    
    def _classify_content_type(self, text: str) -> str:
        """Clasifica el tipo de contenido del chunk"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['resuelve', 'falla', 'condena']):
            return 'dispositivo'
        elif any(word in text_lower for word in ['considerando', 'visto que']):
            return 'fundamentacion'
        elif any(word in text_lower for word in ['demanda', 'solicita', 'peticiona']):
            return 'petitorio'
        elif any(word in text_lower for word in ['prueba', 'acredita', 'demuestra']):
            return 'probatorio'
        else:
            return 'general'
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extrae keywords importantes del texto"""
        # Keywords legales comunes
        legal_keywords = [
            'inconstitucional', 'nulidad', 'prescripción', 'caducidad',
            'responsabilidad', 'daños y perjuicios', 'medida cautelar',
            'cosa juzgada', 'litispendencia', 'competencia'
        ]
        
        found_keywords = []
        text_lower = text.lower()
        
        for keyword in legal_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def _get_context(self, text: str, match: str, window: int = 30) -> str:
        """Obtiene contexto alrededor de un match"""
        index = text.find(str(match))
        if index == -1:
            return ""
        
        start = max(0, index - window)
        end = min(len(text), index + len(str(match)) + window)
        
        return text[start:end].strip()
```

### 3.3 Búsqueda Híbrida Mejorada

```python
# /infrastructure/rag/search/hybrid_searcher.py

from typing import List, Dict, Any
import chromadb
from sentence_transformers import CrossEncoder
import numpy as np

class HybridLegalSearcher:
    """Sistema de búsqueda híbrida optimizado para documentos legales"""
    
    def __init__(self, chroma_client, collection_name: str):
        self.chroma_client = chroma_client
        self.collection = chroma_client.get_collection(collection_name)
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-12-v2')
        
        # Sinónimos legales para expansión de queries
        self.legal_synonyms = {
            'sentencia': ['fallo', 'resolución', 'pronunciamiento', 'decisorio'],
            'demanda': ['acción', 'pretensión', 'reclamo', 'demanda judicial'],
            'actor': ['demandante', 'accionante', 'peticionante', 'requirente'],
            'demandado': ['accionado', 'requerido', 'demandada parte'],
            'prueba': ['evidencia', 'elemento probatorio', 'medio de prueba'],
            'nulidad': ['invalidez', 'anulación', 'ineficacia'],
            'apelación': ['recurso', 'alzada', 'impugnación', 'recurso de apelación']
        }
    
    def search(self, 
              query: str, 
              expediente_numero: str = None,
              filters: Dict = None,
              n_results: int = 10) -> List[Dict]:
        """
        Búsqueda híbrida con múltiples estrategias
        
        Args:
            query: Consulta del usuario
            expediente_numero: Filtrar por expediente específico
            filters: Filtros adicionales
            n_results: Cantidad de resultados
        """
        
        # 1. Expandir query con sinónimos
        expanded_query = self._expand_query(query)
        
        # 2. Búsqueda semántica
        semantic_results = self._semantic_search(
            expanded_query, 
            expediente_numero, 
            filters,
            n_results * 2  # Obtener más candidatos
        )
        
        # 3. Búsqueda por metadata (si hay entidades o referencias)
        metadata_results = self._metadata_search(
            query,
            expediente_numero,
            filters,
            n_results
        )
        
        # 4. Fusionar resultados
        fused_results = self._fuse_results(semantic_results, metadata_results)
        
        # 5. Reranking con cross-encoder
        reranked_results = self._rerank_results(query, fused_results)
        
        # 6. Diversificación MMR
        diverse_results = self._mmr_diversify(reranked_results, lambda_param=0.7)
        
        return diverse_results[:n_results]
    
    def _expand_query(self, query: str) -> str:
        """Expande query con sinónimos legales"""
        expanded = query
        
        for term, synonyms in self.legal_synonyms.items():
            if term in query.lower():
                # Agregar sinónimos pero con menor peso
                expanded += ' ' + ' '.join(synonyms)
        
        return expanded
    
    def _semantic_search(self, query: str, expediente: str, filters: Dict, n_results: int) -> List[Dict]:
        """Búsqueda por similaridad semántica"""
        
        # Construir filtros para ChromaDB
        where_clause = {}
        
        if expediente:
            where_clause['expediente_numero'] = expediente
        
        if filters:
            if 'tipo_actuacion' in filters:
                where_clause['tipo_actuacion'] = {'$in': filters['tipo_actuacion']}
            
            if 'fecha_desde' in filters:
                where_clause['fecha_actuacion'] = {'$gte': filters['fecha_desde']}
            
            if 'utilidad_minima' in filters:
                where_clause['utilidad'] = {'$in': ['alta', 'media'] if filters['utilidad_minima'] == 'media' else ['alta']}
        
        # Búsqueda en ChromaDB
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_clause if where_clause else None,
            include=['documents', 'metadatas', 'distances']
        )
        
        # Formatear resultados
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                'id': results['ids'][0][i],
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'score': 1 - results['distances'][0][i]  # Convertir distancia a score
            })
        
        return formatted_results
    
    def _metadata_search(self, query: str, expediente: str, filters: Dict, n_results: int) -> List[Dict]:
        """Búsqueda por metadata específica"""
        
        # Extraer entidades y referencias de la query
        entities = self._extract_query_entities(query)
        legal_refs = self._extract_query_legal_refs(query)
        
        if not entities and not legal_refs:
            return []
        
        # Construir filtros de metadata
        where_clause = {}
        
        if expediente:
            where_clause['expediente_numero'] = expediente
        
        # Buscar por entidades mencionadas
        if entities:
            entity_conditions = []
            for entity_type, values in entities.items():
                for value in values:
                    entity_conditions.append({
                        f'entities.{entity_type}': {'$contains': value}
                    })
            
            if entity_conditions:
                where_clause['$or'] = entity_conditions
        
        # Buscar por referencias legales
        if legal_refs:
            ref_conditions = []
            for ref in legal_refs:
                ref_conditions.append({
                    'legal_references': {'$contains': ref}
                })
            
            if ref_conditions:
                if '$or' in where_clause:
                    where_clause['$or'].extend(ref_conditions)
                else:
                    where_clause['$or'] = ref_conditions
        
        if not where_clause:
            return []
        
        # Búsqueda en ChromaDB por metadata
        results = self.collection.get(
            where=where_clause,
            limit=n_results,
            include=['documents', 'metadatas']
        )
        
        # Formatear resultados
        formatted_results = []
        for i in range(len(results['ids'])):
            formatted_results.append({
                'id': results['ids'][i],
                'text': results['documents'][i],
                'metadata': results['metadatas'][i],
                'score': 0.8  # Score base para búsqueda por metadata
            })
        
        return formatted_results
    
    def _fuse_results(self, semantic_results: List[Dict], metadata_results: List[Dict]) -> List[Dict]:
        """Fusiona resultados de diferentes búsquedas"""
        
        # Diccionario para acumular scores
        fused_scores = {}
        all_results = {}
        
        # Procesar resultados semánticos
        for result in semantic_results:
            doc_id = result['id']
            all_results[doc_id] = result
            fused_scores[doc_id] = result['score']
        
        # Procesar resultados de metadata (boost si ya existe)
        for result in metadata_results:
            doc_id = result['id']
            if doc_id in fused_scores:
                # Boost si aparece en ambas búsquedas
                fused_scores[doc_id] *= 1.5
            else:
                all_results[doc_id] = result
                fused_scores[doc_id] = result['score']
        
        # Ordenar por score fusionado
        sorted_ids = sorted(fused_scores.keys(), key=lambda x: fused_scores[x], reverse=True)
        
        # Construir lista de resultados fusionados
        fused_results = []
        for doc_id in sorted_ids:
            result = all_results[doc_id].copy()
            result['fused_score'] = fused_scores[doc_id]
            fused_results.append(result)
        
        return fused_results
    
    def _rerank_results(self, query: str, results: List[Dict]) -> List[Dict]:
        """Reranking con cross-encoder"""
        
        if not results:
            return results
        
        # Preparar pares query-documento
        pairs = []
        for result in results:
            # Incluir metadata relevante en el texto para reranking
            enhanced_text = self._enhance_text_with_metadata(result)
            pairs.append([query, enhanced_text])
        
        # Obtener scores del reranker
        rerank_scores = self.reranker.predict(pairs)
        
        # Actualizar scores
        for i, result in enumerate(results):
            result['rerank_score'] = float(rerank_scores[i])
            # Combinar score original con rerank
            result['final_score'] = (result.get('fused_score', result['score']) * 0.3 + 
                                    result['rerank_score'] * 0.7)
        
        # Ordenar por score final
        results.sort(key=lambda x: x['final_score'], reverse=True)
        
        return results
    
    def _enhance_text_with_metadata(self, result: Dict) -> str:
        """Enriquece texto con metadata para mejor reranking"""
        
        text = result['text']
        metadata = result.get('metadata', {})
        
        # Agregar información relevante de metadata
        enhanced = f"{text}\n"
        
        if metadata.get('section'):
            enhanced += f"Sección: {metadata['section']}. "
        
        if metadata.get('entities'):
            for entity_type, values in metadata['entities'].items():
                enhanced += f"{entity_type}: {', '.join(values)}. "
        
        if metadata.get('legal_references'):
            refs = [ref['value'] for ref in metadata['legal_references']]
            enhanced += f"Referencias: {', '.join(refs)}. "
        
        return enhanced
    
    def _mmr_diversify(self, results: List[Dict], lambda_param: float = 0.5) -> List[Dict]:
        """Maximum Marginal Relevance para diversificar resultados"""
        
        if len(results) <= 1:
            return results
        
        # Seleccionar el primer documento (mayor score)
        selected = [results[0]]
        remaining = results[1:]
        
        while remaining and len(selected) < len(results):
            mmr_scores = []
            
            for doc in remaining:
                # Relevancia con la query (ya calculada)
                relevance = doc['final_score']
                
                # Máxima similaridad con documentos ya seleccionados
                max_sim = max([
                    self._compute_text_similarity(doc['text'], sel['text']) 
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
    
    def _compute_text_similarity(self, text1: str, text2: str) -> float:
        """Calcula similaridad entre dos textos"""
        # Implementación simple con Jaccard similarity
        # En producción, usar embeddings para mejor precisión
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def _extract_query_entities(self, query: str) -> Dict:
        """Extrae entidades de la query"""
        # Implementación simplificada
        # En producción, usar NER
        entities = {}
        
        # Buscar patterns comunes
        if 'c/' in query or 'contra' in query:
            parts = re.split(r'c/|contra', query)
            if len(parts) >= 2:
                entities['actor'] = [parts[0].strip()]
                entities['demandado'] = [parts[1].strip()]
        
        return entities
    
    def _extract_query_legal_refs(self, query: str) -> List[str]:
        """Extrae referencias legales de la query"""
        refs = []
        
        # Buscar leyes
        ley_matches = re.findall(r'ley\s+(\d+)', query, re.IGNORECASE)
        refs.extend([f"ley {m}" for m in ley_matches])
        
        # Buscar artículos
        art_matches = re.findall(r'art(?:ículo)?\s+(\d+)', query, re.IGNORECASE)
        refs.extend([f"artículo {m}" for m in art_matches])
        
        return refs
```

---

## 🔧 4. Integración con el Flujo Existente {#integración-flujo}

### 4.1 Modificación del Procesador de Actuaciones

```python
# Modificar: /core/procesador_pdf/__init__.py

def procesar_actuacion(
    actuacion: Actuacion,
    ruta_pdf: str = None,
    clasificador: Clasificador = None,
    analizador_vencimientos: AnalizadorVencimientos = None,
    detector_duplicados: DetectorDuplicados = None,
    rag_service: Any = None,
    chunker: LegalDocumentChunker = None,  # ← NUEVO
    metadata_enricher: LegalMetadataEnricher = None  # ← NUEVO
) -> ResultadoProcesamientoActuacion:
    """Procesa una actuación individual con chunking mejorado"""
    
    # ... código existente ...
    
    # MODIFICACIÓN: Indexación mejorada en ChromaDB
    if rag_service and resultado.texto_extraido:
        # Inicializar chunker y enricher si no se proporcionan
        if not chunker:
            chunker = LegalDocumentChunker(chunk_size=1500, overlap=300)
        if not metadata_enricher:
            metadata_enricher = LegalMetadataEnricher()
        
        # 1. Dividir en chunks semánticos
        chunks = chunker.chunk_actuacion(
            resultado.texto_extraido,
            actuacion.tipo
        )
        
        # 2. Enriquecer cada chunk con metadata
        actuacion_data = {
            'id': actuacion.id,
            'expediente_numero': actuacion.expediente_numero,
            'tipo': actuacion.tipo,
            'fecha': actuacion.fecha.isoformat() if actuacion.fecha else None,
            'utilidad': resultado.clasificacion.utilidad.value if resultado.clasificacion else 'media'
        }
        
        enriched_chunks = []
        for chunk in chunks:
            enriched_chunk = metadata_enricher.enrich_chunk(chunk, actuacion_data)
            enriched_chunks.append(enriched_chunk)
        
        # 3. Indexar cada chunk por separado
        for i, chunk in enumerate(enriched_chunks):
            doc_id = f"actuacion_{actuacion.id}_chunk_{i}"
            
            try:
                rag_service.indexar_documento(
                    contenido=chunk['text'],
                    metadata=chunk['metadata'],
                    doc_id=doc_id
                )
                
                # Marcar como indexado en la base de datos
                resultado.indexado_rag = True
                
            except Exception as e:
                logger.error(f"Error indexando chunk {doc_id}: {str(e)}")
                resultado.indexado_rag = False
    
    return resultado
```

### 4.2 Nuevo Endpoint para Consultas RAG

```python
# Agregar a: /presentation/api/rest/routers/procesamiento.py

from infrastructure.rag.search.hybrid_searcher import HybridLegalSearcher

@router.post("/consulta-rag", response_model=ConsultaRAGResponse)
async def consultar_rag(
    request: ConsultaRAGRequest,
    current_user: Usuario = Depends(get_current_user),
    limiter: RateLimiter = Depends(get_rate_limiter)
):
    """
    Consulta el sistema RAG con búsqueda híbrida mejorada
    """
    try:
        # Inicializar searcher
        chroma_client = chromadb.PersistentClient(path=settings.IA_CHROMADB_PATH)
        searcher = HybridLegalSearcher(chroma_client, "actuaciones_procesadas")
        
        # Realizar búsqueda
        resultados = searcher.search(
            query=request.consulta,
            expediente_numero=request.expediente_numero,
            filters=request.filtros,
            n_results=request.max_resultados or 5
        )
        
        # Generar respuesta con LLM si está disponible
        if settings.IA_OLLAMA_ENABLED:
            respuesta = await generar_respuesta_llm(
                query=request.consulta,
                contextos=resultados,
                modelo=settings.IA_OLLAMA_MODEL
            )
        else:
            # Respuesta simple sin LLM
            respuesta = formatear_respuesta_simple(resultados)
        
        return ConsultaRAGResponse(
            consulta=request.consulta,
            respuesta=respuesta,
            fuentes=resultados[:3],  # Top 3 fuentes
            confianza=calcular_confianza(resultados)
        )
        
    except Exception as e:
        logger.error(f"Error en consulta RAG: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def generar_respuesta_llm(query: str, contextos: List[Dict], modelo: str) -> str:
    """Genera respuesta usando LLM con contextos mejorados"""
    
    # Construir prompt optimizado
    prompt = f"""Sos un asistente legal especializado en derecho argentino.
    
    CONSULTA: {query}
    
    CONTEXTOS RELEVANTES:
    """
    
    for i, ctx in enumerate(contextos[:5]):
        prompt += f"\n[Documento {i+1}]"
        prompt += f"\n- Expediente: {ctx['metadata'].get('expediente_numero', 'N/A')}"
        prompt += f"\n- Tipo: {ctx['metadata'].get('tipo_actuacion', 'N/A')}"
        prompt += f"\n- Fecha: {ctx['metadata'].get('fecha_actuacion', 'N/A')}"
        prompt += f"\n- Sección: {ctx['metadata'].get('section', 'N/A')}"
        prompt += f"\n- Contenido: {ctx['text'][:500]}..."
        
        # Agregar entidades si existen
        if ctx['metadata'].get('entities'):
            prompt += f"\n- Partes: {ctx['metadata']['entities']}"
        
        # Agregar referencias legales si existen
        if ctx['metadata'].get('legal_references'):
            refs = [ref['value'] for ref in ctx['metadata']['legal_references']]
            prompt += f"\n- Referencias: {', '.join(refs)}"
        
        prompt += "\n"
    
    prompt += """
    INSTRUCCIONES:
    1. Responder la consulta basándote ÚNICAMENTE en los contextos proporcionados
    2. Citar específicamente el número de expediente y fecha cuando menciones información
    3. Si los contextos no contienen información suficiente, indicarlo claramente
    4. Usar terminología legal precisa
    5. Ser conciso pero completo
    
    RESPUESTA:
    """
    
    # Llamar a Ollama
    response = await ollama.generate(model=modelo, prompt=prompt)
    
    return response['response']
```

### 4.3 Actualización del Frontend

```python
# Agregar a: /frontend/src/api/procesamientoApi.ts

export interface ConsultaRAGRequest {
  consulta: string
  expediente_numero?: string
  filtros?: {
    tipo_actuacion?: string[]
    fecha_desde?: string
    fecha_hasta?: string
    utilidad_minima?: 'alta' | 'media'
  }
  max_resultados?: number
}

export interface ConsultaRAGResponse {
  consulta: string
  respuesta: string
  fuentes: FuenteRAG[]
  confianza: number
}

export interface FuenteRAG {
  id: string
  texto: string
  metadata: {
    expediente_numero: string
    tipo_actuacion: string
    fecha_actuacion: string
    section?: string
    score: number
  }
}

export async function consultarRAG(request: ConsultaRAGRequest): Promise<ConsultaRAGResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/procesamiento/consulta-rag`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getAuthToken()}`
    },
    body: JSON.stringify(request)
  })
  
  if (!response.ok) {
    throw new Error(`Error en consulta RAG: ${response.status}`)
  }
  
  return response.json()
}
```

---

## 📝 5. Implementación Paso a Paso {#implementación}

### Fase 1: Preparación (1-2 días)

1. **Backup de datos actuales**
   ```bash
   cp -r ./data/chromadb ./data/chromadb_backup_$(date +%Y%m%d)
   mysqldump sintaxis > sintaxis_backup_$(date +%Y%m%d).sql
   ```

2. **Instalar dependencias nuevas**
   ```bash
   pip install sentence-transformers cross-encoder transformers
   pip install chromadb --upgrade
   ```

3. **Crear estructura de directorios**
   ```bash
   mkdir -p infrastructure/rag/{chunkers,enrichers,search}
   ```

### Fase 2: Implementación Core (3-4 días)

1. **Implementar LegalDocumentChunker**
   - Crear `/infrastructure/rag/chunkers/legal_chunker.py`
   - Tests unitarios

2. **Implementar LegalMetadataEnricher**
   - Crear `/infrastructure/rag/enrichers/metadata_enricher.py`
   - Tests unitarios

3. **Implementar HybridLegalSearcher**
   - Crear `/infrastructure/rag/search/hybrid_searcher.py`
   - Tests de integración

### Fase 3: Integración (2-3 días)

1. **Modificar procesador_pdf**
   - Actualizar función `procesar_actuacion`
   - Agregar parámetros de chunker y enricher

2. **Agregar endpoint de consulta RAG**
   - Actualizar router de procesamiento
   - Implementar generación de respuestas

3. **Actualizar frontend**
   - Agregar componente de búsqueda RAG
   - Integrar en detalle de expediente

### Fase 4: Migración de Datos (2-3 días)

1. **Script de migración**
   ```python
   # /scripts/migrate_chromadb.py
   
   import chromadb
   from infrastructure.rag.chunkers.legal_chunker import LegalDocumentChunker
   from infrastructure.rag.enrichers.metadata_enricher import LegalMetadataEnricher
   
   def migrate_existing_data():
       """Reprocesa documentos existentes con nuevo sistema"""
       
       # Conectar a base de datos
       db = connect_to_mysql()
       
       # Obtener actuaciones procesadas
       actuaciones = db.query("SELECT * FROM actuaciones WHERE texto_extraido IS NOT NULL")
       
       # Inicializar componentes
       chunker = LegalDocumentChunker()
       enricher = LegalMetadataEnricher()
       chroma_client = chromadb.PersistentClient(path="./data/chromadb_new")
       collection = chroma_client.create_collection("actuaciones_v2")
       
       # Procesar cada actuación
       for actuacion in actuaciones:
           print(f"Procesando actuación {actuacion.id}...")
           
           # Chunking y enriquecimiento
           chunks = chunker.chunk_actuacion(actuacion.texto_extraido, actuacion.tipo)
           
           for i, chunk in enumerate(chunks):
               enriched = enricher.enrich_chunk(chunk, actuacion)
               
               # Indexar en nueva collection
               collection.add(
                   documents=[enriched['text']],
                   metadatas=[enriched['metadata']],
                   ids=[f"actuacion_{actuacion.id}_chunk_{i}"]
               )
       
       print("Migración completada!")
   ```

2. **Ejecutar migración**
   ```bash
   python scripts/migrate_chromadb.py
   ```

### Fase 5: Testing y Optimización (2-3 días)

1. **Tests de calidad**
   ```python
   # /tests/test_rag_quality.py
   
   def test_respuesta_quality():
       """Verifica que las respuestas sean más específicas"""
       
       queries = [
           "¿Cuál es el monto reclamado en el expediente FRE_005088_2021?",
           "¿Qué resolvió el juez sobre la prescripción?",
           "¿Quiénes son las partes en la causa?"
       ]
       
       for query in queries:
           response = consultar_rag(query)
           
           # Verificar que incluye información específica
           assert any([
               'pesos' in response.respuesta.lower(),
               'artículo' in response.respuesta.lower(),
               'resuelve' in response.respuesta.lower()
           ])
           
           # Verificar que cita fuentes
           assert len(response.fuentes) > 0
           
           # Verificar confianza mínima
           assert response.confianza > 0.7
   ```

2. **Benchmark de performance**
   ```python
   def benchmark_search_speed():
       """Mide tiempos de respuesta"""
       
       import time
       
       queries = generate_test_queries(100)
       times = []
       
       for query in queries:
           start = time.time()
           _ = searcher.search(query, n_results=5)
           elapsed = time.time() - start
           times.append(elapsed)
       
       avg_time = sum(times) / len(times)
       assert avg_time < 0.5  # Menos de 500ms promedio
   ```

---

## ⚙️ 6. Configuración Recomendada {#configuración}

### 6.1 Variables de Entorno Actualizadas

```bash
# .env

# ChromaDB Optimizado
IA_CHROMADB_PATH=./data/chromadb_v2
IA_CHROMADB_COLLECTION=actuaciones_v2

# Chunking
CHUNK_SIZE=1500
CHUNK_OVERLAP=300
MIN_CHUNK_SIZE=500
MAX_CHUNK_SIZE=3000

# Embeddings
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-mpnet-base-v2
EMBEDDING_BATCH_SIZE=32

# Search
SEARCH_TOP_K_INITIAL=20
SEARCH_TOP_K_RERANK=10
SEARCH_TOP_K_FINAL=5
SEARCH_USE_MMR=true
SEARCH_MMR_LAMBDA=0.7

# Reranking
RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-12-v2
RERANKER_ENABLED=true

# Cache
SEARCH_CACHE_ENABLED=true
SEARCH_CACHE_TTL=3600
SEARCH_CACHE_SIZE=1000
```

### 6.2 Configuración de ChromaDB

```python
# /infrastructure/config/chromadb_config.py

CHROMADB_SETTINGS = {
    'collection_settings': {
        'actuaciones_v2': {
            'metadata': {
                'hnsw:space': 'cosine',
                'hnsw:M': 32,  # Mayor conectividad para mejor recall
                'hnsw:ef_construction': 200,
                'hnsw:ef_search': 100
            }
        }
    },
    
    'embedding_function': {
        'model_name': 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2',
        'device': 'cuda' if torch.cuda.is_available() else 'cpu',
        'normalize_embeddings': True
    },
    
    'persistence': {
        'path': './data/chromadb_v2',
        'auto_save': True,
        'save_interval': 100  # Guardar cada 100 operaciones
    }
}
```

---

## 📊 7. Métricas de Evaluación {#métricas}

### 7.1 Métricas de Calidad

```python
# /monitoring/rag_metrics.py

class RAGMetrics:
    """Sistema de métricas para evaluar calidad del RAG"""
    
    def __init__(self):
        self.metrics = {
            'retrieval_precision': [],
            'retrieval_recall': [],
            'answer_relevance': [],
            'answer_completeness': [],
            'response_time': [],
            'user_satisfaction': []
        }
    
    def evaluate_retrieval(self, query: str, retrieved_docs: List, relevant_docs: List):
        """Evalúa precisión y recall del retrieval"""
        
        retrieved_ids = [doc['id'] for doc in retrieved_docs]
        
        # Precision: ¿Qué porcentaje de docs recuperados son relevantes?
        precision = len(set(retrieved_ids) & set(relevant_docs)) / len(retrieved_ids)
        
        # Recall: ¿Qué porcentaje de docs relevantes fueron recuperados?
        recall = len(set(retrieved_ids) & set(relevant_docs)) / len(relevant_docs)
        
        self.metrics['retrieval_precision'].append(precision)
        self.metrics['retrieval_recall'].append(recall)
        
        return {'precision': precision, 'recall': recall}
    
    def evaluate_answer_quality(self, query: str, answer: str, expected_elements: List[str]):
        """Evalúa calidad de la respuesta generada"""
        
        # Relevancia: ¿La respuesta aborda la pregunta?
        relevance_score = self._calculate_relevance(query, answer)
        
        # Completitud: ¿Incluye los elementos esperados?
        completeness_score = sum(1 for elem in expected_elements if elem in answer) / len(expected_elements)
        
        self.metrics['answer_relevance'].append(relevance_score)
        self.metrics['answer_completeness'].append(completeness_score)
        
        return {
            'relevance': relevance_score,
            'completeness': completeness_score
        }
    
    def get_summary(self) -> Dict:
        """Resumen de métricas"""
        
        return {
            'avg_precision': np.mean(self.metrics['retrieval_precision']),
            'avg_recall': np.mean(self.metrics['retrieval_recall']),
            'avg_relevance': np.mean(self.metrics['answer_relevance']),
            'avg_completeness': np.mean(self.metrics['answer_completeness']),
            'avg_response_time': np.mean(self.metrics['response_time']),
            'user_satisfaction': np.mean(self.metrics['user_satisfaction'])
        }
```

### 7.2 Dashboard de Monitoreo

```python
# /frontend/src/components/RAGDashboard.tsx

export const RAGDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<RAGMetrics | null>(null)
  
  useEffect(() => {
    fetchRAGMetrics().then(setMetrics)
  }, [])
  
  return (
    <div className="rag-dashboard">
      <h2>Métricas del Sistema RAG</h2>
      
      <div className="metrics-grid">
        <MetricCard
          title="Precisión Promedio"
          value={metrics?.avg_precision.toFixed(2)}
          target={0.85}
          unit="%"
        />
        
        <MetricCard
          title="Recall Promedio"
          value={metrics?.avg_recall.toFixed(2)}
          target={0.80}
          unit="%"
        />
        
        <MetricCard
          title="Relevancia de Respuestas"
          value={metrics?.avg_relevance.toFixed(2)}
          target={0.90}
          unit="%"
        />
        
        <MetricCard
          title="Tiempo de Respuesta"
          value={metrics?.avg_response_time.toFixed(2)}
          target={0.5}
          unit="seg"
        />
      </div>
      
      <div className="charts">
        <LineChart data={metrics?.time_series} title="Evolución de Métricas" />
        <BarChart data={metrics?.by_document_type} title="Performance por Tipo de Documento" />
      </div>
    </div>
  )
}
```

---

## 🚀 8. Plan de Migración {#migración}

### Semana 1: Preparación
- [ ] Backup completo del sistema
- [ ] Instalar dependencias
- [ ] Crear estructura de directorios
- [ ] Configurar entorno de desarrollo

### Semana 2: Desarrollo
- [ ] Implementar chunker legal
- [ ] Implementar metadata enricher
- [ ] Implementar búsqueda híbrida
- [ ] Tests unitarios

### Semana 3: Integración
- [ ] Modificar procesador de actuaciones
- [ ] Agregar endpoint de consulta RAG
- [ ] Actualizar frontend
- [ ] Tests de integración

### Semana 4: Migración y Testing
- [ ] Migrar datos existentes
- [ ] Testing en ambiente de staging
- [ ] Ajustes de performance
- [ ] Documentación

### Semana 5: Despliegue
- [ ] Deploy a producción
- [ ] Monitoreo inicial
- [ ] Ajustes finos
- [ ] Capacitación usuarios

---

## 💡 Recomendaciones Finales

### Quick Wins Inmediatos

1. **Aumentar tamaño de chunks** de texto completo a 1500 caracteres
2. **Agregar overlap del 20%** entre chunks
3. **Implementar reranking** con cross-encoder
4. **Expandir queries** con sinónimos legales

### Mejoras a Mediano Plazo

1. **Fine-tuning del modelo de embeddings** con datos propios
2. **Implementar caché** de búsquedas frecuentes
3. **A/B testing** de diferentes configuraciones
4. **Feedback loop** para mejorar continuamente

### Consideraciones de Performance

- **Batch processing** para documentos grandes
- **Índices optimizados** en ChromaDB
- **Rate limiting** en endpoints de consulta
- **Monitoreo continuo** de métricas

---

## 📚 Recursos Adicionales

- [ChromaDB Docs](https://docs.trychroma.com/)
- [Sentence Transformers](https://www.sbert.net/)
- [Modelos para Español Legal](https://huggingface.co/PlanTL-GOB-ES)
- [Cross-Encoders for Reranking](https://www.sbert.net/docs/pretrained_cross-encoders.html)

---

**Última actualización:** 2025-11-25  
**Versión:** 2.0  
**Autor:** Sistema de Optimización RAG para sintaXis
