"""Utilidades compartidas para gestionar `config_monitor.json`."""

from __future__ import annotations

import json
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
    },
    "fuera_horario": {"intervalo_minutos": 240},
    "filtro_expedientes": {
        "modo": "ultimo_dia_habil",
        "dias_atras": 1,
        "orden": "fecha",
    },
    "comparacion": {
        "modo": "parcial",
    },
    "respaldo": {
        "destino": "datos_extraidos/monitoreo/historico",
    },
}

MODOS_VALIDOS: tuple[str, ...] = ("automatico", "laboral", "no_laboral")


def _inyectar_defaults(config: dict) -> dict:
    """Completa el diccionario recibido con los valores por defecto."""

    resultado = deepcopy(DEFAULT_CONFIG)
    for clave, valor in config.items():
        if isinstance(valor, dict) and isinstance(resultado.get(clave), dict):
            resultado[clave].update(valor)
        else:
            resultado[clave] = valor
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
