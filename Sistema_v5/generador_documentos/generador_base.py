"""
Generador de Documentos Jurídicos Base.

Este módulo proporciona una clase base para generadores de documentos que
utiliza la integración con procesador_pdf para filtrar contenido relevante.

Ejemplo de implementación que muestra cómo usar el filtrado inteligente para
generar documentos de mejor calidad.

Autor: Sistema SintaXis
Fecha: 2025-11-03
Tarea: 6 - Integración Generador de Documentos
"""

from __future__ import annotations

import logging
from typing import List, Dict, Optional
from pathlib import Path

try:
    from Sistema_v5.generador_documentos.integracion_procesador import (
        FiltroContenidoInteligente,
        generar_contexto_filtrado,
        PROCESADOR_DISPONIBLE
    )
except ImportError:
    PROCESADOR_DISPONIBLE = False
    logging.warning("Integración con procesador_pdf no disponible")


logger = logging.getLogger(__name__)


class GeneradorDocumentosBase:
    """
    Clase base para generadores de documentos jurídicos.

    Proporciona funcionalidades básicas de filtrado de contenido usando
    procesador_pdf para mejorar la calidad de los documentos generados.

    Esta es una clase de ejemplo que muestra cómo integrar el filtrado
    inteligente en un generador de documentos.

    Example:
        >>> generador = GeneradorDocumentosBase()
        >>> contexto = generador.preparar_contexto(actuaciones, min_utilidad="ALTA")
        >>> # Usar contexto con LLM para generar documento
        >>> documento = llm.generar(contexto)
    """

    def __init__(self, usar_filtrado: bool = True):
        """
        Inicializa el generador.

        Args:
            usar_filtrado: Si usar filtrado inteligente con procesador_pdf

        Raises:
            ImportError: Si usar_filtrado=True pero procesador_pdf no está disponible
        """
        self.usar_filtrado = usar_filtrado

        if usar_filtrado and not PROCESADOR_DISPONIBLE:
            raise ImportError(
                "Filtrado inteligente solicitado pero procesador_pdf no disponible"
            )

        if usar_filtrado:
            logger.info("GeneradorDocumentosBase inicializado con filtrado inteligente")
        else:
            logger.info("GeneradorDocumentosBase inicializado SIN filtrado")

    def preparar_contexto(
        self,
        actuaciones: List[Dict],
        min_utilidad: str = "MEDIA",
        max_caracteres: Optional[int] = None,
        formato: str = "markdown"
    ) -> str:
        """
        Prepara contexto para generación de documentos.

        Args:
            actuaciones: Lista de actuaciones del expediente
            min_utilidad: Nivel mínimo de utilidad ("ALTA", "MEDIA", "BAJA", "NULA")
            max_caracteres: Límite de caracteres para el contexto
            formato: Formato del contexto ("markdown", "texto", "json")

        Returns:
            String con el contexto preparado

        Example:
            >>> contexto = generador.preparar_contexto(
            ...     actuaciones,
            ...     min_utilidad="ALTA",
            ...     max_caracteres=5000
            ... )
        """
        if not self.usar_filtrado:
            # Sin filtrado, usar todas las actuaciones
            return self._generar_contexto_simple(actuaciones, formato, max_caracteres)

        # Con filtrado inteligente
        logger.info(f"Preparando contexto con filtrado (min_utilidad={min_utilidad})")

        contexto = generar_contexto_filtrado(
            actuaciones,
            min_utilidad=min_utilidad,
            formato=formato,
            max_caracteres=max_caracteres
        )

        logger.info(f"Contexto generado: {len(contexto)} caracteres")
        return contexto

    def generar_recurso_apelacion(
        self,
        expediente_datos: Dict,
        actuaciones: List[Dict],
        resolucion_apelada: Dict,
        usar_solo_relevantes: bool = True
    ) -> str:
        """
        Genera un recurso de apelación.

        Este es un ejemplo de generador específico que muestra cómo usar
        el filtrado para crear documentos de mejor calidad.

        Args:
            expediente_datos: Datos del expediente
            actuaciones: Lista de actuaciones
            resolucion_apelada: Datos de la resolución a apelar
            usar_solo_relevantes: Si filtrar solo actuaciones relevantes

        Returns:
            String con el recurso generado (contexto preparado para LLM)

        Example:
            >>> recurso = generador.generar_recurso_apelacion(
            ...     expediente_datos,
            ...     actuaciones,
            ...     resolucion_apelada,
            ...     usar_solo_relevantes=True
            ... )
        """
        logger.info(f"Generando recurso de apelación para expediente {expediente_datos.get('numero')}")

        # Preparar contexto filtrado
        if usar_solo_relevantes and self.usar_filtrado:
            # Usar solo actuaciones de utilidad ALTA o MEDIA
            contexto_actuaciones = self.preparar_contexto(
                actuaciones,
                min_utilidad="MEDIA",
                formato="markdown"
            )
        else:
            # Usar todas las actuaciones
            contexto_actuaciones = self._generar_contexto_simple(
                actuaciones,
                "markdown",
                None
            )

        # Construir el prompt/contexto para el LLM
        contexto_completo = f"""
# Recurso de Apelación

## Datos del Expediente
**Número:** {expediente_datos.get('numero')}
**Carátula:** {expediente_datos.get('caratula')}
**Dependencia:** {expediente_datos.get('dependencia')}

## Resolución a Apelar
**Tipo:** {resolucion_apelada.get('tipo')}
**Fecha:** {resolucion_apelada.get('fecha')}
**Detalle:** {resolucion_apelada.get('detalle')}

## Actuaciones Relevantes del Expediente
{contexto_actuaciones}

---

**NOTA**: Este contexto incluye solo las actuaciones de utilidad MEDIA o ALTA,
excluyendo automáticamente proveídos de mero trámite y otras actuaciones
de baja relevancia jurídica.

**Instrucciones para el LLM**:
Genera un recurso de apelación fundamentado basándote en:
1. Las actuaciones relevantes listadas arriba
2. La resolución a apelar
3. Los fundamentos jurídicos aplicables
        """

        return contexto_completo

    def generar_memorial_demanda(
        self,
        datos_demanda: Dict,
        hechos: List[str],
        fundamentos_derecho: List[str],
        usar_filtrado: bool = True
    ) -> str:
        """
        Genera un memorial de demanda.

        Args:
            datos_demanda: Datos básicos de la demanda
            hechos: Lista de hechos a incluir
            fundamentos_derecho: Fundamentos de derecho
            usar_filtrado: Si filtrar hechos por relevancia

        Returns:
            String con el memorial (contexto para LLM)

        Example:
            >>> memorial = generador.generar_memorial_demanda(
            ...     datos_demanda,
            ...     hechos,
            ...     fundamentos_derecho
            ... )
        """
        logger.info("Generando memorial de demanda")

        # Por ahora, retornar estructura básica
        # En implementación completa, aquí se filtraría y estructuraría el contenido

        contexto = f"""
# Memorial de Demanda

## Datos de la Demanda
**Actor:** {datos_demanda.get('actor')}
**Demandado:** {datos_demanda.get('demandado')}
**Objeto:** {datos_demanda.get('objeto')}

## Hechos
"""

        for i, hecho in enumerate(hechos, 1):
            contexto += f"{i}. {hecho}\n"

        contexto += "\n## Fundamentos de Derecho\n"

        for i, fundamento in enumerate(fundamentos_derecho, 1):
            contexto += f"{i}. {fundamento}\n"

        return contexto

    def _generar_contexto_simple(
        self,
        actuaciones: List[Dict],
        formato: str,
        max_caracteres: Optional[int]
    ) -> str:
        """
        Genera contexto sin filtrado (todas las actuaciones).

        Args:
            actuaciones: Lista de actuaciones
            formato: Formato del contexto
            max_caracteres: Límite de caracteres

        Returns:
            String con contexto sin filtrar
        """
        lineas = []

        for i, act in enumerate(actuaciones, 1):
            if formato == "markdown":
                lineas.append(f"## {i}. {act.get('Tipo')}")
                lineas.append(f"**Fecha:** {act.get('Fecha')}")
                lineas.append(f"**Detalle:** {act.get('Detalle')}\n")
            else:
                lineas.append(f"{i}. {act.get('Tipo')} - {act.get('Fecha')}")
                lineas.append(f"   {act.get('Detalle')}\n")

        contexto = "\n".join(lineas)

        if max_caracteres and len(contexto) > max_caracteres:
            contexto = contexto[:max_caracteres] + "\n[... truncado ...]"

        return contexto


# Función auxiliar para uso directo
def generar_documento_simple(
    tipo_documento: str,
    actuaciones: List[Dict],
    datos_adicionales: Optional[Dict] = None,
    min_utilidad: str = "MEDIA"
) -> str:
    """
    Función auxiliar para generar documentos de forma simple.

    Args:
        tipo_documento: Tipo de documento ("recurso_apelacion", "memorial_demanda")
        actuaciones: Lista de actuaciones
        datos_adicionales: Datos adicionales según tipo de documento
        min_utilidad: Nivel mínimo de utilidad

    Returns:
        String con el documento/contexto generado

    Example:
        >>> contexto = generar_documento_simple(
        ...     "recurso_apelacion",
        ...     actuaciones,
        ...     {"expediente": {...}, "resolucion": {...}}
        ... )
    """
    if not PROCESADOR_DISPONIBLE:
        logger.warning("procesador_pdf no disponible, generando sin filtrado")

    generador = GeneradorDocumentosBase(usar_filtrado=PROCESADOR_DISPONIBLE)

    if tipo_documento == "recurso_apelacion" and datos_adicionales:
        return generador.generar_recurso_apelacion(
            datos_adicionales.get("expediente", {}),
            actuaciones,
            datos_adicionales.get("resolucion", {}),
            usar_solo_relevantes=PROCESADOR_DISPONIBLE
        )
    elif tipo_documento == "memorial_demanda" and datos_adicionales:
        return generador.generar_memorial_demanda(
            datos_adicionales.get("demanda", {}),
            datos_adicionales.get("hechos", []),
            datos_adicionales.get("fundamentos", [])
        )
    else:
        # Contexto genérico
        return generador.preparar_contexto(
            actuaciones,
            min_utilidad=min_utilidad
        )
