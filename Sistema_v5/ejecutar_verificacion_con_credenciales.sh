#!/bin/bash

echo "🔐 Cargando credenciales..."
source ~/.pjn_credentials.sh

echo "✅ Credenciales cargadas"
echo "   Usuario: $PJN_USER"
echo ""

echo "🔍 Iniciando verificación de actualización automática de manifests..."
echo ""

cd /Users/davidalejandroliva/PycharmProjects/sintaXis/Sistema_v5

python verificar_actualizacion_manifests.py

echo ""
echo "✅ Verificación completada"
