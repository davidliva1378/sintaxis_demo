#!/bin/bash
# =============================================================================
# Script de inicio: Servidor MCP SSE con ngrok
# =============================================================================
#
# Inicia el servidor MCP SSE y crea un túnel ngrok para acceso remoto.
#
# Requisitos:
#   - ngrok instalado: brew install ngrok
#   - Token ngrok configurado: ngrok config add-authtoken YOUR_TOKEN
#   - Python con dependencias MCP
#
# Uso:
#   ./start_mcp_with_ngrok.sh              # Sin autenticación
#   ./start_mcp_with_ngrok.sh --auth       # Con autenticación Bearer
#   ./start_mcp_with_ngrok.sh --auth --ssl # Con autenticación y HTTPS
#
# =============================================================================

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SINTAXIS_ROOT="$(dirname "$PROJECT_ROOT")"

MCP_PORT="${MCP_PORT:-8765}"
MCP_HOST="${MCP_HOST:-0.0.0.0}"
AUTH_FLAG=""
RATE_LIMIT_FLAG=""
SSL_FLAG=""

# Procesar argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        --auth)
            AUTH_FLAG="--auth"
            shift
            ;;
        --rate-limit)
            RATE_LIMIT_FLAG="--rate-limit"
            shift
            ;;
        --ssl)
            SSL_FLAG="--ssl"
            shift
            ;;
        --port)
            MCP_PORT="$2"
            shift 2
            ;;
        --help|-h)
            echo "Uso: $0 [opciones]"
            echo ""
            echo "Opciones:"
            echo "  --auth         Habilitar autenticación Bearer"
            echo "  --rate-limit   Habilitar rate limiting"
            echo "  --ssl          Habilitar HTTPS"
            echo "  --port PORT    Puerto del servidor MCP (default: 8765)"
            echo "  --help         Mostrar esta ayuda"
            exit 0
            ;;
        *)
            echo -e "${RED}Opción desconocida: $1${NC}"
            exit 1
            ;;
    esac
done

# Verificar ngrok
if ! command -v ngrok &> /dev/null; then
    echo -e "${RED}Error: ngrok no está instalado${NC}"
    echo ""
    echo "Instalar con:"
    echo "  brew install ngrok"
    echo ""
    echo "Luego configurar token (obtener en https://dashboard.ngrok.com):"
    echo "  ngrok config add-authtoken YOUR_TOKEN"
    exit 1
fi

# Banner
echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Servidor MCP SSE + ngrok${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Cleanup al salir
cleanup() {
    echo ""
    echo -e "${YELLOW}Deteniendo servicios...${NC}"

    if [ -n "$MCP_PID" ] && kill -0 "$MCP_PID" 2>/dev/null; then
        kill "$MCP_PID" 2>/dev/null || true
        echo -e "${GREEN}✓ Servidor MCP detenido${NC}"
    fi

    if [ -n "$NGROK_PID" ] && kill -0 "$NGROK_PID" 2>/dev/null; then
        kill "$NGROK_PID" 2>/dev/null || true
        echo -e "${GREEN}✓ ngrok detenido${NC}"
    fi

    echo -e "${GREEN}Limpieza completada${NC}"
}

trap cleanup EXIT INT TERM

# Iniciar servidor MCP
echo -e "${YELLOW}Iniciando servidor MCP SSE...${NC}"
echo "  Puerto: $MCP_PORT"
echo "  Auth: ${AUTH_FLAG:-deshabilitado}"
echo "  Rate Limit: ${RATE_LIMIT_FLAG:-deshabilitado}"
echo "  SSL: ${SSL_FLAG:-deshabilitado}"
echo ""

cd "$PROJECT_ROOT"

PYTHONPATH="$SINTAXIS_ROOT:$PROJECT_ROOT:$PYTHONPATH" \
MYSQL_PASSWORD="${MYSQL_PASSWORD:-}" \
python -m sintaxis_mcp.sintaxis_mcp_server_sse \
    --host "$MCP_HOST" \
    --port "$MCP_PORT" \
    $AUTH_FLAG \
    $RATE_LIMIT_FLAG \
    $SSL_FLAG &

MCP_PID=$!

# Esperar a que el servidor inicie
echo -e "${YELLOW}Esperando que el servidor MCP inicie...${NC}"
sleep 3

# Verificar que el servidor está corriendo
if ! kill -0 "$MCP_PID" 2>/dev/null; then
    echo -e "${RED}Error: El servidor MCP no pudo iniciar${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Servidor MCP iniciado (PID: $MCP_PID)${NC}"
echo ""

# Iniciar ngrok
echo -e "${YELLOW}Iniciando túnel ngrok...${NC}"

ngrok http "$MCP_PORT" --log=stdout > /tmp/ngrok.log 2>&1 &
NGROK_PID=$!

# Esperar a que ngrok inicie
sleep 3

# Verificar que ngrok está corriendo
if ! kill -0 "$NGROK_PID" 2>/dev/null; then
    echo -e "${RED}Error: ngrok no pudo iniciar${NC}"
    echo "Verifica los logs en /tmp/ngrok.log"
    exit 1
fi

# Obtener URL pública de ngrok
echo -e "${YELLOW}Obteniendo URL pública...${NC}"
sleep 2

NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | \
    python3 -c "import sys, json; data=json.load(sys.stdin); print(data['tunnels'][0]['public_url'] if data.get('tunnels') else '')" 2>/dev/null || echo "")

if [ -z "$NGROK_URL" ]; then
    echo -e "${RED}No se pudo obtener la URL de ngrok${NC}"
    echo "Verifica que ngrok esté configurado correctamente"
    echo "Logs: /tmp/ngrok.log"
    exit 1
fi

echo -e "${GREEN}✓ ngrok iniciado (PID: $NGROK_PID)${NC}"
echo ""

# Mostrar información de conexión
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  SERVIDOR MCP DISPONIBLE${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "  ${BLUE}Local:${NC}   http://localhost:$MCP_PORT/sse"
echo -e "  ${BLUE}Público:${NC} $NGROK_URL/sse"
echo ""
echo -e "  ${BLUE}Health:${NC}  $NGROK_URL/health"
echo ""

# Mostrar configuración para Claude Desktop
echo -e "${YELLOW}============================================${NC}"
echo -e "${YELLOW}  Configuración para Claude Desktop${NC}"
echo -e "${YELLOW}============================================${NC}"
echo ""

if [ -n "$AUTH_FLAG" ]; then
    echo "Agregar a ~/Library/Application Support/Claude/claude_desktop_config.json:"
    echo ""
    echo -e "${GREEN}{"
    echo '  "mcpServers": {'
    echo '    "sintaxis-remoto": {'
    echo "      \"url\": \"$NGROK_URL/sse\","
    echo '      "transport": "sse",'
    echo '      "headers": {'
    echo '        "Authorization": "Bearer TU_TOKEN_AQUI"'
    echo '      }'
    echo '    }'
    echo '  }'
    echo -e "}${NC}"
    echo ""
    echo -e "${YELLOW}NOTA: Genera un token con:${NC}"
    echo "  python -m sintaxis_mcp.sintaxis_mcp_server_sse --generate-token 'claude-desktop'"
else
    echo "Agregar a ~/Library/Application Support/Claude/claude_desktop_config.json:"
    echo ""
    echo -e "${GREEN}{"
    echo '  "mcpServers": {'
    echo '    "sintaxis-remoto": {'
    echo "      \"url\": \"$NGROK_URL/sse\","
    echo '      "transport": "sse"'
    echo '    }'
    echo '  }'
    echo -e "}${NC}"
fi

echo ""
echo -e "${YELLOW}============================================${NC}"
echo -e "${YELLOW}  Panel de ngrok: http://localhost:4040${NC}"
echo -e "${YELLOW}============================================${NC}"
echo ""
echo -e "${BLUE}Presiona Ctrl+C para detener${NC}"
echo ""

# Mantener el script corriendo
wait $MCP_PID
