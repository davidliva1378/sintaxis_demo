#!/usr/bin/env python3
"""Script personalizado del monitor para expedientes - Ajusta segun tus necesidades."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pjn.monitor.config import MonitorConfig
from pjn.monitor.core import MonitorPJN
from pjn.utils.logging import setup_logging, get_logger

# ==== CONFIGURACION PERSONALIZADA ====

# Nivel de logging: "DEBUG", "INFO", "WARNING", "ERROR"
NIVEL_LOG = "INFO"

# Archivo de configuracion (opcional)
CONFIG_FILE = "config/monitor.json"

# ======================================

setup_logging(level=NIVEL_LOG)
logger = get_logger(__name__)


async def main():
    """Ejecuta el monitor enfocado en expedientes."""

    # Opcion 1: Cargar desde archivo JSON
    # config = MonitorConfig.from_file(CONFIG_FILE)

    # Opcion 2: Crear configuracion programaticamente
    config = MonitorConfig(
        modo="automatico",
        headless=False,  # Cambiar a True para ejecucion sin interfaz

        # Desactivar verificacion de entradas
        verificar_entradas=False,

        # Activar verificacion de expedientes
        verificar_expedientes=True,

        # Intervalos de verificacion (minutos)
        intervalos_laboral_expedientes=15,
        intervalos_no_laboral_expedientes=60,

        # Filtros de fecha para expedientes
        # Opciones:
        # - None: Extrae todos los expedientes
        # - "DD/MM/YYYY": Fecha especifica
        # - "YYYY-MM-DD": Formato ISO
        fecha_desde_expedientes=None,  # Ej: "01/10/2025"
        fecha_hasta_expedientes=None,  # Ej: "17/10/2025"

        # Alternativa: fecha de corte (extrae desde esta fecha hacia atras)
        # Nota: fecha_desde_expedientes tiene prioridad sobre fecha_corte_expedientes
        fecha_corte_expedientes=None,  # Ej: "2025-10-01"

        # Notificaciones
        notificar_cambios_expedientes=True,
        notificar_errores=True,

        # Directorio de datos
        directorio_datos="data/monitor_expedientes"
    )

    logger.info("=" * 60)
    logger.info("MONITOR DE EXPEDIENTES PJN")
    logger.info("=" * 60)
    logger.info(f"  Modo: {config.modo}")
    logger.info(f"  Headless: {config.headless}")
    logger.info(f"  Verificar entradas: {config.verificar_entradas}")
    logger.info(f"  Verificar expedientes: {config.verificar_expedientes}")
    logger.info(f"  Directorio de datos: {config.directorio_datos}")

    if config.fecha_desde_expedientes or config.fecha_hasta_expedientes:
        logger.info(f"  Rango fechas: {config.fecha_desde_expedientes} - {config.fecha_hasta_expedientes}")
    elif config.fecha_corte_expedientes:
        logger.info(f"  Fecha de corte: {config.fecha_corte_expedientes}")

    logger.info("=" * 60)

    monitor = MonitorPJN(config)

    try:
        # Verificar expedientes
        if config.verificar_expedientes:
            logger.info("\n📊 Verificando expedientes...")
            cambios = await monitor.verificar_expedientes()

            if cambios:
                logger.info(f"\n✅ {len(cambios)} expedientes con cambios detectados:\n")

                for i, exp in enumerate(cambios, 1):
                    logger.info(f"{i}. Expediente: {exp.numero}")
                    logger.info(f"   Caratula: {exp.caratula}")
                    logger.info(f"   Dependencia: {exp.dependencia}")
                    logger.info(f"   Situacion: {exp.situacion_actual}")
                    logger.info(f"   Ultima actuacion: {exp.ultima_actuacion}")

                    if exp.fecha_inicio:
                        logger.info(f"   Fecha inicio: {exp.fecha_inicio}")

                    if exp.objeto:
                        logger.info(f"   Objeto: {exp.objeto}")

                    logger.info("")

                # Resumen por dependencia
                dependencias = {}
                for exp in cambios:
                    dep = exp.dependencia or "Sin dependencia"
                    dependencias[dep] = dependencias.get(dep, 0) + 1

                logger.info("📈 Resumen por dependencia:")
                for dep, count in sorted(dependencias.items(), key=lambda x: x[1], reverse=True):
                    logger.info(f"   {dep}: {count} expediente(s)")

            else:
                logger.info("\n✅ Sin cambios en expedientes detectados")

        # Verificar entradas (si está habilitado)
        if config.verificar_entradas:
            logger.info("\n📥 Verificando entradas...")
            nuevas = await monitor.verificar_entradas()

            if nuevas:
                logger.info(f"\n✅ {len(nuevas)} nuevas entradas:")
                for i, entrada in enumerate(nuevas[:5], 1):  # Mostrar hasta 5
                    logger.info(f"{i}. {entrada.numero} - {entrada.evento}")

                if len(nuevas) > 5:
                    logger.info(f"   ... y {len(nuevas) - 5} más")
            else:
                logger.info("\n✅ Sin nuevas entradas")

        logger.info("\n" + "=" * 60)
        logger.info("✅ VERIFICACION COMPLETADA EXITOSAMENTE")
        logger.info("=" * 60)

        # Mostrar informacion del estado
        logger.info("\n📊 Estado del monitor:")
        logger.info(f"   Ultima verificacion expedientes: {monitor.estado.ultima_verificacion_expedientes}")
        logger.info(f"   Errores consecutivos: {monitor.estado.errores_consecutivos_expedientes}")

        # Mostrar rutas de archivos
        logger.info("\n📁 Archivos guardados en:")
        logger.info(f"   Estado: {monitor.storage.archivo_estado}")
        logger.info(f"   Historial expedientes: {monitor.storage.archivo_expedientes}")
        if config.verificar_entradas:
            logger.info(f"   Historial entradas: {monitor.storage.archivo_entradas}")

        return 0

    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupcion por usuario")
        return 0

    except Exception as e:
        logger.error(f"\n❌ Error durante verificacion: {e}", exc_info=True)
        logger.info("\n" + "=" * 60)
        logger.info("❌ VERIFICACION FALLO")
        logger.info("=" * 60)
        return 1


if __name__ == "__main__":
    resultado = asyncio.run(main())
    sys.exit(resultado)
