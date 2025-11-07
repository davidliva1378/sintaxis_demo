"""Presentation package - Presentation Layer.

Este paquete contiene todas las interfaces de usuario del sistema.

Módulos:
    - api/rest: REST API (FastAPI)
    - api/mcp: MCP Server (Model Context Protocol)
    - cli: Command Line Interface
    - web: Web UI (React/Vue.js)

Principios:
    - Depende de Application (use cases y services)
    - No contiene lógica de negocio
    - Múltiples interfaces para el mismo core
"""

__version__ = "6.0.0"
