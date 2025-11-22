"""
Servicio de NER (Named Entity Recognition) para textos jurídicos.

Utiliza GLiNER para extracción de entidades sin necesidad de
entrenamiento específico (zero-shot).
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


# Entidades jurídicas predefinidas
ENTIDADES_JURIDICAS = [
    "PERSONA",           # Nombres de personas
    "ORGANIZACION",      # Empresas, instituciones
    "TRIBUNAL",          # Juzgados, cámaras, tribunales
    "JUEZ",              # Nombres de jueces
    "ABOGADO",           # Nombres de abogados
    "FECHA",             # Fechas
    "MONTO",             # Cantidades de dinero
    "NORMA",             # Artículos, leyes, decretos
    "PLAZO",             # Plazos procesales
    "EXPEDIENTE",        # Números de expediente
    "DOMICILIO",         # Direcciones
    "DECRETO",           # Decretos específicos
    "CONCEPTO",          # Conceptos jurídicos relevantes
    "ACTOR",             # Parte demandante/actora
    "DEMANDADO",         # Parte demandada
    "TERCERO",           # Terceros citados en proceso
    "PERITO",            # Peritos designados
    "TESTIGO",           # Testigos del proceso
]


def get_tipos_entidad_from_db() -> list[str]:
    """
    Obtiene los tipos de entidad activos desde la base de datos.

    Returns:
        Lista de nombres de tipos de entidad activos
    """
    try:
        import os
        import mysql.connector

        conn = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', ''),
            database=os.getenv('MYSQL_DATABASE', 'sintaxis')
        )
        cursor = conn.cursor()
        cursor.execute("SELECT nombre FROM tipos_entidad_custom WHERE activo = TRUE ORDER BY nombre")
        tipos = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return tipos if tipos else ENTIDADES_JURIDICAS
    except Exception as e:
        logger.warning(f"Error obteniendo tipos de BD: {e}. Usando predefinidos.")
        return ENTIDADES_JURIDICAS


class NERService:
    """
    Servicio para extracción de entidades de textos jurídicos.

    Utiliza GLiNER (Generalist and Lightweight model for Named Entity Recognition)
    que permite definir entidades en runtime sin entrenamiento.
    """

    def __init__(
        self,
        model_name: str = "urchade/gliner_medium-v2.1",
        device: str = "cuda",
        threshold: float = 0.5
    ):
        """
        Inicializa el servicio NER.

        Args:
            model_name: Nombre del modelo GLiNER
            device: Dispositivo ('cuda', 'cpu')
            threshold: Umbral de confianza para aceptar entidades
        """
        self.model_name = model_name
        self.device = device
        self.threshold = threshold
        self._model = None

    def _lazy_load_model(self):
        """Carga el modelo solo cuando se necesita."""
        if self._model is None:
            try:
                from gliner import GLiNER

                logger.info(f"Cargando modelo NER: {self.model_name}")

                self._model = GLiNER.from_pretrained(self.model_name)

                # Mover a GPU si disponible
                if self.device == "cuda":
                    try:
                        self._model = self._model.to("cuda")
                        logger.info("Modelo NER cargado en GPU")
                    except Exception:
                        logger.warning("GPU no disponible, usando CPU")
                        self.device = "cpu"

                logger.info(f"Modelo NER cargado: {self.model_name}")

            except ImportError:
                raise ImportError(
                    "GLiNER no está instalado. "
                    "Instalar con: pip install gliner"
                )

        return self._model

    def extract(
        self,
        text: str,
        labels: Optional[List[str]] = None,
        threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Extrae entidades de un texto.

        Args:
            text: Texto a analizar
            labels: Lista de etiquetas de entidades a buscar
            threshold: Umbral de confianza (usa el default si no se especifica)

        Returns:
            Lista de entidades encontradas con:
            - text: texto de la entidad
            - label: tipo de entidad
            - score: confianza
            - start: posición inicio
            - end: posición fin
        """
        model = self._lazy_load_model()

        if labels is None:
            labels = ENTIDADES_JURIDICAS

        if threshold is None:
            threshold = self.threshold

        # Extraer entidades
        entities = model.predict_entities(
            text,
            labels,
            threshold=threshold
        )

        # Formatear resultado
        result = []
        for entity in entities:
            result.append({
                "text": entity["text"],
                "label": entity["label"],
                "score": round(entity["score"], 3),
                "start": entity["start"],
                "end": entity["end"]
            })

        # Ordenar por posición
        result.sort(key=lambda x: x["start"])

        return result

    def extract_juridico(self, text: str) -> Dict[str, List[str]]:
        """
        Extrae entidades jurídicas y las agrupa por tipo.

        Args:
            text: Texto a analizar

        Returns:
            Dict con listas de entidades por tipo
        """
        entities = self.extract(text, labels=ENTIDADES_JURIDICAS)

        # Agrupar por tipo
        result = {label: [] for label in ENTIDADES_JURIDICAS}

        for entity in entities:
            label = entity["label"]
            if label in result:
                text_value = entity["text"]
                if text_value not in result[label]:
                    result[label].append(text_value)

        # Limpiar tipos vacíos
        return {k: v for k, v in result.items() if v}

    def extract_partes(self, text: str) -> Dict[str, List[str]]:
        """
        Extrae partes procesales de un texto.

        Args:
            text: Texto a analizar

        Returns:
            Dict con actora, demandada, terceros
        """
        labels = ["PARTE_ACTORA", "PARTE_DEMANDADA", "TERCERO", "PERSONA", "ORGANIZACION"]
        entities = self.extract(text, labels=labels, threshold=0.4)

        result = {
            "actora": [],
            "demandada": [],
            "otros": []
        }

        for entity in entities:
            label = entity["label"]
            text_value = entity["text"]

            if "ACTORA" in label:
                if text_value not in result["actora"]:
                    result["actora"].append(text_value)
            elif "DEMANDADA" in label:
                if text_value not in result["demandada"]:
                    result["demandada"].append(text_value)
            else:
                if text_value not in result["otros"]:
                    result["otros"].append(text_value)

        return result

    def extract_fechas_plazos(self, text: str) -> Dict[str, List[str]]:
        """
        Extrae fechas y plazos de un texto.

        Args:
            text: Texto a analizar

        Returns:
            Dict con fechas y plazos
        """
        labels = ["FECHA", "PLAZO", "VENCIMIENTO"]
        entities = self.extract(text, labels=labels, threshold=0.4)

        result = {
            "fechas": [],
            "plazos": []
        }

        for entity in entities:
            label = entity["label"]
            text_value = entity["text"]

            if label == "FECHA":
                if text_value not in result["fechas"]:
                    result["fechas"].append(text_value)
            else:
                if text_value not in result["plazos"]:
                    result["plazos"].append(text_value)

        return result

    def extract_montos(self, text: str) -> List[Dict[str, Any]]:
        """
        Extrae montos monetarios de un texto.

        Args:
            text: Texto a analizar

        Returns:
            Lista de montos encontrados
        """
        labels = ["MONTO", "DINERO", "HONORARIOS", "CAPITAL", "INTERESES"]
        entities = self.extract(text, labels=labels, threshold=0.4)

        result = []
        seen = set()

        for entity in entities:
            text_value = entity["text"]
            if text_value not in seen:
                seen.add(text_value)
                result.append({
                    "monto": text_value,
                    "tipo": entity["label"],
                    "score": entity["score"]
                })

        return result

    def extract_normas(self, text: str) -> List[str]:
        """
        Extrae referencias a normas legales.

        Args:
            text: Texto a analizar

        Returns:
            Lista de normas encontradas
        """
        labels = ["NORMA", "LEY", "ARTICULO", "DECRETO", "RESOLUCION"]
        entities = self.extract(text, labels=labels, threshold=0.4)

        result = []
        seen = set()

        for entity in entities:
            text_value = entity["text"]
            if text_value not in seen:
                seen.add(text_value)
                result.append(text_value)

        return result

    def is_available(self) -> bool:
        """
        Verifica si el servicio está disponible.

        Returns:
            True si se puede cargar el modelo
        """
        try:
            self._lazy_load_model()
            return True
        except Exception as e:
            logger.error(f"Servicio NER no disponible: {e}")
            return False

    def get_model_info(self) -> dict:
        """
        Retorna información del modelo.

        Returns:
            Dict con información del modelo
        """
        return {
            "model_name": self.model_name,
            "device": self.device,
            "threshold": self.threshold,
            "labels_default": ENTIDADES_JURIDICAS,
            "loaded": self._model is not None
        }
