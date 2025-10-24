"""Configuración unificada del sistema PJN.

Este módulo centraliza TODAS las configuraciones del sistema en una única clase,
unificando las configuraciones dispersas en config.py, monitor/config.py y
models/extraccion_config.py.

Proporciona:
- Configuración de directorios (organización de archivos)
- Configuración de monitoreo (intervalos, horarios, notificaciones)
- Configuración de extracción (scraping, browser, límites)
- Configuración del sistema (logs, backups, cache)
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Literal
from datetime import datetime

from ..monitor.shared_config import ModoMonitor, MonitorSharedConfig
from ..monitor.validators import (
    validar_max_reintentos,
    validar_formato_fecha,
    validar_directorio,
)
from ..utils.env import parse_bool, parse_int, parse_str_list

# ============================================================================
# Tipos
# ============================================================================

ModoComparacion = Literal["automatico", "manual", "deshabilitado"]
FormatoReporte = Literal["json", "excel", "pdf"]
NivelLog = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


ENV_FIELD_MAP: dict[str, str] = {
    # Directorios
    "directorio_extraccion_inicial": "DIRECTORIO_EXTRACCION_INICIAL",
    "directorio_extracciones_temporales": "DIRECTORIO_EXTRACCIONES_TEMPORALES",
    "directorio_expedientes_base": "DIRECTORIO_EXPEDIENTES_BASE",
    "directorio_comparaciones": "DIRECTORIO_COMPARACIONES",
    "directorio_reportes": "DIRECTORIO_REPORTES",
    "directorio_logs": "DIRECTORIO_LOGS",
    "directorio_backups": "DIRECTORIO_BACKUPS",
    "directorio_cache": "DIRECTORIO_CACHE",
    "directorio_descargas": "DIRECTORIO_DESCARGAS",
    "directorio_monitor_datos": "DIRECTORIO_MONITOR_DATOS",
    # Monitoreo
    "modo_monitor": "MODO_MONITOR",
    "headless": "HEADLESS",
    "intervalos_laboral_expedientes": "INTERVALOS_LABORAL_EXPEDIENTES",
    "intervalos_laboral_entradas": "INTERVALOS_LABORAL_ENTRADAS",
    "intervalos_no_laboral_expedientes": "INTERVALOS_NO_LABORAL_EXPEDIENTES",
    "intervalos_no_laboral_entradas": "INTERVALOS_NO_LABORAL_ENTRADAS",
    "dias_laborales": "DIAS_LABORALES",
    "hora_inicio": "HORA_INICIO",
    "hora_fin": "HORA_FIN",
    "max_reintentos_expedientes": "MAX_REINTENTOS_EXPEDIENTES",
    "espera_reintentos_expedientes": "ESPERA_REINTENTOS_EXPEDIENTES",
    "max_reintentos_entradas": "MAX_REINTENTOS_ENTRADAS",
    "espera_reintentos_entradas": "ESPERA_REINTENTOS_ENTRADAS",
    "notificar_nuevas_entradas": "NOTIFICAR_NUEVAS_ENTRADAS",
    "notificar_cambios_expedientes": "NOTIFICAR_CAMBIOS_EXPEDIENTES",
    "notificar_errores": "NOTIFICAR_ERRORES",
    "actualizar_actuaciones_automaticamente": "ACTUALIZAR_ACTUACIONES_AUTOMATICAMENTE",
    "max_reintentos_actualizacion_actuaciones": "MAX_REINTENTOS_ACTUALIZACION_ACTUACIONES",
    "verificar_entradas": "VERIFICAR_ENTRADAS",
    "verificar_expedientes": "VERIFICAR_EXPEDIENTES",
    "tipos_entradas": "TIPOS_ENTRADAS",
    "comparacion_automatica": "COMPARACION_AUTOMATICA",
    "fecha_corte_expedientes": "FECHA_CORTE_EXPEDIENTES",
    "fecha_desde_entradas": "FECHA_DESDE_ENTRADAS",
    "fecha_hasta_entradas": "FECHA_HASTA_ENTRADAS",
    "fecha_desde_expedientes": "FECHA_DESDE_EXPEDIENTES",
    "fecha_hasta_expedientes": "FECHA_HASTA_EXPEDIENTES",
    "dias_atras_entradas": "DIAS_ATRAS_ENTRADAS",
    "dias_atras_expedientes": "DIAS_ATRAS_EXPEDIENTES",
    # Extracción y scraping
    "max_paginas_expedientes": "MAX_PAGINAS_EXPEDIENTES",
    "extraccion_expedientes_completa": "EXTRACCION_EXPEDIENTES_COMPLETA",
    "expedientes_orden": "EXPEDIENTES_ORDEN",
    "expedientes_detener_duplicados": "EXPEDIENTES_DETENER_DUPLICADOS",
    "expedientes_max_paginas": "EXPEDIENTES_MAX_PAGINAS",
    "timeout_default": "TIMEOUT_DEFAULT",
    "timeout_login": "TIMEOUT_LOGIN",
    "timeout_descarga": "TIMEOUT_DESCARGA",
    "max_reintentos_descarga": "MAX_REINTENTOS_DESCARGA",
    "generar_reportes_automaticos": "GENERAR_REPORTES_AUTOMATICOS",
    # Comparaciones y reportes
    "modo_comparacion": "MODO_COMPARACION",
    "formato_reportes": "FORMATO_REPORTES",
    # Sistema
    "fecha_inicio_sistema": "FECHA_INICIO_SISTEMA",
    "fecha_ultimo_backup": "FECHA_ULTIMO_BACKUP",
    "intervalo_backup_automatico": "INTERVALO_BACKUP_AUTOMATICO",
    "retener_historico_dias": "RETENER_HISTORICO_DIAS",
    "nivel_log": "NIVEL_LOG",
    "max_tamaño_log_mb": "MAX_TAMANO_LOG_MB",
    "rotacion_logs": "ROTACION_LOGS",
    "guardar_sesion": "GUARDAR_SESION",
    "duracion_sesion_horas": "DURACION_SESION_HORAS",
    "limite_memoria_mb": "LIMITE_MEMORIA_MB",
    "max_archivos_cache": "MAX_ARCHIVOS_CACHE",
}


BOOL_FIELDS = {
    "headless",
    "notificar_nuevas_entradas",
    "notificar_cambios_expedientes",
    "notificar_errores",
    "actualizar_actuaciones_automaticamente",
    "verificar_entradas",
    "verificar_expedientes",
    "comparacion_automatica",
    "generar_reportes_automaticos",
    "rotacion_logs",
    "guardar_sesion",
    "extraccion_expedientes_completa",
    "expedientes_detener_duplicados",
}


INT_FIELDS = {
    "intervalos_laboral_expedientes",
    "intervalos_laboral_entradas",
    "intervalos_no_laboral_expedientes",
    "intervalos_no_laboral_entradas",
    "max_reintentos_expedientes",
    "espera_reintentos_expedientes",
    "max_reintentos_entradas",
    "espera_reintentos_entradas",
    "max_paginas_expedientes",
    "timeout_default",
    "timeout_login",
    "timeout_descarga",
    "max_reintentos_descarga",
    "intervalo_backup_automatico",
    "retener_historico_dias",
    "max_tamaño_log_mb",
    "duracion_sesion_horas",
    "limite_memoria_mb",
    "max_archivos_cache",
    "dias_atras_entradas",
    "dias_atras_expedientes",
    "expedientes_max_paginas",
}


LIST_FIELDS = {"dias_laborales", "tipos_entradas"}


LOWER_FIELDS = {
    "modo_monitor",
    "modo_comparacion",
    "formato_reportes",
    "expedientes_orden",
}


UPPER_FIELDS = {"nivel_log"}


OPTIONAL_STR_FIELDS = {
    "fecha_corte_expedientes",
    "fecha_desde_entradas",
    "fecha_hasta_entradas",
    "fecha_desde_expedientes",
    "fecha_hasta_expedientes",
    "fecha_inicio_sistema",
    "fecha_ultimo_backup",
}


# ============================================================================
# CONFIGURACIÓN UNIFICADA DEL SISTEMA
# ============================================================================

@dataclass
class SystemConfig(MonitorSharedConfig):
    """Configuración completa y unificada del sistema PJN.

    Esta clase unifica todas las configuraciones del sistema en un único lugar,
    reemplazando la configuración dispersa anterior.

    Attributes:
        # ===== DIRECTORIOS =====
        directorio_extraccion_inicial: Donde se guardan extracciones iniciales
            (fuente para comparaciones en el monitoreo)
        directorio_extracciones_temporales: Para extracciones en progreso
        directorio_expedientes_base: Base para carpetas de expedientes individuales
        directorio_comparaciones: Resultados de comparaciones
        directorio_reportes: Reportes generados por el sistema
        directorio_logs: Archivos de log del sistema
        directorio_backups: Backups de configuraciones
        directorio_cache: Cache de sesiones y datos temporales
        directorio_descargas: PDFs y archivos descargados del portal
        directorio_monitor_datos: Datos del monitor (estado, historial)

        # ===== MONITOREO =====
        modo_monitor: Modo de operación del monitor
        intervalos_laboral_expedientes: Minutos entre verificaciones (laboral)
        intervalos_laboral_entradas: Minutos entre verificaciones (laboral)
        intervalos_no_laboral_expedientes: Minutos entre verificaciones (no laboral)
        intervalos_no_laboral_entradas: Minutos entre verificaciones (no laboral)
        dias_laborales: Días considerados laborales
        hora_inicio: Hora de inicio del horario laboral
        hora_fin: Hora de fin del horario laboral
        verificar_entradas: Si verificar entradas
        verificar_expedientes: Si verificar expedientes
        tipos_entradas: Tipos de entradas a incluir (combinaciones de "N" y "D")
        notificar_nuevas_entradas: Si notificar nuevas entradas
        notificar_cambios_expedientes: Si notificar cambios en expedientes
        notificar_errores: Si notificar errores del monitor
        actualizar_actuaciones_automaticamente: Si actualizar actuaciones al detectar cambios
        max_reintentos_actualizacion_actuaciones: Número de reintentos al actualizar actuaciones
        fecha_desde_entradas: Filtro de fecha desde para entradas
        fecha_hasta_entradas: Filtro de fecha hasta para entradas
        fecha_desde_expedientes: Filtro de fecha desde para expedientes
        fecha_hasta_expedientes: Filtro de fecha hasta para expedientes
        fecha_corte_expedientes: Fecha de corte para extracción (legacy)

        # ===== EXTRACCIÓN Y SCRAPING =====
        headless: Si ejecutar browser en modo headless
        max_paginas_expedientes: Límite de páginas a extraer
        timeout_default: Timeout por defecto en ms
        timeout_login: Timeout para autenticación en ms
        timeout_descarga: Timeout para descargas en ms
        max_reintentos_expedientes: Reintentos al fallar verificación
        espera_reintentos_expedientes: Segundos entre reintentos
        max_reintentos_entradas: Reintentos al fallar verificación
        espera_reintentos_entradas: Segundos entre reintentos
        max_reintentos_descarga: Reintentos para descargas

        # ===== COMPARACIONES =====
        modo_comparacion: Modo de comparación de expedientes
        comparacion_automatica: Si comparar tras cada verificación (legacy)
        generar_reportes_automaticos: Si generar reportes automáticamente
        formato_reportes: Formato de los reportes generados

        # ===== SISTEMA =====
        fecha_inicio_sistema: Fecha de primera ejecución
        fecha_ultimo_backup: Última vez que se hizo backup
        intervalo_backup_automatico: Frecuencia de backups en días
        retener_historico_dias: Días de retención de históricos
        nivel_log: Nivel de logging
        max_tamaño_log_mb: Tamaño máximo de logs en MB
        rotacion_logs: Si habilitar rotación de logs
        guardar_sesion: Si guardar sesión del portal
        duracion_sesion_horas: Horas antes de re-autenticar
        limite_memoria_mb: Límite de uso de memoria en MB
        max_archivos_cache: Límite de archivos en cache
    """

    # =========================================================================
    # DIRECTORIOS
    # =========================================================================

    directorio_extraccion_inicial: str = "data/inicial"
    """Donde se guardan las extracciones iniciales (fuente para comparaciones)."""

    directorio_extracciones_temporales: str = "data/temp"
    """Para extracciones en progreso."""

    directorio_expedientes_base: str = "data/expedientes"
    """Base para carpetas de expedientes individuales (data/expedientes/EXP-001/)."""

    directorio_comparaciones: str = "data/comparaciones"
    """Resultados de comparaciones entre extracciones."""

    directorio_reportes: str = "data/reportes"
    """Reportes generados por el sistema."""

    directorio_logs: str = "logs"
    """Archivos de log del sistema."""

    directorio_backups: str = "backups"
    """Backups de configuraciones y datos importantes."""

    directorio_cache: str = ".cache"
    """Cache de sesiones y datos temporales."""

    directorio_descargas: str = "descargas"
    """PDFs y archivos descargados del portal."""

    # =========================================================================
    # EXTRACCIÓN Y SCRAPING
    # =========================================================================

    headless: bool = True
    """Si ejecutar el browser en modo headless (sin interfaz gráfica)."""

    max_paginas_expedientes: int = 200
    """Límite máximo de páginas a extraer."""

    timeout_default: int = 8_000
    """Timeout por defecto para operaciones en ms."""

    timeout_login: int = 60_000
    """Timeout para proceso de autenticación en ms."""

    timeout_descarga: int = 30_000
    """Timeout para descargas individuales en ms."""

    max_reintentos_expedientes: int = 3
    """Número máximo de reintentos al fallar verificación de expedientes."""

    espera_reintentos_expedientes: int = 30
    """Segundos de espera entre reintentos de expedientes."""

    max_reintentos_entradas: int = 3
    """Número máximo de reintentos al fallar verificación de entradas."""

    espera_reintentos_entradas: int = 30
    """Segundos de espera entre reintentos de entradas."""

    max_reintentos_descarga: int = 3
    """Número máximo de reintentos para descargas fallidas."""

    # =========================================================================
    # COMPARACIONES
    # =========================================================================

    modo_comparacion: ModoComparacion = "manual"
    """Modo de comparación: automatico, manual, deshabilitado."""

    comparacion_automatica: bool = False
    """Si comparar expedientes tras cada verificación (legacy)."""

    generar_reportes_automaticos: bool = False
    """Si generar reportes automáticamente."""

    formato_reportes: FormatoReporte = "json"
    """Formato de los reportes: json, excel, pdf."""

    # =========================================================================
    # SISTEMA
    # =========================================================================

    fecha_inicio_sistema: str | None = None
    """Fecha de primera ejecución del sistema (auto-generada)."""

    fecha_ultimo_backup: str | None = None
    """Última vez que se hizo backup (auto-actualizada)."""

    intervalo_backup_automatico: int = 7
    """Frecuencia de backups automáticos en días."""

    retener_historico_dias: int = 90
    """Días de retención de históricos antes de limpieza."""

    nivel_log: NivelLog = "INFO"
    """Nivel de logging: DEBUG, INFO, WARNING, ERROR, CRITICAL."""

    max_tamaño_log_mb: int = 50
    """Tamaño máximo de archivos de log en MB."""

    rotacion_logs: bool = True
    """Si habilitar rotación automática de logs."""

    guardar_sesion: bool = True
    """Si guardar la sesión del portal entre ejecuciones."""

    duracion_sesion_horas: int = 24
    """Horas antes de forzar re-autenticación."""

    limite_memoria_mb: int = 2048
    """Límite de uso de memoria en MB (0 = sin límite)."""

    max_archivos_cache: int = 1000
    """Límite de archivos en cache (0 = sin límite)."""

    def __post_init__(self):
        """Valida la configuración después de la inicialización.

        Raises:
            ValidationError: Si algún parámetro es inválido
            IntervalError: Si los intervalos están fuera de rango
            DateRangeError: Si las fechas son inválidas
            WorkHoursError: Si las horas laborales son inválidas
        """
        super().__post_init__()

        # Validar directorios
        for dir_attr in [
            "directorio_extraccion_inicial",
            "directorio_extracciones_temporales",
            "directorio_expedientes_base",
            "directorio_comparaciones",
            "directorio_reportes",
            "directorio_logs",
            "directorio_backups",
            "directorio_cache",
            "directorio_descargas",
            "directorio_monitor_datos",
        ]:
            dir_value = getattr(self, dir_attr)
            normalized = validar_directorio(
                dir_value,
                dir_attr,
                create=True,
            )
            setattr(self, dir_attr, normalized)

        validar_max_reintentos(
            self.max_reintentos_descarga,
            "max_reintentos_descarga"
        )

        # Validar fechas de sistema
        validar_formato_fecha(self.fecha_inicio_sistema, "fecha_inicio_sistema")
        validar_formato_fecha(self.fecha_ultimo_backup, "fecha_ultimo_backup")

        # Inicializar fecha_inicio_sistema si es None
        if self.fecha_inicio_sistema is None:
            self.fecha_inicio_sistema = datetime.now().strftime("%Y-%m-%d")

    @staticmethod
    def _sanitize_data(data: dict) -> dict:
        """Elimina claves usadas como comentarios en las plantillas JSON."""

        return {
            key: value
            for key, value in data.items()
            if not key.startswith("//") and not key.startswith("__")
        }

    @classmethod
    def from_env(cls, prefix: str = "SISTEMA_") -> "SystemConfig":
        """Crea una configuración leyendo variables de entorno.

        Args:
            prefix: Prefijo de las variables de entorno. Por defecto ``SISTEMA_``.

        Returns:
            SystemConfig: Instancia con los valores cargados desde el entorno.
        """

        overrides: dict[str, object] = {}
        normalized_prefix = prefix or ""

        for field_name, env_suffix in ENV_FIELD_MAP.items():
            env_key = f"{normalized_prefix}{env_suffix}"
            raw_value = os.getenv(env_key)

            if raw_value is None:
                continue

            stripped_value = raw_value.strip()

            if field_name in OPTIONAL_STR_FIELDS and stripped_value.lower() in {"", "none", "null"}:
                overrides[field_name] = None
                continue

            if field_name in BOOL_FIELDS:
                overrides[field_name] = parse_bool(stripped_value)
            elif field_name in INT_FIELDS:
                overrides[field_name] = parse_int(stripped_value)
            elif field_name in LIST_FIELDS:
                overrides[field_name] = parse_str_list(stripped_value)
            elif field_name in LOWER_FIELDS:
                overrides[field_name] = stripped_value.lower()
            elif field_name in UPPER_FIELDS:
                overrides[field_name] = stripped_value.upper()
            else:
                overrides[field_name] = stripped_value

        if not overrides:
            return cls()

        return cls(**overrides)

    @classmethod
    def from_file(cls, path: str | Path = "config/sistema.json") -> "SystemConfig":
        """Carga configuración desde archivo JSON.

        Args:
            path: Ruta al archivo de configuración JSON

        Returns:
            SystemConfig: Instancia con configuración cargada

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
    def from_monitor_config(cls, monitor_config_path: str | Path = "config/monitor.json") -> "SystemConfig":
        """Crea SystemConfig desde un archivo monitor.json existente.

        Útil para migración desde el sistema de configuración anterior.

        Args:
            monitor_config_path: Ruta al archivo monitor.json

        Returns:
            SystemConfig: Instancia con valores migrados desde monitor.json

        Example:
            >>> config = SystemConfig.from_monitor_config("config/monitor.json")
            >>> config.to_file("config/sistema.json")
        """
        monitor_path = Path(monitor_config_path)

        if not monitor_path.exists():
            # Si no existe, retornar config por defecto
            return cls()

        with monitor_path.open("r", encoding="utf-8") as f:
            monitor_data = json.load(f)

        # Mapear campos de monitor.json a SystemConfig
        return cls(
            modo_monitor=monitor_data.get("modo", "automatico"),
            headless=monitor_data.get("headless", True),
            directorio_monitor_datos=monitor_data.get("directorio_datos", "data/monitor"),
            intervalos_laboral_expedientes=monitor_data.get("intervalos_laboral_expedientes", 15),
            intervalos_laboral_entradas=monitor_data.get("intervalos_laboral_entradas", 10),
            intervalos_no_laboral_expedientes=monitor_data.get("intervalos_no_laboral_expedientes", 60),
            intervalos_no_laboral_entradas=monitor_data.get("intervalos_no_laboral_entradas", 30),
            dias_laborales=monitor_data.get("dias_laborales", [
                "lunes", "martes", "miercoles", "jueves", "viernes"
            ]),
            hora_inicio=monitor_data.get("hora_inicio", "08:00"),
            hora_fin=monitor_data.get("hora_fin", "18:00"),
            max_reintentos_expedientes=monitor_data.get("max_reintentos_expedientes", 3),
            espera_reintentos_expedientes=monitor_data.get("espera_reintentos_expedientes", 30),
            max_reintentos_entradas=monitor_data.get("max_reintentos_entradas", 3),
            espera_reintentos_entradas=monitor_data.get("espera_reintentos_entradas", 30),
            notificar_nuevas_entradas=monitor_data.get("notificar_nuevas_entradas", True),
            notificar_cambios_expedientes=monitor_data.get("notificar_cambios_expedientes", True),
            notificar_errores=monitor_data.get("notificar_errores", True),
            actualizar_actuaciones_automaticamente=monitor_data.get("actualizar_actuaciones_automaticamente", True),
            max_reintentos_actualizacion_actuaciones=monitor_data.get("max_reintentos_actualizacion_actuaciones", 3),
            verificar_entradas=monitor_data.get("verificar_entradas", True),
            verificar_expedientes=monitor_data.get("verificar_expedientes", True),
            tipos_entradas=monitor_data.get("tipos_entradas", ("N",)),
            comparacion_automatica=monitor_data.get("comparacion_automatica", False),
            fecha_corte_expedientes=monitor_data.get("fecha_corte_expedientes"),
            fecha_desde_entradas=monitor_data.get("fecha_desde_entradas"),
            fecha_hasta_entradas=monitor_data.get("fecha_hasta_entradas"),
            fecha_desde_expedientes=monitor_data.get("fecha_desde_expedientes"),
            fecha_hasta_expedientes=monitor_data.get("fecha_hasta_expedientes"),
        )

    def to_file(self, path: str | Path = "config/sistema.json") -> None:
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
        data["tipos_entradas"] = list(self.tipos_entradas)
        return data

    def crear_directorios(self) -> None:
        """Crea todos los directorios definidos en la configuración.

        Útil para inicialización del sistema.
        """
        directorios = [
            self.directorio_extraccion_inicial,
            self.directorio_extracciones_temporales,
            self.directorio_expedientes_base,
            self.directorio_comparaciones,
            self.directorio_reportes,
            self.directorio_logs,
            self.directorio_backups,
            self.directorio_cache,
            self.directorio_descargas,
            self.directorio_monitor_datos,
        ]

        for directorio in directorios:
            Path(directorio).mkdir(parents=True, exist_ok=True)

    def hacer_backup(self, destino: str | Path | None = None) -> Path:
        """Crea un backup de la configuración actual.

        Args:
            destino: Ruta del archivo de backup. Si None, usa directorio_backups
                    con timestamp.

        Returns:
            Path: Ruta del archivo de backup creado
        """
        if destino is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            destino = Path(self.directorio_backups) / f"sistema_{timestamp}.json"
        else:
            destino = Path(destino)

        destino.parent.mkdir(parents=True, exist_ok=True)
        self.to_file(destino)

        # Actualizar fecha de último backup
        self.fecha_ultimo_backup = datetime.now().strftime("%Y-%m-%d")

        return destino


__all__ = [
    "SystemConfig",
    "ModoMonitor",
    "ModoComparacion",
    "FormatoReporte",
    "NivelLog",
]
