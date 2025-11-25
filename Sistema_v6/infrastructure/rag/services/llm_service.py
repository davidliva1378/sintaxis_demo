"""
LLMService - Servicio para generar respuestas con Ollama LLM

Maneja:
- Conexión con Ollama
- Generación de prompts con contexto
- Generación de respuestas basadas en chunks recuperados
- Gestión de tokens y temperature
"""

import logging
import requests
from typing import List, Optional, Dict, Any

from infrastructure.rag.config import get_rag_settings
from infrastructure.rag.models.dto import SearchResult, RAGResponse

logger = logging.getLogger(__name__)


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
        search_results: List[SearchResult]
    ) -> str:
        """Construir prompt con contexto legal"""

        # Extraer contexto de los chunks (ya viene limitado desde generate_answer)
        context_parts = []
        for i, result in enumerate(search_results):  # Usar todos los chunks recibidos
            chunk = result.chunk
            context_parts.append(
                f"[Documento {i+1}] Expediente: {chunk.metadata.get('expediente_numero', 'N/A')}\n"
                f"Tipo: {chunk.chunk_type.value}\n"
                f"Contenido: {chunk.texto[:500]}..."  # Limitar tamaño
            )

        context = "\n\n".join(context_parts)

        # Prompt legal específico - mejorado para evitar respuestas genéricas
        prompt = f"""Eres un asistente legal que analiza documentos judiciales argentinos.
IMPORTANTE: Debes responder ÚNICAMENTE usando la información del CONTEXTO proporcionado abajo.
NO inventes información ni des consejos genéricos. Si la respuesta está en el contexto, respóndela directamente.

CONTEXTO DE DOCUMENTOS JUDICIALES:
{context}

PREGUNTA DEL USUARIO: {question}

INSTRUCCIONES ESTRICTAS:
1. Responde SOLO con información del contexto anterior
2. Cita el número de expediente y fechas cuando estén disponibles
3. NO sugieras consultar abogados ni des disclaimers legales
4. Si la información no está en el contexto, di simplemente "La información solicitada no está disponible en los documentos indexados"
5. Sé directo y específico

RESPUESTA BASADA EN LOS DOCUMENTOS:"""

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
                logger.error(f"Ollama retornó status {response.status_code}")
                return "Error: No se pudo generar respuesta"

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


# RAG Service completo (combina búsqueda + LLM)
class RAGService:
    """Servicio RAG completo: Búsqueda + Generación"""

    def __init__(self, hybrid_search_service, llm_service: Optional[LLMService] = None):
        self.search = hybrid_search_service
        self.llm = llm_service or LLMService()

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

        # 1. Búsqueda híbrida (con pesos dinámicos si se especifican)
        search_query = SearchQuery(texto=question, **search_params)
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
