"""
Registro Unificado de Tools MCP.

Proporciona una única fuente de verdad para las definiciones de tools
que se usan en los servidores MCP (STDIO y SSE) y en la API REST.

Las 37 tools están organizadas en 7 categorías:
1. Expedientes (6): contar, listar, obtener, buscar, por_dependencia, recientes
2. Actuaciones (5): listar, buscar, por_tipo, con_texto, obtener_texto
3. Vencimientos (5): pendientes, urgentes, vencidos, proximos, resumen
4. Entidades NER (5): listar, buscar, por_tipo, estadisticas, personas
5. Estadísticas (4): sistema, expediente, procesamiento, actividad
6. Análisis (4): duplicados, clasificacion_ia, importantes, resumen
7. Monitoreo (8): estado, listar, cambios, estadisticas, agregar, pausar, reanudar, sincronizar
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ToolCategory(Enum):
    """Categorías de tools disponibles."""
    EXPEDIENTES = "expedientes"
    ACTUACIONES = "actuaciones"
    VENCIMIENTOS = "vencimientos"
    ENTIDADES = "entidades"
    ESTADISTICAS = "estadisticas"
    ANALISIS = "analisis"
    MONITOREO = "monitoreo"


@dataclass
class ToolDefinition:
    """Definición de una tool MCP."""
    name: str
    description: str
    category: ToolCategory
    parameters: Dict[str, Any]
    required_params: List[str] = field(default_factory=list)

    def to_mcp_format(self) -> Dict[str, Any]:
        """Convierte a formato MCP (inputSchema)."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": self.parameters,
                "required": self.required_params
            }
        }

    def to_openai_format(self) -> Dict[str, Any]:
        """Convierte a formato OpenAI function calling."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": self.parameters,
                "required": self.required_params
            }
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario simple."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "parameters": self.parameters,
            "required": self.required_params
        }


class ToolsRegistry:
    """
    Registro singleton de todas las tools MCP disponibles.

    Uso:
        registry = ToolsRegistry()

        # Obtener todas las definiciones
        all_tools = registry.get_all_definitions()

        # Obtener en formato MCP
        mcp_tools = registry.get_mcp_definitions()

        # Obtener por categoría
        exp_tools = registry.get_by_category(ToolCategory.EXPEDIENTES)

        # Ejecutar tool
        result = registry.execute("listar_expedientes", {"limite": 10})
    """

    _instance = None
    _tools: Dict[str, ToolDefinition] = {}
    _service = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._tools = {}
        self._register_all_tools()

    def _get_service(self):
        """Obtiene instancia lazy del ToolsService."""
        if self._service is None:
            from application.services.ia.tools_service import ToolsService
            self._service = ToolsService()
        return self._service

    def _register_all_tools(self):
        """Registra todas las 37 tools."""

        # =====================================================
        # CATEGORIA 1: EXPEDIENTES (6 tools)
        # =====================================================

        self._register(ToolDefinition(
            name="contar_expedientes",
            description="Cuenta el total de expedientes con filtros opcionales por estado, dependencia o fechas",
            category=ToolCategory.EXPEDIENTES,
            parameters={
                "estado": {
                    "type": "string",
                    "description": "Filtrar por estado: activo, pausado, archivado",
                    "enum": ["activo", "pausado", "archivado"]
                },
                "dependencia": {
                    "type": "string",
                    "description": "Filtrar por juzgado/dependencia (búsqueda parcial)"
                },
                "desde": {
                    "type": "string",
                    "format": "date",
                    "description": "Fecha mínima de creación (YYYY-MM-DD)"
                },
                "hasta": {
                    "type": "string",
                    "format": "date",
                    "description": "Fecha máxima de creación (YYYY-MM-DD)"
                }
            }
        ))

        self._register(ToolDefinition(
            name="listar_expedientes",
            description="Lista expedientes con paginación y filtros. Retorna número, carátula, dependencia y estadísticas",
            category=ToolCategory.EXPEDIENTES,
            parameters={
                "estado": {
                    "type": "string",
                    "description": "Filtrar por estado",
                    "enum": ["activo", "pausado", "archivado"],
                    "default": "activo"
                },
                "dependencia": {
                    "type": "string",
                    "description": "Filtrar por juzgado"
                },
                "prioridad": {
                    "type": "string",
                    "description": "Filtrar por prioridad",
                    "enum": ["alta", "media", "baja"]
                },
                "limite": {
                    "type": "integer",
                    "description": "Máximo de resultados",
                    "default": 20
                },
                "offset": {
                    "type": "integer",
                    "description": "Saltar N resultados",
                    "default": 0
                }
            }
        ))

        self._register(ToolDefinition(
            name="obtener_expediente",
            description="Obtiene detalle completo de un expediente por su número. Incluye estadísticas, conteos y fechas",
            category=ToolCategory.EXPEDIENTES,
            parameters={
                "numero": {
                    "type": "string",
                    "description": "Número del expediente (ej: FPO-006767-2025 o FPO_006767_2025)"
                }
            },
            required_params=["numero"]
        ))

        self._register(ToolDefinition(
            name="buscar_expedientes",
            description="Busca expedientes por texto en número o carátula. Soporta búsqueda parcial",
            category=ToolCategory.EXPEDIENTES,
            parameters={
                "texto": {
                    "type": "string",
                    "description": "Texto a buscar en número o carátula"
                },
                "limite": {
                    "type": "integer",
                    "description": "Máximo de resultados",
                    "default": 20
                }
            },
            required_params=["texto"]
        ))

        self._register(ToolDefinition(
            name="expedientes_por_dependencia",
            description="Agrupa expedientes por dependencia/juzgado con conteos de activos",
            category=ToolCategory.EXPEDIENTES,
            parameters={
                "limite_por_dep": {
                    "type": "integer",
                    "description": "Máximo de expedientes a mostrar por dependencia",
                    "default": 5
                }
            }
        ))

        self._register(ToolDefinition(
            name="expedientes_recientes",
            description="Obtiene expedientes con actividad reciente (actuaciones en los últimos N días)",
            category=ToolCategory.EXPEDIENTES,
            parameters={
                "dias": {
                    "type": "integer",
                    "description": "Días hacia atrás a considerar",
                    "default": 7
                },
                "limite": {
                    "type": "integer",
                    "description": "Máximo de resultados",
                    "default": 20
                }
            }
        ))

        # =====================================================
        # CATEGORIA 2: ACTUACIONES (5 tools)
        # =====================================================

        self._register(ToolDefinition(
            name="listar_actuaciones",
            description="Lista actuaciones de un expediente ordenadas por fecha. Incluye tipo clasificado por IA",
            category=ToolCategory.ACTUACIONES,
            parameters={
                "expediente_numero": {
                    "type": "string",
                    "description": "Número del expediente"
                },
                "tipo": {
                    "type": "string",
                    "description": "Filtrar por tipo de actuación (sentencia, auto, etc)"
                },
                "desde": {
                    "type": "string",
                    "format": "date",
                    "description": "Fecha mínima"
                },
                "hasta": {
                    "type": "string",
                    "format": "date",
                    "description": "Fecha máxima"
                },
                "limite": {
                    "type": "integer",
                    "description": "Máximo de resultados",
                    "default": 50
                }
            },
            required_params=["expediente_numero"]
        ))

        self._register(ToolDefinition(
            name="buscar_actuaciones",
            description="Busca actuaciones por texto en título o contenido PDF extraído",
            category=ToolCategory.ACTUACIONES,
            parameters={
                "texto": {
                    "type": "string",
                    "description": "Texto a buscar"
                },
                "expediente_numero": {
                    "type": "string",
                    "description": "Limitar a un expediente (opcional)"
                },
                "limite": {
                    "type": "integer",
                    "description": "Máximo de resultados",
                    "default": 20
                }
            },
            required_params=["texto"]
        ))

        self._register(ToolDefinition(
            name="actuaciones_por_tipo",
            description="Agrupa actuaciones por tipo con conteos y utilidad promedio",
            category=ToolCategory.ACTUACIONES,
            parameters={
                "expediente_numero": {
                    "type": "string",
                    "description": "Limitar a un expediente (opcional)"
                }
            }
        ))

        self._register(ToolDefinition(
            name="actuaciones_con_texto",
            description="Obtiene actuaciones que tienen texto extraído de PDF disponible",
            category=ToolCategory.ACTUACIONES,
            parameters={
                "expediente_numero": {
                    "type": "string",
                    "description": "Número del expediente"
                },
                "limite": {
                    "type": "integer",
                    "description": "Máximo de resultados",
                    "default": 20
                }
            },
            required_params=["expediente_numero"]
        ))

        self._register(ToolDefinition(
            name="obtener_texto_actuacion",
            description="Obtiene el texto completo extraído del PDF de una actuación",
            category=ToolCategory.ACTUACIONES,
            parameters={
                "actuacion_id": {
                    "type": "string",
                    "description": "ID de la actuación"
                }
            },
            required_params=["actuacion_id"]
        ))

        # =====================================================
        # CATEGORIA 3: VENCIMIENTOS (5 tools)
        # =====================================================

        self._register(ToolDefinition(
            name="vencimientos_pendientes",
            description="Lista vencimientos pendientes ordenados por fecha próxima",
            category=ToolCategory.VENCIMIENTOS,
            parameters={
                "expediente_numero": {
                    "type": "string",
                    "description": "Limitar a un expediente (opcional)"
                },
                "limite": {
                    "type": "integer",
                    "description": "Máximo de resultados",
                    "default": 50
                }
            }
        ))

        self._register(ToolDefinition(
            name="vencimientos_urgentes",
            description="Obtiene vencimientos próximos a vencer en los próximos N días",
            category=ToolCategory.VENCIMIENTOS,
            parameters={
                "dias": {
                    "type": "integer",
                    "description": "Días hacia adelante a considerar",
                    "default": 7
                },
                "limite": {
                    "type": "integer",
                    "description": "Máximo de resultados",
                    "default": 20
                }
            }
        ))

        self._register(ToolDefinition(
            name="vencimientos_vencidos",
            description="Lista vencimientos que ya pasaron su fecha límite",
            category=ToolCategory.VENCIMIENTOS,
            parameters={
                "expediente_numero": {
                    "type": "string",
                    "description": "Limitar a un expediente (opcional)"
                },
                "limite": {
                    "type": "integer",
                    "description": "Máximo de resultados",
                    "default": 20
                }
            }
        ))

        self._register(ToolDefinition(
            name="proximos_vencimientos",
            description="Calendario de próximos vencimientos agrupados por día, semana o mes",
            category=ToolCategory.VENCIMIENTOS,
            parameters={
                "dias": {
                    "type": "integer",
                    "description": "Días hacia adelante",
                    "default": 30
                },
                "agrupar_por": {
                    "type": "string",
                    "description": "Agrupación temporal",
                    "enum": ["dia", "semana", "mes"],
                    "default": "semana"
                }
            }
        ))

        self._register(ToolDefinition(
            name="resumen_vencimientos",
            description="Estadísticas generales de vencimientos: pendientes, cumplidos, vencidos, urgentes",
            category=ToolCategory.VENCIMIENTOS,
            parameters={}
        ))

        # =====================================================
        # CATEGORIA 4: ENTIDADES NER (5 tools)
        # =====================================================

        self._register(ToolDefinition(
            name="listar_entidades",
            description="Lista entidades (personas, organizaciones, etc) extraídas de un expediente",
            category=ToolCategory.ENTIDADES,
            parameters={
                "expediente_numero": {
                    "type": "string",
                    "description": "Número del expediente"
                },
                "tipo": {
                    "type": "string",
                    "description": "Filtrar por tipo: PERSONA, ORGANIZACION, FECHA, etc"
                },
                "limite": {
                    "type": "integer",
                    "description": "Máximo de resultados",
                    "default": 100
                }
            },
            required_params=["expediente_numero"]
        ))

        self._register(ToolDefinition(
            name="buscar_entidades",
            description="Busca entidades por valor en todos los expedientes",
            category=ToolCategory.ENTIDADES,
            parameters={
                "valor": {
                    "type": "string",
                    "description": "Texto a buscar (nombre, etc)"
                },
                "tipo": {
                    "type": "string",
                    "description": "Filtrar por tipo (opcional)"
                },
                "limite": {
                    "type": "integer",
                    "description": "Máximo de resultados",
                    "default": 20
                }
            },
            required_params=["valor"]
        ))

        self._register(ToolDefinition(
            name="entidades_por_tipo",
            description="Agrupa entidades por tipo con conteos y score promedio",
            category=ToolCategory.ENTIDADES,
            parameters={
                "expediente_numero": {
                    "type": "string",
                    "description": "Limitar a un expediente (opcional)"
                }
            }
        ))

        self._register(ToolDefinition(
            name="estadisticas_entidades",
            description="Estadísticas generales de entidades extraídas en todo el sistema",
            category=ToolCategory.ENTIDADES,
            parameters={}
        ))

        self._register(ToolDefinition(
            name="personas_expediente",
            description="Obtiene personas mencionadas en un expediente con roles inferidos",
            category=ToolCategory.ENTIDADES,
            parameters={
                "expediente_numero": {
                    "type": "string",
                    "description": "Número del expediente"
                },
                "score_minimo": {
                    "type": "number",
                    "description": "Score mínimo de confianza (0-1)",
                    "default": 0.5
                }
            },
            required_params=["expediente_numero"]
        ))

        # =====================================================
        # CATEGORIA 5: ESTADISTICAS (4 tools)
        # =====================================================

        self._register(ToolDefinition(
            name="estadisticas_sistema",
            description="Obtiene estadísticas generales del sistema: expedientes, actuaciones, vencimientos",
            category=ToolCategory.ESTADISTICAS,
            parameters={}
        ))

        self._register(ToolDefinition(
            name="estadisticas_expediente",
            description="Obtiene estadísticas detalladas de un expediente específico",
            category=ToolCategory.ESTADISTICAS,
            parameters={
                "expediente_numero": {
                    "type": "string",
                    "description": "Número del expediente"
                }
            },
            required_params=["expediente_numero"]
        ))

        self._register(ToolDefinition(
            name="estadisticas_procesamiento",
            description="Estadísticas de procesamiento IA: clasificación y NER",
            category=ToolCategory.ESTADISTICAS,
            parameters={}
        ))

        self._register(ToolDefinition(
            name="actividad_reciente",
            description="Timeline de actividad reciente en el sistema (actuaciones y vencimientos)",
            category=ToolCategory.ESTADISTICAS,
            parameters={
                "dias": {
                    "type": "integer",
                    "description": "Días hacia atrás",
                    "default": 7
                },
                "limite": {
                    "type": "integer",
                    "description": "Máximo de eventos",
                    "default": 50
                }
            }
        ))

        # =====================================================
        # CATEGORIA 6: ANALISIS (4 tools)
        # =====================================================

        self._register(ToolDefinition(
            name="duplicados_detectados",
            description="Lista actuaciones marcadas como posibles duplicados",
            category=ToolCategory.ANALISIS,
            parameters={
                "expediente_numero": {
                    "type": "string",
                    "description": "Limitar a un expediente (opcional)"
                },
                "limite": {
                    "type": "integer",
                    "description": "Máximo de resultados",
                    "default": 20
                }
            }
        ))

        self._register(ToolDefinition(
            name="clasificacion_ia",
            description="Obtiene resultados de clasificación IA de actuaciones de un expediente",
            category=ToolCategory.ANALISIS,
            parameters={
                "expediente_numero": {
                    "type": "string",
                    "description": "Número del expediente"
                }
            },
            required_params=["expediente_numero"]
        ))

        self._register(ToolDefinition(
            name="actuaciones_importantes",
            description="Obtiene actuaciones clasificadas como de alta o media utilidad",
            category=ToolCategory.ANALISIS,
            parameters={
                "expediente_numero": {
                    "type": "string",
                    "description": "Limitar a un expediente (opcional)"
                },
                "utilidad_minima": {
                    "type": "string",
                    "description": "Utilidad mínima requerida",
                    "enum": ["alta", "media"],
                    "default": "alta"
                },
                "limite": {
                    "type": "integer",
                    "description": "Máximo de resultados",
                    "default": 20
                }
            }
        ))

        self._register(ToolDefinition(
            name="resumen_expediente",
            description="Genera resumen completo de un expediente con actuaciones, vencimientos y entidades",
            category=ToolCategory.ANALISIS,
            parameters={
                "expediente_numero": {
                    "type": "string",
                    "description": "Número del expediente"
                },
                "incluir_actuaciones": {
                    "type": "boolean",
                    "description": "Incluir últimas actuaciones",
                    "default": True
                },
                "incluir_vencimientos": {
                    "type": "boolean",
                    "description": "Incluir vencimientos pendientes",
                    "default": True
                },
                "incluir_entidades": {
                    "type": "boolean",
                    "description": "Incluir entidades extraídas",
                    "default": True
                }
            },
            required_params=["expediente_numero"]
        ))

        # =====================================================
        # CATEGORIA 7: MONITOREO (8 tools)
        # =====================================================

        self._register(ToolDefinition(
            name="estado_monitoreo",
            description="Obtiene el estado actual del sistema de monitoreo automático",
            category=ToolCategory.MONITOREO,
            parameters={}
        ))

        self._register(ToolDefinition(
            name="listar_expedientes_monitoreados",
            description="Lista los expedientes que están siendo monitoreados",
            category=ToolCategory.MONITOREO,
            parameters={
                "solo_activos": {
                    "type": "boolean",
                    "description": "Solo mostrar expedientes con monitoreo activo",
                    "default": False
                },
                "limite": {
                    "type": "integer",
                    "description": "Máximo de resultados",
                    "default": 50
                }
            }
        ))

        self._register(ToolDefinition(
            name="listar_cambios_monitoreo",
            description="Lista los cambios detectados por el sistema de monitoreo",
            category=ToolCategory.MONITOREO,
            parameters={
                "solo_no_leidos": {
                    "type": "boolean",
                    "description": "Solo cambios no leídos",
                    "default": False
                },
                "tipo_cambio": {
                    "type": "string",
                    "description": "Filtrar por tipo: nueva_actuacion, cambio_estado, etc"
                },
                "expediente_numero": {
                    "type": "string",
                    "description": "Filtrar por expediente"
                },
                "limite": {
                    "type": "integer",
                    "description": "Máximo de resultados",
                    "default": 50
                }
            }
        ))

        self._register(ToolDefinition(
            name="estadisticas_monitoreo",
            description="Obtiene estadísticas del sistema de monitoreo",
            category=ToolCategory.MONITOREO,
            parameters={}
        ))

        self._register(ToolDefinition(
            name="agregar_expediente_monitoreo",
            description="Agrega un expediente al sistema de monitoreo automático",
            category=ToolCategory.MONITOREO,
            parameters={
                "expediente_numero": {
                    "type": "string",
                    "description": "Número del expediente a monitorear"
                },
                "prioridad": {
                    "type": "string",
                    "description": "Prioridad del monitoreo",
                    "enum": ["baja", "media", "alta"],
                    "default": "media"
                },
                "notas": {
                    "type": "string",
                    "description": "Notas adicionales"
                }
            },
            required_params=["expediente_numero"]
        ))

        self._register(ToolDefinition(
            name="pausar_expediente_monitoreo",
            description="Pausa el monitoreo de un expediente",
            category=ToolCategory.MONITOREO,
            parameters={
                "expediente_numero": {
                    "type": "string",
                    "description": "Número del expediente"
                }
            },
            required_params=["expediente_numero"]
        ))

        self._register(ToolDefinition(
            name="reanudar_expediente_monitoreo",
            description="Reanuda el monitoreo de un expediente pausado",
            category=ToolCategory.MONITOREO,
            parameters={
                "expediente_numero": {
                    "type": "string",
                    "description": "Número del expediente"
                }
            },
            required_params=["expediente_numero"]
        ))

        self._register(ToolDefinition(
            name="sincronizar_expedientes_monitoreo",
            description="Sincroniza expedientes activos al sistema de monitoreo",
            category=ToolCategory.MONITOREO,
            parameters={}
        ))

        logger.info(f"ToolsRegistry inicializado con {len(self._tools)} tools")

    def _register(self, tool: ToolDefinition):
        """Registra una tool."""
        self._tools[tool.name] = tool

    # =========================================================
    # Métodos de consulta
    # =========================================================

    def get(self, name: str) -> Optional[ToolDefinition]:
        """Obtiene una tool por nombre."""
        return self._tools.get(name)

    def get_all_definitions(self) -> List[ToolDefinition]:
        """Retorna todas las definiciones de tools."""
        return list(self._tools.values())

    def get_all_names(self) -> List[str]:
        """Retorna nombres de todas las tools."""
        return list(self._tools.keys())

    def get_by_category(self, category: ToolCategory) -> List[ToolDefinition]:
        """Retorna tools de una categoría específica."""
        return [t for t in self._tools.values() if t.category == category]

    def get_mcp_definitions(self) -> List[Dict[str, Any]]:
        """Retorna definiciones en formato MCP."""
        return [t.to_mcp_format() for t in self._tools.values()]

    def get_openai_definitions(self) -> List[Dict[str, Any]]:
        """Retorna definiciones en formato OpenAI."""
        return [t.to_openai_format() for t in self._tools.values()]

    def get_summary(self) -> Dict[str, Any]:
        """Retorna resumen del registro."""
        by_category = {}
        for cat in ToolCategory:
            tools = self.get_by_category(cat)
            by_category[cat.value] = {
                "count": len(tools),
                "tools": [t.name for t in tools]
            }

        return {
            "total_tools": len(self._tools),
            "categories": len(ToolCategory),
            "by_category": by_category
        }

    # =========================================================
    # Ejecución de tools
    # =========================================================

    def execute(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """
        Ejecuta una tool por nombre.

        Args:
            tool_name: Nombre de la tool
            params: Parámetros de la tool

        Returns:
            Resultado de la ejecución

        Raises:
            ValueError: Si la tool no existe
        """
        if tool_name not in self._tools:
            raise ValueError(f"Tool '{tool_name}' no encontrada. Disponibles: {self.get_all_names()}")

        service = self._get_service()
        return service.execute_tool(tool_name, params)

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools


# Singleton global para acceso rápido
_registry: Optional[ToolsRegistry] = None

def get_registry() -> ToolsRegistry:
    """Obtiene instancia singleton del registro."""
    global _registry
    if _registry is None:
        _registry = ToolsRegistry()
    return _registry
