"""Router de configuración del sistema.

Este módulo define los endpoints para leer y actualizar la configuración del sistema.
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException

from infrastructure.config import get_settings, reload_settings
from infrastructure.config.settings import PROJECT_ROOT
from presentation.api.rest.schemas import (
    BrowserConfigSchema,
    ConfigUpdateResponse,
    MCPConfigSchema,
    MonitoreoConfigSchema,
    ScrapingConfigSchema,
    StorageConfigSchema,
    SystemConfigResponse,
    SystemConfigUpdateRequest,
)
from core.config.vencimientos_config import VencimientosConfig, VencimientosConfigModel

router = APIRouter(prefix="/config", tags=["configuracion"])
logger = logging.getLogger(__name__)


@router.get("/sistema", response_model=SystemConfigResponse)
async def obtener_configuracion_sistema():
    """Obtiene toda la configuración del sistema.

    Returns:
        SystemConfigResponse: Configuración completa del sistema

    Example:
        >>> GET /api/v1/config/sistema
        {
            "browser": {...},
            "monitoreo": {...},
            "scraping": {...},
            "mcp": {...},
            "storage": {...}
        }
    """
    try:
        settings = get_settings()

        return SystemConfigResponse(
            browser=BrowserConfigSchema(
                headless=settings.browser.headless,
                timeout_ms=settings.browser.timeout_ms,
                navigation_timeout_ms=settings.browser.navigation_timeout_ms,
                user_agent=settings.browser.user_agent,
            ),
            monitoreo=MonitoreoConfigSchema(
                intervalo_segundos=settings.monitoreo.intervalo_segundos,
                dias_actividad=settings.monitoreo.dias_actividad,
                max_reintentos=settings.monitoreo.max_reintentos,
                notificar_cambios=settings.monitoreo.notificar_cambios,
                descargar_archivos=settings.monitoreo.descargar_archivos,
                # Opciones de extracción
                fecha_corte_dias=settings.monitoreo.fecha_corte_dias,
                max_paginas_monitoreo=settings.monitoreo.max_paginas_monitoreo,
                tiempo_maximo_extraccion=settings.monitoreo.tiempo_maximo_extraccion,
                detener_en_duplicado=settings.monitoreo.detener_en_duplicado,
                orden_extraccion=settings.monitoreo.orden_extraccion,
                # Avanzado
                intervalos_laboral_expedientes=settings.monitoreo.intervalos_laboral_expedientes,
                intervalos_laboral_entradas=settings.monitoreo.intervalos_laboral_entradas,
                intervalos_no_laboral_expedientes=settings.monitoreo.intervalos_no_laboral_expedientes,
                intervalos_no_laboral_entradas=settings.monitoreo.intervalos_no_laboral_entradas,
                dias_laborales=settings.monitoreo.dias_laborales,
                hora_inicio=settings.monitoreo.hora_inicio,
                hora_fin=settings.monitoreo.hora_fin,
            ),
            scraping=ScrapingConfigSchema(
                timeout_default=settings.scraping.timeout_default,
                timeout_login=settings.scraping.timeout_login,
                timeout_descarga=settings.scraping.timeout_descarga,
                max_paginas_expedientes=settings.scraping.max_paginas_expedientes,
                max_reintentos_descarga=settings.scraping.max_reintentos_descarga,
            ),
            mcp=MCPConfigSchema(
                habilitar=settings.mcp.habilitar,
                puerto=settings.mcp.puerto,
                mode=settings.mcp.mode,
                workspace_path=settings.mcp.workspace_path,
                server_name=settings.mcp.server_name,
                enable_pdf_extraction=settings.mcp.enable_pdf_extraction,
                enable_full_text_search=settings.mcp.enable_full_text_search,
                enable_statistics=settings.mcp.enable_statistics,
                max_pdf_pages=settings.mcp.max_pdf_pages,
                max_pdf_size_mb=settings.mcp.max_pdf_size_mb,
            ),
            storage=StorageConfigSchema(
                base_path=str(settings.storage.base_path),
                json_base_file=settings.storage.json_base_file,
                json_sistema_file=settings.storage.json_sistema_file,
                workspaces_dir=settings.storage.workspaces_dir,
                downloads_dir=settings.storage.downloads_dir,
                pretty_json=settings.storage.pretty_json,
                ensure_ascii=settings.storage.ensure_ascii,
            ),
        )

    except Exception as e:
        logger.exception("Error al obtener configuración del sistema")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener configuración: {str(e)}"
        )


@router.put("/sistema", response_model=ConfigUpdateResponse)
async def actualizar_configuracion_sistema(config: SystemConfigUpdateRequest):
    """Actualiza la configuración del sistema y la persiste en .env.

    Args:
        config: Configuración a actualizar (solo se actualizan campos enviados)

    Returns:
        ConfigUpdateResponse: Resultado de la actualización

    Raises:
        HTTPException: Si hay error al validar o actualizar

    Example:
        >>> PUT /api/v1/config/sistema
        {
            "browser": {
                "headless": true,
                "timeout_ms": 30000
            }
        }
    """
    try:
        # 1. Validar que los valores sean correctos
        if config.browser:
            if config.browser.timeout_ms < 1000:
                raise HTTPException(
                    status_code=400,
                    detail="browser.timeout_ms debe ser >= 1000ms"
                )
            if config.browser.navigation_timeout_ms < 1000:
                raise HTTPException(
                    status_code=400,
                    detail="browser.navigation_timeout_ms debe ser >= 1000ms"
                )

        if config.monitoreo:
            if config.monitoreo.intervalo_segundos < 0:
                raise HTTPException(
                    status_code=400,
                    detail="monitoreo.intervalo_segundos debe ser >= 0"
                )
            if config.monitoreo.dias_actividad < 1:
                raise HTTPException(
                    status_code=400,
                    detail="monitoreo.dias_actividad debe ser >= 1"
                )
            if config.monitoreo.max_reintentos < 1:
                raise HTTPException(
                    status_code=400,
                    detail="monitoreo.max_reintentos debe ser >= 1"
                )

        if config.scraping:
            if config.scraping.timeout_default < 1000:
                raise HTTPException(
                    status_code=400,
                    detail="scraping.timeout_default debe ser >= 1000ms"
                )
            if config.scraping.max_reintentos_descarga < 1:
                raise HTTPException(
                    status_code=400,
                    detail="scraping.max_reintentos_descarga debe ser >= 1"
                )

        if config.mcp:
            if config.mcp.puerto < 1 or config.mcp.puerto > 65535:
                raise HTTPException(
                    status_code=400,
                    detail="mcp.puerto debe estar entre 1 y 65535"
                )
            if config.mcp.max_pdf_pages < 1:
                raise HTTPException(
                    status_code=400,
                    detail="mcp.max_pdf_pages debe ser >= 1"
                )
            if config.mcp.max_pdf_size_mb < 1:
                raise HTTPException(
                    status_code=400,
                    detail="mcp.max_pdf_size_mb debe ser >= 1"
                )

        # 2. Construir diccionario de actualizaciones para .env
        env_updates: dict[str, str] = {}

        if config.browser:
            env_updates["BROWSER_HEADLESS"] = str(config.browser.headless).lower()
            env_updates["BROWSER_TIMEOUT_MS"] = str(config.browser.timeout_ms)
            env_updates["BROWSER_NAVIGATION_TIMEOUT_MS"] = str(config.browser.navigation_timeout_ms)
            if config.browser.user_agent:
                env_updates["BROWSER_USER_AGENT"] = config.browser.user_agent

        if config.monitoreo:
            env_updates["MONITOREO_INTERVALO_SEGUNDOS"] = str(config.monitoreo.intervalo_segundos)
            env_updates["MONITOREO_DIAS_ACTIVIDAD"] = str(config.monitoreo.dias_actividad)
            env_updates["MONITOREO_MAX_REINTENTOS"] = str(config.monitoreo.max_reintentos)
            env_updates["MONITOREO_NOTIFICAR_CAMBIOS"] = str(config.monitoreo.notificar_cambios).lower()
            env_updates["MONITOREO_DESCARGAR_ARCHIVOS"] = str(config.monitoreo.descargar_archivos).lower()

            # Opciones de extracción
            if config.monitoreo.fecha_corte_dias is not None:
                env_updates["MONITOREO_FECHA_CORTE_DIAS"] = str(config.monitoreo.fecha_corte_dias)
            if config.monitoreo.max_paginas_monitoreo is not None:
                env_updates["MONITOREO_MAX_PAGINAS_MONITOREO"] = str(config.monitoreo.max_paginas_monitoreo)
            if config.monitoreo.tiempo_maximo_extraccion is not None:
                env_updates["MONITOREO_TIEMPO_MAXIMO_EXTRACCION"] = str(config.monitoreo.tiempo_maximo_extraccion)
            env_updates["MONITOREO_DETENER_EN_DUPLICADO"] = str(config.monitoreo.detener_en_duplicado).lower()
            env_updates["MONITOREO_ORDEN_EXTRACCION"] = config.monitoreo.orden_extraccion

            # Avanzado
            if config.monitoreo.intervalos_laboral_expedientes is not None:
                env_updates["MONITOREO_INTERVALOS_LABORAL_EXPEDIENTES"] = str(config.monitoreo.intervalos_laboral_expedientes)
            if config.monitoreo.intervalos_laboral_entradas is not None:
                env_updates["MONITOREO_INTERVALOS_LABORAL_ENTRADAS"] = str(config.monitoreo.intervalos_laboral_entradas)
            if config.monitoreo.intervalos_no_laboral_expedientes is not None:
                env_updates["MONITOREO_INTERVALOS_NO_LABORAL_EXPEDIENTES"] = str(config.monitoreo.intervalos_no_laboral_expedientes)
            if config.monitoreo.intervalos_no_laboral_entradas is not None:
                env_updates["MONITOREO_INTERVALOS_NO_LABORAL_ENTRADAS"] = str(config.monitoreo.intervalos_no_laboral_entradas)

            env_updates["MONITOREO_DIAS_LABORALES"] = ",".join(config.monitoreo.dias_laborales)
            env_updates["MONITOREO_HORA_INICIO"] = config.monitoreo.hora_inicio
            env_updates["MONITOREO_HORA_FIN"] = config.monitoreo.hora_fin

        if config.scraping:
            env_updates["SCRAPING_TIMEOUT_DEFAULT"] = str(config.scraping.timeout_default)
            env_updates["SCRAPING_TIMEOUT_LOGIN"] = str(config.scraping.timeout_login)
            env_updates["SCRAPING_TIMEOUT_DESCARGA"] = str(config.scraping.timeout_descarga)
            if config.scraping.max_paginas_expedientes is not None:
                env_updates["SCRAPING_MAX_PAGINAS_EXPEDIENTES"] = str(config.scraping.max_paginas_expedientes)
            env_updates["SCRAPING_MAX_REINTENTOS_DESCARGA"] = str(config.scraping.max_reintentos_descarga)

        if config.mcp:
            env_updates["MCP_HABILITAR"] = str(config.mcp.habilitar).lower()
            env_updates["MCP_PUERTO"] = str(config.mcp.puerto)
            env_updates["MCP_MODE"] = config.mcp.mode
            env_updates["MCP_WORKSPACE_PATH"] = config.mcp.workspace_path
            env_updates["MCP_SERVER_NAME"] = config.mcp.server_name
            env_updates["MCP_ENABLE_PDF_EXTRACTION"] = str(config.mcp.enable_pdf_extraction).lower()
            env_updates["MCP_ENABLE_FULL_TEXT_SEARCH"] = str(config.mcp.enable_full_text_search).lower()
            env_updates["MCP_ENABLE_STATISTICS"] = str(config.mcp.enable_statistics).lower()
            env_updates["MCP_MAX_PDF_PAGES"] = str(config.mcp.max_pdf_pages)
            env_updates["MCP_MAX_PDF_SIZE_MB"] = str(config.mcp.max_pdf_size_mb)

        if config.storage:
            env_updates["STORAGE_BASE_PATH"] = config.storage.base_path
            env_updates["STORAGE_JSON_BASE_FILE"] = config.storage.json_base_file
            env_updates["STORAGE_JSON_SISTEMA_FILE"] = config.storage.json_sistema_file
            env_updates["STORAGE_WORKSPACES_DIR"] = config.storage.workspaces_dir
            env_updates["STORAGE_DOWNLOADS_DIR"] = config.storage.downloads_dir
            env_updates["STORAGE_PRETTY_JSON"] = str(config.storage.pretty_json).lower()
            env_updates["STORAGE_ENSURE_ASCII"] = str(config.storage.ensure_ascii).lower()

        # 3. Actualizar archivo .env
        env_path = PROJECT_ROOT / ".env"
        logger.info(f"Actualizando archivo .env en: {env_path}")
        _actualizar_env_file(env_path, env_updates)

        # 4. Recargar configuración del singleton para aplicar cambios inmediatamente
        reload_settings()
        logger.info("Configuración recargada exitosamente")

        logger.info(f"Configuración actualizada: {len(env_updates)} variables modificadas")

        return ConfigUpdateResponse(
            success=True,
            message="Configuración actualizada correctamente. Los cambios se han aplicado.",
            updates=env_updates
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error al actualizar configuración")
        raise HTTPException(
            status_code=500,
            detail=f"Error al actualizar configuración: {str(e)}"
        )



@router.get("/vencimientos", response_model=VencimientosConfigModel)
async def get_vencimientos_config():
    """Obtiene configuración de vencimientos."""
    return VencimientosConfig.get_instance().config


@router.post("/vencimientos", response_model=VencimientosConfigModel)
async def update_vencimientos_config(config: VencimientosConfigModel):
    """Actualiza configuración de vencimientos."""
    VencimientosConfig.get_instance().update(config.dict())
    return VencimientosConfig.get_instance().config

def _actualizar_env_file(env_path: Path, updates: dict[str, str]) -> None:
    """Actualiza variables en el archivo .env.

    Args:
        env_path: Path al archivo .env
        updates: Diccionario con las variables a actualizar (key=valor)

    Raises:
        FileNotFoundError: Si el archivo .env no existe
    """
    if not env_path.exists():
        raise FileNotFoundError(f"Archivo .env no encontrado en {env_path}")

    # Leer contenido actual
    lines = env_path.read_text().splitlines()

    # Actualizar valores existentes
    updated_lines = []
    updated_keys = set()

    for line in lines:
        # Ignorar comentarios y líneas vacías
        if not line.strip() or line.strip().startswith("#"):
            updated_lines.append(line)
            continue

        # Procesar líneas con variables
        if "=" in line:
            key = line.split("=", 1)[0].strip()
            if key in updates:
                updated_lines.append(f"{key}={updates[key]}")
                updated_keys.add(key)
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)

    # Agregar nuevas variables que no existían
    for key, value in updates.items():
        if key not in updated_keys:
            updated_lines.append(f"{key}={value}")

    # Escribir de vuelta al archivo
    env_path.write_text("\n".join(updated_lines) + "\n")
    logger.debug(f"Archivo .env actualizado: {len(updates)} variables")
