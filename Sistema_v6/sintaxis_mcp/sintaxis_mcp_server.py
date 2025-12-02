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
    from mcp.types import Tool, TextContent, Resource, ResourceTemplate, Prompt, PromptMessage, GetPromptResult
    MCP_INSTALLED = True
except ImportError:
    # Si MCP no esta instalado, definimos mocks para que el archivo se pueda importar
    # sin romper el backend. El servidor no funcionara, pero la API no crasheara.
    print("Advertencia: MCP no esta instalado. El servidor MCP no funcionara.", file=sys.stderr)
    MCP_INSTALLED = False
    
    class Mock:
        def __init__(self, name="Mock"):
            self._name = name
        
        def __call__(self, *args, **kwargs):
            # Si se usa como decorador (1 argumento callable y sin kwargs), retornar la funcion original
            if len(args) == 1 and not kwargs and callable(args[0]) and not isinstance(args[0], Mock):
                return args[0]
            return Mock(name=f"{self._name}()")
            
        def __getattr__(self, item):
            return Mock(name=f"{self._name}.{item}")
            
        def __str__(self):
            return "MockValue"
            
        def __iter__(self):
            # Retornar un iterador con un elemento Mock para que los loops funcionen
            return iter([Mock(name=f"{self._name}_item")])
            
        def __await__(self):
            async def _coro(): return self
            return _coro().__await__()
            
        async def __aenter__(self): return (Mock(), Mock())
        async def __aexit__(self, exc_type, exc_val, exc_tb): pass
        
    Server = Mock
    stdio_server = Mock
    Tool = Mock
    TextContent = Mock
    Resource = Mock
    ResourceTemplate = Mock
    Prompt = Mock
    PromptMessage = Mock
    GetPromptResult = Mock

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


# ============================================================================
# RESOURCES
# ============================================================================

@app.list_resources()
async def list_resources() -> list[Resource]:
    """Lista los recursos disponibles."""
    # Nota: En un sistema real con miles de expedientes, no listariamos todos aqui.
    # Listamos ejemplos o categorias.
    return [
        Resource(
            uri="expediente://listado/recientes",
            name="Expedientes Recientes",
            mimeType="application/json",
            description="Lista de expedientes con actividad reciente"
        )
    ]

@app.read_resource()
async def read_resource(uri: str) -> str:
    """Lee un recurso especifico."""
    parsed = uri.split("://")
    if len(parsed) != 2:
        raise ValueError(f"URI invalida: {uri}")
    
    scheme, path = parsed
    
    # === EXPEDIENTES ===
    if scheme == "expediente":
        # expediente://{numero}/resumen
        parts = path.split("/")
        numero = parts[0]
        
        if numero == "listado" and parts[1] == "recientes":
            result = tools_service.expedientes_recientes(limite=10)
            return serialize_result(result)
            
        if len(parts) > 1 and parts[1] == "resumen":
            # Obtener datos completos
            datos = tools_service.obtener_expediente(numero)
            if not datos:
                raise ValueError(f"Expediente no encontrado: {numero}")
            
            # Formatear como Markdown para facil lectura del LLM
            md = f"# Expediente {datos['numero_normalizado']}\n\n"
            md += f"**Caratula**: {datos['caratula']}\n"
            md += f"**Dependencia**: {datos['dependencia']}\n"
            md += f"**Estado**: {datos.get('estado_monitoreo', 'N/A')}\n\n"
            
            # Actuaciones recientes
            actuaciones = tools_service.listar_actuaciones(numero, limite=5)
            md += "## Ultimas Actuaciones\n"
            for act in actuaciones:
                md += f"- **{act['fecha']}** - {act['titulo']} (ID: {act['id']})\n"
                
            return md

    # === ACTUACIONES ===
    elif scheme == "actuacion":
        # actuacion://{id}/texto
        parts = path.split("/")
        act_id = parts[0]
        accion = parts[1] if len(parts) > 1 else "texto"
        
        if accion == "texto":
            datos = tools_service.obtener_texto_actuacion(act_id)
            if not datos:
                raise ValueError(f"Actuacion no encontrada: {act_id}")
            
            texto = datos.get('texto') or "Sin texto extraido."
            return texto
            
        elif accion == "contexto":
            # Texto + Metadata + Entidades
            datos = tools_service.obtener_texto_actuacion(act_id)
            if not datos:
                raise ValueError(f"Actuacion no encontrada: {act_id}")
                
            md = f"# Actuacion {act_id}\n"
            md += f"**Fecha**: {datos['fecha']}\n"
            md += f"**Titulo**: {datos['titulo']}\n"
            md += f"**Tipo**: {datos['tipo']}\n\n"
            md += "## Contenido\n"
            md += f"{datos.get('texto', 'Sin texto')}\n"
            
            return md

    raise ValueError(f"Recurso no encontrado: {uri}")


# ============================================================================
# PROMPTS
# ============================================================================

@app.list_prompts()
async def list_prompts():
    """Lista los prompts predefinidos."""
    from mcp.types import Prompt
    
    return [
        Prompt(
            name="analizar_apelacion",
            description="Analiza una sentencia para fundamentar una apelacion",
            arguments=[
                {"name": "actuacion_id", "description": "ID de la sentencia a apelar", "required": True}
            ]
        ),
        Prompt(
            name="contestar_agravios",
            description="Genera estructura para contestar agravios",
            arguments=[
                {"name": "actuacion_id", "description": "ID del escrito de expresion de agravios", "required": True}
            ]
        ),
        Prompt(
            name="verificar_vencimientos",
            description="Revisa vencimientos pendientes y sugiere acciones",
            arguments=[
                {"name": "expediente_numero", "description": "Numero del expediente", "required": True}
            ]
        )
    ]

@app.get_prompt()
async def get_prompt(name: str, arguments: dict = None):
    """Obtiene un prompt especifico con contexto cargado."""
    from mcp.types import PromptMessage, GetPromptResult
    
    arguments = arguments or {}
    
    if name == "analizar_apelacion":
        act_id = arguments.get("actuacion_id")
        if not act_id:
            raise ValueError("Falta actuacion_id")
            
        # Obtener texto de la sentencia
        datos = tools_service.obtener_texto_actuacion(act_id)
        if not datos:
            raise ValueError(f"Actuacion {act_id} no encontrada")
            
        texto = datos.get('texto', 'Sin texto')
        
        prompt_text = f"""Actúa como un abogado experto en derecho procesal argentino.
Analiza la siguiente sentencia y estructura los fundamentos para una apelación.

SENTENCIA (ID: {act_id}):
{texto}

TAREA:
1. Identifica los puntos resolutivos que causan agravio.
2. Señala errores in iudicando o in procedendo.
3. Esboza los argumentos principales para el memorial."""

        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=prompt_text
                )
            ]
        )

    elif name == "contestar_agravios":
        act_id = arguments.get("actuacion_id")
        if not act_id:
            raise ValueError("Falta actuacion_id")
            
        datos = tools_service.obtener_texto_actuacion(act_id)
        if not datos:
            raise ValueError(f"Actuacion {act_id} no encontrada")
            
        texto = datos.get('texto', 'Sin texto')
        
        prompt_text = f"""Actúa como un abogado experto.
Debemos contestar la expresión de agravios de la contraparte.

EXPRESIÓN DE AGRAVIOS (ID: {act_id}):
{texto}

TAREA:
1. Resume los agravios planteados.
2. Refuta cada agravio punto por punto.
3. Cita jurisprudencia aplicable (sugerida)."""

        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=prompt_text
                )
            ]
        )

    elif name == "verificar_vencimientos":
        exp_num = arguments.get("expediente_numero")
        if not exp_num:
            raise ValueError("Falta expediente_numero")
            
        vencimientos = tools_service.vencimientos_pendientes(expediente_numero=exp_num)
        
        contexto = "VENCIMIENTOS PENDIENTES:\n"
        for v in vencimientos:
            contexto += f"- {v['fecha_vencimiento']}: {v['descripcion']} (Estado: {v['estado']})\n"
            
        prompt_text = f"""Analiza los siguientes vencimientos del expediente {exp_num} y sugiere prioridades.

{contexto}

TAREA:
1. Identifica los plazos fatales inminentes.
2. Sugiere el orden de trabajo.
3. Alerta sobre cualquier inconsistencia."""

        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=prompt_text
                )
            ]
        )

    raise ValueError(f"Prompt no encontrado: {name}")


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

        # === MONITOREO ===
        Tool(
            name="estado_monitoreo",
            description="Obtiene el estado actual del sistema de monitoreo: si está activo, frecuencia, cambios pendientes",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="listar_expedientes_monitoreados",
            description="Lista los expedientes que están siendo monitoreados para detectar cambios",
            inputSchema={
                "type": "object",
                "properties": {
                    "solo_activos": {"type": "boolean", "default": False, "description": "Solo expedientes con monitoreo activo"},
                    "limite": {"type": "integer", "default": 50}
                }
            }
        ),
        Tool(
            name="listar_cambios_monitoreo",
            description="Lista los cambios detectados por el sistema de monitoreo (nuevas actuaciones, cambios de estado, etc)",
            inputSchema={
                "type": "object",
                "properties": {
                    "solo_no_leidos": {"type": "boolean", "default": False},
                    "tipo_cambio": {"type": "string", "description": "nueva_actuacion, cambio_estado, etc"},
                    "expediente_numero": {"type": "string"},
                    "limite": {"type": "integer", "default": 50}
                }
            }
        ),
        Tool(
            name="estadisticas_monitoreo",
            description="Obtiene estadísticas del sistema de monitoreo: total expedientes, cambios detectados, etc",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="sincronizar_expedientes_monitoreo",
            description="Sincroniza todos los expedientes del sistema principal al sistema de monitoreo",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="agregar_expediente_monitoreo",
            description="Agrega un expediente específico al sistema de monitoreo",
            inputSchema={
                "type": "object",
                "properties": {
                    "expediente_numero": {"type": "string", "description": "Número del expediente a monitorear"},
                    "prioridad": {"type": "string", "enum": ["baja", "media", "alta"], "default": "media"},
                    "notas": {"type": "string", "description": "Notas opcionales"}
                },
                "required": ["expediente_numero"]
            }
        ),
        Tool(
            name="pausar_expediente_monitoreo",
            description="Pausa el monitoreo de un expediente específico",
            inputSchema={
                "type": "object",
                "properties": {
                    "expediente_numero": {"type": "string"}
                },
                "required": ["expediente_numero"]
            }
        ),
        Tool(
            name="reanudar_expediente_monitoreo",
            description="Reanuda el monitoreo de un expediente que fue pausado",
            inputSchema={
                "type": "object",
                "properties": {
                    "expediente_numero": {"type": "string"}
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
