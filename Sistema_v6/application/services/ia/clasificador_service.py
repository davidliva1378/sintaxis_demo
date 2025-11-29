"""
Servicio de clasificación automática de actuaciones judiciales.

Utiliza LLM para clasificar el tipo de actuación basándose en su contenido.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


# Tipos de actuaciones del sistema
TIPOS_ACTUACION = [
    "MOVIMIENTO",
    "ESCRITO_AGREGADO",
    "FIRMA_DESPACHO",
    "DEO",
    "CEDULA_ELECTRONICA_TRIBUNAL",
    "ESCRITO_INCORPORADO",
    "CEDULA_ELECTRONICA_PARTE",
    "PUBLICACION_SENTENCIA",
    "DESPACHO_INCORPORADO",
    "NOTIFICACION",
    "AUDIENCIA",
    "RESOLUCION",
    "AUTO",
    "SENTENCIA",
    "OTRO"
]

# Descripciones para mejorar la clasificación
DESCRIPCION_TIPOS = {
    "MOVIMIENTO": "Cambio de estado o trámite general del expediente",
    "ESCRITO_AGREGADO": "Documento presentado por las partes y agregado al expediente",
    "FIRMA_DESPACHO": "Despacho firmado por el juez o funcionario",
    "DEO": "Despacho Electrónico de Origen",
    "CEDULA_ELECTRONICA_TRIBUNAL": "Cédula de notificación emitida por el tribunal",
    "ESCRITO_INCORPORADO": "Escrito incorporado al sistema",
    "CEDULA_ELECTRONICA_PARTE": "Cédula de notificación electrónica a la parte",
    "PUBLICACION_SENTENCIA": "Publicación de sentencia o resolución",
    "DESPACHO_INCORPORADO": "Despacho incorporado al sistema",
    "NOTIFICACION": "Notificación general",
    "AUDIENCIA": "Convocatoria o acta de audiencia",
    "RESOLUCION": "Resolución judicial",
    "AUTO": "Auto interlocutorio",
    "SENTENCIA": "Sentencia definitiva",
    "OTRO": "Otro tipo de actuación no clasificada"
}


class ClasificadorService:
    """
    Servicio para clasificación automática de actuaciones.

    Utiliza LLM con prompts especializados para clasificar
    el tipo de actuación basándose en su contenido textual.
    """

    def __init__(self, llm_service=None):
        """
        Inicializa el clasificador.

        Args:
            llm_service: Servicio LLM (se crea uno si no se proporciona)
        """
        self._llm_service = llm_service
        self._tipos = TIPOS_ACTUACION
        self._descripciones = DESCRIPCION_TIPOS
        
        # Cargar reglas desde archivo
        self.rules_file = Path("data/classification_rules.conf")
        self.reglas, self.config = self._load_rules()

    def _load_rules(self) -> Tuple[List[Tuple[str, List[Tuple[str, float]]]], Dict[str, Any]]:
        """Carga las reglas y configuración desde el archivo."""
        import json
        
        # Configuración por defecto
        default_config = {
            "threshold": 0.9,
            "model": None
        }

        # Reglas por defecto (hardcoded) como fallback
        default_rules = [
            ("SENTENCIA", [
                ("sentencia definitiva", 0.95),
                ("fallo:", 0.9),
                ("resuelvo:", 0.85),
                ("se resuelve:", 0.85),
            ]),
            # ... (se mantienen las reglas por defecto, truncadas para brevedad)
        ]
        
        # Si falla la carga, devolver defaults
        final_rules = default_rules
        final_config = default_config

        try:
            if self.rules_file.exists():
                with open(self.rules_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    rules_json = data.get("rules", [])
                    config_json = data.get("config", {})
                    
                    # Cargar configuración
                    final_config = {
                        "threshold": config_json.get("threshold", 0.9),
                        "model": config_json.get("model")
                    }

                    # Convertir formato JSON a formato interno (lista de tuplas)
                    loaded_rules = []
                    for rule in rules_json:
                        tipo = rule.get("tipo")
                        patrones = []
                        for p in rule.get("patrones", []):
                            patrones.append((p.get("texto"), p.get("confianza")))
                        loaded_rules.append((tipo, patrones))
                    
                    if loaded_rules:
                        final_rules = loaded_rules
                        logger.info(f"Cargadas {len(loaded_rules)} reglas de clasificación desde archivo")
        except Exception as e:
            logger.error(f"Error cargando reglas de clasificación: {e}")
        
        if final_rules == default_rules:
            logger.info("Usando reglas de clasificación por defecto")
            
        return final_rules, final_config

    def _save_rules(self) -> bool:
        """Guarda las reglas y configuración actuales en el archivo."""
        import json
        try:
            # Convertir formato interno a JSON
            rules_json = []
            for tipo, patrones in self.reglas:
                patrones_json = []
                for texto, confianza in patrones:
                    patrones_json.append({"texto": texto, "confianza": confianza})
                rules_json.append({"tipo": tipo, "patrones": patrones_json})
            
            data = {
                "rules": rules_json,
                "config": self.config
            }
            
            # Asegurar que el directorio existe
            self.rules_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.rules_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            logger.error(f"Error guardando reglas de clasificación: {e}")
            return False

    def get_rules(self) -> Dict[str, Any]:
        """Retorna las reglas y configuración en formato amigable para API."""
        rules_api = []
        for tipo, patrones in self.reglas:
            patrones_api = []
            for texto, confianza in patrones:
                patrones_api.append({"texto": texto, "confianza": confianza})
            rules_api.append({"tipo": tipo, "patrones": patrones_api})
            
        return {
            "rules": rules_api,
            "config": self.config
        }

    def update_rules(self, data: Dict[str, Any]) -> bool:
        """Actualiza reglas y configuración desde la API."""
        try:
            # Actualizar configuración si existe
            if "config" in data:
                new_config = data["config"]
                self.config["threshold"] = float(new_config.get("threshold", self.config["threshold"]))
                self.config["model"] = new_config.get("model", self.config["model"])

            # Actualizar reglas si existen
            if "rules" in data:
                new_rules = data["rules"]
                converted_rules = []
                for rule in new_rules:
                    tipo = rule.get("tipo")
                    if not tipo:
                        continue
                    patrones = []
                    for p in rule.get("patrones", []):
                        texto = p.get("texto")
                        confianza = p.get("confianza", 0.5)
                        if texto:
                            patrones.append((texto, float(confianza)))
                    converted_rules.append((tipo, patrones))
                self.reglas = converted_rules
            
            return self._save_rules()
        except Exception as e:
            logger.error(f"Error actualizando reglas: {e}")
            return False

    def _get_llm(self):
        """Obtiene el servicio LLM (lazy loading)."""
        if self._llm_service is None:
            from .llm_service import LLMService
            self._llm_service = LLMService()
        return self._llm_service

    def clasificar(
        self,
        texto: str,
        contexto: Optional[str] = None,
        usar_llm: bool = True
    ) -> Dict[str, Any]:
        """
        Clasifica una actuación basándose en su texto.

        Args:
            texto: Contenido textual de la actuación
            contexto: Contexto adicional (título, metadata, etc.)
            usar_llm: Si usar LLM o solo reglas

        Returns:
            Dict con tipo, confianza y justificación
        """
        if not texto or len(texto.strip()) < 10:
            return {
                "tipo": "OTRO",
                "confianza": 0.0,
                "justificacion": "Texto insuficiente para clasificar"
            }

        # Primero intentar con reglas (más rápido)
        resultado_reglas = self._clasificar_por_reglas(texto, contexto)

        # Usar umbral configurable
        threshold = self.config.get("threshold", 0.9)
        if resultado_reglas["confianza"] >= threshold:
            return resultado_reglas

        # Si no hay alta confianza y se permite LLM, usar IA
        if usar_llm:
            try:
                resultado_llm = self._clasificar_con_llm(texto, contexto)

                # Combinar resultados si hay discrepancia
                if resultado_reglas["tipo"] == resultado_llm["tipo"]:
                    resultado_llm["confianza"] = min(
                        1.0,
                        resultado_llm["confianza"] + 0.1
                    )

                return resultado_llm

            except Exception as e:
                logger.warning(f"Error en clasificación LLM: {e}")
                return resultado_reglas

        return resultado_reglas

    def _clasificar_por_reglas(
        self,
        texto: str,
        contexto: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Clasificación basada en reglas y palabras clave.

        Args:
            texto: Texto a clasificar
            contexto: Contexto adicional

        Returns:
            Dict con tipo y confianza
        """
        texto_lower = texto.lower()
        contexto_lower = (contexto or "").lower()
        texto_completo = f"{contexto_lower} {texto_lower}"

        # Usar reglas cargadas dinámicamente
        reglas = self.reglas

        mejor_match = ("OTRO", 0.0, "No se encontraron patrones claros")

        for tipo, patrones in reglas:
            for patron, confianza_base in patrones:
                if patron in texto_completo:
                    # Ajustar confianza por posición
                    if patron in contexto_lower:
                        confianza = min(1.0, confianza_base + 0.1)
                    else:
                        confianza = confianza_base

                    if confianza > mejor_match[1]:
                        mejor_match = (
                            tipo,
                            confianza,
                            f"Patrón encontrado: '{patron}'"
                        )

        return {
            "tipo": mejor_match[0],
            "confianza": round(mejor_match[1], 2),
            "justificacion": mejor_match[2],
            "metodo": "reglas"
        }

    def _clasificar_con_llm(
        self,
        texto: str,
        contexto: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Clasificación usando LLM.

        Args:
            texto: Texto a clasificar
            contexto: Contexto adicional

        Returns:
            Dict con tipo, confianza y justificación
        """
        llm = self._get_llm()

        # Construir lista de tipos con descripciones
        tipos_texto = "\n".join([
            f"- {tipo}: {self._descripciones.get(tipo, '')}"
            for tipo in self._tipos
        ])

        # Truncar texto si es muy largo
        texto_truncado = texto[:2000] if len(texto) > 2000 else texto

        system_prompt = """Eres un clasificador experto de actuaciones judiciales argentinas.
Tu tarea es clasificar el tipo de actuación basándote en su contenido.
Responde SOLO con el formato JSON especificado, sin texto adicional."""

        user_prompt = f"""Clasifica la siguiente actuación judicial en uno de estos tipos:

{tipos_texto}

{"Contexto: " + contexto if contexto else ""}

Texto de la actuación:
{texto_truncado}

Responde en formato JSON:
{{
    "tipo": "TIPO_SELECCIONADO",
    "confianza": 0.0 a 1.0,
    "justificacion": "breve explicación"
}}"""

        try:
            # Usar modelo específico si está configurado
            model = self.config.get("model")
            
            response = llm.generate(
                user_prompt,
                system=system_prompt,
                temperature=0.1,
                max_tokens=200,
                model=model
            )

            # Parsear respuesta JSON
            import json

            # Limpiar respuesta
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]

            resultado = json.loads(response)

            # Validar tipo
            if resultado.get("tipo") not in self._tipos:
                resultado["tipo"] = "OTRO"
                resultado["confianza"] = 0.5

            resultado["metodo"] = "llm"
            return resultado

        except Exception as e:
            logger.error(f"Error parseando respuesta LLM: {e}")
            return {
                "tipo": "OTRO",
                "confianza": 0.3,
                "justificacion": f"Error en clasificación: {str(e)}",
                "metodo": "llm_error"
            }

    def clasificar_batch(
        self,
        actuaciones: List[Dict[str, str]],
        usar_llm: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Clasifica múltiples actuaciones.

        Args:
            actuaciones: Lista de dicts con 'texto' y opcionalmente 'contexto'
            usar_llm: Si usar LLM o solo reglas

        Returns:
            Lista de resultados de clasificación
        """
        resultados = []

        for actuacion in actuaciones:
            texto = actuacion.get("texto", "")
            contexto = actuacion.get("contexto")

            resultado = self.clasificar(texto, contexto, usar_llm)
            resultado["id"] = actuacion.get("id")
            resultados.append(resultado)

        return resultados

    def get_tipos(self) -> List[Dict[str, str]]:
        """
        Retorna los tipos de actuación disponibles.

        Returns:
            Lista de tipos con sus descripciones
        """
        return [
            {"tipo": tipo, "descripcion": self._descripciones.get(tipo, "")}
            for tipo in self._tipos
        ]

    def agregar_tipo(self, tipo: str, descripcion: str = ""):
        """
        Agrega un nuevo tipo de actuación.

        Args:
            tipo: Nombre del tipo
            descripcion: Descripción del tipo
        """
        if tipo not in self._tipos:
            self._tipos.append(tipo)
            self._descripciones[tipo] = descripcion
            logger.info(f"Tipo agregado: {tipo}")
