"""Filtrado avanzado de expedientes.

Este módulo provee la clase FiltradorExpedientes que permite aplicar
múltiples filtros combinables sobre un listado de expedientes extraídos.
Soporta filtrado por fecha de última actuación, situación procesal,
dependencia y rango de fechas de inicio.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Sequence

from ..pjn.models.expediente import ExpedienteResumen


class FiltradorExpedientes:
    """Aplica filtros complejos sobre listados de expedientes.

    Implementa el patrón fluent interface para encadenar múltiples filtros.
    Cada método de filtrado retorna la propia instancia permitiendo:

    >>> filtrador = FiltradorExpedientes(expedientes)
    >>> resultado = filtrador.filtrar_por_situacion(["En trámite"]) \\
    ...                      .filtrar_por_dias_atras(30) \\
    ...                      .obtener_resultados()

    Attributes:
        expedientes_originales: Listado completo sin filtrar (inmutable)
        expedientes_filtrados: Resultado actual tras aplicar filtros
        filtros_aplicados: Registro de filtros aplicados para trazabilidad
    """

    def __init__(self, expedientes: Sequence[ExpedienteResumen]):
        """Inicializa el filtrador con un listado de expedientes.

        Args:
            expedientes: Secuencia de expedientes a filtrar (se copia)
        """
        self.expedientes_originales = list(expedientes)
        self.expedientes_filtrados = list(expedientes)
        self.filtros_aplicados: list[dict[str, object]] = []

    def filtrar_por_dias_atras(
        self,
        dias: int,
        *,
        campo_fecha: str = "ultima_actuacion",
    ) -> "FiltradorExpedientes":
        """Filtra expedientes con actividad en los últimos N días.

        Args:
            dias: Número de días hacia atrás desde hoy
            campo_fecha: Campo del modelo a utilizar (default: ultima_actuacion)

        Returns:
            Self para encadenamiento fluent

        Example:
            >>> filtrador.filtrar_por_dias_atras(30)  # Últimos 30 días
        """
        if dias <= 0:
            return self

        fecha_corte = datetime.now().date() - timedelta(days=dias)

        def tiene_actividad_reciente(exp: ExpedienteResumen) -> bool:
            fecha_str = getattr(exp, campo_fecha, None)
            if not fecha_str:
                return False

            try:
                # Soporta formatos: YYYY-MM-DD, DD/MM/YYYY
                if "/" in fecha_str:
                    fecha = datetime.strptime(fecha_str, "%d/%m/%Y").date()
                else:
                    fecha = datetime.fromisoformat(fecha_str).date()
                return fecha >= fecha_corte
            except (ValueError, AttributeError):
                return False

        self.expedientes_filtrados = [
            exp for exp in self.expedientes_filtrados
            if tiene_actividad_reciente(exp)
        ]

        self.filtros_aplicados.append({
            "tipo": "dias_atras",
            "dias": dias,
            "fecha_corte": fecha_corte.isoformat(),
            "campo": campo_fecha,
            "resultados": len(self.expedientes_filtrados),
        })

        return self

    def filtrar_por_situacion(
        self,
        situaciones: Sequence[str],
        *,
        case_sensitive: bool = False,
    ) -> "FiltradorExpedientes":
        """Filtra expedientes por situación procesal.

        Args:
            situaciones: Lista de situaciones a incluir (ej: ["En trámite", "Archivado"])
            case_sensitive: Si True, comparación sensible a mayúsculas/minúsculas

        Returns:
            Self para encadenamiento fluent

        Example:
            >>> filtrador.filtrar_por_situacion(["En trámite", "Sentenciado"])
        """
        if not situaciones:
            return self

        situaciones_set = (
            set(situaciones) if case_sensitive
            else {s.casefold() for s in situaciones}
        )

        def coincide_situacion(exp: ExpedienteResumen) -> bool:
            if not exp.situacion:
                return False

            situacion_exp = (
                exp.situacion if case_sensitive
                else exp.situacion.casefold()
            )
            return situacion_exp in situaciones_set

        self.expedientes_filtrados = [
            exp for exp in self.expedientes_filtrados
            if coincide_situacion(exp)
        ]

        self.filtros_aplicados.append({
            "tipo": "situacion",
            "situaciones": list(situaciones),
            "case_sensitive": case_sensitive,
            "resultados": len(self.expedientes_filtrados),
        })

        return self

    def filtrar_por_dependencia(
        self,
        pattern: str,
        *,
        regex: bool = False,
        case_sensitive: bool = False,
    ) -> "FiltradorExpedientes":
        """Filtra expedientes por dependencia (juzgado/fuero).

        Args:
            pattern: Patrón a buscar en el nombre de la dependencia
            regex: Si True, interpreta pattern como expresión regular
            case_sensitive: Si True, comparación sensible a mayúsculas/minúsculas

        Returns:
            Self para encadenamiento fluent

        Example:
            >>> filtrador.filtrar_por_dependencia("JUZ. CIV.", regex=False)
            >>> filtrador.filtrar_por_dependencia(r"JUZ\. CIV\. \d+", regex=True)
        """
        if not pattern:
            return self

        flags = 0 if case_sensitive else re.IGNORECASE

        if regex:
            try:
                compiled_pattern = re.compile(pattern, flags)
                matcher: Callable[[str], bool] = lambda dep: bool(compiled_pattern.search(dep))
            except re.error as e:
                raise ValueError(f"Patrón regex inválido '{pattern}': {e}") from e
        else:
            if case_sensitive:
                matcher = lambda dep: pattern in dep
            else:
                pattern_norm = pattern.casefold()
                matcher = lambda dep: pattern_norm in dep.casefold()

        self.expedientes_filtrados = [
            exp for exp in self.expedientes_filtrados
            if matcher(exp.dependencia)
        ]

        self.filtros_aplicados.append({
            "tipo": "dependencia",
            "pattern": pattern,
            "regex": regex,
            "case_sensitive": case_sensitive,
            "resultados": len(self.expedientes_filtrados),
        })

        return self

    def filtrar_por_rango_fechas(
        self,
        fecha_desde: str | None = None,
        fecha_hasta: str | None = None,
        *,
        campo_fecha: str = "fecha",
    ) -> "FiltradorExpedientes":
        """Filtra expedientes por rango de fechas de inicio.

        Args:
            fecha_desde: Fecha mínima (formato: YYYY-MM-DD o DD/MM/YYYY)
            fecha_hasta: Fecha máxima (formato: YYYY-MM-DD o DD/MM/YYYY)
            campo_fecha: Campo del modelo a utilizar

        Returns:
            Self para encadenamiento fluent

        Example:
            >>> filtrador.filtrar_por_rango_fechas("2024-01-01", "2024-12-31")
        """
        if not fecha_desde and not fecha_hasta:
            return self

        def parsear_fecha(fecha_str: str) -> datetime:
            if "/" in fecha_str:
                return datetime.strptime(fecha_str, "%d/%m/%Y")
            return datetime.fromisoformat(fecha_str)

        try:
            fecha_min = parsear_fecha(fecha_desde) if fecha_desde else datetime.min
            fecha_max = parsear_fecha(fecha_hasta) if fecha_hasta else datetime.max
        except ValueError as e:
            raise ValueError(
                f"Formato de fecha inválido (use YYYY-MM-DD o DD/MM/YYYY): {e}"
            ) from e

        def en_rango(exp: ExpedienteResumen) -> bool:
            fecha_str = getattr(exp, campo_fecha, None)
            if not fecha_str:
                return False

            try:
                fecha_exp = parsear_fecha(fecha_str)
                return fecha_min <= fecha_exp <= fecha_max
            except (ValueError, AttributeError):
                return False

        self.expedientes_filtrados = [
            exp for exp in self.expedientes_filtrados
            if en_rango(exp)
        ]

        self.filtros_aplicados.append({
            "tipo": "rango_fechas",
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta,
            "campo": campo_fecha,
            "resultados": len(self.expedientes_filtrados),
        })

        return self

    def filtrar_personalizado(
        self,
        predicado: Callable[[ExpedienteResumen], bool],
        *,
        nombre_filtro: str = "personalizado",
    ) -> "FiltradorExpedientes":
        """Aplica un filtro personalizado mediante función predicado.

        Args:
            predicado: Función que retorna True para expedientes a incluir
            nombre_filtro: Nombre descriptivo del filtro para trazabilidad

        Returns:
            Self para encadenamiento fluent

        Example:
            >>> filtrador.filtrar_personalizado(
            ...     lambda exp: "AMPARO" in exp.caratula.upper(),
            ...     nombre_filtro="contiene_amparo"
            ... )
        """
        self.expedientes_filtrados = [
            exp for exp in self.expedientes_filtrados
            if predicado(exp)
        ]

        self.filtros_aplicados.append({
            "tipo": "personalizado",
            "nombre": nombre_filtro,
            "resultados": len(self.expedientes_filtrados),
        })

        return self

    def obtener_resultados(self) -> list[ExpedienteResumen]:
        """Retorna el listado actual tras aplicar todos los filtros.

        Returns:
            Lista de expedientes que pasaron todos los filtros
        """
        return list(self.expedientes_filtrados)

    def obtener_estadisticas(self) -> dict[str, object]:
        """Retorna estadísticas del proceso de filtrado.

        Returns:
            Diccionario con: total_original, total_filtrado, filtros_aplicados,
            porcentaje_retenido
        """
        total_original = len(self.expedientes_originales)
        total_filtrado = len(self.expedientes_filtrados)

        return {
            "total_original": total_original,
            "total_filtrado": total_filtrado,
            "filtros_aplicados": len(self.filtros_aplicados),
            "porcentaje_retenido": (
                (total_filtrado / total_original * 100) if total_original > 0 else 0
            ),
            "detalles_filtros": list(self.filtros_aplicados),
        }

    def resetear(self) -> "FiltradorExpedientes":
        """Elimina todos los filtros aplicados y restaura el listado original.

        Returns:
            Self para encadenamiento fluent
        """
        self.expedientes_filtrados = list(self.expedientes_originales)
        self.filtros_aplicados.clear()
        return self


__all__ = ["FiltradorExpedientes"]
