#!/bin/bash
# ============================================================================
# sintaXis - Script de Inicio del Sistema
# ============================================================================
#
# Este script inicia el sistema completo con splash screen opcional.
#
# Uso:
#   ./start.sh              # Inicio completo con splash
#   ./start.sh --no-splash  # Sin splash screen
#   ./start.sh --backend    # Solo backend
#   ./start.sh --frontend   # Solo frontend
#   ./start.sh --stop       # Detener servicios
#
# ============================================================================

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directorio del script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

# Configuracion
BACKEND_PORT=8000
FRONTEND_PORT=5173
BACKEND_URL="http://localhost:$BACKEND_PORT"
FRONTEND_URL="http://localhost:$FRONTEND_PORT"

# PIDs de procesos
BACKEND_PID=""
FRONTEND_PID=""
SPLASH_PID=""

# ============================================================================
# Funciones de utilidad
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Puerto en uso
    else
        return 1  # Puerto libre
    fi
}

wait_for_service() {
    local url=$1
    local max_attempts=${2:-30}
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
        ((attempt++))
    done
    return 1
}

# ============================================================================
# Funciones de servicios
# ============================================================================

start_backend() {
    if check_port $BACKEND_PORT; then
        log_warn "Backend ya corriendo en puerto $BACKEND_PORT"
        return 0
    fi

    log_info "Iniciando backend en puerto $BACKEND_PORT..."

    export PYTHONPATH="$PARENT_DIR:$SCRIPT_DIR:$PYTHONPATH"

    cd "$SCRIPT_DIR"
    uvicorn presentation.api.rest.main:app \
        --host 0.0.0.0 \
        --port $BACKEND_PORT \
        --reload \
        > /tmp/sintaxis_backend.log 2>&1 &

    BACKEND_PID=$!
    echo $BACKEND_PID > /tmp/sintaxis_backend.pid

    # Esperar a que el backend este disponible
    if wait_for_service "$BACKEND_URL/api/v1/health" 15; then
        log_success "Backend iniciado (PID: $BACKEND_PID)"
    else
        log_warn "Backend iniciando... puede tomar mas tiempo"
    fi
}

start_frontend() {
    if check_port $FRONTEND_PORT; then
        log_warn "Frontend ya corriendo en puerto $FRONTEND_PORT"
        return 0
    fi

    if [ ! -d "$FRONTEND_DIR" ]; then
        log_error "Directorio frontend no encontrado: $FRONTEND_DIR"
        return 1
    fi

    log_info "Iniciando frontend en puerto $FRONTEND_PORT..."

    cd "$FRONTEND_DIR"
    npm run dev > /tmp/sintaxis_frontend.log 2>&1 &

    FRONTEND_PID=$!
    echo $FRONTEND_PID > /tmp/sintaxis_frontend.pid

    sleep 3
    log_success "Frontend iniciado (PID: $FRONTEND_PID)"
}

start_splash() {
    log_info "Mostrando splash screen..."

    cd "$SCRIPT_DIR"
    python3 Plan_ia/splash.py &
    SPLASH_PID=$!

    # Esperar a que termine el splash
    wait $SPLASH_PID 2>/dev/null || true
    log_success "Splash completado"
}

stop_services() {
    log_info "Deteniendo servicios..."

    # Detener backend
    if [ -f /tmp/sintaxis_backend.pid ]; then
        local pid=$(cat /tmp/sintaxis_backend.pid)
        if kill -0 $pid 2>/dev/null; then
            kill $pid 2>/dev/null || true
            log_success "Backend detenido (PID: $pid)"
        fi
        rm -f /tmp/sintaxis_backend.pid
    fi

    # Detener procesos uvicorn huerfanos
    pkill -f "uvicorn presentation.api.rest.main:app" 2>/dev/null || true

    # Detener frontend
    if [ -f /tmp/sintaxis_frontend.pid ]; then
        local pid=$(cat /tmp/sintaxis_frontend.pid)
        if kill -0 $pid 2>/dev/null; then
            kill $pid 2>/dev/null || true
            log_success "Frontend detenido (PID: $pid)"
        fi
        rm -f /tmp/sintaxis_frontend.pid
    fi

    # Detener procesos npm huerfanos del frontend
    pkill -f "vite.*$FRONTEND_DIR" 2>/dev/null || true

    log_success "Servicios detenidos"
}

open_browser() {
    log_info "Abriendo navegador..."
    sleep 2

    # macOS
    if command -v open &> /dev/null; then
        open "$FRONTEND_URL"
    # Linux
    elif command -v xdg-open &> /dev/null; then
        xdg-open "$FRONTEND_URL"
    # Windows (WSL)
    elif command -v cmd.exe &> /dev/null; then
        cmd.exe /c start "$FRONTEND_URL"
    else
        log_warn "No se pudo abrir el navegador automaticamente"
        log_info "Abre manualmente: $FRONTEND_URL"
    fi
}

show_status() {
    echo ""
    echo "=================================================="
    echo "  sintaXis - Sistema de Gestion Judicial v6"
    echo "=================================================="
    echo ""
    echo "  Frontend: $FRONTEND_URL"
    echo "  Backend:  $BACKEND_URL"
    echo "  API Docs: $BACKEND_URL/docs"
    echo ""
    echo "  Logs:"
    echo "    Backend:  /tmp/sintaxis_backend.log"
    echo "    Frontend: /tmp/sintaxis_frontend.log"
    echo ""
    echo "  Para detener: $0 --stop"
    echo "=================================================="
}

cleanup() {
    echo ""
    log_info "Recibida senal de interrupcion..."
    stop_services
    exit 0
}

# ============================================================================
# Main
# ============================================================================

# Capturar Ctrl+C
trap cleanup SIGINT SIGTERM

# Parsear argumentos
NO_SPLASH=false
BACKEND_ONLY=false
FRONTEND_ONLY=false
STOP=false
NO_BROWSER=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-splash)
            NO_SPLASH=true
            shift
            ;;
        --backend)
            BACKEND_ONLY=true
            shift
            ;;
        --frontend)
            FRONTEND_ONLY=true
            shift
            ;;
        --stop)
            STOP=true
            shift
            ;;
        --no-browser)
            NO_BROWSER=true
            shift
            ;;
        *)
            log_error "Opcion desconocida: $1"
            echo "Uso: $0 [--no-splash] [--backend] [--frontend] [--stop] [--no-browser]"
            exit 1
            ;;
    esac
done

# Ejecutar accion
if [ "$STOP" = true ]; then
    stop_services
    exit 0
fi

echo ""
echo "=================================================="
echo "  Iniciando sintaXis..."
echo "=================================================="
echo ""

# Iniciar servicios
if [ "$FRONTEND_ONLY" = false ]; then
    start_backend
fi

if [ "$BACKEND_ONLY" = false ]; then
    start_frontend
fi

# Mostrar splash (bloquea hasta terminar)
if [ "$NO_SPLASH" = false ] && [ "$BACKEND_ONLY" = false ]; then
    # Verificar si PySide6 esta disponible
    if python3 -c "import PySide6" 2>/dev/null; then
        start_splash
    else
        log_warn "PySide6 no instalado, omitiendo splash"
        log_info "Para instalar: pip install PySide6"
        sleep 2
    fi
fi

# Abrir navegador
if [ "$NO_BROWSER" = false ] && [ "$BACKEND_ONLY" = false ]; then
    open_browser
fi

# Mostrar estado
show_status

# Mantener script corriendo (para ver logs con Ctrl+C)
log_info "Sistema corriendo. Presiona Ctrl+C para detener."
echo ""

# Esperar indefinidamente
while true; do
    sleep 1
done
