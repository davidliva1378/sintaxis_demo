#!/usr/bin/env python3
"""
Servidor MCP (Model Context Protocol) con transporte SSE para Sistema Sintaxis.

Expone las herramientas de ToolsService a traves del protocolo MCP
usando Server-Sent Events para permitir conexiones remotas.

Uso:
    python sintaxis_mcp_server_sse.py [--port 8765] [--host 0.0.0.0]

Configuracion en Claude Desktop (remoto):
    Agregar servidor MCP con URL: http://IP:8765/sse
"""

import asyncio
import json
import sys
import os
import argparse
import ssl
import ipaddress
from datetime import datetime
from typing import Any
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
except ImportError as e:
    print(f"Error: Dependencias no instaladas. Ejecutar: pip install mcp starlette uvicorn", file=sys.stderr)
    print(f"Detalle: {e}", file=sys.stderr)
    sys.exit(1)

from application.services.ia.tools_service import ToolsService

# Crear servidor MCP
mcp_app = Server("sintaxis")

# Instancia del servicio de tools
tools_service = ToolsService()

# Transporte SSE
sse_transport = SseServerTransport("/messages")


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
    ]


@mcp_app.call_tool()
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


async def handle_sse(request):
    """Maneja conexiones SSE entrantes."""
    async with sse_transport.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await mcp_app.run(
            streams[0], streams[1], mcp_app.create_initialization_options()
        )


async def handle_messages(request):
    """Maneja mensajes POST del cliente."""
    await sse_transport.handle_post_message(request.scope, request.receive, request._send)


async def health_check(request):
    """Endpoint de health check."""
    return JSONResponse({
        "status": "ok",
        "server": "sintaxis-mcp-sse",
        "tools_count": 29
    })


# Crear aplicacion Starlette
app = Starlette(
    debug=False,
    routes=[
        Route("/sse", endpoint=handle_sse),
        Route("/messages", endpoint=handle_messages, methods=["POST"]),
        Route("/health", endpoint=health_check),
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
    parser = argparse.ArgumentParser(description="Servidor MCP SSE para Sintaxis")
    parser.add_argument("--host", default="0.0.0.0", help="Host a escuchar (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8765, help="Puerto (default: 8765)")
    parser.add_argument("--ssl", action="store_true", help="Habilitar HTTPS")
    parser.add_argument("--cert", help="Ruta al certificado SSL")
    parser.add_argument("--key", help="Ruta a la clave privada SSL")

    args = parser.parse_args()

    ssl_keyfile = None
    ssl_certfile = None
    protocol = "http"

    if args.ssl:
        protocol = "https"
        if args.cert and args.key:
            ssl_certfile = args.cert
            ssl_keyfile = args.key
        else:
            # Generar certificados auto-firmados
            cert_dir = Path(project_root) / "config" / "ssl"
            ssl_certfile, ssl_keyfile = generate_self_signed_cert(cert_dir)
            print("\nNOTA: Usando certificado auto-firmado.")
            print("Para evitar advertencias de seguridad en Claude Desktop,")
            print("importa el certificado como confiable en tu sistema.\n")

    print(f"Iniciando servidor MCP SSE en {protocol}://{args.host}:{args.port}")
    print(f"URL para Claude Desktop: {protocol}://<IP>:{args.port}/sse")

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
