"""
NER LLM Fallback Service - Mejora entidades de baja confianza usando LLM

Funcionalidades:
- Procesa entidades de GLiNER con score bajo
- Usa LLM para validar/corregir entidades
- Extrae entidades que GLiNER no detectó
- Cache de resultados frecuentes
"""

import json
import logging
import hashlib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from infrastructure.config.hardware_profiles import get_active_profile, HardwareProfile

logger = logging.getLogger(__name__)


@dataclass
class EnhancedEntity:
    """Entidad mejorada con información del LLM"""
    text: str
    label: str
    score: float
    start: int
    end: int
    source: str  # "gliner", "llm", "llm_corrected"
    original_label: Optional[str] = None  # Si fue corregida


class NERLLMFallbackService:
    """Servicio para mejorar NER usando LLM como fallback"""

    # Umbral de confianza para usar LLM
    DEFAULT_THRESHOLD = 0.6

    # Prompt para extracción con LLM
    EXTRACTION_PROMPT = """Eres un experto en análisis de documentos legales argentinos. Tu tarea es extraer entidades nombradas del siguiente texto jurídico.

Texto a analizar:
---
{text}
---

Extrae TODAS las entidades que encuentres de los siguientes tipos:
- PERSONA: Nombres completos de personas
- ORGANIZACION: Empresas, instituciones, organismos
- TRIBUNAL: Juzgados, cámaras, cortes
- JUEZ: Nombres de jueces o magistrados
- ABOGADO: Nombres de abogados o letrados
- FECHA: Fechas en cualquier formato
- MONTO: Cantidades de dinero (pesos, dólares, etc.)
- NORMA: Artículos, leyes, decretos, resoluciones
- EXPEDIENTE: Números de expediente
- DOMICILIO: Direcciones postales
- ACTOR: Parte demandante/actora
- DEMANDADO: Parte demandada

IMPORTANTE: Responde SOLO en formato JSON con esta estructura:
{{
    "entidades": [
        {{"text": "texto exacto", "label": "TIPO", "score": 0.95}},
        ...
    ]
}}"""

    # Prompt para validación
    VALIDATION_PROMPT = """Analiza las siguientes entidades extraídas de un texto jurídico argentino y valida si están correctamente clasificadas.

Texto original:
---
{text}
---

Entidades a validar:
{entities_json}

Para cada entidad, indica:
1. Si la clasificación es correcta
2. Si no es correcta, cuál sería la clasificación adecuada
3. Si la entidad es válida o es ruido (texto que no es una entidad real)

Responde en JSON:
{{
    "validaciones": [
        {{
            "text": "texto original",
            "label_original": "TIPO_ORIGINAL",
            "valido": true/false,
            "label_correcto": "TIPO_CORRECTO o null si es correcto",
            "confianza": 0.95
        }},
        ...
    ]
}}"""

    def __init__(
        self,
        llm_service=None,
        threshold: float = DEFAULT_THRESHOLD,
        profile: Optional[HardwareProfile] = None
    ):
        """
        Inicializa el servicio.

        Args:
            llm_service: Servicio LLM (se crea si no se proporciona)
            threshold: Umbral bajo el cual usar LLM
            profile: Perfil de hardware
        """
        self.profile = profile or get_active_profile()
        self._llm_service = llm_service
        self.threshold = threshold
        self._cache: Dict[str, List[EnhancedEntity]] = {}

        logger.info(f"NERLLMFallbackService inicializado (threshold={threshold})")

    @property
    def llm_service(self):
        """Lazy loading del servicio LLM"""
        if self._llm_service is None:
            try:
                from infrastructure.rag.services.llm_service import LLMService
                self._llm_service = LLMService()
            except Exception as e:
                logger.warning(f"No se pudo cargar LLMService: {e}")
        return self._llm_service

    def enhance_entities(
        self,
        text: str,
        entities: List[Dict[str, Any]],
        threshold: Optional[float] = None
    ) -> List[EnhancedEntity]:
        """
        Mejora entidades usando LLM para las de baja confianza.

        Args:
            text: Texto original
            entities: Entidades de GLiNER
            threshold: Umbral de confianza

        Returns:
            Lista de entidades mejoradas
        """
        threshold = threshold or self.threshold

        # Separar entidades por confianza
        high_confidence = []
        low_confidence = []

        for entity in entities:
            enhanced = EnhancedEntity(
                text=entity["text"],
                label=entity["label"],
                score=entity["score"],
                start=entity["start"],
                end=entity["end"],
                source="gliner"
            )
            if entity["score"] >= threshold:
                high_confidence.append(enhanced)
            else:
                low_confidence.append(enhanced)

        # Si no hay entidades de baja confianza, retornar directamente
        if not low_confidence:
            return high_confidence

        # Validar entidades de baja confianza con LLM
        if self.llm_service:
            try:
                validated = self._validate_with_llm(text, low_confidence)
                high_confidence.extend(validated)
            except Exception as e:
                logger.warning(f"Error validando con LLM: {e}")
                # Agregar de todos modos con score original
                high_confidence.extend(low_confidence)
        else:
            high_confidence.extend(low_confidence)

        # Ordenar por posición
        high_confidence.sort(key=lambda x: x.start)

        return high_confidence

    def extract_missing_entities(
        self,
        text: str,
        existing_entities: List[Dict[str, Any]]
    ) -> List[EnhancedEntity]:
        """
        Extrae entidades que GLiNER no detectó usando LLM.

        Args:
            text: Texto a analizar
            existing_entities: Entidades ya extraídas por GLiNER

        Returns:
            Nuevas entidades encontradas por LLM
        """
        if not self.llm_service:
            return []

        try:
            # Obtener posiciones existentes para evitar duplicados
            existing_positions = {
                (e["start"], e["end"]) for e in existing_entities
            }
            existing_texts = {e["text"].lower() for e in existing_entities}

            # Extraer con LLM
            llm_entities = self._extract_with_llm(text)

            # Filtrar duplicados
            new_entities = []
            for entity in llm_entities:
                # Buscar posición en el texto
                start = text.lower().find(entity["text"].lower())
                if start >= 0:
                    end = start + len(entity["text"])
                    pos = (start, end)

                    # Evitar duplicados
                    if pos not in existing_positions and entity["text"].lower() not in existing_texts:
                        new_entities.append(EnhancedEntity(
                            text=entity["text"],
                            label=entity["label"],
                            score=entity.get("score", 0.8),
                            start=start,
                            end=end,
                            source="llm"
                        ))
                        existing_positions.add(pos)
                        existing_texts.add(entity["text"].lower())

            return new_entities

        except Exception as e:
            logger.error(f"Error extrayendo entidades con LLM: {e}")
            return []

    def _validate_with_llm(
        self,
        text: str,
        entities: List[EnhancedEntity]
    ) -> List[EnhancedEntity]:
        """Valida entidades de baja confianza con LLM"""
        if not entities:
            return []

        # Preparar JSON de entidades
        entities_data = [
            {"text": e.text, "label": e.label, "score": e.score}
            for e in entities
        ]

        prompt = self.VALIDATION_PROMPT.format(
            text=text[:2000],  # Limitar texto
            entities_json=json.dumps(entities_data, ensure_ascii=False, indent=2)
        )

        response = self.llm_service.generate(
            prompt=prompt,
            temperature=0.1,
            max_tokens=1000
        )

        # Parsear respuesta
        data = self._parse_json_response(response)
        if not data or "validaciones" not in data:
            return entities  # Retornar sin cambios si falla

        # Procesar validaciones
        validated = []
        validations_by_text = {v["text"]: v for v in data["validaciones"]}

        for entity in entities:
            validation = validations_by_text.get(entity.text)
            if validation:
                if validation.get("valido", True):
                    # Si tiene label correcto diferente, corregir
                    if validation.get("label_correcto") and validation["label_correcto"] != entity.label:
                        entity.original_label = entity.label
                        entity.label = validation["label_correcto"]
                        entity.source = "llm_corrected"

                    entity.score = validation.get("confianza", entity.score)
                    validated.append(entity)
                # Si no es válido, no agregar
            else:
                validated.append(entity)  # Mantener si no hay validación

        return validated

    def _extract_with_llm(self, text: str) -> List[Dict[str, Any]]:
        """Extrae entidades directamente con LLM"""
        prompt = self.EXTRACTION_PROMPT.format(text=text[:3000])

        response = self.llm_service.generate(
            prompt=prompt,
            temperature=0.1,
            max_tokens=1500
        )

        data = self._parse_json_response(response)
        if not data or "entidades" not in data:
            return []

        return data["entidades"]

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

    def process_full(
        self,
        text: str,
        gliner_entities: List[Dict[str, Any]],
        threshold: Optional[float] = None,
        extract_missing: bool = True
    ) -> List[EnhancedEntity]:
        """
        Proceso completo: mejora + extracción de faltantes.

        Args:
            text: Texto a analizar
            gliner_entities: Entidades de GLiNER
            threshold: Umbral de confianza
            extract_missing: Si extraer entidades faltantes

        Returns:
            Lista completa de entidades mejoradas
        """
        # 1. Mejorar entidades existentes
        enhanced = self.enhance_entities(text, gliner_entities, threshold)

        # 2. Extraer entidades faltantes (opcional)
        if extract_missing and self.llm_service:
            missing = self.extract_missing_entities(text, gliner_entities)
            enhanced.extend(missing)

        # 3. Ordenar por posición
        enhanced.sort(key=lambda x: x.start)

        return enhanced

    def to_dict_list(self, entities: List[EnhancedEntity]) -> List[Dict[str, Any]]:
        """Convierte lista de EnhancedEntity a lista de dicts"""
        return [
            {
                "text": e.text,
                "label": e.label,
                "score": e.score,
                "start": e.start,
                "end": e.end,
                "source": e.source,
                "original_label": e.original_label
            }
            for e in entities
        ]
