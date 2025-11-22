"""
Integración de procesador_pdf en el Generador de Documentos.

Este módulo proporciona utilidades para filtrar contenido jurídico
basándose en la clasificación de utilidad de procesador_pdf.

Funcionalidades principales:
- Filtrado de actuaciones por nivel de utilidad
- Generación de contexto optimizado para LLMs
- Reducción de ruido en documentos generados
- Priorización de contenido relevante

Autor: Sistema SintaXis
Fecha: 2025-11-03
Tarea: 6 - Integración Generador de Documentos
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Dict, Optional, Literal
from pathlib import Path

# Importar procesador_pdf (opcional)
try:
    from core.procesador_pdf import (
        ClasificadorActuaciones,
        AnalizadorVencimientos,
        UtilidadJuridica
    )
    PROCESADOR_DISPONIBLE = True
except ImportError:
    PROCESADOR_DISPONIBLE = False
    logging.warning(
        "procesador_pdf no disponible. Filtrado inteligente no estará disponible."
    )


logger = logging.getLogger(__name__)


# Tipos literales para niveles de utilidad
NivelUtilidad = Literal["ALTA", "MEDIA", "BAJA", "NULA"]


@dataclass
class ActuacionFiltrada:
    """
    Representa una actuación filtrada con su clasificación.

    Attributes:
        fecha: Fecha de la actuación
        tipo: Tipo de actuación
        detalle: Detalle completo
        utilidad: Nivel de utilidad (ALTA, MEDIA, BAJA, NULA)
        score: Confianza de clasificación (0-100)
        motivo: Explicación de la clasificación
        tiene_plazo: Si tiene plazo procesal probable
        texto_completo: Texto extraído (si existe)
        prioridad: Prioridad calculada (0-100)
    """
    fecha: str
    tipo: str
    detalle: str
    utilidad: NivelUtilidad
    score: float
    motivo: str
    tiene_plazo: bool
    texto_completo: Optional[str] = None
    prioridad: int = 0


class FiltroContenidoInteligente:
    """
    Filtra contenido jurídico usando procesador_pdf para generar documentos.

    Esta clase permite filtrar actuaciones de un expediente basándose en
    su utilidad jurídica, reduciendo el ruido y mejorando la calidad de
    los documentos generados por LLMs.

    Example:
        >>> filtro = FiltroContenidoInteligente(min_utilidad="MEDIA")
        >>> actuaciones_filtradas = filtro.filtrar_actuaciones(actuaciones)
        >>> contexto = filtro.generar_contexto_para_llm(actuaciones_filtradas)
        >>> documento = llm.generar(contexto)
    """

    def __init__(
        self,
        min_utilidad: NivelUtilidad = "MEDIA",
        incluir_vencimientos: bool = True,
        ordenar_por_prioridad: bool = True
    ):
        """
        Inicializa el filtro de contenido.

        Args:
            min_utilidad: Nivel mínimo de utilidad a incluir
                         "ALTA" = Solo utilidad ALTA
                         "MEDIA" = ALTA y MEDIA
                         "BAJA" = ALTA, MEDIA y BAJA
                         "NULA" = Todas (sin filtrar)
            incluir_vencimientos: Si analizar y destacar vencimientos
            ordenar_por_prioridad: Si ordenar por prioridad calculada

        Raises:
            ImportError: Si procesador_pdf no está disponible
        """
        if not PROCESADOR_DISPONIBLE:
            raise ImportError(
                "procesador_pdf no disponible. Instala las dependencias necesarias."
            )

        self.min_utilidad = min_utilidad
        self.incluir_vencimientos = incluir_vencimientos
        self.ordenar_por_prioridad = ordenar_por_prioridad

        # Inicializar componentes
        self.clasificador = ClasificadorActuaciones()

        if incluir_vencimientos:
            self.analizador_vencimientos = AnalizadorVencimientos()
        else:
            self.analizador_vencimientos = None

        # Mapping de niveles de utilidad
        self.nivel_orden = {
            "ALTA": 4,
            "MEDIA": 3,
            "BAJA": 2,
            "NULA": 1
        }

        logger.info(
            f"FiltroContenidoInteligente inicializado: min_utilidad={min_utilidad}"
        )

    def filtrar_actuaciones(
        self,
        actuaciones: List[Dict],
        incluir_estadisticas: bool = False
    ) -> List[ActuacionFiltrada] | Dict:
        """
        Filtra actuaciones por nivel de utilidad.

        Args:
            actuaciones: Lista de actuaciones con estructura:
                {
                    "Fecha": "DD/MM/YYYY",
                    "Tipo": "...",
                    "Detalle": "...",
                    "TieneArchivo": bool,
                    "TextoExtraido": str (opcional)
                }
            incluir_estadisticas: Si retornar estadísticas de filtrado

        Returns:
            Si incluir_estadisticas=False: Lista de ActuacionFiltrada
            Si incluir_estadisticas=True: Dict con actuaciones y estadísticas
        """
        if not actuaciones:
            logger.warning("No hay actuaciones para filtrar")
            return [] if not incluir_estadisticas else {
                "actuaciones": [],
                "estadisticas": self._estadisticas_vacias()
            }

        logger.info(f"Filtrando {len(actuaciones)} actuaciones con nivel mínimo: {self.min_utilidad}")

        actuaciones_filtradas = []
        estadisticas = {
            "total": len(actuaciones),
            "filtradas": 0,
            "por_utilidad": {"ALTA": 0, "MEDIA": 0, "BAJA": 0, "NULA": 0},
            "con_vencimientos": 0,
            "vencimientos_urgentes": 0
        }

        for actuacion in actuaciones:
            # Clasificar actuación
            clasificacion = self.clasificador.clasificar(
                tipo=actuacion.get("Tipo", ""),
                detalle=actuacion.get("Detalle", ""),
                tiene_archivo=actuacion.get("TieneArchivo", False),
                texto_completo=actuacion.get("TextoExtraido", "")
            )

            utilidad_str = clasificacion.utilidad.value
            estadisticas["por_utilidad"][utilidad_str] += 1

            # Verificar si cumple filtro mínimo
            if not self._cumple_filtro(clasificacion.utilidad):
                continue

            # Analizar vencimiento si está habilitado
            tiene_vencimiento = False
            if self.incluir_vencimientos:
                vencimiento = self.analizador_vencimientos.analizar_actuacion(actuacion)
                if vencimiento and vencimiento.fecha_vencimiento:
                    tiene_vencimiento = True
                    estadisticas["con_vencimientos"] += 1
                    if vencimiento.dias_restantes <= 7:
                        estadisticas["vencimientos_urgentes"] += 1

            # Calcular prioridad
            prioridad = self._calcular_prioridad(
                clasificacion,
                tiene_vencimiento
            )

            # Crear actuación filtrada
            actuacion_filtrada = ActuacionFiltrada(
                fecha=actuacion.get("Fecha", ""),
                tipo=actuacion.get("Tipo", ""),
                detalle=actuacion.get("Detalle", ""),
                utilidad=utilidad_str,
                score=clasificacion.score_confianza,
                motivo=clasificacion.motivo_clasificacion,
                tiene_plazo=clasificacion.tiene_plazo_probable or tiene_vencimiento,
                texto_completo=actuacion.get("TextoExtraido"),
                prioridad=prioridad
            )

            actuaciones_filtradas.append(actuacion_filtrada)
            estadisticas["filtradas"] += 1

        # Ordenar por prioridad si está habilitado
        if self.ordenar_por_prioridad:
            actuaciones_filtradas.sort(key=lambda x: x.prioridad, reverse=True)

        logger.info(
            f"Filtrado completado: {estadisticas['filtradas']}/{estadisticas['total']} actuaciones incluidas"
        )

        if incluir_estadisticas:
            return {
                "actuaciones": actuaciones_filtradas,
                "estadisticas": estadisticas
            }

        return actuaciones_filtradas

    def generar_contexto_para_llm(
        self,
        actuaciones_filtradas: List[ActuacionFiltrada],
        formato: Literal["texto", "json", "markdown"] = "markdown",
        max_caracteres: Optional[int] = None
    ) -> str:
        """
        Genera contexto optimizado para LLM a partir de actuaciones filtradas.

        Args:
            actuaciones_filtradas: Lista de ActuacionFiltrada
            formato: Formato del contexto ("texto", "json", "markdown")
            max_caracteres: Límite de caracteres (None = sin límite)

        Returns:
            String con el contexto formateado
        """
        if not actuaciones_filtradas:
            return ""

        if formato == "markdown":
            return self._generar_markdown(actuaciones_filtradas, max_caracteres)
        elif formato == "json":
            return self._generar_json(actuaciones_filtradas)
        else:  # texto
            return self._generar_texto(actuaciones_filtradas, max_caracteres)

    def _cumple_filtro(self, utilidad: UtilidadJuridica) -> bool:
        """Verifica si una utilidad cumple el filtro mínimo."""
        nivel_minimo = self.nivel_orden[self.min_utilidad]
        nivel_actual = self.nivel_orden[utilidad.value]
        return nivel_actual >= nivel_minimo

    def _calcular_prioridad(
        self,
        clasificacion,
        tiene_vencimiento: bool
    ) -> int:
        """
        Calcula prioridad de una actuación (0-100).

        Factores:
        - Utilidad (40 puntos): ALTA=40, MEDIA=25, BAJA=10, NULA=0
        - Score de confianza (30 puntos): score_confianza * 0.3
        - Vencimiento (30 puntos): tiene_vencimiento=30, no=0
        """
        # Utilidad base
        utilidad_puntos = {
            "ALTA": 40,
            "MEDIA": 25,
            "BAJA": 10,
            "NULA": 0
        }
        puntos = utilidad_puntos[clasificacion.utilidad.value]

        # Score de confianza
        puntos += int(clasificacion.score_confianza * 0.3)

        # Vencimiento
        if tiene_vencimiento:
            puntos += 30

        return min(puntos, 100)

    def _generar_markdown(
        self,
        actuaciones: List[ActuacionFiltrada],
        max_caracteres: Optional[int]
    ) -> str:
        """Genera contexto en formato Markdown."""
        lineas = ["# Actuaciones Relevantes del Expediente\n"]

        for i, act in enumerate(actuaciones, 1):
            # Header de actuación
            urgente = "⚠️ URGENTE " if act.tiene_plazo else ""
            utilidad_emoji = {
                "ALTA": "🔴",
                "MEDIA": "🟡",
                "BAJA": "🟢",
                "NULA": "⚪"
            }
            emoji = utilidad_emoji.get(act.utilidad, "")

            lineas.append(f"\n## {i}. {urgente}{emoji} {act.tipo}")
            lineas.append(f"**Fecha:** {act.fecha}  ")
            lineas.append(f"**Utilidad:** {act.utilidad} (Confianza: {act.score:.1f}%)  ")
            lineas.append(f"**Detalle:** {act.detalle}\n")

            if act.texto_completo:
                lineas.append(f"**Contenido:**\n```\n{act.texto_completo[:500]}...\n```\n")

        contexto = "\n".join(lineas)

        if max_caracteres and len(contexto) > max_caracteres:
            contexto = contexto[:max_caracteres] + "\n\n[... contexto truncado ...]"

        return contexto

    def _generar_texto(
        self,
        actuaciones: List[ActuacionFiltrada],
        max_caracteres: Optional[int]
    ) -> str:
        """Genera contexto en formato texto plano."""
        lineas = ["ACTUACIONES RELEVANTES DEL EXPEDIENTE\n" + "=" * 50 + "\n"]

        for i, act in enumerate(actuaciones, 1):
            urgente = "[URGENTE] " if act.tiene_plazo else ""
            lineas.append(f"\n{i}. {urgente}{act.tipo}")
            lineas.append(f"   Fecha: {act.fecha}")
            lineas.append(f"   Utilidad: {act.utilidad}")
            lineas.append(f"   Detalle: {act.detalle}")

            if act.texto_completo:
                lineas.append(f"   Contenido: {act.texto_completo[:300]}...")

        contexto = "\n".join(lineas)

        if max_caracteres and len(contexto) > max_caracteres:
            contexto = contexto[:max_caracteres] + "\n[... truncado ...]"

        return contexto

    def _generar_json(self, actuaciones: List[ActuacionFiltrada]) -> str:
        """Genera contexto en formato JSON."""
        import json

        data = []
        for act in actuaciones:
            data.append({
                "fecha": act.fecha,
                "tipo": act.tipo,
                "detalle": act.detalle,
                "utilidad": act.utilidad,
                "score": act.score,
                "tiene_plazo": act.tiene_plazo,
                "prioridad": act.prioridad
            })

        return json.dumps(data, indent=2, ensure_ascii=False)

    def _estadisticas_vacias(self) -> Dict:
        """Retorna estadísticas vacías."""
        return {
            "total": 0,
            "filtradas": 0,
            "por_utilidad": {"ALTA": 0, "MEDIA": 0, "BAJA": 0, "NULA": 0},
            "con_vencimientos": 0,
            "vencimientos_urgentes": 0
        }


# Función auxiliar para uso directo
def generar_contexto_filtrado(
    actuaciones: List[Dict],
    min_utilidad: NivelUtilidad = "MEDIA",
    formato: Literal["texto", "json", "markdown"] = "markdown",
    max_caracteres: Optional[int] = None
) -> str:
    """
    Función auxiliar para generar contexto filtrado en un solo paso.

    Args:
        actuaciones: Lista de actuaciones a filtrar
        min_utilidad: Nivel mínimo de utilidad
        formato: Formato del contexto
        max_caracteres: Límite de caracteres

    Returns:
        String con contexto filtrado y formateado

    Example:
        >>> contexto = generar_contexto_filtrado(
        ...     actuaciones,
        ...     min_utilidad="MEDIA",
        ...     formato="markdown"
        ... )
        >>> documento = llm.generar(contexto)
    """
    if not PROCESADOR_DISPONIBLE:
        raise ImportError("procesador_pdf no disponible")

    filtro = FiltroContenidoInteligente(min_utilidad=min_utilidad)
    actuaciones_filtradas = filtro.filtrar_actuaciones(actuaciones)
    return filtro.generar_contexto_para_llm(
        actuaciones_filtradas,
        formato=formato,
        max_caracteres=max_caracteres
    )
