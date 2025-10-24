#!/usr/bin/env python3
"""Script auxiliar para seleccionar expedientes desde un JSON ya extraído.

Uso:
    python seleccionar_expedientes.py [ruta_al_json]

Si no se proporciona ruta, usa el JSON más reciente en data/extraccion_inicial/
"""

from __future__ import annotations

import sys
from pathlib import Path

# Configurar paths
SISTEMA_V5_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SISTEMA_V5_DIR.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Sistema_v5.extractor_inicial import cargar_json, mostrar_filtros_avanzados


def encontrar_ultimo_json() -> Path | None:
    """Encuentra el JSON más reciente en extraccion_inicial."""
    extraccion_dir = SISTEMA_V5_DIR / "configuracion" / "gui" / "data" / "extraccion_inicial"

    if not extraccion_dir.exists():
        return None

    archivos = sorted(extraccion_dir.glob("expedientes_*.json"), reverse=True)
    return archivos[0] if archivos else None


def main():
    """Función principal."""
    # Determinar archivo JSON
    if len(sys.argv) > 1:
        json_path = Path(sys.argv[1])
    else:
        json_path = encontrar_ultimo_json()
        if json_path is None:
            print("❌ No se encontró ningún archivo de extracción inicial")
            print("   Ejecuta primero: python ejecutar_extraccion_inicial_v2.py --headless")
            sys.exit(1)

    if not json_path.exists():
        print(f"❌ Archivo no encontrado: {json_path}")
        sys.exit(1)

    print(f"📄 Cargando expedientes desde: {json_path.name}")

    # Cargar expedientes
    try:
        expedientes, metadata = cargar_json(json_path)
    except Exception as e:
        print(f"❌ Error al cargar JSON: {e}")
        sys.exit(1)

    print(f"✅ Cargados {len(expedientes)} expedientes")
    print(f"   Timestamp: {metadata.get('timestamp', 'N/A')}")
    print()
    print("🔍 Abriendo GUI de filtros...")

    # Mostrar GUI de filtros
    seleccion = mostrar_filtros_avanzados(
        expedientes,
        titulo="Selección de Expedientes para Descarga Completa"
    )

    if seleccion is None:
        print("❌ Usuario canceló la selección")
        sys.exit(0)

    print(f"\n✅ Usuario seleccionó {len(seleccion)} expedientes:")
    print()
    for i, exp in enumerate(seleccion[:10], 1):
        print(f"   {i}. {exp.numero} - {exp.caratula[:60]}")

    if len(seleccion) > 10:
        print(f"   ... y {len(seleccion) - 10} más")

    print()
    print("💾 Para procesar estos expedientes, ejecuta:")
    print(f"   python ejecutar_extraccion_completa.py --json {json_path}")


if __name__ == "__main__":
    main()
