#!/usr/bin/env python3
"""
Script para procesar actuaciones desde archivos JSON existentes.

Este script permite clasificar y analizar actuaciones que ya fueron
extraídas previamente, sin necesidad de volver a extraerlas del PJN.

Uso:
    python procesar_actuaciones_json.py <ruta_json>
    python procesar_actuaciones_json.py <ruta_json> --dias-urgentes 5
    python procesar_actuaciones_json.py <carpeta_con_jsons> --recursivo

Ejemplos:
    # Procesar un único archivo
    python procesar_actuaciones_json.py datos_extraidos/expediente_123.json

    # Procesar todos los JSON de una carpeta
    python procesar_actuaciones_json.py datos_extraidos/monitoreo/ --recursivo

    # Cambiar umbral de urgencia de vencimientos
    python procesar_actuaciones_json.py datos.json --dias-urgentes 3
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List

try:
    from Sistema_v6.extractor_inicial.procesamiento_expedientes import (
        clasificar_actuaciones_desde_json,
        PROCESADOR_DISPONIBLE
    )
except ImportError:
    print("❌ Error: No se pudo importar el módulo de procesamiento")
    print("   Asegúrate de que procesador_pdf esté instalado")
    sys.exit(1)


def procesar_archivo(ruta_json: Path, config: dict) -> dict:
    """
    Procesa un archivo JSON con actuaciones.

    Args:
        ruta_json: Path al archivo JSON
        config: Configuración para el procesamiento

    Returns:
        Dict con resultados del procesamiento
    """
    print(f"\n{'=' * 70}")
    print(f"📄 Procesando: {ruta_json.name}")
    print(f"{'=' * 70}")

    try:
        resultado = clasificar_actuaciones_desde_json(ruta_json, config)

        # Mostrar resumen
        stats = resultado.get("estadisticas", {})
        print(f"\n📊 ESTADÍSTICAS:")
        print(f"  Total actuaciones: {resultado['total_actuaciones']}")
        print(f"  Utilidad ALTA:     {stats.get('alta', 0)} ({stats.get('porcentajes', {}).get('alta', 0)}%)")
        print(f"  Utilidad MEDIA:    {stats.get('media', 0)} ({stats.get('porcentajes', {}).get('media', 0)}%)")
        print(f"  Utilidad BAJA:     {stats.get('baja', 0)} ({stats.get('porcentajes', {}).get('baja', 0)}%)")
        print(f"  Utilidad NULA:     {stats.get('nula', 0)} ({stats.get('porcentajes', {}).get('nula', 0)}%)")

        # Mostrar vencimientos si hay
        vencimientos = resultado.get("vencimientos", [])
        if vencimientos:
            urgentes = [v for v in vencimientos if v.get("es_urgente", False)]
            print(f"\n⏰ VENCIMIENTOS:")
            print(f"  Total detectados: {len(vencimientos)}")
            if urgentes:
                print(f"  ⚠️  URGENTES (≤{config['dias_urgentes']} días): {len(urgentes)}")

                # Mostrar los primeros 3 urgentes
                print(f"\n  Vencimientos urgentes:")
                for v in urgentes[:3]:
                    print(f"    • {v['tipo']} - Vence: {v['fecha_vencimiento']} ({v['dias_restantes']} días)")

        # Guardar resultado
        carpeta_salida = ruta_json.parent / "reportes_procesamiento"
        carpeta_salida.mkdir(parents=True, exist_ok=True)

        nombre_reporte = ruta_json.stem + "_procesado.json"
        ruta_reporte = carpeta_salida / nombre_reporte

        with open(ruta_reporte, "w", encoding="utf-8") as f:
            json.dump(resultado, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Reporte guardado en: {ruta_reporte}")

        return resultado

    except FileNotFoundError:
        print(f"❌ Archivo no encontrado: {ruta_json}")
        return None
    except json.JSONDecodeError:
        print(f"❌ Error: El archivo no es un JSON válido")
        return None
    except Exception as e:
        print(f"❌ Error procesando archivo: {e}")
        return None


def procesar_carpeta(carpeta: Path, config: dict, recursivo: bool = False) -> List[dict]:
    """
    Procesa todos los archivos JSON de una carpeta.

    Args:
        carpeta: Path a la carpeta
        config: Configuración para el procesamiento
        recursivo: Si buscar en subcarpetas

    Returns:
        Lista de resultados de procesamiento
    """
    patron = "**/*.json" if recursivo else "*.json"
    archivos_json = list(carpeta.glob(patron))

    # Filtrar archivos que no sean reportes procesados
    archivos_json = [
        f for f in archivos_json
        if not f.stem.endswith("_procesado") and "reportes_procesamiento" not in str(f)
    ]

    if not archivos_json:
        print(f"⚠️ No se encontraron archivos JSON en {carpeta}")
        return []

    print(f"📁 Encontrados {len(archivos_json)} archivos JSON")

    resultados = []
    for archivo in archivos_json:
        resultado = procesar_archivo(archivo, config)
        if resultado:
            resultados.append(resultado)

    return resultados


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description="Procesa actuaciones desde archivos JSON con procesador_pdf",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  %(prog)s datos.json
  %(prog)s carpeta_expedientes/ --recursivo
  %(prog)s datos.json --dias-urgentes 3 --analizar-vencimientos
        """
    )

    parser.add_argument(
        "ruta",
        type=str,
        help="Ruta al archivo JSON o carpeta con archivos JSON"
    )

    parser.add_argument(
        "--recursivo",
        "-r",
        action="store_true",
        help="Buscar archivos JSON recursivamente en subcarpetas"
    )

    parser.add_argument(
        "--dias-urgentes",
        type=int,
        default=7,
        help="Número de días para considerar un vencimiento como urgente (default: 7)"
    )

    parser.add_argument(
        "--no-vencimientos",
        action="store_true",
        help="Desactivar análisis de vencimientos"
    )

    args = parser.parse_args()

    # Verificar que procesador_pdf esté disponible
    if not PROCESADOR_DISPONIBLE:
        print("❌ Error: procesador_pdf no está disponible")
        print("   Instala las dependencias con: pip install -r Sistema_v5/procesador_pdf/requirements.txt")
        sys.exit(1)

    # Preparar configuración
    config = {
        "clasificar": True,
        "analizar_vencimientos": not args.no_vencimientos,
        "dias_urgentes": args.dias_urgentes,
    }

    # Procesar ruta
    ruta = Path(args.ruta)

    if not ruta.exists():
        print(f"❌ Error: La ruta no existe: {ruta}")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("🔄 PROCESAMIENTO DE ACTUACIONES CON procesador_pdf")
    print("=" * 70)
    print(f"\nConfiguración:")
    print(f"  Clasificar: {config['clasificar']}")
    print(f"  Analizar vencimientos: {config['analizar_vencimientos']}")
    print(f"  Días urgentes: {config['dias_urgentes']}")

    # Procesar según tipo de ruta
    if ruta.is_file():
        if ruta.suffix != ".json":
            print(f"⚠️ Advertencia: El archivo no tiene extensión .json")

        resultado = procesar_archivo(ruta, config)

        if resultado:
            print("\n" + "=" * 70)
            print("✅ PROCESAMIENTO COMPLETADO")
            print("=" * 70)
        else:
            print("\n❌ El procesamiento falló")
            sys.exit(1)

    elif ruta.is_dir():
        resultados = procesar_carpeta(ruta, config, args.recursivo)

        print("\n" + "=" * 70)
        print(f"✅ PROCESAMIENTO COMPLETADO: {len(resultados)} archivos procesados")
        print("=" * 70)

        # Resumen consolidado
        if resultados:
            total_actuaciones = sum(r["total_actuaciones"] for r in resultados)
            total_vencimientos_urgentes = sum(
                len([v for v in r.get("vencimientos", []) if v.get("es_urgente", False)])
                for r in resultados
            )

            print(f"\n📊 RESUMEN CONSOLIDADO:")
            print(f"  Archivos procesados: {len(resultados)}")
            print(f"  Total actuaciones: {total_actuaciones}")
            if total_vencimientos_urgentes > 0:
                print(f"  ⚠️  Vencimientos urgentes: {total_vencimientos_urgentes}")

    else:
        print(f"❌ Error: La ruta no es un archivo ni un directorio válido")
        sys.exit(1)


if __name__ == "__main__":
    main()
