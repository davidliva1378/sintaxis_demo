"""
Relation Extraction Service - Extrae relaciones entre entidades usando LLM

Funcionalidades:
- Identifica relaciones entre entidades extraídas
- Soporta relaciones jurídicas específicas (actor-demandado, juez-expediente, etc.)
- Genera grafos de conocimiento para visualización
- Cache de relaciones frecuentes
"""

import json
import logging
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

from infrastructure.config.hardware_profiles import get_active_profile, HardwareProfile

logger = logging.getLogger(__name__)


@dataclass
class Relation:
    """Representa una relación entre dos entidades"""
    source_entity: str
    source_label: str
    target_entity: str
    target_label: str
    relation_type: str
    confidence: float
    context: Optional[str] = None  # Fragmento de texto que soporta la relación


@dataclass
class RelationExtractionResult:
    """Resultado de extracción de relaciones"""
    entities: List[Dict[str, Any]]
    relations: List[Relation]
    graph_data: Optional[Dict[str, Any]] = None  # Para visualización


class RelationExtractionService:
    """Servicio para extracción de relaciones entre entidades usando LLM"""

    # Tipos de relaciones jurídicas
    RELATION_TYPES = {
        "DEMANDA": "La entidad A demanda/acciona contra B",
        "REPRESENTA": "El abogado A representa a la parte B",
        "JUZGA": "El juez A interviene en el expediente B",
        "PERTENECE_A": "La actuación A pertenece al expediente B",
        "DICTAMINA": "El juez/tribunal A dictamina/resuelve sobre B",
        "CITA": "El documento A cita la norma/artículo B",
        "RECLAMA": "La parte A reclama el monto B",
        "NOTIFICA": "Se notifica a la entidad A sobre B",
        "APELA": "La parte A apela la resolución B",
        "CONDENA": "Se condena a A a pagar/hacer B",
        "ABSUELVE": "Se absuelve a A de B",
        "CAUTELAR": "Se traba medida cautelar sobre A a favor de B",
        "PERICIA": "El perito A realiza pericia sobre B",
        "TESTIFICA": "El testigo A declara sobre B",
    }

    # Prompt para extracción de relaciones
    EXTRACTION_PROMPT = """Eres un experto en análisis de documentos legales argentinos. Tu tarea es identificar relaciones entre las entidades de un texto jurídico.

Texto a analizar:
---
{text}
---

Entidades identificadas:
{entities_json}

Identifica todas las relaciones entre estas entidades. Los tipos de relaciones posibles son:
{relation_types}

Para cada relación encontrada, indica:
1. Entidad origen (source)
2. Entidad destino (target)
3. Tipo de relación
4. Confianza (0.0 a 1.0)
5. Contexto: fragmento del texto que evidencia la relación

IMPORTANTE: Responde SOLO en formato JSON con esta estructura:
{{
    "relations": [
        {{
            "source": "texto de entidad origen",
            "source_label": "TIPO_ENTIDAD",
            "target": "texto de entidad destino",
            "target_label": "TIPO_ENTIDAD",
            "relation_type": "TIPO_RELACION",
            "confidence": 0.95,
            "context": "fragmento del texto..."
        }},
        ...
    ]
}}"""

    def __init__(
        self,
        llm_service=None,
        profile: Optional[HardwareProfile] = None
    ):
        """
        Inicializa el servicio de extracción de relaciones.

        Args:
            llm_service: Servicio LLM (se crea si no se proporciona)
            profile: Perfil de hardware
        """
        self.profile = profile or get_active_profile()
        self._llm_service = llm_service
        self._cache: Dict[str, List[Relation]] = {}

        logger.info("RelationExtractionService inicializado")

    @property
    def llm_service(self):
        """Lazy loading del servicio LLM"""
        if self._llm_service is None:
            try:
                from application.services.ia.llm_service import LLMService
                self._llm_service = LLMService()
            except Exception as e:
                logger.warning(f"No se pudo cargar LLMService: {e}")
        return self._llm_service

    def extract_relations(
        self,
        text: str,
        entities: List[Dict[str, Any]],
        use_cache: bool = True
    ) -> RelationExtractionResult:
        """
        Extrae relaciones entre entidades de un texto.

        Args:
            text: Texto original
            entities: Lista de entidades extraídas
            use_cache: Si usar cache

        Returns:
            RelationExtractionResult con entidades y relaciones
        """
        if not entities or len(entities) < 2:
            return RelationExtractionResult(
                entities=entities,
                relations=[],
                graph_data=None
            )

        # Verificar cache
        cache_key = self._get_cache_key(text, entities)
        if use_cache and cache_key in self._cache:
            logger.debug("Cache hit para extracción de relaciones")
            cached_relations = self._cache[cache_key]
            return RelationExtractionResult(
                entities=entities,
                relations=cached_relations,
                graph_data=self._build_graph_data(entities, cached_relations)
            )

        # Extraer relaciones con LLM
        relations = self._extract_with_llm(text, entities)

        # Guardar en cache
        if use_cache:
            self._cache[cache_key] = relations

        # Construir datos del grafo
        graph_data = self._build_graph_data(entities, relations)

        return RelationExtractionResult(
            entities=entities,
            relations=relations,
            graph_data=graph_data
        )

    def _extract_with_llm(
        self,
        text: str,
        entities: List[Dict[str, Any]]
    ) -> List[Relation]:
        """Extrae relaciones usando LLM"""
        if not self.llm_service:
            logger.warning("LLM service no disponible")
            return []

        try:
            # Preparar entities JSON
            entities_data = [
                {"text": e["text"], "label": e["label"]}
                for e in entities
            ]

            # Preparar tipos de relación
            relation_types_str = "\n".join(
                f"- {k}: {v}" for k, v in self.RELATION_TYPES.items()
            )

            prompt = self.EXTRACTION_PROMPT.format(
                text=text[:3000],  # Limitar texto
                entities_json=json.dumps(entities_data, ensure_ascii=False, indent=2),
                relation_types=relation_types_str
            )

            response = self.llm_service.generate(
                prompt=prompt,
                temperature=0.1,
                max_tokens=2000
            )

            # Parsear respuesta
            data = self._parse_json_response(response)
            if not data or "relations" not in data:
                return []

            # Convertir a objetos Relation
            relations = []
            for rel in data["relations"]:
                try:
                    relation = Relation(
                        source_entity=rel["source"],
                        source_label=rel.get("source_label", "UNKNOWN"),
                        target_entity=rel["target"],
                        target_label=rel.get("target_label", "UNKNOWN"),
                        relation_type=rel["relation_type"],
                        confidence=float(rel.get("confidence", 0.8)),
                        context=rel.get("context")
                    )
                    relations.append(relation)
                except (KeyError, ValueError) as e:
                    logger.warning(f"Error parseando relación: {e}")
                    continue

            logger.info(f"Extraídas {len(relations)} relaciones")
            return relations

        except Exception as e:
            logger.error(f"Error extrayendo relaciones: {e}")
            return []

    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """Parsea respuesta JSON del LLM"""
        try:
            response = response.strip()

            # Buscar JSON en la respuesta
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            # Encontrar el JSON
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                response = response[start:end]

            return json.loads(response)

        except json.JSONDecodeError as e:
            logger.warning(f"Error parseando JSON: {e}")
            return None

    def _build_graph_data(
        self,
        entities: List[Dict[str, Any]],
        relations: List[Relation]
    ) -> Dict[str, Any]:
        """
        Construye datos para visualización de grafo.

        Returns:
            Dict con nodos y edges para visualización (formato Cytoscape.js compatible)
        """
        # Crear nodos únicos
        nodes = {}
        for entity in entities:
            node_id = self._get_node_id(entity["text"])
            if node_id not in nodes:
                nodes[node_id] = {
                    "data": {
                        "id": node_id,
                        "label": entity["text"],
                        "type": entity["label"],
                        "score": entity.get("score", 1.0)
                    }
                }

        # Crear edges
        edges = []
        for i, rel in enumerate(relations):
            source_id = self._get_node_id(rel.source_entity)
            target_id = self._get_node_id(rel.target_entity)

            # Asegurar que los nodos existen
            if source_id not in nodes:
                nodes[source_id] = {
                    "data": {
                        "id": source_id,
                        "label": rel.source_entity,
                        "type": rel.source_label,
                        "score": 0.5
                    }
                }
            if target_id not in nodes:
                nodes[target_id] = {
                    "data": {
                        "id": target_id,
                        "label": rel.target_entity,
                        "type": rel.target_label,
                        "score": 0.5
                    }
                }

            edges.append({
                "data": {
                    "id": f"edge_{i}",
                    "source": source_id,
                    "target": target_id,
                    "label": rel.relation_type,
                    "confidence": rel.confidence,
                    "context": rel.context
                }
            })

        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }

    def _get_node_id(self, text: str) -> str:
        """Genera ID único para un nodo"""
        return hashlib.md5(text.lower().strip().encode()).hexdigest()[:8]

    def _get_cache_key(self, text: str, entities: List[Dict]) -> str:
        """Genera clave de cache"""
        entities_str = json.dumps(
            sorted([e["text"] for e in entities]),
            sort_keys=True
        )
        combined = f"{text[:500]}{entities_str}"
        return hashlib.md5(combined.encode()).hexdigest()

    def extract_partes_procesales(
        self,
        text: str,
        entities: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """
        Extrae partes procesales basándose en relaciones.

        Args:
            text: Texto original
            entities: Entidades extraídas

        Returns:
            Dict con actora, demandada, representantes
        """
        result = self.extract_relations(text, entities)

        partes = {
            "actora": [],
            "demandada": [],
            "representantes_actora": [],
            "representantes_demandada": [],
            "juez": [],
            "tribunal": []
        }

        # Identificar partes por relaciones
        for rel in result.relations:
            if rel.relation_type == "DEMANDA":
                if rel.source_entity not in partes["actora"]:
                    partes["actora"].append(rel.source_entity)
                if rel.target_entity not in partes["demandada"]:
                    partes["demandada"].append(rel.target_entity)

            elif rel.relation_type == "REPRESENTA":
                # El abogado representa a alguien
                if rel.target_entity in partes["actora"]:
                    if rel.source_entity not in partes["representantes_actora"]:
                        partes["representantes_actora"].append(rel.source_entity)
                elif rel.target_entity in partes["demandada"]:
                    if rel.source_entity not in partes["representantes_demandada"]:
                        partes["representantes_demandada"].append(rel.source_entity)

            elif rel.relation_type in ("JUZGA", "DICTAMINA"):
                if rel.source_label in ("JUEZ", "MAGISTRADO"):
                    if rel.source_entity not in partes["juez"]:
                        partes["juez"].append(rel.source_entity)
                elif rel.source_label == "TRIBUNAL":
                    if rel.source_entity not in partes["tribunal"]:
                        partes["tribunal"].append(rel.source_entity)

        # Limpiar vacíos
        return {k: v for k, v in partes.items() if v}

    def to_dict(self, result: RelationExtractionResult) -> Dict[str, Any]:
        """Convierte resultado a diccionario serializable"""
        return {
            "entities": result.entities,
            "relations": [
                {
                    "source_entity": r.source_entity,
                    "source_label": r.source_label,
                    "target_entity": r.target_entity,
                    "target_label": r.target_label,
                    "relation_type": r.relation_type,
                    "confidence": r.confidence,
                    "context": r.context
                }
                for r in result.relations
            ],
            "graph_data": result.graph_data
        }

    def clear_cache(self):
        """Limpia el cache de relaciones"""
        self._cache = {}
        logger.info("Cache de relaciones limpiado")
