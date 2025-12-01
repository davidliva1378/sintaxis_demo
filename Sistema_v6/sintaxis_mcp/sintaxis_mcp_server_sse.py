#!/usr/bin/env python3
"""
Servidor MCP (Model Context Protocol) con transporte SSE para Sistema Sintaxis.

Expone las herramientas de ToolsService a traves del protocolo MCP
usando Server-Sent Events para permitir conexiones remotas.

Uso:
    python sintaxis_mcp_server_sse.py [--port 8765] [--host 0.0.0.0]
    python sintaxis_mcp_server_sse.py --auth  # Con autenticación Bearer

Configuracion en Claude Desktop (remoto):
    Agregar servidor MCP con URL: http://IP:8765/sse
    Si usa autenticación: agregar header Authorization: Bearer <token>
"""

import asyncio
import json
import sys
import os
import argparse
import ssl
import ipaddress
import logging
from datetime import datetime
from typing import Any, Optional
from pathlib import Path

# Agregar path del proyecto
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(project_root))

try:
    from mcp.server import Server
    from mcp.server.sse import SseServerTransport
    from mcp.types import Tool, TextContent
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.responses import JSONResponse
    import uvicorn
    MCP_INSTALLED = True
except ImportError as e:
    print(f"Advertencia: Dependencias MCP no instaladas ({e}). El servidor funcionara en modo limitado.", file=sys.stderr)
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
            return iter([Mock(name=f"{self._name}_item")])
            
        def __await__(self):
            async def _coro(): return self
            return _coro().__await__()
            
        async def __aenter__(self): return (Mock(), Mock())
        async def __aexit__(self, exc_type, exc_val, exc_tb): pass
        
    Server = Mock
    SseServerTransport = Mock
    Tool = Mock
    TextContent = Mock
    
    # Intentar importar Starlette/Uvicorn si estan disponibles (son deps de FastAPI)
    try:
        from starlette.applications import Starlette
        from starlette.routing import Route
        from starlette.responses import JSONResponse
        import uvicorn
    except ImportError:
        Starlette = Mock
        Route = Mock
        JSONResponse = Mock
        uvicorn = Mock

from application.services.ia.tools_service import ToolsService

# Importar auth (puede no estar disponible)
try:
    from sintaxis_mcp.auth import TokenManager, RateLimiter
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False
    TokenManager = None
    RateLimiter = None

# Importar métricas
try:
    from sintaxis_mcp.core.metrics import get_metrics, MetricsContext
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    get_metrics = None
    MetricsContext = None

# Importar cache
try:
    from sintaxis_mcp.core.cache import get_cache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    get_cache = None

logger = logging.getLogger(__name__)

# Crear servidor MCP
mcp_app = Server("sintaxis")

# Instancia del servicio de tools
tools_service = ToolsService()

# Transporte SSE
sse_transport = SseServerTransport("/messages")

# Variables globales para autenticación y rate limiting
token_manager: Optional["TokenManager"] = None
rate_limiter: Optional["RateLimiter"] = None
auth_enabled: bool = False
rate_limit_enabled: bool = False


def serialize_result(result: Any) -> str:
    """Serializa resultado a JSON, manejando tipos especiales."""
    def default_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return str(obj)

    return json.dumps(result, default=default_serializer, ensure_ascii=False, indent=2)


@mcp_app.list_tools()
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


@mcp_app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Ejecuta una herramienta y retorna el resultado."""
    import time
    start_time = time.time()
    success = True
    error_type = None
    cache_hit = False

    try:
        # Convertir fechas string a datetime
        args_for_cache = dict(arguments)  # Copia antes de modificar
        for key in ['desde', 'hasta']:
            if key in arguments and arguments[key]:
                arguments[key] = datetime.fromisoformat(arguments[key])

        # Intentar obtener del cache
        if CACHE_AVAILABLE and get_cache:
            cache = get_cache()
            if cache.is_cacheable(name):
                cached_result = cache.get(name, args_for_cache)
                if cached_result is not None:
                    cache_hit = True
                    content = serialize_result(cached_result)
                    return [TextContent(type="text", text=content)]

        # Ejecutar tool
        result = tools_service.execute_tool(name, arguments)

        # Guardar en cache si está habilitado
        if CACHE_AVAILABLE and get_cache and not cache_hit:
            cache = get_cache()
            if cache.is_cacheable(name):
                cache.set(name, args_for_cache, result)

        # Serializar resultado
        content = serialize_result(result)

        return [TextContent(type="text", text=content)]

    except ValueError as e:
        success = False
        error_type = "ValueError"
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        success = False
        error_type = type(e).__name__
        return [TextContent(type="text", text=f"Error ejecutando {name}: {str(e)}")]
    finally:
        # Registrar métricas (incluyendo si fue cache hit)
        if METRICS_AVAILABLE and get_metrics:
            duration_ms = (time.time() - start_time) * 1000
            # Los cache hits son muy rápidos, registrar igualmente
            get_metrics().record_call(name, duration_ms, success, error_type)


def get_client_ip(request) -> str:
    """Obtiene IP del cliente, considerando proxies."""
    # Intentar X-Forwarded-For primero (para proxies/load balancers)
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()

    # Fallback a IP directa
    client = request.scope.get("client")
    if client:
        return client[0]
    return "unknown"


def check_rate_limit(request, token_name: Optional[str] = None) -> tuple[bool, Optional[float]]:
    """
    Verifica rate limit si está habilitado.

    Returns:
        (allowed, retry_after)
    """
    global rate_limit_enabled, rate_limiter

    if not rate_limit_enabled or not rate_limiter:
        return True, None

    client_ip = get_client_ip(request)
    return rate_limiter.is_allowed(client_ip, token_name)


def validate_auth(request) -> tuple[bool, Optional[str], Optional[str]]:
    """
    Valida autenticación Bearer si está habilitada.

    Returns:
        (is_valid, error_message, token_name)
    """
    global auth_enabled, token_manager

    if not auth_enabled:
        return True, None, None

    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        return False, "Authorization header required", None

    token_str = auth_header[7:]
    if not token_manager:
        return False, "Token manager not initialized", None

    token = token_manager.validate_token(token_str)
    if not token:
        return False, "Invalid or expired token", None

    logger.debug(f"Request autenticado: {token.name}")
    return True, None, token.name


async def handle_sse(request):
    """Maneja conexiones SSE entrantes."""
    # Validar autenticación
    is_valid, error, token_name = validate_auth(request)
    if not is_valid:
        logger.warning(f"SSE auth failed: {error}")
        return JSONResponse(
            {"error": error, "code": "AUTH_REQUIRED"},
            status_code=401
        )

    # Verificar rate limit
    allowed, retry_after = check_rate_limit(request, token_name)
    if not allowed:
        logger.warning(f"SSE rate limit exceeded for {get_client_ip(request)}")
        return JSONResponse(
            {"error": "Rate limit exceeded", "code": "RATE_LIMITED", "retry_after": retry_after},
            status_code=429,
            headers={"Retry-After": str(int(retry_after or 60))}
        )

    async with sse_transport.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await mcp_app.run(
            streams[0], streams[1], mcp_app.create_initialization_options()
        )


async def handle_messages(request):
    """Maneja mensajes POST del cliente."""
    # Validar autenticación
    is_valid, error, token_name = validate_auth(request)
    if not is_valid:
        logger.warning(f"Messages auth failed: {error}")
        return JSONResponse(
            {"error": error, "code": "AUTH_REQUIRED"},
            status_code=401
        )

    # Verificar rate limit
    allowed, retry_after = check_rate_limit(request, token_name)
    if not allowed:
        logger.warning(f"Messages rate limit exceeded for {get_client_ip(request)}")
        return JSONResponse(
            {"error": "Rate limit exceeded", "code": "RATE_LIMITED", "retry_after": retry_after},
            status_code=429,
            headers={"Retry-After": str(int(retry_after or 60))}
        )

    await sse_transport.handle_post_message(request.scope, request.receive, request._send)


async def health_check(request):
    """Endpoint de health check."""
    rate_stats = {}
    if rate_limiter:
        rate_stats = rate_limiter.get_stats()

    metrics_summary = {}
    if METRICS_AVAILABLE and get_metrics:
        full_stats = get_metrics().get_stats()
        metrics_summary = full_stats.get("summary", {})

    cache_summary = {}
    if CACHE_AVAILABLE and get_cache:
        cache_stats = get_cache().get_stats()
        cache_summary = {
            "enabled": cache_stats.get("enabled"),
            "size": cache_stats.get("size"),
            "hit_rate": cache_stats.get("stats", {}).get("hit_rate")
        }

    return JSONResponse({
        "status": "ok",
        "server": "sintaxis-mcp-sse",
        "tools_count": 37,
        "auth_enabled": auth_enabled,
        "rate_limit_enabled": rate_limit_enabled,
        "metrics_enabled": METRICS_AVAILABLE,
        "cache_enabled": CACHE_AVAILABLE,
        "rate_limit_stats": rate_stats if rate_limit_enabled else None,
        "metrics_summary": metrics_summary if METRICS_AVAILABLE else None,
        "cache_summary": cache_summary if CACHE_AVAILABLE else None
    })


async def metrics_endpoint(request):
    """Endpoint para obtener métricas detalladas."""
    # Validar autenticación si está habilitada
    is_valid, error, token_name = validate_auth(request)
    if not is_valid:
        return JSONResponse({"error": error}, status_code=401)

    if not METRICS_AVAILABLE or not get_metrics:
        return JSONResponse({"error": "Metrics not available"}, status_code=501)

    return JSONResponse(get_metrics().get_stats())


async def cache_endpoint(request):
    """Endpoint para obtener estadísticas del cache."""
    # Validar autenticación si está habilitada
    is_valid, error, token_name = validate_auth(request)
    if not is_valid:
        return JSONResponse({"error": error}, status_code=401)

    if not CACHE_AVAILABLE or not get_cache:
        return JSONResponse({"error": "Cache not available"}, status_code=501)

    return JSONResponse(get_cache().get_stats())


# Crear aplicacion Starlette
app = Starlette(
    debug=False,
    routes=[
        Route("/sse", endpoint=handle_sse),
        Route("/messages", endpoint=handle_messages, methods=["POST"]),
        Route("/health", endpoint=health_check),
        Route("/metrics", endpoint=metrics_endpoint),
        Route("/cache", endpoint=cache_endpoint),
    ],
)


def generate_self_signed_cert(cert_dir: Path):
    """Genera certificados SSL auto-firmados si no existen."""
    cert_file = cert_dir / "cert.pem"
    key_file = cert_dir / "key.pem"

    if cert_file.exists() and key_file.exists():
        return str(cert_file), str(key_file)

    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        import datetime

        # Generar clave privada
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        # Generar certificado
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "AR"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Buenos Aires"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "CABA"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Sintaxis MCP"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])

        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
            .add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName("localhost"),
                    x509.DNSName("*.local"),
                    x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                ]),
                critical=False,
            )
            .sign(key, hashes.SHA256(), default_backend())
        )

        # Guardar archivos
        cert_dir.mkdir(parents=True, exist_ok=True)

        with open(key_file, "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))

        with open(cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        print(f"Certificados SSL generados en {cert_dir}")
        return str(cert_file), str(key_file)

    except ImportError:
        print("Error: Para HTTPS necesitas instalar cryptography: pip install cryptography")
        sys.exit(1)


def main():
    """Inicia el servidor MCP SSE."""
    global auth_enabled, token_manager, rate_limit_enabled, rate_limiter

    parser = argparse.ArgumentParser(description="Servidor MCP SSE para Sintaxis")
    parser.add_argument("--host", default="0.0.0.0", help="Host a escuchar (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8765, help="Puerto (default: 8765)")
    parser.add_argument("--ssl", action="store_true", help="Habilitar HTTPS")
    parser.add_argument("--cert", help="Ruta al certificado SSL")
    parser.add_argument("--key", help="Ruta a la clave privada SSL")
    parser.add_argument("--auth", action="store_true", help="Habilitar autenticación Bearer")
    parser.add_argument("--rate-limit", action="store_true", help="Habilitar rate limiting")
    parser.add_argument("--rpm", type=int, default=60, help="Requests por minuto (anon, default: 60)")
    parser.add_argument("--rpm-auth", type=int, default=120, help="Requests por minuto (auth, default: 120)")
    parser.add_argument("--generate-token", metavar="NAME", help="Generar token y salir")

    args = parser.parse_args()

    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    # Generar token si se solicita
    if args.generate_token:
        if not AUTH_AVAILABLE:
            print("Error: Módulo de autenticación no disponible")
            sys.exit(1)

        tm = TokenManager()
        token_str, token = tm.generate_token(args.generate_token)
        print("\n" + "=" * 60)
        print("✅ TOKEN GENERADO")
        print("=" * 60)
        print(f"Nombre: {args.generate_token}")
        print(f"Token ID: {token.token_id}")
        print(f"\n🔑 TOKEN: {token_str}")
        print("\n⚠️  Guarda este token de forma segura.")
        print("   No podrás verlo de nuevo.")
        print("=" * 60)
        sys.exit(0)

    # Configurar autenticación
    if args.auth:
        if not AUTH_AVAILABLE:
            print("Error: Módulo de autenticación no disponible")
            print("       Asegúrate de que sintaxis_mcp/auth existe")
            sys.exit(1)

        auth_enabled = True
        token_manager = TokenManager()
        tokens = token_manager.list_tokens()
        print(f"\n🔐 Autenticación HABILITADA ({len(tokens)} tokens activos)")

        if not tokens:
            print("\n⚠️  No hay tokens configurados.")
            print("   Genera uno con: python sintaxis_mcp_server_sse.py --generate-token 'nombre'")
            print("   O usa el CLI: python bin/mcp_token_cli.py generate --name 'nombre'\n")

    # Configurar rate limiting
    if args.rate_limit:
        if not AUTH_AVAILABLE or RateLimiter is None:
            print("Error: Módulo de rate limiting no disponible")
            sys.exit(1)

        rate_limit_enabled = True
        rate_limiter = RateLimiter(
            requests_per_minute=args.rpm,
            requests_per_minute_authenticated=args.rpm_auth
        )
        print(f"\n⚡ Rate Limiting HABILITADO: {args.rpm}/min (anon), {args.rpm_auth}/min (auth)")

    ssl_keyfile = None
    ssl_certfile = None
    protocol = "http"

    if args.ssl:
        protocol = "https"
        if args.cert and args.key:
            ssl_certfile = args.cert
            ssl_keyfile = args.key
        else:
            # Usar CertificateManager para gestión mejorada de certificados
            from sintaxis_mcp.core.certificate_manager import CertificateManager

            cert_dir = Path(project_root) / "config" / "ssl"
            cert_manager = CertificateManager(cert_dir=cert_dir)
            ssl_certfile, ssl_keyfile = cert_manager.get_or_create()

            # Mostrar info del certificado
            cert_info = cert_manager.get_info()
            if cert_info.get("days_remaining"):
                print(f"\n📜 Certificado SSL:")
                print(f"   Ruta: {ssl_certfile}")
                print(f"   Expira en: {cert_info['days_remaining']} días")
                if cert_info.get("needs_renewal"):
                    print(f"   ⚠️  Próximo a expirar, se renovará automáticamente")
            print("\nNOTA: Certificado auto-firmado persistente.")
            print("Para evitar advertencias de seguridad en Claude Desktop,")
            print("importa el certificado como confiable en tu sistema.\n")

    print(f"\n🚀 Iniciando servidor MCP SSE en {protocol}://{args.host}:{args.port}")
    print(f"📡 URL para Claude Desktop: {protocol}://<IP>:{args.port}/sse")
    print(f"🔐 Autenticación: {'Habilitada' if auth_enabled else 'Deshabilitada'}")
    print(f"⚡ Rate Limiting: {'Habilitado' if rate_limit_enabled else 'Deshabilitado'}")
    print(f"🔧 Tools disponibles: 37\n")

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info",
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile
    )


if __name__ == "__main__":
    main()
