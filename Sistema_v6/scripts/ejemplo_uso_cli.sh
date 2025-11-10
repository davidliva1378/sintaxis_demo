#!/bin/bash
# Ejemplo de uso del CLI del Sistema PJN v6
#
# Este script demuestra los comandos principales del CLI.
# Ejecutar desde el directorio raíz del proyecto Sistema_v6.

echo "=== Ejemplos de uso del CLI - Sistema PJN v6 ==="
echo ""

# 1. Ver ayuda general
echo "1. Ayuda general:"
python -m presentation.cli.main --help
echo ""

# 2. Ver información del sistema
echo "2. Información del sistema:"
python -m presentation.cli.main info
echo ""

# 3. Extraer expedientes (requiere credenciales)
echo "3. Extraer expedientes:"
echo "   python -m presentation.cli.main extraer --usuario 20123456789 --password XXXXX"
echo "   (Requiere scraping implementado)"
echo ""

# 4. Filtrar expedientes
echo "4. Filtrar expedientes:"
echo "   python -m presentation.cli.main filtrar \\"
echo "     --origen datos/expedientes_base.json \\"
echo "     --destino datos/expedientes_sistema.json \\"
echo "     --numeros \"CNM 0001/2024\" \"CNM 0002/2024\" \\"
echo "     --activos"
echo ""

# 5. Crear workspaces
echo "5. Crear workspaces:"
echo "   python -m presentation.cli.main workspace \\"
echo "     --sistema datos/expedientes_sistema.json \\"
echo "     --workspaces-dir datos/workspaces"
echo ""

# 6. Monitorear cambios
echo "6. Monitorear cambios:"
echo "   python -m presentation.cli.main monitorear \\"
echo "     --sistema datos/expedientes_sistema.json \\"
echo "     --workspaces-dir datos/workspaces \\"
echo "     --intervalo 60 \\"
echo "     --notificar"
echo ""

echo "=== Para ejecutar estos comandos, descomenta las líneas correspondientes ==="
