"""Objetos de configuración para extracción de expedientes - Sprint 2, Tarea 2.3.

Este módulo define objetos de configuración que agrupan parámetros relacionados
para simplificar las firmas de funciones y mejorar la mantenibilidad.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, TypeVar

if TYPE_CHECKING:
    from pjn.models.expediente import ExpedienteResumen
    from pjn.scraping.pagination import PaginationStrategy

TResumen = TypeVar("TResumen")


@dataclass
class ExtraccionExpedientesConfig:
    """Configuración para extracción de expedientes.

    Agrupa todos los parámetros de configuración de `extraer_expedientes_completos()`
    en un objeto cohesivo y validado, simplificando la firma de la función.

    Attributes:
        sel_tabla: Selector de la tabla principal.
        sel_tbody: Selector del tbody de la tabla.
        sel_siguiente: Selector del botón "Siguiente".
        max_paginas: Límite máximo de páginas a extraer.
        omitir_duplicados: Si omitir expedientes duplicados.
        detener_en_duplicado: Si detener al encontrar duplicado.
        fecha_corte: Fecha de corte para filtrar expedientes.
        tiempo_maximo_segundos: Tiempo máximo de extracción en segundos.
        orden: Criterio de ordenamiento (fecha, caratula, oficina, situacion).
        mapper: Función para mapear ExpedienteResumen a otro tipo.
        pagination_strategy: Estrategia de paginación personalizada.

    Example:
        >>> # Configuración básica
        >>> config = ExtraccionExpedientesConfig(max_paginas=10)
        >>> expedientes, motivo, meta = await extraer_expedientes_completos(page, config)

        >>> # Configuración con fecha de corte
        >>> config = ExtraccionExpedientesConfig(
        ...     max_paginas=50,
        ...     fecha_corte="2025-01-01",
        ...     orden="fecha"
        ... )

        >>> # Usando presets
        >>> config = ExtraccionExpedientesConfig.rapido()
        >>> config = ExtraccionExpedientesConfig.completo()
    """

    # Selectores
    sel_tabla: str = "table.table-striped"
    sel_tbody: str = ""  # Se calcula en __post_init__
    sel_siguiente: str = (
        "a.ui-paginator-next:not(.ui-state-disabled), "
        "a[aria-label='Siguiente']:not(.ui-state-disabled)"
    )

    # Límites
    max_paginas: int | None = None
    tiempo_maximo_segundos: int | None = None

    # Filtros
    fecha_corte: str | None = None
    omitir_duplicados: bool = True
    detener_en_duplicado: bool = True

    # Ordenamiento
    orden: str | None = None

    # Estrategias avanzadas
    mapper: Callable[[ExpedienteResumen], TResumen] | None = None  # type: ignore[valid-type]
    pagination_strategy: PaginationStrategy | None = None  # type: ignore[valid-type]

    def __post_init__(self) -> None:
        """Valida y normaliza la configuración después de la inicialización."""
        # Calcular sel_tbody si no se especificó
        if not self.sel_tbody:
            self.sel_tbody = f"{self.sel_tabla} tbody"

        # Validar orden si se especificó
        if self.orden:
            self._validar_orden()

    def _validar_orden(self) -> None:
        """Valida que el criterio de ordenamiento sea válido.

        Raises:
            ValueError: Si el criterio de orden no es válido.
        """
        validos = {"fecha", "caratula", "oficina", "situacion"}
        if self.orden and self.orden.lower() not in validos:
            raise ValueError(
                f"Criterio de orden inválido: '{self.orden}'. "
                f"Debe ser uno de: {', '.join(sorted(validos))}"
            )

    @classmethod
    def rapido(cls, max_paginas: int = 5) -> ExtraccionExpedientesConfig:
        """Configuración para extracción rápida (testing/desarrollo).

        Args:
            max_paginas: Número máximo de páginas (default: 5).

        Returns:
            Configuración optimizada para extracción rápida.

        Example:
            >>> config = ExtraccionExpedientesConfig.rapido()
            >>> config.max_paginas
            5
            >>> config.tiempo_maximo_segundos
            60
        """
        return cls(
            max_paginas=max_paginas,
            tiempo_maximo_segundos=60,
            omitir_duplicados=True,
            detener_en_duplicado=True,
        )

    @classmethod
    def completo(cls) -> ExtraccionExpedientesConfig:
        """Configuración para extracción completa (producción).

        Returns:
            Configuración sin límites para extracción completa.

        Example:
            >>> config = ExtraccionExpedientesConfig.completo()
            >>> config.max_paginas is None
            True
            >>> config.detener_en_duplicado
            False
        """
        return cls(
            max_paginas=None,
            tiempo_maximo_segundos=None,
            omitir_duplicados=True,
            detener_en_duplicado=False,  # No detener, extraer todo
        )

    @classmethod
    def con_fecha_corte(cls, fecha_corte: str, max_paginas: int = 100) -> ExtraccionExpedientesConfig:
        """Configuración con fecha de corte específica.

        Args:
            fecha_corte: Fecha de corte en formato YYYY-MM-DD o DD/MM/YYYY.
            max_paginas: Número máximo de páginas (default: 100).

        Returns:
            Configuración con fecha de corte configurada.

        Example:
            >>> config = ExtraccionExpedientesConfig.con_fecha_corte("2025-01-01")
            >>> config.fecha_corte
            '2025-01-01'
        """
        return cls(
            max_paginas=max_paginas,
            fecha_corte=fecha_corte,
            omitir_duplicados=True,
            detener_en_duplicado=True,
        )

    def to_dict(self) -> dict:
        """Convierte la configuración a diccionario.

        Returns:
            Diccionario con todos los parámetros de configuración.
        """
        return {
            "sel_tabla": self.sel_tabla,
            "sel_tbody": self.sel_tbody,
            "sel_siguiente": self.sel_siguiente,
            "max_paginas": self.max_paginas,
            "tiempo_maximo_segundos": self.tiempo_maximo_segundos,
            "fecha_corte": self.fecha_corte,
            "omitir_duplicados": self.omitir_duplicados,
            "detener_en_duplicado": self.detener_en_duplicado,
            "orden": self.orden,
            "mapper": self.mapper,
            "pagination_strategy": self.pagination_strategy,
        }
