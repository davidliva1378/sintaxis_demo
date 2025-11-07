#!/bin/bash
# Script de Validación de Entorno
# Verifica que todo está listo para implementar la Solución 1

set -e

echo "🔍 VALIDACIÓN DE ENTORNO PARA UNIFICACIÓN DE EXTRACCIÓN MASIVA"
echo "================================================================"
echo ""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SUCCESS=0
WARNINGS=0
ERRORS=0

check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✅${NC} $1 está instalado"
        SUCCESS=$((SUCCESS + 1))
        return 0
    else
        echo -e "${RED}❌${NC} $1 NO está instalado"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✅${NC} $1 existe"
        SUCCESS=$((SUCCESS + 1))
        return 0
    else
        echo -e "${RED}❌${NC} $1 NO existe"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✅${NC} $1 existe"
        SUCCESS=$((SUCCESS + 1))
        return 0
    else
        echo -e "${RED}❌${NC} $1 NO existe"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

echo "1️⃣  VERIFICANDO HERRAMIENTAS BÁSICAS"
echo "────────────────────────────────────"
check_command python
check_command node
check_command npm
check_command git
echo ""

echo "2️⃣  VERIFICANDO VERSIONES"
echo "────────────────────────────────────"
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
NODE_VERSION=$(node --version 2>&1 | sed 's/v//')

echo "Python: $PYTHON_VERSION"
if [[ "$PYTHON_VERSION" > "3.10" ]]; then
    echo -e "${GREEN}✅${NC} Python >= 3.10"
    SUCCESS=$((SUCCESS + 1))
else
    echo -e "${YELLOW}⚠️${NC}  Python < 3.10 (recomendado: 3.10+)"
    WARNINGS=$((WARNINGS + 1))
fi

echo "Node: $NODE_VERSION"
if [[ "$NODE_VERSION" > "18.0" ]]; then
    echo -e "${GREEN}✅${NC} Node >= 18.0"
    SUCCESS=$((SUCCESS + 1))
else
    echo -e "${YELLOW}⚠️${NC}  Node < 18.0 (recomendado: 18+)"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

echo "3️⃣  VERIFICANDO ESTRUCTURA DEL PROYECTO"
echo "────────────────────────────────────"
cd /home/user/sintaXis
check_dir "Sistema_v6"
check_dir "Sistema_v6/application"
check_dir "Sistema_v6/application/use_cases"
check_dir "Sistema_v6/application/dtos"
check_dir "Sistema_v6/infrastructure"
check_dir "Sistema_v6/presentation"
check_dir "Sistema_v6/presentation/api"
check_dir "Sistema_v6/presentation/api/rest"
check_dir "Sistema_v6/frontend"
check_dir "Sistema_v6/frontend/src"
check_dir "Sistema_v6/extraccion_masiva"
echo ""

echo "4️⃣  VERIFICANDO ARCHIVOS CLAVE"
echo "────────────────────────────────────"
check_file "Sistema_v6/extraccion_masiva/extractor_masivo.py"
check_file "Sistema_v6/extraccion_masiva/gestor_batch.py"
check_file "Sistema_v6/extraccion_masiva/exportadores.py"
check_file "Sistema_v6/application/use_cases/__init__.py"
check_file "Sistema_v6/application/dtos/__init__.py"
check_file "Sistema_v6/infrastructure/di_container.py"
check_file "Sistema_v6/presentation/api/rest/main.py"
check_file "Sistema_v6/presentation/api/rest/routers/expedientes.py"
check_file "Sistema_v6/frontend/src/stores/expedientesStore.ts"
check_file "Sistema_v6/interfaz_web/backend/api/extraccion.py"
echo ""

echo "5️⃣  VERIFICANDO DEPENDENCIAS PYTHON"
echo "────────────────────────────────────"
cd /home/user/sintaXis/Sistema_v6

if python -c "import fastapi" 2>/dev/null; then
    echo -e "${GREEN}✅${NC} fastapi instalado"
    SUCCESS=$((SUCCESS + 1))
else
    echo -e "${RED}❌${NC} fastapi NO instalado"
    ERRORS=$((ERRORS + 1))
fi

if python -c "import pydantic" 2>/dev/null; then
    echo -e "${GREEN}✅${NC} pydantic instalado"
    SUCCESS=$((SUCCESS + 1))
else
    echo -e "${RED}❌${NC} pydantic NO instalado"
    ERRORS=$((ERRORS + 1))
fi

if python -c "import uvicorn" 2>/dev/null; then
    echo -e "${GREEN}✅${NC} uvicorn instalado"
    SUCCESS=$((SUCCESS + 1))
else
    echo -e "${RED}❌${NC} uvicorn NO instalado"
    ERRORS=$((ERRORS + 1))
fi
echo ""

echo "6️⃣  VERIFICANDO MÓDULOS PYTHON DEL PROYECTO"
echo "────────────────────────────────────"
export PYTHONPATH="${PYTHONPATH}:/home/user/sintaXis/Sistema_v6"

if python -c "from Sistema_v6.extraccion_masiva import ExtractorMasivo" 2>/dev/null; then
    echo -e "${GREEN}✅${NC} ExtractorMasivo importable"
    SUCCESS=$((SUCCESS + 1))
else
    echo -e "${RED}❌${NC} ExtractorMasivo NO importable"
    ERRORS=$((ERRORS + 1))
fi

if python -c "from application.use_cases import ExtraerExpedientesUseCase" 2>/dev/null; then
    echo -e "${GREEN}✅${NC} Use cases importables"
    SUCCESS=$((SUCCESS + 1))
else
    echo -e "${RED}❌${NC} Use cases NO importables"
    ERRORS=$((ERRORS + 1))
fi

if python -c "from infrastructure.di_container import get_container" 2>/dev/null; then
    echo -e "${GREEN}✅${NC} DI Container importable"
    SUCCESS=$((SUCCESS + 1))
else
    echo -e "${RED}❌${NC} DI Container NO importable"
    ERRORS=$((ERRORS + 1))
fi
echo ""

echo "7️⃣  VERIFICANDO DEPENDENCIAS FRONTEND"
echo "────────────────────────────────────"
cd /home/user/sintaXis/Sistema_v6/frontend

if [ -f "package.json" ]; then
    echo -e "${GREEN}✅${NC} package.json existe"
    SUCCESS=$((SUCCESS + 1))

    if [ -d "node_modules" ]; then
        echo -e "${GREEN}✅${NC} node_modules existe"
        SUCCESS=$((SUCCESS + 1))

        if [ -d "node_modules/zustand" ]; then
            echo -e "${GREEN}✅${NC} zustand instalado"
            SUCCESS=$((SUCCESS + 1))
        else
            echo -e "${YELLOW}⚠️${NC}  zustand NO instalado (ejecutar: npm install)"
            WARNINGS=$((WARNINGS + 1))
        fi

        if [ -d "node_modules/axios" ]; then
            echo -e "${GREEN}✅${NC} axios instalado"
            SUCCESS=$((SUCCESS + 1))
        else
            echo -e "${YELLOW}⚠️${NC}  axios NO instalado (ejecutar: npm install)"
            WARNINGS=$((WARNINGS + 1))
        fi
    else
        echo -e "${YELLOW}⚠️${NC}  node_modules NO existe (ejecutar: npm install)"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "${RED}❌${NC} package.json NO existe"
    ERRORS=$((ERRORS + 1))
fi
echo ""

echo "8️⃣  VERIFICANDO DOCUMENTACIÓN DEL PLAN"
echo "────────────────────────────────────"
cd /home/user/sintaXis
check_file "PLAN_UNIFICACION_EXTRACCION_MASIVA.md"
check_file "CHECKLIST_IMPLEMENTACION.md"
check_file "REFERENCIA_ROUTER_EXTRACCION_MASIVA.py"
check_file "REFERENCIA_FRONTEND_UPDATES.md"
check_file "README_IMPLEMENTACION.md"
echo ""

echo "9️⃣  VERIFICANDO GIT"
echo "────────────────────────────────────"
cd /home/user/sintaXis

if git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC} Repositorio git válido"
    SUCCESS=$((SUCCESS + 1))

    CURRENT_BRANCH=$(git branch --show-current)
    echo "Rama actual: $CURRENT_BRANCH"

    if [ "$CURRENT_BRANCH" = "sintaxis_parcial" ]; then
        echo -e "${GREEN}✅${NC} En rama sintaxis_parcial"
        SUCCESS=$((SUCCESS + 1))
    else
        echo -e "${YELLOW}⚠️${NC}  No estás en rama sintaxis_parcial"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "${RED}❌${NC} NO es un repositorio git válido"
    ERRORS=$((ERRORS + 1))
fi
echo ""

echo "🔟  VERIFICANDO PUERTOS DISPONIBLES"
echo "────────────────────────────────────"
if ! lsof -i:8000 > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC} Puerto 8000 disponible (backend)"
    SUCCESS=$((SUCCESS + 1))
else
    echo -e "${YELLOW}⚠️${NC}  Puerto 8000 en uso"
    WARNINGS=$((WARNINGS + 1))
fi

if ! lsof -i:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC} Puerto 3000 disponible (frontend)"
    SUCCESS=$((SUCCESS + 1))
else
    echo -e "${YELLOW}⚠️${NC}  Puerto 3000 en uso"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

echo "================================================================"
echo "📊 RESUMEN DE VALIDACIÓN"
echo "================================================================"
echo -e "${GREEN}✅ Éxitos:${NC} $SUCCESS"
echo -e "${YELLOW}⚠️  Advertencias:${NC} $WARNINGS"
echo -e "${RED}❌ Errores:${NC} $ERRORS"
echo ""

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}🎉 ¡ENTORNO LISTO PARA IMPLEMENTACIÓN!${NC}"
    echo ""
    echo "Siguiente paso:"
    echo "  1. Lee el plan: cat PLAN_UNIFICACION_EXTRACCION_MASIVA.md"
    echo "  2. Sigue el checklist: cat CHECKLIST_IMPLEMENTACION.md"
    echo "  3. Comienza con el Paso 1"
    echo ""
    exit 0
elif [ $ERRORS -le 3 ] && [ $WARNINGS -le 5 ]; then
    echo -e "${YELLOW}⚠️  ENTORNO CON ADVERTENCIAS - Puedes continuar con precaución${NC}"
    echo ""
    echo "Recomendaciones:"
    echo "  - Revisa los errores mencionados arriba"
    echo "  - Instala dependencias faltantes si es necesario"
    echo "  - Continúa con la implementación"
    echo ""
    exit 0
else
    echo -e "${RED}❌ ENTORNO NO LISTO - Corrige los errores antes de continuar${NC}"
    echo ""
    echo "Acciones requeridas:"
    echo "  1. Instala las herramientas faltantes"
    echo "  2. Instala las dependencias de Python: pip install -r requirements.txt"
    echo "  3. Instala las dependencias de Node: cd Sistema_v6/frontend && npm install"
    echo "  4. Vuelve a ejecutar este script: bash validar_entorno.sh"
    echo ""
    exit 1
fi
