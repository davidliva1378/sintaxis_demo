"""
QueryExpansionService - Expande queries usando LLM para mejorar recall

Funcionalidades:
- Genera variaciones semánticas de la query
- Extrae términos jurídicos clave
- Identifica sinónimos del dominio legal
- Cache de expansiones frecuentes
"""

import logging
import hashlib
import json
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from pathlib import Path

from infrastructure.config.hardware_profiles import get_active_profile, HardwareProfile

logger = logging.getLogger(__name__)


@dataclass
class ExpandedQuery:
    """Resultado de expansión de query"""
    original: str
    variations: List[str]
    keywords: List[str]
    legal_terms: List[str]
    expansion_method: str  # "llm", "rules", "cache"


class QueryExpansionService:
    """Servicio para expandir queries usando LLM"""

    # Términos jurídicos comunes para expansión basada en reglas
    LEGAL_SYNONYMS = {
        "sentencia": ["fallo", "resolución", "dictamen", "pronunciamiento"],
        "demanda": ["escrito inicial", "libelo", "pretensión"],
        "apelación": ["recurso", "impugnación", "alzada"],
        "prueba": ["evidencia", "elemento probatorio", "medio de prueba"],
        "actor": ["demandante", "accionante", "parte actora", "reclamante"],
        "demandado": ["accionado", "parte demandada", "requerido"],
        "juez": ["magistrado", "juzgador", "tribunal"],
        "abogado": ["letrado", "apoderado", "representante legal", "patrocinante"],
        "daños y perjuicios": ["indemnización", "resarcimiento", "reparación"],
        "contrato": ["convenio", "acuerdo", "pacto"],
        "notificación": ["cédula", "comunicación", "emplazamiento"],
        "plazo": ["término", "lapso", "período"],
        "nulidad": ["invalidez", "anulación", "ineficacia"],
        "embargo": ["medida cautelar", "traba", "afectación"],
        "caducidad": ["perención", "decaimiento", "extinción del proceso"],
        "prescripción": ["extinción por el tiempo", "liberación"],
        "costas": ["gastos del proceso", "honorarios"],
        "recurso extraordinario": ["REX", "recurso federal"],
        "amparo": ["acción de amparo", "tutela urgente"],
        "medida cautelar": ["cautelar", "tutela anticipada", "medida precautoria"],
    }

    # Prompt para expansión con LLM
    EXPANSION_PROMPT = """Eres un experto en derecho argentino. Tu tarea es expandir la siguiente consulta de búsqueda jurídica para mejorar los resultados.

Consulta original: "{query}"

Genera exactamente {n_variations} variaciones de esta consulta que:
1. Mantengan el mismo significado pero usen términos jurídicos alternativos
2. Sean relevantes para expedientes judiciales argentinos
3. Incluyan sinónimos legales apropiados

Responde SOLO en formato JSON con esta estructura:
{{
    "variations": ["variación 1", "variación 2", ...],
    "keywords": ["palabra clave 1", "palabra clave 2", ...],
    "legal_terms": ["término legal 1", "término legal 2", ...]
}}"""

    def __init__(self, llm_service=None, profile: Optional[HardwareProfile] = None):
        """
        Inicializa el servicio de expansión de queries.

        Args:
            llm_service: Servicio LLM opcional (se crea si no se proporciona)
            profile: Perfil de hardware opcional
        """
        self.profile = profile or get_active_profile()
        self._llm_service = llm_service
        self._cache: Dict[str, ExpandedQuery] = {}
        self._cache_file = Path(__file__).parent.parent / "data" / "query_expansion_cache.json"

        # Cargar cache si existe
        self._load_cache()

        logger.info(
            f"QueryExpansionService inicializado (enabled={self.profile.query_expansion_enabled}, "
            f"max_variations={self.profile.query_expansion_max_variations})"
        )

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

    def expand(
        self,
        query: str,
        n_variations: Optional[int] = None,
        use_llm: bool = True,
        use_cache: bool = True
    ) -> ExpandedQuery:
        """
        Expande una query para mejorar los resultados de búsqueda.

        Args:
            query: Query original
            n_variations: Número de variaciones a generar
            use_llm: Si usar LLM para expansión
            use_cache: Si usar cache de expansiones

        Returns:
            ExpandedQuery con variaciones y términos
        """
        if not self.profile.query_expansion_enabled:
            return ExpandedQuery(
                original=query,
                variations=[query],
                keywords=[],
                legal_terms=[],
                expansion_method="disabled"
            )

        n_vars = n_variations or self.profile.query_expansion_max_variations

        # 1. Verificar cache
        cache_key = self._get_cache_key(query)
        if use_cache and cache_key in self._cache:
            logger.debug(f"Cache hit para query: {query[:50]}...")
            cached = self._cache[cache_key]
            cached.expansion_method = "cache"
            return cached

        # 2. Intentar expansión con LLM
        if use_llm and self.llm_service:
            try:
                expanded = self._expand_with_llm(query, n_vars)
                if expanded:
                    self._cache[cache_key] = expanded
                    self._save_cache()
                    return expanded
            except Exception as e:
                logger.warning(f"Error en expansión LLM: {e}")

        # 3. Fallback a expansión basada en reglas
        expanded = self._expand_with_rules(query)
        self._cache[cache_key] = expanded
        self._save_cache()

        return expanded

    def _expand_with_llm(self, query: str, n_variations: int) -> Optional[ExpandedQuery]:
        """Expande query usando LLM"""
        try:
            prompt = self.EXPANSION_PROMPT.format(
                query=query,
                n_variations=n_variations
            )

            response = self.llm_service.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=500
            )

            # Parsear respuesta JSON
            data = self._parse_llm_response(response)
            if not data:
                return None

            return ExpandedQuery(
                original=query,
                variations=data.get("variations", [query])[:n_variations],
                keywords=data.get("keywords", []),
                legal_terms=data.get("legal_terms", []),
                expansion_method="llm"
            )

        except Exception as e:
            logger.error(f"Error en expansión LLM: {e}")
            return None

    def _parse_llm_response(self, response: str) -> Optional[Dict]:
        """Parsea respuesta JSON del LLM"""
        try:
            # Limpiar respuesta
            response = response.strip()

            # Buscar JSON en la respuesta
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            # Intentar encontrar el JSON
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                response = response[start:end]

            return json.loads(response)

        except json.JSONDecodeError as e:
            logger.warning(f"Error parseando JSON de LLM: {e}")
            return None

    def _expand_with_rules(self, query: str) -> ExpandedQuery:
        """Expande query usando reglas predefinidas"""
        variations = [query]
        keywords = []
        legal_terms = []

        query_lower = query.lower()

        # Buscar términos conocidos y agregar sinónimos
        for term, synonyms in self.LEGAL_SYNONYMS.items():
            if term in query_lower:
                legal_terms.append(term)
                keywords.extend(synonyms[:2])  # Agregar algunos sinónimos

                # Crear variaciones reemplazando el término
                for syn in synonyms[:self.profile.query_expansion_max_variations - 1]:
                    variation = query_lower.replace(term, syn)
                    if variation != query_lower and variation not in variations:
                        variations.append(variation)

        # Extraer palabras clave (palabras > 4 caracteres que no son stopwords)
        stopwords = {"para", "como", "esta", "este", "estos", "estas", "donde", "cuando",
                     "sobre", "entre", "desde", "hasta", "contra", "ante", "hacia"}
        words = query_lower.split()
        keywords.extend([w for w in words if len(w) > 4 and w not in stopwords])

        return ExpandedQuery(
            original=query,
            variations=variations[:self.profile.query_expansion_max_variations],
            keywords=list(set(keywords)),
            legal_terms=list(set(legal_terms)),
            expansion_method="rules"
        )

    def _get_cache_key(self, query: str) -> str:
        """Genera clave de cache para una query"""
        normalized = query.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()

    def _load_cache(self):
        """Carga cache de expansiones desde disco"""
        try:
            if self._cache_file.exists():
                with open(self._cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for key, value in data.items():
                        self._cache[key] = ExpandedQuery(**value)
                logger.info(f"Cache cargado: {len(self._cache)} entradas")
        except Exception as e:
            logger.warning(f"Error cargando cache: {e}")
            self._cache = {}

    def _save_cache(self):
        """Guarda cache de expansiones a disco"""
        try:
            # Crear directorio si no existe
            self._cache_file.parent.mkdir(parents=True, exist_ok=True)

            # Convertir a dict para serializar
            data = {}
            for key, value in self._cache.items():
                data[key] = {
                    "original": value.original,
                    "variations": value.variations,
                    "keywords": value.keywords,
                    "legal_terms": value.legal_terms,
                    "expansion_method": value.expansion_method
                }

            with open(self._cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.warning(f"Error guardando cache: {e}")

    def get_all_query_variations(self, query: str) -> List[str]:
        """
        Obtiene todas las variaciones de query para búsqueda multi-query.

        Args:
            query: Query original

        Returns:
            Lista de todas las variaciones incluyendo la original
        """
        expanded = self.expand(query)

        all_queries = [expanded.original]
        all_queries.extend(expanded.variations)

        # Agregar queries con términos legales
        for term in expanded.legal_terms[:2]:
            if term not in query.lower():
                all_queries.append(f"{query} {term}")

        return list(set(all_queries))

    def clear_cache(self):
        """Limpia el cache de expansiones"""
        self._cache = {}
        if self._cache_file.exists():
            self._cache_file.unlink()
        logger.info("Cache de expansiones limpiado")
