"""Configuraciones compartidas para componentes de monitoreo PJN."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .validators import (
    validar_directorio,
    validar_dias_laborales,
    validar_formato_fecha,
    validar_formato_hora,
    validar_intervalo,
    validar_max_reintentos,
    validar_rango_fechas,
    validar_rango_horas,
    validar_tipos_entradas,
)

ModoMonitor = Literal["automatico", "laboral", "no_laboral"]


@dataclass
class MonitorSharedConfig:
    """Campos y validaciones comunes para configuraciones de monitoreo."""

    modo_monitor: ModoMonitor = "automatico"
    headless: bool = True
    directorio_monitor_datos: str = "data/monitor"

    intervalos_laboral_expedientes: int = 15
    intervalos_laboral_entradas: int = 10
    intervalos_no_laboral_expedientes: int = 60
    intervalos_no_laboral_entradas: int = 30

    dias_laborales: list[str] = field(
        default_factory=lambda: [
            "lunes",
            "martes",
            "miercoles",
            "jueves",
            "viernes",
        ]
    )
    hora_inicio: str = "08:00"
    hora_fin: str = "18:00"

    max_reintentos_expedientes: int = 3
    espera_reintentos_expedientes: int = 30
    max_reintentos_entradas: int = 3
    espera_reintentos_entradas: int = 30

    notificar_nuevas_entradas: bool = True
    notificar_cambios_expedientes: bool = True
    notificar_errores: bool = True

    verificar_entradas: bool = True
    verificar_expedientes: bool = True
    tipos_entradas: tuple[str, ...] = ("N",)

    comparacion_automatica: bool = False
    fecha_corte_expedientes: str | None = None

    fecha_desde_entradas: str | None = None
    fecha_hasta_entradas: str | None = None
    fecha_desde_expedientes: str | None = None
    fecha_hasta_expedientes: str | None = None

    # Nuevos campos - días hacia atrás
    dias_atras_entradas: int | None = None
    dias_atras_expedientes: int | None = None

    # Nuevos campos - configuración avanzada de expedientes
    extraccion_expedientes_completa: bool = False
    expedientes_orden: str | None = None  # fecha, caratula, oficina, situacion
    expedientes_detener_duplicados: bool = True
    expedientes_max_paginas: int | None = None

    def __post_init__(self) -> None:
        """Ejecuta las validaciones comunes para el monitoreo."""

        self.directorio_monitor_datos = validar_directorio(
            self.directorio_monitor_datos, "directorio_monitor_datos"
        )

        for campo_intervalo in (
            "intervalos_laboral_expedientes",
            "intervalos_laboral_entradas",
            "intervalos_no_laboral_expedientes",
            "intervalos_no_laboral_entradas",
        ):
            valor = getattr(self, campo_intervalo)
            validar_intervalo(
                valor * 60,
                campo_intervalo,
                min_val=60,
                max_val=1440 * 60,
            )

        validar_intervalo(
            self.espera_reintentos_expedientes,
            "espera_reintentos_expedientes",
            min_val=1,
            max_val=300,
        )
        validar_intervalo(
            self.espera_reintentos_entradas,
            "espera_reintentos_entradas",
            min_val=1,
            max_val=300,
        )

        validar_max_reintentos(
            self.max_reintentos_expedientes, "max_reintentos_expedientes"
        )
        validar_max_reintentos(
            self.max_reintentos_entradas, "max_reintentos_entradas"
        )

        validar_dias_laborales(self.dias_laborales, "dias_laborales")

        validar_formato_hora(self.hora_inicio, "hora_inicio")
        validar_formato_hora(self.hora_fin, "hora_fin")
        validar_rango_horas(self.hora_inicio, self.hora_fin)

        validar_formato_fecha(
            self.fecha_desde_entradas, "fecha_desde_entradas"
        )
        validar_formato_fecha(
            self.fecha_hasta_entradas, "fecha_hasta_entradas"
        )
        validar_rango_fechas(
            self.fecha_desde_entradas,
            self.fecha_hasta_entradas,
            "fecha_desde_entradas",
            "fecha_hasta_entradas",
        )

        validar_formato_fecha(
            self.fecha_desde_expedientes, "fecha_desde_expedientes"
        )
        validar_formato_fecha(
            self.fecha_hasta_expedientes, "fecha_hasta_expedientes"
        )
        validar_rango_fechas(
            self.fecha_desde_expedientes,
            self.fecha_hasta_expedientes,
            "fecha_desde_expedientes",
            "fecha_hasta_expedientes",
        )

        validar_formato_fecha(
            self.fecha_corte_expedientes, "fecha_corte_expedientes"
        )

        self.tipos_entradas = validar_tipos_entradas(self.tipos_entradas)

        # Validar días hacia atrás
        if self.dias_atras_entradas is not None:
            if not isinstance(self.dias_atras_entradas, int) or self.dias_atras_entradas < 1:
                raise ValueError(
                    f"dias_atras_entradas debe ser un entero positivo, "
                    f"recibido: {self.dias_atras_entradas}"
                )
            if self.dias_atras_entradas > 365:
                raise ValueError(
                    f"dias_atras_entradas no puede exceder 365 días, "
                    f"recibido: {self.dias_atras_entradas}"
                )

        if self.dias_atras_expedientes is not None:
            if not isinstance(self.dias_atras_expedientes, int) or self.dias_atras_expedientes < 1:
                raise ValueError(
                    f"dias_atras_expedientes debe ser un entero positivo, "
                    f"recibido: {self.dias_atras_expedientes}"
                )
            if self.dias_atras_expedientes > 365:
                raise ValueError(
                    f"dias_atras_expedientes no puede exceder 365 días, "
                    f"recibido: {self.dias_atras_expedientes}"
                )

        # Validar criterio de orden de expedientes
        if self.expedientes_orden:
            validos = {"fecha", "caratula", "oficina", "situacion"}
            if self.expedientes_orden.lower() not in validos:
                raise ValueError(
                    f"expedientes_orden inválido: '{self.expedientes_orden}'. "
                    f"Debe ser uno de: {', '.join(sorted(validos))}"
                )

        # Validar max_paginas de expedientes
        if self.expedientes_max_paginas is not None:
            if not isinstance(self.expedientes_max_paginas, int) or self.expedientes_max_paginas < 1:
                raise ValueError(
                    f"expedientes_max_paginas debe ser un entero positivo, "
                    f"recibido: {self.expedientes_max_paginas}"
                )


__all__ = ["ModoMonitor", "MonitorSharedConfig"]
