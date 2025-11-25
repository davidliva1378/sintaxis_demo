"""
Servicio de LLM para generación de texto.

Utiliza Ollama para ejecutar modelos localmente (Llama 3.1, etc).
"""

import logging
import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Generator

logger = logging.getLogger(__name__)

# Modelo por defecto (puede ser sobreescrito con variable de entorno)
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")

# Ruta del archivo de configuración
CONFIG_DIR = Path(__file__).parent.parent.parent.parent / "config"
CONFIG_FILE = CONFIG_DIR / "ia_settings.json"


def _load_saved_model() -> Optional[str]:
    """Carga el modelo guardado del archivo de configuración."""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config.get("llm_model")
    except Exception as e:
        logger.warning(f"Error cargando configuración de IA: {e}")
    return None


def _save_model(model: str) -> bool:
    """Guarda el modelo en el archivo de configuración."""
    try:
        # Crear directorio si no existe
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        # Cargar config existente o crear nueva
        config = {}
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
            except:
                pass

        # Actualizar modelo
        config["llm_model"] = model

        # Guardar
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)

        logger.info(f"Modelo LLM guardado en configuración: {model}")
        return True
    except Exception as e:
        logger.error(f"Error guardando configuración de IA: {e}")
        return False


class LLMService:
    """
    Servicio para generación de texto con LLM local.

    Utiliza Ollama como backend para ejecutar modelos como Llama 3.1.
    """

    def __init__(
        self,
        model: str = None,
        host: str = "http://localhost:11434",
        timeout: int = 120
    ):
        """
        Inicializa el servicio LLM.

        Args:
            model: Nombre del modelo en Ollama (default: OLLAMA_MODEL env o llama3.1:8b)
            host: URL del servidor Ollama
            timeout: Timeout en segundos
        """
        # Prioridad: parámetro > config guardada > env > default
        if model:
            self.model = model
        else:
            saved_model = _load_saved_model()
            self.model = saved_model or DEFAULT_MODEL
            if saved_model:
                logger.info(f"Modelo LLM cargado desde configuración: {saved_model}")

        self.host = host
        self.timeout = timeout
        self._client = None

    def set_model(self, model: str) -> bool:
        """
        Cambia el modelo activo.

        Args:
            model: Nombre del modelo

        Returns:
            True si el modelo está disponible
        """
        available = self.list_models()
        # Verificar si el modelo está disponible (con o sin :latest)
        if model in available or f"{model}:latest" in available:
            self.model = model
            # Resetear el cliente para que se reinicialice con el nuevo modelo
            self._client = None
            # Guardar en configuración para persistir entre reinicios
            _save_model(model)
            logger.info(f"Modelo cambiado a: {model}")
            return True
        else:
            logger.warning(f"Modelo {model} no disponible. Disponibles: {available}")
            return False

    def get_current_model(self) -> str:
        """
        Retorna el modelo actualmente configurado.

        Returns:
            Nombre del modelo
        """
        return self.model

    def _lazy_load_client(self):
        """Carga el cliente de Ollama solo cuando se necesita."""
        if self._client is None:
            try:
                from ollama import Client

                self._client = Client(host=self.host)

                # Verificar que el modelo esté disponible
                models = self._client.list()

                # Manejar respuesta como dict o Pydantic model
                if hasattr(models, 'models'):
                    model_list = models.models
                elif isinstance(models, dict):
                    model_list = models.get('models', [])
                else:
                    model_list = []

                # Extraer nombres - cada modelo puede ser dict o Pydantic
                # Nota: Pydantic model usa 'model' no 'name'
                model_names = []
                for m in model_list:
                    if hasattr(m, 'model'):
                        model_names.append(m.model)
                    elif hasattr(m, 'name'):
                        model_names.append(m.name)
                    elif isinstance(m, dict) and 'model' in m:
                        model_names.append(m['model'])
                    elif isinstance(m, dict) and 'name' in m:
                        model_names.append(m['name'])

                if self.model not in model_names and f"{self.model}:latest" not in model_names:
                    logger.warning(
                        f"Modelo {self.model} no encontrado. "
                        f"Modelos disponibles: {model_names}"
                    )

                logger.info(f"Cliente Ollama conectado: {self.host}")

            except ImportError:
                raise ImportError(
                    "ollama no está instalado. "
                    "Instalar con: pip install ollama"
                )
            except Exception as e:
                logger.error(f"Error conectando a Ollama: {e}")
                raise ConnectionError(
                    f"No se pudo conectar a Ollama en {self.host}. "
                    "Asegúrese de que Ollama esté ejecutándose."
                )

        return self._client

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stop: Optional[List[str]] = None
    ) -> str:
        """
        Genera texto a partir de un prompt.

        Args:
            prompt: Prompt del usuario
            system: Prompt del sistema (opcional)
            temperature: Creatividad (0-1)
            max_tokens: Máximo de tokens a generar
            stop: Secuencias de parada

        Returns:
            Texto generado
        """
        client = self._lazy_load_client()

        options = {
            "temperature": temperature,
            "num_predict": max_tokens,
            "num_ctx": 4096,  # Limitar contexto para evitar uso excesivo de memoria
        }

        if stop:
            options["stop"] = stop

        try:
            # Siempre usar chat() para mejor compatibilidad con todos los modelos
            # (generate() no funciona correctamente con algunos modelos como gpt-oss)
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            # Asegurar un mínimo de num_predict para evitar problemas con algunos modelos
            # (gpt-oss:20b retorna vacío con num_predict < 100)
            options["num_predict"] = max(options.get("num_predict", 100), 100)

            response = client.chat(
                model=self.model,
                messages=messages,
                options=options
            )

            # Manejar respuesta como dict o Pydantic model
            if hasattr(response, 'message'):
                msg = response.message
                return msg.content if hasattr(msg, 'content') else msg['content']
            else:
                return response['message']['content']

        except Exception as e:
            logger.error(f"Error generando texto: {e}")
            raise

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        Genera respuesta en formato chat.

        Args:
            messages: Lista de mensajes [{"role": "user/assistant/system", "content": "..."}]
            temperature: Creatividad
            max_tokens: Máximo de tokens

        Returns:
            Respuesta del asistente
        """
        client = self._lazy_load_client()

        options = {
            "temperature": temperature,
            "num_predict": max_tokens,
            "num_ctx": 4096,  # Limitar contexto para evitar uso excesivo de memoria
        }

        try:
            response = client.chat(
                model=self.model,
                messages=messages,
                options=options
            )
            # Manejar respuesta como dict o Pydantic model
            if hasattr(response, 'message'):
                msg = response.message
                return msg.content if hasattr(msg, 'content') else msg['content']
            else:
                return response['message']['content']

        except Exception as e:
            logger.error(f"Error en chat: {e}")
            raise

    def stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7
    ) -> Generator[str, None, None]:
        """
        Genera texto en streaming.

        Args:
            prompt: Prompt del usuario
            system: Prompt del sistema
            temperature: Creatividad

        Yields:
            Fragmentos de texto
        """
        client = self._lazy_load_client()

        options = {
            "temperature": temperature,
            "num_ctx": 4096,  # Limitar contexto para evitar uso excesivo de memoria
        }

        try:
            if system:
                stream = client.chat(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt}
                    ],
                    options=options,
                    stream=True
                )
                for chunk in stream:
                    yield chunk['message']['content']
            else:
                stream = client.generate(
                    model=self.model,
                    prompt=prompt,
                    options=options,
                    stream=True
                )
                for chunk in stream:
                    yield chunk['response']

        except Exception as e:
            logger.error(f"Error en streaming: {e}")
            raise

    def summarize(
        self,
        text: str,
        max_length: int = 200,
        language: str = "español"
    ) -> str:
        """
        Resume un texto.

        Args:
            text: Texto a resumir
            max_length: Longitud máxima del resumen
            language: Idioma del resumen

        Returns:
            Resumen del texto
        """
        system = f"""Eres un asistente experto en resumir textos jurídicos.
Tu tarea es crear resúmenes concisos y precisos en {language}.
Enfócate en los puntos clave: qué se decide, fundamentos principales, y consecuencias."""

        prompt = f"""Resume el siguiente texto en máximo {max_length} palabras:

{text}

Resumen:"""

        return self.generate(prompt, system=system, temperature=0.3)

    def extract_info(
        self,
        text: str,
        fields: List[str]
    ) -> Dict[str, Any]:
        """
        Extrae información estructurada de un texto.

        Args:
            text: Texto a analizar
            fields: Campos a extraer

        Returns:
            Dict con los campos extraídos
        """
        fields_str = ", ".join(fields)

        system = """Eres un asistente experto en análisis de documentos jurídicos.
Extrae información de manera precisa y estructurada.
Si un campo no se encuentra, indica "No especificado".
Responde SOLO en formato JSON válido."""

        prompt = f"""Del siguiente texto, extrae estos campos: {fields_str}

Texto:
{text}

Responde en formato JSON:"""

        response = self.generate(prompt, system=system, temperature=0.1)

        # Intentar parsear JSON
        import json
        try:
            # Limpiar posibles caracteres extra
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning(f"No se pudo parsear JSON: {response}")
            return {"raw": response}

    def classify(
        self,
        text: str,
        categories: List[str],
        return_scores: bool = False
    ) -> str:
        """
        Clasifica un texto en una categoría.

        Args:
            text: Texto a clasificar
            categories: Lista de categorías posibles
            return_scores: Si retornar scores de confianza

        Returns:
            Categoría seleccionada
        """
        categories_str = ", ".join(categories)

        system = """Eres un clasificador de textos jurídicos.
Analiza el texto y selecciona la categoría más apropiada.
Responde SOLO con el nombre de la categoría."""

        prompt = f"""Clasifica el siguiente texto en una de estas categorías: {categories_str}

Texto:
{text}

Categoría:"""

        response = self.generate(prompt, system=system, temperature=0.1)

        # Limpiar respuesta
        response = response.strip().upper()

        # Buscar match con categorías
        for cat in categories:
            if cat.upper() in response:
                return cat

        return response

    def is_available(self) -> bool:
        """
        Verifica si el servicio está disponible.

        Returns:
            True si se puede conectar a Ollama
        """
        try:
            client = self._lazy_load_client()
            client.list()
            return True
        except Exception as e:
            logger.error(f"Servicio LLM no disponible: {e}")
            return False

    def list_models(self) -> List[str]:
        """
        Lista los modelos disponibles en Ollama.

        Returns:
            Lista de nombres de modelos
        """
        try:
            client = self._lazy_load_client()
            models = client.list()

            # La respuesta puede ser un dict o un objeto con atributo 'models'
            if hasattr(models, 'models'):
                model_list = models.models
            elif isinstance(models, dict):
                model_list = models.get('models', [])
            else:
                logger.warning(f"Formato inesperado de respuesta: {type(models)}")
                return []

            # Extraer nombres - cada modelo puede ser dict o Pydantic
            # Nota: Pydantic model usa 'model' no 'name'
            result = []
            for m in model_list:
                if hasattr(m, 'model'):
                    result.append(m.model)
                elif hasattr(m, 'name'):
                    result.append(m.name)
                elif isinstance(m, dict) and 'model' in m:
                    result.append(m['model'])
                elif isinstance(m, dict) and 'name' in m:
                    result.append(m['name'])

            return result
        except Exception as e:
            logger.error(f"Error listando modelos: {e}")
            return []

    def get_model_info(self) -> dict:
        """
        Retorna información del modelo.

        Returns:
            Dict con información
        """
        return {
            "model": self.model,
            "host": self.host,
            "timeout": self.timeout,
            "available_models": self.list_models() if self._client else [],
            "connected": self._client is not None
        }
