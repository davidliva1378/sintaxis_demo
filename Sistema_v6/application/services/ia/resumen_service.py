"""
Servicio de resumen ejecutivo para expedientes judiciales.

Genera resumenes ejecutivos consolidados usando LLM.
"""

import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class ResumenService:
    """
    Servicio para generar resumenes ejecutivos de expedientes.

    Utiliza LLMService para generar resumenes contextualizados.
    """

    def __init__(self, llm_service=None):
        """
        Inicializa el servicio de resumen.

        Args:
            llm_service: Instancia de LLMService (opcional, se crea si no se provee)
        """
        self._llm = llm_service

    def _get_llm(self):
        """Obtiene o crea instancia de LLMService."""
        if self._llm is None:
            from .llm_service import LLMService
            self._llm = LLMService()
        return self._llm

    def generar_resumen_expediente(
        self,
        caratula: str,
        actuaciones_textos: List[str],
        entidades: Optional[Dict[str, List[str]]] = None,
        partes: Optional[Dict[str, List[str]]] = None,
        max_palabras: int = 150
    ) -> Optional[str]:
        """
        Genera un resumen ejecutivo del expediente.

        Args:
            caratula: Caratula del expediente
            actuaciones_textos: Lista de textos de actuaciones relevantes
            entidades: Dict de entidades agrupadas por tipo
            partes: Dict de partes procesales
            max_palabras: Maximo de palabras del resumen

        Returns:
            Resumen ejecutivo o None si falla
        """
        try:
            llm = self._get_llm()

            if not llm.is_available():
                logger.warning("LLM no disponible para generar resumen")
                return None

            # Construir contexto
            contexto = self._construir_contexto(
                caratula, actuaciones_textos, entidades, partes
            )

            # Prompt especializado para resumenes juridicos
            system = """Eres un asistente juridico experto en resumir expedientes judiciales argentinos.

Tu tarea es generar un RESUMEN EJECUTIVO conciso que permita a un abogado entender rapidamente:
1. De que trata el caso (objeto)
2. Quienes son las partes (si se identifican)
3. Estado procesal actual o ultimas novedades relevantes
4. Aspectos clave a tener en cuenta

Reglas:
- Escribe en español rioplatense profesional
- Se directo y conciso, sin frases innecesarias
- Usa terminologia juridica apropiada
- Si hay montos, mencionalos
- Si hay plazos o vencimientos proximos, resaltalos
- NO inventes informacion que no este en el contexto"""

            prompt = f"""Genera un resumen ejecutivo de maximo {max_palabras} palabras para el siguiente expediente:

CARATULA: {caratula}

{contexto}

RESUMEN EJECUTIVO:"""

            resumen = llm.generate(
                prompt=prompt,
                system=system,
                temperature=0.3,  # Baja creatividad para precision
                max_tokens=500
            )

            # Limpiar resumen
            resumen = resumen.strip()
            if resumen.startswith("RESUMEN EJECUTIVO:"):
                resumen = resumen[18:].strip()

            return resumen

        except Exception as e:
            logger.error(f"Error generando resumen: {e}")
            return None

    def _construir_contexto(
        self,
        caratula: str,
        actuaciones_textos: List[str],
        entidades: Optional[Dict[str, List[str]]] = None,
        partes: Optional[Dict[str, List[str]]] = None
    ) -> str:
        """Construye el contexto para el prompt."""
        partes_ctx = []

        # Partes procesales
        if partes:
            partes_str = []
            for rol, nombres in partes.items():
                if nombres:
                    partes_str.append(f"- {rol}: {', '.join(nombres[:3])}")
            if partes_str:
                partes_ctx.append("PARTES IDENTIFICADAS:")
                partes_ctx.extend(partes_str)
                partes_ctx.append("")

        # Entidades relevantes
        if entidades:
            entidades_str = []
            for tipo, valores in entidades.items():
                if valores and tipo in ['MONTO', 'FECHA', 'NORMA']:
                    entidades_str.append(f"- {tipo}: {', '.join(valores[:5])}")
            if entidades_str:
                partes_ctx.append("DATOS RELEVANTES:")
                partes_ctx.extend(entidades_str)
                partes_ctx.append("")

        # Actuaciones (limitadas para no exceder contexto)
        if actuaciones_textos:
            # Tomar las ultimas actuaciones (mas relevantes)
            textos_seleccionados = actuaciones_textos[-5:]
            texto_actuaciones = "\n---\n".join(
                t[:1000] for t in textos_seleccionados if t
            )
            if texto_actuaciones:
                partes_ctx.append("ULTIMAS ACTUACIONES RELEVANTES:")
                partes_ctx.append(texto_actuaciones[:3000])  # Limitar total

        return "\n".join(partes_ctx)

    def generar_resumen_actuacion(
        self,
        tipo: str,
        detalle: str,
        texto_extraido: Optional[str] = None,
        max_palabras: int = 50
    ) -> Optional[str]:
        """
        Genera un resumen breve de una actuacion individual.

        Args:
            tipo: Tipo de actuacion
            detalle: Detalle de la actuacion
            texto_extraido: Texto del PDF (opcional)
            max_palabras: Maximo de palabras

        Returns:
            Resumen breve o None
        """
        try:
            llm = self._get_llm()

            if not llm.is_available():
                return None

            # Usar texto extraido si disponible
            contenido = texto_extraido[:2000] if texto_extraido else detalle

            prompt = f"""Resume en maximo {max_palabras} palabras esta actuacion judicial:

Tipo: {tipo}
Contenido: {contenido}

Resumen:"""

            system = "Eres un asistente juridico. Resume de forma concisa y profesional."

            resumen = llm.generate(
                prompt=prompt,
                system=system,
                temperature=0.2,
                max_tokens=150
            )

            return resumen.strip()

        except Exception as e:
            logger.warning(f"Error resumiendo actuacion: {e}")
            return None

    def is_available(self) -> bool:
        """Verifica si el servicio esta disponible."""
        try:
            return self._get_llm().is_available()
        except Exception:
            return False


# Singleton para reutilizar instancia
_resumen_service: Optional[ResumenService] = None


def get_resumen_service() -> ResumenService:
    """Obtiene instancia singleton del servicio de resumen."""
    global _resumen_service
    if _resumen_service is None:
        _resumen_service = ResumenService()
    return _resumen_service
