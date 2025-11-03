"""Utilidades compartidas para gestionar `config_monitor.json`."""

from __future__ import annotations

import json
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path

try:
    from core.modulos_monitor.expedientes_modular.verificacion_expedientes import (
        obtener_fecha_corte as _obtener_fecha_corte_legacy,
    )
except ImportError:  # pragma: no cover - ejecución directa fuera del paquete
    _obtener_fecha_corte_legacy = None

CONFIG_PATH = Path("config/config_monitor.json")

DEFAULT_CONFIG = {
    "modo": "automatico",
    "horario_laboral": {
        "dias": ["lunes", "martes", "miércoles", "jueves", "viernes"],
        "hora_inicio": "07:00",
        "hora_fin": "20:00",
        "intervalo_minutos": 30,
        "intervalo_minutos_entradas": 30,
    },
    "fuera_horario": {
        "intervalo_minutos": 240,
        "intervalo_minutos_entradas": 240,
    },
    "filtro_expedientes": {
        "modo": "ultimo_dia_habil",
        "dias_atras": 1,
        "orden": "fecha",
    },
    "comparacion": {
        "modo": "parcial",
        "auto": True,
    },
    "respaldo": {
        "destino": "datos_extraidos/monitoreo/historico",
        "archivos": [],
    },
    "rutas": {
        "monitoreo": "datos_extraidos/monitoreo",
    },
    "reintentos": {
        "expedientes": {"maximos": 5, "espera_segundos": 5},
        "entradas": {"maximos": 5, "espera_segundos": 5},
    },
    "notificaciones": {
        "respaldo": True,
        "comparacion_sin_cambios": False,
        "comparacion_faltantes": True,
    },
    "procesador_pdf": {
        "habilitado": True,
        "clasificacion_automatica": True,
        "confianza_minima": 0.75,
        "vencimientos_automaticos": True,
        "dias_urgentes": 7,
        "duplicados_analisis": True,
        "timeout_clasificacion": 300,
        "guardar_reportes": True,
        "carpeta_reportes": "datos_extraidos/monitoreo/reportes_pdf",
    },
}

MODOS_VALIDOS: tuple[str, ...] = ("automatico", "laboral", "no_laboral")


def _mezclar_dicts(base: dict, override: Mapping) -> dict:
    """Mezcla dos diccionarios de manera recursiva preservando defaults."""

    for clave, valor in override.items():
        valor_base = base.get(clave)
        if isinstance(valor_base, dict) and isinstance(valor, Mapping):
            base[clave] = _mezclar_dicts(valor_base, valor)
        else:
            base[clave] = deepcopy(valor)
    return base


def _inyectar_defaults(config: dict) -> dict:
    """Completa el diccionario recibido con los valores por defecto."""

    resultado = deepcopy(DEFAULT_CONFIG)
    if isinstance(config, Mapping):
        resultado = _mezclar_dicts(resultado, config)
    return resultado


def cargar_config_monitor(path: Path | None = None) -> dict:
    """Lee `config_monitor.json` asegurando que existan los defaults esperados."""

    destino = path or CONFIG_PATH
    try:
        with destino.open("r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
    except Exception:
        datos = {}
    return _inyectar_defaults(datos)


def guardar_config_monitor(config: dict, path: Path | None = None) -> None:
    """Persiste la configuración del monitor en disco."""

    destino = path or CONFIG_PATH
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", encoding="utf-8") as archivo:
        json.dump(config, archivo, ensure_ascii=False, indent=2)


def actualizar_modo_monitor(nuevo_modo: str, path: Path | None = None) -> dict:
    """Actualiza el modo y devuelve la configuración persistida."""

    if nuevo_modo not in MODOS_VALIDOS:
        modos = ", ".join(MODOS_VALIDOS)
        raise ValueError(f"Modo inválido '{nuevo_modo}'. Opciones permitidas: {modos}.")

    config = cargar_config_monitor(path)
    config["modo"] = nuevo_modo
    guardar_config_monitor(config, path)
    return config


def es_modo_valido(modo: str) -> bool:
    """Permite validar sin lanzar excepciones los modos soportados."""

    return modo in MODOS_VALIDOS


def obtener_fecha_corte(config: dict | None = None, path: Path | None = None) -> str | None:
    """Resuelve la fecha de corte reutilizando el helper del monitor heredado."""

    if _obtener_fecha_corte_legacy is None:
        raise ImportError(
            "El helper 'obtener_fecha_corte' no está disponible en esta instalación."
        )

    if config is None:
        config = cargar_config_monitor(path)

    return _obtener_fecha_corte_legacy(config)


__all__ = [
    "CONFIG_PATH",
    "DEFAULT_CONFIG",
    "MODOS_VALIDOS",
    "actualizar_modo_monitor",
    "cargar_config_monitor",
    "es_modo_valido",
    "guardar_config_monitor",
    "obtener_fecha_corte",
]
