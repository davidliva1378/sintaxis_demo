"""
Router para gestión del servidor MCP.

Endpoints para controlar y configurar el servidor MCP (Model Context Protocol).
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from application.services.mcp_manager import get_mcp_manager

router = APIRouter(prefix="/mcp", tags=["mcp"])


# === Schemas ===

class MCPConfigUpdate(BaseModel):
    """Schema para actualizar configuración MCP."""
    auto_start: Optional[bool] = None
    mode: Optional[str] = None
    port: Optional[int] = None
    workspace_path: Optional[str] = None
    log_level: Optional[str] = None


class ToolsEnableRequest(BaseModel):
    """Schema para habilitar/deshabilitar tools."""
    tools: List[str]


# === Endpoints de Estado ===

@router.get("/status")
async def get_mcp_status():
    """
    Obtiene el estado actual del servidor MCP.

    Returns:
        Estado del servidor, PID, uptime, configuración
    """
    manager = get_mcp_manager()
    return manager.get_status()


@router.post("/start")
async def start_mcp_server():
    """
    Inicia el servidor MCP.

    Returns:
        Resultado de la operación con PID si exitoso
    """
    manager = get_mcp_manager()
    result = manager.start()

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Error iniciando servidor MCP")
        )

    return result


@router.post("/stop")
async def stop_mcp_server():
    """
    Detiene el servidor MCP.

    Returns:
        Resultado de la operación
    """
    manager = get_mcp_manager()
    result = manager.stop()

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Error deteniendo servidor MCP")
        )

    return result


@router.post("/restart")
async def restart_mcp_server():
    """
    Reinicia el servidor MCP.

    Returns:
        Resultado de la operación
    """
    manager = get_mcp_manager()
    result = manager.restart()

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Error reiniciando servidor MCP")
        )

    return result


# === Endpoints de Configuración ===

@router.get("/config")
async def get_mcp_config():
    """
    Obtiene la configuración actual del servidor MCP.

    Returns:
        Configuración actual
    """
    manager = get_mcp_manager()
    return manager.get_config()


@router.put("/config")
async def update_mcp_config(config: MCPConfigUpdate):
    """
    Actualiza la configuración del servidor MCP.

    Args:
        config: Nuevos valores de configuración

    Returns:
        Resultado con configuración actualizada
    """
    manager = get_mcp_manager()

    # Convertir a dict excluyendo None
    new_config = {k: v for k, v in config.dict().items() if v is not None}

    result = manager.update_config(new_config)

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Error actualizando configuración")
        )

    return result


# === Endpoints de Logs ===

@router.get("/logs")
async def get_mcp_logs(
    lines: int = Query(100, ge=1, le=1000, description="Número de líneas a retornar")
):
    """
    Obtiene las últimas líneas del log del servidor MCP.

    Args:
        lines: Número de líneas (1-1000)

    Returns:
        Lista de líneas de log
    """
    manager = get_mcp_manager()
    logs = manager.get_logs(lines)
    return {"logs": logs, "count": len(logs)}


@router.delete("/logs")
async def clear_mcp_logs():
    """
    Limpia el archivo de logs del servidor MCP.

    Returns:
        Resultado de la operación
    """
    manager = get_mcp_manager()
    result = manager.clear_logs()

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Error limpiando logs")
        )

    return result


# === Endpoints de Tools ===

@router.get("/tools")
async def get_mcp_tools():
    """
    Obtiene la lista de tools disponibles con estado.

    Returns:
        Lista de tools con nombre, descripción, categoría, habilitada
    """
    manager = get_mcp_manager()
    tools = manager.get_tools_list()
    return {"tools": tools, "total": len(tools)}


@router.put("/tools/enable")
async def set_enabled_tools(request: ToolsEnableRequest):
    """
    Establece las tools habilitadas.

    Args:
        request: Lista de nombres de tools a habilitar (vacío = todas)

    Returns:
        Resultado de la operación
    """
    manager = get_mcp_manager()
    result = manager.set_enabled_tools(request.tools)

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Error actualizando tools")
        )

    return result


@router.get("/tools/stats")
async def get_tools_stats():
    """
    Obtiene estadísticas de uso de tools.

    Returns:
        Estadísticas de uso
    """
    manager = get_mcp_manager()
    return manager.get_tool_stats()


@router.get("/resources")
async def get_mcp_resources():
    """
    Obtiene la lista de recursos disponibles.

    Returns:
        Lista de recursos
    """
    manager = get_mcp_manager()
    resources = manager.get_resources_list()
    return {"resources": resources, "total": len(resources)}


@router.get("/prompts")
async def get_mcp_prompts():
    """
    Obtiene la lista de prompts disponibles.

    Returns:
        Lista de prompts
    """
    manager = get_mcp_manager()
    prompts = manager.get_prompts_list()
    return {"prompts": prompts, "total": len(prompts)}


# === Endpoints de Utilidad ===

@router.get("/claude-config")
async def get_claude_config():
    """
    Genera la configuración JSON para usar con Claude Code.

    Returns:
        Configuración JSON para copiar a claude-code
    """
    manager = get_mcp_manager()
    config_json = manager.generate_claude_config()
    return {
        "config": config_json,
        "instructions": "Copiar este JSON a ~/.config/claude-code/mcp.json"
    }
