"""Servicios para obtener listados iniciales de expedientes."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from ...configuracion.core import ExtraccionExpedientesConfig, SystemConfig
from ...configuracion.monitor.config import MonitorConfig
from ...pjn.scraping.base import obtener_pagina_autenticada
from ...pjn.scraping.expedientes import extraer_expedientes_completos_modelos

if TYPE_CHECKING:  # pragma: no cover - solo para tipado
    from ...pjn.models.expediente import ExpedienteResumen


def obtener_listado_inicial(
    config: SystemConfig | MonitorConfig,
    *,
    extraccion: ExtraccionExpedientesConfig | None = None,
) -> tuple[list["ExpedienteResumen"], str, dict[str, object]]:
    """Envoltorio síncrono sobre :func:`extraer_listado_inicial`."""

    return asyncio.run(
        extraer_listado_inicial(
            config,
            extraccion=extraccion,
        )
    )


async def extraer_listado_inicial(
    config: SystemConfig | MonitorConfig,
    *,
    extraccion: ExtraccionExpedientesConfig | None = None,
) -> tuple[list["ExpedienteResumen"], str, dict[str, object]]:
    """Obtiene el listado completo de expedientes iniciales."""

    extraccion_config = _prepare_extraccion_config(config, extraccion)

    cm = obtener_pagina_autenticada(headless=config.headless)
    exc_type: type[BaseException] | None = None
    exc: BaseException | None = None
    tb = None
    try:
        page, _context, _browser = await cm.__aenter__()
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
        return expedientes, motivo, metadata
    except Exception as error:  # noqa: BLE001 - repropagamos tras cerrar la sesión
        exc_type, exc, tb = type(error), error, error.__traceback__
        raise
    finally:
        await cm.__aexit__(exc_type, exc, tb)


def _prepare_extraccion_config(
    config: SystemConfig | MonitorConfig,
    extraccion: ExtraccionExpedientesConfig | None,
) -> ExtraccionExpedientesConfig:
    base_config = extraccion or ExtraccionExpedientesConfig.completo()
    extraccion_config = replace(base_config)

    extraccion_config.orden = getattr(config, "expedientes_orden", extraccion_config.orden)

    fecha_corte = _resolve_fecha_corte(config)
    if fecha_corte:
        extraccion_config.fecha_corte = fecha_corte

    if getattr(config, "extraccion_expedientes_completa", False):
        extraccion_config.max_paginas = None
        extraccion_config.detener_en_duplicado = False
    else:
        max_paginas = getattr(config, "expedientes_max_paginas", None)
        if max_paginas is None:
            max_paginas = getattr(config, "max_paginas_expedientes", None)
        if max_paginas is not None:
            extraccion_config.max_paginas = max_paginas
        detener = getattr(config, "expedientes_detener_duplicados", None)
        if detener is not None:
            extraccion_config.detener_en_duplicado = detener

    return extraccion_config


def _resolve_fecha_corte(config: SystemConfig | MonitorConfig) -> str | None:
    fecha = getattr(config, "fecha_desde_expedientes", None) or getattr(
        config, "fecha_corte_expedientes", None
    )
    if fecha:
        return fecha

    dias_atras = getattr(config, "dias_atras_expedientes", None)
    if dias_atras:
        base = datetime.now() - timedelta(days=dias_atras)
        return base.strftime("%Y-%m-%d")

    return None
