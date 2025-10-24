#!/bin/bash

echo "🚀 Ejecutando Monitor Universal con actualización de actuaciones..."
echo "=================================================="
echo ""

# Cargar credenciales si existen
if [ -f ~/.pjn_credentials ]; then
    source ~/.pjn_credentials
    echo "✅ Credenciales cargadas"
else
    echo "⚠️  No se encontraron credenciales en ~/.pjn_credentials"
    echo "   Asegúrate de tener las variables PJN_USERNAME y PJN_PASSWORD configuradas"
fi

echo ""
echo "Configuración actual:"
echo "  - actualizar_actuaciones_automaticamente: true"
echo "  - max_reintentos_actualizacion_actuaciones: 3"
echo ""
echo "El monitor se ejecutará y actualizará actuaciones cuando detecte cambios..."
echo "Presiona Ctrl+C para detener"
echo ""
echo "=================================================="
echo ""

cd Sistema_v5
python -m monitor.universal --verificar-una-vez

echo ""
echo "=================================================="
echo "Monitor finalizado"
