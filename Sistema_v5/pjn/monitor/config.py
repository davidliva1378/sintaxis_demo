"""Configuración del sistema de monitoreo PJN.

Este módulo define la configuración completa del monitor usando dataclasses,
permitiendo carga desde archivo JSON o creación programática.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Literal

from .validators import (
    validar_intervalo,
    validar_max_reintentos,
    validar_formato_fecha,
    validar_rango_fechas,
    validar_formato_hora,
    validar_rango_horas,
    validar_dias_laborales,
    validar_directorio,
)

ModoMonitor = Literal["automatico", "laboral", "no_laboral"]


@dataclass
class MonitorConfig:
    """Configuración completa del monitor PJN.

    Attributes:
        modo: Modo de operación del monitor
            - "automatico": Alterna entre intervalos laborales y no laborales
            - "laboral": Siempre usa intervalos laborales
            - "no_laboral": Siempre usa intervalos no laborales
        headless: Si True, ejecuta el browser sin interfaz gráfica
        directorio_datos: Directorio donde se guardan los datos del monitor

        intervalos_laboral_expedientes: Intervalo en minutos para verificar
            expedientes durante horario laboral
        intervalos_laboral_entradas: Intervalo en minutos para verificar
            entradas durante horario laboral
        intervalos_no_laboral_expedientes: Intervalo en minutos para verificar
            expedientes fuera de horario laboral
        intervalos_no_laboral_entradas: Intervalo en minutos para verificar
            entradas fuera de horario laboral

        dias_laborales: Lista de días considerados laborales (ej: ["lunes", "martes"])
        hora_inicio: Hora de inicio del horario laboral (formato "HH:MM")
        hora_fin: Hora de fin del horario laboral (formato "HH:MM")

        max_reintentos_expedientes: Número máximo de reintentos al fallar verificación
        espera_reintentos_expedientes: Segundos de espera entre reintentos
        max_reintentos_entradas: Número máximo de reintentos al fallar verificación
        espera_reintentos_entradas: Segundos de espera entre reintentos

        notificar_nuevas_entradas: Si True, notifica cuando hay nuevas entradas
        notificar_cambios_expedientes: Si True, notifica cambios en expedientes
        notificar_errores: Si True, notifica errores del monitor

        comparacion_automatica: Si True, compara expedientes tras cada verificación
        fecha_corte_expedientes: Fecha de corte para extracción de expedientes (YYYY-MM-DD)
        fecha_desde_entradas: Fecha desde para filtrar entradas (YYYY-MM-DD o DD/MM/YYYY)
        fecha_hasta_entradas: Fecha hasta para filtrar entradas (YYYY-MM-DD o DD/MM/YYYY)
        fecha_desde_expedientes: Fecha desde para filtrar expedientes (YYYY-MM-DD o DD/MM/YYYY)
        fecha_hasta_expedientes: Fecha hasta para filtrar expedientes (YYYY-MM-DD o DD/MM/YYYY)
    """

    # Básico
    modo: ModoMonitor = "automatico"
    headless: bool = True
    directorio_datos: str = "data/monitor"

    # Intervalos en minutos
    intervalos_laboral_expedientes: int = 15
    intervalos_laboral_entradas: int = 10
    intervalos_no_laboral_expedientes: int = 60
    intervalos_no_laboral_entradas: int = 30

    # Horario laboral
    dias_laborales: list[str] = field(default_factory=lambda: [
        "lunes", "martes", "miercoles", "jueves", "viernes"
    ])
    hora_inicio: str = "08:00"
    hora_fin: str = "18:00"

    # Reintentos
    max_reintentos_expedientes: int = 3
    espera_reintentos_expedientes: int = 30  # segundos
    max_reintentos_entradas: int = 3
    espera_reintentos_entradas: int = 30  # segundos

    # Notificaciones
    notificar_nuevas_entradas: bool = True
    notificar_cambios_expedientes: bool = True
    notificar_errores: bool = True

    # Verificaciones (habilitar/deshabilitar)
    verificar_entradas: bool = True
    verificar_expedientes: bool = True

    # Avanzado
    comparacion_automatica: bool = False
    fecha_corte_expedientes: str | None = None

    # Filtros de rango de fechas para entradas
    fecha_desde_entradas: str | None = None  # Formato: YYYY-MM-DD o DD/MM/YYYY
    fecha_hasta_entradas: str | None = None  # Formato: YYYY-MM-DD o DD/MM/YYYY

    # Filtros de rango de fechas para expedientes
    fecha_desde_expedientes: str | None = None  # Formato: YYYY-MM-DD o DD/MM/YYYY
    fecha_hasta_expedientes: str | None = None  # Formato: YYYY-MM-DD o DD/MM/YYYY

    def __post_init__(self):
        """Valida la configuración después de la inicialización.

        Raises:
            ValidationError: Si algún parámetro es inválido
            IntervalError: Si los intervalos están fuera de rango
            DateRangeError: Si las fechas son inválidas
            WorkHoursError: Si las horas laborales son inválidas
        """
        # Validar directorio
        validar_directorio(self.directorio_datos, "directorio_datos")

        # Validar intervalos (convertir minutos a segundos para validación)
        validar_intervalo(
            self.intervalos_laboral_expedientes * 60,
            "intervalos_laboral_expedientes",
            min_val=60,  # Mínimo 1 minuto
            max_val=1440 * 60  # Máximo 24 horas
        )
        validar_intervalo(
            self.intervalos_laboral_entradas * 60,
            "intervalos_laboral_entradas",
            min_val=60,
            max_val=1440 * 60
        )
        validar_intervalo(
            self.intervalos_no_laboral_expedientes * 60,
            "intervalos_no_laboral_expedientes",
            min_val=60,
            max_val=1440 * 60
        )
        validar_intervalo(
            self.intervalos_no_laboral_entradas * 60,
            "intervalos_no_laboral_entradas",
            min_val=60,
            max_val=1440 * 60
        )

        # Validar espera de reintentos (en segundos)
        validar_intervalo(
            self.espera_reintentos_expedientes,
            "espera_reintentos_expedientes",
            min_val=1,
            max_val=300  # Máximo 5 minutos
        )
        validar_intervalo(
            self.espera_reintentos_entradas,
            "espera_reintentos_entradas",
            min_val=1,
            max_val=300
        )

        # Validar número de reintentos
        validar_max_reintentos(
            self.max_reintentos_expedientes,
            "max_reintentos_expedientes"
        )
        validar_max_reintentos(
            self.max_reintentos_entradas,
            "max_reintentos_entradas"
        )

        # Validar días laborales
        validar_dias_laborales(self.dias_laborales, "dias_laborales")

        # Validar formato de horas
        validar_formato_hora(self.hora_inicio, "hora_inicio")
        validar_formato_hora(self.hora_fin, "hora_fin")

        # Validar rango de horas
        validar_rango_horas(self.hora_inicio, self.hora_fin)

        # Validar fechas de entradas
        validar_formato_fecha(self.fecha_desde_entradas, "fecha_desde_entradas")
        validar_formato_fecha(self.fecha_hasta_entradas, "fecha_hasta_entradas")
        validar_rango_fechas(
            self.fecha_desde_entradas,
            self.fecha_hasta_entradas,
            "fecha_desde_entradas",
            "fecha_hasta_entradas"
        )

        # Validar fechas de expedientes
        validar_formato_fecha(self.fecha_desde_expedientes, "fecha_desde_expedientes")
        validar_formato_fecha(self.fecha_hasta_expedientes, "fecha_hasta_expedientes")
        validar_rango_fechas(
            self.fecha_desde_expedientes,
            self.fecha_hasta_expedientes,
            "fecha_desde_expedientes",
            "fecha_hasta_expedientes"
        )

        # Validar fecha_corte_expedientes (formato legacy)
        validar_formato_fecha(self.fecha_corte_expedientes, "fecha_corte_expedientes")

    @classmethod
    def from_file(cls, path: str | Path = "config/monitor.json") -> "MonitorConfig":
        """Carga configuración desde archivo JSON.

        Args:
            path: Ruta al archivo de configuración JSON

        Returns:
            MonitorConfig: Instancia con configuración cargada

        Raises:
            FileNotFoundError: Si el archivo no existe
            json.JSONDecodeError: Si el archivo JSON es inválido
        """
        path = Path(path)

        if not path.exists():
            # Intentar buscar desde el directorio del proyecto
            alt_path = Path(__file__).parent.parent.parent / path
            if alt_path.exists():
                path = alt_path
            else:
                # Crear configuración por defecto
                config = cls()
                config.to_file(path)
                return config

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        return cls(**data)

    @classmethod
    def from_env(cls) -> "MonitorConfig":
        """Carga configuración desde variables de entorno.

        Variables de entorno soportadas:
            MONITOR_MODO: Modo del monitor
            MONITOR_HEADLESS: Si ejecutar en modo headless (1/true/yes)
            MONITOR_INTERVALO_LAB_EXP: Intervalo laboral expedientes (minutos)
            MONITOR_INTERVALO_LAB_ENT: Intervalo laboral entradas (minutos)
            MONITOR_NOTIF_ENTRADAS: Notificar nuevas entradas (1/true/yes)
            MONITOR_NOTIF_EXPEDIENTES: Notificar cambios expedientes (1/true/yes)

        Returns:
            MonitorConfig: Instancia con configuración desde env
        """
        config = cls()

        # Modo
        if modo := os.getenv("MONITOR_MODO"):
            if modo in ("automatico", "laboral", "no_laboral"):
                config.modo = modo  # type: ignore

        # Headless
        if headless_env := os.getenv("MONITOR_HEADLESS"):
            config.headless = headless_env.lower() in ("1", "true", "yes", "y")

        # Intervalos
        if intervalo := os.getenv("MONITOR_INTERVALO_LAB_EXP"):
            config.intervalos_laboral_expedientes = int(intervalo)

        if intervalo := os.getenv("MONITOR_INTERVALO_LAB_ENT"):
            config.intervalos_laboral_entradas = int(intervalo)

        # Notificaciones
        if notif := os.getenv("MONITOR_NOTIF_ENTRADAS"):
            config.notificar_nuevas_entradas = notif.lower() in ("1", "true", "yes", "y")

        if notif := os.getenv("MONITOR_NOTIF_EXPEDIENTES"):
            config.notificar_cambios_expedientes = notif.lower() in ("1", "true", "yes", "y")

        return config

    def to_file(self, path: str | Path = "config/monitor.json") -> None:
        """Guarda configuración a archivo JSON.

        Args:
            path: Ruta donde guardar el archivo
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2, ensure_ascii=False)

    def to_dict(self) -> dict:
        """Convierte la configuración a diccionario.

        Returns:
            dict: Configuración como diccionario
        """
        return asdict(self)

    @classmethod
    def from_system_config(cls, system_config) -> "MonitorConfig":
        """Crea MonitorConfig desde SystemConfig.

        Este método permite usar SystemConfig con código que espera MonitorConfig,
        manteniendo retrocompatibilidad.

        Args:
            system_config: Instancia de SystemConfig

        Returns:
            MonitorConfig: Configuración del monitor extraída de SystemConfig

        Example:
            >>> from pjn import SystemConfig
            >>> system_config = SystemConfig.from_file("config/sistema.json")
            >>> monitor_config = MonitorConfig.from_system_config(system_config)
            >>> monitor = MonitorPJN(monitor_config)
        """
        return cls(
            modo=system_config.modo_monitor,
            headless=system_config.headless,
            directorio_datos=system_config.directorio_monitor_datos,
            intervalos_laboral_expedientes=system_config.intervalos_laboral_expedientes,
            intervalos_laboral_entradas=system_config.intervalos_laboral_entradas,
            intervalos_no_laboral_expedientes=system_config.intervalos_no_laboral_expedientes,
            intervalos_no_laboral_entradas=system_config.intervalos_no_laboral_entradas,
            dias_laborales=system_config.dias_laborales.copy(),
            hora_inicio=system_config.hora_inicio,
            hora_fin=system_config.hora_fin,
            max_reintentos_expedientes=system_config.max_reintentos_expedientes,
            espera_reintentos_expedientes=system_config.espera_reintentos_expedientes,
            max_reintentos_entradas=system_config.max_reintentos_entradas,
            espera_reintentos_entradas=system_config.espera_reintentos_entradas,
            notificar_nuevas_entradas=system_config.notificar_nuevas_entradas,
            notificar_cambios_expedientes=system_config.notificar_cambios_expedientes,
            notificar_errores=system_config.notificar_errores,
            verificar_entradas=system_config.verificar_entradas,
            verificar_expedientes=system_config.verificar_expedientes,
            comparacion_automatica=system_config.comparacion_automatica,
            fecha_corte_expedientes=system_config.fecha_corte_expedientes,
            fecha_desde_entradas=system_config.fecha_desde_entradas,
            fecha_hasta_entradas=system_config.fecha_hasta_entradas,
            fecha_desde_expedientes=system_config.fecha_desde_expedientes,
            fecha_hasta_expedientes=system_config.fecha_hasta_expedientes,
        )


__all__ = ["MonitorConfig", "ModoMonitor"]
