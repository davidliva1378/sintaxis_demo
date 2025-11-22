#!/usr/bin/env python3
"""
Servidor MCP (Model Context Protocol) para Sistema Sintaxis.

Expone las herramientas de ToolsService a traves del protocolo MCP
para integracion con Claude Code y otros clientes MCP.

Uso:
    python sintaxis_mcp_server.py

Configuracion en Claude Code:
    {
      "mcpServers": {
        "sintaxis": {
          "command": "python",
          "args": ["/path/to/sintaxis_mcp_server.py"],
          "env": {
            "MYSQL_PASSWORD": "tu_password"
          }
        }
      }
    }
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Any

# Agregar path del proyecto
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(project_root))

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("Error: MCP no esta instalado. Ejecutar: pip install mcp", file=sys.stderr)
    sys.exit(1)

from application.services.ia.tools_service import ToolsService

# Crear servidor MCP
app = Server("sintaxis")

# Instancia del servicio de tools
tools_service = ToolsService()


def serialize_result(result: Any) -> str:
    """Serializa resultado a JSON, manejando tipos especiales."""
    def default_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return str(obj)

    return json.dumps(result, default=default_serializer, ensure_ascii=False, indent=2)


@app.list_tools()
async def list_tools():
    """Lista todas las herramientas disponibles."""
    return [
        # === EXPEDIENTES ===
        Tool(
            name="contar_expedientes",
            description="Cuenta el total de expedientes con filtros opcionales por estado, dependencia y fechas",
            inputSchema={
                "type": "object",
                "properties": {
                    "estado": {"type": "string", "description": "Estado: activo, pausado, archivado"},
                    "dependencia": {"type": "string", "description": "Juzgado/dependencia"},
                    "desde": {"type": "string", "format": "date", "description": "Fecha desde (YYYY-MM-DD)"},
                    "hasta": {"type": "string", "format": "date", "description": "Fecha hasta (YYYY-MM-DD)"}
                }
            }
        ),
        Tool(
            name="listar_expedientes",
            description="Lista expedientes con paginacion y filtros por estado, dependencia, prioridad",
            inputSchema={
                "type": "object",
                "properties": {
                    "estado": {"type": "string"},
                    "dependencia": {"type": "string"},
                    "prioridad": {"type": "string", "enum": ["alta", "media", "baja"]},
                    "limite": {"type": "integer", "default": 20},
                    "offset": {"type": "integer", "default": 0}
                }
            }
        ),
        Tool(
            name="obtener_expediente",
            description="Obtiene detalle completo de un expediente por su numero (ej: FPO-006767-2025)",
            inputSchema={
                "type": "object",
                "properties": {
                    "numero": {"type": "string", "description": "Numero del expediente"}
                },
                "required": ["numero"]
            }
        ),
        Tool(
            name="buscar_expedientes",
            description="Busca expedientes por texto en numero o caratula",
            inputSchema={
                "type": "object",
                "properties": {
                    "texto": {"type": "string", "description": "Texto a buscar"},
                    "limite": {"type": "integer", "default": 20}
                },
                "required": ["texto"]
            }
        ),
        Tool(
            name="expedientes_recientes",
            description="Obtiene expedientes con actividad reciente en los ultimos N dias",
            inputSchema={
                "type": "object",
                "properties": {
                    "dias": {"type": "integer", "default": 7},
                    "limite": {"type": "integer", "default": 20}
                }
            }
        ),
        Tool(
            name="expedientes_por_dependencia",
            description="Agrupa expedientes por juzgado/dependencia con conteos",
            inputSchema={"type": "object", "properties": {}}
        ),

        # === ACTUACIONES ===
        Tool(
            name="listar_actuaciones",
            description="Lista actuaciones de un expediente, opcionalmente filtradas por tipo y fechas",
            inputSchema={
                "type": "object",
                "properties": {
                    "expediente_numero": {"type": "string", "description": "Numero del expediente"},
                    "tipo": {"type": "string", "description": "Tipo de actuacion"},
                    "desde": {"type": "string", "format": "date"},
                    "hasta": {"type": "string", "format": "date"},
                    "limite": {"type": "integer", "default": 50}
                },
                "required": ["expediente_numero"]
            }
        ),
        Tool(
            name="buscar_actuaciones",
            description="Busca actuaciones por texto en titulo o contenido",
            inputSchema={
                "type": "object",
                "properties": {
                    "texto": {"type": "string"},
                    "expediente_numero": {"type": "string"},
                    "limite": {"type": "integer", "default": 20}
                },
                "required": ["texto"]
            }
        ),
        Tool(
            name="obtener_texto_actuacion",
            description="Obtiene el texto extraido de una actuacion por su ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "actuacion_id": {"type": "string"}
                },
                "required": ["actuacion_id"]
            }
        ),
        Tool(
            name="actuaciones_por_tipo",
            description="Agrupa actuaciones por tipo con conteos y utilidad promedio",
            inputSchema={
                "type": "object",
                "properties": {
                    "expediente_numero": {"type": "string"}
                }
            }
        ),
        Tool(
            name="actuaciones_con_texto",
            description="Lista actuaciones que tienen texto extraido de PDF",
            inputSchema={
                "type": "object",
                "properties": {
                    "expediente_numero": {"type": "string"},
                    "limite": {"type": "integer", "default": 20}
                },
                "required": ["expediente_numero"]
            }
        ),

        # === VENCIMIENTOS ===
        Tool(
            name="vencimientos_pendientes",
            description="Lista vencimientos pendientes, opcionalmente de un expediente especifico",
            inputSchema={
                "type": "object",
                "properties": {
                    "expediente_numero": {"type": "string"},
                    "limite": {"type": "integer", "default": 50}
                }
            }
        ),
        Tool(
            name="vencimientos_urgentes",
            description="Obtiene vencimientos proximos a vencer en los proximos N dias",
            inputSchema={
                "type": "object",
                "properties": {
                    "dias": {"type": "integer", "default": 7},
                    "limite": {"type": "integer", "default": 20}
                }
            }
        ),
        Tool(
            name="vencimientos_vencidos",
            description="Lista vencimientos que ya pasaron su fecha limite",
            inputSchema={
                "type": "object",
                "properties": {
                    "expediente_numero": {"type": "string"},
                    "limite": {"type": "integer", "default": 20}
                }
            }
        ),
        Tool(
            name="resumen_vencimientos",
            description="Estadisticas generales de vencimientos: pendientes, cumplidos, vencidos, urgentes",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="proximos_vencimientos",
            description="Calendario de proximos vencimientos agrupados por dia, semana o mes",
            inputSchema={
                "type": "object",
                "properties": {
                    "dias": {"type": "integer", "default": 30},
                    "agrupar_por": {"type": "string", "enum": ["dia", "semana", "mes"], "default": "semana"}
                }
            }
        ),

        # === ENTIDADES NER ===
        Tool(
            name="listar_entidades",
            description="Lista entidades extraidas (personas, organizaciones, etc) de un expediente",
            inputSchema={
                "type": "object",
                "properties": {
                    "expediente_numero": {"type": "string"},
                    "tipo": {"type": "string", "description": "PERSONA, ORGANIZACION, etc"},
                    "limite": {"type": "integer", "default": 100}
                },
                "required": ["expediente_numero"]
            }
        ),
        Tool(
            name="buscar_entidades",
            description="Busca entidades por valor en todos los expedientes",
            inputSchema={
                "type": "object",
                "properties": {
                    "valor": {"type": "string"},
                    "tipo": {"type": "string"},
                    "limite": {"type": "integer", "default": 20}
                },
                "required": ["valor"]
            }
        ),
        Tool(
            name="personas_expediente",
            description="Obtiene personas mencionadas en un expediente con roles inferidos",
            inputSchema={
                "type": "object",
                "properties": {
                    "expediente_numero": {"type": "string"},
                    "score_minimo": {"type": "number", "default": 0.5}
                },
                "required": ["expediente_numero"]
            }
        ),
        Tool(
            name="entidades_por_tipo",
            description="Agrupa entidades por tipo con conteos",
            inputSchema={
                "type": "object",
                "properties": {
                    "expediente_numero": {"type": "string"}
                }
            }
        ),
        Tool(
            name="estadisticas_entidades",
            description="Estadisticas generales de entidades extraidas en el sistema",
            inputSchema={"type": "object", "properties": {}}
        ),

        # === ESTADISTICAS ===
        Tool(
            name="estadisticas_sistema",
            description="Obtiene estadisticas generales del sistema: expedientes, actuaciones, vencimientos, entidades",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="estadisticas_expediente",
            description="Obtiene estadisticas detalladas de un expediente especifico",
            inputSchema={
                "type": "object",
                "properties": {
                    "expediente_numero": {"type": "string"}
                },
                "required": ["expediente_numero"]
            }
        ),
        Tool(
            name="estadisticas_procesamiento",
            description="Estadisticas de procesamiento de IA: clasificacion, NER, utilidad",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="actividad_reciente",
            description="Timeline de actividad reciente en el sistema (actuaciones y vencimientos)",
            inputSchema={
                "type": "object",
                "properties": {
                    "dias": {"type": "integer", "default": 7},
                    "limite": {"type": "integer", "default": 50}
                }
            }
        ),

        # === ANALISIS ===
        Tool(
            name="duplicados_detectados",
            description="Lista actuaciones marcadas como posibles duplicados",
            inputSchema={
                "type": "object",
                "properties": {
                    "expediente_numero": {"type": "string"},
                    "limite": {"type": "integer", "default": 20}
                }
            }
        ),
        Tool(
            name="clasificacion_ia",
            description="Obtiene resultados de clasificacion IA de actuaciones de un expediente",
            inputSchema={
                "type": "object",
                "properties": {
                    "expediente_numero": {"type": "string"}
                },
                "required": ["expediente_numero"]
            }
        ),
        Tool(
            name="actuaciones_importantes",
            description="Obtiene actuaciones de alta utilidad (importantes)",
            inputSchema={
                "type": "object",
                "properties": {
                    "expediente_numero": {"type": "string"},
                    "utilidad_minima": {"type": "string", "enum": ["alta", "media"], "default": "alta"},
                    "limite": {"type": "integer", "default": 20}
                }
            }
        ),
        Tool(
            name="resumen_expediente",
            description="Genera resumen completo de un expediente con actuaciones, vencimientos y entidades",
            inputSchema={
                "type": "object",
                "properties": {
                    "expediente_numero": {"type": "string"},
                    "incluir_actuaciones": {"type": "boolean", "default": True},
                    "incluir_vencimientos": {"type": "boolean", "default": True},
                    "incluir_entidades": {"type": "boolean", "default": True}
                },
                "required": ["expediente_numero"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Ejecuta una herramienta y retorna el resultado."""
    try:
        # Convertir fechas string a datetime
        for key in ['desde', 'hasta']:
            if key in arguments and arguments[key]:
                arguments[key] = datetime.fromisoformat(arguments[key])

        # Ejecutar tool
        result = tools_service.execute_tool(name, arguments)

        # Serializar resultado
        content = serialize_result(result)

        return [TextContent(type="text", text=content)]

    except ValueError as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error ejecutando {name}: {str(e)}")]


async def main():
    """Inicia el servidor MCP."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
