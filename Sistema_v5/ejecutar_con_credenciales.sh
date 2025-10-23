#!/bin/bash

echo "🔐 Cargando credenciales..."
source ~/.pjn_credentials.sh

echo "✅ Credenciales cargadas"
echo "   Usuario: $PJN_USER"
echo ""

echo "🚀 Iniciando descarga completa de expedientes..."
echo ""

cd /Users/davidalejandroliva/PycharmProjects/sintaXis/Sistema_v5

python ejecutar_extraccion_inicial_v2.py \
  --headless \
  --desde-json configuracion/gui/data/extraccion_inicial/expedientes_20251023_154733.json

echo ""
echo "✅ Proceso completado"
