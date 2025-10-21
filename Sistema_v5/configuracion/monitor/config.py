"""Configuración del sistema de monitoreo PJN.

Este módulo define la configuración completa del monitor usando dataclasses,
permitiendo carga desde archivo JSON o creación programática.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

from .shared_config import ModoMonitor, MonitorSharedConfig
from .validators import validar_directorio
from ..utils.env import parse_bool, parse_int


@dataclass
class MonitorConfig(MonitorSharedConfig):
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
    def __init__(
        self,
        modo: ModoMonitor = "automatico",
        headless: bool = True,
        directorio_datos: str = "data/monitor",
        intervalos_laboral_expedientes: int = 15,
        intervalos_laboral_entradas: int = 10,
        intervalos_no_laboral_expedientes: int = 60,
        intervalos_no_laboral_entradas: int = 30,
        dias_laborales: list[str] | None = None,
        hora_inicio: str = "08:00",
        hora_fin: str = "18:00",
        max_reintentos_expedientes: int = 3,
        espera_reintentos_expedientes: int = 30,
        max_reintentos_entradas: int = 3,
        espera_reintentos_entradas: int = 30,
        notificar_nuevas_entradas: bool = True,
        notificar_cambios_expedientes: bool = True,
        notificar_errores: bool = True,
        verificar_entradas: bool = True,
        verificar_expedientes: bool = True,
        comparacion_automatica: bool = False,
        fecha_corte_expedientes: str | None = None,
        fecha_desde_entradas: str | None = None,
        fecha_hasta_entradas: str | None = None,
        fecha_desde_expedientes: str | None = None,
        fecha_hasta_expedientes: str | None = None,
        # Nuevos parámetros
        dias_atras_entradas: int | None = None,
        dias_atras_expedientes: int | None = None,
        extraccion_expedientes_completa: bool = False,
        expedientes_orden: str | None = None,
        expedientes_detener_duplicados: bool = True,
        expedientes_max_paginas: int | None = None,
    ) -> None:
        shared_kwargs = dict(
            modo_monitor=modo,
            headless=headless,
            directorio_monitor_datos=directorio_datos,
            intervalos_laboral_expedientes=intervalos_laboral_expedientes,
            intervalos_laboral_entradas=intervalos_laboral_entradas,
            intervalos_no_laboral_expedientes=intervalos_no_laboral_expedientes,
            intervalos_no_laboral_entradas=intervalos_no_laboral_entradas,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            max_reintentos_expedientes=max_reintentos_expedientes,
            espera_reintentos_expedientes=espera_reintentos_expedientes,
            max_reintentos_entradas=max_reintentos_entradas,
            espera_reintentos_entradas=espera_reintentos_entradas,
            notificar_nuevas_entradas=notificar_nuevas_entradas,
            notificar_cambios_expedientes=notificar_cambios_expedientes,
            notificar_errores=notificar_errores,
            verificar_entradas=verificar_entradas,
            verificar_expedientes=verificar_expedientes,
            comparacion_automatica=comparacion_automatica,
            fecha_corte_expedientes=fecha_corte_expedientes,
            fecha_desde_entradas=fecha_desde_entradas,
            fecha_hasta_entradas=fecha_hasta_entradas,
            fecha_desde_expedientes=fecha_desde_expedientes,
            fecha_hasta_expedientes=fecha_hasta_expedientes,
            # Nuevos campos
            dias_atras_entradas=dias_atras_entradas,
            dias_atras_expedientes=dias_atras_expedientes,
            extraccion_expedientes_completa=extraccion_expedientes_completa,
            expedientes_orden=expedientes_orden,
            expedientes_detener_duplicados=expedientes_detener_duplicados,
            expedientes_max_paginas=expedientes_max_paginas,
        )
        if dias_laborales is not None:
            shared_kwargs["dias_laborales"] = dias_laborales

        super().__init__(**shared_kwargs)

    @property
    def modo(self) -> ModoMonitor:
        return self.modo_monitor

    @modo.setter
    def modo(self, value: ModoMonitor) -> None:
        self.modo_monitor = value

    @property
    def directorio_datos(self) -> str:
        return self.directorio_monitor_datos

    @directorio_datos.setter
    def directorio_datos(self, value: str) -> None:
        self.directorio_monitor_datos = value

    def __post_init__(self) -> None:
        super().__post_init__()
        self.directorio_datos = validar_directorio(
            self.directorio_datos,
            "directorio_datos",
            create=True,
        )

    @staticmethod
    def _sanitize_data(data: dict) -> dict:
        """Elimina claves usadas como comentarios en las plantillas JSON."""

        return {
            key: value
            for key, value in data.items()
            if not key.startswith("//") and not key.startswith("__")
        }

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
            project_root = Path(__file__).resolve().parents[3]

            # Para rutas relativas, intentar resolverlas desde la raíz del proyecto
            candidate = path if path.is_absolute() else project_root / path

            if candidate.exists():
                path = candidate
            else:
                # Crear configuración por defecto en la ubicación resuelta
                path = candidate
                config = cls()
                config.to_file(path)
                return config

        with path.open("r", encoding="utf-8") as f:
            raw_data = json.load(f)

        data = cls._sanitize_data(raw_data)

        return cls(**data)

    @classmethod
    def from_env(cls, prefix: str = "MONITOR_") -> "MonitorConfig":
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
        data: dict[str, object] = {}

        # Modo
        if modo := os.getenv(f"{prefix}MODO"):
            modo_normalized = modo.strip().lower()
            if modo_normalized in ("automatico", "laboral", "no_laboral"):
                data["modo"] = modo_normalized

        # Headless
        headless_env = os.getenv(f"{prefix}HEADLESS")
        if headless_env is not None:
            data["headless"] = parse_bool(headless_env)

        # Intervalos
        intervalo = os.getenv(f"{prefix}INTERVALO_LAB_EXP")
        if intervalo is not None:
            data["intervalos_laboral_expedientes"] = parse_int(intervalo)

        intervalo = os.getenv(f"{prefix}INTERVALO_LAB_ENT")
        if intervalo is not None:
            data["intervalos_laboral_entradas"] = parse_int(intervalo)

        # Notificaciones
        notif = os.getenv(f"{prefix}NOTIF_ENTRADAS")
        if notif is not None:
            data["notificar_nuevas_entradas"] = parse_bool(notif)

        notif = os.getenv(f"{prefix}NOTIF_EXPEDIENTES")
        if notif is not None:
            data["notificar_cambios_expedientes"] = parse_bool(notif)

        return cls(**data)

    def to_file(self, path: str | Path = "config/monitor.json") -> None:
        """Guarda configuración a archivo JSON.

        Args:
            path: Ruta donde guardar el archivo
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    def to_dict(self) -> dict:
        """Convierte la configuración a diccionario.

        Returns:
            dict: Configuración como diccionario
        """
        data = asdict(self)
        data["modo"] = data.pop("modo_monitor")
        data["directorio_datos"] = data.pop("directorio_monitor_datos")
        return data

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
            # Nuevos campos
            dias_atras_entradas=system_config.dias_atras_entradas,
            dias_atras_expedientes=system_config.dias_atras_expedientes,
            extraccion_expedientes_completa=system_config.extraccion_expedientes_completa,
            expedientes_orden=system_config.expedientes_orden,
            expedientes_detener_duplicados=system_config.expedientes_detener_duplicados,
            expedientes_max_paginas=system_config.expedientes_max_paginas,
        )


__all__ = ["MonitorConfig", "ModoMonitor"]
