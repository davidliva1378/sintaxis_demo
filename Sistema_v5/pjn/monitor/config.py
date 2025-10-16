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


__all__ = ["MonitorConfig", "ModoMonitor"]
