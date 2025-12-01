"""
LLMService - Servicio para generar respuestas con Ollama LLM

Maneja:
- Conexión con Ollama
- Generación de prompts con contexto
- Generación de respuestas basadas en chunks recuperados
- Gestión de tokens y temperature
- Prompts dinámicos por tipo de pregunta (TAREA 1.3)
- Chain-of-Thought reasoning (TAREA 1.4)
- Compresión de contexto (TAREA 1.5)
"""

import logging
import requests
import re
from typing import List, Optional, Dict, Any, Literal

from infrastructure.rag.config import get_rag_settings
from infrastructure.rag.models.dto import SearchResult, RAGResponse

logger = logging.getLogger(__name__)


# =============================================================================
# TAREA 1.3: Prompts Dinámicos por Tipo de Pregunta
# =============================================================================

QuestionType = Literal["factual", "analisis", "temporal", "procesal", "default"]

PROMPT_TEMPLATES: Dict[QuestionType, str] = {
    "factual": """Responde con hechos concretos del expediente.
Cita fechas, nombres y eventos específicos.
Sé preciso y directo.""",

    "analisis": """Analiza el razonamiento jurídico del caso.
Explica los fundamentos legales y precedentes citados.
Identifica argumentos clave de cada parte.""",

    "temporal": """Ordena cronológicamente los eventos del expediente.
Identifica plazos y vencimientos importantes.
Señala fechas clave del proceso.""",

    "procesal": """Indica el estado procesal actual del expediente.
Describe la última actuación relevante.
Sugiere próximos pasos según el procedimiento.""",

    "default": """Responde de manera clara y estructurada.
Usa la información disponible en los documentos.
Cita fuentes cuando sea posible."""
}


def detect_question_type(query: str) -> QuestionType:
    """
    Detecta el tipo de pregunta para seleccionar el prompt adecuado.

    Args:
        query: Pregunta del usuario

    Returns:
        Tipo de pregunta detectado
    """
    query_lower = query.lower()

    # Patrones para cada tipo
    factual_patterns = [
        "qué pasó", "qué ocurrió", "cuáles son los hechos",
        "quién es", "qué dice", "cuál es el monto", "cuánto",
        "dónde", "nombre del", "quiénes son"
    ]

    analisis_patterns = [
        "por qué", "fundamento", "razón", "argumento",
        "cómo se justifica", "análisis", "interpretación",
        "explica", "explique", "motivo", "causa"
    ]

    temporal_patterns = [
        "cuándo", "fecha", "plazo", "término", "vencimiento",
        "cronología", "historia", "tiempo", "días",
        "antes de", "después de", "orden"
    ]

    procesal_patterns = [
        "qué sigue", "próximo paso", "estado", "etapa",
        "instancia", "recurso", "apelación", "apelacion", "apelar",
        "situación actual", "notificación", "pendiente"
    ]

    # Detectar tipo
    if any(p in query_lower for p in factual_patterns):
        return "factual"
    elif any(p in query_lower for p in analisis_patterns):
        return "analisis"
    elif any(p in query_lower for p in temporal_patterns):
        return "temporal"
    elif any(p in query_lower for p in procesal_patterns):
        return "procesal"

    return "default"


# =============================================================================
# TAREA 1.4: Chain-of-Thought System Prompt
# =============================================================================

SYSTEM_PROMPT_COT = """Eres un asistente jurídico argentino experto en análisis de expedientes judiciales.

PROCESO DE RESPUESTA (sigue estos pasos):
1. ANÁLISIS: Identifica qué información relevante hay en los documentos proporcionados
2. CONEXIÓN: Relaciona la información con la pregunta del usuario
3. RESPUESTA: Formula una respuesta clara y estructurada
4. CITAS: Indica exactamente de qué documento obtuviste cada información

REGLAS ESTRICTAS:
- SOLO usa información de los documentos proporcionados
- Si no encuentras la información, indícalo claramente
- Cita siempre la fuente: [Doc X]
- Usa terminología jurídica argentina apropiada
- NO inventes información ni des consejos genéricos
- NO sugieras consultar abogados ni des disclaimers"""


class LLMService:
    """Servicio para generar respuestas usando Ollama LLM"""

    def __init__(self):
        self.settings = get_rag_settings()
        self.base_url = self.settings.ollama_host
        self.model = self.settings.ollama_model
        self.temperature = self.settings.ollama_temperature
        self.max_tokens = self.settings.ollama_max_tokens

    def health_check(self) -> bool:
        """Verificar que Ollama esté disponible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check falló: {e}")
            return False

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None
    ) -> str:
        """
        Genera texto libre (wrapper para _call_ollama compatible con ClasificadorService).
        """
        full_prompt = prompt
        if system:
            full_prompt = f"{system}\n\n{prompt}"
            
        return self._call_ollama(full_prompt, model=model, temperature=temperature)

    def generate_answer(
        self,
        question: str,
        search_results: List[SearchResult],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        num_chunks: Optional[int] = None,
    ) -> RAGResponse:
        """
        Generar respuesta usando LLM + contexto de chunks

        Args:
            question: Pregunta del usuario
            search_results: Chunks relevantes recuperados
            model: Modelo a usar (opcional, usa default si no se especifica)
            temperature: Temperature del LLM (opcional)
            num_chunks: Cantidad de chunks a usar para contexto (opcional)

        Returns:
            RAGResponse con respuesta generada
        """
        try:
            logger.info(f"Generando respuesta para: '{question}'")

            # Usar parámetros dinámicos o defaults
            use_model = model or self.model
            use_temperature = temperature if temperature is not None else self.temperature
            use_num_chunks = num_chunks if num_chunks is not None else 5

            # Construir prompt con contexto (limitado a num_chunks)
            prompt = self._build_prompt(question, search_results[:use_num_chunks])

            # Generar respuesta con parámetros dinámicos
            response_text = self._call_ollama(prompt, model=use_model, temperature=use_temperature)

            # Crear RAGResponse
            rag_response = RAGResponse(
                pregunta=question,
                respuesta=response_text,
                resultados=search_results[:use_num_chunks],
                metadata={
                    "model": use_model,
                    "num_chunks": len(search_results[:use_num_chunks]),
                    "temperature": use_temperature,
                }
            )

            logger.info(f"✅ Respuesta generada ({len(response_text)} caracteres)")
            return rag_response

        except Exception as e:
            logger.error(f"Error al generar respuesta: {e}")
            # Retornar respuesta de error
            return RAGResponse(
                pregunta=question,
                respuesta=f"Error al generar respuesta: {str(e)}",
                resultados=search_results,
                metadata={"error": str(e)}
            )

    def _build_prompt(
        self,
        question: str,
        search_results: List[SearchResult],
        use_cot: bool = True
    ) -> str:
        """
        Construir prompt con contexto legal.

        TAREA 1.3: Usa prompts dinámicos según tipo de pregunta
        TAREA 1.4: Incluye Chain-of-Thought si use_cot=True

        Args:
            question: Pregunta del usuario
            search_results: Resultados de búsqueda
            use_cot: Si usar Chain-of-Thought reasoning

        Returns:
            Prompt construido
        """
        # Detectar tipo de pregunta (TAREA 1.3)
        question_type = detect_question_type(question)
        type_specific_instructions = PROMPT_TEMPLATES.get(question_type, PROMPT_TEMPLATES["default"])

        logger.debug(f"Tipo de pregunta detectado: {question_type}")

        # Extraer contexto de los chunks
        context_parts = []
        for i, result in enumerate(search_results):
            chunk = result.chunk
            expediente = chunk.metadata.get('expediente_numero', 'N/A')
            fecha = chunk.metadata.get('fecha', '')
            tipo = chunk.chunk_type.value if hasattr(chunk.chunk_type, 'value') else str(chunk.chunk_type)

            # Incluir más metadata para citas precisas
            header = f"[Doc {i+1}] Expediente: {expediente}"
            if fecha:
                header += f" | Fecha: {fecha}"
            header += f" | Tipo: {tipo}"

            context_parts.append(
                f"{header}\n{chunk.texto[:600]}"
            )

        context = "\n\n---\n\n".join(context_parts)

        # Construir prompt según modo (TAREA 1.4)
        if use_cot:
            # Chain-of-Thought: razonamiento estructurado
            prompt = f"""{SYSTEM_PROMPT_COT}

INSTRUCCIONES ESPECÍFICAS PARA ESTA PREGUNTA:
{type_specific_instructions}

DOCUMENTOS DISPONIBLES:
{context}

PREGUNTA: {question}

RESPUESTA (siguiendo el proceso ANÁLISIS → CONEXIÓN → RESPUESTA → CITAS):"""
        else:
            # Modo directo sin CoT
            prompt = f"""Eres un asistente legal experto en documentos judiciales argentinos.

{type_specific_instructions}

CONTEXTO DE DOCUMENTOS:
{context}

PREGUNTA: {question}

REGLAS:
- Responde SOLO con información del contexto
- Cita fuentes: [Doc X]
- Si no hay información, indícalo claramente

RESPUESTA:"""

        return prompt

    def _call_ollama(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Llamar a Ollama API para generar respuesta"""
        try:
            url = f"{self.base_url}/api/generate"

            use_model = model or self.model
            use_temperature = temperature if temperature is not None else self.temperature

            payload = {
                "model": use_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": use_temperature,
                    "num_predict": self.max_tokens,
                }
            }

            response = requests.post(
                url,
                json=payload,
                timeout=self.settings.ollama_timeout
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                logger.error(f"Ollama retornó status {response.status_code}: {response.text}")
                return f"Error: No se pudo generar respuesta (Status {response.status_code})"

        except Exception as e:
            logger.error(f"Error llamando a Ollama: {e}")
            raise

    def list_models(self) -> List[str]:
        """Listar modelos disponibles en Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            return []
        except Exception as e:
            logger.error(f"Error listando modelos: {e}")
            return []

    def summarize(self, text: str, max_length: int = 500) -> str:
        """
        Genera un resumen del texto proporcionado.

        Args:
            text: Texto a resumir
            max_length: Longitud aproximada del resumen (en palabras)

        Returns:
            Resumen generado
        """
        try:
            prompt = f"""Resume el siguiente texto legal de manera concisa y precisa.
Mantén los puntos clave, fechas, montos y nombres importantes.
El resumen debe tener aproximadamente {max_length} palabras.

TEXTO:
{text[:15000]}  # Limitar entrada para evitar errores

RESUMEN:"""

            return self._call_ollama(prompt, temperature=0.2)
        except Exception as e:
            logger.error(f"Error generando resumen: {e}")
            return "No se pudo generar el resumen."


# =============================================================================
# TAREA 1.5: Context Compressor
# =============================================================================

class ContextCompressor:
    """
    Comprime contexto largo manteniendo información relevante para la query.

    Útil cuando hay muchos chunks y se quiere reducir tokens enviados al LLM.
    """

    def __init__(self, llm_service: Optional['LLMService'] = None):
        """
        Args:
            llm_service: Servicio LLM para comprimir (opcional, crea uno nuevo si no se pasa)
        """
        self._llm = llm_service

    @property
    def llm(self) -> 'LLMService':
        """Lazy loading del servicio LLM"""
        if self._llm is None:
            self._llm = LLMService()
        return self._llm

    def compress(
        self,
        chunks: List[str],
        query: str,
        max_chars: int = 3000
    ) -> str:
        """
        Comprime una lista de chunks manteniendo información relevante.

        Args:
            chunks: Lista de textos a comprimir
            query: Pregunta del usuario (para filtrar relevancia)
            max_chars: Máximo de caracteres en resultado

        Returns:
            Texto comprimido
        """
        total_chars = sum(len(c) for c in chunks)

        # Si ya cabe, retornar sin comprimir
        if total_chars <= max_chars:
            return "\n---\n".join(chunks)

        logger.info(f"Comprimiendo contexto: {total_chars} -> {max_chars} chars")

        # Comprimir cada chunk
        compressed = []
        chars_per_chunk = max_chars // len(chunks)

        for i, chunk in enumerate(chunks):
            if len(chunk) <= chars_per_chunk:
                # Chunk pequeño, no comprimir
                compressed.append(f"[Doc {i+1}] {chunk}")
            else:
                # Comprimir con LLM
                summary = self._compress_chunk(chunk, query, chars_per_chunk)
                compressed.append(f"[Doc {i+1}] {summary}")

        return "\n---\n".join(compressed)

    def _compress_chunk(
        self,
        chunk: str,
        query: str,
        max_chars: int
    ) -> str:
        """Comprime un chunk individual usando LLM"""
        try:
            prompt = f"""Resume este fragmento de documento judicial,
manteniendo SOLO información relevante para: "{query}"

Fragmento:
{chunk[:1500]}

INSTRUCCIONES:
- Máximo {max_chars // 4} palabras
- Mantén fechas, nombres y montos exactos
- Elimina información no relacionada con la pregunta
- Sé conciso pero preciso

Resumen:"""

            response = self.llm._call_ollama(prompt, temperature=0.1)
            return response[:max_chars]

        except Exception as e:
            logger.warning(f"Error comprimiendo chunk: {e}")
            # Fallback: truncar
            return chunk[:max_chars] + "..."

    def compress_search_results(
        self,
        results: List[SearchResult],
        query: str,
        max_chars: int = 3000
    ) -> List[SearchResult]:
        """
        Comprime los textos de una lista de SearchResult.

        Args:
            results: Lista de SearchResult
            query: Pregunta del usuario
            max_chars: Máximo total de caracteres

        Returns:
            Lista de SearchResult con textos comprimidos
        """
        chunks = [r.chunk.texto for r in results]
        total_chars = sum(len(c) for c in chunks)

        if total_chars <= max_chars:
            return results

        # Calcular ratio de compresión
        ratio = max_chars / total_chars

        # Comprimir cada resultado
        for result in results:
            target_len = int(len(result.chunk.texto) * ratio)
            if target_len < len(result.chunk.texto):
                result.chunk.texto = self._compress_chunk(
                    result.chunk.texto,
                    query,
                    target_len
                )

        return results


# RAG Service completo (combina búsqueda + LLM)
class RAGService:
    """Servicio RAG completo: Búsqueda + Generación"""

    def __init__(
        self,
        hybrid_search_service,
        llm_service: Optional[LLMService] = None,
        compressor: Optional[ContextCompressor] = None
    ):
        self.search = hybrid_search_service
        self.llm = llm_service or LLMService()
        self.compressor = compressor or ContextCompressor(self.llm)

    def query(
        self,
        question: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        dense_weight: Optional[float] = None,
        sparse_weight: Optional[float] = None,
        **search_params
    ) -> RAGResponse:
        """
        Query completo RAG: Búsqueda + Generación

        Args:
            question: Pregunta del usuario
            model: Modelo LLM a usar (opcional)
            temperature: Temperature del LLM (opcional)
            dense_weight: Peso búsqueda vectorial (opcional)
            sparse_weight: Peso búsqueda BM25 (opcional)
            **search_params: Parámetros adicionales para búsqueda

        Returns:
            RAGResponse con respuesta generada
        """
        from infrastructure.rag.models.dto import SearchQuery
        from core.domain.expediente_utils import normalizar_numero_expediente

        # Extraer y normalizar número de expediente
        filter_expediente = search_params.get("filter_expediente")
        if filter_expediente:
            filter_expediente = normalizar_numero_expediente(filter_expediente)

        # 1. Búsqueda híbrida (con pesos dinámicos si se especifican)
        search_query = SearchQuery(
            texto=question,
            limit=search_params.get("limit", 10),
            filter_expediente=filter_expediente,
            filter_tipo=search_params.get("filter_tipo")
        )
        search_results = self.search.search(
            search_query,
            dense_weight=dense_weight,
            sparse_weight=sparse_weight
        )

        if not search_results:
            return RAGResponse(
                pregunta=question,
                respuesta="No se encontraron documentos relevantes para responder la pregunta.",
                resultados=[],
                metadata={"warning": "no_results"}
            )

        # 2. Generar respuesta con LLM (con parámetros dinámicos)
        num_chunks = search_params.get("limit", 5)
        rag_response = self.llm.generate_answer(
            question,
            search_results,
            model=model,
            temperature=temperature,
            num_chunks=num_chunks
        )

        return rag_response
