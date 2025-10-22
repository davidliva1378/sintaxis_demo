"""Coordinación del ciclo de prueba del extractor inicial PJN.

Este módulo implementa el flujo manual descrito en la documentación de la
fase de pruebas del extractor inicial y enlaza cada una de las tareas
existentes:

1. **Configuración del sistema**. Se carga :class:`~configuracion.core.SystemConfig`
   desde el archivo indicado, reutilizando la infraestructura unificada de
   configuraciones.
2. **Formulario de directorios (Tarea 2)**. Se lanza la ventana
   :class:`Sistema_v5.extractor_inicial.ui.directorios_form.DirectoriosForm` para que la
   persona operadora confirme o ajuste las rutas que utilizarán los siguientes
   pasos.
3. **Servicio de extracción inicial (Tarea 3)**. Se ejecuta la extracción de
   expedientes mediante :func:`Sistema_v5.pjn.scraping.expedientes.extraer_expedientes_completos_modelos`
   y se persiste el resultado en ``directorio_extraccion_inicial``.
4. **Formulario de filtrado (Tarea 4)**. Se abre la interfaz de filtrado de
   historiales :func:`Sistema_v5.ui.gui_monitor_form.launch_monitor_form`,
   delegando el manejo de la sesión autenticada a la propia GUI.
5. **Procesamiento automatizado (Tarea 5)**. Finalmente se invoca el motor de
   monitoreo :class:`Sistema_v5.pjn.monitor.core.MonitorPJN` para ejecutar las
   verificaciones automáticas de entradas y expedientes usando la configuración
   consolidada.

Las funciones auxiliares expuestas permiten reutilizar cada etapa por
separado, mientras que :func:`run_ciclo_prueba` orquesta el recorrido completo
para scripts o herramientas de línea de comandos.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Coroutine

if __package__ is None or __package__ == "":  # pragma: no cover - comportamiento CLI
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.append(str(project_root))
    __package__ = "Sistema_v5.extractor_inicial"

PROJECT_ROOT = Path(__file__).resolve().parents[2]

from ..configuracion.core import SystemConfig
from ..configuracion.core.extraccion_config import ExtraccionExpedientesConfig
from ..configuracion.monitor.config import MonitorConfig
from ..pjn.monitor.core import MonitorPJN
from ..pjn.scraping import obtener_pagina_autenticada
from ..pjn.scraping.expedientes import extraer_expedientes_completos_modelos
from ..ui.gui_monitor_form import launch_monitor_form
from .ui.directorios_form import (
    mostrar_formulario_directorios as _mostrar_formulario_directorios_gui,
)

logger = logging.getLogger(__name__)


def run_ciclo_prueba(
    config_sistema_path: str | Path = "config/sistema.json",
    config_monitor_path: str | Path = "config/monitor.json",
    *,
    directorio_extraccion: str | Path | None = None,
    directorio_datos_monitor: str | Path | None = None,
    mostrar_formulario_directorios: bool = True,
    mostrar_formulario_filtrado: bool = True,
) -> Path | None:
    """Ejecuta el ciclo completo del extractor inicial.

    Args:
        config_sistema_path: Ruta al archivo ``sistema.json``.
        config_monitor_path: Ruta al archivo ``monitor.json`` que usará la GUI.
        directorio_extraccion: Directorio opcional para guardar la extracción
            inicial. Si no se indica se usa ``SystemConfig.directorio_extraccion_inicial``.
        directorio_datos_monitor: Directorio opcional donde el monitor
            almacenará historiales y selecciones. Por defecto se reutiliza el
            configurado en ``SystemConfig``/``MonitorConfig``.
        mostrar_formulario_directorios: Si ``True`` se abre el formulario de
            directorios antes de continuar.
        mostrar_formulario_filtrado: Si ``True`` se abre la interfaz de
            filtrado antes del procesamiento automatizado.

    Returns:
        Ruta del archivo JSON generado durante la extracción inicial (si se
        ejecutó la etapa correspondiente). Puede devolver ``None`` si la
        extracción fue omitida por un error.
    """

    sistema_path = _resolve_config_path(Path(config_sistema_path))
    monitor_path = _resolve_config_path(Path(config_monitor_path))

    if mostrar_formulario_directorios:
        logger.info("🖥️  Abriendo formulario de directorios")
        system_config = _mostrar_formulario_directorios_gui(sistema_path)
    else:
        logger.info("📥 Cargando configuración del sistema desde %s", sistema_path)
        system_config = _load_system_config(sistema_path)

    monitor_config = _prepare_monitor_config(
        monitor_path,
        system_config,
        directorio_datos_monitor,
    )

    logger.info("🚀 Ejecutando extracción inicial de expedientes")
    json_path: Path | None = None
    try:
        json_path = _ejecutar_extraccion_inicial(
            system_config,
            directorio_extraccion,
        )
    except Exception as exc:  # pragma: no cover - defensivo frente a I/O real
        logger.exception("No se pudo completar la extracción inicial: %s", exc)

    if mostrar_formulario_filtrado:
        logger.info("🗂️  Abriendo formulario de filtrado del monitor")
        _abrir_formulario_filtrado(
            monitor_path,
            monitor_config,
            directorio_datos_monitor,
        )
        # El formulario puede haber ajustado directorios; reflejar cambios
        monitor_config = MonitorConfig.from_file(monitor_path)

    logger.info("🤖 Ejecutando procesamiento automatizado del monitor")
    try:
        _ejecutar_procesamiento_automatizado(monitor_config)
    except Exception as exc:  # pragma: no cover - defensivo
        logger.exception("Fallo durante el procesamiento automatizado: %s", exc)

    return json_path


def _load_system_config(config_path: Path) -> SystemConfig:
    if not config_path.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo de configuración del sistema: {config_path}"
        )
    return SystemConfig.from_file(config_path)


def _resolve_config_path(path: Path) -> Path:
    if path.is_absolute() or path.exists():
        return path

    candidate = PROJECT_ROOT / path
    if candidate.exists() or candidate.parent.exists():
        return candidate

    return path


def _prepare_monitor_config(
    monitor_path: Path,
    system_config: SystemConfig,
    directorio_datos_monitor: str | Path | None,
) -> MonitorConfig:
    monitor_config = MonitorConfig.from_system_config(system_config)

    if directorio_datos_monitor is not None:
        monitor_config.directorio_datos = str(Path(directorio_datos_monitor))

    monitor_path.parent.mkdir(parents=True, exist_ok=True)
    monitor_config.to_file(monitor_path)
    return monitor_config


def _ejecutar_extraccion_inicial(
    system_config: SystemConfig,
    directorio_extraccion: str | Path | None,
) -> Path:
    destino_base = Path(
        directorio_extraccion or system_config.directorio_extraccion_inicial
    )
    destino_base.mkdir(parents=True, exist_ok=True)

    output_path = _run_async_task(
        _extraer_expedientes_iniciales(system_config, destino_base)
    )
    logger.info("📁 Extracción inicial guardada en %s", output_path)
    return output_path


async def _extraer_expedientes_iniciales(
    system_config: SystemConfig,
    destino_base: Path,
) -> Path:
    extraccion_config = _build_extraccion_config(system_config)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_path = destino_base / f"expedientes-inicial-{timestamp}.json"

    async with obtener_pagina_autenticada(headless=system_config.headless) as (
        page,
        _context,
        _browser,
    ):
        expedientes, motivo, metadata = await extraer_expedientes_completos_modelos(
            page,
            sel_tabla=extraccion_config.sel_tabla,
            sel_tbody=extraccion_config.sel_tbody,
            sel_siguiente=extraccion_config.sel_siguiente,
            max_paginas=extraccion_config.max_paginas,
            omitir_duplicados=extraccion_config.omitir_duplicados,
            detener_en_duplicado=extraccion_config.detener_en_duplicado,
            fecha_corte=extraccion_config.fecha_corte,
            tiempo_maximo_segundos=extraccion_config.tiempo_maximo_segundos,
            orden=extraccion_config.orden,
            pagination_strategy=extraccion_config.pagination_strategy,
        )

    payload = {
        "generado_en": datetime.now().isoformat(timespec="seconds"),
        "motivo": motivo,
        "metadata": metadata,
        "expedientes": [exp.to_dict() for exp in expedientes],
    }
    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    return output_path


def _build_extraccion_config(system_config: SystemConfig) -> ExtraccionExpedientesConfig:
    fecha_corte = _determine_fecha_corte(system_config)

    if system_config.extraccion_expedientes_completa:
        max_paginas: int | None = None
        detener = False
    else:
        max_paginas = system_config.expedientes_max_paginas or system_config.max_paginas_expedientes
        detener = system_config.expedientes_detener_duplicados

    return ExtraccionExpedientesConfig(
        max_paginas=max_paginas,
        fecha_corte=fecha_corte,
        detener_en_duplicado=detener,
        orden=system_config.expedientes_orden,
    )


def _determine_fecha_corte(system_config: SystemConfig) -> str | None:
    fecha = (
        system_config.fecha_desde_expedientes
        or system_config.fecha_corte_expedientes
    )

    if fecha:
        return fecha

    dias_atras = system_config.dias_atras_expedientes
    if dias_atras is not None:
        base = datetime.now().date() - timedelta(days=dias_atras)
        return base.strftime("%Y-%m-%d")

    return None


def _abrir_formulario_filtrado(
    monitor_path: Path,
    monitor_config: MonitorConfig,
    directorio_datos_monitor: str | Path | None,
) -> None:
    datos_dir = Path(directorio_datos_monitor or monitor_config.directorio_datos)
    datos_dir.mkdir(parents=True, exist_ok=True)

    launch_monitor_form(
        monitor_path,
        datos_dir=datos_dir,
    )


def _ejecutar_procesamiento_automatizado(monitor_config: MonitorConfig) -> None:
    monitor = MonitorPJN(monitor_config)

    async def _run() -> None:
        if monitor.config.verificar_entradas:
            await monitor.verificar_entradas()
        if monitor.config.verificar_expedientes:
            await monitor.verificar_expedientes()

    _run_async_task(_run())


def _run_async_task(coro: Coroutine[Any, Any, Any]) -> Any:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    raise RuntimeError(
        "run_ciclo_prueba debe ejecutarse desde un contexto síncrono sin un bucle "
        "asyncio activo"
    )


# Exponer helpers adicionales para pruebas o reutilización externa
__all__ = ["run_ciclo_prueba"]


if __name__ == "__main__":  # pragma: no cover - punto de entrada CLI
    run_ciclo_prueba()
