#!/usr/bin/env python3
"""Script de verificación post-extracción inicial.

Este script ayuda a verificar que la extracción inicial se completó
correctamente y muestra un resumen de los resultados.

Uso:
    cd Sistema_v5
    python verificar_extraccion.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime

# Configurar paths
SISTEMA_V5_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SISTEMA_V5_DIR.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def verificar_directorios() -> dict:
    """Verifica directorios de expedientes creados."""
    print("\n" + "=" * 60)
    print("📁 VERIFICACIÓN DE DIRECTORIOS")
    print("=" * 60)

    expedientes_dir = SISTEMA_V5_DIR / "data" / "expedientes"

    if not expedientes_dir.exists():
        print("❌ No existe el directorio data/expedientes/")
        print(f"   Ruta esperada: {expedientes_dir}")
        return {"total": 0, "con_actuaciones": 0, "con_adjuntos": 0}

    # Contar directorios de expedientes
    directorios = [d for d in expedientes_dir.iterdir() if d.is_dir()]
    total = len(directorios)

    # Verificar contenido
    con_expediente_json = 0
    con_actuaciones_json = 0
    con_adjuntos = 0

    for exp_dir in directorios:
        if (exp_dir / "expediente.json").exists():
            con_expediente_json += 1
        if (exp_dir / "actuaciones.json").exists():
            con_actuaciones_json += 1
        if (exp_dir / "adjuntos").exists() and any((exp_dir / "adjuntos").iterdir()):
            con_adjuntos += 1

    print(f"\n📊 Resumen de directorios:")
    print(f"   Total directorios creados: {total}")
    print(f"   Con expediente.json: {con_expediente_json}")
    print(f"   Con actuaciones.json: {con_actuaciones_json}")
    print(f"   Con adjuntos descargados: {con_adjuntos}")

    if total > 0:
        print(f"\n✅ Estructura correcta: {con_expediente_json}/{total} expedientes")

        # Mostrar ejemplos
        print(f"\n📝 Primeros 5 expedientes:")
        for exp_dir in sorted(directorios)[:5]:
            print(f"   - {exp_dir.name}")
    else:
        print("\n⚠️  No se encontraron directorios de expedientes")

    return {
        "total": total,
        "con_expediente_json": con_expediente_json,
        "con_actuaciones": con_actuaciones_json,
        "con_adjuntos": con_adjuntos,
    }


def verificar_reportes() -> dict | None:
    """Verifica reportes de extracción."""
    print("\n" + "=" * 60)
    print("📊 VERIFICACIÓN DE REPORTES")
    print("=" * 60)

    reportes_dir = SISTEMA_V5_DIR / "data" / "reportes"

    if not reportes_dir.exists():
        print("❌ No existe el directorio data/reportes/")
        return None

    # Buscar reportes de extracción
    reportes = sorted(reportes_dir.glob("extraccion_*.json"))

    if not reportes:
        print("⚠️  No se encontraron reportes de extracción")
        return None

    # Leer último reporte
    ultimo_reporte = reportes[-1]
    print(f"\n📄 Último reporte: {ultimo_reporte.name}")

    try:
        data = json.loads(ultimo_reporte.read_text(encoding="utf-8"))
        resumen = data.get("resumen", {})

        print(f"\n📈 Resumen de extracción:")
        print(f"   Total procesado: {resumen.get('total', 0)}")
        print(f"   ✅ Exitosos: {resumen.get('exitosos', 0)}")
        print(f"   ❌ Errores: {resumen.get('errores', 0)}")
        print(f"   ⊘  Omitidos: {resumen.get('omitidos', 0)}")
        print(f"   ⏱️  Duración: {resumen.get('duracion_segundos', 0):.1f} segundos")
        print(f"   🕐 Inicio: {resumen.get('tiempo_inicio', 'N/A')}")
        print(f"   🕐 Fin: {resumen.get('tiempo_fin', 'N/A')}")

        # Mostrar errores si los hay
        if resumen.get('errores', 0) > 0:
            print(f"\n⚠️  Expedientes con errores:")
            resultados = data.get("resultados", [])
            errores = [r for r in resultados if r.get("estado") == "error"]
            for error in errores[:5]:  # Mostrar primeros 5
                print(f"   - {error.get('numero')}: {error.get('mensaje')}")
            if len(errores) > 5:
                print(f"   ... y {len(errores) - 5} más")

        return resumen

    except Exception as e:
        print(f"❌ Error al leer reporte: {e}")
        return None


def verificar_logs() -> None:
    """Verifica logs de extracción."""
    print("\n" + "=" * 60)
    print("📝 VERIFICACIÓN DE LOGS")
    print("=" * 60)

    log_file = SISTEMA_V5_DIR / "logs" / "extraccion_inicial_v2.log"

    if not log_file.exists():
        print("⚠️  No se encontró el archivo de log")
        print(f"   Ruta esperada: {log_file}")
        return

    print(f"\n📄 Log: {log_file.name}")
    print(f"   Tamaño: {log_file.stat().st_size / 1024:.1f} KB")

    # Leer últimas líneas
    try:
        lines = log_file.read_text(encoding="utf-8").split("\n")

        # Buscar líneas importantes
        errores = [l for l in lines if "ERROR" in l or "❌" in l]
        warnings = [l for l in lines if "WARNING" in l or "⚠️" in l]
        exito = [l for l in lines if "COMPLETADA CON ÉXITO" in l]

        print(f"\n📊 Análisis del log:")
        print(f"   Total líneas: {len(lines)}")
        print(f"   Errores: {len(errores)}")
        print(f"   Warnings: {len(warnings)}")

        if exito:
            print(f"   ✅ Extracción completada exitosamente")
        else:
            print(f"   ⚠️  No se encontró mensaje de éxito")

        # Mostrar últimas 10 líneas
        print(f"\n📄 Últimas 10 líneas del log:")
        for line in lines[-10:]:
            if line.strip():
                print(f"   {line[:80]}")

    except Exception as e:
        print(f"❌ Error al leer log: {e}")


def verificar_listado_inicial() -> dict | None:
    """Verifica archivo de listado inicial."""
    print("\n" + "=" * 60)
    print("📋 VERIFICACIÓN DE LISTADO INICIAL")
    print("=" * 60)

    extraccion_dir = SISTEMA_V5_DIR / "data" / "extraccion_inicial"

    if not extraccion_dir.exists():
        print("⚠️  No existe el directorio data/extraccion_inicial/")
        return None

    # Buscar archivos JSON
    archivos_json = sorted(extraccion_dir.glob("expedientes_*.json"))

    if not archivos_json:
        print("⚠️  No se encontraron archivos de listado inicial")
        return None

    # Leer último archivo
    ultimo_archivo = archivos_json[-1]
    print(f"\n📄 Último listado: {ultimo_archivo.name}")

    try:
        data = json.loads(ultimo_archivo.read_text(encoding="utf-8"))

        metadata = data.get("metadata", {})
        expedientes = data.get("expedientes", [])

        print(f"\n📊 Información del listado:")
        print(f"   Versión: {metadata.get('version', 'N/A')}")
        print(f"   Timestamp: {metadata.get('timestamp', 'N/A')}")
        print(f"   Total expedientes: {metadata.get('total_expedientes', len(expedientes))}")

        # Verificar CSV asociado
        csv_file = ultimo_archivo.with_suffix(".csv")
        if csv_file.exists():
            print(f"   ✅ CSV asociado: {csv_file.name}")
        else:
            print(f"   ⚠️  No se encontró CSV asociado")

        return {
            "total": len(expedientes),
            "metadata": metadata,
        }

    except Exception as e:
        print(f"❌ Error al leer listado: {e}")
        return None


def generar_resumen_final(dir_stats: dict, reporte: dict | None, listado: dict | None) -> None:
    """Genera resumen final de la verificación."""
    print("\n" + "=" * 60)
    print("🎯 RESUMEN FINAL")
    print("=" * 60)

    # Estado general
    print(f"\n✅ Estado de la extracción inicial:")

    total_directorios = dir_stats.get("total", 0)
    exitosos = reporte.get("exitosos", 0) if reporte else 0
    errores = reporte.get("errores", 0) if reporte else 0

    if total_directorios > 0:
        print(f"   ✅ Directorios creados: {total_directorios}")
        print(f"   ✅ Expedientes procesados exitosamente: {exitosos}")

        if errores > 0:
            print(f"   ⚠️  Expedientes con errores: {errores}")

        porcentaje = (exitosos / total_directorios * 100) if total_directorios > 0 else 0
        print(f"   📊 Tasa de éxito: {porcentaje:.1f}%")
    else:
        print(f"   ❌ No se crearon directorios de expedientes")

    # Próximos pasos
    print(f"\n📌 Próximos pasos:")

    if total_directorios > 0:
        print(f"   1. ✅ La extracción inicial está completa")
        print(f"   2. 🔄 Configurar y ejecutar el monitor:")
        print(f"      cd Sistema_v5")
        print(f"      python ejecutar_monitor.py")
        print(f"   3. 📖 Consultar: docs/FLUJO_COMPLETO_SISTEMA.md")
    else:
        print(f"   1. ⚠️  Ejecutar extracción inicial:")
        print(f"      cd Sistema_v5")
        print(f"      python ejecutar_extraccion_inicial_v2.py --headless")
        print(f"   2. 📖 Consultar: docs/GUIA_EXTRACCION_INICIAL_V2.md")

    print()


def main():
    """Función principal."""
    print("\n" + "🔍" * 30)
    print("VERIFICACIÓN POST-EXTRACCIÓN INICIAL")
    print("🔍" * 30)

    # Ejecutar verificaciones
    dir_stats = verificar_directorios()
    listado = verificar_listado_inicial()
    reporte = verificar_reportes()
    verificar_logs()

    # Resumen final
    generar_resumen_final(dir_stats, reporte, listado)


if __name__ == "__main__":
    main()
