"""MCP Server - Model Context Protocol Server for Sistema PJN v6.

Este módulo implementa un servidor MCP (Model Context Protocol) que expone
las capacidades del sistema a modelos de lenguaje (LLMs) a través de herramientas
estructuradas.

MCP permite que los LLMs:
- Extraigan expedientes del PJN
- Filtren y gestionen expedientes
- Creen workspaces y organicen información
- Monitoreen cambios automáticamente

Uso:
    ```bash
    # Iniciar servidor MCP
    python -m presentation.api.mcp.server
    ```

Protocolo:
    - Basado en JSON-RPC 2.0
    - Comunicación vía stdio o HTTP
    - Herramientas tipadas con JSON Schema
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from typing import Any

from infrastructure.config import get_settings
from infrastructure.di_container import get_container

from .tools import (
    crear_workspaces_tool,
    extraer_expedientes_tool,
    filtrar_expedientes_tool,
    listar_expedientes_tool,
    monitorear_expedientes_tool,
    obtener_expediente_tool,
)

logger = logging.getLogger(__name__)


class MCPServer:
    """Servidor MCP para Sistema PJN v6.

    Implementa el protocolo MCP para exponer las capacidades del sistema
    a modelos de lenguaje.
    """

    def __init__(self):
        """Inicializa el servidor MCP."""
        self.settings = get_settings()
        self.container = get_container()

        # Registro de herramientas disponibles
        self.tools = {
            "extraer_expedientes": extraer_expedientes_tool,
            "filtrar_expedientes": filtrar_expedientes_tool,
            "listar_expedientes": listar_expedientes_tool,
            "obtener_expediente": obtener_expediente_tool,
            "crear_workspaces": crear_workspaces_tool,
            "monitorear_expedientes": monitorear_expedientes_tool,
        }

        # Aplicar configuración MCP
        self.mcp_config = self.settings.mcp
        logger.info(
            f"MCP Server inicializado: {self.mcp_config.server_name} | "
            f"Mode: {self.mcp_config.mode} | Port: {self.mcp_config.puerto} | "
            f"Tools: {len(self.tools)}"
        )

    def get_tools_schema(self) -> list[dict[str, Any]]:
        """Obtiene el schema JSON de todas las herramientas disponibles.

        Returns:
            Lista de schemas de herramientas
        """
        return [
            {
                "name": "extraer_expedientes",
                "description": "Extrae la lista completa de expedientes del Portal Judicial Nacional",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "usuario": {"type": "string", "description": "Usuario del PJN (CUIL)"},
                        "contrasena": {"type": "string", "description": "Contraseña del PJN"},
                        "headless": {"type": "boolean", "description": "Ejecutar navegador sin interfaz", "default": True},
                        "guardar_en": {"type": "string", "description": "Path donde guardar JSON"},
                    },
                },
            },
            {
                "name": "filtrar_expedientes",
                "description": "Filtra expedientes según selección del usuario o criterios automáticos",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "numeros_seleccionados": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Lista de números de expedientes",
                        },
                        "origen": {"type": "string", "description": "Path del JSON origen (base)"},
                        "destino": {"type": "string", "description": "Path del JSON destino (sistema)"},
                        "incluir_activos": {"type": "boolean", "description": "Incluir expedientes activos automáticamente", "default": False},
                        "dias_actividad": {"type": "integer", "description": "Días para considerar activo", "default": 30},
                    },
                    "required": ["numeros_seleccionados", "origen"],
                },
            },
            {
                "name": "listar_expedientes",
                "description": "Lista expedientes almacenados en el sistema",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "activos_solo": {"type": "boolean", "description": "Solo expedientes activos", "default": False},
                        "dias": {"type": "integer", "description": "Días para considerar activo", "default": 30},
                    },
                },
            },
            {
                "name": "obtener_expediente",
                "description": "Obtiene detalles de un expediente específico por número",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "numero": {"type": "string", "description": "Número del expediente (ej: CNM 0001/2024)"},
                    },
                    "required": ["numero"],
                },
            },
            {
                "name": "crear_workspaces",
                "description": "Crea workspaces (directorios organizados) para expedientes del sistema",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "archivo_sistema": {"type": "string", "description": "Path del JSON sistema"},
                        "workspaces_dir": {"type": "string", "description": "Directorio base para workspaces"},
                        "extraer_actuaciones": {"type": "boolean", "description": "Extraer actuaciones al crear", "default": False},
                        "descargar_archivos": {"type": "boolean", "description": "Descargar archivos adjuntos", "default": False},
                    },
                    "required": ["archivo_sistema"],
                },
            },
            {
                "name": "monitorear_expedientes",
                "description": "Monitorea expedientes del sistema para detectar cambios (verificación única)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "archivo_sistema": {"type": "string", "description": "Path del JSON sistema"},
                        "workspaces_dir": {"type": "string", "description": "Directorio base para workspaces"},
                        "intervalo_minutos": {"type": "integer", "description": "Intervalo de verificación", "default": 60},
                        "notificar": {"type": "boolean", "description": "Enviar notificaciones", "default": True},
                    },
                    "required": ["archivo_sistema"],
                },
            },
        ]

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Ejecuta una herramienta.

        Args:
            name: Nombre de la herramienta
            arguments: Argumentos para la herramienta

        Returns:
            Resultado de la herramienta

        Raises:
            ValueError: Si la herramienta no existe
        """
        if name not in self.tools:
            raise ValueError(f"Herramienta desconocida: {name}")

        tool_func = self.tools[name]
        logger.info(f"Ejecutando herramienta: {name}")

        try:
            result = await tool_func(self.container, **arguments)
            return {"success": True, "result": result}
        except Exception as e:
            logger.exception(f"Error en herramienta {name}")
            return {"success": False, "error": str(e), "error_type": type(e).__name__}

    async def handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Maneja una petición JSON-RPC.

        Args:
            request: Petición JSON-RPC

        Returns:
            Respuesta JSON-RPC
        """
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        logger.debug(f"Request: method={method}, id={request_id}")

        # Métodos del protocolo MCP
        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": self.get_tools_schema()},
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            tool_arguments = params.get("arguments", {})

            result = await self.call_tool(tool_name, tool_arguments)

            return {"jsonrpc": "2.0", "id": request_id, "result": result}

        elif method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "1.0",
                    "serverInfo": {
                        "name": self.mcp_config.server_name,
                        "version": "6.0.0",
                    },
                    "capabilities": {
                        "tools": True,
                        "resources": False,
                        "prompts": False,
                    },
                },
            }

        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Método desconocido: {method}"},
            }

    async def run_stdio(self):
        """Ejecuta el servidor en modo stdio (lectura de stdin, escritura a stdout)."""
        logger.info("MCP Server iniciado en modo stdio")

        while True:
            try:
                # Leer línea de stdin
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)

                if not line:
                    break

                # Parsear JSON
                request = json.loads(line.strip())

                # Procesar petición
                response = await self.handle_request(request)

                # Escribir respuesta a stdout
                print(json.dumps(response), flush=True)

            except json.JSONDecodeError as e:
                logger.error(f"Error parseando JSON: {e}")
                continue

            except KeyboardInterrupt:
                logger.info("Servidor detenido por usuario")
                break

            except Exception as e:
                logger.exception("Error procesando petición")
                continue

        logger.info("MCP Server cerrado")


async def main():
    """Función principal para iniciar el servidor MCP."""
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("mcp_server.log"), logging.StreamHandler(sys.stderr)],
    )

    # Crear servidor
    server = MCPServer()

    # Ejecutar en modo configurado
    if server.mcp_config.mode == "stdio":
        logger.info("Iniciando servidor en modo STDIO")
        await server.run_stdio()
    elif server.mcp_config.mode == "http":
        logger.warning("Modo HTTP no implementado aún, usando stdio")
        logger.info(f"Puerto configurado: {server.mcp_config.puerto}")
        await server.run_stdio()
    else:
        logger.error(f"Modo desconocido: {server.mcp_config.mode}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
