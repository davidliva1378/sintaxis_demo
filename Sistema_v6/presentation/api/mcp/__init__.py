"""MCP Module - Model Context Protocol Server for Sistema PJN v6.

Este módulo implementa un servidor MCP (Model Context Protocol) que permite
a los modelos de lenguaje (LLMs) interactuar con el Sistema PJN v6 mediante
herramientas estructuradas.

Capacidades:
    - Extracción de expedientes del PJN
    - Filtrado y gestión de expedientes
    - Creación de workspaces organizados
    - Monitoreo de cambios automático
    - Consultas sobre expedientes específicos

Uso:
    ```bash
    # Iniciar servidor MCP en modo stdio
    python -m presentation.api.mcp.server

    # O importar programáticamente
    from presentation.api.mcp.server import MCPServer
    server = MCPServer()
    await server.run_stdio()
    ```

Protocolo:
    - JSON-RPC 2.0 sobre stdio
    - Herramientas tipadas con JSON Schema
    - Compatible con Claude Desktop, Cline, y otros clientes MCP

Estructura:
    - server.py: Servidor MCP principal
    - tools/: Herramientas individuales para cada capacidad
    - prompts/: Prompts predefinidos (futuro)
    - resources/: Recursos contextuales (futuro)
"""

from .server import MCPServer

__all__ = ["MCPServer"]
