#!/usr/bin/env python3
"""
Script principal para ejecutar la extracción incremental de expedientes.

Con integración opcional de procesador_pdf para clasificación y análisis.

Uso:
    python main_extraccion.py
    python main_extraccion.py --procesar
    python main_extraccion.py --procesar --dias-urgentes 5
"""

import argparse
import asyncio
import sys

try:
    from Sistema_v6.extractor_inicial.extraccion_inicial import extraccion_incremental_async, PROCESADOR_DISPONIBLE
except ImportError:
    print("❌ Error: No se pudo importar extraccion_inicial")
    print("   Asegúrate de ejecutar desde la raíz del proyecto")
    sys.exit(1)


def main():
    """Función principal con argumentos CLI."""
    parser = argparse.ArgumentParser(
        description="Extracción incremental de expedientes del PJN",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  %(prog)s                              # Extracción sin procesamiento
  %(prog)s --procesar                   # Extracción con procesamiento
  %(prog)s --procesar --dias-urgentes 3 # Procesar con umbral personalizado
  %(prog)s --no-procesar                # Explícitamente sin procesamiento
        """
    )

    parser.add_argument(
        "--procesar",
        action="store_true",
        help="Procesar expedientes con procesador_pdf (clasificación, vencimientos)"
    )

    parser.add_argument(
        "--no-procesar",
        action="store_true",
        help="NO procesar expedientes (solo extracción básica)"
    )

    parser.add_argument(
        "--dias-urgentes",
        type=int,
        default=7,
        help="Días para considerar un vencimiento como urgente (default: 7)"
    )

    args = parser.parse_args()

    # Determinar si procesar o no
    procesar = args.procesar

    if args.no_procesar and args.procesar:
        print("⚠️ Advertencia: --procesar y --no-procesar son mutuamente excluyentes")
        print("   Se usará --no-procesar (no se procesará)")
        procesar = False
    elif args.no_procesar:
        procesar = False

    # Verificar disponibilidad si se solicita procesamiento
    if procesar and not PROCESADOR_DISPONIBLE:
        print("⚠️ Advertencia: Procesamiento solicitado pero procesador_pdf no está disponible")
        print("   Se ejecutará solo la extracción básica")
        procesar = False

    # Mostrar configuración
    print("\n" + "=" * 70)
    print("EXTRACCIÓN INCREMENTAL DE EXPEDIENTES")
    print("=" * 70)
    print(f"\nConfiguración:")
    print(f"  Procesar expedientes: {'✅ SÍ' if procesar else '❌ NO'}")
    if procesar:
        print(f"  Días para urgencia: {args.dias_urgentes}")
    print(f"  procesador_pdf disponible: {'✅ SÍ' if PROCESADOR_DISPONIBLE else '❌ NO'}")
    print()

    # Ejecutar extracción
    try:
        asyncio.run(extraccion_incremental_async(procesar_expedientes=procesar))
    except KeyboardInterrupt:
        print("\n\n⚠️ Extracción cancelada por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error durante la extracción: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
