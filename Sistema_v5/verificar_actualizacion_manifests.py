#!/usr/bin/env python3
"""Script para verificar que la actualización automática de manifests funciona correctamente.

Este script:
1. Lee algunos manifests existentes
2. Ejecuta un ciclo de monitoreo
3. Verifica que los manifests se actualizaron con historial_cambios

Uso (desde directorio Sistema_v5):
    python verificar_actualizacion_manifests.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Configurar paths
SISTEMA_V5_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SISTEMA_V5_DIR.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Sistema_v5.configuracion.core import SystemConfig
from Sistema_v5.pjn.monitor import MonitorPJN, MonitorConfig
from Sistema_v5.pjn.utils.logging import setup_logging, get_logger

logger = get_logger(__name__)


def leer_manifests_existentes(config: SystemConfig, max_count: int = 5) -> list[dict]:
    """Lee algunos manifests existentes para verificar antes/después."""
    # Usar directorio de configuración
    expedientes_dir = Path(config.directorio_expedientes_base)

    if not expedientes_dir.exists():
        logger.warning(f"❌ No existe directorio de expedientes: {expedientes_dir}")
        return []

    manifests = []

    # Buscar manifests en subdirectorios
    for subdir in expedientes_dir.iterdir():
        if not subdir.is_dir():
            continue

        manifest_path = subdir / "manifest.json"
        if not manifest_path.exists():
            continue

        try:
            manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifests.append({
                "path": manifest_path,
                "numero": manifest_data.get("metadata", {}).get("numero_expediente", "???"),
                "data_antes": manifest_data,
            })

            if len(manifests) >= max_count:
                break
        except Exception as e:
            logger.warning(f"Error leyendo manifest {manifest_path}: {e}")

    return manifests


def comparar_manifests(manifests_antes: list[dict]) -> None:
    """Compara manifests antes y después del monitoreo."""
    cambios_detectados = 0

    logger.info("")
    logger.info("=" * 60)
    logger.info("COMPARACIÓN DE MANIFESTS")
    logger.info("=" * 60)

    for info in manifests_antes:
        manifest_path = info["path"]
        numero = info["numero"]
        data_antes = info["data_antes"]

        # Leer manifest actualizado
        try:
            data_despues = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error(f"❌ Error leyendo manifest actualizado {numero}: {e}")
            continue

        # Verificar cambios
        metadata_antes = data_antes.get("metadata", {})
        metadata_despues = data_despues.get("metadata", {})

        # Verificar historial_cambios
        historial_antes = metadata_antes.get("historial_cambios", [])
        historial_despues = metadata_despues.get("historial_cambios", [])

        # Verificar estado_portal
        portal_antes = metadata_antes.get("estado_portal", {})
        portal_despues = metadata_despues.get("estado_portal", {})

        # Verificar procesamiento.ultima_sincronizacion
        proc_antes = metadata_antes.get("procesamiento", {})
        proc_despues = metadata_despues.get("procesamiento", {})
        sincro_antes = proc_antes.get("ultima_sincronizacion")
        sincro_despues = proc_despues.get("ultima_sincronizacion")

        logger.info("")
        logger.info(f"📄 Expediente: {numero}")
        logger.info(f"   Ruta: {manifest_path.relative_to(SISTEMA_V5_DIR)}")

        # Análisis de cambios
        tiene_cambios = False

        if len(historial_despues) > len(historial_antes):
            nuevas_entradas = len(historial_despues) - len(historial_antes)
            logger.info(f"   ✅ Historial actualizado: +{nuevas_entradas} entrada(s)")

            # Mostrar últimas entradas
            for entrada in historial_despues[-nuevas_entradas:]:
                tipo = entrada.get("tipo", "???")
                timestamp = entrada.get("timestamp", "???")
                logger.info(f"      - {timestamp}: {tipo}")

            tiene_cambios = True

        if portal_despues != portal_antes:
            logger.info(f"   ✅ Estado portal actualizado")
            for campo in ["situacion", "dependencia", "caratula", "ultima_actuacion"]:
                if portal_antes.get(campo) != portal_despues.get(campo):
                    logger.info(f"      - {campo}: '{portal_antes.get(campo)}' → '{portal_despues.get(campo)}'")
            tiene_cambios = True

        if sincro_despues != sincro_antes:
            logger.info(f"   ✅ Sincronización actualizada: {sincro_antes} → {sincro_despues}")
            tiene_cambios = True

        if not tiene_cambios:
            logger.info(f"   ℹ️  Sin cambios detectados")
        else:
            cambios_detectados += 1

    logger.info("")
    logger.info("=" * 60)
    logger.info(f"RESUMEN: {cambios_detectados}/{len(manifests_antes)} manifests con cambios")
    logger.info("=" * 60)


async def main() -> int:
    """Función principal de verificación."""
    # Configurar logging
    log_dir = SISTEMA_V5_DIR / "logs"
    log_dir.mkdir(exist_ok=True)
    setup_logging(
        level="INFO",
        log_file=log_dir / "verificacion_manifests.log",
    )

    logger.info("🔍 Verificación de Actualización Automática de Manifests")
    logger.info("=" * 60)

    try:
        # Cargar configuración
        config_path = SISTEMA_V5_DIR / ".." / "config" / "sistema.json"
        if not config_path.exists():
            logger.error(f"❌ No se encontró configuración: {config_path}")
            return 1

        config = SystemConfig.from_file(config_path)

        # Paso 1: Leer manifests existentes
        logger.info("")
        logger.info("PASO 1: Leyendo manifests existentes...")
        manifests_antes = leer_manifests_existentes(config, max_count=10)

        if not manifests_antes:
            logger.warning("⚠️  No se encontraron manifests para verificar")
            logger.info("Sugerencia: Ejecute primero una extracción inicial")
            return 0

        logger.info(f"✅ Leídos {len(manifests_antes)} manifests")
        for info in manifests_antes:
            logger.info(f"   - {info['numero']}")

        # Paso 2: Ejecutar ciclo de monitoreo
        logger.info("")
        logger.info("PASO 2: Ejecutando ciclo de monitoreo...")
        logger.info("(Esto puede tomar varios minutos)")

        monitor_config = MonitorConfig.from_system_config(config)
        monitor_config.headless = True  # Modo headless para pruebas
        monitor = MonitorPJN(monitor_config)

        # Ejecutar verificación (esto detectará cambios y actualizará manifests automáticamente)
        await monitor.verificar_expedientes()

        logger.info("✅ Ciclo de monitoreo completado")

        # Paso 3: Comparar manifests
        logger.info("")
        logger.info("PASO 3: Comparando manifests...")
        comparar_manifests(manifests_antes)

        logger.info("")
        logger.info("✅ VERIFICACIÓN COMPLETADA")
        return 0

    except KeyboardInterrupt:
        logger.warning("\n⚠️  Verificación interrumpida por el usuario")
        return 130

    except Exception as exc:
        logger.exception(f"❌ Error durante verificación: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
